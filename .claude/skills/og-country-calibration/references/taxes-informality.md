# Taxes and informality

Contents
- Every rate is an effective rate
- Payroll tax
- The bequest tax
- The corporate tax block
- The income-tax form
- Fitting a progressive form to the schedule (GS, HSV)
- Informality
- Revenue OG-Core has no line for
- Effective rates size reforms

Each lesson gives the rule, the check, why, and where it was learned (`[CODE]`; the case is in
`lessons/<CODE>.md`). Confirm parameter shapes in your ogcore's `default_parameters.json`
(`number_dims`) and formulas in `tax.py`, `txfunc.py` and `aggregates.py`.

## Every rate is an effective rate

**Rule.** For every instrument, rate = collections ÷ the model's own base for that instrument:
personal income tax, `tau_c` (VAT and all other indirect taxes on household consumption), the
corporate tax (through the block below), `tau_payroll`, `tau_bq` and the wealth tax. Take
collections by instrument from the national revenue authority, the OECD Revenue Statistics country
note, or the IMF fiscal tables, on one GDP basis.

**Check.**
- Model revenue by instrument against collections, each its own dashboard row; the same
  informality adjustment applied to every instrument it affects (not income tax discounted and
  payroll left statutory). [BRA]
- `tau_c` = consumption-tax collections ÷ household consumption at producer prices; VAT collected
  on government purchases or investment is netted out, or the choice stated.

**Why.** Statutory rates collect well above what countries raise, sometimes many times over; the
excess hides spending above revenue (fiscal-consistency.md) and mis-sizes every reform.

## Payroll tax

**Rule.** `tau_payroll` (by year and income group where its `number_dims` is 2; an older flat-list
value may not load) is levied on wages on top of the income-tax function. Use it only when the income-tax function
excludes payroll; functions estimated from microdata (OG-USA) already include it, and `tau_payroll`
stays zero. Set it from social contributions over the covered groups' wage bill.

How revenue is reported (check `aggregates.get_payroll_tax_revenue` in your build): with
`tau_payroll` nonzero, payroll revenue is computed directly and `frac_tax_payroll` is ignored; with `tau_payroll` zero, `frac_tax_payroll` splits the
income-tax total into income tax and payroll. Its default (about 0.47, from OG-USA) then reports
almost half your income tax as payroll: set it to zero when your function is income tax only.

**Check.** The model's `payroll_tax_revenue`/Y against contributions; the combined household take
against income tax plus contributions.

**Why.** A statutory payroll rate on the whole wage bill collected a hidden 5.8% of GDP on top of
the income tax, which that ogcore reported on the income-tax line. [PHL]

## The bequest tax

**Rule.** `tau_bq` = estate and gift tax collections ÷ the model's bequest flow; usually close to
zero.

**Check.** Grep the JSON: a `tau_bq` equal to a statutory rate, or copied from a sibling, is the
error.

**Why.** Deductions, exemptions and non-filing put effective estate taxation one to two orders of
magnitude below statutory; copied statutory values collected 1–4% of GDP against almost nothing in
the data. [ZAF, PHL, IDN, ETH, BRA]

## The corporate tax block

