"""HTTP client for the MUIOGO Flask API.

Mechanical only: request shapes, session cookie, file downloads. Every method
mirrors an endpoint observed working against MUIOGO @ 3db8b816 (see
docs/API_ENDPOINTS.md). No analysis, no judgment.

Session model: MUIOGO keeps the selected case in a server-side Flask session
('osycase') keyed by cookie. List/run/generate endpoints take the case name
explicitly; copy and download endpoints are session-gated. select_case() sets
the session; methods that need it call it implicitly when given a case.
"""
import json
import uuid
from pathlib import Path

import requests

DEFAULT_URL = "http://127.0.0.1:5002"


class MuiogoError(RuntimeError):
    """An API call failed (HTTP error or status_code == 'error' in the body)."""


class MuiogoClient:
    def __init__(self, base_url=DEFAULT_URL, timeout=600):
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self._http = requests.Session()

    # -- plumbing ------------------------------------------------------------

    def _get(self, path, **kwargs):
        r = self._http.get(f"{self.base_url}{path}", timeout=self.timeout, **kwargs)
        r.raise_for_status()
        return r

    def _post_json(self, path, payload):
        r = self._http.post(f"{self.base_url}{path}", json=payload, timeout=self.timeout)
        r.raise_for_status()
        body = r.json()
        if isinstance(body, dict) and body.get("status_code") == "error":
            raise MuiogoError(body.get("message") or str(body))
        return body

    # -- session -------------------------------------------------------------

    def get_selected_case(self):
        """Case currently in the server session, or None."""
        return self._get("/getSession").json().get("session")

    def select_case(self, case):
        """Set the server session's active case ('osycase')."""
        return self._post_json("/setSession", {"case": case})

    # -- cases ---------------------------------------------------------------

    def list_cases(self):
        return self._get("/getCases").json()

    def copy_case(self, case):
        """Copy `case` to '<case>_copy'. Session-gated: session must match `case`."""
        self.select_case(case)
        return self._post_json("/copyCase", {"casename": case})

    def delete_case(self, case):
        """Delete `case`. Session-gated like copy_case."""
        self.select_case(case)
        return self._post_json("/deleteCase", {"casename": case})

    # -- runs ----------------------------------------------------------------

    def generate_datafile(self, case, run):
        """Write res/<run>/data.txt from the case's scenario data."""
        return self._post_json("/generateDataFile", {"casename": case, "caserunname": run})

    def run(self, case, run, solver="cbc", generate=True):
        """Solve one case run. Synchronous: returns when the solver finishes.

        solver: 'cbc' (preprocesses data, GUI default) or 'glpk' (currently
        broken upstream: skips preprocessing, fails on MODEperTECHNOLOGY).

        MUIOGO returns HTTP 200 for solver failures, and its status_code is
        'success' ONLY when CBC reported "Optimal" — an infeasible model comes
        back as 'warning' and produces NO result CSVs. So anything other than
        success is raised as a failure here; a caller that got a value can trust
        results exist.
        """
        if generate:
            self.generate_datafile(case, run)
        body = self._post_json("/run", {"casename": case, "caserunname": run, "solver": solver})
        status = (body or {}).get("status_code")
        if status != "success":
            detail = (body.get("timer") or "").strip() or f"solver status: {status}"
            hint = ""
            if status == "warning":
                hint = (" The model did not solve to optimality (usually infeasible), "
                        "so no results were written.")
            raise MuiogoError(f"run {run!r} of {case!r} did not succeed. {detail}{hint}")
        return body

    def results_exist(self, case, run):
        body = self._post_json("/resultsExists", {"casename": case, "caserunname": run})
        return body

    def batch_run(self, case, runs):
        """Generate + solve several runs in one request. Server-side solver is CBC."""
        return self._post_json("/batchRun", {"modelname": case, "cases": list(runs)})

    def server_log(self):
        """MUIOGO's process-wide runtime log.

        Note this is the whole server's log, not one run's: /readLogFile takes no
        parameters and ignores any that are sent. For a single run's solver
        output use run_output().
        """
        r = self._http.get(f"{self.base_url}/readLogFile", timeout=self.timeout)
        return r.text if r.status_code == 200 else ""

    def run_output(self, case, run, data_storage, limit=6000):
        """A run's own solver output, read from res/<run>/results.txt.

        This is the per-run record; the first line carries the solver's verdict.
        Returns '' when the run has never produced output.
        """
        path = Path(data_storage) / case / "res" / run / "results.txt"
        if not path.is_file():
            return ""
        text = path.read_text(encoding="utf-8", errors="replace")
        return text[:limit]

    # -- scenarios and runs --------------------------------------------------
    # A case defines named SCENARIOS (parameter overlays, in genData.json's
    # 'osy-scenarios'). A RUN ("case run") is a named combination that activates
    # a subset of them; the set lives in view/resData.json. Solving a run merges
    # the active overlays onto the base scenario. Verified against MUIOGO
    # 3db8b816 on the CLEWs Demo case.

    def describe_case(self, case):
        """Free-text description of a case."""
        body = self._post_json("/getDesc", {"casename": case})
        return body.get("desc") if isinstance(body, dict) else body

    def case_dir(self, case, data_storage):
        return Path(data_storage) / case

    def list_scenarios(self, case, data_storage):
        """Scenarios defined on a case: [{ScenarioId, Scenario, Desc, Active}].

        Read from the case's genData.json — there is no endpoint that returns
        the scenario list on its own.
        """
        gen = self.case_dir(case, data_storage) / "genData.json"
        with open(gen, encoding="utf-8") as f:
            return json.load(f).get("osy-scenarios", [])

    def list_runs(self, case, data_storage):
        """Runs defined on a case, each with the scenarios it activates."""
        res_data = self.case_dir(case, data_storage) / "view" / "resData.json"
        if not res_data.is_file():
            return []
        with open(res_data, encoding="utf-8") as f:
            return json.load(f).get("osy-cases", [])

    def create_run(self, case, run, activate, data_storage, desc=""):
        """Create a run that activates the named scenarios.

        `activate` holds scenario NAMES (or ids) to switch on; the base scenario
        (SC_0) is always included. Returns the server's response.
        """
        scenarios = self.list_scenarios(case, data_storage)
        if not scenarios:
            raise MuiogoError(f"case {case!r} defines no scenarios")
        wanted = {str(a) for a in activate}
        rows = []
        for s in scenarios:
            on = (
                s.get("ScenarioId") == "SC_0"
                or s.get("Scenario") in wanted
                or s.get("ScenarioId") in wanted
            )
            rows.append({**s, "Active": bool(on)})
        unmatched = wanted - {s.get("Scenario") for s in scenarios} - {
            s.get("ScenarioId") for s in scenarios
        }
        if unmatched:
            raise MuiogoError(
                f"no such scenario(s) in {case!r}: {', '.join(sorted(unmatched))}"
            )
        payload = {
            "Case": run,
            "CaseId": f"CS_{uuid.uuid4().hex[:5]}",
            "Desc": desc or f"{run} ({', '.join(sorted(wanted)) or 'base only'})",
            "Runtime": "created by muiogo-client",
            "Scenarios": rows,
        }
        return self._post_json(
            "/createCaseRun",
            {"casename": case, "caserunname": run, "data": payload},
        )

    # -- bringing models and data in and out ---------------------------------

    def validate_inputs(self, case, run):
        """Check a case run's inputs before committing to a long solve."""
        return self._post_json("/validateInputs", {"casename": case, "caserunname": run})

    def import_case(self, zip_path, timeout=900):
        """Install a MUIO case from a .zip, the same path the GUI's restore uses.

        The archive must contain one top-level case folder holding genData.json.
        Returns the server's response; confirm afterwards with list_cases().
        """
        path = Path(zip_path)
        if not path.is_file():
            raise MuiogoError(f"no such file: {path}")
        with open(path, "rb") as f:
            r = self._http.post(f"{self.base_url}/uploadCase",
                                files={"file": (path.name, f, "application/zip")},
                                timeout=timeout)
        r.raise_for_status()
        try:
            return r.json()
        except ValueError:
            return {"raw": r.text[:400]}

    def import_xls(self, case, xls_path, timeout=900):
        """Load an Excel workbook into a case. Session-gated: selects `case`."""
        self.select_case(case)
        path = Path(xls_path)
        if not path.is_file():
            raise MuiogoError(f"no such file: {path}")
        with open(path, "rb") as f:
            r = self._http.post(f"{self.base_url}/uploadXls",
                                files={"file": (path.name, f, "application/vnd.ms-excel")},
                                timeout=timeout)
        r.raise_for_status()
        try:
            return r.json()
        except ValueError:
            return {"raw": r.text[:400]}

    def export_case(self, case, dest, timeout=900):
        """Download a case as a .zip — the shareable, self-contained package."""
        self.select_case(case)
        # /backupCase reads the query key `case`, not `casename` (verified:
        # UploadRoute.backupCase -> request.args.get('case')).
        r = self._http.get(f"{self.base_url}/backupCase",
                           params={"case": case}, timeout=timeout)
        r.raise_for_status()
        # Treat --out as a directory unless it names a .zip, so a path that does
        # not exist yet becomes a folder rather than an extensionless file.
        out = Path(dest)
        if out.is_dir() or out.suffix.lower() != ".zip":
            out.mkdir(parents=True, exist_ok=True)
            out = out / f"{case}.zip"
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_bytes(r.content)
        return out

    # -- OG country models (MUIOGO's own installer layer) --------------------
    # MUIOGO wraps the upstream OG-Core universal installer and keeps a registry
    # of installed calibrations. Driving it through here means the GUI, the
    # OG-CLEWs link and the skills all see the same models.

    @staticmethod
    def _countries(body):
        """Both /ogc list endpoints wrap their rows in a 'countries' key."""
        if isinstance(body, dict):
            return body.get("countries") or body.get("calibrations") or []
        return body or []

    def og_catalog(self):
        """Country calibrations available to install, read live from upstream."""
        return self._countries(self._get("/ogc/getCalibrationCatalog").json())

    def og_installed(self):
        """Country calibrations installed on this machine."""
        return self._countries(self._get("/ogc/getInstalledCalibrations").json())

    def og_install(self, catalog_key=None, repo_url=None, branch=None):
        """Start an OG country-model install. Returns the job's install_id.

        Asynchronous: the install clones and syncs a full model environment,
        which takes minutes. Poll with og_install_status().
        """
        if not (catalog_key or repo_url):
            raise MuiogoError("give either catalog_key or repo_url")
        payload = {}
        if catalog_key:
            payload["catalog_key"] = catalog_key
        if repo_url:
            payload["repo_url"] = repo_url
        if branch:
            payload["branch"] = branch
        return self._post_json("/ogc/installCalibration", payload)

    def og_register_local(self, country_id, country_name, local_path,
                          package_name=None, run_uv_sync=False):
        """Register an OG model that is ALREADY on this machine.

        This is MUIOGO's own mechanism for adopting an existing checkout, and it
        writes MUIOGO's registry — so the GUI, the OG-CLEWs link and the skills
        all see the same model. Prefer it over installing a second copy.
        """
        return self._post_json("/ogc/registerLocalCalibration", {
            "country_id": country_id,
            "country_name": country_name,
            "local_path": str(local_path),
            "package_name": package_name,
            "run_uv_sync": bool(run_uv_sync),
        })

    def og_install_status(self, install_id):
        r = self._get("/ogc/getInstallStatus", params={"install_id": install_id})
        return r.json()

    def delete_run(self, case, run, results_only=False):
        return self._post_json(
            "/deleteCaseRun",
            {"casename": case, "caserunname": run, "resultsOnly": bool(results_only)},
        )

    # -- results -------------------------------------------------------------

    def list_result_csvs(self, case, run):
        """Names of result CSVs for a solved run."""
        return self._post_json("/getResultCSV", {"casename": case, "caserunname": run})

    def download_csv(self, case, run, filename, dest_dir):
        """Download one result CSV. Session-gated; selects `case` first."""
        self.select_case(case)
        r = self._get("/downloadCSVFile", params={"caserunname": run, "file": filename})
        dest = Path(dest_dir) / filename
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_bytes(r.content)
        return dest

    def download_all_csvs(self, case, run, dest_dir):
        """Download every result CSV of a run into dest_dir. Returns the paths."""
        return [
            self.download_csv(case, run, name, dest_dir)
            for name in self.list_result_csvs(case, run)
        ]

    def download_results_txt(self, case, run, dest_dir):
        """Download the raw solver results.txt. Session-gated."""
        self.select_case(case)
        r = self._get("/downloadResultsFile", params={"caserunname": run})
        dest = Path(dest_dir) / "results.txt"
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_bytes(r.content)
        return dest
