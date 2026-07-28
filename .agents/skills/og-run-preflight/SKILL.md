---
name: og-run-preflight
description: >-
  Mandatory preflight before launching ANY OG-Core / CLEWS model computation — a steady-state or
  TPI solve, an example script (run_og_*.py), a battery, an ogclews-link run, or any long
  computation that imports ogcore or a country package (ogphl/ogzaf/ogidn/ogbra/ogeth/ogusa) or
  ogclews_link. Use it the moment a session is about to launch such a run, even if the environment
  "looks right" — it verifies branch+HEAD of every repo involved, that the interpreter imports the
  intended worktree's code (all three shadowing vectors), and that each worktree has its own venv.
  Also use when a run result looks contaminated or reproduces a known-buggy number.
---

# OG run preflight

A battery once silently ran a whole night on stale code from another worktree (2026-07-07,
contaminated golden records). The cause was import shadowing — invisible at launch, expensive to
discover. This skill exists so that never recurs: **no solve, battery, or long computation gets
launched without a GO from the preflight script.** "It looks right" is not a check.

## The rule

Run `scripts/preflight.py` (bundled, stdlib-only) before every launch. It is deterministic and
read-only. If it prints `NO-GO`, do not launch — fix the failure, re-run the preflight, and only
launch on `GO`. Never work around a failure by hand-editing `sys.path` or exporting `PYTHONPATH`;
fix the environment the failure points at.

```bash
python3 scripts/preflight.py \
  --check <REPO>::<pkg>[,<dep-pkg>...][::<venv-python>] \
  [--check ...] \
  --run-cwd <dir the run launches from> \
  --entry-script <script the run executes>
```

- One `--check` per repo/environment involved in the run.
- First package name = the repo's own package (must resolve **inside** the repo).
  Comma-separated extras (e.g. `ogcore`) must resolve inside the repo or its venv — never a
  sibling checkout.
- `<venv-python>` defaults to `<REPO>/.venv/bin/python`.
- Always pass `--run-cwd` and (when the run executes a script) `--entry-script`: a plain `-c`
  probe alone does **not** reproduce script-dir shadowing, so probe with the run's own invocation
  style. Console scripts are immune to cwd shadowing; `python script.py` and `python -c` are not.

Single-repo example (country model):

```bash
python3 scripts/preflight.py \
  --check ~/Projects/OG-PHL::ogphl,ogcore \
  --run-cwd ~/Projects/OG-PHL \
  --entry-script ~/Projects/OG-PHL/examples/run_og_phl.py
```

Cross-env example (ogclews-link, which subprocesses the OG model's own interpreter): one `--check`
per environment, with the OG side's interpreter taken from the model registry
(`og_model_registry.json` → `env_python`, `source_dir`) — not from memory:

```bash
python3 scripts/preflight.py \
  --check ~/Projects/ogclews-link::ogclews_link \
  --check <registry source_dir's repo root>::ogphl,ogcore::<registry env_python> \
  --run-cwd ~/Projects/ogclews-link \
  --entry-script ~/Projects/ogclews-link/experiments/run_battery.py
```

The link env must NOT import ogcore — so ogcore goes on the OG side's check line only.

## What the script verifies (and what a failure means)

| Check | Failure means | Fix |
|---|---|---|
| git branch + HEAD printed per repo | (informational — but confirm it's the branch you *intend*, not just any branch) | `git switch` in the right worktree |
| venv prefix inside the repo | shared/foreign venv; per-worktree-venv rule broken | `python -m venv .venv && .venv/bin/pip install -e .` in that worktree |
| import from neutral cwd lands in repo | **editable install points at another worktree** | `pip install -e <repo>` with that venv's pip |
| import from `--run-cwd` lands in repo | **cwd shadowing** — launching from another checkout's root imports THAT checkout | launch from the worktree under test, or use the console script |
| import with entry-script dir at `sys.path[0]` lands in repo | **script-dir shadowing** | move/rename the shadowing package next to the script, or pin+assert in the script |
| extra packages resolve in repo or venv | a sibling checkout is bleeding into the dependency | reinstall the dependency in this venv |

Uncommitted changes are a WARN, not a FAIL — sometimes you *mean* to run dirty code. Say so out
loud before launching: "running with N uncommitted changes in <repo>."

## Judgment calls the script can't make

- **The branch check is only mechanical halfway.** The script prints branch+HEAD; *you* must
  confirm it's the branch the experiment is supposed to test. Compare against the task's intent,
  not against what's checked out.
- **Entry scripts for anything battery-grade should pin and assert**: `sys.path.insert(0, REPO)`
  then assert the resolved `<pkg>.__file__` is under `REPO` (pattern:
  `ogclews-link/experiments/run_battery.py`). The preflight catches a bad launch; the in-script
  assert catches a bad *re*-launch weeks later.
- **Run as a user would**: the documented CLI from the checkout's own env. If the preflight only
  passes under some ad-hoc invocation, the environment is wrong, not the preflight.
- **A GO is a precondition, not an authorization.** This skill never launches the run itself.
  SS solves are minutes; TPI runs and batteries are much longer and invisible while running.
  After a GO, propose the exact launch command with its expected duration and wait for the
  user's explicit call (house approval gate — see the OG family README).
- **Contamination heuristic (post-run, standing):** if a fresh run reproduces a number from a
  known-buggy earlier run, assume the wrong code ran. Stop, re-run the preflight, and never
  commit or bless those outputs.
