# Alignment, solving and checking

inputs.md builds the inputs. This file keeps the single- and multi-industry models describing the
same economy, gets the multi model to solve, and checks the result. Much of it comes from OG-PHL's
practitioner guide (`docs/single_multi_calibration_guide.md` on its multi-industry branch), which is
worth reading whole.

"Broad agreement" means: the same reform run through both models gives the same signs and similar
magnitudes; shared data targets bind identically; remaining gaps are known and explained. Not
equality.

Contents
- How OG-Core treats industries
- Direction A: trust the single, build the multi
- Direction B: trust the multi, set the single
- The chi units conversion
- The Z level
- The equivalence test
- Reaching the steady state
- Checking the solved model
- Fault-finding
- When OG-Core changes
- Tests worth having

## How OG-Core treats industries

Check these against the ogcore you run; the multi-industry design is still being extended upstream.

- **The last industry is the numeraire and the only non-consumption producer.** Prices are
  normalised by it, and all non-consumption demand (private and public investment, government
  consumption, net capital outflows, remittances, aid) lands on it. Its nominal output share is
  therefore inflated and never comparable to a value-added share. Industries 1..M−1 produce only
  consumption goods.
- **Consumption mapping.** `alpha_c` (length I, sums to 1) are Cobb-Douglas budget shares;
  `io_matrix` (I × M) maps goods to industries through `io_matrix.T @ C`. `tau_c` is per good;
  `cit_rate`, `gamma`, `gamma_g`, `epsilon`, `Z`, `delta_tau_annual`, `inv_tax_credit` per industry.
- **One wage, one depreciation rate** (the last industry's); households do not choose a sector, so a
  formal/informal wage gap is not representable without extending OG-Core.
- **The composite consumption price is unnormalised:**
  `p_tilde = prod_i ((1 + tau_c_i) · p_i / alpha_c_i)^alpha_c_i`. It carries a units constant
  `k = prod_i alpha_c_i^(−alpha_c_i)` (1 when I = 1; 2.97 for PHL's five goods). Because `chi_n` and
  `chi_b` are fixed numbers, this changes behaviour, not just units.
- **The TFP level is not a free normalisation in an open economy.** With the world interest rate as
  an absolute anchor, scaling every Z moves the real wage relative to the world return, hence saving
  against foreign inflows, hence `r` and `K_f/K`. These models are open.
- **`factor` ties both models to the same currency data** (`factor = mean_income_data / model mean
  income`). With `mean_income_data` shared, the two solved factors should nearly match, which makes
  `factor` the best single number for spotting a level misalignment.
- **No `io_matrix` row-sum check.** The description says rows must sum to 1; nothing enforces it.
- **Steady-state guesses start every industry price at 1**, and the built-in fallback retries scaled
  `r` and `TR` guesses, not a homotopy. A reform warm-starts from the baseline only when the shapes
  match.

## Direction A: trust the single, build the multi

1. **Economy-wide values come from the base**, verbatim: demographics, preferences, fiscal ratios,
   open-economy dials, `g_y`, statutory rates. The two-step load does this; any difference is a bug.
2. **`gamma_m`:** keep the data's dispersion, impose the single's level (inputs.md).
3. **`Z_m`:** relative values from data, last industry = 1. Test whether the level needs moving;
   do not assume (below).
4. **Convert `chi_n` and `chi_b`** for the units change (below). In PHL this was the lever that
   mattered.
5. **What the data do not identify stays uniform** at the single's value (inputs.md).
6. **Identities:** `alpha_c` sums to 1, `io_matrix` rows sum to 1.
7. **Solver seeds: one set, in the base, shared.** The multi's continuation anchor (flat `gamma`,
   Z = 1) is the shared aggregate economy and cold-starts from the base seeds. If they are stale,
   the anchor fails exactly as the single would. The anchor's own solved `r`, `TR` and `factor`
   reproduce the seeds to within a few percent, so the multi can refresh them. Never give the
   overlay its own copy.

## Direction B: trust the multi, set the single

1. Economy-wide values: same rule.
2. **`gamma`** = VA-weighted arithmetic mean of `gamma_m` (shares aggregate additively).
3. **`Z`:** decide which model owns the level. If the multi's level is a numeraire convention (it
   usually is), keep the single at Z = 1 and treat the multi as the adjustable side. If the multi's
   level was anchored to data, set the single's Z to the VA-weighted geometric mean of `Z_m`. One
   owner; two conventions make two economies.
