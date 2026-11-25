# Validation dashboard

The near-term fiscal path panel is in fiscal-consistency.md; build it together with this one.

Contents
- What the dashboard is for
- Every tuned dial has its own scored moment
- Rows to include
- One GDP basis: market prices
- Reading the model side
- The expenditure identity and the current account
- Steady state or early transition: say which
- Traps when adding rows
- Where the data come from
- Paths: both tails
- Keeping numbers in docs true to the run

Lessons give the rule, the check and why where they apply, and where each was learned (`[CODE]`;
the case is in `lessons/<CODE>.md`).

## What the dashboard is for

A table, model against data, each row with its source and its tier, built from the solved output by
code. Most parameters are only weakly identified on their own; the test is whether the economy
they jointly produce resembles the country. Tiers: fiscal rows first (collections by instrument,
debt, the interest bill), then the foreign-owned capital share, then production, saving and
earnings rows; rows the model is not built to match go in a last tier with a written reason.

## Every tuned dial has its own scored moment

**Rule.** Each tuned parameter is steered by one moment that is on the dashboard; totals and
residuals are checks.

**Check.** List the tuned dials and the dashboard rows; every dial maps to a row, and two dials share
a row only where the moment × lever table (method.md) says so. A dial moved to close total revenue,
or any residual, absorbs every other line's error.

**Why.** A dial with no scored moment drifts: `zeta_K` sat at a placeholder through fourteen tuning
rounds because the foreign-owned share was not a row. [JPN]

## Rows to include

| Row | What it identifies or checks | Data |
|---|---|---|
| Revenue by instrument / GDP | each tax dial | revenue statistics by instrument |
| `r_gov × D` / GDP | the government rate | interest paid, on the same debt concept |
| `K_f/K` | `zeta_K` | investment position, gross or net as decided (macro-open-economy.md) |
| Private `K/Y` | the capital block | capital stock, private, at national prices |
| `(I_total + I_g)`/GDP | `delta`, `alpha_I`, saving | gross fixed capital formation, private plus public |
| Private consumption, `G`, `NX` / GDP | checks on the identity | expenditure accounts |
| Solved `G/Y` against `alpha_G` | the budget identity | measured government consumption |
| Owners' return on capital, `r + (1 − tau_b)·MPK_g·K_g/K` | patience bound | return evidence (macro-open-economy.md) |
| Labour share `wL`/GDP | `gamma` | labour share, on the same GDP basis |
| Wealth by age and group | `chi_b`, initial wealth | household wealth surveys |
| Hours and consumption by age | `chi_n`, family transfers (where the model has them) | labour force and household surveys |
| `g_n_ss` | the demographic window | the UN projection's implied growth |

Input checks, not moments: first-year debt (`initial_debt_ratio`); first-year foreign share of debt
and its steady-state share (`zeta_D` by construction); `G/Y` before `tG1`, `TR/Y` and `RM/Y`, which
equal their input shares up to the GDP basis. `factor` sets the currency income at which taxes
are evaluated, so a wrong `mean_income_data` shows in the revenue rows.

**Wealth by age.** `chi_b` moves the old end of the profile, and also `K/Y` and bequest revenue:
re-tune patience and `tau_bq` with it. Where the young end falls short because young households
hold leveraged housing, which OG-Core does not model, document it. [KOR]

## One GDP basis: market prices

**Rule.** Compare model and data on GDP at market prices, on one national-accounts vintage. OG-Core's
`Y` is output at producer prices, and the model puts every tax on products on consumption. So:

```
GDP at market prices        = Y + cons_tax_revenue
private consumption, market = Σ_i p_i·C_i + cons_tax_revenue      (one good: C_i + cons_tax_revenue)
any other ratio to GDP      = x / (Y + cons_tax_revenue)
```

Convert every input OG-Core takes as a share of its own `Y` (`alpha_G`, `alpha_T`, `alpha_I`,
`alpha_FA`, debt ratios, remittances, `initial_wealth_ratio`, family transfers where present) with
the data's factor, market-price GDP over the model's `Y` concept (`1 / (1 − product-tax share)`, with
the product-tax share as your revenue mapping defines it), and check the solved
`(Y + cons_tax_revenue)/Y` against it. The capital share is a share of the model's `Y`: a labour
share measured over market-price GDP converts the same way. Shares of `K` or `D` (`K_f/K`, `zeta_D`)
and rates do not convert. Ratios of stocks to GDP (private `K/Y`, wealth) follow the same rule; the
closed forms in method.md are written on the model's `Y`, so convert when you use them.

**Check.** The conversion factor is reported and agrees with the data's; after a national-accounts
rebasing every stock and flow is on the new basis (or on the old one and converted at the end),
never mixed.

**Why.** With a consumption tax near 8% of GDP every ratio to `Y` sat about 8% off, and comparing
tax-inclusive data consumption with producer-price model consumption moved the gap into net
exports. A rebasing moves every ratio with nothing real changing; mixing bases put a capital ratio
25% too high. [PHL, THA, ETH]

## Reading the model side

