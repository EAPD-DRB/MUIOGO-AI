# MUIOGO API — observed endpoint reference

Status: living document. Everything in "Verified" was exercised headless against
MUIOGO @ `3db8b816` (2026-07-27) with a plain HTTP client and no GUI; payload
shapes are copied from working calls. Endpoints under "Present, not yet
exercised" were read in the route code but not driven.

Base URL: `http://127.0.0.1:5002` (port from `PORT` env; server started with
`<root>/.venv/bin/python API/app.py` — no browser opens; MUIOGO's start.sh is
what opens the browser).

## Session model

- Flask cookie session; one key: `osycase` = the selected case name.
- `GET /getSession` → `{"session": <case-or-null>}` — works cold, also a good
  readiness probe.
- `POST /setSession` `{"case": "CLEWs Demo"}` → `{"osycase": "CLEWs Demo"}`.
  404 if the case directory doesn't exist; `{"case": null}` clears.
- Most read/run endpoints take `casename` explicitly and work from a cold
  session. **Session-gated** (403/400 unless `osycase` matches): `copyCase`,
  `deleteCase`, `downloadCSVFile`, `downloadResultsFile` (and other download
  routes by the same pattern).

## Verified endpoints

| Endpoint | Method | Payload / params | Returns |
|---|---|---|---|
| `/getSession` | GET | — | `{"session": name-or-null}` |
| `/setSession` | POST | `{"case": name}` | `{"osycase": name}` |
| `/getCases` | GET | — | `["CLEWs Demo", ...]` |
| `/copyCase` | POST | `{"casename": name}` (session must match) | message; creates `<name>_copy` |
| `/deleteCase` | POST | `{"casename": name}` (session must match) | message |
| `/generateDataFile` | POST | `{"casename", "caserunname"}` | writes `res/<run>/data.txt` |
| `/run` | POST | `{"casename", "caserunname", "solver": "cbc"\|"glpk"}` | see below |
| `/getResultCSV` | POST | `{"casename", "caserunname"}` | list of result CSV names |
| `/downloadCSVFile` | GET | `?caserunname=<run>&file=<name>.csv` (session-gated) | CSV bytes |
| `/downloadResultsFile` | GET | `?caserunname=<run>` (session-gated) | raw `results.txt` |

### `/run` semantics (important)

- **Synchronous**: the request blocks until the solver finishes (demo case:
  ~1–4 s with CBC). Client timeouts must allow for real model sizes.
- **HTTP status is not the run status**: solver failures still return 200.
  The JSON body's `status_code` (`"success"`/`"error"`) is the real signal;
  `timer` carries the solver's result line, `glpk_message`/`cbc_message` the
  solver stdout.
- **Solver choice**: `"cbc"` is the GUI default and works — it preprocesses
  `data.txt` → `data_processed.txt`, builds `lp.lp` with glpsol `--check`,
  solves with CBC. `"glpk"` is broken at `3db8b816`: that branch skips
  preprocessing and feeds raw `data.txt` to the preprocessed model
  (`model.v.5.4.txt`), which fails on `MODEperTECHNOLOGY` (upstream fix filed
  from this work).
- Re-running deletes the run's previous results first.

### Solver prerequisites

`glpsol` and `cbc` binaries must be resolvable (env var, PATH, or platform
standard locations — see MUIOGO `docs/ARCHITECTURE.md`). On macOS:
`brew install glpk cbc`. Resolution happens per request; no server restart
needed after installing.

## Present, not yet exercised

From `API/Routes/` at the same commit — payloads unverified:

- Case data: `/getDesc`, `/getParamFile`, `/saveParamFile`, `/updateData`,
  `/saveCase`, `/saveScOrder`, `/getResultData`, `/resultsExists`,
  `/prepareCSV`, `/downloadCSV`, `/importTemplate`
- Runs: `/createCaseRun`, `/updateCaseRun`, `/deleteCaseRun`,
  `/deleteScenarioCaseRuns`, `/batchRun` (CBC hardcoded), `/cleanUp`,
  `/validateInputs`, `/readDataFile`, `/readModelFile`, `/readLogFile`,
  `/saveView`, `/updateViews`, `/downloadDataFile`, `/downloadFile`
- OG-Core (`/ogc/*`): `/getCalibrationCatalog`, `/getInstalledCalibrations`,
  `/checkCalibration`, `/installCalibration`, `/registerLocalCalibration`
- Upload & S3 sync routes.

Next to exercise (Phase-1 scenarios work): `/createCaseRun`, `/updateData`,
`/batchRun`, `/readLogFile`.
