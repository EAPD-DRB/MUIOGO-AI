# Fiscal consistency and the near-term fiscal path

Contents
- The budget identity at the debt anchor
- The steady state hides a fiscal error; the transition shows it
- Revenue by instrument, before trusting the balance
- The baseline fiscal stance and the debt anchor
- The closure: tG1, tG2, rho_G
- The interest-growth differential
- Validate the near-term fiscal path
- Spending as a path when outlays move
- An early spike points elsewhere

Each lesson gives the rule, the check, why, and where it was learned (`[CODE]`; the case is in
`lessons/<CODE>.md`). Formulas follow OG-Core's `fiscal.py`; confirm them in your ogcore. Ratios
here are to the model's `Y`; compare them with data on one GDP basis (validation-dashboard.md):
convert the data, or report the model over `Y + cons_tax_revenue`.

## The budget identity at the debt anchor

**Rule.** Spending shares, transfers, public investment, pensions and revenue must satisfy the
steady-state budget at `debt_ratio_ss`. Set government consumption from the identity, not from a
sibling or from today's outturn.

```
pb* = (r_gov − g)·debt_ratio_ss,        g = e^{g_y}(1 + g_n_ss) − 1

G/Y = (revenue + aid + net FDC payments)/Y − (TR + I_g + pensions + UBI)/Y − pb*
```

Revenue is total tax revenue; aid is `alpha_FA`; net FDC payments (funded defined-contribution
fund to the government, which can be negative) are zero unless that pension system is on.

**Check.**
- After every steady-state solve, rebuild `G/Y` from the saved output (`total_tax_revenue`,
  `foreign_aid`, `fdc_fund_revenue`, `fdc_fund_transfer`, `TR`, `I_g`, `agg_pension_outlays`,
  `UBI`, `D`, `r_gov`, `Y`) and match the solved `G/Y` to four decimals. Solved `G` is positive.
- Compare the solved `G/Y` with the steady-state `alpha_G` you entered. A gap that no adopted plan
  explains is a fiscal error the transition will carry.
- The gap between solved `G/Y` and observed government consumption is about the country's actual
  primary balance less `pb*`, plus measurement differences: the consolidation the stable-debt
  steady state embeds. Name it in the docs. [PHL, ZAF]
- Public investment (`alpha_I`) is itself sourced, not a placeholder.

**Why.** The steady-state closure sets `G` to whatever balances the budget, so a wrong input does
not stop the steady state from solving. Computing `alpha_G` from an identity that omits public
investment or pensions overstates it by their share of GDP [PHL]; the steady state hides any such
error, and only the transition shows it [JPN].

## The steady state hides a fiscal error; the transition shows it

**Rule.** When the steady state solves but the baseline transition diverges or overshoots, check
the budget identity before any solver setting.

**Check.** Debt-to-GDP over the first `tG1` years of the baseline: a climb that the adopted plan
does not have is a spending-revenue gap (or a near-term interest-growth gap; see below). With a
debt-elastic premium on (`r_gov_DY`, `r_gov_DY2`), the climb feeds the premium and the path runs
away.

**Why.** On the transition `alpha_T` holds throughout and `alpha_G` until `tG1`; only then does the
closure move `G`. A real fiscal runaway is not a convergence problem, and no damping or acceleration
fixes it. [ZAF]

## Revenue by instrument, before trusting the balance

**Rule.** Score each revenue line against collections by instrument: personal income tax,
corporate tax, consumption taxes (`tau_c` covers all indirect taxes, not VAT alone), payroll,
bequest and wealth taxes. OG-Core has no line for non-tax revenue: either fold it into a named tax
and say so, or net it against spending in `alpha_G`, and state which.

**Check.** Every nonzero tax parameter in the JSON maps to a collection line; a tax the docs call
zero is zero in the JSON.

**Why.** A rate set too high, or a tax left over from a sibling, raises revenue that hides spending
above revenue, and the model looks stable until that tax is fixed. Switching a flat income tax to a
progressive one exposes such a gap, because progressive revenue moves more along the transition;
check the balance before blaming the tax form. [ZAF]

## The baseline fiscal stance and the debt anchor

**Rule.** The baseline is the country's normal operation under current policy: outturns for past
years, the adopted budget, and the government's own medium-term plans where they are budgeted and
financed. A program not adopted as policy, an international forecast or an aspirational target is a
scenario run against the baseline; its documents are sources of data, not the baseline.

**Check.** For each path you put into the baseline, name the document that commits the government
to it (budget law, medium-term fiscal framework). If you cannot, it is a scenario.

**Why.** Reforms are measured against how the country actually runs; a baseline built on a program
measures them against an assumption.

**The debt anchor.** OG-Core needs a stable debt ratio in the long run; it is a modelling anchor,
not a claim that the country will consolidate. Choose `debt_ratio_ss` as the anchor adopted in law
or in the medium-term framework (a fiscal rule) if there is one; otherwise the ratio current plans
stabilise at, or today's ratio. A program or lender anchor is a scenario. Say which you used, check
that the debt is in a currency and on terms that make a stable ratio meaningful, and compare the
`pb*` it implies with the country's recent primary balances. [JPN, PHL, ZAF]

