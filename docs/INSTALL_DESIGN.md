# One-line installer: assessment and design

Goal: one command takes a clean machine to a fully working headless OG-CLEWS
stack — MUIOGO (headless), solvers, OG country model(s), ogclews-link, and the
muiogo-ai client/skills — with every component in its correct, isolated
environment, verified at the end.

Assessed 2026-07-27 by reading and (where noted) running the actual installers.
MUIOGO @ `3db8b816` (the pin), ogclews-link @ local checkout, OG universal
installer @ PSLmodels/OG-Core master.

## 0. Verification log (2026-07-27, macOS)

Run-verified, not just read:

- **MUIOGO upstream installer, headless end-to-end**: fetched
  `install.sh` from EAPD-DRB/MUIOGO main, ran `--dest <dir> --yes`
  non-interactively to completion ("MUIOGO is installed and ready"); the fresh
  install answered `/getCases` → `["CLEWs Demo"]`. Two behaviors confirmed by
  execution: `--dest` must be an existing **parent** directory (the clone
  lands at `<dest>/MUIOGO`), and `--yes` really does auto-start the app and
  open a browser (finding #1) — the process had to be killed by port lookup.
- **OG universal installer, headless**: fetched from PSLmodels/OG-Core master
  and ran `--list-json` locally (catalog: og-core, og-eth, og-zaf, og-idn,
  og-phl, og-bra). A full country install was NOT run (multi-minute, ~GB) —
  its non-interactive flags are verified from its own usage text and from the
  two wrappers below.
- **MUIOGO delegates to the upstream OG installer** (code):
  `API/Classes/OGCore/Installer.py` downloads the script from the PSLmodels
  raw URLs in `Config`, caches it, and invokes
  `bash install.sh --dest … --yes --no-log --repo <key>` under
  `ogc_clean_env()`.
- **ogclews-link delegates to the same upstream installer** (code):
  `scripts/setup.sh` uses a local `../OG-Core/scripts/install.sh` if present,
  else curls the PSLmodels raw URL.
- **ogclews-link installer, headless**: repo is public, `setup.sh` fetchable
  raw, contains zero `read` prompts; ran `--check` (correctly reported no
  venv) then full `setup.sh` (created the venv, verified the CLI); the
  `ogclews-link` CLI (`run`, `list`, `channels`, `models`) works.

Post-install interfaces available to skills: MUIOGO → HTTP API;
OG model → `<model>/.venv/bin/python` (subprocessed, never imported);
link → `ogclews-link` CLI + `OGCLEWS_*` env vars + its model registry.

## 1. What exists today (component inventory)

### MUIOGO installer — `MUIOGO/scripts/install.sh` (+ `install.ps1`)

- Steps: check git → install uv → provision Python → clone → `uv sync` →
  solvers (GLPK/CBC via OS package manager, `setup_dev.py`) → demo data
  (cached, SHA-256-verified) → step-report table → offer to start the app.
- Non-interactive: `--yes`; also `--dest`, `--branch`, `--repo-url`,
  `--no-demo-data`, `--skip-uv-install`, `--log`.
- Environment: `<MUIOGO>/.venv` (uv-managed).
- **Composition blocker:** with `--yes`, the final "Start MUIOGO now?" prompt
  auto-answers **yes** — the installer opens a browser and blocks running
  `API/app.py` in the foreground (install.sh:454-469). There is no
  `--no-start`. This is the one thing that prevents clean scripted composition.

### OG universal installer — `PSLmodels/OG-Core/scripts/install.sh` (+ `.ps1`, `repos.json`)

- Steps per repo: install uv → clone → `uv sync --extra dev` → verify import.
- Fully scriptable: `--repo og-phl[,og-zaf,...] | --all`, `--dest`, `--yes`,
  `--branch`, `--repo-url`, `--no-dev-deps`, `--skip-uv-install`, `--no-log`,
  `--list-json` (machine-readable catalog: og-core, og-eth, og-zaf, og-idn,
  og-phl, og-bra as of today).
- Environment: `<dest>/<OG-Repo>/.venv` — one venv per model.
- **Constraint:** refuses to run inside an active venv/conda env. MUIOGO
  already handles this by spawning it with a stripped environment
  (`Config.ogc_clean_env()`); any composed installer must do the same.
- MUIOGO drives this same installer through its `/ogc/installCalibration` API
  and records installs in its registry (`~/.muiogo/og-state/`, models at
  `~/.muiogo/og-models/<Repo>/` by default).

### ogclews-link — `ogclews-link/scripts/setup.sh` (+ `test-drive.sh`)

- The link is deliberately ogcore-free: its own small uv venv
  (numpy/pandas/scipy/openpyxl/matplotlib); to solve, it **subprocesses the OG
  model's own interpreter**. Correct-environments discipline is already built
  into its design.
- `setup.sh`: creates the link venv, verifies the CLI, registers OG models —
  `--og-path <dir>` (existing checkout), `--install-og <key>` (fetches via the
  upstream universal installer), `--check` (verify only). Registry:
  `og_model_registry.json` / `$OGCLEWS_MODEL_REGISTRY`.
- `test-drive.sh`: **already a working prototype of a composed one-liner** —
  zero-input, resume-safe (every step skips itself if done), takes a clean
  machine to a solved coupled Philippine example. The muiogo-ai installer
  should copy its structure.
- Country/case configuration is data, not code: `ogclews_countries.json`.
- No Windows script yet (bash only).

## 2. Environment topology (what "correct environments" means)

Everything the installer creates lives under **one master directory**, default
`~/muiogo-ai`, so it never competes with checkouts used for live work:

```
~/muiogo-ai/                          the master directory (--dest)
  MUIOGO/.venv                        MUIOGO app (Flask, waitress, ...)
  og-models/<OG-XXX>/.venv            one env per OG country model (uv)
  og-state/                           THIS installation's OG registry + jobs
  ogclews-link/.venv                  link env (small; never imports ogcore)
  manifest.json                       what is installed and where
~/.muiogo/manifest.json               a pointer, so any directory can find it
system (brew/apt/dnf)                 GLPK + CBC solver binaries
```

Isolation rules that must survive composition: the OG installer runs with a
clean env (no active venv); the link never shares an env with OG models or
MUIOGO; solvers are system-level and resolved by MUIOGO at request time.

### Why the registry lives inside the master directory (verified 2026-07-28)

MUIOGO's OG registry is a dict **keyed by country code** — `{"calibrations":
{"PHL": {...}, "ZAF": {...}}}` — so it holds exactly one entry per country.
Registering a second clone of OG-PHL overwrites the first. With the registry at
the shared default `~/.muiogo/og-state/`, installing an isolated OG-PHL would
silently displace the one someone uses for live work.

A new MUIOGO install does **not** get its own registry automatically. Config.py
resolves it as `MUIOGO_OG_DATA_DIR` or, failing that, the user-level
`~/.muiogo/og-state` — deliberately, so the CLEWs case picker never sees it
(MUIOGO issue #500). So every MUIOGO on the machine shares one registry unless
that variable is set.

Setting it as a process environment variable is not enough either: it would only
apply when MUIOGO is started through our tooling, and the same install started
by its own `start.sh` would silently fall back to the shared registry.

The resolution is MUIOGO's own configuration mechanism. `Config.py` calls
`load_dotenv()`, so the installer writes into `<master>/MUIOGO/.env`:

```
MUIOGO_OG_DATA_DIR=<master>/og-state
MUIOGO_OG_MODELS_DIR=<master>/og-models
```

That holds however MUIOGO is launched — `muiogo serve`, its own `start.sh`, or
the GUI — because all of them run from the MUIOGO root, where `load_dotenv()`
looks. Verified: `load_dotenv()` picks those values up from a `.env` beside the
app.

Two clones of the same country can then coexist, each registered in its own
workspace, with `MUIOGO_WORKSPACE` selecting which one the tooling uses.

**Only for installations the installer creates.** A checkout that was already
there keeps whatever registry its owner configured; rewriting someone's `.env`
would change how their own MUIOGO behaves. Adopted setups therefore keep the
shared `~/.muiogo/og-state`, which is what their GUI expects.

Multiple clones are otherwise unproblematic: git keeps no machine-level record
of them, so a repo may be cloned any number of times, on different branches.
The two things that do bite are disk (an OG country model is 0.7–2.8 GB) and
Python shadowing — every clone needs its own `.venv`, and a run must use that
checkout's interpreter, which is what `og-run-preflight` checks.

## 3. Integration findings (gaps the plan must close)

1. **MUIOGO installer auto-starts the app under `--yes`** (browser + blocking
   foreground). Fix upstream: a `--no-start` flag — a small, generally useful
   PR (pairs with the `--headless`/`--no-browser` start.sh flag already in
   SCOPE Phase 0). Interim: the orchestrator can treat the auto-start as its
   smoke test — poll the port, verify, then stop the process — but the flag is
   the honest fix.
2. **Registry location skew:** ogclews-link discovers MUIOGO-installed OG
   models by reading `WebAPP/DataStorage/OGCore/og_calibrations_installed.json`
   (`ogclews_link/registry.py:151`), but MUIOGO moved that registry to
   `~/.muiogo/og-state/` (MUIOGO issue #500). At the pin, the link's MUIOGO
   auto-discovery is silently broken. Fix in ogclews-link: read the new
   location (fall back to the old one).
3. **Private-repo one-liner:** while MUIOGO-AI is private, `curl` against
   raw.githubusercontent.com fails without a token. Two forms needed:
   - while private: `gh repo clone EAPD-DRB/MUIOGO-AI && MUIOGO-AI/scripts/install.sh`
   - when public: `/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/EAPD-DRB/MUIOGO-AI/main/scripts/install.sh)"`
