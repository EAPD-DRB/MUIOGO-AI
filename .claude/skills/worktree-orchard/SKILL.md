---
name: worktree-orchard
description: "Inventories checkout sprawl for a project family under the projects root (default ~/Projects): every clone, git worktree, _bak, copy and holding-pen folder, with which are merged, diverged, dirty or dead. Use when asked which checkouts of a repo exist, which worktrees can be deleted, or whether a copy is stale, and before an og-repo-fleet-sync sweep. Read-only; cleanup is only ever listed as commands for the user to review and run."
---

# Worktree orchard

The standing problem: 22+ registered worktrees plus backup/copy dirs accumulate under
`~/Projects`, and knowing which are merged, diverged, dirty, or dead requires re-deriving it by
hand each time. This skill makes the inventory a one-command, read-only operation.

## Which world

This skill deliberately works across the user's **own** checkouts — the adopted setup —
because inventorying and reconciling them is the whole point. That makes it the one
place where crossing is intended, so be explicit: name the checkouts you looked at
and the world they belong to, and never touch the runtime installation's copies
under a world's `og-models` directory unless the user asked. Never present a live
checkout's state as if it were the installation's. Full rules:
`../WORLD_DISCIPLINE.md`.

## Run the inventory

```bash
python3 scripts/orchard.py --family OG-PHL            # one family (matches OG-PHL*)
python3 scripts/orchard.py --family "OG-*"            # the whole OG fleet
python3 scripts/orchard.py --family "*bak*" --root ~/Projects
```

The script (stdlib-only, strictly read-only) finds name-matching checkouts, follows each
checkout's `git worktree list` to catch worktrees living elsewhere (including hidden ones under
`<repo>/.claude/worktrees/`), and flags matching non-git dirs. Per entry: branch, HEAD, dirty
count, stashes, ahead/behind the default branch, last commit date, and a class:

- `MERGED` — HEAD is an ancestor of the default branch, tree clean → retirement candidate.
- `DIVERGED` — has commits the default branch lacks → needs a decision (merge/PR/abandon).
- `UNCOMMITTED` — dirty tree (trumps everything; verified live: dirty-but-merged worktrees
  classify as UNCOMMITTED, not MERGED).
- `NOT-GIT` — a matching dir that isn't a checkout (the `_bak` / `copy` / `holding pen` class).

It ends with candidate cleanup commands — **printed, never executed**.

## Judgment layer (yours, not the script's)

- **Retire only from the MERGED + no-stash list**, and even then check the worktree isn't the
  target of something live: an editable install (`og-run-preflight` finds those), an
  `og_model_registry.json` `env_python`/`source_dir` entry (ogclews points at a PHL worktree), a
  cron job, or an open PR branch. A merged-looking worktree that a registry points at is
  load-bearing, not dead.
- **DIVERGED worktrees**: list their unique commits (`git log --oneline <base>..HEAD`) and decide
  per branch: PR-worthy → propose a PR (ask first, house rules); experiment concluded → recommend
  deletion *by listing the command*; unclear → leave, note in the report.
- **NOT-GIT copy dirs**: never recommend deletion on name alone. Diff against the canonical
  checkout first; if the copy contains unique files (data, tokens, half-finished work), say
  exactly which files before any retirement talk. Watch for secrets (`un_api_token.txt` has
  turned up in copies) — flag, don't copy or quote them.
- **Ahead/behind is measured against `upstream/<default>`** when that remote exists, else
  `origin/<default>`, else the local branch, in that order; the BASE column shows which. Those
  refs are only as fresh as the last fetch, and `upstream/<default>` can be older than
  `origin/<default>` if only one was fetched: `git fetch --all` (a read operation on the remotes, safe) before
  trusting close calls. A fetch updates the local remote-tracking refs; if nothing local may
  change at all, `git ls-remote` reads the remote heads without touching anything.
- **Stashes are per repository, not per worktree:** every worktree of one repo shows the
  repo's total. Check `git stash list` to see which branch each stash belongs to.
- **Squash-merged branches always read DIVERGED.** A squash merge leaves the branch's commits
  off the default branch, so check the PR state (`gh pr list --state merged --head <branch>`)
  before calling a DIVERGED branch unmerged work.
- **Report format**: lead with the counts (N checkouts, M worktrees, K candidates), then the
  table, then per-candidate reasoning. The deliverable is the decision support, not the raw table.

## Hard rule

This skill never deletes, prunes, or removes anything itself — not even with user approval in the
moment; it produces the reviewed command list and the user runs it. That asymmetry is the point:
inventory is cheap and safe to repeat, deletion is not.
