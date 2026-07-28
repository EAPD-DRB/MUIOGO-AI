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


def check_repo(spec: str, run_cwd: str | None, entry_script: str | None, rep: Report) -> None:
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
    python = real(parts[2]) if len(parts) == 3 else os.path.join(repo, ".venv", "bin", "python")

    print(f"\n=== {own} @ {repo} ===")
    if not os.path.isdir(repo):
        rep.fail(f"repo path does not exist: {repo}")
        return
    git_state(repo, rep)

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
    if not ok:
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


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--check", action="append", required=True,
                    metavar="REPO::PKG[,PKG..][::VENV_PY]")
    ap.add_argument("--run-cwd", help="directory the run will be launched from")
    ap.add_argument("--entry-script", help="the script the run will execute")
    args = ap.parse_args()

    rep = Report()
    for spec in args.check:
        check_repo(spec, args.run_cwd, args.entry_script, rep)

    print()
    if rep.failures:
        print(f"RESULT: {RED}NO-GO{RESET} -- {rep.failures} failure(s), "
              f"{rep.warnings} warning(s). Do not launch.")
        return 1
    print(f"RESULT: {GREEN}GO{RESET} -- all checks passed "
          f"({rep.warnings} warning(s)).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
