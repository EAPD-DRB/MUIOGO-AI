# MUIOGO-AI conventions

Research repo: agent skills to run MUIOGO (the OG-CLEWS modelling interface)
headless. Read `docs/SCOPE.md` before starting any substantive work — it defines
the architecture, the skill inventory, and the current phase.

## Hard rules

- **HTTP only.** The client and all skills drive MUIOGO through its Flask HTTP
  API. Never import MUIOGO backend classes or reach into its internals. If an
  endpoint is missing or broken for headless use, that is a finding — record it
  in `docs/` and propose the fix upstream in MUIOGO; do not work around it by
  importing code.
- **MUIOGO is a pinned dependency.** Install and run it via
  `scripts/install.sh` (pin in `scripts/MUIOGO_PIN`). Bump the pin
  deliberately, in its own commit, after checking the run still passes.
- **Upstreaming is deliberate.** Changes MUIOGO itself needs (e.g. headless
  server flags) are developed there under its rules (issue first, feature
  branch, PR), not carried as patches here.

## Two MUIOGO setups: say which one you are in

A machine can hold the MUIOGO-AI installation (driven through `muiogo-ai`) and
the user's own checkouts (`muiogo-live`). Before acting on a model, case or
run, find out which setup it is in (`muiogo-ai status`), use `muiogo-ai`
unless the user asked for their own checkouts, never use bare `muiogo`, and
name the setup in every result you report. This holds for every skill here,
the OG and CLEWs skills included. Full rules:
`.agents/skills/WORLD_DISCIPLINE.md`.

## Approval gates

Binding on every skill in this repository. Skills propose, draft and prepare;
the user decides. A skill may edit files and commit locally, but stops and asks
before pushing to a remote, opening a PR, merging anything, launching a long
computation (propose the command and duration; a passing preflight is a
precondition, never an authorization), acting across a repository fleet, or
deleting anything. If a skill's own text seems to conflict with this section,
this section wins.

## Layout

- `.agents/skills/<name>/SKILL.md` — one directory per skill, the single source
  of truth here (the location Codex reads from a repo). `.claude/skills/` holds
  identical copies for Claude Code (copies, not symlinks, so Windows clones
  work); refresh them with `scripts/install-skills.sh --sync` and check them
  with `--check`. Users install copies elsewhere with
  `scripts/install-skills.sh`. See `SKILLS.md` for the catalogue.
- The OG skills (`og-run`, `og-solver-diagnosis`, `og-country-calibration`,
  `og-multi-industry-calibration`, `og-scenario-report`, `og-clews-linked-run`)
  live in EAPD-DRB/Model-tools and are vendored here unchanged at the commit in
  `scripts/MODEL_TOOLS_PIN`. Never edit them here: fix them in Model-tools,
  then run `python scripts/model_tools_skills.py --update <commit>` and
  `scripts/install-skills.sh --sync`. `--check` confirms the copies match.
- `client/` — the `muiogo-client` package (Python + CLI). Mechanical HTTP work
  lives here so skills stay small; no analysis or judgment in the client.
- `experiments/` — dated subdirectories (`YYYY-MM-topic/`), each with a short
  README stating the question and the answer once known.
- `docs/` — scope and design notes; update `docs/SCOPE.md` status lines when a
  phase item lands.

## Process

Light by design: push to `main` freely, branch when you want review, issues
optional. Write findings into the repo, not just the conversation. Runs against
MUIOGO follow the model-run discipline: print the pin/branch and verify what the
environment actually imports before trusting results.