**Rule.** OG-Core's business tax rate is `cit_rate × c_corp_share_of_assets ×
adjustment_factor_for_cit_receipts`; only the product is identified by collections. Keep `cit_rate`
statutory, set `c_corp_share_of_assets` from data or leave it with a stated reason, and tune the
adjustment factor to corporate tax collections from ordinary business. `delta_tau_annual` (tax
depreciation, a US 0.027 by default) and `inv_tax_credit` come from the country's tax law.

**Applies when** resource revenue is large: royalties, petroleum taxes and state oil-company profits
are rents, not a tax on the saving and investment margin. Loaded onto the adjustment factor they
raise the tax on all capital, depress `K/Y` and mis-size corporate tax reforms. Keep them out of the
factor: model a resource industry (og-multi-industry-calibration), or net them against spending and
say so.

**Check.** Model business tax over GDP against corporate collections excluding resource taxes;
`delta_tau_annual` and `inv_tax_credit` documented, since they enter the firm's return (method.md).

## The income-tax form

**Rule.** Use the highest form the data supports:
1. A flat (`linear`) rate from collections over the base: a first pass only.
2. A progressive parametric form fitted to the statutory schedule and to collections: needs only the
   schedule and a collections total. Default to GS (Gouveia-Strauss).
3. Functions estimated from tax microdata by age and year (OG-USA via Tax-Calculator), where a
   microsimulation model and filer data exist; this wins where it is available.

**Why GS over HSV.** GS's effective rate is positive for positive parameters and income and tends to
zero at low incomes. HSV's is negative below `y = λ^(1/τ)`, a subsidy that drains revenue: on ZAF it
added to a debt runaway whose root cause was a budget that did not balance (fiscal-consistency.md).
[ZAF]

## Fitting a progressive form to the schedule (GS, HSV)

Both forms use the same parameters for `etr_params`, `mtrx_params` (the marginal rate on labour
income) and `mtry_params` (on capital income). The parameters vary by year and age, not by income
group. Incomes enter in currency through `factor`, so scale parameters carry income units:
re-expressing `mean_income_data` in thousands or millions rescales GS's `φ2` by `unit^φ1` and
nothing else.

**GS** (`tax_func_type = "GS"`, parameters `φ0, φ1, φ2`): `T(y) = φ0·(y − (y^−φ1 + φ2)^(−1/φ1))`
on total income; the effective rate rises from near zero toward `φ0`.
- `φ0` = the statutory top marginal rate (an anchor). If no `φ2` reaches collections, a small,
  documented lift of `φ0` is the fallback; say that the top rate then differs from the law's. [ZAF]
- `φ1` (curvature) fitted to the schedule's shape.
- `φ2` (scale) tuned in the model to income-tax collections; the informality and effective-rate
  wedge enters here (or through a compliance scale; see Informality, not both). Revenue responds less
  than proportionally to `φ2` (top incomes pay near `φ0` whatever `φ2` is), so expect two or three
  iterations. [PHL]

**HSV** (`tax_func_type = "HSV"`, parameters `[λ, τ]`): `ETR = 1 − λ·y^(−τ)`. `τ` (progressivity)
does not depend on income units, so fit it to the schedule's shape; `λ` does, so tune it to
collections. Use HSV only where the bottom-end subsidy is harmless.

**Check.** The fitted effective rate against the schedule at several incomes (well below the
threshold, at it, at the median, near the top) and revenue against collections. Pin the bottom
rate in a test as a bound, not an equality.

## Informality

**Rule.** Choose the rung the data supports, and say which:
1. A stated informality reason for effective rates far below statutory, with no mechanism.
2. Household non-compliance graded by lifetime-income group:
   `labor_income_tax_noncompliance_rate` and `capital_income_tax_noncompliance_rate`, by year and
   group, with the informal employment share setting how many bottom groups do not pay. The rate is
   the share of tax owed that is not paid: OG-Core multiplies the income tax by one minus it (the
   parameter's description in `default_parameters.json` says the opposite; the code governs). Bring
   the paying groups' tax to collections with `φ2` or with a scale on the compliance shape, not
   both. [ETH]
3. An informal industry in a multi-industry model (no corporate or consumption tax, its own capital
   intensity and consumption share); illustrative unless anchored to revenue. With an informal
   industry, take firm-side informality out of the corporate adjustment factor. [IDN]

**Check.**
- Non-compliance and `income_tax_filer` do not reduce payroll tax: set `tau_payroll` by group, zero
  for the groups that do not contribute.
- Use non-compliance for tax owed but not paid, and `income_tax_filer` = 0 only for groups legally
  below the threshold. They act the same way in the income-tax arithmetic; the choice documents the
  reason. [ZAF]
- Revenue against collections with the compliance settings in place. For a reform that changes
  compliance over time, transition revenue moves with it; if it tracks the baseline while labour
  supply moves, your ogcore applies the first year's compliance to the whole path.

## Revenue OG-Core has no line for

**Rule.** Recurring non-tax revenue and residual taxes (often several percent of GDP) belong in the
model, mapped to the instrument that prices the same margin and tuned to collections:
- property-type taxes (recurrent property tax, transaction and stamp duties, local levies) to the
  wealth tax, made flat: `h_wealth = 1` and `m_wealth` small next to wealth in model units but
  positive (zero divides 0/0 at zero wealth, which entrants hold), `p_wealth` tuned;
- government capital income from ordinary business (dividends of state enterprises and the central
  bank, interest income) and unallocable income taxes (final withholding) to the corporate
  adjustment factor;
- fees and charges to `tau_c`.

**Check.** Recurring flows only: exclude one-offs (privatisation, fund transfers, concession fees).
Estate and gift taxes are classed under property taxes (OECD heading 4300), and inside an "other"
residual in some country notes: net them out so they do not count twice against `tau_bq`. Total
income tax can exceed personal plus corporate income tax; the gap, income tax not allocable
between persons and companies (OECD 1300), is real revenue for the capital side. If you net a stream against spending instead, say so (fiscal-consistency.md).

**Why.** Left out, the budget identity pushes model spending too low. [PHL]

## Effective rates size reforms

A statutory cut moves the business tax rate by the cut × `c_corp_share_of_assets` × the adjustment
factor. When the factor rose to carry true collections, the same corporate rate cut's steady-state
GDP effect roughly doubled. A calibration that misstates an instrument's effective rate mis-sizes
every reform that runs through it. [PHL]
