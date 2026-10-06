# Households and demographics

Contents
- Earnings (the e ability matrix)
- Demographics: method and country_id
- The data window sets the long-run growth rate
- Discontinuities: the frozen window and fixper
- Cache the processed arrays
- Income-differentiated demographics
- Pensions
- Labour supply (chi_n)

## Earnings (the e ability matrix)

- **Method [family: PHL/IDN/BRA/ETH].** Reuse OG-USA's calibrated `e` matrix as the base and apply
  a single-scalar exponential tilt `e_country = e_USA · exp(a·e_USA)`, solving the one scalar `a` by
  bisection so the model Gini matches the country's target Gini. One number per country, no bespoke
  data collection. It is solved in `income.py`'s `get_e_interp(gini_to_match=...)`.
- **The method has two halves and the repos ship one.** EAPD-DRB/OG-ZAF#18 specifies (1) an
  age-shape adjustment from NTA income by age and (2) the Gini tilt. Shipping only the tilt leaves the
  US age profile in place, which is wrong wherever the country's age-earnings shape differs
  structurally (seniority pay, mandatory retirement, informality). Japan's factor is 1.09 at 55 and
  0.62 at 65; peak earnings age moves 61 → 57. **[net-new: JPN]**
  - NTA has no API. Establish a session, POST the query to `/web/nta/download-confirm`, then POST
    the session-scoped download form it returns with a `Referer` header (403 without one). The US is
    `"US"`, not `"United States"`.
  - Both countries must come from NTA on the same variable and variable type; national wage surveys
    are not comparable to NTA levels. Normalise each profile over prime working ages before taking
    the ratio, and cap it at high ages where both approach zero.
- **Do not use the ZAF-style hard-coded-coefficient method** (`get_e_orig`, a WID-then-NTA two-step
  with hand-tuned arctan extrapolation). It needs per-country re-derivation and is not a drop-in.
