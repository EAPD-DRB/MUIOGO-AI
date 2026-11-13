#!/usr/bin/env python3
"""Deterministic pre-run preflight for OG-Core / CLEWS model runs.

Refuses (exit 1) unless every check passes:
  1. Every repo involved is a git checkout; branch + HEAD printed.
  2. The repo's venv exists and its sys.prefix resolves inside the repo
     (per-worktree venv house rule).
  3. The repo's own package imports from INSIDE the repo under three
     invocation styles (the three shadowing vectors):
       a. neutral cwd            -> catches editable installs pointing at
                                    another worktree
       b. the intended run cwd   -> catches cwd shadowing (`python -c` /
                                    `python script.py` put cwd/script dir at
                                    sys.path[0])
       c. the entry script's dir -> catches script-dir shadowing
  4. Extra packages (e.g. ogcore) resolve inside the repo or the venv --
     never inside some other sibling checkout.
  5. An OG model checkout (one whose --check names ogcore) was made by
     OG-Core's official installer, and its ogcore is what the repo's uv.lock
     pins: not an editable or local-folder install of another build.
  6. The entry script is the repo's own code: inside the first --check's repo
     and tracked by git (an example or tuning script it ships), not a driver,
     wrapper or copy of your own.

There is no probe-only GO: a lead is produced the same way as a reported run.

Usage:
  preflight.py --check REPO::PKG[,PKG2,...][::VENV_PYTHON] \
               [--check ...] [--run-cwd DIR] [--entry-script PATH]

  REPO         path to the checkout the run is supposed to use
  PKG          the repo's own importable package (first name); further
               comma-separated names are dependency packages to locate
  VENV_PYTHON  defaults to REPO/.venv/bin/python

Example (cross-env ogclews run -- one --check per environment):
  preflight.py \
    --check ~/Projects/ogclews-link::ogclews_link \
    --check ~/Projects/OG-PHL::ogphl,ogcore::/path/to/registry/env_python \
    --run-cwd ~/Projects/ogclews-link \
    --entry-script ~/Projects/ogclews-link/experiments/run_battery.py

Written after a battery silently ran stale code via import shadowing
(2026-07-07). This script exists so that never recurs.

Trust boundary: the probes execute the target repo's venv python and import the
package (module-level code runs). That is the same trust decision as running the
model itself -- only point this at repos/venvs you intend to run anyway.
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import tempfile

GREEN, RED, YELLOW, RESET = "\033[32m", "\033[31m", "\033[33m", "\033[0m"


def valid_pkg(name: str) -> bool:
    """Package names are interpolated into `python -c "import <name>"` — restrict them to
    (dotted) identifiers so a crafted name can never smuggle code into the probe."""
    return bool(name) and all(part.isidentifier() for part in name.split("."))


def real(p: str) -> str:
    return os.path.realpath(os.path.expanduser(p))


def under(path: str, root: str) -> bool:
    path, root = real(path), real(root)
    return path == root or path.startswith(root + os.sep)


class Report:
    def __init__(self) -> None:
        self.failures = 0
        self.warnings = 0
        self.dev_checkouts: list[str] = []

    def info(self, tag: str, msg: str) -> None:
        print(f"[{tag:5}] {msg}")

    def ok(self, msg: str) -> None:
        print(f"[{GREEN}PASS{RESET} ] {msg}")

    def warn(self, msg: str) -> None:
        self.warnings += 1
        print(f"[{YELLOW}WARN{RESET} ] {msg}")

    def fail(self, msg: str) -> None:
        self.failures += 1
        print(f"[{RED}FAIL{RESET} ] {msg}")


def git_state(repo: str, rep: Report) -> None:
    def g(*args: str) -> str:
        return subprocess.run(
            ["git", "-C", repo, *args], capture_output=True, text=True
        ).stdout.strip()

    inside = subprocess.run(
        ["git", "-C", repo, "rev-parse", "--is-inside-work-tree"],
        capture_output=True, text=True,
    )
    if inside.returncode != 0:
        rep.fail(f"not a git checkout: {repo}")
        return
    branch = g("rev-parse", "--abbrev-ref", "HEAD")
    head = g("rev-parse", "--short", "HEAD")
    dirty = g("status", "--porcelain")
    n_dirty = len(dirty.splitlines()) if dirty else 0
    rep.info("GIT", f"{repo}  branch={branch}  HEAD={head}  dirty_files={n_dirty}")
    if n_dirty:
        rep.warn(f"{repo}: {n_dirty} uncommitted change(s) -- the run will use them")


def check_not_moved(repo: str, rep: Report, required: bool) -> None:
    """An installer copy is tied to the commit it cloned. A pull, checkout or
    reset afterwards moves it to code the installer never synced: re-install
    instead (a new folder per commit)."""
    r = subprocess.run(["git", "-C", repo, "reflog", "--format=%gs"],
                       capture_output=True, text=True)
    moves = [m for m in r.stdout.splitlines() if not m.startswith("clone:")]
    if not moves:
        rep.ok("still at the commit the installer cloned")
        return
    msg = (f"{repo}: moved since the installer made it ({len(moves)} time(s), last: "
           f"{moves[0]}) -- re-install the new commit into a new folder")
    rep.fail(msg) if required else rep.warn(msg)


def check_installer_record(repo: str, rep: Report,
                           installer_log: str | None = None,
                           required: bool = False) -> None:
    """OG-Core's installer writes an .install-*.log next to the installer
    script (not next to the clone), naming each clone's path. A log that
    names this checkout and reports success marks an installer-built copy.
    No such log means a hand-built environment (a dev worktree, `uv sync` by
    hand). For an OG model checkout (required=True) that is a failure: probes
    and reported runs alike come from installer copies (og-run). For other
    repos in a cross-env run (e.g. ogclews-link) it stays a warning."""
    import glob
    target = real(repo)
    if installer_log:
        candidates = [real(installer_log)]
    else:
        dirs = {os.path.dirname(target), os.getcwd()}
        candidates = sorted(
            f for d in dirs for f in glob.glob(os.path.join(d, ".install-*.log"))
        )
    for log in candidates:
        try:
            text = open(log, errors="replace").read()
        except OSError:
            continue
        cloned_here = f"Cloning into '{target}'" in text
        if cloned_here and "installed successfully" in text:
            rep.ok(f"installer record: {log}")
            check_not_moved(repo, rep, required)
            return
    hint = (" (pass --installer-log PATH: the installer writes its log beside "
            "install.sh)") if not installer_log else ""
    if required:
        rep.fail(
            f"{repo}: no installer record found -- hand-built checkout. Install it with "
            f"OG-Core's installer (--repo-url ... --branch ...) into a new folder and run "
            f"from there; there is no probe-only exception{hint}."
        )
        return
    rep.warn(
        f"{repo}: no installer record found -- hand-built checkout. "
        f"GO covers in-task probes only, NOT reported runs (see og-run){hint}."
    )
    rep.dev_checkouts.append(repo)


def probe(python: str, pkg: str, cwd: str, prepend: str | None = None) -> tuple[bool, str]:
    """Import pkg with the given interpreter/cwd; return (ok, resolved_path_or_err)."""
    if prepend is not None:
        code = (
            "import sys; sys.path.insert(0, {p!r}); "
            "import {m}; print({m}.__file__)"
        ).format(p=prepend, m=pkg)
    else:
        code = f"import {pkg}; print({pkg}.__file__)"
    r = subprocess.run(
        [python, "-c", code], capture_output=True, text=True, cwd=cwd, timeout=120
    )
    if r.returncode != 0:
        return False, r.stderr.strip().splitlines()[-1] if r.stderr.strip() else "import failed"
    return True, real(r.stdout.strip())


def check_repo(spec: str, run_cwd: str | None, entry_script: str | None, rep: Report,
               params_json: str | None = None, installer_log: str | None = None) -> None:
    parts = spec.split("::")
    if len(parts) not in (2, 3):
        rep.fail(f"bad --check spec (want REPO::PKG[,PKG..][::VENV_PY]): {spec}")
        return
    repo = real(parts[0])
    pkgs = [p.strip() for p in parts[1].split(",") if p.strip()]
    bad = [p for p in pkgs if not valid_pkg(p)]
    if bad:
        rep.fail(f"invalid package name(s) {bad} -- must be plain (dotted) identifiers")
        return
    own, extras = pkgs[0], pkgs[1:]
    # abspath, NOT realpath: a uv venv's python is a symlink to uv's base interpreter, and running
    # the resolved target would report the base prefix instead of the venv's.
    python = (os.path.abspath(os.path.expanduser(parts[2])) if len(parts) == 3
              else os.path.join(repo, ".venv", "bin", "python"))

    print(f"\n=== {own} @ {repo} ===")
    if not os.path.isdir(repo):
        rep.fail(f"repo path does not exist: {repo}")
        return
    git_state(repo, rep)
    check_installer_record(repo, rep, installer_log, required="ogcore" in pkgs)

    if not os.access(python, os.X_OK):
        rep.fail(f"venv python not found/executable: {python}")
        return
    ok, prefix = True, ""
    r = subprocess.run([python, "-c", "import sys; print(sys.prefix)"],
                       capture_output=True, text=True)
    if r.returncode != 0:
        rep.fail(f"interpreter unusable: {python}")
        return
    prefix = real(r.stdout.strip())
    if under(python, repo) or under(prefix, repo):
        rep.ok(f"per-worktree venv: prefix={prefix}")
    else:
        rep.fail(
            f"venv is NOT inside the repo (prefix={prefix}); each worktree "
            "gets its own venv -- `python -m venv .venv && .venv/bin/pip install -e .`"
        )

    if os.environ.get("PYTHONPATH"):
        rep.warn(f"PYTHONPATH is set and will affect the run: {os.environ['PYTHONPATH']}")

    # Vector (a): editable install -> another worktree. Neutral cwd.
    with tempfile.TemporaryDirectory() as neutral:
        ok, path = probe(python, own, neutral)
    not_installed = not ok and f"No module named '{own.split('.')[0]}'" in path
    if not_installed:
        # Nothing installed, so no other checkout can shadow it. Safe only if the run
        # launches from a folder where it resolves inside the repo -- checked below.
        rep.info("INFO", f"{own} is not installed (runs from its folder); the run-cwd import decides")
        if not run_cwd:
            rep.fail(f"{own} is not installed and no --run-cwd was given: cannot confirm which code runs")
    elif not ok:
        rep.fail(f"import {own} (neutral cwd) failed: {path}")
    elif under(path, repo):
        rep.ok(f"import {own} (neutral cwd) -> {path}")
    else:
        rep.fail(
            f"import {own} (neutral cwd) -> {path} -- OUTSIDE {repo}. "
            "The venv's (editable) install points at another checkout; "
            f"re-run `{python} -m pip install -e {repo}`"
        )

    # Vector (b): cwd shadowing -- probe from the cwd the run will use.
    if run_cwd:
        ok, path = probe(python, own, real(run_cwd))
        if not ok:
            rep.fail(f"import {own} (run cwd={run_cwd}) failed: {path}")
        elif under(path, repo):
            rep.ok(f"import {own} (run cwd={run_cwd}) -> {path}")
        else:
            rep.fail(
                f"import {own} (run cwd={run_cwd}) -> {path} -- the run cwd "
                "shadows the intended checkout. Launch from the worktree under "
                "test, or use a console script (immune to cwd shadowing)."
            )

    # Vector (c): script-dir shadowing -- simulate `python script.py` sys.path[0].
    if entry_script:
        sdir = os.path.dirname(real(entry_script))
        with tempfile.TemporaryDirectory() as neutral:
            ok, path = probe(python, own, neutral, prepend=sdir)
        if not ok:
            rep.fail(f"import {own} (script dir {sdir}) failed: {path}")
        elif under(path, repo):
            rep.ok(f"import {own} (script dir {sdir} at sys.path[0]) -> {path}")
        else:
            rep.fail(
                f"import {own} (script dir {sdir} at sys.path[0]) -> {path} -- "
                "the entry script's directory shadows the intended checkout."
            )

    # Extra packages: must live in the repo or the venv, never a sibling checkout.
    for pkg in extras:
        with tempfile.TemporaryDirectory() as neutral:
            ok, path = probe(python, pkg, neutral)
        if not ok:
            rep.fail(f"import {pkg} failed: {path}")
        elif under(path, repo) or under(path, prefix):
            rep.ok(f"import {pkg} -> {path}")
        else:
            rep.fail(
                f"import {pkg} -> {path} -- resolves outside both the repo and "
                "its venv (another checkout is bleeding in)"
            )

    if "ogcore" in pkgs:
        ogcore_build(python, rep, repo)
    if params_json:
        check_params(python, params_json, rep)


OGCORE_BUILD = r"""
import json, ogcore
from importlib import metadata
try:
    raw = metadata.distribution("ogcore").read_text("direct_url.json")
