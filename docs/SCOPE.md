# MUIOGO Headless: Skills Scope

Status: **founding scope of MUIOGO-AI** (July 2026). This document defines the
vision, architecture, skill inventory, and phased delivery plan for running
MUIOGO headless through a collection of agent skills. The work lives in this
research repo, separate from MUIOGO, and pieces are proposed upstream only once
they mature (see "Where things live" below).

## Vision

Today MUIOGO is operated through its web GUI. The headless vision is that every
workflow the GUI offers — and the analytical workflows around it — can be driven
by an agent (or a script) with no browser: install the app, calibrate an OG
country model, build and run CLEWs scenarios, run the linked OG-CLEWS workflow,
interpret the results, visualize them, and produce short analytical write-ups on
demand. A companion set of knowledge skills teaches users (and grounds agents)
on MUIOGO, CLEWs/OSeMOSYS, and the OG-Core model family.

This makes MUIOGO usable in three new modes:

1. **Agent-operated**: a country analyst asks in natural language for a scenario
   run and a briefing note; the skills do the rest.
2. **Scripted/reproducible**: batteries of runs, CI validation, and country
   deployments become scriptable and repeatable.
3. **Server-ready**: the same headless surface is what a future hosted MUIOGO
   needs anyway (see MUIOGO's README scalability note), so nothing here is
   throwaway.

## Architectural approach

**Skills drive the existing Flask API over HTTP.** They do not import backend
classes directly.

Rationale: the full workflow surface already exists as HTTP endpoints —
case CRUD, scenario management, parameter editing, data-file generation,
`/run` and `/batchRun`, results retrieval (`API/Routes/Case/`,
`API/Routes/DataFile/`), and the OG-Core install/calibration layer
(`API/Routes/OGCore/`, `/ogc/*`). Driving these endpoints exercises the same
code paths the GUI uses, so headless runs stay behaviorally identical to GUI
runs and every GUI fix benefits headless for free. Direct class imports would
create a second, drifting integration surface.

The stack, bottom to top:

```
skills (agent-facing, judgment + workflow)     → skills/          (this repo)
   │
muiogo client  (thin Python client + CLI;      → client/          (this repo)
   │            mechanical HTTP work, no judgment)
   │
Flask API      (existing; gets a headless      → MUIOGO repo, via normal
                server mode + small gap fixes)   issue-first PRs to main
```

The client/CLI is the enabling artifact: skills stay small and readable because
mechanical HTTP work (sessions, polling, file paths) lives in the client. It is
also independently useful to non-agent users.

### Where things live (repo organization)

- **This repo (MUIOGO-AI)** holds the research: skills under
  `skills/`, the `muiogo-client` package under `client/`, design notes
  under `docs/`, and studies under `experiments/`. Process is light: push to
  `main`, issues optional (see `README.md` working agreements).
- **MUIOGO** receives only the small enabling changes headless operation needs
  in the app itself (headless start flag, session fixes, endpoint gaps). Those
  are developed in MUIOGO under its own rules — issue first, feature branch,
  PR — and are useful to MUIOGO independent of this research.
- **MUIOGO is a pinned dependency** here: installed via
  `scripts/install-muiogo.sh` at the ref in `scripts/MUIOGO_PIN`, so everyone
  runs research against the same version.
- **Graduation path**: when a skill or the client is mature enough that every
  MUIOGO checkout should carry it, that is the signal to propose it upstream —
  as a deliberate PR, not a merge of research history.

## Phase 0 — Foundations (blocking everything else)

Verified gaps (July 2026, MUIOGO @ `3db8b816`) that headless operation needs
closed:

| Gap | Evidence | Fix | Where |
|---|---|---|---|
| Start scripts always open a browser | `scripts/start.sh:78-83`, `start.bat` | `--headless` / `--no-browser` flag; print URL instead | MUIOGO PR |
| Endpoints depend on a GUI-managed Flask session (`getSession`/`setSession` in `API/app.py`) | case/model selection is session state | Client manages the session cookie and sets case context explicitly; verify every endpoint works from a cold session | client here; fixes upstream if needed |
| No API client or CLI | — | Build `muiogo-client`: session handling, case/scenario CRUD, run + poll, results download | this repo |
| No machine-readable endpoint reference | — | Generate an endpoint inventory as part of client work | `docs/` here; upstream when stable |
| Results shaped for GUI consumption | `WebAPP/DataStorage/<case>/` layout | Document the results contract (CSV/JSON paths per run) so analysis skills read files, not the GUI | `docs/` here |

**Definition of done (Phase 0):** from a fresh clone of this repo, a script
with no browser can install MUIOGO at the pin, start the server, create a case
from the demo data, run it with GLPK or CBC, and download the result CSVs.

The install story (MUIOGO + OG models + ogclews-link + this repo, one line,
correct environments) is assessed and designed in `INSTALL_DESIGN.md`.

## The skill inventory

Ten capabilities from the vision, mapped to nine skills in four groups.

### Group A — Operate (Phase 1)

1. **`muiogo-install`** — install, verify, update, and repair a MUIOGO
   installation: wraps MUIOGO's `scripts/install.sh` / `install.ps1`, solver
   discovery (the four-tier chain in MUIOGO's `docs/ARCHITECTURE.md`),
   demo-data download and checksum, `uv sync`, and the smoke test. Output: a
   verified, running installation and a diagnosis when something is broken.
2. **`muiogo-run`** — the workhorse: start/stop the headless server, generate
   data files, launch `/run` and `/batchRun`, monitor `readLogFile`, detect
   solver failures, and collect outputs. Every other workflow skill calls
   through this one.
3. **`muiogo-scenarios`** — develop and run scenarios: create/copy cases, edit
   parameters and scenario data (`updateData`, `saveCase`, scenario ordering),
   build scenario matrices (e.g., carbon-price × demand-growth grids), and
   batch-execute them via `muiogo-run`.

### Group B — OG integration (Phase 2)

4. ~~**`og-calibrate`**~~ — covered by `og-country-calibration`, installed in
   `skills/`.
5. **`og-clews-linked-run`** — run CLEWs and OG-Core coupled: hand OSeMOSYS
   results (energy investment, prices, emissions) to OG-Core inputs and
   vice versa, execute both, and reconcile. **Dependency:** the linkage engine
   is the core MUIOGO project deliverable and is still being built (only the
   install/calibration layer exists in `API/Classes/OGCore/` today). The skill
   lands in two steps: (a) an interim version that does the data hand-off
   explicitly through files, which doubles as a spec for the engine; (b) a
   thin wrapper once the in-app linkage exists.

### Group C — Analyze (Phase 3, parallelizable with Phase 2)

6. **`muiogo-interpret`** — read run outputs (result CSVs, `Duals.json`,
   `Indicators.json`), check solution health (infeasibilities, binding
   constraints, suspicious shadow prices), compare scenarios, and produce a
   structured findings summary.
7. **`muiogo-visualize`** — standard chart set from results (capacity
   expansion, generation mix, emissions trajectories, water/land use, OG macro
   paths), rendered headless to files/HTML artifacts with a consistent style.
8. **`muiogo-brief`** — short analytical outputs on demand: a 1–3 page policy
   brief or technical note from one or more runs, combining `muiogo-interpret`
   findings and `muiogo-visualize` charts, in plain language for policymakers.

### Group D — Teach (Phase 4, independent)

9. **`muiogo-tutor`** and **`og-clews-tutor`** — training skills, in two
   senses: (a) interactive guided onboarding for a new user or contributor
   (MUIOGO workflows; CLEWs/OSeMOSYS and OG-Core concepts and model families),
   and (b) canonical grounding so agents answer from the project's actual docs
   and model structure rather than from memory. Content sources: MUIOGO repo
   docs, the wiki's background material, OSeMOSYS and OG-Core documentation.

## Phasing and milestones

| Phase | Delivers | Depends on | Definition of done |
|---|---|---|---|
| 0. Foundations | headless server mode (upstream), `muiogo-client` + CLI, endpoint + results contract docs | — | cold-start scripted run passes (see above) |
| 1. Operate | skills 1–3 | Phase 0 | agent installs MUIOGO, builds a 2×2 scenario matrix on demo data, runs it, collects results — no browser, no human clicks |
| 2. OG integration | skills 4–5 (5 in interim file-handoff form) | Phase 0; linkage engine for 5b | agent installs a country calibration and completes one documented interim linked run |
| 3. Analyze | skills 6–8 | Phase 1 outputs | agent produces a correct, chart-bearing brief from a scenario matrix, verified against hand-checked numbers |
| 4. Teach | skill 9 pair | none (content work) | a new user completes a guided first run via the tutor alone |

Sequencing notes: Phases 2–4 are independent of each other and can proceed in
parallel once their dependencies exist. The interim linked-run work in Phase 2
is deliberately positioned to inform the linkage-engine design rather than
wait for it.

## Non-goals (this workstream)

- Building the OG-CLEWS linkage engine itself — that is the main MUIOGO
  roadmap; this workstream consumes it and, via the interim hand-off, informs it.
- Rewriting or decoupling the GUI. Headless drives the same API the GUI uses.
- A hosted/server deployment. The headless surface is a prerequisite for that
  future, but deployment is out of scope here.
- Duplicating personal method skills (e.g., calibration judgment) into the
  repo — repo skills carry execution mechanics; methodology skills stay
  separable.

## Assumptions to confirm

1. "Training" in the vision = tutoring/grounding skills (Group D), not
   fine-tuning an ML model on model outputs.
2. The interim file-based OG↔CLEWs hand-off is acceptable as a Phase-2
   deliverable ahead of the in-app linkage engine.

## History

Originally drafted 2026-07-26 in the MUIOGO repo (branch
`feature/headless-skills-scoping`, since retired); moved here at the founding
of MUIOGO-AI with the repo-organization and client-location sections revised
for the separate-repo model.