4. **Rates the multi differentiates:** aggregate with matching weights (output-weighted CIT,
   consumption-weighted `tau_c`).
5. **Retune the single's solver seeds** to its own steady state; it cold-starts from them.
6. **A change to the single's `gamma` (or any structural value) is a sourced-parameter change in
   the single model.** Every dial it tuned against the old value (the tax dials, `beta`, `zeta_K`)
   needs re-tuning, in og-country-calibration's order; then re-solve both models in the same
   change.

## The chi units conversion

Moving from one good to several shrinks composite-consumption units by k while `chi_n` and `chi_b`
stay fixed. Invariance of the household first-order conditions gives the exact fix: scale both by
`k^(σ−1)` in the overlay, computed by the builder from `alpha_c` and the base `sigma`. Derived, not
fitted; pin it in a test.

PHL (k = 2.97, σ = 1.5, scale 1.72):

| | single | M=8 before | M=8 after |
|---|---|---|---|
| r | 0.0708 | 0.0885 | 0.0808 |
| K_f/K | 0.257 | 0.528 | 0.336 |
| B/Y | 3.67 | 2.38 | 3.29 |
| K/Y | 4.29 | 4.02 | 4.24 |
| p_tilde·C/Y | 0.510 | 0.471 | 0.496 |

It closed 44–80% of each gap; the rest are composition effects. Side effects to expect: aggregate
labour moved from +7.7% to −5.8% relative to the single, and `factor` drifted 4.7%.

PHL's composite-price experiment (two identical industries) separates two problems. Investment
landing only on the numeraire industry is small. The units effect is large, and the chi-converted
run matches a run with a normalised price index to every digit. So the conversion is exactly a
correction for the unnormalised index: if OG-Core ever normalises it, the conversion must come out
of every overlay in the same change, or it double-corrects.

## The Z level

The last-industry = 1 convention pins relative TFP and leaves the level free. Two different uses;
keep them apart:

- **To close `r` or `K_f/K` gaps: no.** It is a weak and sometimes wrong-signed lever (PHL: an 11.7%
  rise moved `r` up 17bp). Check the chi conversion first.
- **To align `factor` with the single: yes, if needed.** It sets the incomes at which the
  progressive tax functions are evaluated, so a factor gap mis-collects PIT; `r`, `r_gov` and `K/Y`
  barely move. Whether the convention lands `factor` close is luck: PHL 0.02% (no rescale); ZAF 23%
  off, fixed by a common Z multiplier of 0.865 found by a log-log root-find on the solved `factor`
  (two or three solves, slope about 1.8).

## The equivalence test

