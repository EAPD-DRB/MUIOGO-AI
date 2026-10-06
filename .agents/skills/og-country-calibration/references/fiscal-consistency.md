# Fiscal consistency and the near-term fiscal path

Contents
- The budget identity (with pensions and UBI)
- Why it bites the transition, not the steady state
- Over-collecting taxes mask the inconsistency
- Progressive taxes expose what flat taxes hide
- Reconcile against the country's own fiscal plan
- A hot interest-growth differential forces spending too low
- Validation priority: the near-term fiscal path first
- Transition-path validation against the fiscal program
- The alpha_G glide
- A violent early-transition spike is a diagnosis
- Deliverable: the path panel

The single most destabilizing calibration error is a government budget that does not balance at the
debt target. The spending ratios (`alpha_G`, `alpha_T`), the revenue the tax system actually raises,
and `debt_ratio_ss` are independently set knobs that must satisfy one identity, or the transition
blows up. **[net-new: ZAF, proven by TPI simulations]**

## The budget identity (with pensions and UBI)

For debt to hold at `debt_ratio_ss` in the steady state, the government must run a primary balance

```
pb* = (r_gov − g)/(1 + g) · debt_ratio_ss,     g = e^{g_y}(1 + g_n_ss) − 1
```

where `g` is the model's real, detrended growth and `r_gov` the steady-state real sovereign rate.
Primary spending must equal revenue − `pb*`, and primary spending includes public investment,
pensions and any UBI. `fiscal.get_G_ss` subtracts all of them:

```
alpha_G + alpha_T + alpha_I + agg_pension_outlays/Y + UBI_outlays/Y  =  revenue/Y − pb*
```

- Forgetting `alpha_I ≈ 0.05` mis-sets `alpha_G` by 5pp of GDP. **[PHL]** Check `alpha_I` itself is
  sourced: OG-ZAF's `main` ships 0.0003, a placeholder. **[ZAF]**
- Omitting pensions sets `alpha_G` too high by the whole pension bill (JPN: 0.63pp of GDP).
  **[net-new: JPN]** UBI is usually zero; include it when it is not.
- **The steady state will not tell you.** The closure forces `G` to the consistent level, so the
  steady state solves and reports a `G/Y` below your `alpha_G` input. That silent gap between input
  and solved `G/Y` is the diagnostic; read it every solve. The transition has no such closure for
  the first `tG1` periods, so it over-spends the full error.
- Set the spending side from the identity; do not inherit it. With `r_gov < g` (common for emerging
  markets after an honest `r_gov` re-anchor), `pb*` is negative: the country stabilizes debt while
  running primary deficits, which usually matches its fiscal history.
- **Frame the residual honestly.** After capturing all recurring revenue, the remaining gap between
  model `G/Y` and observed government consumption should be about (actual primary balance − `pb*`),
  the country's real consolidation distance, plus measurement differences. Name it in the docs as
  what the stable-debt steady state embeds. (PHL: actual pb −2.8% vs `pb*` −0.7%, so ~2pp embedded
  consolidation.) **[ZAF; the alpha_I identity and consolidation-gap framing: PHL]**

## Why it bites the transition, not the steady state

OG-Core's steady-state closure forces spending to the consistent level to hit the debt target, so
the steady state always solves and looks fine. The transition holds `alpha_G + alpha_T` at their
input values for the first `tG1` periods before the closure adjusts. If input spending exceeds the
consistent level, debt balloons before the closure corrects it violently. With a debt-elastic
premium on, the overshoot feeds the convex premium and the TPI runs away (debt → ∞). Symptom: the
steady state solves, the baseline transition diverges or overshoots wildly. Damping and better
solvers, Anderson included, do not fix it: it is a real fiscal runaway, not a convergence artifact.

## Over-collecting taxes mask the inconsistency

Audit revenue by instrument. A flat or placeholder tax rate set too high, or a leftover tax
parameter, inflates revenue and accidentally balances an over-set spending side; the model looks
stable until you fix the tax. Two ZAF examples that hid a ~3%-of-GDP spending > revenue gap:

- a flat PIT collecting ~16% of GDP when actual PIT is ~10% (a flat rate on everyone over-collects
  against a progressive schedule);
- a spurious `tau_bq = 0.2` collecting 3.9% of GDP when the country has negligible estate duty and
  the docs said bequest tax was zero (doc/JSON drift).

Check every revenue line against actual collections by instrument (PIT, CIT, VAT + fuel, excise and
customs; `tau_c` should capture all consumption and indirect taxes, not VAT alone; payroll, bequest,
wealth), and grep the JSON for nonzero taxes the docs claim are off.

## Progressive taxes expose what flat taxes hide

A flat rate raises revenue in proportion to income and is robust along the transition; a progressive
schedule's revenue is far more sensitive. A spending > revenue gap a flat tax papered over will
destabilize the transition once you switch to a progressive (GS/HSV) form. Do not blame the
progressive form; check the fiscal balance first.

## Reconcile against the country's own fiscal plan

