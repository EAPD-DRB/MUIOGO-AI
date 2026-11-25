# Households and demographics

Contents
- Model dimensions and the age convention
- Earnings across ages and income groups (the e matrix)
- Demographics: the country code and the data source
- The data window sets long-run population growth
- The two population breaks and the run's tolerance
- Income gradients in fertility and mortality
- Pensions
- Hours of work by age (chi_n)
- Transfers by age along the transition (eta, eta_RM)
- Family support and consumption by age
- Preferences: sigma, the subsistence floor, Frisch, bequests
- Values from cross-country tables

Each lesson gives the rule, when it applies, the check, why, and where it was learned (`[CODE]`;
the case is in `lessons/<CODE>.md`). Confirm parameter names, defaults and valid ranges in your
ogcore's `default_parameters.json`.

## Model dimensions and the age convention

**Rule.** Keep OG-Core's dimensions (`starting_age` 20, `ending_age` 100, `S` 80 one-year
periods, `J` 7 groups with shares `lambdas`, `T` 320) unless there is a reason; changing
`starting_age` or `S` re-derives every age-indexed input (`e`, `chi_n`, `eta`, tax-function ages,
retirement). With one-year periods, model row `s` is completed age `starting_age + s`, and every
by-age target (hours, earnings, consumption, wealth) uses that convention. Legal ages map the same
way: OG-Core pays pensions from row `round((R − starting_age)·S/80) − 1`, completed age `R − 1`.

**Check.** The by-age targets are aligned on the same ages; `J` and `lambdas` match the earnings
data's groups; a legal age entered as a parameter gives the intended row.

**Why.** A target labelled one year off shifted every by-age fit. [ETH]

## Earnings across ages and income groups (the e matrix)

**Rule.** Give `e` the country's own age shape and the country's own spread across groups,
measured on the same income concept as the reference you start from. Three rungs, best first:
1. Age shape from the National Transfer Accounts' labour income by age, country against the
   reference country, same variable and type, normalised over ages 20 to 64, the ratio capped where
   both near zero; group spread from income shares by group (for example the World Inequality
   Database's pre-tax shares). The NTA data come through a web form, not an API; the ETH and
   JPN cases show working fetches. [ETH, KOR, JPN]
2. The reference matrix with one exponential tilt, `e·exp(a·e)`, with `a` solved so the tilted
   matrix's Gini relative to the reference matrix's equals the country's Gini relative to the
   reference country's, on one income concept. Several country repos implement it (as
   `get_e_interp`, with a US anchor of 41.5, World Bank income concept). It leaves the reference country's age profile in place. [PHL, IDN, BRA]
3. The reference matrix unchanged, said plainly.

**Check.**
- The country Gini is on the same welfare concept as the US anchor: a consumption Gini against an
  income Gini understates inequality. [ETH]
- Where hours are calibrated, the age shape is earnings per hour: divide labour income per person
  by hours per person by age before taking the ratio, or hours count twice, in `e` and in `n`.
- `factor` is solved in the steady state, not set.

## Demographics: the country code and the data source

**Rule.** Demographics come from `ogcore.demographics` (UN fertility, mortality and the
immigration residual); the one country input is the UN M49 code. Keep it in one named constant
used at every call site, and test that the constant equals the country's code.

**Check.**
- A test asserts the literal code ("231", "608"), not only that the call uses the constant. [ETH]
- Without UN API access (a token; how to supply one: og-run), ogcore falls back to a helper archive of UN population data,
  EAPD-DRB/Population-Data, which covers a set list of countries: for a new country, check it is
  there, or runs without a token fail with an error that names the country code, not the cause.
- Cache the processed arrays: ogcore refetches the series on every call, which is slow and makes
  the endpoint fail intermittently.

**Why.** Files copied from a sibling kept the sibling's code twice in one repo. [ETH]

## The data window sets long-run population growth

**Rule.** `get_pop_objs` holds fertility, mortality and immigration at `final_data_year` forever.
Run the window to the last usable year of the projection, not two years past the start.

**Check.**
- The model's `g_n_ss` against the growth rate the UN projection itself implies; a value well
  outside it is a short window, not a demographic fact.