- **Gini-concept trap [issue #33; family-wide risk].** The target-country Gini and the US reference
  Gini (`gini_usa_data`) must be the same welfare concept. Mixing a World Bank PIP Gini
  (consumption-based for many developing countries) with the World Bank income-concept US anchor
  (`gini_usa_data = 41.5`, WB SI.POV.GINI) systematically understates the target's inequality. Use a
  matching concept for both (e.g. WID income) and check the docstring default matches the code.
- `lambdas` (lifetime-income groups, J=7) are byte-identical across the country ports
  (PHL/ZAF/IDN/BRA/ETH) and never re-derived; only the tilt `a` changes. OG-USA is the J=10 source
  the ports interpolate down from. `factor` is solved endogenously in the steady state, not a
  calibration input.

## Demographics: method and country_id

- **Method [family].** The shared `ogcore.demographics` module: fertility and mortality from the UN
  Population Division API, infant mortality from the UN age-0 mortality rate (same UN WPP series),
  and immigration solved as the residual that reconciles consecutive UN population distributions
  (appropriate when immigration data is weak).
- The only per-country input is `country_id` (UN M49 code). Use a single named constant
  (`UN_COUNTRY_CODE`) referenced at both call sites, not an inline literal. **[safer: PHL/IDN/BRA]**
- **Pitfall [ETH, regressed twice].** `calibrate.py` gets refreshed by copying a sibling, and the
  hard-coded `country_id` literal was wrong (710 = South Africa instead of 231 = Ethiopia), twice,
  because a wholesale file copy forgot to swap it. Add a regression test asserting `country_id`
  matches the country being calibrated.

## The data window sets the long-run growth rate

`get_pop_objs` holds fertility, mortality and immigration constant at `final_data_year`. Every repo
passed `start_year + 1` when this was written, so the model saw two years of UN data and then frozen
rates forever (ogcore's own default, `start_year + 2`, is barely better). Where projected demographic
change is the point of the exercise, this decides the answer. On Japan, widening from 2 to 74 years
moved `g_n_ss` from −1.070%/yr to −0.463% and `pb*` from a surplus to a deficit.

**The check:** compare the model's `g_n_ss` with the UN projection's own implied CAGR. A value well
outside it is a too-short window, not a demographic fact. Use the terminal UN rates: the steady
state is a long-run object, so a mid-transition snapshot is a category error. UN WPP ends at 2100,
and ogcore asserts against going beyond `start_year + 74` (and a 2099 cap).
**[net-new: JPN; worth a fleet sweep]**

## Discontinuities: the frozen window and fixper

A finite window leaves a discontinuity, and ogcore adds a second. Where the rates freeze, and again
at `fixper = int(1.5 * S)` (period 120 for S=80), where ogcore replaces the population distribution
with its fixed steady-state one in a single period, the transition's resource constraint breaches.
On JPN, 318 of 320 periods satisfied `RC_TPI` with a median residual of 7.96e-08; the two that failed
were exactly those periods. `fixper` is invariant to any country-side setting; report it upstream
rather than tuning around it. **[net-new: JPN]**

## Cache the processed arrays

ogcore refetches the whole UN series on every call and never reads its own `download_path` back. At
a wide window that is ~100s per solve, and hammering the endpoint makes it fail intermittently.
ogcore then falls back to the offline mirror and the run can die with `KeyError: '<country_id>'`,
naming the wrong cause. **[net-new: JPN]** (Recent ogcore also reads a UN API token from
`un_token`, `UN_API_TOKEN` or a per-user file, managed with `og-token`; a missing or expired token
is another route to the archive fallback.)

## Income-differentiated demographics

Recent ogcore's `get_pop_objs()` accepts `income_percentiles` (pass the model's own `lambdas`; it is
not data) plus `fert_gradient`, `mort_gradient` and `infmort_gradient`: fertility and mortality
tilted across lifetime-income groups instead of identical across J. Check the signature of your
resolved `get_pop_objs` before relying on it.

- **The measured gradients live in
  [EAPD-DRB/Demographic-Gradients](https://github.com/EAPD-DRB/Demographic-Gradients):** DHS fertility
  (TFR) and infant-mortality (IMR) tilts for ~78 countries, census household-deaths adult-mortality
  tilts for 14, and a GNI-keyed general fallback for everyone else. It plays the role for demographic
  differentials that Population-Data plays for levels; reference data by raw URL.
- **Before using it, fetch and follow its AGENTS.md**
  (`https://raw.githubusercontent.com/EAPD-DRB/Demographic-Gradients/main/AGENTS.md`). It maps each
  ogcore input to a file, states precedence, and lists the traps. It is the source of truth; do not
  work from a copy of its rules.
- **Check the country is in the library first.** It covers 78 developing countries, and its AGENTS.md
  says the income-based fallback is valid only between $200 and $10,000 GNI per head; high-income
  countries are out of scope, not missing. Extrapolating can reverse the sign: in high-income
  countries the fertility gradient often runs through marriage rates rather than family size. Leave
  them unset, say so, and pin the decision in a test so it is not later "fixed". **[net-new: JPN]**
- Two rules that change results: **divide the library's tilt by 100** (it is per unit wealth rank;
  ogcore wants per centered percentile point, so getting this wrong is a silent 100× error), and **a
  country's own measurement beats the general gradient**. State which route was taken and the survey
  or census year.

## Pensions

OG-Core supports `"US-Style Social Security"` (the default), `"Defined Benefits"`,
`"Notional Defined Contribution"` and `"Points System"`.

- **Leaving the default applies the US benefit formula in US dollars** (AIME bend points, PIA
  rates) to earnings scaled by `mean_income_data`, itself a US figure. A pension result from an
  uncalibrated port is arithmetic, not validation.
- **`alpha_db` defaults to 0.0.** Switching to `"Defined Benefits"` without setting it pays zero
  pensions.
- For a DB system `yr_contrib × alpha_db` is the gross replacement rate, so the parameter is directly
  observable. But OECD replacement rates are old-age only, while pension spending also funds
  survivors' and disability pensions that OG-Core's single block cannot separate. Expect to carry
  about `OECD rate × (1 + survivors & disability share)`, about 15% more for Japan.
- `alpha_db` is sensitive to assumed productivity growth, since OG-Core averages the last
  `avg_earn_num_years` of earnings. Check the growth the OECD's own pension modelling assumes
  (1.25%/yr) against yours.
- Set `mean_income_data` in local currency, and `avg_earn_num_years` to the country's convention
  (career average vs final salary).
- `replacement_rate_adjust` applied only to US-style Social Security in older ogcore; recent ogcore
  applies it to all four systems. Check before relying on it outside the US system. The pension
  code is newer and less tested than the core model, so look at OG-Core's open issues before leaning
  on pension results.
- Pension outlays belong in the fiscal identity (fiscal-consistency.md).

Validate against public pension expenditure as a share of GDP, not against the replacement rate you
fed in. **[net-new: JPN]**

## Labour supply (chi_n)

- **Honest default state [family].** `chi_n` (the 80-age disutility-of-labour profile) is
  byte-identical to OG-USA's values in every country repo, never recalibrated to a country's own
  labour data. The estimation machinery is broken or absent everywhere (USA's is commented out; most
  repos have no `labor.py`; ETH's `labor.py` is orphaned ZAF QLFS code with a missing
  `estimate_chi_n` module).
- So treat "chi_n borrowed from OG-USA, uncalibrated" as the default state of any port and say so;
  never present it as calibrated.
- **Before assuming the borrow is harmless, compare total labour input per working-age person with
  the US** (hours per worker × employment rate). Japan is within 1% (10.5% fewer hours offset by a
  much higher employment rate), which makes the borrow defensible rather than merely conventional. A
  country far off that ratio has a real problem. **[net-new: JPN]**
- To calibrate it: either (a) a single-scalar re-tilt like the earnings Gini trick, matching an
  aggregate hours or participation target; or (b) wire the labour force survey through a rewritten
  `labor.py` and a real `estimate_chi_n.py`.
- In a multi-industry model, `chi_n`/`chi_b` also take the units conversion (og-multi-industry-calibration).
