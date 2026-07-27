---
name: og-repo-fleet-sync
description: >-
  Apply one change across the OG-Core country-repo fleet (OG-USA, OG-PHL, OG-ZAF, OG-IDN, OG-BRA,
  OG-ETH, OG-FJI and variants) and track which repos have it. Use whenever a fix or upgrade needs
  to propagate to more than one country repo: a dependency break (the pandas-datareader/pandas-3
  class), a CI workflow update, an AGENTS.md/docs revision, a ruff or conda→uv migration, a shared
  test or packaging fix. Also use when asked "which repos still need X?" or when a fix proven in
  one repo should be rolled out to siblings. Prepares per-repo branches and commits; never pushes
  or opens PRs without asking.
---

# OG repo fleet sync

Generalized from the pandas-3 import-fix rollout (`~/Projects/PANDAS3_IMPORT_FIX_PLAYBOOK.md`,
the worked instance — read it when you want a full example of the level of detail a playbook
should reach). The problem this solves: ~20 sibling repos drift apart because changes land in one
repo and propagate by hand, or never (the conda→uv drift is the standing cost of not doing this).

## The shape of the work

Never loop "fix repo, next repo" from memory. Four phases, with a written artifact between each:

### 1. Characterize the change once — write the playbook

From the repo where the fix is already proven (or being developed), write a short playbook file
before touching a second repo. It must contain, concretely:

- **Detection**: a command that decides "is this repo affected?" mechanically, e.g.
  `rg -n "pandas_datareader|wb\.download" .` plus a smoke probe
  (`.venv/bin/python -c "import <pkg>"`). Detection must be runnable read-only.
- **Fix pattern**: the minimal change, as a pattern, not a diff — repos differ in package name
  (`ogphl`/`ogzaf`/...), layout, and idiom, so a blind cherry-pick is usually wrong.
- **Semantic assumptions to preserve**: the non-obvious invariants the fix must not break. (In the
  worked instance: descending date order mattered because downstream used `pct_change(-1)` —
  transport-level replacement, semantic-level bug.)
- **Tests to add** (e.g. an import smoke test) and **validation commands** — the repo's own
  (`uv run python -m pytest -m 'not local' -q`, `black --check`/`make format`), not a generic set.
- **Scope boundary**: what is explicitly Phase-2 cleanup (design changes, gating, docs refactors)
  that goes to follow-up issues, never into this rollout.

### 2. Probe the fleet — build the tracking table

Enumerate the fleet fresh (`ls -d ~/Projects/OG-*`), and separate **canonical checkouts** from
worktrees/`_bak`/`copy` dirs — sync canonical checkouts only (the `worktree-orchard` skill is the
disambiguator when sprawl makes this unclear). Run detection read-only on every repo and write the
tracking table to a file (it outlives the session — put it next to the playbook, never inside a
country repo):

| repo | org | affected? | already fixed? | branch | status | notes |
|---|---|---|---|---|---|---|

Statuses: `unaffected` / `already-fixed` / `branch-ready` / `blocked` / `needs-decision`.
Fleet facts that change the work per row: EAPD-DRB repos (PHL/ZAF/IDN/ETH/FJI) share the uv +
Dependabot-lock convention — **never commit a `uv.lock` change from sync work**; PSLmodels repos
(USA/BRA) differ in tooling and review culture. Record the org.

### 3. Apply per repo — fresh branch, minimal scope, repo's own validation

Per affected repo:

1. `git fetch` first; branch off the up-to-date default branch (`git switch -c <change>-<slug>`).
   Never work on a repo's default branch directly.
2. Re-run detection *in this repo* and read the actual code — expect the pattern to vary. The
   worked instance's second repo lesson: fixing the primary import exposed a *second* import-time
   side effect that also had to move; the smoke test, not the plan, decides when you're done.
3. Apply the minimal fix; add the playbook's tests; run the repo's own validation commands.
   Distinguish *your* failures from pre-existing ones — several repos carry unrelated CI/test
   debt; note pre-existing failures in the table rather than fixing them (scope boundary).
   Distrust old green tests near your change (the worked instance found a
   `list(x).sort() == y.sort()` test that compared `None == None`).
4. Commit with a single-line message; update the tracking table row to `branch-ready`.

### 4. Report and ask — never push, never PR, on your own

When the sweep is done (or blocked), present: the tracking table, a per-repo diffstat, and any
`needs-decision` rows. Everything up to here — local branches and local commits — is preparation;
nothing has left the machine. Then the gates, in order and each with its own explicit approval:

1. **Ask which repos to push.** Never push all branches on one blanket "go ahead"; the user names
   the repos (or explicitly approves the batch as a batch).
2. **After pushes succeed, ask again before opening any PR** — pushing and PR-opening are never
   one step. Show each PR's draft text first. A PR for a PSLmodels repo may warrant different
   framing than an EAPD-DRB one.
3. **Never merge anything**, ever — merges are the user's alone.

Opening N PRs across a fleet is exactly the "expensive and expansive" action the family's
approval gates exist for (the OG family README): the skill's deliverable is the prepared
branches, drafted PR texts, and the tracking table — not the outbound actions. If PRs are
approved: per-repo PR text follows the playbook (what/why/tested), with Phase-2 items filed as
follow-up issues, not folded in.

## Standing rules

- The tracking table is the deliverable as much as the branches — a half-done sweep with an
  accurate table is resumable; a half-done sweep in memory is lost.
- Mechanical work repeating across 3+ repos gets a script (detection sweeps especially); judgment
  (adapting the fix, reading validation output) stays manual per repo.
- Secrets (`un_api_token.txt` sits in several working trees) must never end up in commits, diffs,
  or the playbook.
- If a repo's fix stops being minimal (architecture fights back, third attempt), stop — mark
  `needs-decision` with the evidence and move on; don't sink the fleet sweep into one repo.
