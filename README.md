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

1. Install MUIOGO at the pinned version: `./scripts/install-muiogo.sh`
2. Read `docs/SCOPE.md`, pick a phase-0 item, and go.

## License

Apache License 2.0 (`LICENSE`), same as MUIOGO.
