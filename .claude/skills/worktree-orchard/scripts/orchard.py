#!/usr/bin/env python3
"""Read-only inventory of every checkout / worktree / backup-copy dir for a project family.

Finds, under --root:
  * git checkouts whose directory name matches the family pattern
  * their registered linked worktrees (git worktree list), wherever they live
    (including hidden ones like <repo>/.claude/worktrees/*)
  * suspicious non-git directories matching the pattern (_bak, copy, holding pen, ...)

For each, reports: branch, HEAD, dirty file count, stash count, ahead/behind vs the
repo's default branch, last commit date, and a classification:
  MERGED      HEAD is an ancestor of the default branch and the tree is clean
  DIVERGED    commits not on the default branch
  UNCOMMITTED dirty working tree (with or without divergence)
  STALE-REF   default branch could not be determined (bare/odd repo)
  NOT-GIT     matching directory that is not a git checkout at all

STRICTLY READ-ONLY: runs only git read commands; prints candidate cleanup commands
for a human to review and run -- it never executes them.

Usage:
  orchard.py --family OG-PHL [--root ~/Projects]
  orchard.py --family "OG-*" --root ~/Projects
"""

from __future__ import annotations

import argparse
import fnmatch
import os
import shlex
import subprocess
import sys

SUSPECT_HINTS = ("_bak", "bak", "copy", "old", "holding", "backup", "tmp")


def clean(s: str) -> str:
    """Strip control characters (incl. ANSI escapes) from untrusted names before
    printing -- directory and branch names are attacker-influenceable text."""
    return "".join(c for c in s if c.isprintable())


def run(args: list[str], cwd: str | None = None) -> str:
    r = subprocess.run(args, capture_output=True, text=True, cwd=cwd, timeout=60)
    return r.stdout.strip() if r.returncode == 0 else ""


def is_git(path: str) -> bool:
    return run(["git", "-C", path, "rev-parse", "--is-inside-work-tree"]) == "true"


def default_branch(path: str) -> str:
    ref = run(["git", "-C", path, "symbolic-ref", "--quiet", "refs/remotes/origin/HEAD"])
    if ref:
        return ref.rsplit("/", 1)[-1]
    for cand in ("main", "master"):
        if run(["git", "-C", path, "rev-parse", "--verify", "--quiet", cand]):
            return cand
    return ""


def describe(path: str, main_ref_repo: str | None = None) -> dict:
    """main_ref_repo: repo to resolve the default branch in (the primary checkout
    for linked worktrees -- they share refs, so path itself works too)."""
    d: dict = {"path": path}
    d["branch"] = run(["git", "-C", path, "rev-parse", "--abbrev-ref", "HEAD"]) or "?"
    d["head"] = run(["git", "-C", path, "rev-parse", "--short", "HEAD"]) or "?"
    d["dirty"] = len(run(["git", "-C", path, "status", "--porcelain"]).splitlines())
    d["stashes"] = len(run(["git", "-C", path, "stash", "list"]).splitlines())
    d["last_commit"] = run(["git", "-C", path, "log", "-1", "--format=%cs"]) or "?"
    base = default_branch(main_ref_repo or path)
    d["base"] = base
    if not base:
        d["cls"] = "STALE-REF"
        d["ahead"] = d["behind"] = "?"
        return d
    counts = run(["git", "-C", path, "rev-list", "--left-right", "--count",
                  f"{base}...HEAD"])
    behind, ahead = (counts.split() + ["?", "?"])[:2] if counts else ("?", "?")
    d["ahead"], d["behind"] = ahead, behind
    merged = subprocess.run(
        ["git", "-C", path, "merge-base", "--is-ancestor", "HEAD", base],
        capture_output=True).returncode == 0
    if d["dirty"]:
        d["cls"] = "UNCOMMITTED"
    elif merged:
        d["cls"] = "MERGED"
    else:
        d["cls"] = "DIVERGED"
    return d


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--family", required=True,
                    help="directory-name pattern, e.g. 'OG-PHL' (matches OG-PHL*) or a glob")
    ap.add_argument("--root", default=os.path.expanduser("~/Projects"))
    args = ap.parse_args()

    root = os.path.realpath(os.path.expanduser(args.root))
    pat = args.family if any(c in args.family for c in "*?[") else args.family + "*"

    tops = sorted(
        os.path.join(root, n) for n in os.listdir(root)
        if fnmatch.fnmatch(n.lower(), pat.lower()) and os.path.isdir(os.path.join(root, n))
    )
    if not tops:
        print(f"no directories under {root} match {pat!r}")
        return 1

    seen: dict[str, dict] = {}
    not_git: list[str] = []
    for top in tops:
        if not is_git(top):
            not_git.append(top)
            continue
        rp = os.path.realpath(top)
        if rp not in seen:
            seen[rp] = describe(top)
            seen[rp]["kind"] = "checkout"
        # registered linked worktrees (wherever they live)
        wt = run(["git", "-C", top, "worktree", "list", "--porcelain"])
        for line in wt.splitlines():
            if line.startswith("worktree "):
                w = os.path.realpath(line.split(" ", 1)[1])
                if w not in seen:
                    seen[w] = describe(w, main_ref_repo=top)
                    seen[w]["kind"] = "worktree"

    rows = sorted(seen.values(), key=lambda d: d["path"])
    wpath = max(len(d["path"]) for d in rows) if rows else 10
    print(f"{'PATH':<{wpath}}  {'KIND':<8} {'CLASS':<11} {'BRANCH':<28} "
          f"{'HEAD':<9} {'DIRTY':<5} {'A/B':<7} LAST")
    for d in rows:
        print(f"{clean(d['path']):<{wpath}}  {d['kind']:<8} {d['cls']:<11} "
              f"{clean(d['branch']):<28} {clean(d['head']):<9} {d['dirty']:<5} "
              f"{d['ahead']}/{d['behind']:<5} {clean(d['last_commit'])}")
    for p in not_git:
        print(f"{clean(p):<{wpath}}  {'dir':<8} {'NOT-GIT':<11} {'-':<28} {'-':<9} {'-':<5} {'-':<7} -")

    # Candidate cleanup commands -- PRINTED ONLY, never run.
    print("\n--- candidate cleanup commands (review each; nothing has been executed) ---")
    any_cand = False
    for d in rows:
        if d["kind"] == "worktree" and d["cls"] == "MERGED" and d["stashes"] == 0:
            any_cand = True
            print(f"# fully merged, clean worktree:\n"
                  f"git -C <primary-checkout> worktree remove {shlex.quote(d['path'])}")
    for p in not_git:
        base = os.path.basename(p).lower()
        tag = "backup/copy-looking, " if any(h in base for h in SUSPECT_HINTS) else ""
        any_cand = True
        print(f"# {tag}not a git repo -- diff against the canonical checkout before deciding:\n"
              f"diff -rq {shlex.quote(p)} <canonical-checkout> | head -50")
    if not any_cand:
        print("# none -- nothing is an obvious retirement candidate")
    print("# DIVERGED or UNCOMMITTED entries need a human decision; "
          "list their unique commits with:\n"
          "# git -C <path> log --oneline <base>..HEAD")
    return 0


if __name__ == "__main__":
    sys.exit(main())
