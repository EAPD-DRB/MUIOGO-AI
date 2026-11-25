<!-- GENERATED FILE - do not edit here.
     Source: docs/og-lessons/ETH.md
     Regenerate: python scripts/sync_shared.py -->

# Ethiopia (ETH): lessons behind the OG skills

What happened behind lessons in the OG skills (og-country-calibration,
og-multi-industry-calibration, og-solver-diagnosis, og-run). The skills teach the method; these
are one country's numbers, kept here so the skills stay general. They record what was true when
written; check the country repo before relying on any of them. Do not copy them into another
country's calibration.

Contents (by the skill file each entry backs; search a file for its `###` headings)
- og-country-calibration/SKILL.md
- og-country-calibration/references/macro-open-economy.md
- og-country-calibration/references/taxes-informality.md
- og-country-calibration/references/households-demographics.md
- og-country-calibration/references/validation-dashboard.md
- og-solver-diagnosis/references/solve-procedures.md
- shared/og-run-rules.md

## og-country-calibration/SKILL.md

### The mental model: judge the joint steady state, fiscal rows first

- **Lesson:** most parameters are weakly identified alone, so the test is whether the joint steady
  state resembles the economy, and the dashboard should lead with fiscal data.
- **What happened:** OG-ETH's macro chapter says the parameters are "only weakly identified from
  the data on their own" and compares the solved steady state and program-year paths with
  Ethiopian data. The table leads with fiscal rows: `D/Y` 0.505 against 50.5% (FY2024/25), external
  debt, `r_gov`, `T/Y` 0.093 against 7.8%, PIT/Y 1.36% against 1.4%, then `G/Y`, `TR/Y`, pensions
  and `I_g/Y`, all sourced to IMF Country Report 26/174. Production and price rows (`K/Y`, `C/Y`,
  `r`) come after.
- **Evidence:** table added in
  https://github.com/EAPD-DRB/OG-ETH/commit/15f424f3fd2eca22e144c1b36c5f8b82e5c0defc, merged in
  https://github.com/EAPD-DRB/OG-ETH/pull/70; current text at
  https://github.com/EAPD-DRB/OG-ETH/blob/49ec411ab7e6fe36938d402b5280aa2e84084516/docs/book/content/calibration/macro.md
- **When:** 2026-07 (written), 2026-09 (merged, OG-ETH 0.3.0); checked at upstream/main 49ec411.

## og-country-calibration/references/macro-open-economy.md

### Initial household wealth: the balance-sheet ratio and the capital-side number

- **Lesson:** prefer the capital-side measure of initial wealth, cross-check it against household
  balance sheets, and write down which you used.
- **What happened:** the earlier entry said OG-Core's own documentation tabulates balance-sheet
  ratios, with ETH at 1.70 (PHL 2.50, ZAF 2.56). That table was not found. What OG-ETH ships is the
  capital-side number: PWT `K/Y` about 2.2, less the inward FDI stock of about 0.24 of GDP
  (UNCTAD), plus domestically held public debt of 18.7% of GDP, giving 2.15 against a steady-state
  wealth ratio near 3.1. It lives in `ogeth.macro_params.INITIAL_WEALTH_RATIO` and needs
  PSLmodels/OG-Core#1189 (`initial_wealth_ratio`, still open).
- **Evidence:** 2.15 anchor in
  https://github.com/EAPD-DRB/OG-ETH/commit/55c2d1331a7e1cebf4e3a30d686328468c68ac58 (merged in
  https://github.com/EAPD-DRB/OG-ETH/pull/70); macro chapter at
  https://github.com/EAPD-DRB/OG-ETH/blob/49ec411ab7e6fe36938d402b5280aa2e84084516/docs/book/content/calibration/macro.md;
  https://github.com/PSLmodels/OG-Core/pull/1189. For the 1.70 figure: not found (searched: OG-Core
  docs on upstream/master 81f4549 and all local branches, the PR #1189 diff, GitHub code search on
  PSLmodels/OG-Core, OG-ETH docs).
- **When:** 2026-09 (OG-ETH anchor).

### Capital share (gamma): triangulate the labour share for an informal economy

- **Lesson:** in an agrarian or informal economy, adjust the labour share up using non-circular
  evidence and state `gamma` as a range with a centre.
- **What happened:** ILOSTAT's labour share for Ethiopia is 0.385 (2025), which implies a total
  capital share of 0.615. OG-ETH rejects it on three lines: `gamma = (r+δ)(K/Y)` with PWT `K/Y`
  about 2.2 would need an 18% real return; Gollin (2002) puts fuller adjustments at 0.65 to 0.80;
  and all land is state-owned, so imputed land rent inflates measured capital income. It adopts a
  labour share of 0.60, so `gamma` 0.30 after `gamma_g` 0.10, with a range of 0.25 to 0.35.
