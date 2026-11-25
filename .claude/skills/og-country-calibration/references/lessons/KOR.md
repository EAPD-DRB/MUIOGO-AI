<!-- GENERATED FILE - do not edit here.
     Source: docs/og-lessons/KOR.md
     Regenerate: python scripts/sync_shared.py -->

# Republic of Korea (KOR): lessons behind the OG skills

What happened behind lessons in the OG skills (og-country-calibration,
og-multi-industry-calibration, og-solver-diagnosis, og-run). The skills teach the method; these
are one country's numbers, kept here so the skills stay general. They record what was true when
written; check the country repo before relying on any of them. Do not copy them into another
country's calibration.

All KOR work is local and was never pushed. OG-KOR was a timed test of the og-country-calibration
skill on 2026-10-18, with an overnight follow-up into 2026-10-19. The written record is in
`OG-KOR-demo` (local test repo, unpublished) (branch `calib/initial-kor`, plus `test/*` branches):
`DEMO_LOG.md` (the timed log), `OVERNIGHT_BRIEFING.md`, `data_notes/` (sources) and
`docs/book/content/calibration/` (the calibration chapters). Each run was an official-installer copy
in `OG-KOR-demo-runs/install-NN/OG-KOR/` (local test repo, unpublished), with its log in `logs/` and its
output in `examples/OG-KOR-Example/`. Below, "OG-KOR commit" means a commit in that local repo, and
"install-NN" means that run folder. OG-Core 0.21.2 from PyPI unless an entry says otherwise. The
skill changes from the test were merged as EAPD-DRB/Model-tools#5 and EAPD-DRB/MUIOGO-AI#8.

Contents (by the skill file each entry backs; search a file for its `###` headings)
- og-country-calibration/SKILL.md
- og-country-calibration/references/macro-open-economy.md
- og-country-calibration/references/fiscal-consistency.md
- og-country-calibration/references/households-demographics.md
- og-country-calibration/references/validation-dashboard.md
- og-country-calibration/references/solving-tuning.md
- og-solver-diagnosis/SKILL.md
- og-solver-diagnosis/references/failure-taxonomy.md
- og-solver-diagnosis/references/solve-procedures.md
- og-run-preflight/SKILL.md

## og-country-calibration/SKILL.md

### De-siblinging a bootstrap copy: grep for the sibling and audit every inherited value

- **Lesson:** a repo copied from a sibling carries the sibling's country in code, tests and solver
  settings as well as the JSON, so grep for it and audit every inherited value before any solve.
- **What happened:** OG-KOR was copied from OG-PHL `calib/remittances` (52b77ca). Renaming the
  package missed a live-download ISO default of "PHL" (online runs would have overwritten Korea's
  values), FIES remittance shares, a Gini default of 40.7, peso labels, a test asserting UN code
  608 and PHL tax tests. The audit also caught `nu` 0.4 with Anderson inherited from PHL (the run
  rules want 0.2 or lower). PHL's `initial_guess_TR_SS` put KOR's GDP guess 4.6x too high and
  stalled steady-state round r03.
- **Evidence:** local: `OG-KOR-demo/DEMO_LOG.md` (local test repo, unpublished) (steps 1, 1b, 0a/0 and
  5-9); OG-KOR commits 18ebc0e (bootstrap), ce52de6 (de-sibling: tests, live macro path off),
  d1dc5d0 (`nu` 0.4 → 0.2); `OG-KOR-demo-runs/overrides/r03.json` (local test repo, unpublished) (no TR
  seed, so PHL's applied) and `r03b.json` (KOR's own TR seed 0.0267).
- **When:** 2026-10, OG-KOR commits above, ogcore 0.21.2.

### De-siblinging a bootstrap copy: replace the sibling's example reform

- **Lesson:** replace the sibling's example reform with one that means something for the new
  country, such as a reform it has enacted.
- **What happened:** OG-PHL's example reform is a CIT cut and a debt change. OG-KOR's example uses
  the enacted 2026 corporate-rate rise, +1 point in every bracket (`cit_rate` 0.275). In the final
  run it lowered GDP by 0.12% over 2025-34 and 0.14% in the steady state.
