# Map of ~/Projects/notebooks (surveyed 2026-07-27)

What each notebook derives, the intermediate-file graph, and two fully-worked provenance chains.
The dir has no README; this file is the substitute. Re-verify before relying on a row — notebooks
drift. Paths are relative to `/Users/mlafleur/Projects/notebooks` unless absolute.

## Per-notebook: country → parameters → inputs → outputs

| Notebook | Country | Derives | Inputs | Outputs |
|---|---|---|---|---|
| `wdi.ipynb` | ZAF | `initial_debt_ratio`, `initial_foreign_debt_ratio`, `zeta_D`, `g_y_annual`, `gamma`, `alpha_T` — the live draft of `macro_params.py` | World Bank WDI+QPSD (pandas_datareader era), ILO rplumber API, `alphaT_2020.csv` | prints only |
| `GFS.ipynb` | ZAF | `alpha_T`, infant mortality | `alphaT_2020.csv` (manual IMF GFS download, URL in comments), WB `SH.DYN.NMRT` | prints only |
| `yield-wedges_OLS.ipynb` | generic | `r_gov_shift`, `r_gov_scale` (OLS on Li-Magud-Werner-Witte 2021 IMF WP coefficients; URL cited in cell 0) | hardcoded paper coefficients | prints; wiring lands in `archive/macro_params.py` |
| `LIC_byJ-byS.ipynb` | ETH | `factor_j`/`factor_s`-adjusted e-matrix, re-estimated cubic earnings coefficients | `factor_j/factor_j_2023.csv`, `factor_s/factor_s_wide.csv`, `un_zaf_pop.csv` | `DeterministicProfileRegResults-adj.csv` |
| `LIC_byJ-byS-original.ipynb` | ZAF | same, ZAF (factor_j_2021) | same pattern | same CSV name (overwrites!) |
| `LIC_inequality.ipynb` | ZAF | vertical (income-only) e-matrix adjustment, WID `sptinc_992_j`, hardcoded array | `un_zaf_pop.csv` | `DeterministicProfileRegResults_vert-adj.csv` |
| `factor_test-e2.ipynb` | ETH | target ability shares `t_j`, scaled `e_new` | `factor_j/factor_j_2023.csv`, USA `Specifications()` | prints |
| `e_adjust.ipynb` | ETH/generic | `get_e_country_from_coeffs()` helper; tests `arctan_fit` | USA coeffs hardcoded | none |
| `demog1–4.ipynb`, `demog_all*.ipynb` | ZAF (231-variant → ETH) | fertility/mortality/pop transforms, method development | UN Data Portal API, NCHS FTP, `WPP2022_Fertility_by_Age1.zip` | `demog1` can write `un_zaf_pop.csv` (commented out — manually re-enabled historically) |
| `demog_test.ipynb` | ETH | fert/mort/imm rates via `ogcore.demographics` + `ogeth.calibrate` | UN API **with silent fallback to github.com/EAPD-DRB/Population-Data** | writes 6 top-level demographic CSVs (Nov 2025 one-off) |
| `undata_test.ipynb` / `undata_test-ETH.ipynb` | ZAF / ETH | `gamma` via ILO, pop/fert/mort pulls | UN API (bearer token IN CELLS — do not quote), ILO API | ETH variant writes CSVs to `~/Downloads/` |
| `test_pop_api.ipynb`, `un_pop_api_test.ipynb`, `Untitled*.ipynb` | — | API mechanics only (tokens in cells) | UN API | none |
| `factor_s/*.ipynb` (4) | generic | `factor_s` NTA curve construction | local NTA data | feed `factor_s/factor_s_wide.csv` |
| `usaid_testing/*` (6 nb + subtree) | ZAF | disease-burden mortality shocks — a SEPARATE research track with its own FORKED `ogzaf_default_parameters*.json` copies; never conflate with canonical OG-ZAF | various | CSVs inside `usaid_testing/` |

