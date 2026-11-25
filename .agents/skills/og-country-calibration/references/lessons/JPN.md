<!-- GENERATED FILE - do not edit here.
     Source: docs/og-lessons/JPN.md
     Regenerate: python scripts/sync_shared.py -->

# Japan (JPN): lessons behind the OG skills

What happened behind lessons in the OG skills (og-country-calibration,
og-multi-industry-calibration, og-solver-diagnosis, og-run). The skills teach the method; these
are one country's numbers, kept here so the skills stay general. They record what was true when
written; check the country repo before relying on any of them. Do not copy them into another
country's calibration.

The JPN work is one calibration of arihantlodha-cmd/OG-JPN, done on 2026-08-10 and 2026-08-11 on
branch `calibration/japan-macro-fiscal` (local checkout `OG-JPN`). It is
pushed to the fork marcelolafleur/OG-JPN up to e438fa2 and open as draft PR
https://github.com/arihantlodha-cmd/OG-JPN/pull/2, with the findings in issue
https://github.com/arihantlodha-cmd/OG-JPN/issues/1. Three later commits (aefac02, 48b662f,
145c771) touch only `docs/NEXT_STEPS.md` and are local. It ran on ogcore v0.19.0 plus OG-Core PR
#1189. The written record is in the repo's `docs/`: `CALIBRATION_AUDIT.md` (findings and
derivations), `CALIBRATION_JOURNEY.md` (a narrative of the session, with its corrections),
`UPSTREAM_OGCORE.md` and `NEXT_STEPS.md`. Commit links below are to the fork; "docs at e438fa2"
means `https://github.com/marcelolafleur/OG-JPN/blob/e438fa2/<path>`. The arihantlodha-cmd `main`
branch went on to a separate calibration after 2026-08-18; nothing below comes from it.

Contents (by the skill file each entry backs; search a file for its `###` headings)
- og-country-calibration/SKILL.md
- og-country-calibration/references/macro-open-economy.md
- og-country-calibration/references/fiscal-consistency.md
- og-country-calibration/references/households-demographics.md
- og-country-calibration/references/validation-dashboard.md
- og-country-calibration/references/solving-tuning.md
- og-solver-diagnosis/references/solve-procedures.md

## og-country-calibration/SKILL.md

### Calibrating an OG-Core country model: country tags are provenance, not scope

- **Lesson:** a `[JPN]` tag records where a lesson was learned, never which country it applies to.
- **What happened:** this is the skill's reading rule, not a case. It names `[JPN]` only as an
  example tag. The cases behind the JPN tags are the entries below.
- **Evidence:** not found (searched: nothing to search; the line is the rule itself, not a JPN
  case).
- **When:** not applicable.

### The mental model: anything you do not set stays American

- **Lesson:** count what your `Calibration` actually delivers; everything unset keeps OG-Core's US
  defaults, and a packaged JSON makes that whole surface visible where Python functions hide it.
- **What happened:** OG-JPN's `Calibration` passed OG-Core seven things: five macro parameters, one
  consumption tax rate and the demographic arrays. The rest stayed American: `mean_income_data`
  58,644.92 US dollars, US Social Security, `tax_func_type` DEP, `cit_rate` 0.21, `delta` 0.05,
  `beta` 0.96, `tau_payroll` 0.0 (Japan collects 13.2% of GDP in social insurance), `zeta_D` 0.4
  (actual 0.137) and `debt_ratio_ss` 2.0, never chosen. The calibration ended with 34 sourced
  parameters. The audit's Finding 7 traced the gap to the repo building parameters in two Python
  functions instead of the family's packaged JSON (OG-ZAF's has 129 keys). Nothing errored.
- **Evidence:** `docs/CALIBRATION_AUDIT.md` (headline table and Finding 7) at e438fa2,
  https://github.com/marcelolafleur/OG-JPN/blob/e438fa2/docs/CALIBRATION_AUDIT.md ;
  https://github.com/arihantlodha-cmd/OG-JPN/issues/1 ;
  https://github.com/arihantlodha-cmd/OG-JPN/pull/2 ;
  https://github.com/marcelolafleur/OG-JPN/commit/be80490
- **When:** 2026-08 (audit against OG-JPN `main` at babbe80; first sourced pass be80490,
  2026-08-10).

### The mental model: `K_f/K` is first-tier, and gross vs net decides its sign

- **Lesson:** score `K_f/K` as a first-tier moment, and settle gross vs net before choosing its
  target, because for a net creditor the two readings differ in sign.
- **What happened:** `zeta_K` sat at a placeholder 0.10 and solved to `K_f/K` = 1.5%, against a
  gross IIP share of 16.4%. Once tuned (0.78 in cef6000), a sentence written into the skill, that
  OG-Core gives households no foreign assets, was checked against `aggregates.py` and found wrong:
  `K_f` is unclamped and can go negative. On the net reading Japan's target is −23.7% (net IIP
  +¥533tn, 87.5% of GDP), the opposite sign. Commit 1c869fd flagged this as blocking `zeta_K`; the
  calibration settled on gross. Detail is in the `K_f` entry under macro-open-economy.md.
- **Evidence:** https://github.com/marcelolafleur/OG-JPN/commit/cef6000 ;
  https://github.com/marcelolafleur/OG-JPN/commit/1c869fd ; `docs/NEXT_STEPS.md` section 0c and
  `docs/CALIBRATION_JOURNEY.md` section 4.5, docs at e438fa2.