With identical industries (flat `gamma` at the single's value, Z = 1, `gamma_g` = 0), the multi
model must reproduce M=1 to solver precision: `r`, `w`, total K and L, nominal consumption, every
`p_m` = 1 (BRA: relative 1e-8). It is the cleanest proof the plumbing (overlay, chi conversion,
mapping) is right, and it isolates calibration effects from structure. It holds exactly only at
`gamma_g` = 0, because public capital enters each industry's production non-rivalrously; say so
in the test. Mark it `local` if it is slow.

## Reaching the steady state

**Try a cold solve first** from the base seeds. It works when relative prices stay near 1 (ZAF's
M=8, about two minutes). It fails when they spread widely, because OG-Core starts every price at 1
and its fallback only rescales `r` and `TR` (PHL prices span 0.4–3.3, BRA 0.13–2.09).

**Continuation** (PHL and BRA, `solve_ss_by_continuation` in the example):

1. Solve a flat anchor as the baseline: `gamma` at the private mean, Z = 1, `runner(...,
   time_path=False)`.
2. Morph toward the calibrated values, `gamma(t) = (1−t)·anchor + t·target` and the same for Z,
   jointly. Each step is a reform whose `baseline_dir` is the last good step, so the previous steady
   state warm-starts the next.
3. Adapt the step: start around 0.125, multiply by 1.5 on success (cap 0.25), halve on failure, stop
   with an error below about 0.01.
4. **Baseline transition:** copy the final `SS_vars.pkl` into `OUTPUT_BASELINE/SS`, write
   `model_params.pkl`, and call `TPI.run_TPI` directly; the calibrated steady state cannot be
   re-solved cold. The reform then uses `runner(time_path=True)` with the usual baseline warm start.

BRA's continuation takes about two minutes; baseline plus reform take tens of minutes.

**Solver settings:** Anderson (`TPI_outer_method = "anderson"`) with `nu` 0.2, in the overlay. Stiff
multi-industry transitions are where damping alone fails: PHL's baseline took 25 outer iterations at
0.2 and 70 at 0.4, where the reform stalled. Neither setting fixes a fiscal runaway
(fiscal-consistency.md).

## Checking the solved model

**Structural checks after every solve** (PHL's and BRA's `validate_ss`): every `Y_m`, `K_m`, `L_m`,
`p_m` positive; `p_m[-1]` = 1; `r` in a sane band; `K/Y` in a sane band; output shares sum to 1.

**Comparison dashboard against the single:**
- *Must match* (targets and policy): `D/Y`, `D_f/D`, tax rates, transfer and spending shares.
- *Close* (single-digit %): `K/Y`, `p_tilde·C/Y`, aggregate `L`, `factor`.
- *Ballpark with a written reason* (1–2pp on rates, 10–15% on ratios): `r`, `r_p`, `K_f/K`, `B/Y`.
  The multi usually sits a little higher on `r` and the foreign share; know why.
- *Never compare raw:* Y, w, C levels (different units); raw C/Y in the multi; the numeraire
  industry's nominal output share.

**Against data:** sector value-added shares, employment shares, the consumption basket, and the
fiscal moments the single model targets. BRA also checks how well the model's labour allocation
tracks the table's labour income by industry (correlation 0.86).

**Same reform through both models:** same signs, similar magnitudes in the percent-change tables.
Run the same reform in both examples; PHL's single and multi examples ran different reforms, which
makes the comparison impossible.

**Interpretation caveats to state:** the numeraire industry's inflated nominal share; `L_m` is in
efficiency units, not heads; exact M-invariance only at `gamma_g` = 0.

## Fault-finding

- `r` and `K_f/K` both too high in the multi → the chi conversion, first.
- `K/Y` off → the `gamma` rescale or its weights drifted.
- `C/Y` off → you compared raw C/Y, or the `alpha_c`/`tau_c` mapping changed.
- `factor` off → a level misalignment upstream; fix it before anything else.
- Everything off after a recalibration → shared values did not propagate. Re-solve both models in the
  same change, and update any numbers one model's docs quote about the other.
- Cold solve fails → continuation, not seed tuning.
- One industry's Z wildly out of line → its employment number.
- A transition oscillates or stalls → solver settings above; a runaway → the fiscal block.

## When OG-Core changes

The multi-industry design is still being extended upstream: letting several industries supply
government and investment goods, and fixing the composite price index. Before building, look at
open OG-Core work touching `io_matrix`, `get_ptilde` or the numeraire, and plan for:

- **A normalised price index** removes the units constant. Remove the chi conversion from every
  overlay and regenerate in the same change.
- **A taller `io_matrix`** (extra rows saying which industries supply government consumption, public
  investment and private investment). Existing overlays fail validation until extended. To keep
  today's behaviour, the new rows are unit vectors on the last industry (`[0, …, 0, 1]`). Choosing
  other rows is a new calibration from the use table's final-demand columns, and it removes the
  "last industry absorbs everything" caveat.

## Tests worth having

- The overlay holds exactly the intended keys; the packaged JSON equals the builder's output.
- The two-step load keeps base values intact (`debt_ratio_ss`, `zeta_K`, ...).
- The chi conversion equals base × k^(σ−1).
- The concordances cover the data exactly.
- `io_matrix` rows sum to 1; `alpha_c` sums to 1; Z of the last industry is 1.
- Sanity bounds on derived values (`gamma` in (0, 1); energy row mostly electricity; agriculture
  CIT lowest).
- The equivalence test.

None of the repos yet tests the continuation solve, the example, or the calibrated steady state
against data. Say so in the PR rather than implying coverage.
