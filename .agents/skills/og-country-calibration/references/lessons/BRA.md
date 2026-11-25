<!-- GENERATED FILE - do not edit here.
     Source: docs/og-lessons/BRA.md
     Regenerate: python scripts/sync_shared.py -->

# Brazil (BRA): lessons behind the OG skills

What happened behind lessons in the OG skills (og-country-calibration,
og-multi-industry-calibration, og-solver-diagnosis, og-run). The skills teach the method; these
are one country's numbers, kept here so the skills stay general. They record what was true when
written; check the country repo before relying on any of them. Do not copy them into another
country's calibration.

Commits named below: `abd25de` is PSLmodels/OG-BRA main (2026-08-31). `73e07f9` is the head of
PR #10 (branch `multi-industry-data`, the M=9 calibration). `50144b5` is the head of PR #11
(branch `feature/single-industry-refresh`). Both PRs were open on 2026-10-19.

Contents (by the skill file each entry backs; search a file for its `###` headings)
- og-country-calibration/references/macro-open-economy.md
- og-country-calibration/references/taxes-informality.md
- og-country-calibration/references/households-demographics.md
- og-multi-industry-calibration/references/inputs.md
- og-multi-industry-calibration/references/alignment.md

## og-country-calibration/references/macro-open-economy.md

### zeta_K: the 0.9 placeholder is still on main

- **Lesson:** `zeta_K = 0.9` is a placeholder, and the Chinn-Ito index locates the range but is not
  the target; tune `zeta_K` until the solved `K_f/K` matches the IIP.
- **What happened:** OG-BRA main ships `zeta_K` 0.9, and the macro chapter justifies it only as
  "a high degree of openness". The value has been there since the initial files (June 2026). PR #10
  does not change it, so the M=9 branch also runs on 0.9. PR #11 changes it to 0.16, the normalized
  Chinn-Ito index for Brazil (2022), and its PR body reports no model `K_f/K` against the IIP. That
  takes Chinn-Ito as the target, which the skill names as a pitfall. An unpushed local branch,
  `single-calib-corrections` (fba756e), makes the same 0.16 change.