- **When:** 2026-08 (cef6000 and 1c869fd, 2026-08-10).

### Dashboard completeness: every tuned dial needs its own scored moment

- **Lesson:** an unscored moment cannot pull its parameter, so every tuned dial needs a scored
  moment and every resource-constraint component and the early transition must be scored.
- **What happened:** `K_f/K` was not a row on `examples/validate_japan.py`, so `zeta_K` sat at its
  placeholder through fourteen tuning rounds. The dashboard comment added with the row says so.
  The same evening the dashboard gained `K_f/K` (cef6000) and then `I_g`, `NX` and the labour share
  (1c869fd), so the consumption gap could be split into its parts. The cases are under
  validation-dashboard.md below.
- **Evidence:** https://github.com/marcelolafleur/OG-JPN/commit/cef6000 ;
  https://github.com/marcelolafleur/OG-JPN/commit/1c869fd ; `examples/validate_japan.py` at e438fa2,
  https://github.com/marcelolafleur/OG-JPN/blob/e438fa2/examples/validate_japan.py ;
  `docs/CALIBRATION_JOURNEY.md` section 6.
- **When:** 2026-08 (2026-08-10).

### Finding every lever on a moment: the `K/Y` miss, the `beta` that failed, and the world rate

- **Lesson:** a lever that runs out of road is the wrong lever; sweep the unsourced defaults once
  the parameters settle, because a high `zeta_K` hands `r` to `world_int_rate`.
- **What happened:** OG-JPN's `K/Y` came in at 3.50 against a PWT 3.70. `beta` would have needed
  0.984, and at 0.984 the steady state stopped solving, so 0.979 shipped with the miss written up
  as "inside the band the family already tolerates". `zeta_K` sat at 0.10 under its own comment
  `NEEDS TUNING ... pending the IIP anchor`. Set from the IIP (0.78 in cef6000) it closed 79% of
  the `K/Y` gap and 85% of the consumption gap; nothing had failed when it was skipped, so the
  release gate `test_no_unresolved_tuning_markers` followed (bfac931, allowlist emptied in
  c8b5fd1). `world_int_rate` (default 0.04) was invisible at 0.10 and set `r` at 0.78: at a 3.5%
  world rate the same `zeta_K` gave `K/Y` 3.81 and `K_f/K` 27%, against 16.9% at 4%. The skill's
  starting `K/Y` of 3.67 is not written in the repo; 79% of the 0.197 gap from 3.503 implies about
  3.66.
- **Evidence:** `ogjpn/macro_params.py` (`beta_annual` and `zeta_K` blocks) at e438fa2,
  https://github.com/marcelolafleur/OG-JPN/blob/e438fa2/ogjpn/macro_params.py ;
  https://github.com/marcelolafleur/OG-JPN/commit/cef6000 ;
  https://github.com/marcelolafleur/OG-JPN/commit/bfac931 ;
  https://github.com/marcelolafleur/OG-JPN/commit/c8b5fd1 ; `docs/CALIBRATION_JOURNEY.md`
  section 6; `docs/NEXT_STEPS.md` section 0c (source the world rate).
- **When:** 2026-08 (2026-08-10). `zeta_K` later moved to 0.70 and then to 0.534/0.543 as other
  parameters changed; the world-rate test was run at 0.78.

## og-country-calibration/references/macro-open-economy.md

### g_y_annual: measure productivity per hour, not per worker

- **Lesson:** measure `g_y` per hour, because a trend in hours per worker is transitional and must be
  stripped like a trending participation rate.
- **What happened:** the first sourced pass set `g_y_annual` 0.0056 from GDP per worker. PWT via
  FRED over 2000–2019 gave +0.557%/yr per worker, −0.472%/yr in hours per worker and +1.035%/yr
  per hour, so per hour was about 0.5pp a year higher. Commit 4fe80c7 set 0.0104, with the window
  (after the 1997–98 banking crisis, before COVID) in named constants. The change also opened room
  for `beta` (see `beta_annual`).
- **Evidence:** https://github.com/marcelolafleur/OG-JPN/commit/4fe80c7 ; `ogjpn/macro_params.py`
  (`g_y_annual` block) at e438fa2; test `test_productivity_growth_is_per_hour_over_a_named_window`
  in https://github.com/marcelolafleur/OG-JPN/blob/e438fa2/tests/test_ogjpn.py
- **When:** 2026-08 (4fe80c7, 2026-08-10).

### r_gov floor: a negative real sovereign rate was clipped to zero

- **Lesson:** set the `r_gov` floor below the effective rate you calibrate to, and read a reported
  `r_gov` of exactly 0.0000 as clipping.
- **What happened:** Japan's net interest over net debt gives about −0.6% real. The calibrated wedge
  returned −0.6023% and ogcore's hard `np.maximum(..., 0.00)` reported 0.0000. Removing the floor in
  a scratch copy raised solved `G/Y` from 0.1820 to 0.1871, so the clip cost 0.51pp of GDP of
  government spending through `pb*` (it raised `pb*` by 0.68pp); the interest bill was near zero
  either way. The repo worked around it with `ogjpn/rgov_floor.py`. Upstream, OG-Core#1202 led to
  PR #1203, which made the floor the parameter `r_gov_floor` (default 0.0).
