# Method: moments, levers and the dashboard

Contents
- Step zero: write the equations down before you touch a parameter
- Finding every lever on a moment
- Sweep the defaults you did not source
- Diagnosing a gap that will not close
- Why the baseline transition is not optional

Each lesson gives the rule, the check, why, and where it was learned (`[CODE]`; the case is in
`lessons/<CODE>.md`).

## Step zero: write the equations down before you touch a parameter

**Rule.** Before tuning, write a moment × lever table from the equations OG-Core evaluates
(`firm.py`, `aggregates.py`, `household.py`, `fiscal.py`, `tax.py`), not from convention. For each
target moment: its closed form, every parameter in it marked sourced / tuned to a named moment /
defaulted with a reason, and the other moments that share those parameters. The table is also the
tuning order: sourced levers first, then tuned dials, then re-check what shares a lever with what
you moved.

**Check.** Reproduce each solved moment from your closed form to four decimals before trusting it;
a mismatch means you read the wrong equation.

**Worked example, `K/Y`** (single industry, `epsilon` = 1, output price 1). From `firm.get_r`,
`r = (1 − tau_b)·MPK − delta + tau_b·delta_tau + inv_tax_credit·delta`, so

```
K/Y = (1 − tau_b)·gamma / (r + delta − tau_b·delta_tau − inv_tax_credit·delta)

  gamma            sourced (capital share)
  delta            sourced (private CFC / private K)
  tau_b            = cit_rate × c_corp_share_of_assets × adjustment_factor_for_cit_receipts
                     (only the product is identified)
  delta_tau        tax depreciation (default a US value)
  inv_tax_credit   default 0
  r                not a parameter: households' saving and the open-economy block set it.
                     Households earn r_p, an average of the owners' return on capital
                     r + (1 − tau_b)·MPK_g·K_g/K and the government rate r_gov on debt
                     (aggregates.get_r_p). So beta, sigma, g_y, debt_ratio_ss,
                     r_gov_scale and r_gov_shift, zeta_K and world_int_rate all move K/Y.

  shares levers with: I/Y, C/Y, K_f/K, r
```

Write the tax terms in full; they can move the ratio by more than ten percent, and `gamma/(r +
delta)` points at the wrong lever. Convention names one lever for `K/Y` (patience); the table has
about a dozen. [JPN]

## Finding every lever on a moment

**Rule.**
1. Write the model's own closed form for the moment and list its arguments, not the conventional
   pairing.
2. Leave every parameter in one of three states: sourced; tuned to a named moment; defaulted with a
   written reason. A placeholder is open work: a marker such as `NEEDS TUNING`, `TODO` or
   `PLACEHOLDER` fails a test before release.
3. Treat two moments that move together as one gap and look for their shared lever before
   diagnosing either: too little capital means too little investment, and consumption, the
   residual, absorbs it.
4. A lever that runs out of road (a value that will not solve, or one outside its plausible range)
   is the wrong lever, not proof that the gap is structural. A parameter stuck at its bound usually
   means another input is wrong or a mechanism is missing; read it economically (units first, then
   the economics) before widening the bound or asking for an OG-Core change.

**Why.** A capital-output miss written up as a family trait was a foreign-capital share left at a
placeholder for fourteen rounds; setting it from data closed most of that gap and of a separate
consumption gap. A labour-disutility bound that looked binding was units; a patience bound was a
real signal. [JPN, ETH]

## Sweep the defaults you did not source

**Rule.** After the inputs settle, perturb every unsourced parameter and record which target
moments move; source or explicitly declare anything that moves one materially.

**Why.** Relevance depends on settings chosen later: the world rate is invisible at a low
`zeta_K` and sets `r` at a high one. [JPN]

## Diagnosing a gap that will not close

**Rule.** Before reaching for a lever, decompose the gap with identities the model and the data
share: investment = domestic saving + net foreign financing; the current account from flows against
the change in foreign liabilities. The missing half names the lever (saving: patience and
preferences; foreign financing: `zeta_K`, external debt, payments abroad). Measure the candidate
channels in today's data, not in the country's history, then probe each once, at a bound, on the
transition, recording what it buys and what it costs on the other moments.

**Check.** The identities close on both sides (validation-dashboard.md) before any lever moves.

**Why.** A misread consumption series made a saving gap look like a financing gap, and a week went
to the capital share, the state, `zeta_K` and state-enterprise loans before the decomposition
showed it was household saving. [ETH]

## Why the baseline transition is not optional

The steady state uses one number from each time-varying path (its last value), so a whole
mis-specified path is invisible to it, and so is the measured starting point (debt, wealth,
population). Validate the baseline transition with the fiscal path panel and the early-year
dashboard rows. A wrong demographic window survived eleven steady-state rounds with every fiscal
moment within 0.2 points of GDP; one transition run caught it. [JPN]
