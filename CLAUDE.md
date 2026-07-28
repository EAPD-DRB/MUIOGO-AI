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

## Layout

- `.agents/skills/<name>/SKILL.md` — one directory per skill, the single source
  of truth (the Agent Skills standard location Codex reads from a repo).
  `.claude/skills/<name>` is a symlink to each one, the per-entry form Claude
  Code supports; rebuild with `scripts/install-skills.sh --relink` after adding
  or renaming a skill. Users install copies elsewhere with
  `scripts/install-skills.sh`. See `SKILLS.md` for the catalogue, canonical
  homes, and approval gates.
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
