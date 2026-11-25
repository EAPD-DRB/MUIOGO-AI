<!-- GENERATED FILE - do not edit here.
     Source: docs/og-lessons/PHL.md
     Regenerate: python scripts/sync_shared.py -->

# Philippines (PHL): lessons behind the OG skills

What happened behind lessons in the OG skills (og-country-calibration,
og-multi-industry-calibration, og-solver-diagnosis, og-run). The skills teach the method; these
are one country's numbers, kept here so the skills stay general. They record what was true when
written; check the country repo before relying on any of them. Do not copy them into another
country's calibration.

Where the links point. Most of the single-industry work is on the fork branch `calib/remittances`
(draft PR [EAPD-DRB/OG-PHL#85](https://github.com/EAPD-DRB/OG-PHL/pull/85), head `52b77ca`). The
multi-industry work is on `feature/multi-industry-calibration` (draft PR
[EAPD-DRB/OG-PHL#63](https://github.com/EAPD-DRB/OG-PHL/pull/63), head `ec2ee98`). The
open-economy fix is merged in [EAPD-DRB/OG-PHL#68](https://github.com/EAPD-DRB/OG-PHL/pull/68).
A few numbers survive only in the author's working notes (project_tax_recalibration,
unpublished); those entries say so.

Contents (by the skill file each entry backs; search a file for its `###` headings)
- og-country-calibration/references/macro-open-economy.md
- og-country-calibration/references/fiscal-consistency.md
- og-country-calibration/references/taxes-informality.md
- og-country-calibration/references/households-demographics.md
- og-country-calibration/references/validation-dashboard.md
- og-country-calibration/references/solving-tuning.md
- og-country-calibration/references/calibration-pr.md
- og-multi-industry-calibration/references/inputs.md
- og-multi-industry-calibration/references/alignment.md
- og-solver-diagnosis/references/failure-taxonomy.md
- og-solver-diagnosis/references/solve-procedures.md

## og-country-calibration/references/macro-open-economy.md

### start_year: a start one year past the latest data

- **Lesson:** the start year is the latest year the calibration observes; a later start turns the
  packaged initial debt ratio and the latest observed levels into stale values or extrapolations.
- **What happened:** OG-PHL shipped `start_year` 2026 while its latest data was 2025. The packaged
  `initial_debt_ratio` 0.60 was the beginning-of-2025 value (end-2024 debt 60.7%, BTr); a 2026
  start needed about 0.62. The 2025 remittance ratio was being treated as a 2026 value. The user
  caught it and the start moved back to 2025, with demographics, `g_RM` and `eta_RM` regenerated.
  The 2026 value came from a parameter update (PR #48), not from a sibling repo, so the skill's
  "inheriting from a sibling" framing does not describe the PHL case.
- **Evidence:** [commit 607a65d](https://github.com/marcelolafleur/OG-PHL/commit/607a65d451f01308339dc3a79623344e61f49f3d);
  [CHANGELOG at 52b77ca, "Moved the start year to 2025"](https://github.com/marcelolafleur/OG-PHL/blob/52b77ca7657f2a98cae7c994023e7e090772bf32/CHANGELOG.md);
  [PR #85](https://github.com/EAPD-DRB/OG-PHL/pull/85) ("Start year" section); 2025 → 2026 set in
  [commit 1ccaa34](https://github.com/EAPD-DRB/OG-PHL/commit/1ccaa34826e176708bdb7a3ac52c6a9204ee3db1) of
  [PR #48](https://github.com/EAPD-DRB/OG-PHL/pull/48).
- **When:** 2026-07 (ogcore 0.18 plus the PSLmodels/OG-Core#1189 branch).

### zeta_K: re-validate after a tax-side change

- **Lesson:** tax recalibration moves domestic saving, so re-tune `zeta_K` to the IIP foreign
  share after any tax change.
- **What happened:** after PR #68 set `zeta_K` 0.4, the solved `K_f/K` was 0.26. The honest
  revenue side (lower effective taxes, a wealth tax) raised domestic saving and pushed it to 0.14.
  Re-tuning `zeta_K` 0.4 → 0.47 put it back at 0.20, the BSP IIP anchor (solved 0.2027 in the PR
  #85 fit table). Chinn-Ito (about 0.4) stays the prior.
- **Evidence:** [commit fe18125](https://github.com/marcelolafleur/OG-PHL/commit/fe181253bc6ccc5a45f3618c00ae6b8e49b7f9bf);
  [CHANGELOG at 52b77ca, "Retuned `zeta_K` 0.4 -> 0.47"](https://github.com/marcelolafleur/OG-PHL/blob/52b77ca7657f2a98cae7c994023e7e090772bf32/CHANGELOG.md);
  [PR #85](https://github.com/EAPD-DRB/OG-PHL/pull/85) fit table; the 0.26 from
  [PR #68](https://github.com/EAPD-DRB/OG-PHL/pull/68).
- **When:** 2026-07.

### r_gov base wedge: news stories mislabel fiscal years

- **Lesson:** take interest payments and debt from the treasury's own report, not from news.
- **What happened:** the widely quoted "FY2024" interest figure (₱854.1bn) was FY2025. The BTr Cash
  Operations Report puts FY2024 at ₱763.3bn. On about ₱15.3tn of average debt that is 5.0% nominal,
  about 2.0% real, not 2.5%. `r_gov_shift` moved −0.02364 → −0.0190.
- **Evidence:** [CHANGELOG at 52b77ca, "Corrected the FY2024 interest-payment figure"](https://github.com/marcelolafleur/OG-PHL/blob/52b77ca7657f2a98cae7c994023e7e090772bf32/CHANGELOG.md);
  [macro.md at 52b77ca](https://github.com/marcelolafleur/OG-PHL/blob/52b77ca7657f2a98cae7c994023e7e090772bf32/docs/book/content/calibration/macro.md)
  ("Government interest rate wedge"); [commit fe18125](https://github.com/marcelolafleur/OG-PHL/commit/fe181253bc6ccc5a45f3618c00ae6b8e49b7f9bf).
- **When:** 2026-07.

### r_gov base wedge: the LMWW intercept over-predicts what the treasury pays (also ZAF)

- **Lesson:** keep the LMWW slope but re-anchor the shift to the real effective rate on the debt
  stock; with `r_gov < g`, `pb*` is a deficit.
- **What happened:** the raw LMWW intercept put steady-state `r_gov` at 5.1% real, about 3pp above
  the ~2.0% the Treasury pays. That overstated debt service by about 1.9% of GDP and pushed spending
  down. After the re-anchor `r_gov` is 2.03% (PR #85 fit table), growth is about 3.2%, and `pb*`
  is −0.7% of GDP. The slope 0.245 is kept. OG-ZAF made the same correction (ZAF ~3.7%).
- **Evidence:** [macro.md at 52b77ca](https://github.com/marcelolafleur/OG-PHL/blob/52b77ca7657f2a98cae7c994023e7e090772bf32/docs/book/content/calibration/macro.md);
  [commit a2a7376](https://github.com/marcelolafleur/OG-PHL/commit/a2a737605dfe379beec950898bd816dffa7d51d2)
  (first re-anchor, 2.5%) and [fe18125](https://github.com/marcelolafleur/OG-PHL/commit/fe181253bc6ccc5a45f3618c00ae6b8e49b7f9bf)
  (2.0%); [PR #85](https://github.com/EAPD-DRB/OG-PHL/pull/85). ZAF side: see ZAF.md.
- **When:** 2026-07.

### Remittances: a nominal growth rate in the g_RM slot

- **Lesson:** `g_RM` is in the model's detrended growth units; a nominal dollar growth rate there
  makes RM/Y drift.
- **What happened:** OG-PHL shipped `g_RM = 0.03`, the Dec-on-Dec USD growth of remittances.
  OG-Core advances remittances by `(1 + g_RM) / (exp(g_y)(1 + g_n))`, a denominator of about 5.7%
  early on. RM/Y fell from 7.2% to a trough of 4.68% near period 24 (35% below its calibrated
  share) and recovered only after about period 100. Nothing in the docs intended it. The fix is a
  `g_RM` path that tracks `g_n` and holds the share flat; it regenerates with the demographics.
- **Evidence:** [commit 6450e60](https://github.com/marcelolafleur/OG-PHL/commit/6450e60c61abe606cdcfa0839ffd96ccefdc9cd8);
  [CHANGELOG at 52b77ca](https://github.com/marcelolafleur/OG-PHL/blob/52b77ca7657f2a98cae7c994023e7e090772bf32/CHANGELOG.md)
  ("`g_RM` 0.03 -> a path tracking `g_n`"); [issue #40](https://github.com/EAPD-DRB/OG-PHL/issues/40)
  (open; PR #85 says "Fixes #40").
- **When:** 2026-07.

### Remittances: the cash-measure trap

- **Lesson:** the model's `RM` is household income from abroad, the personal (BPM6) measure, not
  the central bank's cash headline.
- **What happened:** OG-PHL's 0.072 came from the BSP headline ratio, which is cash remittances.
  BSP reports 2025 personal remittances of US$39.62bn and cash of US$35.63bn (7.3% of GDP). On the
  same denominator, personal is 0.073 × 39.62/35.63 = 8.12%. `alpha_RM_1` and `alpha_RM_T` moved
  0.072 → 0.0812, inside the 8.0–9.0% band BSP research reports since 2017.
- **Evidence:** [commit 6450e60](https://github.com/marcelolafleur/OG-PHL/commit/6450e60c61abe606cdcfa0839ffd96ccefdc9cd8);
  [macro.md at 52b77ca](https://github.com/marcelolafleur/OG-PHL/blob/52b77ca7657f2a98cae7c994023e7e090772bf32/docs/book/content/calibration/macro.md)
  ("Remittances as a share of GDP"); [PR #85](https://github.com/EAPD-DRB/OG-PHL/pull/85).
- **When:** 2026-07.

### Initial household wealth: balance-sheet ratios run low (also ZAF, ETH)

- **Lesson:** prefer the capital-side wealth number; household balance-sheet estimates are a
  cross-check and run low for emerging markets.
- **What happened:** the OG-Core initial-wealth table lists the Philippines at 250.2% of GDP
  (2022), ZAF 256.2% and ETH 169.5%. PHL's capital-side construction gives 3.35: (PWT 2023 `K/Y`
  3.97 − ICSD public capital 0.38) × 0.80 domestic share + 0.48 domestically held debt. The PHL docs
  put balance-sheet estimates at about 2.3–2.6× GDP. The table is not in released OG-Core docs: it
  is in rickecon's PR #1220 (closed, unmerged) and open PR #1250. The PWT ratio moved from 3.33
  (2019) to 3.97 (2023); the 3.33 is only in the session notes.
- **Evidence:** [PSLmodels/OG-Core#1250](https://github.com/PSLmodels/OG-Core/pull/1250) (open,
  `calibration.md` table); [PSLmodels/OG-Core#1220](https://github.com/PSLmodels/OG-Core/pull/1220)
  (closed); [macro.md at 52b77ca](https://github.com/marcelolafleur/OG-PHL/blob/52b77ca7657f2a98cae7c994023e7e090772bf32/docs/book/content/calibration/macro.md)
  ("Initial household wealth").
- **When:** 2026-07 (PHL construction); 2026-09 and 2026-10 (OG-Core PRs).

### Initial household wealth: measured wealth and the IIP foreign share cannot both hold

- **Lesson:** where model `K/Y` overshoots the PWT, keep the wealth anchor and document the
  initial foreign-share miss with its cause.
- **What happened:** with initial wealth at the measured 3.35, the model's initial foreign capital
  share is about 35% against the IIP's 20%. The model wants `K(0)/Y` near 4.5 against the PWT's
  3.97. Hitting the IIP share would have needed household wealth near 4.3, against the measured
  3.35 (about 28% more). The calibration kept the wealth anchor.
- **Evidence:** [macro.md at 52b77ca](https://github.com/marcelolafleur/OG-PHL/blob/52b77ca7657f2a98cae7c994023e7e090772bf32/docs/book/content/calibration/macro.md)
  ("A documented tension"); [commit 52b77ca](https://github.com/marcelolafleur/OG-PHL/commit/52b77ca7657f2a98cae7c994023e7e090772bf32);
  [PR #85](https://github.com/EAPD-DRB/OG-PHL/pull/85).
- **When:** 2026-07.

### Initial household wealth: the old default scale was a windfall

- **Lesson:** with the initial-wealth parameters unset, ogcore rescales initial wealth so aggregate
  `B(0) = B_ss` (still true in 0.25.2); for a young
  population that is a windfall that shows up only in level exercises.
- **What happened:** for PHL the rescale factor was 1.625, a 63% windfall for every household.
  Retirees consumed at 3–7× steady state for years. Aggregate consumption jumped 41% for one year,
  domestic investment fell to about 2% of its long-run level, and debt was paid down to about 50%
  of GDP against the 60% target. Reform-minus-baseline tables hid it. The fix is
  `initial_wealth_ratio` (PSLmodels/OG-Core#1189, open), set so the solved `B(0)/Y(0)` is 3.35
  (delivered 3.3487).
- **Evidence:** [PSLmodels/OG-Core#1188](https://github.com/PSLmodels/OG-Core/issues/1188) (open);
  [PSLmodels/OG-Core#1189](https://github.com/PSLmodels/OG-Core/pull/1189) (open);
  [commit 62ca82e](https://github.com/marcelolafleur/OG-PHL/commit/62ca82e86223905df77bb342d205f98ed628503d);
  [CHANGELOG at 52b77ca, "Anchored initial household wealth"](https://github.com/marcelolafleur/OG-PHL/blob/52b77ca7657f2a98cae7c994023e7e090772bf32/CHANGELOG.md).
  The "3–7×" figure is only in the session notes.
- **When:** 2026-07 (ogcore 0.18.0; fix on the #1189 branch).

### Initial wealth: the released parameters, a data shape, and beta tuned to the first year

- **Lesson:** set the start with `initial_wealth_ratio` and `initial_hhwealth_dist`; where the
  population is far from stationary, tune `beta` to first-year moments rather than the steady-state
  `K/Y` (macro-open-economy.md, "Initial household wealth" and "Patience (beta_annual)").
- **What happened:** with `beta` tuned so the steady state held today's capital (3.59 times GDP),
  households starting from measured wealth (3.35 times GDP) consumed 80.8% of GDP in 2025 against
  76.1% in the data, and invested 20.2% against 23.6%. An age shape from NTA private asset income
  (2015) did not remove it: every age still held about 1.6 times its steady-state wealth, because the
  population is young (14% of adults over 60 in 2025, 31% in the steady state). Tuning `beta` to 2025
  investment instead (0.9027) gave consumption 75.1% and investment 23.8% in 2025; the steady state
  then holds 3.69 times GDP in private capital, more than today, as an ageing population should.
- **Evidence:** [EAPD-DRB/OG-PHL#111](https://github.com/EAPD-DRB/OG-PHL/pull/111) (`ogphl/initial_wealth.py`, the households and macro chapters).
- **When:** 2026-11, ogcore 0.24.4.

## og-country-calibration/references/fiscal-consistency.md

### The budget identity: alpha_I belongs in it

- **Lesson:** forgetting `alpha_I` mis-sets `alpha_G` by the whole public-investment share; check
  that `alpha_I` itself is sourced.
- **What happened:** PHL's public-investment share is about 5% of GDP, so leaving it out would
  have moved `alpha_G` by about 5pp. The PHL identity includes it (`alpha_G` = revenue − `pb*` −
  `alpha_T` − `alpha_I`), and a test pins it. `alpha_I` is sourced from the MTFF infrastructure
  program: [0.053, 0.051, 0.051, 0.052]. The audit pass caught that the 2025 value (5.3%) had been
  missed when the start year moved. There is no record that PHL ever shipped without `alpha_I`;
  the 5pp is the size of the share.
- **Evidence:** [commit a2a7376](https://github.com/marcelolafleur/OG-PHL/commit/a2a737605dfe379beec950898bd816dffa7d51d2)
  (`test_fiscal_identity_alpha_g`); [commit 52b77ca](https://github.com/marcelolafleur/OG-PHL/commit/52b77ca7657f2a98cae7c994023e7e090772bf32)
  (alpha_I re-mapped); [macro.md at 52b77ca](https://github.com/marcelolafleur/OG-PHL/blob/52b77ca7657f2a98cae7c994023e7e090772bf32/docs/book/content/calibration/macro.md).
- **When:** 2026-07.

### The budget identity: the residual is the consolidation gap

- **Lesson:** after capturing all recurring revenue, name the gap between model `G/Y` and observed
  spending as actual primary balance minus `pb*`.
- **What happened:** the actual FY2024 primary deficit was 2.8% of GDP (BTr). The model's `pb*` is
  −0.7%. So the steady state embeds about 2pp of consolidation. Model `alpha_G` is 0.1045 against
  roughly 13% observed on a primary basis.
- **Evidence:** [macro.md at 52b77ca](https://github.com/marcelolafleur/OG-PHL/blob/52b77ca7657f2a98cae7c994023e7e090772bf32/docs/book/content/calibration/macro.md)
  ("Government expenditures"); [CHANGELOG at 52b77ca](https://github.com/marcelolafleur/OG-PHL/blob/52b77ca7657f2a98cae7c994023e7e090772bf32/CHANGELOG.md);
  [PR #85](https://github.com/EAPD-DRB/OG-PHL/pull/85).
- **When:** 2026-07.

### Transition-path validation against the fiscal program: compare the baseline paths

- **Lesson:** compare the baseline TPI paths of the primary balance, debt, revenue and `I_g/Y`
  with the government's medium-term program over the first 10–15 years.
- **What happened:** PHL built a figure of model paths against BTr actuals (2022–2024) and the
  DBCC MTFF 2022–2030 midterm update. It first exposed the initial-wealth windfall (a revenue spike
  and a debt paydown to about 50%). After the fix the solved primary balance is −2.51 in 2025
  (program −2.51) and −2.20 in 2026 (program −2.22), and runs 0.3–1.1pp looser in 2027–28. Revenue
  uses a +3.78pp bridge from national-government cash to general government, from one OECD-vs-BTr
  overlap year (2023).
- **Evidence:** [commit 690c5d0](https://github.com/marcelolafleur/OG-PHL/commit/690c5d00a40d4191eacc81135398eb2c949ab0b5)
  (figure and section); [macro.md at 52b77ca](https://github.com/marcelolafleur/OG-PHL/blob/52b77ca7657f2a98cae7c994023e7e090772bf32/docs/book/content/calibration/macro.md)
  ("Fiscal paths against actuals and the program"); [PR #85](https://github.com/EAPD-DRB/OG-PHL/pull/85).
  The docs at 52b77ca still quote 0.6–1.3pp and an older glide; the PR #85 body has the final
  numbers.
- **When:** 2026-07.

### The alpha_G glide: a flat alpha_G pays debt far below target

- **Lesson:** put `alpha_G` on the government's consolidation schedule instead of a flat identity
  value.
- **What happened:** with the flat value the model consolidated four years ahead of the plan and
  paid debt down to about 48% of GDP before returning to target. On the MTFF glide the trough rose
  to about 50%; the rest was the initial-wealth windfall. The final glide is [0.1122, 0.1092,
  0.1045] for 2025, 2026 and 2027 on. The earlier note's "58–61% program band" is not in the repo
  text.
- **Evidence:** [commit 690c5d0](https://github.com/marcelolafleur/OG-PHL/commit/690c5d00a40d4191eacc81135398eb2c949ab0b5);
  [CHANGELOG at 52b77ca](https://github.com/marcelolafleur/OG-PHL/blob/52b77ca7657f2a98cae7c994023e7e090772bf32/CHANGELOG.md)
  ("`alpha_G` is now a declining path"); [PR #85](https://github.com/EAPD-DRB/OG-PHL/pull/85).
- **When:** 2026-07.

## og-country-calibration/references/taxes-informality.md

### Payroll is additive on top of the ETR function

- **Lesson:** `tau_payroll` collects on the whole wage bill on top of the income-tax function;
  audit the combined take and set `frac_tax_payroll` to the data split.
- **What happened:** `tau_payroll = 0.14` was collecting a hidden 5.8% of GDP on top of a flat 20%
  ETR. With `frac_tax_payroll = 0` it all reported on the PIT line. The fix: `tau_payroll` 0.0675
  (SSC 2.78% of GDP ÷ labour share 0.412) and `frac_tax_payroll` 0.4712 (2.78/(2.78+3.12)).
- **Evidence:** [commit a2a7376](https://github.com/marcelolafleur/OG-PHL/commit/a2a737605dfe379beec950898bd816dffa7d51d2);
  [CHANGELOG at 52b77ca](https://github.com/marcelolafleur/OG-PHL/blob/52b77ca7657f2a98cae7c994023e7e090772bf32/CHANGELOG.md)
  ("Social security contributions"); [taxes.md at 52b77ca](https://github.com/marcelolafleur/OG-PHL/blob/52b77ca7657f2a98cae7c994023e7e090772bf32/docs/book/content/calibration/taxes.md).
- **When:** 2026-07.

### Progressive-fit recipe: φ2 carries the effective-rate wedge (also ZAF)

- **Lesson:** anchor φ0 to the statutory top rate, fit φ1 to the schedule's shape, and tune φ2
  in-model to PIT collections.
- **What happened:** PHL's GS triple is [0.35, 1.196, 1.9e-8]. φ0 is the TRAIN top rate. φ1 is a
  least-squares fit to the TRAIN schedule (RMSE 1.7pp). The statutory-fit φ2 (5.0e-8) collected
  5.9% of GDP; tuned to 1.9e-8 it gives PIT 3.12% of GDP. The flat 20% ETR it replaced collected
  more PIT than the whole actual tax take. GS smoothing leaves the sub-threshold rate near zero,
  not zero; a test bounds it below 1.5% at ₱200,000 (80% of the ₱250,000 exemption).
- **Evidence:** [taxes.md at 52b77ca](https://github.com/marcelolafleur/OG-PHL/blob/52b77ca7657f2a98cae7c994023e7e090772bf32/docs/book/content/calibration/taxes.md);
  [commit a2a7376](https://github.com/marcelolafleur/OG-PHL/commit/a2a737605dfe379beec950898bd816dffa7d51d2);
  [tests/test_taxes.py at 52b77ca](https://github.com/marcelolafleur/OG-PHL/blob/52b77ca7657f2a98cae7c994023e7e090772bf32/tests/test_taxes.py#L84).
- **When:** 2026-07.

### Progressive-fit recipe: revenue's response to φ2 is concave

- **Lesson:** cutting φ2 cuts revenue by less than proportionally; expect two or three in-model
  iterations.
- **What happened:** φ2 fell to 0.38 of its statutory-fit value (5.0e-8 → 1.9e-8) while PIT
  revenue fell only to 0.53 of its value (5.9% → 3.12% of GDP). Top incomes sit near φ0 whatever φ2
  is.
- **Evidence:** [taxes.md at 52b77ca](https://github.com/marcelolafleur/OG-PHL/blob/52b77ca7657f2a98cae7c994023e7e090772bf32/docs/book/content/calibration/taxes.md)
  ("Personal income taxes"). The iteration count is not recorded in the repo.
- **When:** 2026-07.

### Capturing non-tax and residual-tax revenue: leaving it out forces spending too low

- **Lesson:** map recurring non-tax revenue and residual taxes to the instrument that prices the
  same margin, and tune each to collections.
- **What happened:** about 4.1% of GDP had no instrument. It was mapped as: property-type taxes
  (OECD "other taxes" less estate, 1.32%) on the wealth tax; BTr income (about 1.00%) plus
  unallocable income taxes (0.30%) on the CIT adjustment factor (0.406 → 0.583); recurring fees
  (about 0.55%) on `tau_c` (0.1263 → 0.1451). One-off items were excluded. Modelled resources rose
  to 19.5% of GDP against about 19.4% actual, and `alpha_G` rose from 0.0694 to 0.1045.
- **Evidence:** [commit fe18125](https://github.com/marcelolafleur/OG-PHL/commit/fe181253bc6ccc5a45f3618c00ae6b8e49b7f9bf);
  [CHANGELOG at 52b77ca](https://github.com/marcelolafleur/OG-PHL/blob/52b77ca7657f2a98cae7c994023e7e090772bf32/CHANGELOG.md)
  ("Captured previously unmodeled government revenue"); [taxes.md at 52b77ca](https://github.com/marcelolafleur/OG-PHL/blob/52b77ca7657f2a98cae7c994023e7e090772bf32/docs/book/content/calibration/taxes.md).
- **When:** 2026-07.

### Capturing non-tax and residual-tax revenue: property-type taxes on the wealth tax

- **Lesson:** `h_wealth = 1` with a small positive `m_wealth` makes the wealth tax a flat rate
  `p_wealth`, which prices recurrent property taxes on the saving margin.
- **What happened:** PHL set `h_wealth = 1`, `m_wealth = 0.001` and `p_wealth = 0.00348` (a 0.35%
  annual rate on wealth). It collects 1.32% of GDP, the OECD "other taxes" residual net of estate
  and donor taxes.
- **Evidence:** [taxes.md at 52b77ca](https://github.com/marcelolafleur/OG-PHL/blob/52b77ca7657f2a98cae7c994023e7e090772bf32/docs/book/content/calibration/taxes.md)
  ("Property-type taxes: the wealth tax instrument"); [commit fe18125](https://github.com/marcelolafleur/OG-PHL/commit/fe181253bc6ccc5a45f3618c00ae6b8e49b7f9bf).
- **When:** 2026-07.

### Statutory-for-effective errors bias reforms: a CIT cut's effect doubled

- **Lesson:** a misstated effective rate mis-sizes every reform that runs through the instrument.
- **What happened:** OG-Core's effective CIT is `cit_rate` × 0.7 × the adjustment factor. Moving
  the factor from 0.406 to 0.583 turned the same 25% → 20% statutory cut into a larger effective
  cut (0.05 × 0.7 × 0.406 = 1.42pp before, 2.04pp after). The reform's steady-state GDP effect is
  +0.91% in PR #85. The earlier figure (+0.42%) is only in the session notes.
- **Evidence:** [CHANGELOG at 52b77ca](https://github.com/marcelolafleur/OG-PHL/blob/52b77ca7657f2a98cae7c994023e7e090772bf32/CHANGELOG.md)
  (0.3 → 0.406 → 0.583); [PR #85](https://github.com/EAPD-DRB/OG-PHL/pull/85) (reform table). The
  before figure: not found in any repo or PR (searched: OG-PHL CHANGELOG, PR #85 and #68 bodies
  and comments); session notes only.
- **When:** 2026-07.

### Standing check: the bequest tax at a statutory rate collected 17x actual estate revenue

- **Lesson:** compute `tau_bq` from collections ÷ model bequest flows; a value equal to a statutory
  rate, or copied from a sibling, is the error (taxes-informality.md, "Standing check: the bequest
  tax").
- **What happened:** OG-PHL shipped `tau_bq` 0.06, the statutory estate-tax rate, from its initial
  files. In the model it collected 1.19% of GDP, against actual estate and donor collections of
  about 0.07% (17 times too much). The fiscal recalibration set it to 0.0035, tuned so the model's
  bequest revenue matches BIR estate and donor collections (0.0007 of GDP in the PR's fit table).
- **Evidence:** commit a2a7376 (`tau_bq` 0.06 → 0.0035):
  https://github.com/EAPD-DRB/OG-PHL/commit/a2a737605dfe379beec950898bd816dffa7d51d2 ;
  PR EAPD-DRB/OG-PHL#85 (open), "Revenue" section and fit table:
  https://github.com/EAPD-DRB/OG-PHL/pull/85 ; the 0.06 is on upstream `main`.
- **When:** 2026-07 (branch calib/remittances).

## og-country-calibration/references/households-demographics.md

### Earnings: the single-scalar Gini tilt

- **Lesson:** reuse OG-USA's `e` matrix and tilt it with one scalar so the model Gini matches the
  country's.
- **What happened:** OG-PHL's `get_e_interp` solves `e_PHL = e_USA · exp(a · e_USA)` for `a` by
  bisection on [−1, 1]. Strictly, it matches a ratio: model PHL Gini ÷ model USA Gini = 40.7 ÷ 41.5
  (World Bank data Ginis).
- **Evidence:** [ogphl/income.py at upstream main](https://github.com/EAPD-DRB/OG-PHL/blob/774267ac516761c519fd8a4fc86d130250e6a84a/ogphl/income.py#L131);
  [commit 2ef28b1](https://github.com/EAPD-DRB/OG-PHL/commit/2ef28b19e76c47464e40ca2ed5049d31bc26fb8e)
  ([PR #9](https://github.com/EAPD-DRB/OG-PHL/pull/9)).
- **When:** 2024-08.

### Demographics: one named UN country code

- **Lesson:** use a single named `UN_COUNTRY_CODE` constant at both call sites, and test it.
- **What happened:** OG-PHL defines `UN_COUNTRY_CODE = "608"` in `calibrate.py` and uses it at both
  `get_pop_objs` call sites and in `update_baseline_demographics.py`. The audit pass added a test
  that asserts it is 608.
- **Evidence:** [ogphl/calibrate.py at upstream main](https://github.com/EAPD-DRB/OG-PHL/blob/774267ac516761c519fd8a4fc86d130250e6a84a/ogphl/calibrate.py#L8)
  (since [commit f994abe](https://github.com/EAPD-DRB/OG-PHL/commit/f994abe5ddac11d5d99a31c15686e14c21c56a05));
  [tests/test_calibrate.py at 52b77ca](https://github.com/marcelolafleur/OG-PHL/blob/52b77ca7657f2a98cae7c994023e7e090772bf32/tests/test_calibrate.py#L133).
- **When:** 2024-08 (constant); 2026-07 (test).

### Discontinuities: a loosened RC_TPI in the packaged JSON (also KOR)

- **Lesson:** a sibling's JSON may carry a loosened `RC_TPI`; justify it with a per-period error
  table or tighten it.
- **What happened:** OG-PHL ships `RC_TPI = 0.01`, 100 times OG-Core's default 1e-4. It was raised
  from 0.001 in January 2026, described in the CHANGELOG as temporary. No per-period table
  justifies it.
- **Evidence:** [commit f3fc281](https://github.com/EAPD-DRB/OG-PHL/commit/f3fc28111e5698998c76bb074c1b09d4ecfec601)
  in [PR #41](https://github.com/EAPD-DRB/OG-PHL/pull/41);
  [JSON at upstream main, line 2455](https://github.com/EAPD-DRB/OG-PHL/blob/774267ac516761c519fd8a4fc86d130250e6a84a/ogphl/ogphl_default_parameters.json#L2455).
- **When:** 2026-01 (ogcore >= 0.14.5); still 0.01 on main in 2026-10.

### Labour supply calibrated to hours per person by age

- **Lesson:** compare the model's labour supply by age with hours per person by age, calibrate
  `chi_n` to it with a warm start between solves, and make the earnings profile per hour
  (households-demographics.md, "Hours of work by age (chi_n)").
- **What happened:** with OG-USA's `chi_n`, the model worked about 45% of the time endowment at every
  age up to 55 and a third at 75, against 29% and 5% in the 2024 Labor Force Survey (ILOSTAT), though
  total hours per working-age person were 7% above the US. The OG-ETH loop, run from a cold start,
  failed at its second solve; warm-starting each solve converged in about ten. Prime-age weights came
  out at 240–510 against 20–25 in OG-USA; ages 20–21 and from about 77 reached OG-Core's bound of
  10,000 and were left out of the fit. The NTA labour-income profile was divided by hours per person
  before reshaping `e`.
- **Evidence:** [EAPD-DRB/OG-PHL#111](https://github.com/EAPD-DRB/OG-PHL/pull/111) (`ogphl/labor.py`, `scripts/fetch_ilo_hours_by_age.py`, the households
  chapter's hours table).
- **When:** 2026-11, ogcore 0.24.4.

## og-country-calibration/references/validation-dashboard.md

### Sourcing hierarchy: the OECD Revenue Statistics country note

- **Lesson:** for the revenue side, the OECD Revenue Statistics country note gives every
  instrument on one basis; pair it with the treasury report for non-tax revenue and interest.
- **What happened:** OG-PHL's whole revenue side is anchored to OECD Revenue Statistics in Asia and
  the Pacific 2025 (data for 2023): PIT 3.12, SSC 2.78, CIT 2.90, goods and services 7.39, other
  taxes 1.39, total 17.88% of GDP. Non-tax revenue, interest and the primary balance come from the
  BTr FY2024 Cash Operations Report.
- **Evidence:** [taxes.md at 52b77ca](https://github.com/marcelolafleur/OG-PHL/blob/52b77ca7657f2a98cae7c994023e7e090772bf32/docs/book/content/calibration/taxes.md)
  (target table and sources); [CHANGELOG at 52b77ca](https://github.com/marcelolafleur/OG-PHL/blob/52b77ca7657f2a98cae7c994023e7e090772bf32/CHANGELOG.md).
- **When:** 2026-07.

### Know the family traits: model K/Y runs high

- **Lesson:** model `K/Y` runs high against the PWT across the family; report it with a reason,
  but rule out an untuned lever first.
- **What happened:** PHL's single-industry steady state had `K/Y` 4.29 after PR #68, against a PWT
  ratio of 3.97 (2023). At the start of the transition the model wants `K(0)/Y` near 4.5. ZAF shows
  the same (4.5 against 3.7).
- **Evidence:** [PR #63 comment](https://github.com/EAPD-DRB/OG-PHL/pull/63#issuecomment-4877252964)
  (single-industry K/Y 4.29); [macro.md at 52b77ca](https://github.com/marcelolafleur/OG-PHL/blob/52b77ca7657f2a98cae7c994023e7e090772bf32/docs/book/content/calibration/macro.md)
  ("A documented tension").
- **When:** 2026-07.

### Verify both tails of every path: the min-only debt check

- **Lesson:** for every path claim report the min and max with their years, and look at the plot.
- **What happened:** while testing `initial_wealth_ratio`, a check of the debt path's minimum
  ("trough 60.0, stays on target") passed while the path climbed to about 74% of GDP around 2046.
  The check tested only the direction of the previous failure (the paydown). The user caught it.
  The final docs report both tails: about 59% at the low, about 70% around 2046, then back to 0.60.
- **Evidence:** [macro.md at 52b77ca](https://github.com/marcelolafleur/OG-PHL/blob/52b77ca7657f2a98cae7c994023e7e090772bf32/docs/book/content/calibration/macro.md)
  (fiscal-paths figure caption, both tails). The caught check and the 74%: not found in any repo or
  PR (searched: OG-PHL CHANGELOG and docs, PR #85, PSLmodels/OG-Core#1188 and #1189 bodies and
  comments); session notes only.
- **When:** 2026-07.

### GDP price basis: ratios to market-price GDP

- **Lesson:** compare model and data ratios on one price basis (validation-dashboard.md, "One GDP
  basis: market prices").
- **What happened:** OG-Core's `Y` is the sum of `p_m Y_m`, with the consumption tax paid on top, so
  it excludes product taxes, while every Philippine target is a share of market-price GDP. With a
  consumption tax near 7.9% of GDP, every model ratio over `Y` sat about 8% above the same quantity
  over market-price GDP (a factor of 1.086). A 2018 SAM cross-check gave 1.089. Converting the
  share parameters by that factor and re-tuning moved `beta` from 0.846 to 0.875 and the steady-state
  `r` from 11.4% to 10.2%. The ILO labour share (denominator: market-price GDP) was converted the
  same way, giving a total capital share of 0.515. The literature makes the same adjustment
  (Prescott 2004; Mendoza, Razin and Tesar 1994).
- **Evidence:** [EAPD-DRB/OG-PHL#111](https://github.com/EAPD-DRB/OG-PHL/pull/111) (`ogphl/targets.py`, the macro chapter's "GDP at market prices"
  section).
- **When:** 2026-11, ogcore 0.24.4.

## og-country-calibration/references/solving-tuning.md

### Run engineering: steady state through the client, and the two-phase driver

- **Lesson:** older measurements found the SS slower through the worker client than serial; on a
  current ogcore treat that as a finding, not a reason to build a serial driver.
- **What happened:** during the initial-wealth work the SS through a 7-worker dask client took 12+
  minutes against 66 seconds serial. A hand driver (SS serial, pickle, TPI with the client) was
  used for speed. It is not the example pattern.
- **Evidence:** not found in any repo or PR (searched: OG-PHL CHANGELOG, docs and examples on
  `calib/remittances`, PR #85, PSLmodels/OG-Core#1188 and #1189 bodies and comments); session notes
  only.
- **When:** 2026-07 (ogcore 0.18.0 plus the #1189 branch).

### Run engineering: why Anderson

- **Lesson:** Anderson acceleration cuts transition iterations sharply; it is TPI-only.
- **What happened:** on the M=1 PHL baseline, `TPI_outer_method = "anderson"` solved the transition
  in 11–12 iterations (about 2 minutes) instead of about 30–70 (about 20 minutes), with distances
  falling monotonically. It was validated on the baseline, the reform and the initial-wealth runs
  and is now in the packaged parameters.
- **Evidence:** [commit 62ca82e](https://github.com/marcelolafleur/OG-PHL/commit/62ca82e86223905df77bb342d205f98ed628503d);
  [CHANGELOG at 52b77ca](https://github.com/marcelolafleur/OG-PHL/blob/52b77ca7657f2a98cae7c994023e7e090772bf32/CHANGELOG.md)
  ("`TPI_outer_method = \"anderson\"`"); [PR #85](https://github.com/EAPD-DRB/OG-PHL/pull/85)
  ("Tested").
- **When:** 2026-07.

### The in-model tuning loop: real solves are cheap

- **Lesson:** tune several dials together with real warm-start SS solves and a revenue dashboard;
  ship the tuning script.
- **What happened:** with warm guesses a PHL SS solve took seconds (PR #68: about 25 seconds cold),
  so the revenue dials (GS φ2, `tau_c`, CIT adjustment, `p_wealth`, `r_gov_shift`, `zeta_K`)
  converged in a few solve-and-adjust rounds. The tuning script stayed in a session scratchpad:
  OG-PHL does not ship `examples/tune_ss.py`.
- **Evidence:** [PR #68](https://github.com/EAPD-DRB/OG-PHL/pull/68) (cold-solve time); the
  iteration count and script: not found in any repo (searched: OG-PHL `examples/` and `tests/` on
  `calib/remittances`, PR #85); session notes only.
- **When:** 2026-07.

### Derived parameters regenerate together

- **Lesson:** anything computed from demographics belongs in the regeneration tool, with a test
  that the packaged value equals the constructor's output.
- **What happened:** `g_RM` (from `g_n`) and `eta_RM` (from `omega_SS`) are rebuilt by
  `update_baseline_demographics`. `test_packaged_g_rm_is_consistent_with_packaged_g_n` catches a
  stale `g_RM`. Both were regenerated when the start year moved to 2025.
- **Evidence:** [commit 6450e60](https://github.com/marcelolafleur/OG-PHL/commit/6450e60c61abe606cdcfa0839ffd96ccefdc9cd8)
  (`g_RM`); [commit fe18125](https://github.com/marcelolafleur/OG-PHL/commit/fe181253bc6ccc5a45f3618c00ae6b8e49b7f9bf)
  (`eta_RM`); [tests/test_remittances.py at 52b77ca](https://github.com/marcelolafleur/OG-PHL/blob/52b77ca7657f2a98cae7c994023e7e090772bf32/tests/test_remittances.py#L88).
- **When:** 2026-07.

## og-country-calibration/references/calibration-pr.md

### Preparing the calibration PR: what the PHL #63 review asked for

- **Lesson:** show before/after tables of every changed object, pre-empt the `gamma_g` question,
  keep PR annotations out of docs figures, and explain derived fixes in plain language.
- **What happened:** on PR #63 jdebacker asked first for a new-vs-old `io_matrix` side-by-side.
  The reply showed household energy moving off manufacturing (54% → 4%) onto electricity
  (11% → 74%). He flagged that subtracting `gamma_g` implicitly took public capital out of labour;
  the builder now rescales total capital shares to 0.588 and then subtracts 0.05. He asked that a
  dashed "what changed" line be dropped from the docs figure, and that the multisector JSON hold
  only the changed parameters. The sentence "ask before push, never in the same step" is the
  user's own working rule, not part of jdebacker's review.
- **Evidence:** [io_matrix request](https://github.com/EAPD-DRB/OG-PHL/pull/63#issuecomment-4812233777)
  and [reply](https://github.com/EAPD-DRB/OG-PHL/pull/63#issuecomment-4835605904);
  [gamma_g comment](https://github.com/EAPD-DRB/OG-PHL/pull/63#discussion_r3483275465) and
  [reply](https://github.com/EAPD-DRB/OG-PHL/pull/63#discussion_r3493790674)
  ([commit dc0017d](https://github.com/marcelolafleur/OG-PHL/commit/dc0017d51df46aa966b1f1e4102ac61e21039100));
  [figure comment](https://github.com/EAPD-DRB/OG-PHL/pull/63#discussion_r3483239884);
  [overlay comment](https://github.com/EAPD-DRB/OG-PHL/pull/63#discussion_r3615976213).
- **When:** 2026-06 to 2026-07.

## og-multi-industry-calibration/references/inputs.md

### Finding the data: check the make matrix

- **Lesson:** compute the make matrix's off-diagonal share; exactly 0 means a diagonal make.
- **What happened:** in the 2018 IFPRI PHL SAM the off-diagonal share is exactly 0: each commodity
  `cX` is made only by activity `aX`. The builder pairs them one to one.
- **Evidence:** [ogphl/input_output.py at ec2ee98, line 229](https://github.com/marcelolafleur/OG-PHL/blob/ec2ee98dd11e877c3daea53231fbc9279e1256f7/ogphl/input_output.py#L229);
  the share recomputed from `ogphl/data/002_IFPRI_SAM_PHL_2018_SAM.csv` at ec2ee98 on 2026-10-19.
- **When:** 2026-06.

### Concordances: unchecked mappings ship silently wrong

- **Lesson:** every code in `PROD_DICT` and `CONS_DICT` must be in the data; `isin` skips what it
  cannot match, so test the partition.
- **What happened:** `CONS_DICT["Food"]` lists `"ccott"`, which is not a code in the SAM. It has
  been there since August 2024 and is on upstream main too. Here nothing is lost, because the SAM
  has no cotton commodity and every SAM commodity is mapped. But `get_alpha_c` and the `io_matrix`
  builders sum with `sam.index.isin(...)`, so a misspelled real code would drop out the same way,
  and no test checks the partition.
- **Evidence:** [ogphl/constants.py at ec2ee98, line 323](https://github.com/marcelolafleur/OG-PHL/blob/ec2ee98dd11e877c3daea53231fbc9279e1256f7/ogphl/constants.py#L323);
  [the SAM at ec2ee98](https://github.com/marcelolafleur/OG-PHL/blob/ec2ee98dd11e877c3daea53231fbc9279e1256f7/ogphl/data/002_IFPRI_SAM_PHL_2018_SAM.csv)
  (no `ccott` row or column); added in [commit f994abe](https://github.com/EAPD-DRB/OG-PHL/commit/f994abe5ddac11d5d99a31c15686e14c21c56a05).
- **When:** 2024-08 (added); checked 2026-10-19 at ec2ee98.

### Defining industries and goods: what rides along in a utility split

- **Lesson:** split out what the policy questions need, and check what else rides along.
- **What happened:** PHL split the old Utilities into Electricity (`aelec`) and Water (`awatr`).
  The employment side maps PSA Labor Force Survey section D to Electricity and section E
  ("Water/waste") to Water, so Water carries waste. Section D is the PSIC electricity, gas, steam
  and air-conditioning section.
- **Evidence:** [ogphl/constants.py at ec2ee98](https://github.com/marcelolafleur/OG-PHL/blob/ec2ee98dd11e877c3daea53231fbc9279e1256f7/ogphl/constants.py)
  (`PROD_DICT`); [ogphl/input_output.py at ec2ee98, line 335](https://github.com/marcelolafleur/OG-PHL/blob/ec2ee98dd11e877c3daea53231fbc9279e1256f7/ogphl/input_output.py#L335);
  [commit bdb34e7](https://github.com/marcelolafleur/OG-PHL/commit/bdb34e78cf9711761500c5cc09fb604d28ab7577).
- **When:** 2026-06.

### Defining industries and goods: five household goods

- **Lesson:** goods are household-relevant groups, typically food, energy, non-durables, durables,
  services.
- **What happened:** PHL uses I = 5: Food, Energy and water, Non-durables, Durables, Services.
- **Evidence:** [PR #63 comment](https://github.com/EAPD-DRB/OG-PHL/pull/63#issuecomment-4835605904)
  (row labels); [firms.md at ec2ee98](https://github.com/marcelolafleur/OG-PHL/blob/ec2ee98dd11e877c3daea53231fbc9279e1256f7/docs/book/content/calibration/firms.md).
- **When:** 2026-06.

### gamma_m: the rescale target lands exactly

- **Lesson:** rescale to the single model's total capital share, carve out `gamma_g` after, and
  check the private mean equals the base `gamma`.
- **What happened:** the target is 0.58785 (ILOSTAT labour share). After subtracting
  `gamma_g = 0.05` the value-added-weighted private mean is 0.53785, the base `gamma`. PHL moved
  the carve-out after the rescale following jdebacker's review; per-industry shares shifted by up
  to 2pp.
- **Evidence:** [firms.md at ec2ee98](https://github.com/marcelolafleur/OG-PHL/blob/ec2ee98dd11e877c3daea53231fbc9279e1256f7/docs/book/content/calibration/firms.md)
  ("Private capital's share by industry"); [commit dc0017d](https://github.com/marcelolafleur/OG-PHL/commit/dc0017d51df46aa966b1f1e4102ac61e21039100);
  [review reply](https://github.com/EAPD-DRB/OG-PHL/pull/63#discussion_r3493790674).
- **When:** 2026-06.

### gamma_m: capital-intensive industries below 0.9 solve fine

- **Lesson:** healthy capital-intensive industries solve; imputed-rent-driven shares above 0.9
  break things.
- **What happened:** PHL's highest shares are Mining 0.785 and Electricity 0.782 (Water 0.684).
  The M=8 calibration solves by continuation.
- **Evidence:** [firms.md at ec2ee98](https://github.com/marcelolafleur/OG-PHL/blob/ec2ee98dd11e877c3daea53231fbc9279e1256f7/docs/book/content/calibration/firms.md)
  (table of `gamma_m` and `Z_m`).
- **When:** 2026-07.

### io_matrix: trace household energy through the Leontief inverse

- **Lesson:** the naive direct-use matrix puts most goods on manufacturing; the value-added trace
  puts household energy mostly on electricity.
- **What happened:** traced, PHL's energy row is 73.7% Electricity and 3.5% Manufacturing. The old
  direct-use row was 10.7% Electricity and 54.3% Manufacturing. Durables moved from 74%
  Manufacturing to 54% Construction.
- **Evidence:** [PR #63 side-by-side](https://github.com/EAPD-DRB/OG-PHL/pull/63#issuecomment-4835605904);
  [commit 0b08b7f](https://github.com/marcelolafleur/OG-PHL/commit/0b08b7ff54780878fc1f4f92d7c38b0608250389).
- **When:** 2026-06.

### Z_m: the capital-output ratio and survey capital stocks

- **Lesson:** take `K/Y` from PWT for the SAM year; its level barely matters. Reject
  establishment-survey capital stocks.
- **What happened:** PHL uses the PWT 10.01 2018 ratio, 2.91. The productivity ranking held across
  ratios from 2.9 to 5.3. The PIDS establishment-survey route (ASPBI/CPBI gross additions to fixed
  assets) was tried and rejected: it omits informal capital and would make Construction and
  Agriculture look most productive.
- **Evidence:** [ogphl/input_output.py at ec2ee98, `get_Z`](https://github.com/marcelolafleur/OG-PHL/blob/ec2ee98dd11e877c3daea53231fbc9279e1256f7/ogphl/input_output.py#L404);
  [commit 04f1dd1](https://github.com/marcelolafleur/OG-PHL/commit/04f1dd16122c24f3b7bfe54b3e0f0f59c493849c).
- **When:** 2026-06.

### Z_m: spot-check the ranking

- **Lesson:** check the Z ranking against what is known of the economy's sectors.
- **What happened:** Agriculture is lowest (Z 0.559), then Mining (0.579). Services (1.081) and
  the utilities (0.854 and 0.907) are high, against Manufacturing at 1. That fits low-productivity
  smallholder farming and a large services sector.
- **Evidence:** [firms.md at ec2ee98](https://github.com/marcelolafleur/OG-PHL/blob/ec2ee98dd11e877c3daea53231fbc9279e1256f7/docs/book/content/calibration/firms.md)
  ("Sector total factor productivity").
- **When:** 2026-06.

## og-multi-industry-calibration/references/alignment.md

### How OG-Core treats industries: the composite-price units constant

- **Lesson:** OG-Core's unnormalised composite price carries `k = prod_i alpha_c_i^(−alpha_c_i)`,
  which is 1 with one good and above 1 with several.
- **What happened:** PHL's five budget shares give k = 2.97 (2.9702). The same basket carries a
  price about 3× higher and a measured quantity about 3× smaller than in the single-good model.
- **Evidence:** [PR #63 comment](https://github.com/EAPD-DRB/OG-PHL/pull/63#issuecomment-4877252964);
  [firms.md at ec2ee98](https://github.com/marcelolafleur/OG-PHL/blob/ec2ee98dd11e877c3daea53231fbc9279e1256f7/docs/book/content/calibration/firms.md)
  ("Converting the utility weights").
- **When:** 2026-07.

### The chi units conversion: before and after

- **Lesson:** scale `chi_n` and `chi_b` by `k^(σ−1)` in the overlay; it is derived, not fitted.
- **What happened:** with k = 2.97, σ = 1.5 and a scale of 1.723, the M=8 steady state moved toward
  the single-industry one:

  | | single | M=8 before | M=8 after |
  |---|---|---|---|
  | r | 0.0708 | 0.0885 | 0.0808 |
  | K_f/K | 0.257 | 0.528 | 0.336 |
  | B/Y | 3.67 | 2.38 | 3.29 |
  | K/Y | 4.29 | 4.02 | 4.24 |
  | p_tilde·C/Y | 0.510 | 0.471 | 0.496 |

  It closed 44–80% of each gap. A Z-level rescale was tested first and moved r the wrong way.
- **Evidence:** [PR #63 comment](https://github.com/EAPD-DRB/OG-PHL/pull/63#issuecomment-4877252964);
  [commit 497c56b](https://github.com/marcelolafleur/OG-PHL/commit/497c56b510dabb1eb05209659b4afc1103d4f7cc);
  [commit 4988f99](https://github.com/marcelolafleur/OG-PHL/commit/4988f99ea9ac41d08a98461e3b72b26cedc8ac89) (docs).
- **When:** 2026-07 (ogcore 0.16.3).

### Reaching the steady state: wide relative prices defeat a cold solve

- **Lesson:** a cold solve fails when relative prices spread widely; solve by continuation from a
  flat anchor.
- **What happened:** PHL's solved prices span about 0.4 to 3.3 (the highest about 8 times the
  lowest). OG-Core seeds every price at 1 and its guess search moves only `r` and `TR`, so a direct
  solve diverged. `solve_ss_by_continuation` walks from a homogeneous anchor.
- **Evidence:** [firms.md at ec2ee98](https://github.com/marcelolafleur/OG-PHL/blob/ec2ee98dd11e877c3daea53231fbc9279e1256f7/docs/book/content/calibration/firms.md)
  ("Solving the Multi-Industry Steady State"); [PR #63](https://github.com/EAPD-DRB/OG-PHL/pull/63)
  ("Solving it").
- **When:** 2026-06 to 2026-07.

### Checking the solved model: run the same reform in both examples

- **Lesson:** run the same reform through the single and multi examples; different reforms make
  the comparison impossible.
- **What happened:** on the multi-industry branch, `examples/run_og_phl.py` runs a CIT cut to 0.20
  plus `debt_ratio_ss` 0.65. `examples/run_og_phl_multi_industry_calibrated.py` sets
  `REFORM_PARAMS = {"cit_rate": [[0.20]]}` only. So the two percent-change tables cannot be
  compared as they stand. The gap was noted as open in the local practitioner guide on 2026-07-03.
- **Evidence:** [examples/run_og_phl.py at ec2ee98, lines 79–80](https://github.com/marcelolafleur/OG-PHL/blob/ec2ee98dd11e877c3daea53231fbc9279e1256f7/examples/run_og_phl.py#L79);
  [examples/run_og_phl_multi_industry_calibrated.py at ec2ee98, line 318](https://github.com/marcelolafleur/OG-PHL/blob/ec2ee98dd11e877c3daea53231fbc9279e1256f7/examples/run_og_phl_multi_industry_calibrated.py#L318);
  local guide `OG-PHL/docs/single_multi_calibration_guide.md` (untracked).
- **When:** checked 2026-10-19 at ec2ee98; first noted 2026-07.

## og-solver-diagnosis/references/failure-taxonomy.md

### B. Binding constraint from a calibration placeholder: zeta_K 0.9

- **Lesson:** a `zeta_K = 0.9` placeholder drives `K_d` negative and trips the floor in
  `get_K_splits`; recalibrate it to the IIP.
- **What happened:** OG-PHL shipped `zeta_K = 0.9`. It implied about 96% foreign-owned capital
  against about 20% in the BSP IIP, and left domestic capital at about 4% of the stock, so the
  transition failed the resource constraint. PR #68 set it to 0.4 (normalised Chinn-Ito), and
  upstream main ships 0.4. The calibration branch later moved it to 0.47 (see the macro entry
  above). The "older logs showing the guard firing three times" were not found.
- **Evidence:** [commit 443fce5](https://github.com/EAPD-DRB/OG-PHL/commit/443fce5a73c8b3af915dd4108f72834e8e34df1b)
  in [PR #68](https://github.com/EAPD-DRB/OG-PHL/pull/68) (merged 2026-07-03);
  [JSON at upstream main, line 785](https://github.com/EAPD-DRB/OG-PHL/blob/774267ac516761c519fd8a4fc86d130250e6a84a/ogphl/ogphl_default_parameters.json#L785).
  Logs: not found (searched: `~/Projects` for "K_d has negative" in log and text files, OG-PHL
  checkouts).
- **When:** 2026-07 (ogcore 0.16.3).

### N. Slow transition from a straggler worker

- **Lesson:** a transition whose iterations are slow while one worker does the work points to state
  kept on that worker (the cached Jacobian sparsity pattern, or parameter copies deleted by dask's
  memory manager), not to the calibration or the hardware.
- **What happened:** after the 2026-11 recalibration the baseline took 20.2 minutes (60
  iterations, about 20 s each) on a 4-performance-core laptop with 7 workers, against 12.1 for the
  previous calibration. Run alone, each income group's household solve took 3–4 s. In parallel,
  the worker whose first problem belonged to the top income group detected a sparsity pattern
  missing more than half its links (the threshold was relative to the largest entry of the whole
  Jacobian), and the two lowest groups, which get no pension, left the pension links out of the
  pattern the other groups reused. That worker needed hundreds of Levenberg-Marquardt fallbacks per
  iteration. Turning the pension off made the run slower (37.7 minutes, a 55 s straggler task), so
  a "switch it off" test pointed the wrong way. Separately, dask's memory manager deleted the
  workers' copies of the 34 MB parameters between iterations, so tasks started 2–10 s apart. With
  the pattern fixed, the duplicate tax work removed and the copies kept, the baseline took 11.3
  minutes and the previous calibration 8.6, with results unchanged to about 1e-10. The run-id that
  should reset the pattern cache between runs (PSLmodels/OG-Core#1249) had also stopped working in
  0.24.2.
- **Evidence:** [PSLmodels/OG-Core#1276](https://github.com/PSLmodels/OG-Core/pull/1276) (pattern
  fixes); [PSLmodels/OG-Core#1277](https://github.com/PSLmodels/OG-Core/pull/1277) (net taxes once,
  Defined Benefits cache). The memory-manager change was tested but not proposed. Runs were the
  shipped example from installer copies with the OG-Core commits pinned; the probe logs are
  unpublished.
- **When:** 2026-11-10, ogcore 0.24.4.

## og-solver-diagnosis/references/solve-procedures.md

### Initial-guess fragility: nearness is not solvability

- **Lesson:** choose packaged guesses by solve-path robustness, not by closeness to the solution.
- **What happened:** after the revenue recalibration, guesses retuned to the exact solved values
  (r 0.0642, factor 181,540) sent the solver through a `K_d < 0` region and failed the steady state.
  The older guesses (r 0.064, TR 0.1324, factor 172,241) solved cleanly and were kept; they are
  what the branch ships.
- **Evidence:** the shipped guesses are in
  [the JSON at 52b77ca](https://github.com/marcelolafleur/OG-PHL/blob/52b77ca7657f2a98cae7c994023e7e090772bf32/ogphl/ogphl_default_parameters.json)
  and set in [commit a2a7376](https://github.com/marcelolafleur/OG-PHL/commit/a2a737605dfe379beec950898bd816dffa7d51d2).
  The failed near-exact guesses: not found in any repo or PR (searched: OG-PHL `calib/remittances`
  for 181540, CHANGELOG, PR #85); session notes only.
- **When:** 2026-07.

### Running against an unreleased ogcore: uv run --with-editable

- **Lesson:** `uv run --with-editable <ogcore-checkout>` can resolve ogcore from the uv cache, and
  a `python -c` probe from the checkout root hides it; use a worktree with its own venv.
- **What happened:** while running OG-PHL against the #1189 branch, `uv run --with-editable`
  resolved ogcore from the uv cache instead of the checkout. A `python -c` import probe from the
  repo root looked right because of cwd shadowing. A `sys.path` pin with an assert in the entry
  script caught the contamination.
- **Evidence:** not found in any repo or PR (searched: OG-PHL and OG-Core PR #1189 bodies and
  comments, OG-PHL CHANGELOG); session notes only.
- **When:** 2026-07.