Support scripts: `archive/macro_params.py` (consolidation of wdi/GFS/yield-wedges logic — the
bridge between notebooks and repo `macro_params.py`); `.do` files (`sov-corp yield wedges.do`,
`productivity_matrix-testing.do`); R pipelines `factor_j/*.R` (WID), `e_adj_factors/*.R`
(**newest e-matrix pipeline, Nov–Dec 2025** → `e_adjust_factors.json`; consumer repo not yet
identified — trace before assuming it's wired in).

## Intermediate files: producer → consumer

| File | Producer | Consumer |
|---|---|---|
| `un_zaf_pop.csv` | `demog1.ipynb` (commented `.to_csv`, run manually once) | `LIC_byJ-byS*.ipynb`, `LIC_inequality.ipynb`, `demog3.ipynb` |
| `factor_j/factor_j_{2021,2022,2023}.csv` | `factor_j/*.R` (WID) | `LIC_byJ-byS*.ipynb`, `factor_test-e2.ipynb` |
| `factor_s/factor_s_wide.csv` | `factor_s/*.ipynb` + `e_adj_factors/factor_s*.R` | `LIC_byJ-byS*.ipynb` |
| `DeterministicProfileRegResults-adj.csv` | `LIC_byJ-byS*.ipynb` | no in-dir consumer — copied by hand into a country repo (trace the copy!) |
| `alphaT_2020.csv`, `alpha_G-*.{csv,xlsx}` | manual IMF downloads (URLs in `GFS.ipynb` comments) | `GFS.ipynb`, `wdi.ipynb` (`alpha_G-*`: consumer unidentified) |
| `Z-tfp-ZAF_PWT.{csv,xlsx}`, `country_mapping.xlsx`, `types.csv`, `employment elasticities.xlsx`, `LATC_estimate-*.xlsx` | manual extracts | **no consumer identified** — possibly the `.do` files or by hand |
| top-level `fert_rates.csv` etc. (6 files, Nov 2025) | `demog_test.ipynb` cell 10 | none (diagnostic one-off) |

## Worked chain A — ZAF `gamma` (live-API pattern)

`ogzaf_default_parameters.json:759` → `"gamma": [0.47164000000000006]`
← `ogzaf/macro_params.py` ILOSTAT block (`SDG_1041_NOC_RT_A`, `gamma = 1 − labor_share/100`),
  near-verbatim from `archive/macro_params.py` ← prototyped in `wdi.ipynb` /`undata_test*.ipynb`
← SOURCE: ILOSTAT series `SDG_1041_NOC_RT_A` via rplumber.ilo.org, value = whatever the API
  returned on the last `update_from_api=True` calibration (notebook-era snapshots 0.4136 and
  0.43608 differ from shipped 0.47164 — API revision drift, not an error).
Contrast: OG-PHL freezes gamma (docstring: "frozen at the documented 0.53785") with no code path.

## Worked chain B — `r_gov_shift`/`r_gov_scale` (three patterns side by side)

Paper: Li, Magud, Werner, Witte (2021) IMF WP, table 8 col 2: `8.199 − 2.975·y + 0.478·y²`,
explored in `yield-wedges_OLS.ipynb`, wired in `archive/macro_params.py` (OLS inversion →
`r_gov_scale = 0.24484763593657788` — identical in ZAF and ETH JSONs, confirming a
country-independent constant).

- ZAF: recomputed live in `ogzaf/macro_params.py` under `update_from_api`; shipped shift
  `-0.03376625043803518` (the raw, un-centered LMWW value).
- ETH: frozen via documented `estimate_r_gov(debt_ratio_ss=0.30, r_gov_DY2=0.04)`;
  `shift = base − r_gov_DY2·D̄² = -0.03376625... − 0.04·0.09 = -0.03736625043803518` —
  **arithmetic verified exact** against the shipped JSON (2026-07-27).
- PHL: frozen with a comment only (`r_gov_shift = -0.04816625043803517`, "recentered documented
  values") — no derivation function; re-deriving it needs the ETH formula with PHL's anchor.

## Secrets in the tracing path (flag, never quote/copy)

- `usaid_testing/un_api_token.txt` — non-empty token file (top-level and `examples/` copies are
  empty).
- Live UN bearer JWTs hardcoded in cells of `test_pop_api.ipynb`, `undata_test.ipynb`,
  `undata_test-ETH.ipynb` — flag for rotation/scrubbing if these files are ever shared.
