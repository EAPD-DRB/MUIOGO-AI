# Macro and open-economy block

Contents
- The start year
- Government debt: measured start, chosen anchor
- Debt held abroad
- The capital stock: private, and on one price basis
- Public capital
- The capital share
- Foreign capital (zeta_K), gross or net
- The world interest rate
- Growth of productivity (g_y)
- The government's interest rate
- Remittances and aid
- Initial household wealth
- Patience (beta_annual)
- Cash transfers (alpha_T)

Each lesson gives the rule, when it applies, the check, why, and where it was learned (`[CODE]`;
the case and its numbers are in `lessons/<CODE>.md`). Parameter names and formulas follow OG-Core;
confirm each in your ogcore (`default_parameters.json` gives descriptions, defaults and valid
ranges). The `K/Y` closed form used below is in method.md.

## The start year

**Rule.** The start year is the latest year the calibration observes, not a projection year.

**Check.** For each anchor (initial debt, remittances, collections, the capital stock), say whether
it is an observation or an extrapolation in the start year. `initial_debt_ratio` is the debt at the
start of that year.

**Why.** A start one year past the data turns observed levels into extrapolations and makes the
packaged initial debt the wrong year's. Changing the start year regenerates the demographics and
everything derived from them. [PHL]

## Government debt: measured start, chosen anchor

**Rule.** `initial_debt_ratio` is a measurement; `debt_ratio_ss` is a policy anchor (choosing it:
fiscal-consistency.md). Use one debt concept, paired with the interest paid on that same concept.

**Check.**
- A jump in the debt ratio is real deterioration and not a valuation effect of a currency move.
- Where the government holds large financial assets (a funded pension reserve, a sovereign fund),
  OG-Core's government has no assets beyond any funded-pension fund it models: use gross debt,
  leave out the assets and their income, and expect solved `G/Y` below the data by about that
  income. Keep it out of `alpha_FA`, which is foreign aid and also enters the resource constraint.
  [KOR]

## Debt held abroad

**Rule.** `initial_foreign_debt_ratio` is the measured foreign share of the debt stock. Set
`zeta_D`, the foreign share of new issues, equal to it unless the recent flow is a crisis outlier,
in which case use a projected medium-term flow. In the steady state the foreign share equals
`zeta_D` by construction: an input, not a moment to score.

**Applies when** much public debt is owed to official lenders abroad on concessional terms. Check whether
your ogcore models debt contracted abroad at its own rate (`hasattr(Specifications(),
"alpha_D_ext")`). If it does, model that debt as its own stock at its own real rate (the
foreign-currency rate less foreign inflation, plus expected real depreciation), with market debt,
`debt_ratio_ss` and `zeta_D` covering the rest, and decide what happens after the sustainability
analysis's last year: held at a share of GDP with a rate below growth, it is a permanent inflow from
abroad.

**Check.** Interest paid abroad on public debt against the balance of payments.

**Why.** Without its own rate, concessional debt held abroad earns the household return and the
interest paid abroad is overstated several times over. [ETH]

## The capital stock: private, and on one price basis

**Rule.** The `K/Y` target, `delta_annual` and the investment share are all private and all at
current national prices: net private capital at current national prices over GDP at current
national prices, and private consumption of fixed capital over the same GDP.

```
private K/Y = total K/Y − public K/Y
delta       = (total CFC − government CFC)/Y ÷ private K/Y
delta_g     = government CFC / public capital     (parameter delta_g_annual)
```

**Check.**
- Use the national-price ratio: a net stock at current national prices over GDP at current prices
  (the national accounts' own stock table, or a cross-country source with national-price detail; the
  Penn World Table's main-table stock is at PPPs, its national-price stock is in the capital-detail
  file). Compute a PPP ratio only to show how much the choice
  matters.
- The national-price ratio moves when a devaluation revalues the stock at replacement cost: average
  several years, or say why one year is used.
- On that basis, steady-state investment `(e^{g_y}(1+g_n) − 1 + delta)·K/Y` should be close to the
  measured private investment share (a trend in the relative price of capital goods opens a gap
  here), and the return on capital plausible (the capital share, below). All use the same `K`.
- Public capital in nominal terms over nominal GDP (the national accounts, or the IMF's investment
  and capital stock dataset, which has national-currency series), not a constant-price series.
- After a rebasing, every stock and flow on one GDP basis.

**Why.** OG-Core has one good, so capital, investment and depreciation are consistent only at one
set of prices, and the national accounts' shares are at domestic prices. PPP and national-price
ratios differ by up to a third, in either direction, because capital goods' relative price differs
across countries and over time. If the national-price ratio implies an implausible return, look at
depreciation on another basis, resource rents or product taxes left in the capital share, private
against total capital, and pre-tax against after-tax returns before suspecting the basis: a
sibling's PPP choice that "matched" the return evidence rested on offsetting errors of this kind.
OG-Core's `K` is private, so scoring it against total capital sends patience after a gap that is
not there. [ETH, KOR, ZAF]

