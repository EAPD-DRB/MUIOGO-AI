---
name: og-country-calibration
description: >-
  Calibrates, updates or reviews an OG-Core overlapping-generations country model (OG-USA, PHL,
  ZAF, IDN, BRA, ETH or a new country). Use when setting or checking macro and open-economy
  parameters, the capital stock and capital share, the earnings matrix, demographics, preferences,
  pensions, initial wealth, taxes or informality; when porting the model to a new country or
  updating a calibration to new data; when validating a steady state or transition against country
  data; or when writing a calibration PR. Multi-industry work is og-multi-industry-calibration;
  launching runs is og-run; a failing solve is og-solver-diagnosis.
---

# Calibrating an OG-Core country model

Methods and checks learned across the OG-Core country models, for a new country or an update of an
existing one. Numbers here are examples; derive your own. Check each claim against the repo in
front of you and the installed ogcore: parameters appear, get renamed or change shape between
releases, and some lessons need features only some builds have (each says how to check).

## Running the model

Install each model with OG-Core's installer, one copy per commit, and run the repo's example script
unchanged from that copy's environment; tuning uses the repo's own tuning script, and tests run in
such a copy, after og-run's check before a run. Solver settings live in the packaged parameters:
Anderson (`TPI_outer_method = "anderson"`) with `nu` 0.2 or lower. One model job on the machine at
a time. A run outside this path cannot be reproduced or compared, so its numbers do not count. To investigate, read the saved output. Report with every
result the repo, commit, ogcore version, script and whether it ran online. Detail:
[og-run-rules.md](references/og-run-rules.md) and the og-run skill.

## How a calibration runs

The person you are working with leads: they decide what the baseline targets, which sources to
use, which method settles each parameter, and when to stop. Your part is to find the data and the
methods, propose a choice with a recommendation and its evidence, run, check, and report plainly.

1. **Targets.** The baseline is the country's normal operation in the start year (the latest year
   with data) under current, adopted policy; programs and forecasts are scenarios. Fix the GDP
   basis once (market prices, one national-accounts vintage) and use it for every ratio.
2. **Inputs, one decision at a time.** For each input, the best available data or published
   method, starting with the national institution that owns the number; log each decision with its
   source and the alternatives considered. A choice made by another model or institution is
   evidence only with its reasoning. Settle every input before tuning.
3. **Tune once.** The dials (the income-tax scale, `tau_c`, the corporate factor, `p_wealth`,
   `tau_bq`, `r_gov_shift`, `zeta_K`, patience) against their own measured moments.
4. **Validate.** The example script, steady state and transition, against the dashboard: fiscal
   rows first, then the first model years, then the long run.
5. **Document,** with every number generated from the run and the packaged JSON.
6. **Stop** when the remaining gaps are small or need a model the repo does not have; say which
   gaps remain, with their measured causes. Call diminishing returns when you see them.

Each block has rungs from minimal to ideal: use the highest the data supports and say when you take
a lower one. A documented fallback is a legitimate calibration; an undocumented placeholder is not.
An update follows the same order: start from what the repo ships, list what the new data changes,
re-settle only those inputs, then one retune.

## The mental model

1. **The packaged `og<xxx>_default_parameters.json` is the calibration.** `Calibration(p,
   update_from_api=False)` fetches nothing, but an example may call `update_from_api=True` when
   online and overwrite curated values. Read the example before trusting a hand-set value.
2. **Anything you do not set is OG-Core's default, mostly US values.** Diff the JSON against your
   ogcore's `default_parameters.json`: every key still equal to the default (`delta_annual`,
   `beta_annual`, `mean_income_data` in dollars, the US pension system, `tax_func_type`,
   `cit_rate`, `eta`, `eta_RM`, `chi_b`, `chi_n`, the `initial_guess_*` seeds, `tG1`) is unexamined
   unless documented. Read each parameter's valid range there too. [JPN]
