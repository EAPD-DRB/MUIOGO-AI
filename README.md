# MUIOGO-AI

Side research on running [MUIOGO](https://github.com/EAPD-DRB/MUIOGO) headless
through a collection of agent skills: install it, calibrate OG country models,
build and run CLEWs scenarios, run linked OG-CLEWS workflows, interpret and
visualize the results, and produce short analytical write-ups — all without the
GUI.

This repo is exploratory and separate from MUIOGO on purpose. Nothing here is
proposed for MUIOGO's `main` until it has proven itself; when a piece matures,
it is offered upstream through MUIOGO's normal issue + PR process. MUIOGO is
treated as an installed dependency (pinned, see `scripts/`), never as a code
import: everything drives its HTTP API, the same surface the GUI uses.

Start with [docs/SCOPE.md](docs/SCOPE.md) — the vision, architecture,
skill inventory, and phased plan.

## Layout

- `docs/` — scope, design notes, decisions
- `.claude/skills/` — the agent skills (the heart of the project)
- `client/` — `muiogo-client`, a thin Python client + CLI for the MUIOGO HTTP API
- `experiments/` — scenario studies, notebooks, throwaway explorations
- `scripts/` — setup helpers, including the pinned MUIOGO installer

## Working agreements

This is a research repo, so process is deliberately light:

- Pushing to `main` is fine; branches are for anything you want eyes on first.
- Issues are optional; write findings down in `docs/` or `experiments/` instead
  of letting them live in chat threads.
- The one hard rule: the client and skills talk to MUIOGO over HTTP only —
  no imports of MUIOGO's backend classes. That keeps this work honest
  (identical behavior to the GUI) and upstreamable.

## Getting started

One command installs and verifies the whole headless stack — MUIOGO (with
solvers and demo data), optional OG country model(s), and ogclews-link — each
via its own upstream installer, each in its own environment:

```bash
./scripts/install.sh --og og-phl
```

Flags: `--dest DIR` (workspace, default `~/muiogo-ai-workspace`), `--og
KEYS|none`, `--og-home DIR`, `--no-link`, `--no-demo-data`, `--port N`. The
run ends with a verification battery (demo case solves with CBC, OG models
import from their own venvs, link `--check` passes) and writes
`<workspace>/manifest.json`, which skills read to find every component.
Resume-safe: re-running skips finished steps. See `docs/INSTALL_DESIGN.md`
for the assessment behind it.

Working on the repo itself: read `docs/SCOPE.md`, pick a phase item, and go.

## License

Apache License 2.0 (`LICENSE`), same as MUIOGO.