**Applies most** in a slow-growth economy, where `(g + delta)·K/Y` makes depreciation nearly the
only source of investment demand, so OG-Core's 0.05 default (a US value) sets investment. [JPN]

## Public capital

**Rule.** `initial_Kg_ratio` is the measured public stock (nominal, as above). The steady state
follows OG-Core's law of motion,

```
K_g/Y = (1 − infra_investment_leakage_rate)·alpha_I / (e^{g_y}(1 + g_n) − (1 − delta_g))
```

so a measured stock far above it (a state-built boom) starts high and depreciates. A nonzero
`gamma_g` (public capital's share of output) needs a nonzero `initial_Kg_ratio` (the validator
rejects it otherwise), and with `epsilon` ≤ 1 OG-Core drops `gamma_g` from production wherever the
public stock is zero, including the steady state when `alpha_I` is zero.

**Check.** Put the inefficiency of public investment in one place: the leakage rate and the
measured stock carry it; the output elasticity `gamma_g` comes from estimates of the return to
public capital and is not discounted again. Cite the published version of an estimate.

**Why.** Inefficiency counted in both the leakage and the elasticity discounts public capital
twice; the working-paper and published versions of a standard elasticity differed. [ETH]

## The capital share

**Rule.** `gamma = 1 − labour share − gamma_g`, with the labour share measured on the model's GDP
basis (validation-dashboard.md: a share of market-price GDP converts to the model's `Y`), adjusted
for self-employment income where much of the economy is informal or agricultural (mixed income is
booked as capital), and with natural-resource rents taken out where they are large. State the
result as a range with a centre, from non-circular evidence: the direction of the self-employment
bias, the country's institutions (for example state-owned land), and the return check below.
Decide it once, before tuning; never move it to close a `K/Y` gap.

**Check.**
- The labour share the model implies, `1 − gamma − gamma_g` at `epsilon` 1 where public capital is
  positive, against the data on the same basis.
- The return on capital against evidence of the same kind. Pre-tax evidence (PWT `irr`,
  Caselli-Feyrer) against the model's pre-tax return, `gamma·Y/K − delta` plus the public-capital
  rent before tax. PWT's `irr` divides capital income net of depreciation (nominal GDP less labour
  income less natural-resource rents) by the net stock at current national asset prices, and covers
  all fixed capital, public included. After-tax evidence (FDI income over the FDI stock) against
  the owners' return OG-Core pays, `r + (1 − tau_b)·MPK_g·K_g/K` (`aggregates.get_r_p`). Never
  against `r_p`, which also averages in government debt at `r_gov`.
- A curated `gamma` is off the live-data path: if the example runs with `update_from_api=True`, a
  refreshed `1 − labour share` can overwrite it. Take curated values out of the live path, not
  behind a flag. [ETH]

**Why.** An unadjusted labour share overstates capital in informal economies; a share moved to fit
`K/Y` chases the wrong lever and can push `r` below the world rate. [ETH, THA]

## Foreign capital (zeta_K), gross or net

**Rule.** `zeta_K` is the share of excess capital demand that foreigners fill; no dataset measures
it. Tune it to one moment, the foreign-owned share of private capital `K_f/K` from the
international investment position, after deciding gross or net. Treat net exports as a check.

**Gross or net.** OG-Core has `K = K_d + K_f` with `K_d = B − D_d` (plus funded-pension balances
where that pillar is on): households hold domestic capital and domestic government debt only. So
`K_f/K` is the gross foreign-owned share: inward direct and portfolio equity, over GDP, over private
`K/Y`. `K_f` is not clamped, so a negative value reads as a net creditor position, but the model has
no household foreign assets; calibrate to gross, check the sign of the country's net position, and
state what is missing (its foreign portfolio and that income). [JPN, KOR]

**Check.**
- Solved `K_f/K` against the target; re-tune `zeta_K` after any tax or sourced-parameter change,
  since domestic saving moves the share at a fixed `zeta_K`. [PHL]