except Exception:
    raw = None
print(json.dumps({"version": ogcore.__version__, "direct_url": json.loads(raw) if raw else None}))
"""


def locked_ogcore(repo: str) -> dict | None:
    """The ogcore entry in the repo's uv.lock: its version and, for a git
    source, the pinned commit. None when the repo has no lock or no entry."""
    path = os.path.join(repo, "uv.lock")
    try:
        text = open(path).read()
    except OSError:
        return None
    for block in text.split("[[package]]"):
        if 'name = "ogcore"' not in block:
            continue
        out: dict = {"version": None, "commit": None}
        for line in block.splitlines():
            line = line.strip()
            if line.startswith("version = "):
                out["version"] = line.split('"')[1]
            elif line.startswith("source = ") and "git = " in line and "#" in line:
                out["commit"] = line.split("#")[-1].split('"')[0].strip()
        return out
    return None


def ogcore_build(python: str, rep: Report, repo: str | None = None) -> None:
    """Say which ogcore will run, and require it to be the one the repo's
    uv.lock pins.

    Where ogcore imports from is checked above; this is what it is. An editable or
    local-folder install means someone put another build into the environment by
    hand: that is a failure, whatever the run is for. An unreleased ogcore goes in
    through the country repo's own pin on a branch, then the installer.
    """
    r = subprocess.run([python, "-c", OGCORE_BUILD], capture_output=True, text=True, timeout=120)
    if r.returncode != 0:
        rep.warn("could not read ogcore's version and install source")
        return
    info = json.loads(r.stdout.strip().splitlines()[-1])
    version, url = info["version"], info["direct_url"]
    if not url:
        rep.ok(f"ogcore {version}: a released package")
    elif "vcs_info" in url:
        commit = url["vcs_info"].get("commit_id", "?")[:10]
        rep.info("INFO", f"ogcore {version}: installed from {url.get('url', '?')} at commit {commit}")
    else:
        src = url.get("url", "").replace("file://", "")
        kind = "editable local checkout" if url.get("dir_info", {}).get("editable") else "local build"
        rep.fail(f"ogcore {version}: {kind} from {src} -- installed by hand into this "
                 "environment. Pin the build in the repo (a branch with "
                 "[tool.uv.sources] ogcore = { git = ..., rev = ... } and uv lock), then "
                 "re-install that branch with the installer")
        return
    if repo is None:
        return
    lock = locked_ogcore(repo)
    if lock is None:
        rep.warn(f"no ogcore entry in {repo}/uv.lock -- cannot check the environment against it")
        return
    installed_commit = (url or {}).get("vcs_info", {}).get("commit_id") if url else None
    if lock["commit"]:
        if installed_commit != lock["commit"]:
            rep.fail(f"ogcore commit {str(installed_commit)[:10]} is not the one uv.lock pins "
                     f"({lock['commit'][:10]}) -- the environment has drifted from the lock; "
                     "re-run the installer (or uv sync --extra dev in the installed folder)")
        else:
            rep.ok(f"ogcore matches uv.lock (commit {lock['commit'][:10]})")
    elif lock["version"] and version != lock["version"]:
        rep.fail(f"ogcore {version} is not the version uv.lock pins ({lock['version']}) -- the "
                 "environment has drifted from the lock; re-run the installer")
    elif lock["version"]:
        rep.ok(f"ogcore matches uv.lock ({lock['version']})")


def check_params(python: str, params_json: str, rep: Report) -> None:
    """Load the packaged parameters into Specifications, the way the examples do."""
    code = (
        "import json; from ogcore.parameters import Specifications; "
        "p = Specifications(baseline=True); "
        f"p.update_specifications(json.load(open({params_json!r})))"
    )
    r = subprocess.run([python, "-c", code], capture_output=True, text=True, timeout=300)
    if r.returncode == 0:
        rep.ok(f"packaged parameters load on this ogcore: {params_json}")
    else:
        lines = r.stderr.strip().splitlines()
        # The error spans several lines (paramtools prints a JSON body): keep from the
        # exception line to the end, flattened.
        start = max((i for i, line in enumerate(lines) if "Error" in line.split(":")[0]), default=len(lines) - 1)
        why = " ".join(" ".join(lines[start:]).split())[:300] if lines else "load failed"
        rep.fail(f"packaged parameters do NOT load on this ogcore ({params_json}): {why}")


def check_entry_script(entry_script: str, repo: str, rep: Report) -> None:
    """The run executes the repo's own code: a script inside the repo, tracked by
    git. A driver in a scratch folder, a wrapper, or an untracked copy fails."""
    script = real(entry_script)
    if not os.path.isfile(script):
        rep.fail(f"entry script not found: {entry_script}")
        return
    if not under(script, repo):
        rep.fail(f"entry script {script} is outside {repo} -- run the repo's own script "
                 "from the installed copy, not a driver or wrapper of your own")
        return
    r = subprocess.run(["git", "-C", repo, "ls-files", "--error-unmatch", script],
                       capture_output=True, text=True)
    if r.returncode != 0:
        rep.fail(f"entry script {script} is not tracked by git in {repo} -- a script the "
                 "repo does not ship (a copy, a wrapper, a scratch driver)")
        return
    rep.ok(f"entry script is repo code: {os.path.relpath(script, repo)}")


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--check", action="append", required=True,
                    metavar="REPO::PKG[,PKG..][::VENV_PY]")
    ap.add_argument("--run-cwd", help="directory the run will be launched from")
    ap.add_argument("--entry-script", help="the script the run will execute")
    ap.add_argument("--params-json", help="the packaged parameters JSON the run loads; checked "
                    "to load on the resolved ogcore (applies to the first --check)")
    ap.add_argument("--installer-log", help="the OG-Core installer's .install-*.log, when it "
                    "is not in the checkout's parent or the current directory (the "
                    "installer writes it beside install.sh; applies to the first --check)")
    args = ap.parse_args()

    rep = Report()
    first_repo = real(args.check[0].split("::")[0])
    if "ogcore" in args.check[0].split("::")[1].split(",") and not args.entry_script:
        rep.fail("no --entry-script: name the repo script the run executes "
                 "(e.g. examples/run_og_xxx.py or the repo's tuning script)")
    if args.entry_script:
        check_entry_script(args.entry_script, first_repo, rep)
    for spec in args.check:
        first = spec == args.check[0]
        check_repo(spec, args.run_cwd, args.entry_script, rep,
                   args.params_json if first else None,
                   args.installer_log if first else None)

    print()
    if rep.failures:
        print(f"RESULT: {RED}NO-GO{RESET} -- {rep.failures} failure(s), "
              f"{rep.warnings} warning(s). Do not launch.")
        return 1
    if rep.dev_checkouts:
        print(f"RESULT: {GREEN}GO{RESET} (dev checkout -- in-task probes only, "
              f"NOT valid for reported runs; see og-run) "
              f"({rep.warnings} warning(s)).")
    else:
        print(f"RESULT: {GREEN}GO{RESET} -- all checks passed "
              f"({rep.warnings} warning(s)).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
