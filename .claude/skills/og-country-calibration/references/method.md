# Method: moments, levers and the dashboard

How to find what moves a target moment before tuning anything, and why the transition must be
validated as well as the steady state.

## Step zero: write the equations down before you touch a parameter

Before tuning anything, produce a moment × lever table and commit it. Build it from the equations
OG-Core evaluates (`firm.py`, `aggregates.py`, `household.py`, `fiscal.py`, `tax.py`), not from
convention or this skill's tables. It takes under an hour and is the highest-value hour in a
calibration. For each target moment write:

1. **The closed form,** every symbol in it. Reproduce the solved value from your formula to 4
   decimals before trusting it. A mismatch means you read the wrong equation, and finding that out
   now costs minutes.
2. **Every parameter in it,** marked `sourced` / `tuned-to-<moment>` / `default-unexamined`.
3. **Which other moments share those levers.**

Worked example, `K/Y`, where convention names one instrument (`beta`). From `firm.get_r`,
`r = (1-tau_b)·p_m·MPK - delta + tau_b·delta_tau + inv_tax_credit·delta`, so under Cobb-Douglas:

```
K/Y = (1 - tau_b)·gamma / (r + delta - tau_b·delta_tau - inv_tax_credit·delta)

  gamma            sourced (PWT labour share)
  delta            sourced (CFC/K)
  tau_b            = cit_rate x c_corp_share_of_assets x adjustment_factor
                     c_corp_share_of_assets = 0.55 is a US default, and it is not
                     separately identified from adjustment_factor -- only the product is
  delta_tau        default 0.027 (US tax depreciation)
  inv_tax_credit   default 0.0
  r                not a parameter -- the household Euler pins the portfolio return r_p,
                     and r solves r_p = weighted avg of r (on K) and r_gov (on D).
                     So beta, sigma, g_y, debt_ratio_ss, r_gov_scale/shift,
                     zeta_K and world_int_rate are all levers on K/Y.

  shares levers with: C/Y (via I), I/Y, K_f/K, r
```

Write the tax terms in full; they are not small (on JPN they move the numerator 14% and the
denominator 3.5%), and `gamma/(r+delta)` sends you after the wrong lever. The table has eleven
levers; convention has one. A bigger stock of government debt forces capital to pay more, which
shrinks `K`, so `debt_ratio_ss` and `r_gov` are levers too.

**The table is also the tuning order:** sourced levers first, then tuned dials, then re-check
anything that shares a lever with what you moved.

## Finding every lever on a moment

The failure this prevents: OG-JPN's `K/Y` came in 0.20 below its PWT target. The `beta` that closed
the gap was one at which the steady state stopped solving. That was written up as an acceptable
miss and a "family trait". It was neither. `zeta_K`, at a placeholder 0.10 that the repo's own comment
labelled `NEEDS TUNING ... pending the IIP anchor`, closed 79% of the `K/Y` gap and 85% of a
separate consumption gap when set from the IIP data. Fourteen tuning rounds ran without touching it.

Four rules:

1. **Write the model's own closed form for the moment, then list its arguments** (Step zero). Not
   the conventional pairing.
2. **Every parameter ends in one of three states, and "placeholder" is not one:** sourced;
   tuned to a named moment; deliberately defaulted with a written reason. A `NEEDS TUNING` marker is
   a debt with an exit criterion: make it a release gate and a test that matches any wording of the
   marker (`NEEDS`, `TODO`, `PLACEHOLDER`), as OG-JPN's `test_no_unresolved_tuning_markers` does. The
   JPN comment even named the dataset; it shipped anyway, because nothing failed.
3. **Two moments that move together are one moment.** Check for shared levers before diagnosing
   either. JPN's consumption gap (+2.3pp) and `K/Y` gap (−0.20) were analysed separately for a whole
   calibration. They were the same gap: too little capital means too little investment, and
   `C = Y - I - I_g - G - NX` makes consumption absorb it. One lever closed both. Symptom-by-symptom
   tuning always finds a spurious "structural" residual.
4. **A lever that runs out of road is the wrong lever, not proof the gap is structural.** If the
   instrument needs a value that will not solve, or one outside its plausible range, go back to
   rule 1. Do not write "acceptable band"; that language launders an untuned parameter into a family
   trait.

**Then sweep the defaults you did not source.** Perturb every unsourced parameter and record which
target moments move. Anything that moves one materially must be sourced or explicitly declared.
Relevance depends on settings you have not chosen yet: `world_int_rate` (default 0.04) is invisible
at a low `zeta_K` and sets `r` at a high one; on JPN, dropping it to 3.5% moved `K/Y` from 3.67
to 3.81 and `K_f/K` from 17% to 27%. High openness hands the interest rate from the country's
households to an unsourced global constant. Run the sweep after the parameters settle. **[net-new: JPN]**

## Dashboard completeness

An unscored moment cannot pull its parameter. Every tuned dial needs its own scored moment; never
steer a dial to close a residual; score every resource-constraint component and the early
transition, not only the steady state. The four rules and their cases are in
[validation-dashboard.md](validation-dashboard.md). **[net-new: JPN]**

## Why the baseline transition is not optional

The steady state consumes one number from each time-varying
path (its terminal value), so a whole mis-specified path is invisible to it. On JPN a wrong
demographic window survived eleven steady-state rounds with every fiscal moment inside 0.2pp of GDP;
one transition run caught it.
