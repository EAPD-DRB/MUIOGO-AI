<!-- GENERATED FILE - do not edit here.
     Source: docs/og-lessons/ZAF.md
     Regenerate: python scripts/sync_shared.py -->

# South Africa (ZAF): lessons behind the OG skills

What happened behind lessons in the OG skills (og-country-calibration,
og-multi-industry-calibration, og-solver-diagnosis, og-run). The skills teach the method; these
are one country's numbers, kept here so the skills stay general. They record what was true when
written; check the country repo before relying on any of them. Do not copy them into another
country's calibration.

Most ZAF work sits on two open PRs that had not merged when this file was written (2026-10-19):
[EAPD-DRB/OG-ZAF#135](https://github.com/EAPD-DRB/OG-ZAF/pull/135) (single-industry refresh,
branch `feature/single-industry-refresh`, head 8292bbe) and
[EAPD-DRB/OG-ZAF#142](https://github.com/EAPD-DRB/OG-ZAF/pull/142) (multi-industry M=8, branch
`feature/multi-industry-calibration`, head 571376e, stacked on #135). Upstream `main` (cc357bb)
still ships the old calibration. (2026-11-25: upstream main at 9259d22, 2026-10-29, ships the
refreshed single-industry calibration; entries citing it say so.)

Contents (by the skill file each entry backs; search a file for its `###` headings)
- og-country-calibration/SKILL.md
- og-country-calibration/references/macro-open-economy.md
- og-country-calibration/references/fiscal-consistency.md
- og-country-calibration/references/taxes-informality.md
- og-country-calibration/references/calibration-pr.md
- og-multi-industry-calibration/references/inputs.md
- og-multi-industry-calibration/references/alignment.md
- og-solver-diagnosis/references/failure-taxonomy.md
- og-country-calibration/references/solving-tuning.md

## og-country-calibration/SKILL.md

### Calibrating an OG-Core country model: country tags are provenance

- **Lesson:** a country tag records where a lesson was learned, not which country it applies to.
- **What happened:** this tag is the reading rule itself; `[ZAF]` appears only as an example of a
  tag. There is no ZAF case behind it.
- **Evidence:** not applicable (no lesson to back).
- **When:** 2026-10.

## og-country-calibration/references/macro-open-economy.md

### world_int_rate_annual: say which rule you applied to a sub-investment-grade sovereign

- **Lesson:** a sub-investment-grade but not distressed sovereign sits between the "risk-free plus
  spread" and "leave it at the benchmark" rules; check the sign of `K_f` after setting the rate,
  and say which rule you used.
- **What happened:** South Africa is rated BB/Ba2. ZAF used the open-economy rule: 4% risk-free
  plus the Treasury's 2.26pp sovereign premium, so `world_int_rate_annual` went 0.04 → 0.063, with
  USD bond spreads (2.2–2.6pp) and Damodaran's Ba2 spread as cross-checks. At that rate the solved
  steady state had a mildly negative foreign capital share, `K_f/K` = −4.4%, which the commit read
  as consistent with South Africa's positive net IIP. The later docs keep the rate and the reason
  but no longer report `K_f/K`.
- **Evidence:** [af9dd75](https://github.com/EAPD-DRB/OG-ZAF/commit/af9dd757d0aa26fb9b0b219d0a6ab72de7d927cb)
  (CHANGELOG at that commit gives the −4.4%);
  [macro.md at 8292bbe](https://github.com/EAPD-DRB/OG-ZAF/blob/8292bbe4b32e7630d1ddbc5a63606b5fc1962f42/docs/book/content/calibration/macro.md)
  ("World interest rate"); [OG-ZAF#135](https://github.com/EAPD-DRB/OG-ZAF/pull/135).
- **When:** 2026-07 (ogcore 0.16.3).

### g_y_annual: g_y consistent with the debt anchor

- **Lesson:** `g_y` must match the growth the `debt_ratio_ss` anchor assumes; for a stabilization
  plan built on a recovery, use that recovery's growth less `g_n`, not the stagnant realized window.
- **What happened:** the realized-window `g_y` was 0.0059 (about 0.6%). The 0.765 debt target comes
  from the 2026 Budget Review plan, which, like the IMF Article IV, assumes about 1.8% medium-term
  growth. ZAF set `g_y_annual` = 0.014 (1.8% − `g_n` ≈ 0.42%), a rise of about 0.8pp. The docs call
  the 0.6% pairing the IMF's pessimistic scenario, in which debt drifts toward 84% of GDP.
- **Evidence:** [ebbfdf7](https://github.com/EAPD-DRB/OG-ZAF/commit/ebbfdf798a5041bbc590785abafe33065ac3f3af)
  (JSON 0.005947 → 0.014);
  [macro.md at 8292bbe](https://github.com/EAPD-DRB/OG-ZAF/blob/8292bbe4b32e7630d1ddbc5a63606b5fc1962f42/docs/book/content/calibration/macro.md)
  ("Economic Assumptions"); [OG-ZAF#135](https://github.com/EAPD-DRB/OG-ZAF/pull/135).
- **When:** 2026-07 (ogcore 0.16.3).

### r_gov base wedge: effective r_gov levels (also PHL)

- **Lesson:** keep the LMWW slope but re-anchor `r_gov_shift` so the steady-state `r_gov` equals the
  country's effective real rate on its debt stock.
- **What happened:** the raw LMWW intercept (`mu_d` = 0.0338) implied a steady-state `r_gov` of about
  4.3% real. The Treasury's effective rate is 7.1% nominal (debt service ÷ gross loan debt),
  deflated by about 3.4% to about 3.7% real, so the LMWW level over-predicted by about 0.6pp. ZAF
  kept `r_gov_scale` = 0.24485, re-anchored `mu_d` to 0.0254, and folded it with the premium
  centring into `r_gov_shift` = −0.0488. The docs reject the ~5% real 10-year new-issue yield as the
  wrong (marginal) rate. Exemplar values: ZAF ~3.7%, PHL ~2.0% (see PHL.md).
- **Evidence:** [ebbfdf7](https://github.com/EAPD-DRB/OG-ZAF/commit/ebbfdf798a5041bbc590785abafe33065ac3f3af);
  [macro.md at 8292bbe](https://github.com/EAPD-DRB/OG-ZAF/blob/8292bbe4b32e7630d1ddbc5a63606b5fc1962f42/docs/book/content/calibration/macro.md)
  ("Re-anchoring the level to South Africa's data"); [OG-ZAF#135](https://github.com/EAPD-DRB/OG-ZAF/pull/135).
- **When:** 2026-07 (ogcore 0.16.3).

### Initial household wealth: household balance-sheet wealth ratios (also PHL, ETH)

- **Lesson:** cross-check the capital-side initial wealth ratio against a household balance-sheet
  ratio, which usually runs lower for emerging markets.
- **What happened:** an OG-Core documentation table of household wealth ÷ GDP lists South Africa at
  256.2% (US$1.03T ÷ US$0.401T, 2024), with Philippines 250.2% and Ethiopia 169.5%. ZAF itself has
  not calibrated initial wealth: no ZAF branch sets `initial_wealth_ratio`. Note that the table is
  not on OG-Core `master` (81f4549, checked 2026-10-19). It was added in PR #1220 (closed) and is
  carried by open PR #1250, so the skill's "OG-Core's own documentation tabulates these" is true
  only of an unmerged PR.
- **Evidence:** [PSLmodels/OG-Core#1250](https://github.com/PSLmodels/OG-Core/pull/1250)
  ([calibration.md at its head 5118f34](https://github.com/PSLmodels/OG-Core/blob/5118f343cdd1a8a02feadc16d229437f345e72e6/docs/book/content/theory/calibration.md));
  [PSLmodels/OG-Core#1220](https://github.com/PSLmodels/OG-Core/pull/1220)
  ([70eeb8f](https://github.com/PSLmodels/OG-Core/commit/70eeb8f06d9fbd6a36411d9f5fde1a667923aa1c)).
- **When:** 2026-09 (table first written); 2026-10 (PR #1250 open).

### Capital stock: a PPP stock with national-price depreciation

- **Lesson:** keep the capital stock, depreciation and investment on one price basis (current national prices); judge an implausible return by checking the capital share (resource rents, product taxes), depreciation's basis and pre- versus after-tax returns before changing the basis.
- **What happened:** OG-ZAF main targets private K/Y 2.80 from PWT 11.0 at current PPPs (3.82 total, less the government's 26.7 percent) and sets `delta_annual` to private CFC at domestic prices over that stock (0.0405). On one consistent basis the national-price ratio is 2.42 (1.77 private) and depreciation 0.064. The docs reject the national-price ratio because it implies a 15–20 percent return while the PPP ratio's 11 percent matches PWT's `irr` (12 percent); but `irr` is pre-tax, excludes resource rents and is computed on stocks at national prices, and with PWT's labour share and the SARB's CFC the national-price stock gives about 13 percent. The PPP match rested on offsetting errors.
- **Evidence:** OG-ZAF upstream/main 9259d22, `docs/book/content/calibration/firms.md` (capital stock section), `ogzaf/targets.py`; PWT 11.0; review notes 2026-11-25 (og-analysis/skill-review/zaf_exemplar.md, local).
- **When:** 2026-11-25 (review of the October 2026 calibration).

## og-country-calibration/references/fiscal-consistency.md

### Fiscal consistency: the budget must balance at the debt target (proven by TPI simulations)

- **Lesson:** `alpha_G`, `alpha_T`, actual revenue and `debt_ratio_ss` must satisfy one budget
  identity, or the transition blows up while the steady state looks fine.
- **What happened:** switching ZAF's flat PIT to a progressive form (HSV and GS both) made the
  baseline transition diverge: debt ran away with the debt-elastic premium on, while flat PIT was
  stable. Anderson (ogcore 0.16.4) and heavy damping both failed, so it was a real runaway. The
  cause: `alpha_G + alpha_T` ≈ 27% of GDP against correct revenue of ≈ 24%. Two over-collecting
  taxes had masked it: a flat PIT raising ~16% of GDP against an actual ~10%, and a spurious
  `tau_bq` = 0.2 raising 3.9% of GDP (estate duty is ~0.1%; the docs already said zero). With
  `tau_bq` = 0, `tau_c` 0.15 → 0.18, CIT adjusted to 4.5% of GDP and `alpha_G` 0.233 → 0.19, the
  full example converged and debt settled on 0.765.
- **Evidence:** [ebbfdf7](https://github.com/EAPD-DRB/OG-ZAF/commit/ebbfdf798a5041bbc590785abafe33065ac3f3af);
  [OG-ZAF#135](https://github.com/EAPD-DRB/OG-ZAF/pull/135) ("Why the fiscal reconciliation");
  [macro.md at 8292bbe](https://github.com/EAPD-DRB/OG-ZAF/blob/8292bbe4b32e7630d1ddbc5a63606b5fc1962f42/docs/book/content/calibration/macro.md)
  ("Fiscal consistency"); session notes, local file
  the author's working notes (zaf-tax-informality, unpublished).
- **When:** 2026-07 (ogcore 0.16.3 and 0.16.4).

### The budget identity: alpha_I is a placeholder on OG-ZAF main

- **Lesson:** check that `alpha_I` itself is sourced before using it in the identity.
- **What happened:** OG-ZAF ships `alpha_I` = 0.0003 (0.03% of GDP of public investment). It has
  been in the JSON since the file was first added in 2022, no doc or code gives a source, and
  neither open PR changes it. OG-Core's own default is 0.0.
- **Evidence:** [ogzaf_default_parameters.json at cc357bb](https://github.com/EAPD-DRB/OG-ZAF/blob/cc357bbb63a6d8e44aa8b2940330b55cd33bcf45/ogzaf/ogzaf_default_parameters.json)
  (`alpha_I`); first added in [a65b74f](https://github.com/EAPD-DRB/OG-ZAF/commit/a65b74f19e7df9925374c43cf29ee1d862d974ab);
  unchanged at [8292bbe](https://github.com/EAPD-DRB/OG-ZAF/commit/8292bbe4b32e7630d1ddbc5a63606b5fc1962f42)
  and [571376e](https://github.com/EAPD-DRB/OG-ZAF/commit/571376efe3149050d354a1bd6af0147aff4e1fc5).
- **When:** checked 2026-10-19 (upstream main cc357bb).

### The budget identity: frame the residual honestly

- **Lesson:** name the gap between model `G/Y` and observed spending as the consolidation the
  stable-debt steady state embeds.
- **What happened:** with `r_gov` ≈ 3.7% and `g` ≈ 1.8%, `pb*` ≈ 1.4% of GDP, so consistent primary
  spending is ~22.5% of GDP and `alpha_G` = 0.19, below actual general-government consumption of
  ~0.21. The docs describe the steady state as the sustainable, post-consolidation state the Budget
  Review is steering toward, not current policy. The steady state runs a 1.5% primary surplus,
  against 1.4% needed to stabilize and 2.3% targeted by 2028/29. The docs also note the debt is ~90%
  rand-denominated and rollable, so the stable-debt state is a modelling device, not a solvency
  claim. (The `alpha_I` identity and the consolidation-gap framing come from PHL.)
- **Evidence:** [macro.md at 8292bbe](https://github.com/EAPD-DRB/OG-ZAF/blob/8292bbe4b32e7630d1ddbc5a63606b5fc1962f42/docs/book/content/calibration/macro.md)
  ("Government expenditures", "Fiscal consistency", "Steady-state validation");
  [OG-ZAF#135](https://github.com/EAPD-DRB/OG-ZAF/pull/135).
- **When:** 2026-07.

### A hot interest-growth differential forces spending too low

- **Lesson:** if the model's `r_gov − g` exceeds the country's, `pb*` is inflated and consistent
  spending is too low; check both legs.
- **What happened:** both legs were off on ZAF. The LMWW level put `r_gov` near 4.3% against the
  actual ~3.7%, and the realized `g_y` of ~0.6% understated the ~1.8% growth the debt plan assumes.
  Re-anchoring `r_gov` and moving `g_y` to 0.014 brought `r_gov − g` to about 1.9pp. During the work,
  before that refinement, the notes record that holding debt at 0.765 needed a ~2.6% primary
  surplus; after it, `pb*` was ~1.4% and `alpha_G` could sit at 0.19.
- **Evidence:** [ebbfdf7](https://github.com/EAPD-DRB/OG-ZAF/commit/ebbfdf798a5041bbc590785abafe33065ac3f3af);
  [OG-ZAF#135](https://github.com/EAPD-DRB/OG-ZAF/pull/135) (`r_gov−g ≈ 1.9pp`); local file
  the author's working notes (zaf-tax-informality, unpublished)
  (the 2.6% figure).
- **When:** 2026-07.

## og-country-calibration/references/taxes-informality.md

### Progressive-fit recipe (GS): a documented lift of φ0 above the statutory top rate

- **Lesson:** anchor `φ0` at the statutory top marginal rate; if tuning `φ2` cannot reach
  collections, a small, documented lift of `φ0` is the fallback.
- **What happened:** ZAF's statutory top rate is 45%. The session notes record that with `φ0` =
  0.45 PIT reached about 9.7% of GDP against a 10.1% target, so `φ0` went to 0.464. The tax chapter
  says the rate was "lifted slightly so PIT hits its revenue target". The 2026-10-19 generalisation
  pass first flagged 0.464 as a possible error; the check that day found the lift is deliberate and
  documented, and the skill now names it as a fallback. Upstream `main` still ships linear taxes.
- **Evidence:** [taxes.md at 571376e](https://github.com/EAPD-DRB/OG-ZAF/blob/571376efe3149050d354a1bd6af0147aff4e1fc5/docs/book/content/calibration/taxes.md);
  [tests/test_default_parameters.py at 571376e](https://github.com/EAPD-DRB/OG-ZAF/blob/571376efe3149050d354a1bd6af0147aff4e1fc5/tests/test_default_parameters.py)
  (pins `[0.464, 1.39288, 1.5314e-08]`); local file
  the author's working notes (zaf-tax-informality, unpublished) (the 9.7%).
- **When:** 2026-07 (set); 2026-10-19 (checked).

### Progressive-fit recipe (GS): tune φ2 to collections (also PHL)

- **Lesson:** fit `φ1` to the schedule's shape and tune `φ2` in-model to the PIT/GDP collections
  target; the effective-rate and informality wedge enters through `φ2`.
- **What happened:** ZAF's GS parameters are `φ0` = 0.464, `φ1` = 1.39288 (fit to the SARS 2025/26
  schedule net of the primary rebate) and `φ2` tuned so PIT collects 10.1% of GDP, with top MTR 45%
  statutory. `φ2` was 1.434e-8 at first. After review on #135 set `income_tax_filer` = 0 for the
  bottom two income groups (8.3m above the threshold against 16.8m employed), `φ2` was re-tuned to
  1.5314e-8 so the five paying groups still raise 10.1%. The resulting ETR is ~21% at R500,000 and
  38% at R2,000,000, against 20% and 36% on the SARS schedule.
- **Evidence:** [ebbfdf7](https://github.com/EAPD-DRB/OG-ZAF/commit/ebbfdf798a5041bbc590785abafe33065ac3f3af)
  (`φ2` 1.434077e-08); [bdf0687](https://github.com/EAPD-DRB/OG-ZAF/commit/bdf0687133b6d127a73995f588c02ff011441381)
  (re-tune to 1.5314e-08); review comment on [OG-ZAF#135](https://github.com/EAPD-DRB/OG-ZAF/pull/135)
  (jdebacker, 2026-07-20); [taxes.md at 571376e](https://github.com/EAPD-DRB/OG-ZAF/blob/571376efe3149050d354a1bd6af0147aff4e1fc5/docs/book/content/calibration/taxes.md).
- **When:** 2026-07 (ogcore 0.16.3).

### Progressive-fit recipe (HSV): HSV fit, before the GS switch

- **Lesson:** for HSV, fit τ to the schedule's shape and tune λ to collections; use HSV only where
  a bottom-end subsidy is harmless.
- **What happened:** ZAF first fit HSV. The original skill text, written during that session,
  records τ ≈ 0.14 tracking the SARS 2025/26 schedule (ETR 6 → 21 → 35% across the range, MTR 18 →
  45%). HSV's mildly negative ETR below the threshold drained early-transition revenue and, with the
  debt-elastic premium, helped push the transition into a debt runaway; GS with the same targets
  converged. HSV never reached a committed OG-ZAF parameter file, so the τ value has no repo trace.
- **Evidence:** original skill text in Model-tools
  [29cbdb9](https://github.com/EAPD-DRB/Model-tools/commit/29cbdb91e40c0e8ed23a889417aed6801a0127b4)
  (og-country-calibration, "HSV recipe"); [taxes.md at 571376e](https://github.com/EAPD-DRB/OG-ZAF/blob/571376efe3149050d354a1bd6af0147aff4e1fc5/docs/book/content/calibration/taxes.md)
  (why GS over HSV); local file
  the author's working notes (zaf-tax-informality, unpublished).
- **When:** 2026-07.

## og-country-calibration/references/calibration-pr.md

### Pre-empt the gamma_g question: gamma_g is zero

- **Lesson:** if `gamma_g = 0`, say so in the PR (private = total, no carve-out) so the reviewer need
  not ask.
- **What happened:** OG-ZAF sets `gamma_g` = 0. PR #142 says so in its body, and `constants.py` keeps
  `PUBLIC_CAPITAL_SHARE = 0.0` explicit so a future nonzero value comes out of capital, not labour.
- **Evidence:** [OG-ZAF#142](https://github.com/EAPD-DRB/OG-ZAF/pull/142);
  [ogzaf/constants.py at a143ee7](https://github.com/EAPD-DRB/OG-ZAF/blob/a143ee713cf501512f7fd0c255154fee39d7cea3/ogzaf/constants.py).
- **When:** 2026-07.

## og-multi-industry-calibration/references/inputs.md

### Finding the data: make-matrix structure (also PHL)

- **Lesson:** check whether the make matrix is diagonal or rectangular (off-diagonal share, producers
  per commodity), because it decides the `io_matrix` algebra.
- **What happened:** the 2019 SASAM has a rectangular make, 61 activities × 108 commodities, so ZAF
  uses the full industry-technology make/use algebra rather than PHL's diagonal shortcut (PHL's
  off-diagonal share is exactly 0). The original skill text records that the median commodity has
  more than one producer. That median was not recomputed for this file: only the 2015 SASAM is
  local, and the 2019 file is read from `EAPD-DRB/SAM-files` at run time.
- **Evidence:** [OG-ZAF#142](https://github.com/EAPD-DRB/OG-ZAF/pull/142) ("rectangular make
  matrix (61 activities × 108 commodities)");
  [ogzaf/input_output.py at 571376e](https://github.com/EAPD-DRB/OG-ZAF/blob/571376efe3149050d354a1bd6af0147aff4e1fc5/ogzaf/input_output.py);
  Model-tools [29cbdb9](https://github.com/EAPD-DRB/Model-tools/commit/29cbdb91e40c0e8ed23a889417aed6801a0127b4)
  ("median commodity produced by >1 activity").
- **When:** 2026-07.

### Finding the data: employment survey year

- **Lesson:** take employment from a labour force survey in the same year as the SAM.
- **What happened:** ZAF uses the Stats SA QLFS, 2019 annual average (total ~16,340k employed), to
  match the 2019 SAM.
- **Evidence:** [ogzaf/input_output.py at 571376e](https://github.com/EAPD-DRB/OG-ZAF/blob/571376efe3149050d354a1bd6af0147aff4e1fc5/ogzaf/input_output.py);
  [firms.md at 571376e](https://github.com/EAPD-DRB/OG-ZAF/blob/571376efe3149050d354a1bd6af0147aff4e1fc5/docs/book/content/calibration/firms.md).
- **When:** 2026-07.

### Finding the data: SAM vintage checked against the national accounts

- **Lesson:** check the SAM's value-added shares by broad sector against the statistics office's GDP
  by industry before trusting it.
- **What happened:** ZAF's 2019 SAM matched Stats SA GDP by sector (2019) to within 0.5pp: primary
  8.2% vs 8.2%, secondary 18.6% vs 18.3%, tertiary 73.1% vs 73.6%. Services were 52.6% of household
  consumption against 51.3% measured.
- **Evidence:** [OG-ZAF#142](https://github.com/EAPD-DRB/OG-ZAF/pull/142) ("Steady state lands on
  South African data").
- **When:** 2026-07.

### Concordances: misspelled codes drop out of every sum (also PHL)

- **Lesson:** the concordance dicts must partition the data exactly, because `isin` and `groupby`
  silently skip codes they cannot match.
- **What happened:** OG-ZAF's `CONS_DICT` had two misspelled commodity codes, `colig` (for `coilg`)
  and `ccmemb` (for `cmemb`), so both commodities dropped out of every consumption sum. The
  multi-industry commit fixed them. Its `PROD_DICT` comment states the eight lists cover all 61
  activities exactly once.
- **Evidence:** [a143ee7](https://github.com/EAPD-DRB/OG-ZAF/commit/a143ee713cf501512f7fd0c255154fee39d7cea3)
  (`ogzaf/constants.py` diff); local file
  the author's working notes (multi-industry-port-plan, unpublished).
- **When:** 2026-07.

### Defining industries and goods: utility industries (also PHL, BRA)

- **Lesson:** split electricity from water when the policy question needs it, and watch what rides
  along in each split.
- **What happened:** ZAF's eight industries keep Electricity (`aelcg`) on its own and group Water
  and Waste (`awatd`, `awast`). Waste had sat in Tertiary in the old four-industry dict.
- **Evidence:** [a143ee7](https://github.com/EAPD-DRB/OG-ZAF/commit/a143ee713cf501512f7fd0c255154fee39d7cea3)
  (`PROD_DICT`); [firms.md at 571376e](https://github.com/EAPD-DRB/OG-ZAF/blob/571376efe3149050d354a1bd6af0147aff4e1fc5/docs/book/content/calibration/firms.md).
- **When:** 2026-07.

### Defining industries and goods: goods (also PHL, BRA)

- **Lesson:** goods are household-relevant groups, typically food, energy, non-durables, durables
  and services.
- **What happened:** ZAF uses I = 5: Food, Energy and extraction, Non-durables, Durables, Services,
  with `alpha_c` 0.202, 0.028, 0.164, 0.080 and 0.526.
- **Evidence:** [firms.md at 571376e](https://github.com/EAPD-DRB/OG-ZAF/blob/571376efe3149050d354a1bd6af0147aff4e1fc5/docs/book/content/calibration/firms.md)
  ("Consumption goods").
- **When:** 2026-07.

### io_matrix: traced household energy goes to electricity (also PHL)

- **Lesson:** the naive direct-use matrix puts most goods on manufacturing; tracing value added
  through the Leontief inverse sends household energy mostly to electricity.
- **What happened:** on ZAF, the energy row's electricity share rose from 12% (naive direct use) to
  45% (traced), and its manufacturing share fell from 63% to 11%. Food and durables also moved off
  manufacturing.
- **Evidence:** [OG-ZAF#142](https://github.com/EAPD-DRB/OG-ZAF/pull/142) ("New vs old
  `io_matrix`").
- **When:** 2026-07.

### Z_m: capital-output ratio from PWT (also PHL, BRA)

- **Lesson:** take the capital-output ratio for the SAM year from PWT; its level matters little
  under the normalisation.
- **What happened:** ZAF uses 2.9 (PWT 10.01, net capital stock over GDP), held in
  `CAPITAL_OUTPUT_RATIO`.
- **Evidence:** [ogzaf/constants.py at a143ee7](https://github.com/EAPD-DRB/OG-ZAF/blob/a143ee713cf501512f7fd0c255154fee39d7cea3/ogzaf/constants.py);
  [firms.md at 571376e](https://github.com/EAPD-DRB/OG-ZAF/blob/571376efe3149050d354a1bd6af0147aff4e1fc5/docs/book/content/calibration/firms.md).
- **When:** 2026-07.

## og-multi-industry-calibration/references/alignment.md

### The Z level: a common Z multiplier aligns factor

- **Lesson:** if the multi-industry `factor` misses the single-industry one, rescale the whole `Z`
  vector by a common constant found by a root-find on the solved `factor`.
- **What happened:** with Manufacturing = 1, ZAF's M=8 `factor` came out about 23% low. A common
  Hicks-neutral multiplier of 0.865, found by a log-log root-find on the solved `factor` (two or
  three solves, slope about 1.8), brought it to 124,695 against the single's 124,684. The model
  solved cold from the shared base seeds, with no continuation.
- **Evidence:** [OG-ZAF#142](https://github.com/EAPD-DRB/OG-ZAF/pull/142) (the 23% and 0.865);
  [firms.md at 571376e](https://github.com/EAPD-DRB/OG-ZAF/blob/571376efe3149050d354a1bd6af0147aff4e1fc5/docs/book/content/calibration/firms.md);
  the author's working notes (single-multi-compat-key-lessons, unpublished)
  (the slope ≈ 1.8).
- **When:** 2026-07 (ogcore 0.16.3).

## og-solver-diagnosis/references/failure-taxonomy.md

### B. Binding constraint from a calibration placeholder: upstream main still ships zeta_K 0.9 and tau_bq 0.2

- **Lesson:** grep any inherited JSON for the `zeta_K` = 0.9 placeholder (failure class B), and for
  a bequest tax set at a statutory-style rate (taxes-informality, "Standing check: the bequest
  tax"). Moved out of the skills on 2026-10-19.
- **What happened:** upstream `main` (cc357bb) ships `zeta_K` = 0.9 and `tau_bq` = 0.2, along with a
  4% world rate, a 1.2 debt target and linear taxes. The single-industry refresh changes both:
  `zeta_K` 0.9 → 0.16 (Chinn-Ito `ka_open` for South Africa, 0.1626) in af9dd75, and `tau_bq`
  0.2 → 0.0 in ebbfdf7. The branch head 8292bbe and the multi-industry branch 571376e both carry
  0.16 and 0.0. Until #135 merges, anyone running from `main` gets both placeholders. (The CHANGELOG
  at af9dd75 says "`zeta_K` 0.2 -> 0.16", a leftover from an exploration branch; the JSON diff and
  the final CHANGELOG say 0.9 → 0.16.)
- **Evidence:** [ogzaf_default_parameters.json at cc357bb](https://github.com/EAPD-DRB/OG-ZAF/blob/cc357bbb63a6d8e44aa8b2940330b55cd33bcf45/ogzaf/ogzaf_default_parameters.json);
  [af9dd75](https://github.com/EAPD-DRB/OG-ZAF/commit/af9dd757d0aa26fb9b0b219d0a6ab72de7d927cb)
  (`zeta_K`); [ebbfdf7](https://github.com/EAPD-DRB/OG-ZAF/commit/ebbfdf798a5041bbc590785abafe33065ac3f3af)
  (`tau_bq`); [OG-ZAF#135](https://github.com/EAPD-DRB/OG-ZAF/pull/135) (changed-variables table).
- **When:** checked 2026-10-19 (upstream main cc357bb; refresh branch 8292bbe).

## og-country-calibration/references/solving-tuning.md

### The calibration's working files: plan, targets, tuning script, scorecard

- **Lesson:** keep the calibration's working tools in the repo in a small, fixed form: a written moment × lever table with each lever's status (sourced, tuned, defaulted, unexamined) and the tuning order; one module listing every target with its source; a tuning script that solves the packaged parameters plus overrides and prints model against target; a fiscal-path check on the baseline transition; and a script that regenerates the docs' fit tables from the run.
- **What happened:** OG-ZAF's October 2026 calibration shipped all five, and its docs tables were the only ones in the fleet regenerated from the run (between markers), so they could not drift from it. A review on 2026-11-25 found its economics weaker than its tooling (see "Capital stock: a PPP stock with national-price depreciation"), and its generated parameter table stale because it was not rerun.
- **Evidence:** at commit 9259d22: [docs/CALIBRATION_PLAN.md](https://github.com/EAPD-DRB/OG-ZAF/blob/9259d221cf9554f518e96ad2c400bf3954ca986a/docs/CALIBRATION_PLAN.md), [ogzaf/targets.py](https://github.com/EAPD-DRB/OG-ZAF/blob/9259d221cf9554f518e96ad2c400bf3954ca986a/ogzaf/targets.py), [examples/tune_ss.py](https://github.com/EAPD-DRB/OG-ZAF/blob/9259d221cf9554f518e96ad2c400bf3954ca986a/examples/tune_ss.py), [examples/validate_fiscal_path.py](https://github.com/EAPD-DRB/OG-ZAF/blob/9259d221cf9554f518e96ad2c400bf3954ca986a/examples/validate_fiscal_path.py), [examples/calibration_scorecard.py](https://github.com/EAPD-DRB/OG-ZAF/blob/9259d221cf9554f518e96ad2c400bf3954ca986a/examples/calibration_scorecard.py).
- **When:** 2026-10 (reviewed 2026-11-25).