Pull the primary-balance path and debt trajectory from the IMF Article IV / DSA and the national
budget. If the country actually runs `pb*` (stable or declining debt), the model's steady state
matches current policy. If it runs a deficit and rising debt (common), the stable-debt steady state
is the country's targeted, post-consolidation state: set spending to the consistent (lower) level and
document it as such, rather than matching today's higher actual spending. Confirm the debt is
local-currency and rollable (usually low default risk), so the stable-debt steady state is a
modelling device, not a solvency claim.

## A hot interest-growth differential forces spending too low

If the model's real `(r_gov − g)` exceeds the country's actual, `pb*` is inflated and consistent
spending drops below real spending. Diagnose both legs:

- `r_gov`: the LMWW wedge shift `μ_d` is a cross-country EM average. Check it against the country's
  actual real effective borrowing rate (nominal debt service ÷ gross debt, minus inflation).
- `g`: a `g_y` from a stagnant realized window understates a country whose debt path assumes
  medium-term potential growth. The steady state is long-run, so a forward-looking `g_y` can be the
  honest choice.

Bringing `r_gov − g` in line lets spending sit at a realistic level. **[net-new: ZAF]**

## Validation priority: the near-term fiscal path first

This reverses how most of the family works. The steady state is a destination decades out that
nobody will live in. The near-term fiscal path is the more believable test, and it should be built
and scored with the steady-state dashboard, not after it:

- **It is checkable against what happened.** Debt, primary balance and revenue for recent years are
  published, and the next few are projected by the IMF/OECD and the country's medium-term fiscal
  framework. A model that reproduces them is credible in a way a stylised long run never is.
- **It is the only test that can see the debt level.** In the steady state `D/Y` is
  `debt_ratio_ss`, a policy anchor you chose, so scoring it there compares a choice against a
  measurement. `initial_debt_ratio` is a measurement, and only the transition starts from it. JPN
  shipped `initial_debt_ratio = 0.864` against an actual 1.148, a 28pp-of-GDP error, for a full day,
  in a file whose own `r_gov` derivation used the correct 114.8%. The steady-state dashboard could
  not catch it; a debt-path panel would have shown it in period one. **[net-new: JPN]**
- **It is where a fiscal miscalibration bites.** The steady-state closure protects the steady state;
  the transition holds `alpha_G`/`alpha_T` at their inputs for `tG1` periods.

Both dashboards are required; the path is the one next year's data can falsify.

## Transition-path validation against the fiscal program

**[PHL, net-new; JPN, promoted to first rank]** Compare the baseline TPI paths of the fiscal
variables with the country's published program and international projections, over the first
~10–15 years (model from `TPI_vars.pkl`):

- primary balance (`total_tax_revenue − total_primary_government_outlays`)/Y vs the treasury's
  actual primary balance and the medium-term program's (deficit path less programmed interest);
- `D/Y` vs actual debt ratios and the program's trajectory or targets;
- total revenue/Y vs the program's revenue effort, with a stated concept bridge (model revenue is
  general-government accrual plus captured non-tax; national-government cash programs need a wedge:
  derive it from one overlap year of OECD-vs-treasury data and hold it constant);
- `I_g/Y` vs the program's infrastructure path.

Sources: the medium-term fiscal framework (deficit, revenue, disbursement and infrastructure paths),
the budget document (interest projections, to convert deficit to primary), treasury
cash-operations reports (actuals).

## The alpha_G glide

Put the transition on the government's consolidation schedule. A flat identity-value `alpha_G` makes
the model consolidate at once (pb jumps to `pb*` in year one, typically years ahead of the actual
plan), which pays debt far below target early (PHL: down to ~48% vs a 58–61% program band) before
the closure brings it back. Instead set `alpha_G` as a declining path:

```
alpha_G(t) = SS_revenue_share − pb_program(t) − alpha_T − alpha_I(t)
```

for each program year, capped at the identity-consistent value from the year the program's primary
balance crosses the model's `pb*`. Do not chase extended-projection years tighter than `pb*`; that
re-introduces the undershoot. The steady state is untouched (the closure ignores `alpha_G`); only
the transition's stance changes. If the program's own consolidation converges to `pb*` near the end
of the program window, the steady state is literally where the government's plan is headed: say so
in the docs. Re-tune the glide after fixing the initial-wealth condition.

## A violent early-transition spike is a diagnosis

A one-to-two-year consumption or consumption-tax-revenue pulse at the start of the baseline is the
fingerprint of the imposed initial-wealth condition (macro-open-economy.md, "Initial household
wealth"). Check the B_ss/B0 scale factor and fix it before labelling anything benign. (An earlier
version of this skill advised documenting the spike as "transition dynamics"; that normalized a
fixable artifact.) What legitimately remains after the fix: convergence from a non-stationary
initial age distribution and capital stock, and, under a fiscal glide, early growth above its
long-run value, which erodes the debt ratio before the arithmetic tightens. Never tune fiscal
parameters against whatever residual is left.

## Deliverable: the path panel

A small multi-panel figure (debt ratio, primary balance, revenue, public investment; model line vs
actual dots vs program markers) committed to the docs images, with a caption naming every source,
referenced from the macro chapter's validation section. Set axis limits that show the model's full
path; clipping the divergence you are testing for defeats the exercise. For every path claim report
min and max with their years (validation-dashboard.md, "Verify both tails").