- A placeholder (0.9, or OG-Core's 0.10 default left untouched) shows as a foreign share far from
  the data; at high values domestic capital `K_d` can turn negative and OG-Core floors it ("K_d has
  negative elements") while `K_f` keeps the unfloored value, breaking the capital split.
  [PHL, BRA, ZAF, JPN]
- With `zeta_K` at 1, OG-Core sets `r` to the world rate.

**Not a lever for an investment gap.** A higher `zeta_K` buys investment only as foreign-owned
capital, arriving as a first-year jump and paid the owners' return; keep it on the measured share.
[ETH]

## The world interest rate

**Rule.** For an open, investment-grade economy, the world risk-free rate plus the sovereign spread;
for a near-closed or distressed one (no spread for a sovereign in default or restructuring), the
benchmark (OG-Core's 0.04) with country risk carried by a low `zeta_K` and the debt premium. Say
which rule you applied.

**Check.** The world rate sets the sign of `K_f`: if it is above the solved domestic return,
capital flows out at any `zeta_K`. Solve and confirm the sign the target needs. If a high-saving
creditor's domestic return at the data's `K/Y` is at or below the world rate, no `zeta_K` gives a
positive gross share: keep the sourced rate and `K/Y`, set `zeta_K` from an openness prior with a
reason, and report the miss. [ZAF, KOR]

**Why.** At high `zeta_K` this constant sets `r`, so an unsourced default decides the interest rate.
[JPN]

## Growth of productivity (g_y)

**Rule.** Measure labour-productivity growth per hour (real GDP over persons engaged times average
hours, for example from PWT) over a window chosen with a reason: after a structural break, before
the latest shock, without unrepeatable booms. Make it consistent with the growth the debt anchor
assumes (GDP growth ≈ `g_y` + `g_n_ss`): where the anchor rests on a plan built on a medium-term
recovery, use that recovery's productivity growth (medium-term GDP growth less `g_n_ss`).

**Check.** The window is a named constant with its rationale. Hours-per-worker and participation
trends are both stripped or both kept. Long-run GDP growth in the model matches the growth behind
`debt_ratio_ss`.

**Why.** Steady-state hours per worker are constant, so a falling-hours trend measured per worker
understates productivity growth; a stagnant window paired with a stabilisation anchor is internally
inconsistent and debt will not hold. [JPN, ZAF]

## The government's interest rate

**Rule.** `r_gov = max(r_gov_scale·r − r_gov_shift + r_gov_DY·D/Y + r_gov_DY2·(D/Y)², r_gov_floor)`
multiplies the whole stock, so it is the average effective real rate. Keep the cross-country slope;
set the shift so the steady-state `r_gov` equals the treasury's effective real rate (interest paid
÷ debt, less expected inflation), from the treasury's own reports. Where real rates are negative,
set `r_gov_floor` (if your ogcore has it) below that rate.

**Debt-elastic premium.** Centre the quadratic on the anchor `D̄` so it is zero in the steady state:
`r_gov_DY = −2·r_gov_DY2·D̄` and `r_gov_shift = base − r_gov_DY2·D̄²`. It then prices any departure
of debt from the anchor, below as well as above. Where the premium is evaluated on total debt
including debt contracted abroad, centre it on the long-run total, not on `debt_ratio_ss` alone.

**Check.** Solved steady-state `r_gov` equals the effective rate; a reported `r_gov` equal to
`r_gov_floor` means the floor clipped it; a live-data refresh does not rewrite the shift.

**Why.** The cross-country intercept over-predicted what treasuries pay by 0.5 to 3 points; a
marginal or ten-year yield is new-issue cost, not the average; a clipped negative rate moves `pb*`
and so spending. [ZAF, PHL, JPN]

## Remittances and aid

**Applies when** remittances or aid are material: without them a low-income economy shows a
spurious trade surplus and a fiscal squeeze.

**Rule.**
- Level: personal remittances (BPM6, household income from abroad), on one GDP denominator; a
  central bank's headline ratio is often the narrower cash series, about a point of GDP lower. Aid
  to the government goes in `alpha_FA`.
- Path: remittances start at `alpha_RM_1·Y` in the first year; until `tG1`, `get_RM` compounds them
  by `(1 + g_RM)/(e^{g_y}(1 + g_n))`; from `tG1` it blends linearly toward `alpha_RM_T·Y`, which
  holds from period `tG2 − 1` and in the steady state. Before `tG1`,
  `g_RM[t] = e^{g_y}(1 + g_n[t−1]) − 1` holds remittances constant in model units, a path
  regenerated with the demographics. `g_RM` is in model growth units, not a nominal currency growth
  rate.
- Distribution: OG-Core's default `eta_RM` (identical to the default `eta`) is US population age
  shares times `lambdas`. Households receive `eta_RM·RM/omega` with your own population, so the
  default hands old households in a young country several times the average. At least rebuild it
  from your own `omega_SS` × `lambdas`; replace it from survey evidence on who receives remittances,
  by income group and age, when that exists.

**Check.** Remittances over GDP along the transition stay where intended; the receiving share by
income group matches the survey. [PHL]

## Initial household wealth

**Rule.** Set the level and shape of wealth in the start year from data where your ogcore allows
it: `initial_wealth_ratio` (household wealth over GDP in the first year, valid 0.8 to 7) and
`initial_hhwealth_dist` (each age and group's share of that wealth, an `S×J` matrix of cell totals
summing to one). Unset, OG-Core scales the steady-state profile so starting wealth equals
steady-state wealth, which hands the first households a windfall when today's population is younger
than the stationary one (a confiscation when older).

**The level.** Prefer the capital-side measure, since the model holds `B = K_d + D_d`:

```
(private K/Y) × (1 − foreign-owned share) + (domestic-held share of debt) × D/Y
```

with private `K/Y` as above. Cross-check against household balance sheets, which usually run lower
because they undercount real property, and write down which you used. Loans that state enterprises
owe abroad are neither government external debt nor foreign direct investment; uncounted, they sit
in household wealth. Treat such enterprises as part of the state, or add the loans to the foreign
capital target, knowing that OG-Core then pays them the owners' return and payments abroad rise.
[ETH, PHL, ZAF]

**The shape.** The steady-state profile is a start. A data shape: the National Transfer Accounts'
asset income by age, split across groups by the steady-state split. With no data, take the shape
households choose in the first period of the transition and feed it back part of the way each
round, at life-cycle ages only (the oldest cohorts' savings are mostly bequests), until start and
first period agree, and report the gap that remains. Keep the shape smooth across any age cutoff.
[PHL, ETH]

**Check.**
- Solved first-year wealth over GDP equals the target, and the outer-loop distance falls; if the
  outer loop stalls with the level anchored inside the loop, compare with the level fixed before the
  solve. [KOR]
- Minimum household consumption in the pickle is positive, and the start cohorts' first-order
  conditions hold (og-solver-diagnosis, class M): builds without the start-cohort fix leave them out
  of the reported Euler error, and the constraint checker only logs a warning. [KOR]
- The first-year foreign-owned share `K_f(0)/K(0)` against the investment position; it is not
  targeted, and where model `K/Y` exceeds the data, measured wealth and the measured foreign share
  cannot both hold. [PHL]
- A one-to-two-year consumption spike in ages 60 and over, an investment collapse and a debt
  paydown are the sign of a wrong initial condition; rule out unsolved start cohorts first
  (og-solver-diagnosis). Reform-minus-baseline tables hide it, since both share the start.
- Re-fit any `alpha_G` path afterwards; it was fitted against the old revenue path. [PHL]

## Patience (beta_annual)

**Rule.** Patience sets how much households save; today's returns are nearly fixed by the capital
share, depreciation and the measured capital stock. Fit it to a saving moment, and if the fit
needs more patience than a long-run bound allows, stop at the bound:
- the saving moment: private `K/Y` in the steady state where the population is near stationary and
  the stock reliable; where starting wealth is measured and the population is far from stationary,
  private consumption and investment in the first transition years;
- the bounds: the owners' long-run return on capital (the capital share, above) stays within the
  return evidence; and, for a capital-importing economy, foreign-owned capital stays non-negative in
  the steady state (a net creditor: see the world rate).

Return evidence describes today; applying it to the long run is a judgement, so state it as one. If
a bound binds, hold `beta_annual` at it as a documented constant and report the saving gap that
remains with its measured causes.

**Check.**
- One transition probe at a candidate value, reading the first years against the data: where
  starting wealth differs from what households at that patience want to hold, the first years move
  far more than the steady state.
- `beta` is one of many levers on `K/Y` (method.md); list them before moving it, and re-ask after
  any change to `gamma`, `delta` or `g_y`.
- A fit that wants patience above one, at its lower limit, or past a long-run bound is a signal, not
  a setting: high curvature with fast productivity growth, a saving target the bounds cannot reach,
  or group targets (wealth shares by income) that one discount factor per group cannot carry. Keep
  such targets as checks.
- OG-Core's default (0.96 for every group) is not a country's value; leaving it is a choice to
  document.

**Why.** Fully matching first-year investment needed a long-run return near 2 percent, below the
return evidence [ETH]; where the bounds allow it, matching the first years is right [PHL]. Tuned to
a long-run firms' return at the world rate, patience saved far less than the national accounts
show; judged on the first years within the bounds, it closed most of the gap [ETH]. [JPN]

## Cash transfers (alpha_T)

**Rule.** `alpha_T` is cash transfers only. Health, care and education provided in kind are
government consumption and belong in `alpha_G`.

**Check.** Split social spending into cash and in kind (OECD SOCX or the national social-security
accounts) and set `alpha_T` from the cash part.

**Why.** In-kind spending in `alpha_T` hands households income they do not have and inflates
consumption. [JPN]
