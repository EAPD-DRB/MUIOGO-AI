# OG-Core solve failure taxonomy

Observed classes from the family's real debugging history (`~/Projects/og-country-tests` scripts
and logs, the OG-ZAF fiscal-runaway work, and the calibration playbook). Signatures are literal
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
  country's actual. Full recipe: `og-country-calibration` → Fiscal consistency.
- **Provenance**: OG-ZAF TPI sims, proven; HSV's negative bottom-end ETR draining transition
  revenue contributed on ZAF (GS form with same targets converged).

## B. Binding constraint from a calibration placeholder

- **Signature**: `K_d has negative elements. Setting them positive to prevent NAN.` in the log
  (may still converge — OG-PHL logs show 3 occurrences then clean convergence); or transition
  breaks outright.
- **Cause**: `zeta_K` set to an undocumented high placeholder (the 0.9 case) or other open-economy
  dial forcing `K_d = B − D_d < 0`.
- **Remedy**: recalibrate the placeholder (Chinn-Ito-anchored `zeta_K` + cross-check). Treat the
  warning as a calibration smell even when the run converges.
- **Provenance**: OG-IDN hit and fixed the 0.9; OG-PHL `main` still ships it and its logs show the
  guard firing.

## C. Oscillation / slow outer-loop convergence

- **Signature**: TPI Distance bounces or decays very slowly; iteration counts high (observed
  spread: 23–39 iterations control vs 8–16 with adaptive damping/sparse Jacobian at equal or
  tighter final Distance).
- **Cause**: outer-loop damping too aggressive for the stiffness of the problem (multi-industry
  especially).
- **Remedy**: `TPI_NU` 0.4 → 0.3 → 0.2; Anderson (`TPI_outer_method="anderson"`, ogcore ≥ 0.16.4);
  continuation solve for multi-industry cold starts. These treat oscillation only — never class A.
- **Provenance**: ZAF nu sweeps (`logs_ogzaf_nu06/nu07`), IDN/PHL/ZAF control-vs-treatment logs.

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

## Known engine bugs to check before deep-diving (from the calibration playbook)

- TPI applies **year-0** compliance/filer values to the whole path's revenue accounting — a
  time-varying compliance reform shows behavior responding while revenue tracks baseline.
- `SS.py` tiles capital-noncompliance from the labor rate in the post-solve `mtry_ss` diagnostic —
  keep labor = capital noncompliance.