- **Evidence:** local: `OG-KOR-demo/examples/run_og_kor.py` (local test repo, unpublished) (reform
  block); OG-KOR commit 069a4a2 ("Korean reform (2026 CIT +1pt)"); `DEMO_LOG.md`, "Final run E
  results".
- **When:** 2026-10, OG-KOR commit 069a4a2.

## og-country-calibration/references/macro-open-economy.md

### Debt: a government that owns large financial assets

- **Lesson:** OG-Core's government has debt but no assets, so pair gross debt with the rate on gross
  debt, leave the asset side out, report the missing asset income as the cause of the low `G/Y`,
  and never route it through `alpha_FA`.
- **What happened:** Korea's general government has net financial assets of about 51% of GDP
  (end-2025), mostly the National Pension Service fund (54% of GDP). OG-KOR used D2 with the
  effective rate on gross debt. About 2.4% of GDP of government property income is then missing from
  revenue, and the budget closure set steady-state `G/Y` at 13.0% against 17.5% in the data.
- **Evidence:** local: `OG-KOR-demo/docs/book/content/calibration/macro.md` (local test repo, unpublished)
  ("Government debt and the public balance sheet" and the fit table);
  `OG-KOR-demo/data_notes/macro.md` (local test repo, unpublished) (row 35: GG net financial assets 50.8%
  of GDP, end-2025p); `docs/book/content/calibration/taxes.md` (the 2.4% not captured).
- **When:** 2026-10.

### world_int_rate_annual: the sign check fails at the data's own K/Y

- **Lesson:** for a high-saving net creditor the domestic return at the data's private `K/Y` can sit
  at or below the world rate; then no `zeta_K` gives a positive `K_f/K`, so keep the sourced rate,
  set `zeta_K` from the openness prior and report the miss.
- **What happened:** at private `K/Y` 4.31 (target 4.36) the domestic return was 3.97% against a
  4.0% world rate. `K_f/K` was −0.9% at `zeta_K` 0.17 and −3.3% at 0.5, against a gross IIP target
  of +8.4%. A positive share would have needed a world rate near 3.7%, which no source supports.
  `zeta_K` was set to 0.5 and judged on the transition, where the first-year foreign share was 9.0%
  (run B) and 9.1% (final run E).
- **Evidence:** local: `OG-KOR-demo/docs/book/content/calibration/macro.md` (local test repo, unpublished)
  ("Open economy"); OG-KOR commit 069a4a2 ("zeta_K 0.5 (level not identified at r~r*)");
  `DEMO_LOG.md` step 5-9.
- **When:** 2026-10, ogcore 0.21.2.

### Initial household wealth: test an initial-wealth build on your country before adopting it

- **Lesson:** an in-loop rescale of initial wealth can oscillate and a static anchor converged, but
  neither fixes an early spike caused by unsolved start cohorts, so rule those out first and adopt
  an unreleased build only if it fixes your symptom.
- **What happened:** PSLmodels/OG-Core#1250 (draft) ships `initial_wealth_ratio` (B/Y in the first
  period, default 5.702 and always on) and `initial_hhwealth_dist` (the S×J shape); it is being split
  into smaller PRs, starting with #1251. On KOR, with the capital-side target 4.43 and the default
  shape, its in-loop rescale ran ten damped iterations without decaying (distance 1.47, 1.48, 1.05,
  0.71, 0.64, 1.04, 1.55, 1.29, 1.13, 1.10), where the same calibration without it reached 0.078 by
  iteration 10. PR #1189 (a static anchor set before the solve) converged (9.5e-6 at iteration 55)
  and delivered 4.39, but the 2026 consumption spike grew (C/Y 72.7% against 61.5% in run B). The
  spike was the #1247 solver bug: with the solve fixed, C/Y ran 50.4, 50.5, 50.7% in 2025-27,
  against 48.6, 62.9, 53.3% before, under the default initial condition.
