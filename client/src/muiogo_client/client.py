"""HTTP client for the MUIOGO Flask API.

Mechanical only: request shapes, session cookie, file downloads. Every method
mirrors an endpoint observed working against MUIOGO @ 3db8b816 (see
docs/API_ENDPOINTS.md). No analysis, no judgment.

Session model: MUIOGO keeps the selected case in a server-side Flask session
('osycase') keyed by cookie. List/run/generate endpoints take the case name
explicitly; copy and download endpoints are session-gated. select_case() sets
the session; methods that need it call it implicitly when given a case.
"""
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
        The route returns HTTP 200 even for solver failures; the body's
        status_code field is the real signal, which _post_json enforces.
        """
        if generate:
            self.generate_datafile(case, run)
        body = self._post_json("/run", {"casename": case, "caserunname": run, "solver": solver})
        return body

    def results_exist(self, case, run):
        body = self._post_json("/resultsExists", {"casename": case, "caserunname": run})
        return body

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