Read `SS_vars.pkl` and `TPI_vars.pkl` with `ogcore.utils.safe_read_pickle` from the run's own
output. Revenue totals: `iit_revenue`, `payroll_tax_revenue`, `business_tax_revenue`,
`cons_tax_revenue`, `wealth_tax_revenue`, `bequest_tax_revenue`, `total_tax_revenue`. Private
investment is `I_total` (all private capital, foreign-financed included; not `I`, which adjusts for
immigrants' capital); public is `I_g`. Consumption is `C_i`: with a subsistence floor, OG-Core's
`C` is consumption above the floor and leaves it out.

**Check.** Some keys are per-household arrays, `(S, J)` in the steady state: `wealth_tax`,
`bequest_tax`, `c`, `n`, `b_s`. Aggregate them with `omega_SS` (`omega` by year on the transition),
which already includes `lambdas`, and sanity-check every new row's magnitude before believing a gap;
summing a per-household array once gave a number "of GDP" with no meaning.

**Why.** Reading `C` with a subsistence floor understated consumption and overstated net exports
by about 6.5 points of GDP, and the false trade surplus sent the diagnosis toward foreign financing
for a week. [ETH]

## The expenditure identity and the current account

**Rule.** OG-Core has no consumption parameter and no trade sector: consumption and net exports
are what is left of output. Decompose a consumption gap into the other components' gaps before
looking for its cause.

**Check.** Every solve:
- `resource_constraint_error` is small; net exports computed from the resource constraint (net
  capital outflows less foreign-financed investment, remittances and aid) match `Y` less
  consumption, investment and `G`;
- on the data side, the expenditure shares add to one on the dashboard's definitions; where the
  data's government consumption counts depreciation of public capital, say so next to the table;
- the current account two ways, from flows (net exports plus remittances and aid less payments
  abroad) and from the change in foreign-owned capital and external debt; a mismatch is a misread
  series. [ETH, JPN]

**Why.** Two gaps that move together are one gap: a capital shortfall shows up as both too little
investment and too much consumption. [JPN]

## Steady state or early transition: say which

**Rule.** Score the first-tier rows in the first years of the baseline transition as well as in
the steady state, and label each row with which it scores. Today's economy is the early
transition; the steady state uses the end of every path.

**Check.** Rows that depend on population growth (investment above all) are read in the early
transition for a country mid-way through its demographic change. With `r` above growth, a net
creditor's steady state cannot run a trade surplus: compare only the sign of steady-state `NX` with
the sign of `K_f`, and score `NX` in the early years. [JPN, KOR]

**Why.** A steady state can land close while the first years miss badly (a mis-set initial
wealth), and a steady-state miss can be right for a country still in transition.

## Traps when adding rows

- **Trade balance, not current account.** `NX` is the trade balance; for a country with a large
  investment position most of the current account is primary income. [JPN]
- **The model's own concepts.** `K` is private capital; `I_total` is private investment; national
  `G` may include public depreciation. Match the data to the concept, not the label. [KOR]
- **Pair the debt and interest concepts.** Gross debt with interest on gross debt, net with net:
  `r_gov × D` reproduces the interest bill; the effective rate is interest paid over debt,
  deflated. [JPN]
- **Audit each instrument's base, not only its yield.** A right total can sit on a wrong rate
  times a wrong base, which gives the wrong reform response; size reforms by the revenue they must
  raise where the base is uncertain. [JPN]
- **A gap called a "family trait".** Before calling a gap structural, run method.md's lever rules
  and check the GDP basis (market prices): one capital-output "trait" was an untuned `zeta_K`, and part of
  another was producer-price `Y`. A gap that survives both is reported with its reason, not chased
  by distorting a sourced parameter. [JPN, PHL]

## Where the data come from

**Rule.** For each row, start with the national institution that owns the number (revenue
service, treasury or debt office, statistics office, central bank), then official international
compilations (IMF, World Bank, UN, ILO, PWT; for revenue, the OECD Revenue Statistics country notes
put every instrument on one basis), then regional bodies. When a number seems unavailable, look
for the counterpart statistics (what partners report about the country), regional peers and the
international databases before falling back. A choice made by another model or institution is
evidence only with its reasoning.

**Check.** Each row names its source, year and GDP basis; load-bearing numbers are confirmed by a
second, independent source; a lower-rung number is marked as such rather than dropped. [PHL, ETH]

## Paths: both tails

**Rule.** For every claim about a path, report its minimum and maximum with their years, and look
at the plotted line before writing the sentence.

**Why.** A check of the trough alone passed while the debt path climbed about 14 points of GDP
above target. [PHL]

## Keeping numbers in docs true to the run

**Rule.** Every model input and model result in the docs and the calibration PR comes from code:
tables and figures generated from the final run's saved output and the packaged JSON, and prose
numbers read from the JSON (for example with glue cells). Source and literature figures are typed
with their citation, and entered once in code where the model uses them. Write the docs after the
calibration settles, and use the repo's existing tooling before adding any.

**Check.** At review, look for model numbers typed by hand. A test that pins key packaged values
with their sources, or, where the repo can rebuild its packaged JSON offline, a test that the JSON
equals the rebuilt one, catches silent drift.

**Why.** Hand-typed numbers drifted from the shipped JSON in several repos, and docs written while
tuning went through repeated audits. [ETH]