3. **Lead the dashboard with fiscal data.** Collections by instrument, debt, the interest bill and
   the foreign-owned capital share are published precisely and check each other through the budget
   identity.
4. **Calibrate effective, not statutory, quantities:** rate = collections ÷ the model's base, for
   every instrument.
5. **One capital price basis:** the stock, investment and depreciation all private and at current
   national prices.
6. **Find every lever before tuning.** Write the model's own closed form for each target moment and
   list every parameter in it ([method.md](references/method.md)); a lever that runs out of road is
   the wrong lever, and a parameter at its bound is a signal to read economically before widening
   the bound.
7. **Single-industry first;** multi-industry is an overlay built afterwards.

## Checklist for a new country

Copy into the work log and tick off. For an update, keep the rows the new data touches.

```
- [ ] Existing work: open PRs and branches touching this block; the current gaps and their sign.
- [ ] Targets and GDP basis (market prices) agreed; fiscal path panel and dashboard planned.
- [ ] Moment x lever table from OG-Core's equations (method.md).
- [ ] Bootstrap from the closest sibling, then replace every inherited value (bootstrap.md).
- [ ] Install with the installer; note the resolved ogcore; check which optional features it has.
- [ ] Dimensions and age convention (households-demographics.md).
- [ ] Demographics: named country code + test; window to the last usable year; g_n_ss against
      the UN projection; income gradients if available.
- [ ] Earnings: country age shape and group spread, one income concept.
- [ ] Macro: start_year, debt (measured start, chosen anchor), debt abroad, world rate, g_y per
      hour, remittances and aid, r_gov to the treasury's effective real rate, centred premium,
      public capital, initial wealth, cash transfers only.
- [ ] Capital: private K/Y and delta at current national prices; capital share from the labour
      share (adjusted for self-employment), decided once; owners' return against evidence.
- [ ] Taxes: every rate effective, by instrument; a progressive income tax (GS) fitted to the
      schedule; non-tax revenue mapped. Close the budget identity:
      G/Y = (revenue + aid + net FDC)/Y − (TR + I_g + pensions + UBI)/Y − pb*, where pb* is the
      primary balance that holds debt at debt_ratio_ss. Start alpha_G from the data, solve once,
      then set it from the identity (fiscal-consistency.md).
- [ ] Pensions in local currency; hours by age (chi_n) on survey ages; transfers by age (eta).
- [ ] Preferences: sigma, a subsistence floor if relevant, Frisch, chi_b; then patience.
- [ ] Tune the dials once; validate steady state and transition, including the first-year
      cohorts (og-solver-diagnosis).
- [ ] Warm-start seed from the first converged solve; regenerate after large moves.
- [ ] Final solve of the packaged JSON with no overrides; tests; changelog; docs from the run.
```

When a check fails, go back before moving on: after a tax change re-tune `zeta_K`; after a sourced
input changes, redo the tax dials, then `zeta_K`, then patience; if the packaged JSON fails on its own, revisit
the overrides just folded in; if the transition's resource-constraint error is not small outside
the known population breaks, triage it by period (og-solver-diagnosis) before tuning.

## Reporting

Report in plain language: model against data in tables and figures, with the names the data use.
Say what is measured, what is assumed and what is a check; compute a mechanism from the saved output
before stating it. Keep internal labels (round names, "dials", "official run") out of reports.
The calibration PR is a fit report ([calibration-pr.md](references/calibration-pr.md)).

## Reference files

Read the one for the block you are working on.