## The closure: tG1, tG2, rho_G

OG-Core's closure moves only `G`. For `t < tG1`, `G = alpha_G·Y`; for `tG1 ≤ t < tG2`, `G` closes a
fraction `rho_G` of the gap between debt and `debt_ratio_ss` each year; from `tG2`, it holds debt at
the anchor. `TR` follows `alpha_T·Y` throughout (or the baseline level under `baseline_spending`),
and becomes the residual only when `budget_balance` is on. Defaults: `tG1` 20, `tG2` 256, `rho_G`
0.1. With an FDC fund, the fund pays its whole reserve to the government at `tG1 − 1`.

**Rule (judgement).** Set `tG1` to cover the years of adopted plans and make the hand-over to the
closure believable: by `tG1`, the `alpha_G` path should be near `pb*`, so the closure does not
impose a consolidation the country has never made.

**Check.** The primary balance's largest one-year move after `tG1` against the largest sustained
consolidation in the country's record (excluding one-off years). If it is larger, lengthen the path
to `pb*` before `tG1` or lower `rho_G`.

## The interest-growth differential

**Rule.** Check both legs of `r_gov − g` before accepting the `pb*` they imply.

**Check.** `r_gov` against the treasury's effective real rate (interest paid ÷ average debt, less
inflation on the GDP deflator); `g` against the country's own recent and planned growth.

**Why.** A model differential hotter than the country's inflates `pb*` and pushes consistent
spending below real spending; a cross-country wedge or a stagnant growth window are the usual
causes (macro-open-economy.md, the government's interest rate and `g_y`). [ZAF, PHL]

## Validate the near-term fiscal path

**Rule.** Build the fiscal path panel together with the steady-state dashboard: debt, primary
balance, revenue and public investment over the first ten to fifteen years of the baseline
transition, against outturns and the adopted plans. Ship it as a figure in the docs, generated from
the run, with its sources in the caption.

**Check.**
- Primary balance from `TPI_vars.pkl` on the same concept as the data (usually including grants):
  (`total_tax_revenue` + `foreign_aid` + `fdc_fund_revenue` − `fdc_fund_transfer` −
  `total_primary_government_outlays`)/Y.
- `initial_debt_ratio` is gross debt at the end of the year before the start year, over GDP on the
  same basis, on the same debt concept as `r_gov` and `debt_ratio_ss`; a wrong value is invisible
  in the steady state and obvious in the first year of the panel. [JPN]
- Revenue against the plan's revenue line, with one stated concept bridge (general government
  accrual against central government cash) held constant.
- Axis limits show the whole model path; report each path's minimum and maximum with their years.

**Primary balance right, debt wrong:** the gap is interest and growth. Compare the model's
near-term real `r_gov` and growth with the plan years' own, and report the cause or set a near-term
rate path. [THA]

**Why.** In the steady state debt equals the anchor you chose; only the transition starts from the
measured debt, and next year's data can falsify the path.

## Spending as a path when outlays move

**Rule.** When the adopted plan consolidates gradually, or when pensions or other outlays change a
lot over the transition, set `alpha_G` as a path for `t < tG1`:

```
alpha_G(t) = [revenue(t) + aid(t) + net FDC(t) − TR(t) − I_g(t) − pensions(t) − UBI(t)]/Y(t) − pb_plan(t)
```

with each term taken from a baseline run's own paths and `pb_plan` on the model's concept (grants
included). Where the plan is a debt path, OG-Core's timing gives
`pb_plan(t) = (1 + r_gov,t)·d(t) − (1 + g_t)·d(t+1)`, with `d(t)` debt at the start of year `t`
over that year's GDP (published ratios are end of year), `g_t` the model's own GDP growth in levels,
`e^{g_y}(1 + g_n[t])·Y(t+1)/Y(t) − 1` with the saved, detrended `Y` (not the trend `g` above), and `r_gov,t` the near-term rate
from the baseline run. This avoids bridging the plan's revenue concepts to the model's. Follow the
adopted plan's years; for projection years beyond them, hold at `pb*`.

**Check.** The baseline's primary balance follows the plan year by year, and debt stays inside the
plan's band. The steady state is unchanged (the closure ignores `alpha_G` there). Re-fit the path
after any change to the initial-wealth condition, which moves the revenue path.

**Why.** Where today's primary balance is below `pb*`, a flat identity value makes the model
consolidate in year one, years ahead of the plan; with pension outlays rising from today's level it
runs surpluses that pay debt far below the anchor before the closure starts. [PHL, KOR]

## An early spike points elsewhere

A one-to-two-year pulse in consumption or consumption-tax revenue at the start of the baseline is
an initial-condition problem, not fiscal dynamics: check the start cohorts' solution
(og-solver-diagnosis) and the initial-wealth condition (macro-open-economy.md) first, and do not
tune fiscal parameters against it.
