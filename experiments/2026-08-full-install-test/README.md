# Full install-to-results test (2026-08-03)

**Question.** Can `scripts/install.sh --country PHL` take a machine that has
never seen this tool to a solved Philippine CLEWs run with collected result
CSVs — headless, assistant-mediated, with no clicks — while leaving the user's
own MUIOGO/OG checkouts completely untouched?

**Answer: yes.** Install (exit 0, all steps PASS, ~2 GB, MUIOGO pinned at
`3db8b816`) → `muiogo-ai serve` → CBC solve of the Philippines case →
24 result CSVs downloaded and provenance-verified. The user's own setup was
byte-identical before and after (four fingerprinted files). The test also
surfaced real defects, each fixed and re-verified during the test — which is
what the test was for.

## The run that ends the test

- Case `Philippines_v12_ENV_LAND_WATER_DIAGNOSTIC` (v12.0.0 archive,
  sha256-verified from EAPD-DRB/CLEWs-PHL), run `BASE_CHK` (scenario `BASE`),
  solver CBC.
- **Optimal, objective 375,930,821.34**, 132 CPU s. Years 2020–2053.
- 24 result CSVs (36 MB); `muiogo-ai verify` confirms disk matches the
  provenance record ([RUN.json](RUN.json): input `dd5152ae79ee`, results
  `11b6fcd978d0`).
- CSVs are not committed (size); reproduce with:
  `muiogo-ai run --case "Philippines_v12_ENV_LAND_WATER_DIAGNOSTIC" --run BASE_CHK`
  then `muiogo-ai results ... --out DIR`. `RUN.json` here is the reference.

## Findings (each led to a fix in this repo, except #5)

1. **`--yes` chose the install location silently.** An assistant driving the
   installer decided the user's filesystem layout. Now: interactive runs
   always confirm the location (even under `--yes`), non-interactive runs must
   pass `--dest`, and EOF on the prompt is a refusal, never a default.
2. **Installing registered a "world" and stole the active pointer** — the
   user's bare `muiogo` silently retargeted to the new installation. This led
   to the full disentanglement (commit `790d30e`): one installation per
   machine, no shared state read or written, launcher pins the manifest inside
   the installation, components (MUIOGO, OG models, ogclews-link) treated as
   separate apps that never learn muiogoai exists.
3. **`muiogo status` crashed offline** (KeyError) and mislabelled a registered
   OG model. Now reads the installation's own registry file when the server is
   down; `muiogo-ai status` is the supported offline health check.
4. **Installer temp files leaked** (cleanup arrays wiped after registration;
   fetched installer never listed). Fixed.
5. **Upstream MUIOGO bug, open:** a case restored through `/uploadCase` from a
   portable archive cannot generate data files — zip archives cannot represent
   the empty `res/<run>/` directories, `/uploadCase` does not recreate them for
   the runs defined in the case, and `generateDataFile` assumes the directory
   exists, failing with an unexplained 500 (`FileNotFoundError` →
   `IndexError`). Runs created through the API (`muiogo-ai new-run`) get their
   directory and work — hence `BASE_CHK` instead of the shipped `Base_v12`.
   Fix belongs in MUIOGO (`generateDatafile` should create the run directory,
   or `/uploadCase` should restore it); propose upstream, issue first.
   Also minor: `muiogo-ai validate` before first generation reports
   "Data file is not created" instead of pointing at `run`.

## Wiring check for users

```bash
muiogo-ai status                                   # offline health check
muiogo-ai serve --detach && muiogo-ai cases && muiogo-ai stop   # full round trip
```

Repo at `790d30e` during the results phase; install performed at `1bf3108`
with client fixes (`44fdc70`) applied to the installation in place.
