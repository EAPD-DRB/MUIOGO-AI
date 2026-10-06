# Taxes and informality

Contents
- The universal method: effective rate = collections ÷ base
- Payroll is additive on top of the ETR function
- Standing check: the bequest tax
- PIT functional form: three paths
- Progressive-fit recipe (GS and HSV)
- Informality: the maturity ladder
- OG-Core structural facts
- Known OG-Core bugs in the compliance machinery
- Capturing non-tax and residual-tax revenue
- Statutory-for-effective errors bias reforms
- Doc/code drift

## The universal method: effective rate = collections ÷ base

Apply it to PIT, `tau_c` (VAT and all other indirect taxes), CIT (through
`adjustment_factor_for_cit_receipts` × `c_corp_share_of_assets`), and `tau_payroll` (statutory rate
× covered share of the wage bill, not headcount; or directly, SSC collections ÷ the model's labour
share of income). Apply it consistently. OG-BRA is the cautionary tale: it discounts PIT for
informality but leaves payroll at the full statutory rate. The anchor for every instrument is the
OECD Revenue Statistics country note (validation-dashboard.md, sourcing hierarchy).

## Payroll is additive on top of the ETR function

`tau_payroll` adds to the income-tax function (`income_payroll_tax_liab = T_I + T_P` in ogcore
`tax.py`). With `frac_tax_payroll = 0` the combined take reports on the iit line while the payroll
line shows zero, so a statutory payroll rate silently collects on the whole wage bill in addition to
the income-tax function. PHL: `tau_payroll = 0.14` was collecting a hidden 5.8% of GDP on top of a
flat 20% ETR. Audit the combined household take, decompose it yourself
(`true payroll = tau_payroll × wL/Y`), and set `frac_tax_payroll = SSC/(SSC+PIT)` so the reported
split matches the data. **[PHL]**

Recent ogcore lets `tau_payroll` vary by lifetime-income group as well as time (a `T × J` array
entered in nested form, `[[0.124]]`; check the parameter's `number_dims` in your resolved
`default_parameters.json`). That makes coverage that rises with income representable directly; a
flat-list value from an older JSON will not load once the repo moves to that ogcore.

## Standing check: the bequest tax

The bequest tax is a recurring statutory-for-effective error in this family: ZAF `tau_bq = 0.2` collecting 3.9% of GDP; PHL `tau_bq = 0.06` collecting 1.19% vs actual
estate and donor collections of ~0.07%.
Deductions, exemptions and non-filing put effective estate taxation one to two orders of magnitude
below statutory nearly everywhere. Always compute `tau_bq` from collections ÷ model bequest flows,
and grep every new port for this parameter. IDN, ETH and BRA had not been checked when this was
written.

## PIT functional form: three paths

In increasing fidelity:

1. **Flat `linear`** ("given limited data"): one ETR and one MTR. Cheapest, no progressivity.
   PHL/IDN/BRA pick the number; only ETH derives it (revenue identity). Fine as a first pass.
2. **Progressive parametric form fit to the statutory schedule** **[ZAF; the best data-poor
   option]**: real progressivity with no microdata. You need only the statutory PIT schedule and a
   collections target. Prefer it over flat-linear whenever a schedule exists (almost always).
   **Default to GS (Gouveia-Strauss), not HSV.** GS floors the ETR at exactly zero, which is faithful
   wherever a threshold and rebates exempt the bottom, and is numerically robust. HSV's ETR goes
   negative below the threshold, and that implicit subsidy is not cosmetic: on ZAF it drained
   transition revenue and helped push the TPI into a debt runaway, where GS with the same targets
   converged.
3. **Microdata-estimated nonlinear** (OG-USA via Tax-Calculator): a 12-parameter form fit by
   age × year to microsimulated ETR/MTR. Needs a Tax-Calculator equivalent and filer microdata.

## Progressive-fit recipe (GS and HSV)

Verified against ogcore `txfunc.py`. Both forms calibrate the same way: the statutory schedule pins
the shape, the collections target pins the level. Both use the same parameters for `etr_params`,
`mtrx_params` and `mtry_params` (analytically consistent; mtrx = mtry, the total-income MTR).

**GS** (`tax_func_type = "GS"`, params `(φ0, φ1, φ2)`): `T(y) = φ0·(y − (y^−φ1 + φ2)^(−1/φ1))` on
total income. ETR = 0 at the bottom and tends to `φ0` at the top.

- Set `φ0` = the statutory top marginal rate (an anchor, not a fit).
- Fit `φ1` (curvature) to the schedule's shape.
- Tune `φ2` (scale) in-model to the PIT/GDP collections target. The effective-rate and informality
  wedge enters here, pulling the level down to actual collections.
- Examples: ZAF `[0.464, 1.39288, 1.43e-8]` → PIT 10.1% of GDP, top MTR 45%. PHL
  `[0.35, 1.196, 1.9e-8]` → PIT 3.12% of GDP.
- Tuning mechanics **[PHL]**: revenue's response to `φ2` is concave. Top incomes sit where
  ETR ≈ φ0 regardless of φ2, so halving φ2 cuts revenue by less than half; expect two or three
  in-model iterations, not one proportional step. Lowering φ2 for informality acts like shifting the
  schedule toward higher incomes, the right shape for "most earners effectively untaxed".