- The last usable year is one before the last year of data you have (immigration is inferred from
  the year after), and the fallback archive can end earlier than the API. Put the year in a named
  constant with that reason; too late a year fails with an error far from the cause (in the
  builds seen, an `UnboundLocalError` in ogcore's `pop_rebin`).

**Why.** The long-run growth rate decides `pb*`, saving and the whole steady state; on an ageing
country a two-year window more than doubled the long-run population decline. [JPN, KOR]

## The two population breaks and the run's tolerance

**Rule.** Expect two bookkeeping breaks in the transition's population: where the rates freeze
(the last data year), and at `fixper = int(1.5·S)`, where ogcore swaps in the stationary
population in one period. They show as resource-constraint errors in those periods. Check whether
your ogcore phases the population into the stationary one (`get_pop_objs`' signature and the
code around `fixper`); if not, keep the breaks out of the tuning and report them (a local phase-in
removed most of the error). [KOR]

**Check.**
- The stored rates reproduce the stored population,
  `omega[t+1, s+1](1 + g_n[t]) = omega[t, s](1 − rho[t, s]) + imm_rates[t, s+1]·omega[t, s+1]`, to
  about 1e-15 except at the break periods.
- A loosened `RC_TPI` (OG-Core's default is 1e-4) comes with a table: the error at each break, at
  the last period, the largest elsewhere and in the first ten years. Re-tabulate after any
  calibration change; the break moves with the calibration.

**Why.** A sibling's JSON carried a tolerance a hundred times the default with no record of why; the
table separates bookkeeping from a real failure. [PHL, KOR, JPN]

## Income gradients in fertility and mortality

**Applies when** your ogcore's `get_pop_objs` accepts `income_percentiles`, `fert_gradient`,
`mort_gradient` and `infmort_gradient` (check the signature).

**Rule.** Enter measured gradients across income percentiles (fertility by age, adult mortality,
infant mortality) in the units your ogcore expects, with the model's own `lambdas` as the
percentiles. A helper library provides them:
[EAPD-DRB/Demographic-Gradients](https://github.com/EAPD-DRB/Demographic-Gradients), whose
`AGENTS.md` maps each ogcore input to a file, states the unit conversions and lists the traps.

**Check.** The country is inside the library's coverage and its general gradient's stated income
range (high-income countries are out of scope: leave them unset and say so); the conversions the
library states are applied (a missed one is a silent 100-fold error); fertility is entered by age,
so the timing gap between rich and poor survives.

**Why.** The library is the single maintained source of these rules; a copy here would drift. [JPN]

## Pensions

**Rule.** Choose the pension system the country has, from the choices your ogcore's
`pension_system` accepts (US-style Social Security, the default; Defined Benefits; Notional Defined
Contribution; Points System; hybrids of defined benefits with notional or funded defined
contributions), and set it in local currency: `mean_income_data` is the country's mean income in
its currency, `avg_earn_num_years` the country's averaging rule, `alpha_db` the accrual rate for a
defined-benefit scheme (OG-Core's default is 0, which pays nothing).

**Check.**
- Validate outlays against public pension spending as a share of GDP, not against the replacement
  rate you entered. Old-age replacement rates leave out survivors' and disability pensions, which
  the single pension block pays too; `alpha_db` is sensitive to the productivity growth behind the
  earnings averaging. [JPN]
- A maturing scheme: the steady state is a mature system, so score steady-state outlays against the
  scheme's long-run actuarial projection and the first year against today's spending. If the first
  year is well above today's, phase `alpha_db` in as a path rather than cutting the mature value,
  then re-fit any `alpha_G` path. [KOR, THA]
- In a high-denomination currency, `factor` runs to millions: state `mean_income_data` in thousands
  or millions so the factor seed stays inside its validator (at most 500,000), and rescale the
  income-tax scale to match (taxes-informality.md). A seed exactly at the cap was clipped.
  [KOR, IDN, ETH]
- Pension outlays enter the budget identity (fiscal-consistency.md).

**Why.** Left at the default, the model applies the US benefit formula to US-dollar earnings; a
pension result from an uncalibrated port is arithmetic, not evidence.

## Hours of work by age (chi_n)

**Rule.** Fit `chi_n` so the model's hours per person by age follow the labour force survey
(employment rate × hours of the employed; the model has no participation margin): rescale each
age's `chi_n` by the ratio of marginal disutility at the model's and the target's hours, re-solve,
repeat, warm-starting each solve from the last. Inside an open top age band, take the decline with
age from a household survey's own age bands, anchored to the labour force survey's level; never
from an income profile. Ages where `chi_n` reaches OG-Core's bound (10,000) cannot reach the target:
leave them out of the fit and report the gap. [PHL, ETH]

**Check.**
- The age profile, not only the total: a right total can hide a model that works as much at 75 as
  the data do at 50. [PHL, JPN]
- How steeply `chi_n` rises from prime age. OG-Core's packaged default rises about fourfold to the
  oldest age; US-fitted values approach the bound only past 90, where hours are near zero. The bound
  at ages where the survey still shows substantial hours means something is missing; read it before
  scaling anything.
- If `chi_n` hits the bound at most ages, check units first. Scaling the earnings matrix by a
  constant `k` is an exact normalisation only if every level parameter in model units scales with
  it: `chi_n` by `k^(1−sigma)`, `c_min` and the wealth-tax level parameters by `k`. Scaling
  productivity `Z` is not neutral, since OG-Core's capital demand at the world rate uses a wage
  computed without public capital, and `Z` is capped. Confirm with one steady state that ratios are
  unchanged. [ETH]
- In a multi-industry model `chi_n` and `chi_b` also take the units conversion
  (og-multi-industry-calibration).

**Why.** An old-age target extrapolated with labour income per person already contains the fall in
pay that `e` applies again, so it asks for too few hours; with a low Frisch elasticity and a
subsistence floor, the poorest households work more as pay falls, and `chi_n` runs to the bound.
Workarounds chained on top (an end to working life, special support, a raised cap) each broke the
steady state or the transition. Test an idea on one household's lifetime solve from saved prices,
and on the transition, before calling it done; if a second workaround is needed on top of the first,
stop and re-diagnose from the saved output (og-solver-diagnosis). A workaround that converges is not
therefore right. [ETH]

## Transfers by age along the transition (eta, eta_RM)

**Rule.** `eta` shares government transfers, and `eta_RM` remittances, across age and income
cells; households receive `eta·TR/omega`. OG-Core's defaults are US population age shares times
`lambdas`, not the country's: replace them from program rules or survey evidence where it exists,
or at least rebuild them from the country's own population, and say which.

**Check.** Transfers per person by age and group in the first years and a few decades into the
transition, not only the aggregate. With `eta` fixed, transfers per person move inversely with each
cell's population share: where today's population is younger than the one `eta` was built for, the
old are overpaid in the early decades. If your ogcore accepts `eta` by year (its `number_dims` in
`default_parameters.json` is 3), build it from each year's population. The
same holds for family transfers, also divided by the population.

**Why.** A fixed share overpaid the oldest by five to over a hundred times in the early decades.
[ETH]

## Family support and consumption by age

**Applies when** many older people or young adults live on support from relatives. Check whether
your ogcore has net family transfers (`hasattr(Specifications(), "phi_FT")`); without them, report
the consumption-by-age gap rather than forcing another parameter.

**Rule.** Fit `phi_FT` by age and group so that consumption per adult by age follows a target,
netting to zero within each group. The target concept: OG-Core's households start at
`starting_age` and have no children, so each adult carries the consumption of the children they
support, not only their own (the National Transfer Accounts' own-consumption profile hands young
adults transfers that go to their children). Where no survey links children to parents, build the
target from a cross-country model of the NTA profiles (consumption by age predicted from log GDP
per head at PPP and the old-age dependency ratio), with children's consumption assigned to parents
by fertility by age and spousal age gaps. Where a survey exists, use it, with the cross-country
default as a check. The ETH case cites one build.

**Check.** The target averages one over the base ages (for example 30 to 49); transfers sum to
zero within each group every year; consumption by age against the target, reported as a fit by
construction that treats every difference from the target as family support. [ETH]

## Preferences: sigma, the subsistence floor, Frisch, bequests

**Rule.**
- `sigma` near OG-Core's default (1.5; valid 1 to 2), inside the published range for the
  intertemporal elasticity (Havranek 2015).
- Where subsistence consumption is common, represent it with the floor `c_min` rather than a high
  `sigma` for everyone: only consumption above the floor enters utility, so the effective curvature
  is `sigma / (1 − c_min/c)`, high for the poor and near `sigma` for the rich. Source the floor (for
  example the cost of an energy-sufficient diet) as a share of consumption per person, in model
  units, capped at what the poorest group can afford at its lowest-consumption age. It rises with
  productivity (growth-adjusted units).
- Frisch from bias-corrected micro evidence (about 0.25 for total hours: Elminejad, Havranek,
  Horvath and Irsova 2023), within OG-Core's valid range (0.2 to 0.62); a lower estimate (0.15 to
  0.16 in a low-income setting, Goldberg 2016) cannot be entered, so record the evidence and the
  value used.
- `chi_b`, the bequest weight: OG-Core's packaged default is 80 for every group, not a calibrated
  value. Check old households' wealth by group against surveys (validation-dashboard.md); a weight
  that makes the poorest group hoard wealth into old age can break a reform's transition.

**Check.**
- Patience inside its valid range (if a long-run return bound binds, the saving gap is reported:
  macro-open-economy.md); the poorest group above the floor at every age and in the first years;
  the effective curvature by group reported.
- A sourced preference is not a tuning lever: if fitting hours or saving needs Frisch or `sigma`
  moved, something else is missing.
- Saving motives against a household survey's credit and savings modules: where saving is mostly
  precautionary, patience stands in for a motive the model lacks; say so.

**Why.** A high `sigma` for everyone with fast productivity growth made richer households borrow
against future income and pinned patience at its bound; the floor fixed it. When the poorest
group's transition failed at old ages, its wealth and transfers by age showed a bequest weight that
made it hoard. [ETH]

## Values from cross-country tables

**Rule.** Before using a country's value from a cross-country table, check whether it is a direct
estimate for that country or a formula applied to it, and whether the country is inside the sample
the formula was fitted on. An outlier against comparable countries is a question, not a finding.
Use the model's existing levers before drafting an OG-Core change to widen a bound.

**Check.** The table's notes or method section; the value against the same table's neighbours.

**Why.** A "country estimate" of the intertemporal elasticity that implied `sigma` above 19 was a
fitted formula applied out of sample; it cost days and an OG-Core change that was then dropped.
[ETH]
