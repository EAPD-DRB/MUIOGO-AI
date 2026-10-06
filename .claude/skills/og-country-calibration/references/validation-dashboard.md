# Validation dashboard

The near-term fiscal path panel is in fiscal-consistency.md; build it together with this one.

Contents
- Completeness: an unscored moment cannot pull its parameter
- The steady-state dashboard
- Moments most often tuned for but never scored
- Two traps when adding rows
- Revenue by instrument
- Sourcing hierarchy for the data side
- Mind the GDP vintage
- Read the model side from the solved pickles
- Structural validation (multi-industry)
- Consumption is a residual
- g_n is a path; the steady state uses its terminal value
- Pair the debt concept with the interest concept
- Audit each instrument's base, not just its yield
- Know the family traits before fixing them
- Note derived quantities honestly
- Verify both tails of every path
- Fast value-pinning test
- Prevent doc/JSON drift with glue

## Completeness: an unscored moment cannot pull its parameter

The general form of the `zeta_K` failure (SKILL.md, finding every lever): it sat at a placeholder because `K_f/K` was not a
row on the dashboard, and the loop optimised what it could see. Four rules, all checkable:

1. **Every tuned parameter's identifying moment must be on the dashboard.** Grep the tuned dials,
   grep the dashboard rows, and require a one-to-one match. A dial with no scored moment drifts
   silently.
2. **A dial moved to close a residual is a free parameter, not a calibration.** OG-JPN's `p_wealth`
   and `tau_bq` were nominally tuned to property and inheritance tax but in practice scaled to close
   total revenue, so they absorbed every other line's error. Tune each dial to its own moment; total
   revenue is the check that the parts add up, never the thing you steer.
3. **Score every component of the resource constraint,** not just the residual. Put `I/Y`, `I_g/Y`,
   `G/Y` and `NX/Y` next to `C/Y`.