- GS smoothing makes the sub-threshold ETR near zero, not zero (PHL: ~1.2% at 80% of the exempt
  threshold). Accept it; it is the price of never going negative. Pin it in a test as a bound, not
  an equality.
- Incomes are evaluated in currency units via `factor` (`mean_income_data`), so φ2 has units
  `income^(−φ1)`.

**HSV** (`tax_func_type = "HSV"`, `λ = coef0`, `τ = coef1`): `ETR = 1 − λ·y^(−τ)`,
`MTR = 1 − λ(1−τ)·y^(−τ)`. τ (progressivity) is scale-invariant; fit it to the schedule's shape. λ
absorbs the income scale; tune it to collections. (ZAF's HSV fit had τ ≈ 0.14 tracking SARS, before
the GS switch.) Use HSV only where a bottom-end subsidy is harmless. In a tightly balanced fiscal
block it bleeds transition revenue; if the budget has no slack, use GS.

## Informality: the maturity ladder

Choose the rung the data supports:

1. **Narrative only** **[BRA]**: name informality as the reason effective ≪ statutory, pick a
   stylized flat rate, flag it as provisional. No mechanism.
2. **Structural two-sector demo** **[IDN, "Option B"]**: OG-Core's multi-industry `M`/`I`
   machinery with an informal industry (`cit_rate = 0`, `tau_c = 0`, lower capital intensity, its own
   `alpha_c` share). Illustrative, not revenue-anchored.
3. **Household graded non-compliance** **[ETH, "Option A", fullest]**:
   `labor_income_tax_noncompliance_rate[t,j]`, `capital_income_tax_noncompliance_rate[t,j]` and
   `income_tax_filer[t,j]` grade compliance by lifetime-income group (a proxy for formality: the
   informal employment share sets how many bottom groups get noncompliance = 1). The compliant-group
   ETR is solved from a revenue identity and the MTR set to the statutory top rate. Informality is
   non-remittance, not non-filing (filer stays 1). If you later add an informal industry (Option B),
   move the firm-side informality out of the CIT factor to avoid double counting.

## OG-Core structural facts

- `etr_params`/`mtrx_params`/`mtry_params` vary by (t, age s) only, not by ability type j. Group
  heterogeneity enters only through each household's income arguments.
- `noncompliance`/`income_tax_filer` vary by (t, j), not by age.
- **`mtrx_params` is the marginal rate on labour income; `mtry_params` on capital income.** The
  naming is not mnemonic; any doc that says "mtrx = capital" is wrong (ETH's taxes.md had it reversed;
  it was fixed).

## Known OG-Core bugs in the compliance machinery

From the ETH informality work; check whether your ogcore still has them.

- *SS diagnostic*: `SS.py` tiles the capital-noncompliance array from the labour rate for the
  post-solve `mtry_ss` diagnostic (does not affect the solution). Keep labour = capital
  noncompliance and it never bites.
- *TPI path*: `TPI.py` applies year-0 compliance and filer values to the whole path's revenue
  accounting, so any time-varying compliance reform gives inconsistent transition revenue (behaviour
  responds, revenue does not). Steady states are fine; a formalization reform needs the upstream fix.
  Symptom: reform revenue tracks the baseline exactly while labour supply moves.

## Capturing non-tax and residual-tax revenue

**[PHL, net-new; replicate everywhere]** OG-Core has no "other revenue" parameter, but leaving
recurring non-tax revenue and residual taxes out (often ~4% of GDP) understates government resources
and, through the budget identity, forces model spending too low. Map each stream to the instrument
that prices the same economic margin, then tune in-model to collections:

- **Property-type taxes** (recurrent property tax, transaction and stamp duties, local levies; the
  OECD "other taxes" residual) → the wealth tax: `h_wealth = 1` and `m_wealth` small but positive
  (`m = 0` divides 0/0 at `b = 0`; `0.001` works) make `ETR_wealth ≈ p_wealth` flat, zero at zero
  wealth, MTR → `p_wealth`. A recurrent property tax is a flat tax on a form of wealth, so the
  distortion lands on the right margin (saving). PHL: `p_wealth = 0.0035` gives 1.32% of GDP.
- **Government capital income** (SOE and central-bank dividends, state gaming shares, guarantee
  fees, treasury interest income) and **unallocable income taxes** (final withholding on deposits
  etc.) → the CIT adjustment factor; both are government takes from capital income.
- **Fees and charges** (user payments for services) → `tau_c`.

Use only recurring flows. Treasuries book one-offs (fund-balance transfers, privatization,
concession fees) in non-tax revenue and often flag them; exclude them. Two OECD-accounting traps:
estate and donor taxes sit inside the "other taxes" residual (net them out or they double count
against `tau_bq`), and the income-tax total usually exceeds PIT + CIT; the difference is unallocable
withholding, real revenue that belongs on the capital side.

## Statutory-for-effective errors bias reforms

**[PHL]** A CIT cut's simulated effect doubled once the adjustment factor carried true collections:
the statutory rate change maps to a larger effective-rate change on a properly scaled base. A
calibration that misstates an instrument's effective rate mis-sizes every reform that runs through
it. Size reforms by the revenue they must raise where the base is uncertain (validation-dashboard.md,
"Audit each instrument's base").

## Doc/code drift

Docs drift from the shipped JSON (OG-IDN's `taxes.md` rates were stale against its JSON). Glue doc
numbers from the JSON (validation-dashboard.md).
