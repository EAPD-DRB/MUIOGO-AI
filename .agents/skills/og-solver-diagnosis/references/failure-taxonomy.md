# OG-Core solve failure taxonomy

## Contents
- A. Fiscal runaway · B. Binding constraint from a calibration placeholder · C. Oscillation
- D. Basin flip · E. NaN propagation · F. Stale expected-output fixture · G. Infrastructure noise
- H. Cold-start seed failure · I. Resource-constraint error by timing · J. Single-threaded run
- K. Government rate at its floor · L. Slow steady state on older ogcore
- M. Unsolved start cohorts · Known engine bugs

Observed classes from the family's real debugging history (its test scripts and solve logs, the
OG-ZAF fiscal-runaway work, and the calibration playbook). Signatures are literal
strings to grep for. When you hit a class not listed here, add it.

## A. Fiscal runaway (TPI debt divergence)

- **Signature**: SS solves cleanly; baseline TPI Distance grows or debt overshoots wildly; with a
  debt-elastic premium (`r_gov_DY2 > 0`) the run diverges to infinity. Damping and Anderson do
  NOT help — that is itself diagnostic.
- **Cause**: government budget does not balance at `debt_ratio_ss`: input `alpha_G + alpha_T`
  exceeds revenue − required primary balance. Over-collecting placeholder taxes (flat PIT set too
  high, spurious `tau_bq`) can *mask* it until a tax is fixed — then the "fix" seems to break the
  model.
- **Remedy**: audit revenue by instrument against actual collections; set spending to
  `Σrev/Y − pb*` where `pb* = (r_gov − g)/(1+g)·debt_ratio_ss`; check `r_gov − g` against the
  country's actual. Check the debt-elastic premium is centred: with `r_gov_DY2 > 0`, the
  premium should be zero at `debt_ratio_ss` (`r_gov_DY = -2·r_gov_DY2·D̄`, the constant folded
  into `r_gov_shift`). An uncentred premium adds points to `r_gov` at the target itself and
  inflates `pb*`, a runaway cause in its own right. Full recipe: `og-country-calibration` →
  fiscal consistency and the macro reference's debt-elastic premium section.
- **Provenance**: OG-ZAF TPI sims, proven; HSV's negative bottom-end ETR draining transition
  revenue contributed on ZAF (GS form with same targets converged).

## B. Binding constraint from a calibration placeholder

- **Signature**: `K_d has negative elements. Setting them positive to prevent NAN.` in the log
  (may still converge — OG-PHL logs show 3 occurrences then clean convergence); or transition
  breaks outright.
- **Cause**: `zeta_K` set to an undocumented high placeholder (the 0.9 case) or other open-economy
  dial forcing `K_d = B − D_d < 0`. The guard then floors `K_d` at `0.05·B` (`np.fmax` in
  `aggregates.get_K_splits`) while `K_f` keeps its unfloored value, so `K = K_d + K_f` no longer
  holds exactly in the saved output.
- **Remedy**: recalibrate the placeholder: tune `zeta_K` to the IIP-implied `K_f/K` level, with
  Chinn-Ito only as a prior (`og-country-calibration`). Treat the warning as a calibration smell
  even when the run converges.
- **Provenance**: OG-IDN hit and fixed the 0.9; OG-PHL fixed it later; its older logs show the
  guard firing (case notes: PHL).

## C. Oscillation / slow outer-loop convergence

- **Signature**: TPI Distance bounces or decays very slowly; iteration counts high (observed
  spread: 23–39 iterations control vs 8–16 with adaptive damping/sparse Jacobian at equal or
  tighter final Distance).
- **Cause**: outer-loop damping too aggressive for the stiffness of the problem (multi-industry
  especially).
- **Remedy**: the model owner's standing rule is Anderson (`TPI_outer_method="anderson"`) with
  `nu` 0.2 or lower on every run, so check those are set before anything else (field names can
  differ between ogcore releases).
  Then lower `nu` further (0.4 → 0.3 → 0.2 → lower); continuation solve for multi-industry cold
  starts. Watch the distance series on the first Anderson run and fall back to damped iteration
  if it oscillates. These treat oscillation only — never class A. Recent ogcore can tell a
  cycling loop from a diverging economy for you (solve-procedures.md, "Stall detection").