4. **Score the first-tier moments early in the transition too,** not only at the steady state.
   Report each at t=0–10 as well: a steady state can land close while the first years miss badly
   (OG-JPN's consumption share in 2025, from a mis-set initial wealth). **[JPN]**

The moments most often tuned for but never scored, and the traps when adding rows, follow.
**[net-new: JPN]**

## The steady-state dashboard

**[emerging: IDN, ETH; adopt it]** A table in `macro.md` comparing the solved steady state with
country data targets, each with a source column. Recurring moments: `D/Y`, `D_f/D`, `K_f/K`,
`K_f/Y`, `C/Y`, `(I+I_g)/Y`, `K/Y`, `I_g/Y`, `TR/Y`, `NX/Y`, `RM/Y`, `r`, PIT/Y, CIT/Y, `T/Y`. The
governing sentence: "most parameters are only weakly identified on their own, so the real test is
whether the steady state they jointly produce resembles the economy." Tier the rows: fiscal first,
then production, preference and earnings moments; `r` and `K/Y` against the PWT go in a ballpark
tier with a written reason.

## Moments most often tuned for but never scored

| Moment | Parameter it identifies | Source |
|---|---|---|
| `K_f/K` | `zeta_K` | IIP: inward DI equity + portfolio equity, ÷ GDP ÷ `K/Y` (gross reading; see macro-open-economy.md) |
| `(I + I_g)/Y` | `delta`, `alpha_I` | national accounts GFCF, private + public; `I_total` alone is private |
| `G/Y` | `alpha_G` | government final consumption. Score the solved value: the steady state forces spending to the budget-consistent level, so it will differ from your `alpha_G` input, and the difference is information |
| `NX/Y` | `zeta_K`, `zeta_D` | the trade balance, not the current account (below) |
| property / wealth tax / Y | `p_wealth`, `h_wealth` | revenue statistics |
| bequest tax / Y | `tau_bq` | revenue statistics |
| `w·L/Y` (solved labour share) | validates `gamma` and `epsilon` | PWT `labsh`. JPN solved 0.5700 against 0.571, a real free check, since nothing forces it when `epsilon != 1` |
| wealth Gini / top shares | the `e` matrix, `beta` | household wealth surveys. Distinct from the income Gini the tilt targets, and a much sharper test of an OG model |
| `g_n_ss` | the demographic window | the UN projection's own implied CAGR |

**[net-new: JPN]**

## Two traps when adding rows

- **Check whether the SS key is an aggregate or a per-household array.** `wealth_tax` and
  `bequest_tax` come back shaped `(S, J)`. Summing them gives a number with no units (OG-JPN got
  16.7 "of GDP"), which looks so wrong it gets discarded rather than debugged. Weight by `omega_SS`
  and `lambdas`, and sanity-check every new row against a plausible magnitude before believing a gap.
- **`NX` is the trade balance; the current account is a different object.** For a country with a
  large net international investment position, most of the current account is primary income, not
  trade. Japan's CA surplus is ~3.8% of GDP against a goods-and-services balance near zero, so a model
  `NX/Y` of 0.000 is right, and scoring it against 3.8% would be a concept error.

## Revenue by instrument

Do not just check total tax/GDP. Check PIT, CIT, VAT and payroll each against collections.
Offsetting errors can make the total look right while the composition is wrong.

## Sourcing hierarchy for the data side

Actively search for the most authoritative source that exists. Never fill the dashboard from memory,
and never treat any source list, including this one, as closed. A wrong data anchor silently fails
an otherwise correct calibration, so treat the data column as carefully as the model column. For each
moment, search in descending order of authority and stop at the highest rung that has the number:

1. **The official national institution that owns the number**, the agency that administers it:
   revenue service for collections; treasury or finance ministry (budget review, fiscal framework,
   debt bulletin) for spending, debt and debt service; statistics office for GDP by industry, HFCE
   and the labour force survey; central bank (quarterly bulletin, IIP) for external and monetary
   data. Names differ by country, so search by role ("who administers this number here?"), and expect
   ministries, debt-management offices, planning commissions or social-security agencies you did not
   know existed. Their publications outrank everything else.
2. **Official international compilations of national data**: IMF (Article IV statistical appendix,
   GFS, WEO), World Bank, UN, ILO, PWT. Often the same national numbers, re-published with a lag on
   standardized definitions (useful for cross-checks, weaker on vintage). For the whole revenue side,
   the **OECD Revenue Statistics country note** (Asia-Pacific / LAC / Africa editions, free 4-page
   PDFs) is the single best table in the family's experience **[PHL]**: every instrument as % of GDP
   on one accrual basis and one GDP vintage (PIT, CIT, SSC, VAT, excises, customs, an "other taxes"
   residual). Pair it with the treasury's cash-operations report for non-tax revenue, interest
   payments and the actual primary balance.
3. **Regional development banks and bodies**: AfDB/ADB/IADB/EBRD country diagnostics, regional
   statistical commissions. They often carry country detail (sector data, informality, fiscal risk)
   that neither the national site nor the IMF publishes cleanly.

Typical role → moment map to start from: tax ratios ← revenue service tax statistics + budget
review; debt, foreign share, effective `r_gov` (debt service ÷ gross debt, deflated) ← budget review
or debt office; sector value-added shares ← GDP-by-industry release; household consumption shares ←
HFCE, expenditure survey or CPI weights; employment by industry ← labour force survey; `K/Y` ← PWT.
Re-check the load-bearing numbers against a second, independent source. When every rung comes up
empty, use the best lower-rung number, note the vintage, and mark the moment lower-confidence rather
than dropping it.

## Mind the GDP vintage

When the statistics office rebases GDP, every `x/GDP` ratio moves without anything real changing
(South Africa's 2021 rebasing shifted tax-to-GDP ~2.6pp: 23.7% on the rebased base vs 26.3% on the
old, same year). Compare model and data ratios on one consistent GDP vintage, and say which. A
calibration tuned to an old-vintage ratio looks ~2–3pp off against current data for no real reason.

## Read the model side from the solved pickles

Use `ogcore.utils.safe_read_pickle` on `SS_vars.pkl`; do not eyeball it. Fiscal ratios are revenue
lines over `Y`: PIT `iit_revenue/Y`, CIT `business_tax_revenue/Y`, indirect `cons_tax_revenue/Y`,
total `total_tax_revenue/Y`. `D/Y`, `D_f/D`, `K/Y` from the aggregates over `Y`; `r`, `r_gov`,
`factor` directly; consumption share as `p_tilde·C/Y` (never raw `C/Y` when `I > 1`). Transition
paths come from `TPI_vars.pkl`, parameters from `model_params.pkl`.

## Structural validation (multi-industry)

Check that a SAM or IO table reproduces the national accounts before building on it; see the
og-multi-industry-calibration skill.

## Consumption is a residual

**[net-new: JPN]** There is no consumption parameter: `C = Y − I − I_g − G − NX`, so a consumption
gap is identically the sum of the other gaps. Decompose it; each piece has its own cause. Related
trap: `I_total` in the SS output is private investment, while national-accounts GFCF is private plus
public. Compare `I_total + I_g`, or the gap is overstated by all of public investment.

## g_n is a path; the steady state uses its terminal value

**[net-new: JPN]** For a country mid-demographic-transition these differ a lot (JPN: −0.33% today,
−0.46% terminal), so a steady-state moment that depends on `g` (investment above all) will look wrong
against today's data even when the calibration is right. The honest comparison for "does this look
like the country now" is the early transition. Say which one each dashboard row scores.

## Pair the debt concept with the interest concept

**[net-new: JPN]** Where a government holds large financial assets, net and gross debt differ
enormously. Net debt pairs with net interest; gross debt with the effective rate on gross. The test
is whether `r_gov × D` reproduces the actual interest bill. Either pairing is defensible; mixing them
is not.

## Audit each instrument's base, not just its yield

**[net-new: JPN]** A right total can sit on a wrong rate applied to a wrong base, and only the base
test separates them. A rate tuned in-model to a revenue target on a base the model gets wrong gives
the right level and the wrong reform response. So size reforms by the revenue they must raise, not by
the rate change; that cancels the base error, because the same base appears in numerator and
denominator.

## Know the family traits before fixing them

The model's endogenous `K/Y` runs high against the PWT across the family (ZAF 4.5 vs 3.7; PHL 4.3),
a structural feature of the saving and return block, not a country calibration error. Report it with
a written reason in the ballpark tier; do not distort a country parameter to chase it. But before
calling any gap a trait, run the four lever rules in SKILL.md: JPN's "family trait" `K/Y` miss was an
untuned `zeta_K`.

## Note derived quantities honestly

"Net exports" is a balance-of-payments residual of the resource constraint (OG-Core has no trade
sector), not a modelled export or import.

## Verify both tails of every path

**[PHL, a caught error]** A min-only check on the debt path ("trough = 60.0, stays on target")
passed while the path climbed to 74%; the check tested only the direction the previous failure
pointed. For every path claim, report min and max with their years, and look at the plotted line
before writing the sentence about it.

## Fast value-pinning test

**[emerging: ETH; adopt it]** A `test_default_parameters.py` that loads the shipped JSON and pins
specific calibrated values with inline source citations, explicitly not asserting anything that needs
a solve. Keep it separate from the slow example smoke test. Pin documented decisions too (a gradient
deliberately left unset, a GS sub-threshold ETR bound, no `NEEDS TUNING` markers).

## Prevent doc/JSON drift with glue

**[emerging: ETH; adopt it]** A hidden code cell in the docs loads the packaged JSON and `glue()`s the
numbers (`{glue:text}`), so prose cannot drift from the shipped values.