- **Evidence:** https://github.com/PSLmodels/OG-Core/pull/1250,
  https://github.com/PSLmodels/OG-Core/pull/1251, https://github.com/PSLmodels/OG-Core/pull/1189,
  https://github.com/PSLmodels/OG-Core/issues/1247. Local:
  `OG-KOR-demo-runs/install-11/OG-KOR/logs/example_run_C.log` (local test repo, unpublished) (PR #1250 at
  5118f34, OG-KOR commit eca770a on `test/pr1250-initial-wealth`);
  `install-12/OG-KOR/logs/example_run_D.log` (PR #1189 merged locally as OG-Core a37a039, OG-KOR
  commit 1b84b42 on `test/pr1189-initial-wealth`); C/Y paths from the saved
  `OUTPUT_BASELINE/TPI/TPI_vars.pkl` of install-13 (run E, before) and install-14 (run F, after);
  `OVERNIGHT_BRIEFING.md` section 1; `DEMO_LOG.md` runs 10c and 10d.
- **When:** 2026-10. Run C on #1250 head 5118f34 (ogcore 0.21.3); run D on master 0.21.2 + #1189
  head b440d48. PR states as of 2026-10-19: #1250 open draft, #1251 open, #1189 open.

### Initial household wealth: the default level matched the data by luck

- **Lesson:** the old default rescale's level comes from the gap between today's and the stationary
  age structure, not from data, so take the level from data even when the default lands close.
- **What happened:** giving each household its steady-state wealth for its age, without a rescale,
  gave KOR a B(0)/Y(0) of 2.72. The old default multiplied that by 1.53 to make the aggregate equal
  the steady state's, giving about 4.17, near the capital-side data target of 4.43. The briefing's
  options table gives the default as 4.14 and its section 5 gives 4.17; 2.72 × 1.53 ≈ 4.16, so the
  two are the same figure with different rounding.
- **Evidence:** local: `OG-KOR-demo/OVERNIGHT_BRIEFING.md` (local test repo, unpublished) sections 2 and
  5. The script that computed 2.72 was not found in the repo.
- **When:** 2026-10, ogcore 0.21.2.

### delta_annual: both sides of the ratio are private

- **Lesson:** OG-Core's `K` is private capital, so use private `K/Y` (PWT less public capital) as
  the dashboard target and as the denominator of `delta`, with government CFC out of the numerator.
- **What happened:** PWT 11.0 puts Korea's total `K/Y` at 5.13 (2023); less public capital 0.77,
  private `K/Y` is 4.36. `delta` = (22.3% − 1.6%) / 4.36 = 4.75%, against 4.35% from total CFC over
  total capital. At `K/Y` 5.13 the model's return would have been about 3.1%, about 0.9pp below the
  4.0% world rate. This is also the skill's exemplar for the private/public split.