4. **Windows:** MUIOGO and the OG installer have `.ps1` twins; ogclews-link
   does not. macOS/Linux first; Windows follows the same design later.
5. **GLPK path broken in MUIOGO at the pin** (documented in
   `API_ENDPOINTS.md`; fix filed upstream). Installer verifies with CBC.
6. **OG model branch pins:** real work sometimes needs a model on a specific
   branch/PR (e.g. OG-PHL multi-industry `m8`). The universal installer
   supports `--branch`; the manifest must record what was installed.

## 4. Design: `muiogo-ai install`

One orchestrator script, `scripts/install.sh` in this repo. It **delegates to
each component's own installer** — it never reimplements their steps — and
adds ordering, clean-env handling, a manifest, and end-to-end verification.
Structure copied from `test-drive.sh`: zero-input with flags, resume-safe,
every step idempotent, step-report table at the end.

### Workspace layout (default `~/muiogo-ai`, `--dest` to change)

```
<workspace>/
  MUIOGO-AI/        this repo (skills, client, docs)
  MUIOGO/           pinned checkout via MUIOGO's installer
  ogclews-link/     link repo + its venv
  manifest.json     what was installed, where, at which ref (see below)
```
OG models go to MUIOGO's default (`~/.muiogo/og-models/`) so the GUI, the
link, and the skills all see the same single registry.