- **Variant: Anderson stalls just above `mindist_TPI`** **[KOR]**. Signature: the distance falls
  cleanly to a few times the tolerance, then rises for several iterations in a row (on KOR, from
  2.7e-5 to 4.9e-5 over five iterations, against 1e-5). With `maxiter` 250 it can run for
  hours, so stop it. Damped iteration (`TPI_outer_method="picard"`, `nu` 0.2) from the same
  calibration went through the same level and converged (case notes: KOR). The fallback is
  slower, so it can exceed the run rules' 5–7 minute guide without anything being wrong; record
  the iteration time.
- **Provenance**: ZAF nu sweeps (`logs_ogzaf_nu06/nu07`), IDN/PHL/ZAF control-vs-treatment logs;
  KOR run logs (`example_run_A.log`, `example_run_B.log`).

## D. Basin flip (two valid solutions, ill-conditioned Jacobian)

- **Signature**: two runs differing only in a numerically-tiny detail (dense vs sparse FOC
  Jacobian, a ~1e-10 Jacobian perturbation) converge to *different* answers, both satisfying the
  FOCs; per-cohort paths diverge for specific groups (observed: ZAF's low `e[:,:,0]` cohorts).
- **Cause**: near-flat ridge in the residual surface (small singular value) — Newton's basin of
  attraction flips under microscopic Jacobian differences. Demonstrated in isolation by the
  `ridge_demo*.py` toy systems.
- **Remedy**: identify the calibration block creating the ill-conditioning by substitution
  (swap in the OG-Core default for the suspect block — `test_zaf_substitute_e.py` pattern); then
  either recalibrate the degenerate block or accept and pin one solution with tighter seeds.
  A drift check (0.1% threshold) between dense/sparse belongs in any engine-change validation.
- **Provenance**: sparse-FOC-jac validation campaign; drift verdicts themselves were lost
  (console-only output — hence the log discipline rule).

## E. NaN propagation / crash inside the solve

- **Signature**: Python traceback; NaN in intermediate arrays; negative savings `b_sp1` before the
  NaN.
- **Cause**: usually an upstream bad value (degenerate `gamma_m` near 1 from an imputed-rent
  industry, broken e-matrix, wrong `country_id` demographics) reaching the household problem.
- **Remedy**: instrument to find the *first* bad value, not the last (monkey-patch tracing of
  `SS_solver`/`FOC_savings` — `diagnose_J1.py` pattern); then function-level bisection with fixed
  micro inputs. Fix upstream; `ENFORCE_SOLUTION_CHECKS=False` is a probe tool, never a fix.

## F. Stale expected-output fixture (test "failure", not model failure)

- **Signature**: a unit test comparing against a stored pickle fails after an engine or default
  change (`run_TPI_outputs_J1.pkl` case); the model's own runs look fine.
- **Remedy**: equivalent-config comparison (J=1 vs identical-types J=2 full paths within 1%) to
  prove the code is right; then regenerate the fixture deliberately — never regenerate first.

## G. Infrastructure noise

- **Signature**: Dask `Key lost during replication`, `solve_for_j ... cancelled ... Falling back
  to serial computation`; log ends mid-iteration with no completion line.
- **Remedy**: re-run before diagnosing anything; if it recurs, reduce workers / run serial. Do not
  read model meaning into a truncated log.
- **Provenance**: `logs_idn_control.log` (only log with the warnings, only incomplete log; its
  clean re-run converged normally).

## H. Cold-start seed failure (silent restarts)

- **Signature**: the SS seems slow, with many iterations, but the log shows the solve restarting
  from new initial guesses rather than converging slowly.
- **Cause**: the starting guess is too far from the solution. OG-Core walks down its list of
  `DEV_FACTOR_LIST` scalings and restarts each time, which reads as slow convergence. The
  savings seed is one constant across ages and types (hard-coded in older ogcore, a parameter
  in newer).
- **Remedy**: warm-start from a solved state (solve-procedures.md, "Warm-starting the steady
  state"). A guess that is near in values is not necessarily one the
  solver can start from: nearness is not solvability.
- **Variant: an inconsistent seed set, not a far one** **[KOR]**. ogcore derives the GDP guess as
  `initial_guess_TR_SS / alpha_T`. A repo bootstrapped from a sibling keeps the sibling's TR seed;
  against the new `alpha_T` the GDP guess lands several times too high. Signature: one GE-loop
  residual, the fifth (`Y`, after `r_p`, `r`, `w`, `p_m`), stuck large and negative (KOR −3.5,
  the guess 4.6x the solution) while the rest decay. Residual order, from `SS_fsolve`:
  `[r_p, r, w, p_m..., Y, BQ..., TR, factor]`. Remedy: set every `initial_guess_*` from the
  country's own last solve, then warm-start. Also note `SS_fsolve` divides the factor residual by
  1,000,000, so in a high-denomination currency measured in millions the factor's residual is
  near-invisible to the root-finder; seed it well.

## I. Transition-path resource-constraint error, read by when it occurs

- **Signature**: the baseline TPI resource-constraint error (`RC_error`) is not monotone in time.
- **Cause by shape**: large early and decaying → the initial wealth distribution or its target
  level is wrong; single-period spikes → an input discontinuity, often at
  the end of the demographic window (`fixper`); growing with debt → fiscal runaway (class A).
- **Remedy**: triage by shape before any tuning; fix the input, not the solver
  (solve-procedures.md, "Triage an RC_error by where in time it happens").
- **An error only at the very last period** points to the engine, not the calibration; check
  OG-Core's open issues before tuning anything to remove it.

## J. Single-threaded run mistaken for slow convergence

- **Signature**: a run takes far longer than the owner's ten-minute baseline, with a normal-looking
  log.
- **Cause**: no worker pool. The country examples always create one; ogclews-link's command line
  defaults to 7 workers, but a driver that builds `runtime.RunnerConfig` itself defaults to 1 and
  creates no pool.
- **Remedy**: check the worker count first: the country examples print "Number of workers"; an
  ogclews-link log does not, so check the command's `--workers` or the driver's `RunnerConfig`.
  Then re-run properly. Do not tune the solver.

## K. Government rate clipped at its floor

- **Signature**: `r_gov` sits exactly at a floor for some periods; fiscal paths look kinked.
- **Cause**: `fiscal.get_r_gov` floors the government rate (0.0 by default; settable as
  `r_gov_floor` in newer ogcore). A sovereign that pays negative real rates hits it.
- **Remedy**: set `r_gov_floor` below zero when the country's data supports it; record why.

## L. Slow steady state on an old ogcore

- **Signature**: the steady state takes many minutes with the workers mostly idle and the main
  process busy; the transition path then runs at normal speed.
- **Cause**: older ogcore re-sent the whole parameters object to the workers on every
  steady-state evaluation; newer versions send it once per solve.
- **Remedy**: check the ogcore version and its changelog first. On an old lock, say that the fix
  is an ogcore bump (its own change), not a solver setting.

## M. Unsolved start cohorts (households alive in the first year)

- **Signature**: a jump in consumption (or a drop in investment) in the first years of the
  transition, patchy by age and income group; those households' first-year labour equals the
  solver's seed exactly. The run converges and its reported Euler error is small.
- **Cause**: OG-Core solves households already alive at t=0 with `opt.root` and uses the result
  without checking it (PSLmodels/OG-Core#1247). The reported Euler error covers only cohorts born
  at t=0 or later, so the failures are invisible. On KOR, solving those cohorts moved year-two
  consumption from 62.9% to 50.5% of GDP (case notes: KOR). It looks exactly like an
  initial-wealth problem.
- **Remedy**: check whether your ogcore has the fix (a `_solve_household` retry and a reported
  "cohorts alive at the start" Euler error in the log). If not, recompute those cohorts'
  first-order conditions from the saved path before changing any initial-wealth setting.

## Engine bugs seen before (check whether your ogcore still has them)

- `get_pop_objs` builds the last data year with the frozen rates while storing the previous year's
  rates for it, and switches to the fixed population at `fixper` in one period. These are the two
  single-period spikes of class I. Check the population law of motion (og-country-calibration,
  households-demographics, "Discontinuities") before accepting them.

- TPI applies **year-0** compliance/filer values to the whole path's revenue accounting — a
  time-varying compliance reform shows behavior responding while revenue tracks baseline.
- `SS.py` tiles capital-noncompliance from the labor rate in the post-solve `mtry_ss` diagnostic —
  keep labor = capital noncompliance.