- **Evidence:** local: `OG-KOR-demo/docs/book/content/calibration/firms.md` (local test repo, unpublished);
  OG-KOR commit 069a4a2 ("private delta and K/Y"); `DEMO_LOG.md` step 5-9 ("K/Y and delta must be
  PRIVATE (skill contradicted itself)").
- **When:** 2026-10.

### K_f gross vs net: divide by private K/Y

- **Lesson:** the gross IIP target for `K_f/K` divides by the model's private `K/Y`; total PWT
  capital understates it.
- **What happened:** inward direct-investment equity plus portfolio equity (end-2024) is 12.5% +
  24.0% of GDP. Over private `K/Y` 4.36 that is 8.4%; over total PWT capital it was 7.1%, 1.3pp
  lower. Run C still used 7.1%; the target moved to 8.4% before the final run. Japan's half of this
  lesson is in JPN.md.
- **Evidence:** local: OG-KOR commits eca770a (message: "IIP 0.071") and 6b0b732 ("K_f/K target on
  private capital (8.4%)"); `docs/book/content/calibration/macro.md` ("Open economy").
- **When:** 2026-10.

## og-country-calibration/references/fiscal-consistency.md

### The alpha_G glide: a path from the transition, with pb from the debt path

- **Lesson:** when pensions move a lot over the transition, compute the `alpha_G` glide from the
  transition's own revenue and pension paths, and when the program is a debt path derive the
  primary-balance target from it.
- **What happened:** pensions in KOR's transition start at 2.7% of GDP and grow toward the steady
  state's 5.6%. Under a flat steady-state `alpha_G` (run B), the primary balance was +1.1% to +1.7%
  of GDP a year in 2026-30 (falling to +0.6% by 2036), and debt fell from 49.6% to 35.7% of GDP by
  2036 against a plan near 52%. `examples/glide.py` then built `alpha_G(t)` from run B's revenue and
  pensions, with `pb_target(t)` from the 2026-2030 plan's debt path. In the final run debt was 52.5%
  in 2026 (actual 52.3%) and within 1.6pp of the plan in every plan year.
- **Evidence:** local: `OG-KOR-demo/docs/book/content/calibration/government.md` (local test repo, unpublished);
  OG-KOR commits 0eac634 (glide script) and dbecd71 (glide v2); run B's
  `OG-KOR-demo-runs/install-10/OG-KOR/examples/OG-KOR-Example/OUTPUT_BASELINE/TPI/TPI_vars.pkl` (local test repo, unpublished)
  (primary balance and debt recomputed from it); `DEMO_LOG.md` runs 10b and "Final run E results".
- **When:** 2026-10, ogcore 0.21.2.

## og-country-calibration/references/households-demographics.md

### Earnings (the e ability matrix): the NTA age-shape port

- **Lesson:** port OG-JPN's NTA reference code rather than rewrite it; it moves to another country
  by changing only the country name and year windows.
- **What happened:** OG-KOR ported OG-JPN's NTA download script and age-shape functions, Korea 2019
  against US 2011, with a World Bank Gini of 32.9. Earnings now peak at 47 and fall to 0.60 of the
  US shape by 65, the signature of "honorary retirement" and mandatory retirement at 60.
- **Evidence:** local: OG-KOR commits ce52de6 (adds `scripts/fetch_nta_age_profiles.py`,
  `ogkor/data/nta_labor_income_KOR.csv`, `ogkor/income.py`) and b82213f (e regenerated: "peak age
  47; factor 0.60 at 65"); `docs/book/content/calibration/earnings.md`; `DEMO_LOG.md` step 4.
- **When:** 2026-10.

### The data window: the last usable year is one before the last data year

- **Lesson:** `get_pop` reads `final_data_year + 1`, and the Population-Data archive can end earlier
  than the UN API, so set the window to one year before the archive's last year and name the reason.
- **What happened:** without a UN token ogcore fell back to the archive, which ends at 2099
  (`END_YEAR = 2100 - 1`). So 2098 was KOR's last usable year, while ogcore's assert allows 2099.
  A 2099 window failed far from the cause, as an `UnboundLocalError` in `pop_rebin`.
- **Evidence:** local: OG-KOR commit 069e7b3 ("Demographics window ends 2098: get_pop reads final
  year + 1 and the archive ends 2099"); `DEMO_LOG.md` step 3.
  https://github.com/EAPD-DRB/Population-Data/blob/4d52ef740e1c2c57a9cb3c196557d294262e1161/src/constants.py#L24
- **When:** 2026-10, ogcore 0.21.2.

### Discontinuities: both breaks are OG-Core bookkeeping, not economics

- **Lesson:** the resource-constraint breaks at the final data year and at `fixper` come from how
  OG-Core builds the population, not from demographics, so check the population's law of motion
  before blaming the model.
- **What happened:** the first guess for the period-74 break (2098) was that mortality improvement
  stops there; that was wrong. The downloaded UN rates have one more year than `get_pop_objs`
  assumes (76 rows for 75 periods). Master projects from the year before the last data year, so it
  builds the last year's population with the frozen rates but stores the previous year's rates:
  population and rates disagree by 2.3e-5 in that period. At `fixper` (period 120) Korea's
  population is not stationary (growth −1.18% against −1.005%; the age shape takes about 360 periods
  to settle), so the one-period immigration re-solve is a real jump. Freezing earlier does not help
  (shape gap about 1e-3 for any freeze year 2050-2098) and a 2050 freeze puts long-run growth near
  −1.6%.
- **Evidence:** local: `OG-KOR-demo/OVERNIGHT_BRIEFING.md` (local test repo, unpublished) section 3. Master
  as of 2026-10-19 still projects from `T0 - 1`:
  https://github.com/PSLmodels/OG-Core/blob/81f45496b9aec37bc82dc22aeebba31f055ca5e2/ogcore/demographics.py#L1781
- **When:** 2026-10, OG-Core master 81f45496 (0.21.2 line).

### Discontinuities: the two local fixes and what they did (run H)

- **Lesson:** check whether your ogcore projects the population from the last data year and offers
  `fixper_phase_in`; if it has neither, expect the breaks, report them upstream and do not tune
  against them.
- **What happened:** two local OG-Core fixes: project from the last data year (one line), and an
  opt-in `fixper_phase_in` that ramps immigration into the stationary rates before `fixper`,
  solved jointly so the population is still stationary at 120. With both and `fixper_phase_in=45`,
  run H (install-18) cut the largest resource-constraint error from 9.1e-3 to 1.2e-4 against run F
  (the #1247 fix only): 2.0e-3 → 1.9e-6 around period 74, 9.1e-3 → 6.8e-7 around period 120. What
  is left is the last five periods (1.2e-4). Run G, with a first version of the ramp, added a new
  2.4e-3 error inside the ramp, because its re-solve loop hit a 100-iteration cap without
  converging and nothing checked. Neither fix is upstream as of 2026-10-19.
- **Evidence:** local: `~/Projects/OG-Core.smooth-pop`, branch `fix/smooth-population-switch`,
  commits ce877c95 (data-boundary fix), ebdb7a3b (joint ramp solve), f8d51d1c (tests); run H's build
  `~/Projects/OG-Core.int-g`, branch `integrate/1247-plus-smooth-pop` at 858712b6;
  `OG-KOR-demo-runs/install-18/OG-KOR/logs/example_run_H.log` (local test repo, unpublished) (max error
  1.22e-4) and `install-14/OG-KOR/logs/example_run_F.log` (9.13e-3); per-period maxima recomputed
  from each run's `TPI_vars.pkl` `resource_constraint_error`; OG-KOR commit 3c121be on
  `test/h-pop-exact`; `OVERNIGHT_BRIEFING.md` section 4. No upstream PR found (`gh search prs
  fixper_phase_in` on PSLmodels/OG-Core returned nothing; master has no `fixper_phase_in`).
- **When:** 2026-10-19, ogcore local 858712b6 (0.21.3).

### Discontinuities: triage a loosened RC_TPI by period

- **Lesson:** a sibling's loosened `RC_TPI` must be justified or tightened: tabulate the error at
  each break period, at the last period and everywhere else, and keep the loose value only with
  that table in the docs.
- **What happened:** OG-KOR inherited `RC_TPI` 0.01 from OG-PHL against ogcore's default 1e-4. KOR's
  run B baseline had 9.1e-3 at period 120, 2.0e-3 at period 74, 1.9e-4 at the last period, at most
  2.2e-6 everywhere else and 3.6e-7 in the first ten years. So the loose tolerance was covering the
  two breaks, not the calibration. After run H, it could be tightened toward 1e-4 except for the
  last five periods.
- **Evidence:** local: `OG-KOR-demo/DEMO_LOG.md` (local test repo, unpublished) runs 10 and 10b;
  `OG-KOR-demo-runs/install-10/OG-KOR/logs/example_run_B.log` (local test repo, unpublished) (max 9.13e-3);
  per-period values recomputed from run B's `TPI_vars.pkl`; OG-KOR commit f761a29 (docs: RC
  tolerance); `OVERNIGHT_BRIEFING.md` section 4.
- **When:** 2026-10, ogcore 0.21.2.

### Pensions: a high-denomination currency needs income in millions

- **Lesson:** in a currency like the won, express `mean_income_data` in millions so the factor seed
  fits ogcore's validator, and rescale `φ2` by `unit^φ1`.
- **What happened:** ogcore caps `initial_guess_factor_SS` at 500,000, while Korea's factor in won
  is about 3.6e7. Preflight `--params-json` caught it. OG-KOR moved income to millions of won and
  rescaled `φ2` by 1e6^φ1, OG-JPN's fix.
- **Evidence:** local: OG-KOR commit c48b8c1 ("Income in millions of KRW ..."); `DEMO_LOG.md` steps
  5-8.
- **When:** 2026-10, ogcore 0.21.2.

### Pensions: a young pension system needs two checks

- **Lesson:** score steady-state pension outlays against the scheme's long-run projection and
  today's spending at t=0, and do not tune `alpha_db` down to today's spending.
- **What happened:** OG-KOR's steady state pays 5.6% of GDP in pensions, against 3.1% today (NPS
  1.71% plus the special-occupation schemes 1.39%). The NPS's own projections put its benefits
  alone near 9% of GDP by 2080. At t=0 the model gave 2.65%, below today's 3.1%; why was not
  investigated.
- **Evidence:** local: `OG-KOR-demo/docs/book/content/calibration/households.md` (local test repo, unpublished)
  ("A young system"); 2.65% recomputed from run E's `TPI_vars.pkl` (install-13);
  `data_notes/households.md` (NPS benefits 1.71% of 2024 GDP); OG-KOR commit f761a29 (pension t=0
  wording).
- **When:** 2026-10, ogcore 0.21.2.

## og-country-calibration/references/validation-dashboard.md

### Moments most often tuned for but never scored: wealth by age

- **Lesson:** score the solved wealth-by-age profile against survey ratios; `chi_b` moves the old
  end but also `K/Y` and bequest revenue, and the young end's housing debt is outside the model.
- **What happened:** the solved profile had 60+ at 1.86× the 50-59 level against 0.97 in the 2025
  survey, and under-30s at 0.02 against about 0.2. Cutting `chi_b` from 80 (inherited from OG-PHL)
  to 20 and 5 moved the 60+ ratio to 1.60 and 1.26, but also moved `K/Y` from 4.31 to 3.71 and 3.47,
  so `beta` and `tau_bq` must be re-tuned with it. Young Korean households' net worth is leveraged
  housing, which OG-Core does not model. KOR was not recalibrated to this moment.
- **Evidence:** local: `OG-KOR-demo/OVERNIGHT_BRIEFING.md` (local test repo, unpublished) section 2;
  `OG-KOR-demo-runs/install-13/OG-KOR/logs/tune_chib_20.log` (local test repo, unpublished) (`K/Y` 3.7072)
  and `tune_chib_5.log` (3.4703); survey table in `data_notes/households.md` ("Wealth by age of
  household head").
- **When:** 2026-10, OG-KOR commit dbecd71, ogcore 0.21.2.

### Two traps when adding rows: a trade surplus with a positive NIIP

- **Lesson:** a steady-state net creditor runs a trade deficit, so score `NX/Y` in the early
  transition, compare only its sign in the steady state, and expect most of the `C/Y` gap to be this
  term.
- **What happened:** Korea's data has `NX/Y` +5.5% with a NIIP of +47% of GDP; the model's steady
  state has −3.1%. The `C/Y` gap (59.2% against 48.1%) is a residual: −8.6 from net exports, −4.5
  from government consumption, +2.5 from investment. The skill rounds this to "8.5 points of an
  11-point gap"; the repo's table says 8.6 of 11.1.
- **Evidence:** local: `OG-KOR-demo/docs/book/content/calibration/macro.md` (local test repo, unpublished)
  (steady-state fit table and the paragraph under it); `data_notes/macro.md` (row 19: net IIP 47.1%
  of GDP).
- **When:** 2026-10.

### Two traps when adding rows: use the model's own K concept

- **Lesson:** the `K/Y` row targets private capital: subtract public capital from the PWT ratio.
- **What happened:** the same split as `delta_annual` above: target 4.36, not 5.13. The final
  dashboard scored 4.31 against 4.36. Scoring against 5.13 would have sent `beta` after a gap that
  is not there.
- **Evidence:** local: `OG-KOR-demo/docs/book/content/calibration/macro.md` (local test repo, unpublished)
  (row "Private K / Y") and `firms.md`; `DEMO_LOG.md` step 5-9.
- **When:** 2026-10.

## og-country-calibration/references/solving-tuning.md

### The in-model tuning loop: warm-start every solve

- **Lesson:** seed every tuning solve from the last converged one; a dial move that breaks a
  warm-started solve is a signal about the calibration, while one that breaks a cold start is
  usually the seed.
- **What happened:** the same KOR calibration took 394 s from uniform seeds (r04) and 32 s
  warm-started (r05, the packaged JSON). OG-KOR shipped a warm-start seed ported from OG-JPN. The
  log also shows round r03 stalled on an inherited seed (see og-solver-diagnosis, class H) and was
  run without a log file.
- **Evidence:** local: `OG-KOR-demo-runs/install-08/OG-KOR/logs/tune_r04.log` (local test repo, unpublished)
  ("393.77 seconds") and `install-09/OG-KOR/logs/tune_r05.log` ("32.02 seconds");
  `OG-KOR-demo/CHANGELOG.md` (local test repo, unpublished) ("steady state 394 s -> 32 s"); OG-KOR commit
  069a4a2.
- **When:** 2026-10, ogcore 0.21.2.

## og-solver-diagnosis/SKILL.md

### Which world: skip it for a standalone installer run

- **Lesson:** the "Which world" rules apply only when working through MUIOGO; for a standalone OG
  repo installed with OG-Core's installer, the checkout you were given is the world.
- **What happened:** OG-KOR was a standalone repo run from official-installer copies, with no
  `muiogo-ai` involved. The skill's world rules did not fit, and the test logged it as a gap
  ("Which world" only through MUIOGO). The fix went into both skills in the test's skill PR.
- **Evidence:** local: `OG-KOR-demo/DEMO_LOG.md` (local test repo, unpublished), "How the skill
  performed" (gaps list). https://github.com/EAPD-DRB/MUIOGO-AI/pull/8 (merged 2026-10-19).
- **When:** 2026-10.

## og-solver-diagnosis/references/failure-taxonomy.md

### C. Oscillation: Anderson stalls just above mindist_TPI

- **Lesson:** if Anderson falls to a few times the tolerance and then rises for several iterations
  in a row, stop it and fall back to damped iteration from the same calibration.
- **What happened:** run A's baseline (Anderson) reached 2.7e-5 at iteration 18, then rose to 3.2,
  3.9, 4.4, 4.7 and 4.9e-5 against `mindist_TPI` 1e-5, at about 30 s an iteration. It was stopped.
  Run B, damped (`TPI_outer_method="picard"`, `nu` 0.2), went through the same level and converged at
  9.7e-6 at iteration 55, in about 28 minutes on a loaded 10-core machine.
- **Evidence:** local: `OG-KOR-demo-runs/install-09/OG-KOR/logs/example_run_A.log` (local test repo, unpublished)
  and `install-10/OG-KOR/logs/example_run_B.log`; OG-KOR commit 469305a ("fall back to damped
  iteration ... Anderson stalled at 2.7e-5"); `DEMO_LOG.md` runs 10 and 10b.
- **When:** 2026-10, ogcore 0.21.2.

### H. Cold-start seed failure: an inconsistent seed set, not a far one

- **Lesson:** ogcore guesses GDP as `initial_guess_TR_SS / alpha_T`, so a sibling's TR seed against
  the new `alpha_T` can put the GDP guess several times too high; set every seed from the country's
  own solve.
- **What happened:** OG-KOR kept OG-PHL's TR seed. Against Korea's `alpha_T` the GDP guess was 4.6x
  the solution and round r03 stalled; og-solver-diagnosis found the cause. Round r03b, with Korea's
  own TR seed, solved in 153 s. The skill quotes the stuck `Y` residual as −3.5; r03 ran without a
  log file, so that number could not be checked.
- **Evidence:** local: `OG-KOR-demo/DEMO_LOG.md` (local test repo, unpublished) step 5-9;
  `OG-KOR-demo-runs/overrides/r03.json` (local test repo, unpublished) (no `initial_guess_TR_SS`) and
  `r03b.json` (0.0267); `install-08/OG-KOR/logs/tune_r03b.log`. The −3.5 residual: not found
  (searched the run logs, overrides, DEMO_LOG and commit messages).
- **When:** 2026-10, ogcore 0.21.2.

### M. Unsolved start cohorts (households alive in the first year)

- **Lesson:** OG-Core solves the households alive at t=0 without checking the result, and the
  reported Euler error leaves them out, so an early-year spike patchy by age and income group can be
  unsolved households, not initial wealth.
- **What happened:** for 183 of KOR's 546 start cohorts the solve failed and returned its starting
  guess, with first-order errors up to 7.0. Those households consumed 2.5-3.5x steady state in 2026,
  and C/Y jumped to 62.9%. With the fix (run F against run E, same calibration) C/Y was 50.4, 50.5,
  50.7, 50.8% in 2025-28, households above 1.5x steady-state consumption in 2026 fell from 84 to 4,
  and the worst start-cohort error fell to 4.7e-6. The fix is the user's branch for #1247, rebased
  locally; no PR is open as of 2026-10-19.
- **Evidence:** https://github.com/PSLmodels/OG-Core/issues/1247 (open). Local:
  `~/Projects/OG-Core.fix-start-cohorts`, branch `fix/tpi-start-cohort-solves-rebased`, commits
  536b9109 (retry and check) to 868675a7; run F used a separate local quick fix, OG-Core 88a36183c
  (OG-KOR commit 0817905 on `test/fix-upper-triangle`); C/Y recomputed from the `TPI_vars.pkl` of
  install-13 (run E) and install-14 (run F); `OVERNIGHT_BRIEFING.md` section 1. Not in the tags list
  given for this file; it carries a "(history: KOR)" marker.
- **When:** 2026-10, ogcore 0.21.2 (run E) and 0.21.2 + local fix (run F).

## og-solver-diagnosis/references/solve-procedures.md

### Running against an unreleased ogcore: pin by commit, and check the build carries the PR

- **Lesson:** keep the official installer and pin ogcore by commit on a throwaway branch, and before
  installing an integration build check that it really contains the PR.
- **What happened:** OG-KOR's test branches pinned ogcore with `[tool.uv.sources]`: PR #1250 by its
  fork commit 5118f34, and a local master + #1189 merge by `file://` URL at a37a039. The first
  #1189 build merged a stale local copy of the PR branch: it merged cleanly and contained none of
  the PR's code. Rebuilding from the PR's actual head (b440d48) fixed it; conflicts were only in
  CHANGELOG and tests.
- **Evidence:** local: OG-KOR commits 5b9184c (`test/pr1250-initial-wealth`) and 1b84b42
  (`test/pr1189-initial-wealth`), both `pyproject.toml`; `DEMO_LOG.md` row 10d-setup;
  https://github.com/PSLmodels/OG-Core/pull/1189 (head b440d48). Not in the tags list given for this
  file; the section carries a "[KOR; ETH's main already pins this way]" tag.
- **When:** 2026-10.

## og-run-preflight/SKILL.md

### Which world: skip it for a standalone installer run

- **Lesson:** as in og-solver-diagnosis: the world rules apply only through MUIOGO; for a standalone
  installer run the checkout is the world.
- **What happened:** the same gap as above. Every KOR run was preflighted against its installer
  copy directly (for example run H: install-18, `test/h-pop-exact` at 3c121be, preflight GO).
- **Evidence:** local: `OG-KOR-demo/DEMO_LOG.md` (local test repo, unpublished), "How the skill performed";
  `OVERNIGHT_BRIEFING.md` section 4. https://github.com/EAPD-DRB/MUIOGO-AI/pull/8 (merged
  2026-10-19).
- **When:** 2026-10.