### Steps

1. **Preflight**: git/curl present; no active conda/venv (or strip and warn);
   supported OS; disk space sanity.
2. **MUIOGO-AI**: clone (or `git pull` if present); `uv sync` in `client/`.
3. **MUIOGO**: run its installer with `--dest <workspace> --yes` at the ref in
   `scripts/MUIOGO_PIN` (installer lacks a pin concept: clone step passes
   `--branch` or checks out the pin after; solvers + demo data ride along).
   With the upstream `--no-start` flag, no browser ever opens; until then, the
   orchestrator absorbs the auto-start as its health probe and stops the
   process.
4. **OG models** (`--og og-phl,og-eth`, default none): start MUIOGO headless
   via `muiogo serve`, then install each model through **MUIOGO's
   `/ogc/installCalibration` API** with the client. Rationale: reuses MUIOGO's
   clean-env wrapper, its registry, and its job logging — and honors this
   repo's HTTP-only rule. Models land in `~/.muiogo/og-models/`, registered
   where every consumer looks.
5. **ogclews-link** (`--with-link`, default on when `--og` given): clone; run
   `./scripts/setup.sh`; register the just-installed model(s) via
   `--og-path ~/.muiogo/og-models/<Repo> --key <key>` (explicit registration
   sidesteps finding #2 until the link's discovery is fixed).
6. **Verify** (the install is not done until this passes):
   - `muiogo serve` answers; `muiogo cases` lists the demo; `muiogo run
     --case "CLEWs Demo" --run REF --solver cbc` returns optimal (~seconds).
   - each OG model: `<model>/.venv/bin/python -c "import <pkg>"`.
   - link: `./scripts/setup.sh --check`.
   - solvers: `glpsol --version`, `cbc` exit 0.
7. **Manifest**: write `<workspace>/manifest.json` — component paths, git
   refs, venv pythons, solver versions, install timestamps. Skills read this
   instead of guessing paths; `muiogo-ai doctor` (later) re-runs step 6
   against it.
8. **Report**: step table (ok/skip/fail + detail), elapsed, log file path.

### Flags

`--dest DIR` · `--og KEYS|none` · `--og-branch KEY=BRANCH` (repeatable) ·
`--with-link/--no-link` · `--yes` · `--no-demo-data` · `--skip-solvers` ·
`--no-verify` (discouraged) · `--log/--no-log`

### What stays out

- No conda anywhere; uv end to end (matches all three components today).
- No coupled OG-CLEWS solve during install (that's a 20–30 min model run, not
  installation; `test-drive.sh` remains the worked example for that).
- No reimplementation of any component's install logic.

## 4b. CLEWs countries and matching (added 2026-07-27)

OG countries are code packages with a machine-readable catalog; CLEWs
countries are data packages (versioned "portable MUIO cases" in EAPD-DRB
repos, e.g. CLEWs-PHL v12) described only by READMEs, with layouts that vary
by repo. MUIOGO installs a CLEWs country by getting a case directory into
`WebAPP/DataStorage/` — headless, the validated path is its own
`POST /uploadCase` (multipart zip; same handler as the GUI's restore).

Design (piloted here, PHL first):

- **Self-describing country manifests** — `clews-country.json` per country
  repo: iso3/un_code/name, the cases with roles and a recommended default,
  archive names + checksum file, and the link's coupling fields. Hosted as
  overlays in `clews/countries/<ISO3>.json` until the spec is proposed to the
  CLEWs repos; an in-repo manifest wins once it exists.
- **A CLEWs catalog** — `clews/clews-repos.json`, mirroring the OG
  installer's `repos.json` (key, owner, repo, iso3).
- **Matching = join on ISO3.** OG derives `PHL` from `OG-PHL`; the CLEWs
  manifest declares it. `--country PHL` resolves the OG model, the CLEWs
  case (recommended by default, `--case` to override), link registration,
  and — when the manifest carries coupling fields — the link's countries
  entry. No central mapping table anywhere; each layer publishes its own
  catalog. (PHL generates no link entry: it ships inside ogclews-link as the
  packaged worked example.)
- Long-term home: the catalog and case-install capability belong upstream in
  MUIOGO (a "CLEWs countries" surface symmetric to its OG calibrations tab);
  developed quietly here first per Marcelo's call (2026-07-27).

## 5. Delivery plan

| Step | Delivers | Gate |
|---|---|---|
| v0 | orchestrator with steps 1–3 + 6a + 7–8 (MUIOGO + solvers + client, verified demo solve) | clean-VM run passes end to end |
| v0.5 | upstream PR to MUIOGO: `--no-start` on install.sh (+ `--headless` on start.sh); orchestrator drops the absorb-the-start workaround | PR merged in MUIOGO |
| v1 | step 4 (OG models via `/ogc` API) + step 5 (link) + manifest consumers in skills | one command yields a registered OG-PHL and a passing `setup.sh --check` |
| v1.5 | ogclews-link PR: read registry from `~/.muiogo/og-state/` (finding #2) | link auto-discovers MUIOGO installs again |
| v2 | Windows (`install.ps1`) once the link has a PowerShell setup | parity run on Windows |

Open decisions for Marcelo: default OG country set for `--og` (none vs
`og-phl` as the worked example), and whether the workspace default should be
`~/muiogo-ai` or something shorter.