- **Evidence:**
  [main JSON, `zeta_K`](https://github.com/PSLmodels/OG-BRA/blob/abd25de301553dcb85d2f6d15229a362471cdec9/ogbra/ogbra_default_parameters.json#L1187);
  [main macro.md line 20](https://github.com/PSLmodels/OG-BRA/blob/abd25de301553dcb85d2f6d15229a362471cdec9/docs/book/content/calibration/macro.md#L20);
  [initial files commit eec58c4](https://github.com/PSLmodels/OG-BRA/commit/eec58c4397e61b9c41899ef15427e3385d181dcc)
  (PR [#2](https://github.com/PSLmodels/OG-BRA/pull/2));
  [PR #11](https://github.com/PSLmodels/OG-BRA/pull/11),
  [its CHANGELOG line 81](https://github.com/PSLmodels/OG-BRA/blob/50144b53174cb03af88048cf973c386887ddc9db/CHANGELOG.md#L81);
  local branch `single-calib-corrections` in `OG-BRA` (not pushed).
- **When:** 2026-06 (placeholder introduced), 2026-07 (PR #11), still on main at abd25de
  (2026-08, ogcore 0.20.0 in uv.lock).

### Capital share (gamma): split mixed income per industry first

- **Lesson:** when the table has a mixed-income row, split it between labour and capital per
  industry before rescaling the industry shares.
- **What happened:** Brazil's input-output table has a separate mixed-income row. OG-BRA splits it
  by Gollin's second adjustment at phi = 0.428. Agriculture is 47% mixed income; booking it all as
  capital gives a raw share of 0.81, a plain rescale still gives 0.72, and the split gives 0.55
  (0.50 after the public-capital carve-out). Detail in the gamma_m entries below.
- **Evidence:** [firms.md at 73e07f9, "Private capital's share by industry"](https://github.com/PSLmodels/OG-BRA/blob/73e07f98dd63a4b8d1a42f538f0407a7a14a1433/docs/book/content/calibration/firms.md#L52);
  [`get_gamma`, line 166](https://github.com/PSLmodels/OG-BRA/blob/73e07f98dd63a4b8d1a42f538f0407a7a14a1433/ogbra/input_output.py#L166);
  [PR #10](https://github.com/PSLmodels/OG-BRA/pull/10).
- **When:** 2026-07 (PR #10).

## og-country-calibration/references/taxes-informality.md

### Standing check: the bequest tax: BRA ships a rate with no basis

- **Lesson:** compute `tau_bq` from collections over model bequest flows; a value equal to a
  statutory rate, or copied from a sibling, is the error.
- **What happened:** OG-BRA main ships `tau_bq` 0.2, carried from the initial files, with no
  Brazilian source. Its taxes chapter says bequest taxes are set to zero, so docs and JSON
  disagree. PR #11 changes it to 0.04, the midpoint of the ITCMD state schedules (2–8%) and São
  Paulo's old flat rate, and fixes the docs. That is still a statutory rate, not collections over
  bequests; the chapter only notes that exemptions keep the effective rate "well below" 8%. PR #10
  leaves 0.2 in place.
- **Evidence:**
  [main JSON, `tau_bq`](https://github.com/PSLmodels/OG-BRA/blob/abd25de301553dcb85d2f6d15229a362471cdec9/ogbra/ogbra_default_parameters.json#L2461);
  [main taxes.md line 17](https://github.com/PSLmodels/OG-BRA/blob/abd25de301553dcb85d2f6d15229a362471cdec9/docs/book/content/calibration/taxes.md#L17)
  ("wealth and bequest taxes are set to zero");
  [PR #11](https://github.com/PSLmodels/OG-BRA/pull/11),
  [its taxes.md line 31](https://github.com/PSLmodels/OG-BRA/blob/50144b53174cb03af88048cf973c386887ddc9db/docs/book/content/calibration/taxes.md#L31),
  [its CHANGELOG line 86](https://github.com/PSLmodels/OG-BRA/blob/50144b53174cb03af88048cf973c386887ddc9db/CHANGELOG.md#L86).
- **When:** 2026-06 (0.2 introduced), 2026-07 (PR #11), still 0.2 on main at abd25de (2026-08).

### Informality: the maturity ladder: BRA is at "narrative only"

- **Lesson:** the first rung names informality as the reason effective rates sit far below
  statutory, picks a stylized flat rate and flags it provisional, with no mechanism.
- **What happened:** OG-BRA main's taxes chapter cites the broad exemption and "large informal
  sector", sets a stylized 12% effective PIT rate and 18% marginal rates, and says they should be
  updated from microdata. All noncompliance parameters are 0 and `income_tax_filer` is 1. PR #11
  replaces the PIT rates with DIRPF-based ones (ETR 0.07) and mentions that informal income never
  enters the declared base, but adds no mechanism. Both keep `tau_payroll` at the statutory 0.28.
- **Evidence:** [main taxes.md line 19](https://github.com/PSLmodels/OG-BRA/blob/abd25de301553dcb85d2f6d15229a362471cdec9/docs/book/content/calibration/taxes.md#L19);
  [main JSON, `tau_payroll`](https://github.com/PSLmodels/OG-BRA/blob/abd25de301553dcb85d2f6d15229a362471cdec9/ogbra/ogbra_default_parameters.json#L2464);
  [PR #11 taxes.md line 21](https://github.com/PSLmodels/OG-BRA/blob/50144b53174cb03af88048cf973c386887ddc9db/docs/book/content/calibration/taxes.md#L21).
- **When:** 2026-06 onward; still the state at abd25de (2026-08).

## og-country-calibration/references/households-demographics.md

### Earnings (the e ability matrix): BRA uses the Gini tilt

- **Lesson:** reuse OG-USA's `e` and apply the one-scalar tilt `e_USA · exp(a·e_USA)`, solving `a`
  so the model Gini matches the country's target.
- **What happened:** OG-BRA's `income.get_e_interp` implements the tilt, with `gini_usa_data` =
  41.5. `calibrate.py` calls it without `gini_to_match`, so the code default 50.3 is used. The
  docstring says the default is 52.0 (World Bank, BRA 2022). The code and docstring disagree.
- **Evidence:** [main income.py lines 15–41](https://github.com/PSLmodels/OG-BRA/blob/abd25de301553dcb85d2f6d15229a362471cdec9/ogbra/income.py#L15-L41);
  [main calibrate.py line 113](https://github.com/PSLmodels/OG-BRA/blob/abd25de301553dcb85d2f6d15229a362471cdec9/ogbra/calibrate.py#L113).
- **When:** since the initial files (2026-06); unchanged at abd25de (2026-08).

### Demographics: method and country_id: BRA uses a named constant

- **Lesson:** pass `country_id` as one named constant (`UN_COUNTRY_CODE`) at both call sites, not an
  inline literal.
- **What happened:** OG-BRA defines `UN_COUNTRY_CODE = "076"` (Brazil's UN M49 code) once in
  `calibrate.py` and uses it at both `get_pop_objs` call sites. It has been that way since the
  initial files, and PR #10 keeps it.
- **Evidence:** [main calibrate.py lines 9, 90, 105](https://github.com/PSLmodels/OG-BRA/blob/abd25de301553dcb85d2f6d15229a362471cdec9/ogbra/calibrate.py#L9);
  [initial files commit eec58c4](https://github.com/PSLmodels/OG-BRA/commit/eec58c4397e61b9c41899ef15427e3385d181dcc).
- **When:** 2026-06; unchanged at abd25de (2026-08).

## og-multi-industry-calibration/references/inputs.md

### Defining industries and goods: real estate folded in, M=10 to M=9

- **Lesson:** fold real estate into a broader services or finance group; a standalone imputed-rent
  industry gets a capital share near 1.
- **What happened:** the draft concordance and code assessment on the branch planned M=10 with a
  separate "Real estate & dwellings" industry. The committed calibration is M=9, with activity 6800
  folded into "Finance, real estate & business services". In the packaged 2018 table, activity 6800
  has a capital share of 0.98 with the Gollin split (575,340 of 587,563 factor income is operating
  surplus; my arithmetic). The firms chapter gives the reason: almost pure capital return, no
  meaningful labour margin.
- **Evidence:** [draft concordance, M=10](https://github.com/PSLmodels/OG-BRA/blob/73e07f98dd63a4b8d1a42f538f0407a7a14a1433/data_prep/multi_industry/concordances/concordance.py#L13-L24);
  [CODE_ASSESSMENT.md lines 73–74](https://github.com/PSLmodels/OG-BRA/blob/73e07f98dd63a4b8d1a42f538f0407a7a14a1433/data_prep/multi_industry/CODE_ASSESSMENT.md#L73-L74);
  [constants.py, `SECTORS` and activity 6800](https://github.com/PSLmodels/OG-BRA/blob/73e07f98dd63a4b8d1a42f538f0407a7a14a1433/ogbra/constants.py#L300-L388);
  [firms.md line 36](https://github.com/PSLmodels/OG-BRA/blob/73e07f98dd63a4b8d1a42f538f0407a7a14a1433/docs/book/content/calibration/firms.md#L36);
  [packaged activity table](https://github.com/PSLmodels/OG-BRA/blob/73e07f98dd63a4b8d1a42f538f0407a7a14a1433/ogbra/data/mip_2018_activity.csv).
- **When:** 2026-07 (draft dated 2026-07-09/10; PR #10 commit 2026-07-12).

### Defining industries and goods: what rides along in the utility split

- **Lesson:** when splitting out utilities, check what else each industry carries.
- **What happened:** BRA has `electricity_gas` and `water_waste`. CNAE puts electricity, piped gas
  and steam in one division, and the table has one product for all three, so "Electricity & gas"
  is an electricity-dominated bundle. A pure-power split would need ANEEL/ABEGÁS revenue data.
- **Evidence:** [firms.md line 36](https://github.com/PSLmodels/OG-BRA/blob/73e07f98dd63a4b8d1a42f538f0407a7a14a1433/docs/book/content/calibration/firms.md#L36);
  [CODE_ASSESSMENT.md line 67](https://github.com/PSLmodels/OG-BRA/blob/73e07f98dd63a4b8d1a42f538f0407a7a14a1433/data_prep/multi_industry/CODE_ASSESSMENT.md#L67).
- **When:** 2026-07 (PR #10).

### Defining industries and goods: I=7 with electricity, water and fuels separate

- **Lesson:** goods are household-relevant groups; a finer split can separate electricity, water and
  fuels.
- **What happened:** BRA uses I=7: food and beverages (share 0.196), electricity (0.027), water and
  sanitation (0.009), fuels (0.057), non-durables (0.120), durables (0.101), services (0.490). The
  code assessment records I=5 and I=6 variants tried first and I=7 chosen on 2026-07-09.
- **Evidence:** [firms.md, goods table](https://github.com/PSLmodels/OG-BRA/blob/73e07f98dd63a4b8d1a42f538f0407a7a14a1433/docs/book/content/calibration/firms.md#L40-L50);
  [CODE_ASSESSMENT.md line 73](https://github.com/PSLmodels/OG-BRA/blob/73e07f98dd63a4b8d1a42f538f0407a7a14a1433/data_prep/multi_industry/CODE_ASSESSMENT.md#L73);
  [PR #10](https://github.com/PSLmodels/OG-BRA/pull/10).
- **When:** 2026-07.

### gamma_m: the mixed-income split, phi = 0.428

- **Lesson:** split each industry's mixed income at phi = OS / (compensation + OS), the economy-wide
  capital share of non-mixed factor income.
- **What happened:** 2018 totals are compensation 3,055,773, operating surplus 2,287,642 and mixed
  income 583,568 (R$ million), so phi = 0.428. The raw share with all mixed income as capital
  would be 0.484. `get_gamma` applies the split.
- **Evidence:** [`get_gamma`, lines 163–169](https://github.com/PSLmodels/OG-BRA/blob/73e07f98dd63a4b8d1a42f538f0407a7a14a1433/ogbra/input_output.py#L163-L169);
  [CODE_ASSESSMENT.md lines 125–134](https://github.com/PSLmodels/OG-BRA/blob/73e07f98dd63a4b8d1a42f538f0407a7a14a1433/data_prep/multi_industry/CODE_ASSESSMENT.md#L125-L134);
  [constants.py `TOTAL_CAPITAL_SHARE`](https://github.com/PSLmodels/OG-BRA/blob/73e07f98dd63a4b8d1a42f538f0407a7a14a1433/ogbra/constants.py#L498-L504).
- **When:** 2026-07 (PR #10).

### gamma_m: rescale target taken from the table, not the single model

- **Lesson:** the rescale target must be the single model's total capital share; a target from the
  table's own share leaves a gap with the single model.
- **What happened:** BRA rescales to the table's own 0.428 (`TOTAL_CAPITAL_SHARE`). The single model
  uses 0.407 from ILO SDG 10.4.1 (main: `gamma` 0.40719, `gamma_g` 0; PR #11: 0.35719 + 0.05). The
  firms chapter states the two-point gap. The continuation anchor (0.378 = 0.428 − 0.05) and the
  equivalence test (flat 0.428) also use the table's value. Neither open PR closes the gap.
- **Evidence:** [firms.md lines 12–14 and 54–58](https://github.com/PSLmodels/OG-BRA/blob/73e07f98dd63a4b8d1a42f538f0407a7a14a1433/docs/book/content/calibration/firms.md#L12-L14);
  [create_multisector_calibration.py line 83](https://github.com/PSLmodels/OG-BRA/blob/73e07f98dd63a4b8d1a42f538f0407a7a14a1433/ogbra/create_multisector_calibration.py#L83);
  [PR #10](https://github.com/PSLmodels/OG-BRA/pull/10), [PR #11](https://github.com/PSLmodels/OG-BRA/pull/11).
- **When:** 2026-07; open as of 2026-10.

### Z_m: K_m allocated by all mixed income while gamma takes only phi

- **Lesson:** allocate `K_m` by the same capital income that defines `gamma_m`.
- **What happened:** on the PR #10 branch, `get_gamma` defines capital income as operating surplus
  plus phi of mixed income (line 166). `get_Z` allocates the national capital stock by operating
  surplus plus all mixed income (lines 236–242). The two disagree most where mixed income is
  large. Recomputing Z here from the packaged data with the phi-consistent allocation (my script,
  which reproduces the shipped Z exactly first): agriculture 0.512 → 0.600 (+17%), construction
  0.548 → 0.605 (+10%), mining and electricity about −7%. The ranking holds. Not fixed on the
  branch or in its local worktree.
- **Evidence:** [`get_gamma` line 166](https://github.com/PSLmodels/OG-BRA/blob/73e07f98dd63a4b8d1a42f538f0407a7a14a1433/ogbra/input_output.py#L166);
  [`get_Z` lines 236–242](https://github.com/PSLmodels/OG-BRA/blob/73e07f98dd63a4b8d1a42f538f0407a7a14a1433/ogbra/input_output.py#L236-L242);
  [PR #10](https://github.com/PSLmodels/OG-BRA/pull/10).
- **When:** 2026-07 (73e07f9); still there 2026-10.

### Z_m: capital-output ratio from PWT

- **Lesson:** take the capital-output ratio from PWT for the SAM year; its level matters little.
- **What happened:** BRA uses 4.36, PWT 10.x for Brazil in 2018 (rnna / rgdpna, via FRED series
  RKNANPBRA666NRUG and RGDPNABRA666NRUG).
- **Evidence:** [constants.py `CAPITAL_OUTPUT_RATIO`](https://github.com/PSLmodels/OG-BRA/blob/73e07f98dd63a4b8d1a42f538f0407a7a14a1433/ogbra/constants.py#L510-L513);
  [firms.md line 84](https://github.com/PSLmodels/OG-BRA/blob/73e07f98dd63a4b8d1a42f538f0407a7a14a1433/docs/book/content/calibration/firms.md#L84).
- **When:** 2026-07.

### Z_m: spot-check the ranking

- **Lesson:** check the Z ranking against what is known of the economy's sectors.
- **What happened:** BRA's Z (manufacturing = 1): electricity and gas 1.53, mining 1.49, finance,
  real estate and business 1.45, water 1.05; agriculture 0.51, construction 0.55, public services
  0.60, trade 0.71. The firms chapter reads this as the familiar Brazilian pattern: productive
  extractives and utilities, labour-intensive low-Z agriculture, construction and public services.
- **Evidence:** [firms.md, Z table](https://github.com/PSLmodels/OG-BRA/blob/73e07f98dd63a4b8d1a42f538f0407a7a14a1433/docs/book/content/calibration/firms.md#L75-L98);
  [overlay JSON](https://github.com/PSLmodels/OG-BRA/blob/73e07f98dd63a4b8d1a42f538f0407a7a14a1433/ogbra/ogbra_multisector_default_parameters.json).
- **When:** 2026-07.

### Tax rates by industry and good: per-good tau_c from the use table

- **Lesson:** per-good `tau_c` = taxes on products / (household spending at consumer prices − those
  taxes); energy comes out high, services low.
- **What happened:** BRA: electricity 0.340, fuels 0.291, non-durables 0.229, durables 0.227, food
  0.127, services 0.064, water 0.045. The consumption-weighted mean (0.127) reproduces the single
  model's `tau_c` (0.13 in PR #11). The chapter puts electricity's rate down mainly to state ICMS.
- **Evidence:** [firms.md, goods table](https://github.com/PSLmodels/OG-BRA/blob/73e07f98dd63a4b8d1a42f538f0407a7a14a1433/docs/book/content/calibration/firms.md#L40-L50);
  [`get_tau_c`](https://github.com/PSLmodels/OG-BRA/blob/73e07f98dd63a4b8d1a42f538f0407a7a14a1433/ogbra/input_output.py#L287);
  [PR #10](https://github.com/PSLmodels/OG-BRA/pull/10).
- **When:** 2026-07.

### Tax rates by industry and good: the base CIT factors discount twice

- **Lesson:** an effective per-industry rate must not also pass through the base's
  `c_corp_share_of_assets × adjustment_factor_for_cit_receipts`.
- **What happened:** BRA's per-industry rates are IRPJ + CSLL by CNAE section (2017–2019 mean) over
  operating surplus, averaging about 9%. The overlay does not set the two factors, so the base's
  0.7 and 0.3 apply: about 9% × 0.21 ≈ 2% faced by firms. The single model's 0.34 statutory rate
  times the same factors gives about 7%.
- **Evidence:** [firms.md line 104](https://github.com/PSLmodels/OG-BRA/blob/73e07f98dd63a4b8d1a42f538f0407a7a14a1433/docs/book/content/calibration/firms.md#L104);
  [overlay JSON (no factor keys)](https://github.com/PSLmodels/OG-BRA/blob/73e07f98dd63a4b8d1a42f538f0407a7a14a1433/ogbra/ogbra_multisector_default_parameters.json);
  base `c_corp_share_of_assets` 0.7 and `adjustment_factor_for_cit_receipts` 0.3 in
  [the base JSON at 73e07f9](https://github.com/PSLmodels/OG-BRA/blob/73e07f98dd63a4b8d1a42f538f0407a7a14a1433/ogbra/ogbra_default_parameters.json).
- **When:** 2026-07 (PR #10).

### Public capital: BRA sets it in the overlay from IMF PIMA

- **Lesson:** with `gamma_g > 0` the model needs `initial_Kg_ratio`, `alpha_I` and `delta_g_annual`.
- **What happened:** the PR #10 overlay sets `alpha_I` 0.02, `initial_Kg_ratio` 0.35 and
  `delta_g_annual` 0.047 (from Kg/Y = alpha_I/(g + delta_g)), against main's 0, 0.2 and 0.02. PR #11
  puts the same values into the single model's base, where the ogcore defaults would have built
  public capital to 66% of GDP. Once both land, the overlay copies are redundant.
- **Evidence:** [firms.md line 106](https://github.com/PSLmodels/OG-BRA/blob/73e07f98dd63a4b8d1a42f538f0407a7a14a1433/docs/book/content/calibration/firms.md#L106);
  [PR #11 CHANGELOG](https://github.com/PSLmodels/OG-BRA/blob/50144b53174cb03af88048cf973c386887ddc9db/CHANGELOG.md);
  [PR #10](https://github.com/PSLmodels/OG-BRA/pull/10), [PR #11](https://github.com/PSLmodels/OG-BRA/pull/11).
- **When:** 2026-07.

## og-multi-industry-calibration/references/alignment.md

### Reaching the steady state: prices span 0.13–2.09, so continuation

- **Lesson:** a cold solve fails when relative prices spread widely; solve by continuation from a
  flat anchor.
- **What happened:** BRA's calibrated prices run from 0.13 (mining) to 2.09 (public services), a
  ratio of about 16. A direct solve from p = 1 diverges. `solve_ss_by_continuation` walks from a
  flat-gamma anchor (0.378, Z = 1) to the calibration in about two minutes. TPI uses `nu` 0.2.
- **Evidence:** [firms.md line 116](https://github.com/PSLmodels/OG-BRA/blob/73e07f98dd63a4b8d1a42f538f0407a7a14a1433/docs/book/content/calibration/firms.md#L116);
  [example, `solve_ss_by_continuation`](https://github.com/PSLmodels/OG-BRA/blob/73e07f98dd63a4b8d1a42f538f0407a7a14a1433/examples/run_og_bra_multi_industry.py#L104);
  [PR #10](https://github.com/PSLmodels/OG-BRA/pull/10).
- **When:** 2026-07, ogcore 0.16.2 in that branch's uv.lock.

### Checking the solved model: labour allocation vs the table, correlation 0.86

- **Lesson:** check the model's labour allocation against the table's labour income by industry.
- **What happened:** the firms chapter reports that model labour allocations correlate 0.86 with
  the table's labour income by industry (compensation plus the labour part of mixed income),
  numeraire excluded. The gaps are in public services and construction, whose demand is government
  consumption and investment. The branch ships no code that computes this number: a search for
  correlation code in tests, examples and the package found none.
- **Evidence:** [firms.md line 128](https://github.com/PSLmodels/OG-BRA/blob/73e07f98dd63a4b8d1a42f538f0407a7a14a1433/docs/book/content/calibration/firms.md#L128);
  [example, `validate_ss`](https://github.com/PSLmodels/OG-BRA/blob/73e07f98dd63a4b8d1a42f538f0407a7a14a1433/examples/run_og_bra_multi_industry.py#L174)
  (structural checks only).
- **When:** 2026-07.

### Tests worth having: nothing tests the continuation solve or the calibrated steady state

- **Lesson:** check whether the repo tests the continuation solve, the example and the calibrated
  steady state against data; where it does not, say so in the PR.
- **What happened:** on the PR #10 branch, `tests/test_multisector_equivalence.py` is the only
  multi-industry test that solves. It is marked `local` and checks that identical industries at
  `gamma_g` = 0 reproduce M=1 (`r`, `w`, K, L, nominal C to rel 1e-8; every `p_m` = 1). No test runs
  the continuation solve, the multi-industry example, or checks the calibrated steady state against
  data. The only other solving test, `test_run_example.py` (also `local`), starts the
  single-industry example and passes if it is still running after 300 seconds. PR #10's body
  reports steady-state moments against data but does not say they are untested.
- **Evidence:** [test_multisector_equivalence.py](https://github.com/PSLmodels/OG-BRA/blob/73e07f98dd63a4b8d1a42f538f0407a7a14a1433/tests/test_multisector_equivalence.py#L67);
  [test_run_example.py](https://github.com/PSLmodels/OG-BRA/blob/73e07f98dd63a4b8d1a42f538f0407a7a14a1433/tests/test_run_example.py#L30);
  [PR #10](https://github.com/PSLmodels/OG-BRA/pull/10).
- **When:** 2026-07 (73e07f9).