| File | Read when |
|---|---|
| [method.md](references/method.md) | Before tuning: the moment × lever table, finding every lever, decomposing a gap that will not close |
| [bootstrap.md](references/bootstrap.md) | Copying a sibling repo for a new country |
| [macro-open-economy.md](references/macro-open-economy.md) | Start year, debt and debt abroad, the capital stock and its price basis, public capital, the capital share, `zeta_K`, world rate, `g_y`, `r_gov`, remittances and aid, initial wealth, patience, `alpha_T` |
| [households-demographics.md](references/households-demographics.md) | Dimensions, earnings matrix, demographics, pensions, hours by age, transfers by age, family support, preferences |
| [fiscal-consistency.md](references/fiscal-consistency.md) | The budget identity, the baseline fiscal stance and debt anchor, the closure, the fiscal path panel |
| [taxes-informality.md](references/taxes-informality.md) | Any tax rate, the corporate block, the income-tax form, informality, non-tax revenue |
| [validation-dashboard.md](references/validation-dashboard.md) | Building or scoring the dashboard, the GDP basis (market prices), reading output, numbers in docs |
| [solving-tuning.md](references/solving-tuning.md) | The tuning loop, spending runs while exploring, the environment |
| [calibration-pr.md](references/calibration-pr.md) | Writing the calibration PR |
| [provenance.md](references/provenance.md) | Tracing where an existing value came from |
| [og-run-rules.md](references/og-run-rules.md) | How to run the model |
| [lessons/INDEX.md](references/lessons/INDEX.md) | Your country has a feature another country has dealt with: the cases by situation, each with its evidence at a fixed commit |

Related skills: og-run, og-solver-diagnosis, og-multi-industry-calibration, og-scenario-report. If
one is not available, do the job directly and say which skill would have covered it.

## Lessons and their history

Lessons name the data concept, the transformation and the check. Sources and scripts they mention
are examples and helpers, not requirements: any source that measures the same concept, or any
method that passes the check, will do. Helpers worth knowing: EAPD-DRB/Population-Data (UN
population data, OG-Core's fallback), EAPD-DRB/Demographic-Gradients (fertility and mortality by
income), the National Transfer Accounts (age profiles), the Penn World Table (capital, labour
share, returns), the World Inequality Database (income shares), the IMF's fiscal and capital-stock
data, and the OECD Revenue Statistics; a country repo's own tuning and documentation scripts where
it has them.

A tag such as `[PHL]` records where a lesson was learned, not where it applies; each lesson states
its condition as a country feature (informal economy, net creditor, concessional debt). Each
country's cases, with numbers and evidence, are in `references/lessons/<CODE>.md`; start from the
index by situation. When your country teaches something new, add it as `docs/og-skills-maintenance.md`
in Model-tools describes.

## The traps that cost the most

- **The budget does not balance at the debt target:** the transition runs away while the steady
  state looks fine (fiscal-consistency.md).
- **Statutory rates in effective slots:** `tau_bq`, payroll on top of the income-tax function
  (taxes-informality.md).
- **Capital on mixed price bases:** a PPP stock with national-price depreciation and investment, or
  total capital against the model's private `K` (macro-open-economy.md).
- **Tuning before the inputs are settled:** every later correction costs a retune.
- **Patience judged on the steady state where the population is far from stationary, or pushed past
  the long-run return bound:** with measured starting wealth its effect shows in the first years
  (macro-open-economy.md).
- **The wrong consumption series or GDP basis:** with a subsistence floor score `C_i`, on market
  prices, and check that the expenditure shares add up (validation-dashboard.md).
- **Placeholder `zeta_K`, or `zeta_K` used to close an investment gap:** tune it to the measured
  foreign-owned share.
- **Wrong `initial_debt_ratio`:** invisible in the steady state, obvious in the first year.
- **Transfer shares fixed while the population ages:** the oldest are overpaid many times over;
  check transfers per person by age along the transition.
- **An old-age hours target extrapolated with an income profile:** the fall in pay counted twice;
  fit the survey ages.
- **A cross-country table value used out of sample:** check whether it is an estimate or a formula.
- **A consumption spike in the first years:** rule out unsolved first-year cohorts
  (og-solver-diagnosis) before blaming the initial wealth.
- **Short demographic window:** it sets long-run population growth silently.
- **Live data overwriting a curated value:** take curated parameters off the live path.
- **Remittances or aid left out where they matter:** a spurious trade surplus and a fiscal squeeze.