- **Evidence:** firms chapter, section "Calibrating the capital share", at
  https://github.com/EAPD-DRB/OG-ETH/blob/49ec411ab7e6fe36938d402b5280aa2e84084516/docs/book/content/calibration/firms.md;
  added in https://github.com/EAPD-DRB/OG-ETH/commit/15f424f3fd2eca22e144c1b36c5f8b82e5c0defc
  (https://github.com/EAPD-DRB/OG-ETH/pull/70).
- **When:** 2026-07 (written), 2026-09 (merged).

### Capital share (gamma): the live path clobbers the triangulated value

- **Lesson:** the `update_from_api=True` path recomputes the naive `1 − ILOSTAT` and silently
  overwrites a hand-triangulated `gamma`; take curated parameters off the live path entirely.
- **What happened:** `get_macro_params` still sets `gamma = 1 − labour share − GAMMA_G_LIC` from
  ILOSTAT when online, so it overwrites the shipped 0.30 with 0.515 (the firms chapter names 0.515
  as the ILOSTAT-implied value). PR #63 restricted the live pull but kept `gamma` on it, and
  refreshed the shipped value from it (0.51791 → 0.5169). Days later the triangulation set 0.30,
  and the live pull stayed. The macro chapter still lists `gamma` as a live parameter.
  The shipped `run_og_eth.py` passes `update_from_api=False`, but `run_og_eth_multi_industry.py`
  and `eth_imm_change.py` pass `True`. OG-IDN took `gamma` off the live path in its PR #55.
- **Evidence:** `ogeth/macro_params.py` at
  https://github.com/EAPD-DRB/OG-ETH/blob/49ec411ab7e6fe36938d402b5280aa2e84084516/ogeth/macro_params.py;
  https://github.com/EAPD-DRB/OG-ETH/pull/63; https://github.com/EAPD-DRB/OG-IDN/pull/55.
- **When:** 2026-07 (PR #63 merged 2026-07-03); still true at upstream/main 49ec411 (2026-10-19).

### Capital stock on one GDP basis after a rebasing

- **Lesson:** keep capital stocks and investment in one GDP basis; after a rebasing, measure the
  investment the old accounts missed against old-base GDP and convert the stock at the end.
- **What happened:** the first rebased build subtracted two investment shares with different
  denominators (35.3% of rebased GDP less 20.1% of old-base GDP) and left the stock over old-base
  GDP, giving total K/Y 2.51. A reviewer's audit found it; in one basis the gap is 36.1 points of
  old-base GDP and total K/Y 2.00. Initial wealth, depreciation and the foreign capital share all
  moved with it, and the whole retune was redone.
- **Evidence:** the review on https://github.com/EAPD-DRB/OG-ETH/pull/111; fix in OG-ETH commit 6119f1d.
- **When:** 2026-11.

### Patience: one discount factor to the long-run return when the state finances investment

- **Superseded (2026-11-25)** by "Patience: as much saving as the return evidence allows, judged on the first years" below. The premise did not hold for ETH today: state investment is about 3–4 percent of GDP, and the remaining gap was household saving.

- **Lesson:** where the state, state enterprises or foreign lenders finance much of investment, do
  not tune patience to first-year investment; set one discount factor to the long-run return at
  the world rate and score investment as a check. Use wealth shares by income group as a check if
  matching them forces patience above one or to its lower bound.
- **What happened:** tuning patience to first-year investment (35.3% of rebased GDP) made
  households finance all of it, including state-enterprise investment financed through state banks,
  and needed a long-run return near 2% with foreign capital leaving. The measurable state channels
  (state-enterprise retained earnings about 0.7% of GDP, financial repression beyond the
  below-market government rate about 0.2%) closed less than a point. Matching the WID wealth shares
  by group pushed the top group's patience above one and the bottom's to 0.5. One discount factor
  set to the 4% world rate gave 0.903 (after the preference change below), with first-year
  investment 27.5% against 35.3% reported as a measured miss.
- **Evidence:** https://github.com/EAPD-DRB/OG-ETH/pull/111; OG-ETH commits c257c41, 814a1d7, 93ce1f3; validation chapter of OG-ETH.
- **When:** 2026-11.

### External debt at its own interest rate

- **Lesson:** where external debt is large and mostly concessional, check whether your ogcore models
  debt contracted abroad (`alpha_D_ext`, `r_D_ext_annual`); without it that debt earns the
  household return and interest paid abroad is overstated. Held at a share of GDP with a rate below
  growth, it gives the long-run budget a net inflow from abroad; phase it out where that is wrong.
- **What happened:** with Ethiopia's external debt (15.5% of rebased GDP) held as market debt
  abroad, interest on it was 1.6% of GDP against about 0 in the data. Modelled at the DSA's average
  rate (about −1% real), it was −0.2%. OG-ETH follows the IMF DSA path to 2045 and then phases the
  stock to zero. A reform now starts from the baseline's stock.
- **Evidence:** https://github.com/PSLmodels/OG-Core/pull/1279 (Issue #1125) and its review; https://github.com/EAPD-DRB/OG-ETH/pull/111.
- **When:** 2026-11.

### Initial wealth distribution by a damped burn-in

- **Lesson:** with no wealth-by-age data, impute `initial_hhwealth_dist` from the model: feed the
  savings households choose in the first period back as the starting shape, part of the way each
  round and only at life-cycle ages, until start and first period agree; report the gap.
- **What happened:** the steady-state shape handed first-year households a windfall. A full
  feedback step stalled the transition (74 iterations) because the oldest cohorts' first-period
  savings are mostly bequests; 30% per round at ages below 80 converged. The gap that remained
  (4.6% weighted by wealth) sat at ages 21–24, which hold about 2% of wealth.
- **Evidence:** OG-ETH `ogeth/initial_wealth.py`; commits 814a1d7, 4e90baa, 2480d1e.
- **When:** 2026-11.

### Patience: as much saving as the return evidence allows, judged on the first years

- **Lesson:** patience sets household saving; today's returns do not depend on it (technology and the measured capital stock fix them). Judge it on the first transition years (private consumption and investment against the data), not the steady state, and set it as high as the long-run bounds allow: the owners' long-run return on capital (firms' return plus public-capital rent, government debt excluded) at or above the bottom of the return evidence, and foreign-owned capital non-negative in the steady state. Do not jump between the two extremes (first-year investment fully matched; the steady-state firms' return at the world rate).
- **What happened:** patience had been tuned to first-year investment (needing a long-run return near 2 percent), then from 16 November to the steady-state firms' return at the 4 percent world rate (0.887 to 0.903). The steady-state sweep looked weak (0.887 to 0.95 moved long-run consumption only 81.9 to 78.7 percent of GDP), but one transition probe at 0.94 moved first-year consumption from 77.6 to 70.0 and investment from 24.9 to 30.8 (data 64.4 and 35.3): the measured starting stock sits below what more patient households hold, so they build capital, from 1.66 to 1.84 times GDP by 2035, and the firms' return falls to the world rate by about 2035. At 0.94 the owners' long-run return on capital is 6.1 percent (evidence range 6–10); from 0.96 the steady state exports capital. Adopted 0.94 as a documented constant; about 60 percent of the consumption and investment gap closed.
- **Evidence:** https://github.com/EAPD-DRB/OG-ETH/pull/111; OG-ETH commit fdd3b2b; validation and households chapters.
- **When:** 2026-11.

### Compare return evidence with the return on capital to owners, not the portfolio return

- **Lesson:** OG-Core's `r_p` averages the return on capital with government debt at `r_gov`; where debt is repressed it reads far below the return on capital. Evidence on returns (FDI returns, Caselli-Feyrer) is about capital: compare it with `r + (1 − tau_b)·MPK_g·K_g/K` (`aggregates.get_r_p`), not `r_p`.
- **What happened:** a first patience target used `r_p` (8.1 percent in 2025, with `r_gov` at −10.4) while the capital return was 9.4; an adversarial review caught it before the push.
- **Evidence:** https://github.com/EAPD-DRB/OG-ETH/pull/111; OG-ETH `targets.ss_moments` (`r_K`).
- **When:** 2026-11.

### zeta_K raises investment only through foreign ownership

- **Lesson:** raising `zeta_K` to close an investment gap buys capital owned by foreigners, as a jump in the first year rather than a build-up, and pays them the owners' return; keep it on the measured foreign share.
- **What happened:** a probe at 0.95 (from 0.185) put first-year investment at 33.9 percent of GDP but the foreign share of private capital at 32 percent (59 by 2050, FDI data 10), net exports at −9.1 (data −4.4) and payments abroad at 3.4 percent of GDP (data 0.4).
- **Evidence:** OG-ETH exploration notes, 2026-11-25 (local).
- **When:** 2026-11.

### State enterprises' foreign loans sit in household wealth unless counted

- **Lesson:** loans that state enterprises owe abroad are neither government external debt nor FDI; if left out of both, the initial-wealth construction counts the capital they financed as household wealth. Either treat guaranteed infrastructure enterprises as part of the state (external debt at its own rate, public investment, public capital) or add the loans to the foreign capital target; with OG-Core paying foreign capital the owners' return, the second raises payments abroad, so weigh it before adopting.
- **What happened:** 6.3 percent of rebased GDP (Ministry of Finance Bulletin 56) sat in household wealth. A probe moving it to foreign capital raised investment 0.8 points and payments abroad from 1.16 to 1.77 percent of GDP (data 0.37); documented as a known inconsistency instead.
- **Evidence:** https://github.com/EAPD-DRB/OG-ETH/pull/111; macro chapter of OG-ETH.
- **When:** 2026-11.

### An investment gap: decompose it with the financing identity before choosing a lever

- **Lesson:** before attributing an investment gap to the state or to the capital share, write investment = domestic saving + net foreign financing for the data and the model, measure state investment today (budget capital spending, state-enterprise flows), and read the country's financing history; the gap's half that is missing names the lever.
- **What happened:** the 2005–2019 boom was financed by saving drawn through state banks, state enterprises' foreign borrowing, and remittances and grants (IMF CR 13/308, 20/29); today state investment is 3–4 percent of GDP and the current account about −0.7. With the dashboard corrected, the model's net foreign financing was close to the data and the whole gap was household saving; a week spent on the capital share, the state-investment story, `zeta_K` and state-enterprise loans would have been saved.
- **Evidence:** https://github.com/EAPD-DRB/OG-ETH/pull/111; OG-ETH exploration and financing-history notes, 2026-11-25 (local).
- **When:** 2026-11.

### Capital stock at current national prices; public capital in nominal terms

- **Lesson:** keep the capital stock, investment and depreciation on one price basis, current national prices, nominal over nominal; take public capital from a nominal series.
- **What happened:** the capital-output ratio was first taken from PWT at current PPPs (2.167 in 2023). The PWT stock at current national prices over GDP at current prices was 2.366, 9 percent higher; the two differ by up to a third in other years (2010: 2.52 at PPP, 1.85 at national prices). The public stock first used IMF ICSD's real ratio (0.667) where the nominal one is 0.840. An estimate of the relative price of investment (3.8) was dropped for the direct stock.
- **Evidence:** https://github.com/EAPD-DRB/OG-ETH/pull/111; OG-ETH `ogeth/macro_params.py` (PWT_CAPITAL_OUTPUT_RATIO, PUBLIC_CAPITAL_OUTPUT_RATIO), `scripts/derive_sourced_values.py`, `ogeth/data/pwt110_eth_capital*.csv`.
- **When:** 2026-11-16.

### Capital share: inefficiency counted once, side implications checked, published sources

- **Lesson:** put the inefficiency of public investment in one place (leakage and the measured stock), check the labour share and return a chosen capital share imply, and cite the published version of an estimate.
- **What happened:** the inefficiency was applied both to the output elasticity of public capital and through leakage; the elasticity was the Bom-Ligthart working-paper figure (0.08) where the published article gives 0.083 short run and 0.122 long run; a lower capital share then implied a labour share near 0.76, double the measured one. Half a day of revisions.
- **Evidence:** https://github.com/EAPD-DRB/OG-ETH/pull/111; session record 2026-11-16.
- **When:** 2026-11-16.

### Starting wealth smooth across an age cutoff

- **Lesson:** keep starting wealth smooth across any age boundary used in its construction.
- **What happened:** the burn-in of the starting wealth shape stopped at 80 and the oldest ages kept another shape; the step at 80 made the household solve fail for the poorest cohorts crossing it, in three runs. Continuing ages 80 and over from age 79 per person fixed it.
- **Evidence:** OG-ETH commit 460109e.
- **When:** 2026-11.

## og-country-calibration/references/taxes-informality.md

### Standing check: the bequest tax: ETH ships 0

- **Lesson:** compute `tau_bq` from collections over model bequest flows, and grep every port for
  it.
- **What happened:** the first OG-ETH commit shipped `tau_bq = 0.2`, the OG-ZAF value. PR #3 set
  it to 0.0 a month later, and the taxes chapter says wealth and bequest taxes are zero in the
  default calibration. upstream/main still ships 0.0. Zero was set by statement, not derived from
  collections.
- **Evidence:** 0.2 in https://github.com/EAPD-DRB/OG-ETH/commit/97dbf24f04bd7423a33a84a994ceb1700b653b75;
  0.0 in https://github.com/EAPD-DRB/OG-ETH/commit/2a3124561fe3a5496964f6fa945ffb8f2f688ca2
  (https://github.com/EAPD-DRB/OG-ETH/pull/3); current JSON at
  https://github.com/EAPD-DRB/OG-ETH/blob/49ec411ab7e6fe36938d402b5280aa2e84084516/ogeth/ogeth_default_parameters.json
- **When:** 2025-10 (0.2), 2025-11 (0.0); checked at upstream/main 49ec411 on 2026-10-19.

### Informality: the maturity ladder: graded household non-compliance ("Option A")

- **Lesson:** where data allow, grade income-tax non-compliance by lifetime-income group, keep
  every group a filer, and anchor the level to revenue.
- **What happened:** about 85% of Ethiopian employment is informal (ILO 2021). An exploration
  branch assessed three options and completed "Option A": the bottom five of seven groups (90% of
  households) remit no income tax, with a statutory 35% top MTR and the compliant-group ETR from a
  revenue identity. It landed on main in July 2026 with labour and capital non-compliance equal
  and `income_tax_filer` all ones. On main at 49ec411 the form has since moved on: the statutory GS
  schedule with the compliance shape [0, 0, 0, 0, 0, 0.5, 1] times a calibrated
  `COMPLIANCE_SCALE` (0.198381), so PIT collects 1.4% of GDP.
- **Evidence:** assessment at
  https://github.com/marcelolafleur/OG-ETH/blob/356673faefe0e072abf5d5f7cb45b66bf0803930/INFORMALITY.md
  and status commit https://github.com/marcelolafleur/OG-ETH/commit/ce8a230f10c66afa2f7af6da27cf4914cfa47897;
  main change https://github.com/EAPD-DRB/OG-ETH/commit/a991f6e6baff07e10ea890d83b9385f100001cba
  (https://github.com/EAPD-DRB/OG-ETH/pull/70); current taxes chapter at
  https://github.com/EAPD-DRB/OG-ETH/blob/49ec411ab7e6fe36938d402b5280aa2e84084516/docs/book/content/calibration/taxes.md
- **When:** 2026-07 (Option A, ogcore 0.16.3); current form checked at 49ec411 on 2026-10-19.

## og-country-calibration/references/households-demographics.md

### Earnings (the e ability matrix): ETH used the Gini tilt, then replaced it

- **Lesson:** the family reuses OG-USA's `e` matrix with a single-scalar exponential tilt to the
  country's Gini.
- **What happened:** OG-ETH used the tilt, `get_e_interp(gini_to_match=31.1)`, until September
  2026. PR #70 replaced it: the OG-USA matrix is reshaped over age with the NTA labour-income
  profile (Ethiopia 2005 against the US 2006) and across groups with WID pre-tax income shares
  (2021). The commit says this fixes the consumption-Gini against income-Gini mismatch of issue
  #33. A Gini tilt remains as an option (`tilt_to_gini`). So ETH no longer ships the family method;
  it ships both halves described in EAPD-DRB/OG-ZAF#18.
- **Evidence:** https://github.com/EAPD-DRB/OG-ETH/commit/5a39a86c9486c3ab4c3599f6bbf27fa3134c739e
  (https://github.com/EAPD-DRB/OG-ETH/pull/70); https://github.com/EAPD-DRB/OG-ETH/issues/33
  (still open).
- **Code:** [ogeth/income.py at 402b71d](https://github.com/marcelolafleur/OG-ETH/blob/402b71d3518bccf5943b1d38e7f82be227b61c35/ogeth/income.py) (NTA age factor and WID group shares).
- **When:** tilt until 2026-09; replaced in 0.3.0 (merged 2026-09-26).

### Demographics: method and country_id: the wrong literal, twice

- **Lesson:** use one named `country_id` constant and add a test that it matches the country.
- **What happened:** the first `calibrate.py` passed `country_id="710"` (South Africa) instead of
  "231" (Ethiopia). PR #3 fixed it. In April 2026 a rewrite of `calibrate.py` in PR #22 brought 710
  back at both call sites. PR #49 fixed it again; its author called 710 "a leftover from the OG-ZAF
  lineage". PR #70 then added `UN_COUNTRY_CODE = "231"` and a test. The test checks the call
  against the constant, not against "231", so a wrong constant would still pass.
- **Evidence:** https://github.com/EAPD-DRB/OG-ETH/commit/97dbf24f04bd7423a33a84a994ceb1700b653b75
  (710); https://github.com/EAPD-DRB/OG-ETH/commit/ebb1a3704d912c34d096484a4b75f1d61964b6cd
  (fix, https://github.com/EAPD-DRB/OG-ETH/pull/3);
  https://github.com/EAPD-DRB/OG-ETH/commit/9be21bb5f81f9f53d4fe4bb912e328d0a120403f (710 again,
  https://github.com/EAPD-DRB/OG-ETH/pull/22);
  https://github.com/EAPD-DRB/OG-ETH/commit/719ec9186965b56bf7ce0f7b06faf99ec307552e (fix,
  https://github.com/EAPD-DRB/OG-ETH/pull/49; an earlier attempt,
  https://github.com/EAPD-DRB/OG-ETH/pull/46, was closed);
  https://github.com/EAPD-DRB/OG-ETH/commit/285fb03f3676f8a2204e1ce0c880226f4583a8ab (constant and
  test in `tests/test_demographic_gradients.py`).
- **When:** 2025-10 and 2026-04 (regressions); 2025-11 and 2026-06 (fixes); 2026-09 (constant).

### Pensions: the factor seed sits exactly at the validator cap

- **Lesson:** check that the factor seed sits in the validator range; a seed of exactly 500,000
  was probably clipped to the cap, so compare it with the solved `factor`.
- **What happened:** OG-ETH upstream/main ships `initial_guess_factor_SS` exactly 500,000.0, with
  `mean_income_data` 353,049.55 birr. It is clipped by design: `ogeth.labor.factor_guess` returns
  `min(solved factor, 500000)`, citing OG-Core's cap. So the solved factor was at least 500,000; the
  repo does not record its value. The seed was 322,971 before the September 2026 earnings and
  `chi_n` recalibration. OG-Core validates the seed to at most 500,000.
- **Evidence:** JSON at
  https://github.com/EAPD-DRB/OG-ETH/blob/49ec411ab7e6fe36938d402b5280aa2e84084516/ogeth/ogeth_default_parameters.json;
  `factor_guess` at
  https://github.com/EAPD-DRB/OG-ETH/blob/49ec411ab7e6fe36938d402b5280aa2e84084516/ogeth/labor.py;
  seed change https://github.com/EAPD-DRB/OG-ETH/commit/5a39a86c9486c3ab4c3599f6bbf27fa3134c739e;
  cap at
  https://github.com/PSLmodels/OG-Core/blob/81f45496b9aec37bc82dc22aeebba31f055ca5e2/ogcore/default_parameters.json.
  Solved factor value: not found (searched: OG-ETH docs, CHANGELOG, PR #70 body, code).
- **When:** 2026-09 (seed set); checked at upstream/main 49ec411 on 2026-10-19; cap checked on
  OG-Core master 81f4549 (v0.21.2).

### Preferences: a subsistence floor instead of a high sigma

- **Lesson:** where subsistence consumption is common and growth is fast, keep sigma near OG-Core's
  default and set the subsistence floor `c_min` (Stone-Geary) to a sourced cost; a high sigma for
  every household makes richer households consume against future income and pins patience at its
  bound. Cap the floor at what the poorest group can afford at its lowest-consumption age.
- **What happened:** the low elasticity of substitution measured near subsistence (Havranek 2015;
  Ogaki, Ostry and Reinhart 1996) first led to sigma 3 for everyone. With labour productivity
  growing 4.7% a year, patience then sat at its 0.995 bound and the long-run return stayed at 4.75%
  against 4%. With sigma 1.5 and `c_min` at 80% of the cost of an energy-sufficient diet
  (World Bank/FAO Food Prices for Nutrition; the full cost would have put the poorest group below
  the floor), patience fell to 0.903, first-year investment rose from 23.2% to 27.5% of GDP and
  private consumption fell from 79.7% to 68.2% (data 35.3 and 64.4). Correction (2026-11-25): the 68.2 was read from OG-Core's `C`, which excludes the floor; counted with the floor (`C_i`) private consumption was about 6.5 points higher (see "Consumption with a subsistence floor"). The effective sigma is 2.2 for
  the poorest group and 1.63 at mean consumption. The Ethiopia Socioeconomic Panel Survey 2021/22
  supports the floor: three-quarters of loans come from relatives and neighbours, 0.1% from banks,
  and 80% of savers save for emergencies, 0.9% for old age. `c_min` is in growth-adjusted units and
  the model's reported consumption is the part above the floor.
- **Evidence:** https://github.com/EAPD-DRB/OG-ETH/pull/111; OG-ETH commit 93ce1f3; `examples/ess_credit_saving.py`.
- **When:** 2026-11.

### Labour units: scale the earnings matrix, not productivity

- **Lesson:** when `chi_n` runs into OG-Core's 10,000 bound because model consumption is small,
  rescale the earnings matrix (exact); rescaling productivity `Z` is not neutral, because OG-Core's
  capital demand at the world rate leaves out public capital, and `Z` is capped at 5.
- **What happened:** at sigma 3, `chi_n` exceeded the bound at every age. `Z` = 5 moved the foreign
  capital share; `e` × 10 reproduced every ratio of the original solution in a probe.
- **Evidence:** OG-ETH commit 04d4701; `ogeth.macro_params.EARNINGS_SCALE`.
- **When:** 2026-11.

### Consumption by age: the consumption adults carry, and the model's age convention

- **Lesson:** OG-Core's households start at age `E` (completed years: UN ages 0–99, rows from `E`) and have no children, while national-accounts consumption includes children's. Target consumption per adult with each adult carrying the people under `E` they support, fit net family transfers (`phi_FT`) to it, and report the fit as by construction. A default target for any country: own consumption by age from a cross-country model of the NTA profiles (log GDP per capita PPP and the old-age dependency ratio), plus children's consumption given to parents by UN fertility and population with DHS medians for spousal age gaps and children not living with a parent.
- **What happened:** the 2005 NTA profile (own consumption, a young-adult peak at 1.16) drove large transfers to young adults; the carried-consumption target (0.52 at 20, peak 1.10 in the forties) was within 0.057 of Ethiopia's ESPS 2021/22 survey built the same way. A first version labelled the first model age 21, a one-year shift, fixed before the push.
- **Evidence:** https://github.com/EAPD-DRB/OG-ETH/pull/111; at commit 402b71d: [ogeth/data/consumption_by_age.csv](https://github.com/marcelolafleur/OG-ETH/blob/402b71d3518bccf5943b1d38e7f82be227b61c35/ogeth/data/consumption_by_age.csv) (its header documents the build), [examples/fit_family_transfers.py](https://github.com/marcelolafleur/OG-ETH/blob/402b71d3518bccf5943b1d38e7f82be227b61c35/examples/fit_family_transfers.py).
- **When:** 2026-11.

### Hours by age: an extrapolated target double-counted the fall in pay

- **Lesson:** fit `chi_n` on the ages the survey covers, with old-age targets from survey bands; an old-age target built from labour income per person counts the fall in pay twice. Judge `chi_n` by its rise from prime to old age; stop after two workarounds that do not converge and look for the missing mechanism.
- **What happened:** with sigma 1.5 and the subsistence floor, `chi_n` hit OG-Core's 10,000 bound from age 64 and the fit asked for 1 to 3 million at 80 and over. The hours target beyond the survey had been tapered with NTA labour income per person, which already contains the wage fall that `e` applies again (fixed in commit 78748d5). A chain of workarounds followed over about three working days (an end to working life at 80, direct support for the poorest elderly, a raised cap, ten-fold steps), each breaking the steady state or the transition. It was resolved by a target from survey bands (commit 2aa75b1), transfer shares by year (OG-Core PR 1297) and family transfers fitted to consumption by age (OG-Core PR 1298), with `chi_n` free through 69.
- **Evidence:** https://github.com/EAPD-DRB/OG-ETH/pull/111; OG-ETH commits 78748d5, c7550b6, 2aa75b1; PSLmodels/OG-Core#1297, #1298.
- **When:** 2026-11-19 to 11-24.

### Transfer shares fixed over time overpaid the oldest

- **Lesson:** check transfers per person by age and group along the transition; a fixed `(S, J)` share of transfers with an ageing population pays the oldest more each year. Use transfer shares by year where your ogcore has them, built from each year's population.
- **What happened:** OG-Core's `eta` and `eta_RM` are held at one `(S, J)` matrix over the whole path. As the population aged, transfers per person to the oldest rose to between 5 and about 160 times the intended amount in the early decades (the poorest group at 95: 80 times). The overpayment masked the old-age labour problem; with shares by year, people over 80 consumed a third less and worked more in the early years.
- **Evidence:** PSLmodels/OG-Core#1297 (open); OG-ETH test branch runs of 2026-11-23.
- **When:** 2026-11-19 to 11-23.

### A cross-country table value was a formula applied out of sample

- **Lesson:** before using a country's value from a cross-country table, check whether it is an estimate for that country or a formula applied to it, and whether the country is inside the sample; and use the model's existing levers before drafting an OG-Core change.
- **What happened:** a table in Ogaki, Ostry and Reinhart (1996) gave Ethiopia an elasticity implying sigma 19.2, next to 1.8 for the Philippines; the values came from one fitted formula applied at an assumed subsistence level. An OG-Core change to raise the sigma ceiling was drafted and a second session started before the case was dropped for sigma 1.5 with a subsistence floor. About a day and a half.
- **Evidence:** session record 2026-11-17/18; OG-ETH commit 93ce1f3.
- **When:** 2026-11-17.

### The poorest group's bequest weight broke a reform

- **Lesson:** when a transition fails for old households of one group, read that group's wealth and transfers by age; a bequest weight inherited from other groups can make the poorest hoard.
- **What happened:** the reform transition failed at age 90 in the poorest group (Euler error 109), the same on the released ogcore. That group, at the subsistence floor, held wealth to 3.15 with transfers several times its consumption; a `chi_b` of its own (8.73) fixed it.
- **Evidence:** session record 2026-11-11; OG-ETH JSON `chi_b`.
- **When:** 2026-11-11.

### A sourced value is not a tuning lever

- **Lesson:** a parameter settled from evidence (Frisch, sigma) is not moved to hit a target; a target it would need flags a missing piece.
- **What happened:** moving Frisch to its maximum was proposed to close old-age hours; it had been settled at 0.25 from bias-corrected evidence, and the gap was a missing mechanism (family support).
- **Evidence:** session record 2026-11-23.
- **When:** 2026-11-23.

## og-country-calibration/references/validation-dashboard.md

### The steady-state dashboard: a data-comparison table in macro.md

- **Lesson:** put a table in `macro.md` comparing the solved steady state with data targets, each
  with a source, tiered fiscal first.
- **What happened:** OG-ETH's macro chapter has a 20-row table with a data-source column, for the
  history-anchored baseline and the program scenario. Rows include `D/Y`, external debt, `r_gov`,
  `T/Y`, PIT/Y, `G/Y`, `TR/Y`, pensions, `I_g/Y`, `RM/Y`, `K_f/Y`, `K/Y`, `B/Y`, `(I+I_g)/Y`, `C/Y`,
  `CA/Y`, `NX/Y`, factor payments and `r`. It records misses too: `NX/Y` −4.1 to −4.5% against −8.3
  to −9.9%, explained by factor payments abroad of 5.8% of GDP against about 1%.
- **Evidence:** https://github.com/EAPD-DRB/OG-ETH/blob/49ec411ab7e6fe36938d402b5280aa2e84084516/docs/book/content/calibration/macro.md;
  https://github.com/EAPD-DRB/OG-ETH/pull/70.
- **When:** 2026-07 (written), 2026-09 (merged).

### Fast value-pinning test: test_default_parameters.py

- **Lesson:** a fast test loads the shipped JSON and pins calibrated values with sources, asserting
  nothing that needs a solve.
- **What happened:** OG-ETH added `tests/test_default_parameters.py` with the informality
  calibration. It pins the statutory tax functions, non-compliance by group, the CIT collections
  factor, all-filers and array shapes, cites IMF SIP 2025/108, IMF CR 26/20 and ILO 2021, and says
  the revenue split "requires a model solve and is therefore intentionally NOT asserted here". Its
  docstring still describes the July form (ETR 0.0871 from a revenue identity), which main has
  since replaced.
- **Evidence:** https://github.com/EAPD-DRB/OG-ETH/commit/a991f6e6baff07e10ea890d83b9385f100001cba;
  https://github.com/EAPD-DRB/OG-ETH/blob/49ec411ab7e6fe36938d402b5280aa2e84084516/tests/test_default_parameters.py
- **When:** 2026-07 (added); checked at 49ec411.

### Prevent doc/JSON drift with glue: the taxes chapter

- **Lesson:** a hidden docs cell loads the packaged JSON and `glue()`s the numbers so prose cannot
  drift.
- **What happened:** issue #40 asked that the docs reflect current calibration values. PR #42
  made the taxes chapter read rates such as `tau_payroll` and `cit_rate` from
  `ogeth_default_parameters.json` through `myst_nb.glue`, and closed the issue. Only the taxes
  chapter uses it at 49ec411.
- **Evidence:** https://github.com/EAPD-DRB/OG-ETH/issues/40;
  https://github.com/EAPD-DRB/OG-ETH/pull/42;
  https://github.com/EAPD-DRB/OG-ETH/commit/159315fba05a8b7c364a96ca8f315c54b22cbe7f
- **When:** 2026-05.

### Government consumption: score against the measured series

- **Lesson:** score `G/Y` against measured government final consumption, adding the depreciation
  of public capital as the national accounts do, not against the expenditure-side residual.
- **What happened:** the rebased residual (4.7% of GDP) holds non-profit institutions and the
  statistical discrepancy; the central bank's series is 3.67%, and the model came within 0.3 point
  of it.
- **Evidence:** OG-ETH commit 8b8a2fa.
- **When:** 2026-11.

### Consumption with a subsistence floor: score `C_i`, not `C`

- **Lesson:** with `c_min > 0`, OG-Core saves `C` as consumption above the floor and `C_i` as spending on goods, floor included (the resource constraint's consumption). Score private consumption and net exports with `C_i`, and check every solve that consumption, investment, government consumption and net exports add up to GDP.
- **What happened:** from the floor's introduction (18 November) the dashboard read `C`, understating private consumption and overstating net exports by about 6.5 points of GDP (71.1 against 77.6; +1.1 against −5.4). The reported trade surplus sent the diagnosis toward foreign financing for a week. It was found when the current account computed from flows (+4.5) contradicted the change in foreign liabilities (−2.0).
- **Evidence:** https://github.com/EAPD-DRB/OG-ETH/pull/111; OG-ETH commit fdd3b2b (`targets.py`).
- **When:** 2026-11.

### Docs numbers typed by hand went through six audits

- **Lesson:** write the docs once the calibration settles, take every number from the final run through generated tables and glue, and audit once.
- **What happened:** calibration chapters written while tuning carried hand-typed numbers that each retune made stale; six audit rounds followed before the generator produced every table from the official run.
- **Evidence:** https://github.com/EAPD-DRB/OG-ETH/pull/111; at commit 402b71d: [docs/create_doc_figures.py](https://github.com/marcelolafleur/OG-ETH/blob/402b71d3518bccf5943b1d38e7f82be227b61c35/docs/create_doc_figures.py), [ogeth/targets.py](https://github.com/marcelolafleur/OG-ETH/blob/402b71d3518bccf5943b1d38e7f82be227b61c35/ogeth/targets.py) (market-price basis, `C_i`, the owners' return), [examples/tune.py](https://github.com/marcelolafleur/OG-ETH/blob/402b71d3518bccf5943b1d38e7f82be227b61c35/examples/tune.py), [tests/test_update_baseline.py](https://github.com/marcelolafleur/OG-ETH/blob/402b71d3518bccf5943b1d38e7f82be227b61c35/tests/test_update_baseline.py) (the packaged JSON equals what the code regenerates).
- **When:** 2026-11.

### The calibration PR as a fit report

- **Lesson:** the PR shows the fit to data in tables and figures from the run, with no history, comparisons with earlier runs, tested alternatives or reform results; an independent review checks every number before the push.
- **What happened:** the PR text was rewritten more than five times; a reform table and a tested block were removed ("we are building a calibration, not assessing policy"); a fresh reviewer found twelve problems, two serious, in a draft its author had checked.
- **Evidence:** https://github.com/EAPD-DRB/OG-ETH/pull/111 (description).
- **When:** 2026-11-25.

## og-solver-diagnosis/references/solve-procedures.md

### Running against an unreleased ogcore: ETH's main pins ogcore by commit

- **Superseded (2026-11-25)** for the build: OG-ETH 0.4.0 pins the integration build in the next entry; the method (pin by commit, official installer) is unchanged.

- **Lesson:** to run on an unreleased ogcore, keep the official installer and pin ogcore by commit
  in `[tool.uv.sources]`.
- **What happened:** OG-ETH 0.3.0 needs two OG-Core changes its PR calls unreleased,
  `initial_wealth_ratio` (PSLmodels/OG-Core#1189, still open) and `r_gov_floor` (#1203, since
  merged). Its `pyproject.toml` pins ogcore to
  `marcelolafleur/OG-Core` at `edaa78ab`, a master-plus-#1189 build, while the PyPI metadata keeps
  `ogcore>=0.20.0`. On a released OG-Core the example falls back and says so. The skill
  recommends keeping such a pin off the calibration branch; ETH's main carries it.
- **Evidence:** https://github.com/EAPD-DRB/OG-ETH/commit/e9284552f311f4393a4412f6101681eb22fb5c94;
  https://github.com/EAPD-DRB/OG-ETH/blob/49ec411ab7e6fe36938d402b5280aa2e84084516/pyproject.toml;
  https://github.com/EAPD-DRB/OG-ETH/pull/70.
- **When:** 2026-09.

### The integration build with debt abroad, transfer shares by year and family transfers

- **Lesson:** features the calibration needs before they are released (debt contracted abroad, `eta` by year, net family transfers) come from one integration build of OG-Core pinned by commit, installed the official way; a lesson that needs them says how to check a build for them.
- **What happened:** OG-ETH 0.4.0 pins `marcelolafleur/OG-Core` at `e0415472` (branch `int/eth-pin-v2`): OG-Core 0.25.2 plus PSLmodels/OG-Core#1279 (`alpha_D_ext`, `r_D_ext_annual`), #1297 (`eta` and `eta_RM` by year; `number_dims` 3) and #1298 (`phi_FT`), all open on 2026-11-25.
- **Evidence:** [pyproject.toml at 402b71d](https://github.com/marcelolafleur/OG-ETH/blob/402b71d3518bccf5943b1d38e7f82be227b61c35/pyproject.toml) (`[tool.uv.sources]`); https://github.com/PSLmodels/OG-Core/pull/1279, /1297, /1298.
- **When:** 2026-11.

## shared/og-run-rules.md

### Leads come from installer copies too: hand-built probe paths produced invalid tuning rounds

- **Lesson:** every run, probes and tuning included, comes from an installer copy through the
  repo's own scripts; "it is only a lead" never licenses a hand-built environment, a wrapper, a
  patch at run time, a merge script or a step launched by hand. The preflight now fails these
  (og-run-rules.md, "Install with the official installer", "Calibration tuning runs through repo
  code too", "Evidence about the model"; og-run-preflight).
- **What happened:** testing concessional debt (PSLmodels/OG-Core#1125) in OG-ETH's rebased
  recalibration, an agent built a plain clone and installed an OG-Core worktree into it with
  `uv pip install -e`. That replaced the branch's own ogcore pin, so the first runs went without
  the speed fixes #1276 and #1277 the pin carried. It wrapped `examples/tune.py` in a script that
  monkeypatched OG-ETH's sovereign-rate rule, and drove rounds with its own shell loop whose merge
  step existed because `tune.py --next` writes only the dials. Twice settings were lost: a round
  that dropped the rebased capital stocks, and a round 4 launched after a step started by hand
  skipped the merge, so it ran with neither the capital stocks nor the concessional debt
  (K/Y 1.58 against 2.09, r 12.8 percent). All results from that environment were leads. The
  earlier tuning copy had been installed properly but then moved five times with `git pull`, and
  its installer log was written to a scratch folder, so no record ties it to the installer. The
  preflight of the day passed hand-built checkouts as "GO (dev checkout -- in-task probes only)"
  and only warned on an editable ogcore.
- **Evidence:** session logs of 2026-11-12/13 (OG-ETH branch calib/rebased-fy2025, tuning folder
  og-runs/eth-oda); the preflight run on that environment fails on four counts with the new
  checks.
- **When:** 2026-11, ogcore 0.24.4 / 0.25.0 (local integration build).

### One model job at a time

- **Lesson:** run one model job at a time, and compare installed copies one after the other on an
  idle machine (og-run-rules.md, "One model job at a time").
- **What happened:** twice in two days an agent overlapped jobs to save time: two tuning arms
  beside OG-Core's test suite, then a retune beside the test suite, each with seven workers on a
  ten-core machine. Both ran at about half speed, the timings could not be quoted, and the owner
  asked for one job at a time. In the evaluation that followed, an agent answering S12 with the
  skills still planned to run its treatment and control copies in parallel and compare their
  times.
- **Evidence:** session logs of 2026-11-12/13; evals/og-skills/scores/2026-11-13.md.
- **When:** 2026-11.

### Exploring: one probe per idea, watch the run, one finished calibration

- **Lesson:** while exploring, one probe per idea, read for what it buys and costs; tune static dials on warm steady states and spend transition rounds only on what the transition judges; watch the log and CPU from launch; measure a choice with one switch-off run from the finished calibration rather than parallel arms.
- **What happened:** ten transition solves and four rounds per idea while exploring; two control and treatment arms tuned in parallel for three rounds each (about two hours); stalled runs waited on for an hour that were a ladder of restarts; mechanisms stated without computing them from the output sent the work the wrong way more than once.
- **Evidence:** session records 2026-11-12 to 11-25.
- **When:** 2026-11.
