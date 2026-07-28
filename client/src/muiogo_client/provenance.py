"""Record what produced a run's results, so a number can be defended later.

The pipeline is bit-deterministic: solving the same case run twice gives the same
objective and byte-identical result CSVs, and the generated model input
(`data.txt`) is a stable canonical fingerprint — writing a parameter back through
the API reshuffles the JSON on disk but does not change data.txt. Source JSON
files are therefore useless as fingerprints; data.txt is the right one.

What is missing without this module is not determinism but auditability: nothing
links a result set back to the inputs, the solver, or the code that made it, so
stored results can silently disagree with the case they sit in (MUIOGO's own demo
ships a CO2TAX result its current data no longer reproduces).

A RUN.json answers: which case and run, which scenarios were active, which
solver, what the objective was, what the model input hashed to, and which MUIOGO
this was. `verify()` re-solves and compares.
"""
import datetime
import hashlib
import json
import platform
import subprocess
from pathlib import Path

RECORD_NAME = "RUN.json"
SCHEMA_VERSION = 1


def _sha256(path, limit_mb=512):
    path = Path(path)
    if not path.is_file():
        return None
    h = hashlib.sha256()
    with open(path, "rb") as f:
        read = 0
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
            read += len(chunk)
            if read > limit_mb * (1 << 20):
                return None                     # refuse to fingerprint absurd files
    return h.hexdigest()


def _git_ref(path):
    try:
        out = subprocess.run(
            ["git", "-C", str(path), "rev-parse", "--short=8", "HEAD"],
            capture_output=True, text=True, timeout=15)
        return out.stdout.strip() or None
    except (OSError, subprocess.SubprocessError):
        return None


def run_dir(data_storage, case, run):
    return Path(data_storage) / case / "res" / run


def solver_status(data_storage, case, run):
    """The solver's own verdict: the first line of results.txt."""
    path = run_dir(data_storage, case, run) / "results.txt"
    if not path.is_file():
        return None
    with open(path, encoding="utf-8", errors="replace") as f:
        return f.readline().strip() or None


def objective(data_storage, case, run):
    """Objective value parsed out of the solver status line, or None."""
    line = solver_status(data_storage, case, run) or ""
    for token in line.replace(",", " ").split():
        try:
            return float(token)
        except ValueError:
            continue
    return None


def results_digest(data_storage, case, run):
    """One hash over every result CSV, so two result sets can be compared.

    Deterministic for a given input state: solving the same run twice gives the
    same objective and the same digest (verified). The digest covers the SET of
    files as well as their contents, so it also changes when the set changes —
    MUIOGO writes 32 result variables on a re-solve where some shipped runs
    carry 44. That is a real difference worth catching, not noise, but it means a
    digest is only comparable against one produced by the same MUIOGO version.
    The objective is the more portable check.
    """
    csv_dir = run_dir(data_storage, case, run) / "csv"
    if not csv_dir.is_dir():
        return None, 0
    files = sorted(csv_dir.glob("*.csv"))
    if not files:
        return None, 0
    h = hashlib.sha256()
    for path in files:
        h.update(path.name.encode())
        digest = _sha256(path)
        h.update((digest or "").encode())
    return h.hexdigest(), len(files)


def active_scenarios(data_storage, case, run):
    """The scenarios this run switches on — what actually defines it."""
    res_data = Path(data_storage) / case / "view" / "resData.json"
    if not res_data.is_file():
        return None
    try:
        with open(res_data, encoding="utf-8") as f:
            cases = json.load(f).get("osy-cases", [])
    except (OSError, ValueError):
        return None
    for entry in cases:
        if entry.get("Case") == run:
            return [s.get("Scenario") for s in entry.get("Scenarios", []) if s.get("Active")]
    return None


def build(data_storage, case, run, solver="cbc", muiogo_path=None, extra=None):
    """Assemble the provenance record for a run that has just been solved."""
    rd = run_dir(data_storage, case, run)
    digest, n_files = results_digest(data_storage, case, run)
    record = {
        "schema_version": SCHEMA_VERSION,
        "recorded": datetime.datetime.now().isoformat(timespec="seconds"),
        "case": case,
        "run": run,
        "scenarios_active": active_scenarios(data_storage, case, run),
        "solver": solver,
        "solver_status": solver_status(data_storage, case, run),
        "objective": objective(data_storage, case, run),
        "input_sha256": _sha256(rd / "data.txt"),
        "results_sha256": digest,
        "result_files": n_files,
        "muiogo_ref": _git_ref(muiogo_path) if muiogo_path else None,
        "platform": f"{platform.system()} {platform.machine()}",
    }
    if extra:
        record.update(extra)
    return record


def write(data_storage, case, run, **kwargs):
    """Write RUN.json beside the results. Returns (path, record)."""
    record = build(data_storage, case, run, **kwargs)
    path = run_dir(data_storage, case, run) / RECORD_NAME
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(record, indent=2) + "\n", encoding="utf-8")
    return path, record


def read(data_storage, case, run):
    """The stored record for a run, or None if it was never recorded."""
    path = run_dir(data_storage, case, run) / RECORD_NAME
    if not path.is_file():
        return None
    try:
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    except (OSError, ValueError):
        return None


def compare_to_current(data_storage, case, run):
    """Check a stored record against what is on disk right now.

    Returns (ok, list of differences). This is what catches results that have
    gone stale relative to the case they live in.
    """
    stored = read(data_storage, case, run)
    if stored is None:
        return None, ["no provenance record for this run"]
    current = build(data_storage, case, run, solver=stored.get("solver", "cbc"))
    diffs = []
    for field in ("objective", "input_sha256", "results_sha256", "result_files",
                  "solver_status", "scenarios_active"):
        was, now = stored.get(field), current.get(field)
        if was != now:
            diffs.append(f"{field}: recorded {was!r}, now {now!r}")
    return (not diffs), diffs


def consistency(data_storage, case, runs):
    """Warn when runs in a comparison did not come from the same input state.

    Runs of the same case that were solved from different input data are not
    comparable, and nothing on disk makes that visible without this check.
    """
    seen, unrecorded, drifted = {}, [], []
    for run in runs:
        rec = read(data_storage, case, run)
        if rec is None:
            unrecorded.append(run)
            continue
        # A record that no longer matches disk means the results changed after
        # they were recorded — the run was re-solved, or the case was edited.
        ok, _ = compare_to_current(data_storage, case, run)
        if ok is False:
            drifted.append(run)
        seen.setdefault(rec.get("muiogo_ref"), []).append(run)
    warnings = []
    if drifted:
        warnings.append(
            "results changed since they were recorded for "
            + ", ".join(drifted) + " — re-solve, or `muiogo verify` to see what moved"
        )
    if unrecorded:
        warnings.append(
            "no provenance for " + ", ".join(unrecorded)
            + " — these results may predate the case's current input data; re-solve to be sure"
        )
    if len(seen) > 1:
        detail = "; ".join(f"{ref or 'unknown'}: {', '.join(rs)}" for ref, rs in seen.items())
        warnings.append(f"runs were solved against different MUIOGO versions ({detail})")
    return warnings