- **Evidence:** `docs/UPSTREAM_OGCORE.md` (item 2) and `docs/CALIBRATION_AUDIT.md` ("The government
  gap") at e438fa2; https://github.com/marcelolafleur/OG-JPN/commit/b231e85 (measurement);
  https://github.com/marcelolafleur/OG-JPN/commit/e490b8c (shim);
  https://github.com/PSLmodels/OG-Core/issues/1202 ; https://github.com/PSLmodels/OG-Core/pull/1203
- **When:** 2026-08 (found 2026-08-10, shim 2026-08-11). OG-Core PR #1203 merged 2026-09-02.

### delta_annual: the US 0.05 was silently in force

- **Lesson:** derive `delta` from the country's own CFC over its capital stock rather than leave
  OG-Core's US 0.05.
- **What happened:** OG-JPN ran on 0.05. Japan's consumption of fixed capital was 23.5–24.1% of
  GDP (World Bank, 2016–2019); over a PWT `K/Y` of about 3.7 that gives 0.061–0.064, and 0.062
  shipped. At 0.05 the model invested 17.3% of GDP against Japan's 27.8%. Fixing `delta` together
  with `gamma` (0.38 → 0.43) moved `C/Y` from 0.671 to 0.627 and `K/Y` from 3.87 to 3.67. Later,
  0.060 would have improved both `K/Y` and investment, but it was left alone because it sat below
  the sourced range. The skill's "moved investment 2.7pp of GDP" is not in the repo; it records the
  17.3% level and the combined effect above.
- **Evidence:** https://github.com/marcelolafleur/OG-JPN/commit/92d3021 ;
  https://github.com/marcelolafleur/OG-JPN/commit/0a92904 ;
  https://github.com/marcelolafleur/OG-JPN/commit/1441074 ; `ogjpn/macro_params.py`
  (`delta_annual` block) at e438fa2.
- **When:** 2026-08 (2026-08-10).

### beta_annual: re-ask whether `beta` has room after each sourced change

- **Lesson:** calibrate `beta` to `K/Y` only after the sourced parameters settle, and re-ask after any
  change to `gamma`, `delta` or `g_y`.
- **What happened:** at the per-worker `g_y`, the model's `K/Y` already sat on target, so `beta` had
  no room. Per-hour `g_y` opened a gap, and `beta` went 0.96 → 0.971 (5441eb5). Widening the
  demographic window raised `g` and lowered `K/Y`, so `beta` went to 0.979 (839d19f) and then 0.984
  at the full horizon (608d2e3). At 0.984 the steady state did not solve, and the repo reverted to
  0.979 (af69e67), shipping `K/Y` 3.50 against 3.70.
- **Evidence:** https://github.com/marcelolafleur/OG-JPN/commit/5441eb5 ;
  https://github.com/marcelolafleur/OG-JPN/commit/839d19f ;
  https://github.com/marcelolafleur/OG-JPN/commit/608d2e3 ;
  https://github.com/marcelolafleur/OG-JPN/commit/af69e67 ; `ogjpn/macro_params.py`
  (`beta_annual` block) at e438fa2.
- **When:** 2026-08 (2026-08-10).

### alpha_T: cash transfers only

- **Lesson:** `alpha_T` carries cash transfers only; in-kind health, long-term care and education
  belong in `G`.
- **What happened:** the repo's `main` had 0.10; the first sourced pass set 0.075 as total social
  spending less pensions. IPSS FY2023 shows most of that is in kind (health 7.67% of GDP, long-term
  care 1.93%), and OECD SOCX cash less pensions gives about 2.6% of GDP. Commit a00f3a5 set 0.025:
  the shipped value had been three times the true cash share. The narrative records it as the
  largest single contributor to the consumption error. A side effect: ogcore seeds
  `Yguess = TRguess / alpha_T`, so the fix tripled the implied GDP guess and broke the solver seed
  (add7152).
- **Evidence:** https://github.com/marcelolafleur/OG-JPN/commit/be80490 (0.075);
  https://github.com/marcelolafleur/OG-JPN/commit/a00f3a5 (0.025);
  https://github.com/marcelolafleur/OG-JPN/commit/add7152 ; `docs/CALIBRATION_JOURNEY.md`
  section 4.2.
- **When:** 2026-08 (2026-08-10).

### K_f gross vs net: calibrate to the gross IIP share and state the omitted portfolio

- **Lesson:** calibrate `K_f/K` to the gross foreign-owned share, check the sign of the NIIP, and
  say that the model omits the country's foreign portfolio and its income.
- **What happened:** the gross target, from MOF IIP end-2024 liabilities, is direct-investment
  equity with reinvested earnings ¥34.5tn plus portfolio equity ¥334.8tn, over GDP ¥609tn, over
  `K/Y` 3.70: 16.4%. The placeholder `zeta_K` = 0.10 produced 1.5%, about a tenth. Japan's net IIP
  is +¥533tn (87.5% of GDP), so on the net reading the target is −23.7%, the opposite sign; the
  repo also found it unreachable, since `r` (4.39%) sat above the 4% world rate and so `K_f > 0` at
  any `zeta_K`. Gross was chosen, at a stated cost: ¥1,659tn of foreign assets have no place in
  `B`, and their income, roughly 3.8% of GDP a year, is absent from the resource constraint. For
  KOR (see KOR.md) the gross share was 7.1% on total PWT capital and 8.4% on private.
- **Evidence:** https://github.com/marcelolafleur/OG-JPN/commit/cef6000 ;
  https://github.com/marcelolafleur/OG-JPN/commit/1c869fd ; `docs/NEXT_STEPS.md` section 0c and
  `docs/CALIBRATION_JOURNEY.md` sections 4.5 and 7 at e438fa2.
- **When:** 2026-08 (2026-08-10).

## og-country-calibration/references/fiscal-consistency.md

### The budget identity: pension outlays are a primary outlay

- **Lesson:** primary spending in the identity includes pensions (and any UBI), and the steady state
  hides an omission by forcing `G` to the consistent level.
- **What happened:** the identity in use was `alpha_G + alpha_T + alpha_I = revenue/Y − pb*`, without
  pensions. `alpha_G` shipped at 0.201 (World Bank observed government consumption). The steady
  state solved and reported `G/Y` 0.1947; commit 55cc4bf added pension outlays to the identity and
  set `alpha_G` to 0.1947, 0.63pp lower. The transition holds `alpha_G` at its input for the first
  `tG1` periods, so the old value would have over-spent the full gap.
- **Evidence:** https://github.com/marcelolafleur/OG-JPN/commit/55cc4bf ; `ogjpn/macro_params.py`
  (spending-shares block) and `examples/validate_japan.py` at e438fa2;
  `docs/CALIBRATION_JOURNEY.md` section 4.6.
- **When:** 2026-08 (55cc4bf, 2026-08-10).
- **Note:** the 0.63pp is the gap between the data-set input (0.201) and the identity value
  (0.1947). It is not the size of Japan's pension bill (9.3% of GDP). The skill's "too high by the
  whole pension bill (JPN: 0.63pp)" reads as if it were. The same 0.63pp is also described in the
  audit as the "embedded consolidation" gap.

### Validation priority: the near-term fiscal path caught a wrong `initial_debt_ratio`

- **Lesson:** build and score the near-term fiscal path with the steady-state dashboard, because only
  the transition starts from the measured `initial_debt_ratio`.
- **What happened:** JPN shipped `initial_debt_ratio` = 0.864 against an actual 1.148 (OECD GNFLQ
  net financial liabilities, end-2024), a 28pp-of-GDP error. The first pass had misread the series
  as falling to 86.4 in 2024 and explained the fall as a valuation effect; the series is flat. The
  same file's `r_gov` derivation used the correct 114.8% average, and the two sat inconsistent for
  about a day. The steady-state dashboard could not catch it, because steady-state `D/Y` is the
  chosen anchor. The fix came with the fiscal-path panel (`examples/validate_fiscal_path.py`),
  which then matched net debt 1.1480 against 1.1479 in 2025.
- **Evidence:** https://github.com/marcelolafleur/OG-JPN/commit/be80490 (0.864);
  https://github.com/marcelolafleur/OG-JPN/commit/1e37555 (1.148 and the path panel);
  https://github.com/arihantlodha-cmd/OG-JPN/pull/2 (path table).
- **When:** 2026-08 (shipped 2026-08-10 10:22, fixed 2026-08-11 12:12).
- **Note:** stale text remains at e438fa2. `docs/CALIBRATION_JOURNEY.md` section 4.1 still calls
  86.4% the actual figure. The comments around `initial_debt_ratio` and `debt_ratio_ss` in
  `macro_params.py` still cite 0.864 and "Set to 1.0", while the values are 1.148.

## og-country-calibration/references/households-demographics.md

### Earnings: the NTA age-shape half of the method

- **Lesson:** apply both halves of the earnings method (an NTA age shape, then the Gini tilt),
  because the tilt alone leaves the US age profile in place.
- **What happened:** OG-JPN implemented both. NTA labour income by age for Japan (2004) and the US
  (2003) gave a factor of 1.09 at 55 and 0.62 at 65, from the seniority wage system and retirement
  at 60. Peak earnings age moved from 61 to 57. NTA has no API: the fetch walks a session form and
  needs a `Referer` header on the download POST. A side check: the fitted pension replacement rate
  moved from 0.399 to 0.358, toward its derived 0.373.
- **Evidence:** https://github.com/marcelolafleur/OG-JPN/commit/8ce2428 ;
  `docs/CALIBRATION_AUDIT.md` ("Earnings: the full two-part method") and
  `docs/UPSTREAM_OGCORE.md` item 7 at e438fa2; test `test_age_shape_factor_has_japans_signature`.
- **When:** 2026-08 (8ce2428, 2026-08-10).

### The data window sets the long-run growth rate

- **Lesson:** the demographic data window decides `g_n_ss`; check it against the UN projection and
  use the terminal UN rates.
- **What happened:** OG-JPN, like the family, passed `final_data_year = start_year + 1`, so the
  vital rates froze two years in and `g_n_ss` came out at −1.070%/yr. A 20-year window gave
  −0.698% and moved `pb*` from a +0.52% surplus to a −0.34% deficit. The repo first matched that to
  the UN's 2025–2100 average of −0.676%, then called that a category error and moved to the full
  74 years (to 2099), where the terminal rates give −0.463%. `start_year + 75` fails because UN WPP
  ends at 2100. It surfaced only because the transition was run (an `RC_error` at t=2).
- **Evidence:** https://github.com/marcelolafleur/OG-JPN/commit/7bbdcc5 ;
  https://github.com/marcelolafleur/OG-JPN/commit/46f7993 ;
  https://github.com/marcelolafleur/OG-JPN/commit/608d2e3 ; `ogjpn/constants.py` at e438fa2;
  `docs/UPSTREAM_OGCORE.md` item 1; https://github.com/arihantlodha-cmd/OG-JPN/issues/1
- **When:** 2026-08 (2026-08-10).

### Discontinuities: the frozen window and `fixper`

- **Lesson:** the window end and ogcore's `fixper` each breach the transition's resource constraint,
  and `fixper` cannot be fixed from the country side.
- **What happened:** at the 74-year window, 318 of 320 periods satisfied `RC_TPI`, with a median
  residual of 7.96e-08. The two breaches were t=75, where the data window ends, and t=120,
  `fixper = int(1.5 * S)`, where ogcore swaps in the fixed steady-state population in one period.
  The immigration jump there measured 0.50–0.56 at every window from start+20 to start+74. Both
  were predicted before the run.
- **Evidence:** https://github.com/marcelolafleur/OG-JPN/commit/24fd108 ;
  https://github.com/marcelolafleur/OG-JPN/commit/b63cb88 ; `docs/CALIBRATION_AUDIT.md`
  ("Status of the transition") and `docs/UPSTREAM_OGCORE.md` item 1 at e438fa2.
- **When:** 2026-08 (2026-08-10). The PR's later run reports a median of 2.0e-07.
- **Note:** the skill says to report `fixper` upstream. I found no OG-Core issue or PR for it
  (searched PSLmodels/OG-Core issues and PRs for "fixper", "final_data_year" and "demographic
  window"); it is written up only in `docs/UPSTREAM_OGCORE.md` as "PR to follow".

### Cache the processed demographic arrays

- **Lesson:** cache the processed demographic arrays, because ogcore refetches the UN series on every
  call and a failed fetch dies with a misleading `KeyError`.
- **What happened:** at the 74-year window each solve refetched the whole UN series, and repeated
  calls failed now and then. ogcore then fell back to its offline mirror, which had no Japan, and
  the run died with `KeyError: '392'`. Commit 290d6ae caches the arrays under a hash of every
  input that changes them. Japan was later added to the offline map (OG-Core PR #1196). The UN
  token expired on 2026-08-11, another route to the fallback; OG-Core#1205 asked for one place to
  keep the key. The skill's "~100s per solve" is not in the repo.
- **Evidence:** https://github.com/marcelolafleur/OG-JPN/commit/290d6ae ; `ogjpn/calibrate.py` and
  `ogjpn/constants.py` at e438fa2; https://github.com/PSLmodels/OG-Core/pull/1196 ;
  https://github.com/PSLmodels/OG-Core/issues/1205 ; local `docs/NEXT_STEPS.md` section 0d
  (commits aefac02, 48b662f, unpushed).
- **When:** 2026-08 (290d6ae, 2026-08-10).

### Income-differentiated demographics: high-income countries are out of scope

- **Lesson:** check the country is in Demographic-Gradients first; leave high-income countries unset
  and pin the decision in a test.
- **What happened:** Japan is in none of the library's files. Its AGENTS.md limits the fallback to
  $200–$10,000 GNI per head, and Japan is about $39,000. Japan's published mortality gradient is
  ecological, which the library says not to pool, and a borrowed fertility gradient could have the
  wrong sign, since in Japan it runs through marriage rates. The gradients were left unset and
  `income_percentiles` still passed. Test `test_demographic_gradients_are_deliberately_absent`
  pins it.
- **Evidence:** https://github.com/marcelolafleur/OG-JPN/commit/b231e85 ; `ogjpn/calibrate.py`
  docstring and https://github.com/marcelolafleur/OG-JPN/blob/e438fa2/tests/test_ogjpn.py ;
  `docs/UPSTREAM_OGCORE.md` item 6.
- **When:** 2026-08 (2026-08-10).

### Pensions: validate against pension spending as a share of GDP

- **Lesson:** validate pensions against public pension expenditure as a share of GDP, not against the
  replacement rate you fed in.
- **What happened:** the README claimed the model reproduced Japan's pension burden (11–12% of GDP).
  The target was wrong (OECD *Pensions at a Glance* 2023: 9.3%), and the number came from US
  Social Security at US mean income. Under Defined Benefits, pinning `alpha_db` to the OECD's 32.4%
  replacement rate paid 7.6% of GDP against 9.3%; the uplift to match was later relabelled
  "fitted". Matching 9.3% in the steady state then forced the first transition year to 6.85%, so
  9.3% was moved to the transition path, where 2025 reads 8.9% against 9.3%.
- **Evidence:** `docs/CALIBRATION_AUDIT.md` (Finding 1; adversarial check 5) at e438fa2;
  https://github.com/marcelolafleur/OG-JPN/commit/0a92904 ;
  https://github.com/marcelolafleur/OG-JPN/commit/a00f3a5 ;
  https://github.com/marcelolafleur/OG-JPN/commit/0f4efdb ;
  https://github.com/arihantlodha-cmd/OG-JPN/pull/2
- **When:** 2026-08 (2026-08-10 and 2026-08-11).

### Labour supply (chi_n): check total labour input against the US before borrowing

- **Lesson:** before treating OG-USA's `chi_n` as harmless, compare total labour input per
  working-age person with the US.
- **What happened:** Japan works 1,611 hours per worker at a 79.3% employment rate (15–64), or 1,278
  hours per working-age person. The US works 1,799 at 71.6%, or 1,288. The ratio is 0.992: 10.5%
  fewer hours per worker offset by more people working. `chi_n` stayed borrowed and documented as
  such.
- **Evidence:** https://github.com/marcelolafleur/OG-JPN/commit/b231e85 ;
  `docs/CALIBRATION_AUDIT.md` ("`chi_n` — borrowed") at e438fa2.
- **When:** 2026-08 (2026-08-10).

## og-country-calibration/references/validation-dashboard.md

### Completeness: a dial moved to close a residual is a free parameter

- **Lesson:** tune each dial to its own moment; total revenue is the check, never the thing you steer.
- **What happened:** the skill says OG-JPN's `p_wealth` and `tau_bq` were in practice scaled to close
  total revenue. That claim was written into the skill on 2026-08-10 during the JPN session
  (Model-tools b642c7d). The OG-JPN record does not show it: `tax_params.py` documents each as
  tuned to its own target (property taxes 2.21% of GDP, inheritance tax 0.55%) from the solved
  wealth and bequest bases, and both rows are scored in the fit figure (from 3bdbb82). The command
  line dashboard `examples/validate_japan.py` has no row for either.
- **Evidence:** https://github.com/marcelolafleur/Model-tools/commit/b642c7d (origin of the claim);
  `ogjpn/tax_params.py` at e438fa2,
  https://github.com/marcelolafleur/OG-JPN/blob/e438fa2/ogjpn/tax_params.py ;
  https://github.com/marcelolafleur/OG-JPN/commit/3bdbb82 . Evidence for "scaled to close total
  revenue" in OG-JPN: not found (searched: `git log -S`/`-G` on `p_wealth`, `tau_bq`, "residual",
  "absorb", "close total" across the branch, its docs and the PR).
- **When:** 2026-08 (2026-08-10).

### Completeness: score the first years, not only the steady state

- **Lesson:** report first-tier moments at t=0–10 as well, because a steady state can land close
  while the first years miss badly.
- **What happened:** OG-JPN's first-year consumption share missed because of initial wealth. Without
  OG-Core's `initial_wealth_ratio`, the transition forces `B(0) = B_ss`, which handed every initial
  household a 20% windfall (scale 1.198; `B_ss/Y` 3.923 against 3.253). The fingerprint: consumption
  +13pp of GDP for one year, investment down 12.6pp, a consumption-tax pulse and a spurious debt
  paydown. The fix sets `initial_wealth_ratio` = 3.119, built from PWT capital, which needs OG-Core
  PR #1189 (still open).
- **Evidence:** https://github.com/marcelolafleur/OG-JPN/commit/55cc4bf (diagnosis);
  https://github.com/marcelolafleur/OG-JPN/commit/1462671 (anchor); `docs/NEXT_STEPS.md`
  section 4 at e438fa2; https://github.com/PSLmodels/OG-Core/pull/1189
- **When:** 2026-08 (2026-08-10 and 2026-08-11), ogcore v0.19.0 plus PR #1189.

### Moments most often tuned for but never scored

- **Lesson:** add the moments that identify tuned dials (`K_f/K`, `(I + I_g)/Y`, `G/Y`, `NX/Y`, the
  wealth and bequest tax lines, `w·L/Y`, `g_n_ss`) and watch the traps when adding rows.
- **What happened:** the table was written from the JPN dashboard. `K_f/K` was added in cef6000
  after `zeta_K` drifted; `I_g` (so investment compares with GFCF), `NX` and the labour share in
  1c869fd. The wealth-by-age row in the same table is a KOR lesson (see KOR.md).
- **Evidence:** https://github.com/marcelolafleur/OG-JPN/commit/cef6000 ;
  https://github.com/marcelolafleur/OG-JPN/commit/1c869fd ; `examples/validate_japan.py` at e438fa2;
  https://github.com/marcelolafleur/Model-tools/commit/b642c7d
- **When:** 2026-08 (2026-08-10).

### Moments most often tuned for but never scored: the solved labour share

- **Lesson:** score the solved `w·L/Y` against PWT `labsh`; it is a free check when `epsilon != 1`.
- **What happened:** JPN solved 0.5700 against PWT 0.571. But OG-JPN does not set `epsilon`, so it
  runs OG-Core's default 1.0 (Cobb-Douglas) with `gamma` 0.43 and `gamma_g` 0. There the solved
  labour share is 1 − `gamma` by construction. On JPN the match was therefore not a free check; it
  only confirms that `gamma` came from the same PWT series.
- **Evidence:** https://github.com/marcelolafleur/OG-JPN/commit/1c869fd (row added, with the comment
  "Not forced when epsilon != 1"); `ogjpn/macro_params.py` at e438fa2 (no `epsilon`);
  `ogcore/default_parameters.json` in `OG-Core` (`epsilon` 1.0).
- **When:** 2026-08 (2026-08-10).

### Two traps when adding rows: NX is the trade balance, not the current account

- **Lesson:** score `NX/Y` against the trade balance; for a large net creditor most of the current
  account is primary income.
- **What happened:** Japan's current-account surplus is about 3.8% of GDP, almost all income on its
  net foreign assets, while its goods-and-services balance is near zero. So a model `NX/Y` near
  0.000 is right, and scoring it against 3.8% would be a concept error. The repo also rejected
  putting that income in `alpha_RM`: it would add the income with no asset stock to accumulate,
  which raises consumption, while Japan reinvests its foreign income abroad.
- **Evidence:** https://github.com/marcelolafleur/OG-JPN/commit/1c869fd ; `examples/validate_japan.py`
  (NX row comment) and `docs/CALIBRATION_AUDIT.md` ("An option considered and rejected:
  `alpha_RM`") at e438fa2.
- **When:** 2026-08 (2026-08-10).

### Consumption is a residual: decompose its gap, and compare like with like

- **Lesson:** a consumption gap is the sum of the other resource-constraint gaps, and `I_total` is
  private investment, not GFCF.
- **What happened:** OG-Core has no consumption parameter, so the repo split the gap into investment,
  government and net exports, each with its own cause. Its own adversarial check found an earlier
  comparison of `I_total` (private) against GFCF (private plus public), which overstated the
  investment gap by the 3pp of public investment: 6.9pp became 4.2pp.
- **Evidence:** https://github.com/marcelolafleur/OG-JPN/commit/afbca8e ;
  https://github.com/marcelolafleur/OG-JPN/commit/26844bd ; `docs/CALIBRATION_AUDIT.md`
  (adversarial check 4) and `docs/CALIBRATION_JOURNEY.md` section 4.3 at e438fa2.
- **When:** 2026-08 (2026-08-10).

### g_n is a path; the steady state uses its terminal value

- **Lesson:** for a country mid-demographic-transition, compare "the country now" against the early
  transition, not the steady state.
- **What happened:** Japan's population growth is −0.33%/yr in 2025 and −0.46% at the terminal UN
  rates. At the 2025 rate the model invested 23.3% of GDP against Japan's private 24.5%, a 1.2pp
  gap; at the steady state the gap was 3.9pp. The steady state is Japan's demographic destiny, not
  Japan now.
- **Evidence:** https://github.com/marcelolafleur/OG-JPN/commit/b231e85 ;
  `docs/CALIBRATION_AUDIT.md` ("The investment gap") at e438fa2.
- **When:** 2026-08 (2026-08-10).
- **Note:** that table was computed at the narrow window, where the terminal rate was −1.07%;
  `examples/plot_calibration_diagnostics.py` still says "deepening to −1.07%". The −0.46% terminal
  value is from the 74-year window (`ogjpn/constants.py`).

### Pair the debt concept with the interest concept

- **Lesson:** net debt pairs with net interest and gross debt with the effective rate on gross; test
  that `r_gov × D` reproduces the interest bill.
- **What happened:** Japan's general government holds large financial assets (the GPIF, reserves, the
  Fiscal Loan Fund): gross liabilities were 237.9% of GDP in 2024 and net 114.8%. OG-JPN used net
  debt with net interest. The check: the model's debt service was 0.00% of GDP against Japan's net
  interest of −0.12% in 2024, both about zero. Along the way, the first net-debt figure offered to
  the user (1.3–1.5) was an unchecked estimate.
- **Evidence:** `docs/CALIBRATION_AUDIT.md` (adversarial check 2) and `docs/CALIBRATION_JOURNEY.md`
  section 4.1 at e438fa2; https://github.com/marcelolafleur/OG-JPN/commit/26844bd ;
  https://github.com/marcelolafleur/OG-JPN/commit/1e37555 (gross and net series re-pulled).
- **When:** 2026-08 (2026-08-10 and 2026-08-11).

### Audit each instrument's base, not just its yield

- **Lesson:** a right revenue total can sit on a wrong rate and a wrong base, so test the base and
  size reforms by the revenue they must raise.
- **What happened:** the payroll base passed: `w·L/Y` 0.5700 against 0.570. `tau_c` did not: the
  model's consumption base was 14% larger than Japan's, so the tuned 11.2% delivered Japan's
  indirect-tax revenue where 12.8% would on Japan's base. A rate change would over-deliver by the
  base error. The fix sizes the reform by revenue: Japan's 10% → 12% raises VAT by 0.99pp of GDP, so
  `d(tau_c)` = 0.0099 / model `C/Y` (`reform_tau_c()` in `examples/analysis_consumption_tax.py`).
- **Evidence:** https://github.com/marcelolafleur/OG-JPN/commit/26844bd ;
  https://github.com/marcelolafleur/OG-JPN/commit/b231e85 ; `docs/CALIBRATION_AUDIT.md`
  (adversarial check 1; "The `tau_c` base problem") at e438fa2.
- **When:** 2026-08 (2026-08-10).

### Know the family traits: the "family trait" `K/Y` miss was an untuned `zeta_K`

- **Lesson:** run the lever rules before calling any gap a family trait.
- **What happened:** JPN's `K/Y` miss was first filed as a tolerated family gap: the dashboard row
  still labels the PWT target "family trait: model runs high". It was an untuned `zeta_K`. JPN's
  miss also ran the other way (3.50 against 3.70, low, not high).
- **Evidence:** `examples/validate_japan.py` (K/Y row) and `ogjpn/macro_params.py` (`beta_annual`
  block) at e438fa2; https://github.com/marcelolafleur/OG-JPN/commit/cef6000 ;
  `docs/CALIBRATION_JOURNEY.md` section 6.
- **When:** 2026-08 (2026-08-10).

## og-country-calibration/references/solving-tuning.md

### Run engineering: why the steady state was slower through the client

- **Lesson:** older ogcore made the SS slower through the Dask client than serial; on a current
  ogcore treat that as a finding, not a reason to build a serial driver.
- **What happened:** OG-JPN measured about 38 s per GE iteration through the client against about
  6 s serial, and kept the client to run the model as the family does. It also recorded why seven
  workers is the ceiling: `SS.py` and `TPI.py` submit one task per income group and `J` = 7. The
  cause was later fixed upstream: OG-Core PR #1214 scatters the parameters once per solve instead
  of once per residual evaluation.
- **Evidence:** https://github.com/marcelolafleur/OG-JPN/commit/988ef1e ; `examples/run_ogjpn.py`
  docstring at e438fa2; https://github.com/PSLmodels/OG-Core/pull/1214
- **When:** 2026-08 (988ef1e, 2026-08-10), ogcore v0.19.0. OG-Core #1214 merged 2026-09-01.

### Tuning-loop order: sourced parameters first

- **Lesson:** settle the sourced parameters before tuning, and expect a full retune after each
  upstream correction.
- **What happened:** the JPN loop ran fourteen rounds, largely because sourced inputs kept changing
  under the tuned dials: `g_y` moved to per hour, the demographic window widened twice, `alpha_T`
  was cut, and `beta` was re-fitted each time. Later, moving `debt_ratio_ss` from 1.0 to 1.148
  meant re-tuning `zeta_K` from 0.70 to 0.534 for the same `K_f/K`. The repo's own note says the
  loop converges in three to five iterations once those are fixed.
- **Evidence:** `docs/NEXT_STEPS.md` section 1 and `ogjpn/macro_params.py` (`beta_annual`, `zeta_K`
  blocks) at e438fa2; https://github.com/marcelolafleur/OG-JPN/commit/afbca8e (fourteen rounds);
  https://github.com/marcelolafleur/OG-JPN/commit/e490b8c (`zeta_K` re-tune).
- **When:** 2026-08 (2026-08-10 and 2026-08-11).

## og-solver-diagnosis/references/solve-procedures.md

### Warm-starting the steady state

- **Lesson:** warm-start the household matrices and every outer unknown from a solved state, leave
  the scalar seed parameters alone, and automate it.
- **What happened:** with `use_zeta = False`, ogcore seeds savings at a hardcoded 0.07 for every age
  and group. Japan's solved savings are about 6.1, so the bequest seed landed 134× low in
  aggregate and 349× low for the top group. `K_d = B − D_d` started negative and the solve never
  converged in over 175 evaluations, silently restarting down `DEV_FACTOR_LIST`.
  `initial_guess_factor_SS` is capped at 500,000 while Japan's factor is about 7.0 million yen
  (IDN would be worse), so the right seed could not be entered. Retuning `initial_guess_r_SS` and
  `TR_SS` to solved values made it worse, though that comparison was uncontrolled.
  `ogjpn/warm_start.py` seeds `b`, `n`, the outer unknowns and `factor` from a solved state: 18–22
  evaluations, residual 5.5e-11. A to-do to automate it followed.
- **Evidence:** https://github.com/marcelolafleur/OG-JPN/commit/b62138c ;
  https://github.com/marcelolafleur/OG-JPN/commit/8a3122d ;
  https://github.com/marcelolafleur/OG-JPN/commit/58fa600 ;
  https://github.com/marcelolafleur/OG-JPN/commit/d7ff816 ;
  https://github.com/marcelolafleur/OG-JPN/commit/1b925dd ; `ogjpn/warm_start.py` at e438fa2,
  https://github.com/marcelolafleur/OG-JPN/blob/e438fa2/ogjpn/warm_start.py ;
  `docs/UPSTREAM_OGCORE.md` items 3 and 4.
- **When:** 2026-08 (2026-08-10), ogcore v0.19.0.
- **Note:** `docs/UPSTREAM_OGCORE.md` item 3 gives solved population-weighted savings of about 4.2,
  where `warm_start.py` and the audit say about 6.1. I found no OG-Core issue for the hardcoded
  seed or the factor cap (searched PSLmodels/OG-Core issues and PRs for "bequest seed", "b_guess",
  "initial_guess_factor_SS", "seed").

### Triage an RC_error by where in time it happens

- **Lesson:** read the per-period resource-constraint error even from a failed run; isolated spikes
  point to a discontinuity in a time-varying input.
- **What happened:** the JPN baseline transition raised `RuntimeError: ... (RC_error)`. The outer loop
  had converged cleanly (11 Anderson iterations, distance falling to 6.3e-06) and debt was flat at
  about 1.003, so it was neither oscillation nor runaway. Only 2 of 320 periods breached, t=2 and
  t=120, with neighbours five orders of magnitude smaller, and both lined up with jumps in `rho` and
  `imm_rates`. That led to the data-window and `fixper` findings. OG-Core's `TPI.py` writes
  `TPI_vars.pkl`, including `resource_constraint_error`, before it raises.
- **Evidence:** https://github.com/marcelolafleur/OG-JPN/commit/7bbdcc5 ;
  `docs/CALIBRATION_AUDIT.md` (Finding 8) at e438fa2; OG-Core `ogcore/TPI.py` at master,
  https://github.com/PSLmodels/OG-Core/blob/81f45496b9aec37bc82dc22aeebba31f055ca5e2/ogcore/TPI.py#L1874
  (pickle) and #L1899 (raise). The OG-JPN record does not say how the per-period errors were read.
- **When:** 2026-08 (7bbdcc5, 2026-08-10), ogcore v0.19.0.
