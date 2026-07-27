---
name: og-solver-diagnosis
description: >-
  Structured diagnosis protocol for OG-Core solver trouble: a steady-state (SS) or transition-path
  (TPI) solve that does not converge, diverges, oscillates, crashes, runs away (debt → ∞), throws
  NaN/negative-value warnings, or converges to a suspicious answer; also for dense-vs-sparse or
  control-vs-treatment result drift and failing expected-output tests. Use it BEFORE touching any
  solver knob (TPI_NU, maxiter, Anderson) or proposing a fix — the protocol finds the root cause
  first. Applies to OG-USA/PHL/ZAF/IDN/BRA/ETH and ogclews-link runs.
---

# OG solver diagnosis

Adapted from obra/superpowers `systematic-debugging` (MIT — credit: https://github.com/obra/superpowers),
specialized to OG-Core solves with the failure classes and bisection patterns actually used in this
model family (mined from `~/Projects/og-country-tests`).

**The iron law (inherited): no fix without root-cause investigation first.** Solver knobs are
Phase 4, not Phase 1. Most "solver failures" in this family were not solver failures — they were
fiscal inconsistencies, calibration placeholders, or the wrong code running.

## Phase 0 — Rule out contamination

If the failing result is surprising, or reproduces a previously-known-buggy number: suspect the
wrong code ran before suspecting the model. Run the `og-run-preflight` skill's checks (branch+HEAD,
import resolution, venv). Only continue here once the environment is proven clean.

## Phase 1 — Read the log, characterize the failure

Read the actual solve log before forming any theory. Extract, with grep:

```bash
grep -n "Iteration\|Distance" <log> | tail -20     # convergence trajectory
grep -n "K_d has negative\|Traceback\|RuntimeError\|Key lost\|Falling back" <log>   # known signatures
grep -n "Time path iteration complete\|SS fsolve" <log>   # did it actually finish?
tail -30 <log>
```

Beware the benign-label trap: a naive `grep -i "error"` drowns in `GE loop errors = [...]` and
`Max Euler error` lines, which are per-iteration diagnostics, not failures (verified on the PHL
logs). Grep for the specific signatures above; use the GE-loop-errors *trajectory* (decaying vs
growing) as data, not as an alarm.

Characterize which of these you have — they have different causes:

- **Diverging**: Distance grows monotonically. Think fiscal runaway or a broken calibration, not
  damping.
- **Oscillating / stalling**: Distance bounces or plateaus above `mindist`. Damping/acceleration
  territory — but only after Phase 2.
- **Crash / NaN**: read the full traceback; find the first NaN, not the last.
- **Converged but wrong / drifted**: two runs both satisfy the FOCs with different answers —
  see basin flips in the taxonomy.
- **Warnings then convergence** (e.g. `K_d has negative elements. Setting them positive`): the
  run "succeeded" but is telling you a constraint bound — a calibration smell, triage it.
- **Infrastructure noise** (Dask `Key lost during replication`, `Falling back to serial`): not a
  model failure; re-run before diagnosing anything.

Then classify against `references/failure-taxonomy.md` (read it now — it lists the observed
classes, their signatures, and the known remedy for each).

**Log discipline (a real loss happened without it):** every diagnostic run redirects stdout+stderr
to a named log (`logs_<pkg>_<variant>.log`), and the script echoes its exact settings (nu, mindist,
flags) into the log at startup. In the mined history, the decisive drift verdicts were printed to
an interactive console and never captured — the conclusion of days of work is unrecoverable. Also
don't trust filenames: a log named `nu06` was found printing a different variant's label.

## Phase 2 — Check the two big non-solver causes

Before any bisection, eliminate the two causes that mimic solver failure and that no knob fixes:

1. **Fiscal inconsistency** (the single most destabilizing error): spending ratios + actual tax
   revenue + `debt_ratio_ss` must satisfy the primary-balance identity, or debt balloons on the
   transition and the convex debt premium runs it to infinity. The SS *always* solves and looks
   fine — only the TPI blows up. Symptom match: baseline TPI diverges/overshoots, worse with
   `r_gov_DY2 > 0`. Neither damping nor Anderson fixes this. See the Fiscal-consistency section of
   the `og-country-calibration` skill for the identity and the audit-by-instrument procedure.
2. **Calibration placeholders binding constraints**: `zeta_K = 0.9`-style placeholders drive
   `K_d = B − D_d` negative and break the transition; the `K_d has negative elements` guard is the
   tell. Grep the JSON for the known placeholder values before blaming the solver.

## Phase 3 — Bisect (one variable at a time)

State a single hypothesis in writing ("I think X because Y"), then test it with the smallest
possible run. Three bisection patterns, in increasing depth — pick the shallowest that can decide
your hypothesis:

- **Parameter-level bisection** (pattern: `bisect_J1.py`): start from a known-good configuration
  and apply the failing configuration's overrides *one at a time* (or binary-search groups) until
  the failure appears. The first override that breaks it is your suspect. Use
  `ENFORCE_SOLUTION_CHECKS=False` and a small `maxiter` to make each probe cheap.
- **Function-level bisection** (pattern: `locate_J1_bug.py` / `trace_tpi_J1.py`): feed *identical
  fixed micro inputs* (e.g. `n=0.4, b=1.0` everywhere) directly into each aggregator
  (`get_L`, `get_K`, `get_B`, `get_BQ`, `get_C`, `get_I`) under the good and bad configs and diff
  the outputs. Finds which function diverges without running the solver at all.
- **Control/treatment harness** (pattern: `run_country.py` + `run_country_compare.py`): run the
  same country with exactly one flag/setting flipped, capture both logs, and compare converged
  outputs with an explicit drift threshold (0.1% was the house standard) printing a single
  `NO DRIFT` / `DRIFT DETECTED` verdict — into the log, not just the console. Run the pair across
  2–3 countries (IDN/PHL/ZAF) to learn whether an effect is country-specific (→ calibration) or
  engine-wide (→ OG-Core).

Two auxiliary techniques from the mined history:

- **Equivalent-config comparison**: when a test failure might be a *stale expected pickle* rather
  than a bug, build a mathematically equivalent configuration (e.g. J=1 vs J=2 with identical
  types) and compare full solved paths — agreement within 1% means the code is fine and the
  fixture is stale.
- **Suspect-block substitution** (pattern: `test_zaf_substitute_e.py`): to test whether a specific
  calibration block causes ill-conditioning, substitute the generic OG-Core default for just that
  block and see if the symptom disappears.

**Re-decide after every probe.** Two failed fixes on the same hypothesis = the diagnosis is wrong;
go back to Phase 1 with the new evidence. Three failed fixes = stop and question the setup itself
(calibration, model version, or test fixture), and discuss with the user before a fourth.

## Phase 4 — Remedies, in order of legitimacy

Only after the class is identified:

1. **Fix the cause** (calibration value, fiscal balance, code bug, stale fixture) — always
   preferred. Add the cheapest regression guard that would have caught it (a value-pinning test, a
   drift check).
2. **Oscillation/stall knobs** (treat oscillation, never runaway): heavier damping `TPI_NU`
   0.4 → 0.3 → 0.2; Anderson acceleration (`TPI_outer_method="anderson"`, ogcore ≥ 0.16.4);
   for a multi-industry cold start, the continuation solve (flat anchor → morph gamma/Z; see the
   `og-country-calibration` skill).
3. **Convergence-criteria honesty**: loosening `mindist` or raising `maxiter` is masking, not
   fixing, unless you can show the iterate is genuinely near a solution (Distance decaying, Euler
   errors small).

Report the diagnosis with the evidence chain: log lines → class → hypothesis → probe result →
fix → verification run. Separate what you verified from what you assume.

## Cost gate on probes

Log reading, greps, and aggregator-level probes (no solve) are free — do them liberally. Anything
that *solves* costs real time: a capped-iteration SS probe is borderline (propose it with its
expected runtime); a full SS, any TPI run, a control/treatment pair, or a multi-country sweep is
expensive — present the probe plan (which runs, why, expected total time) and get the user's
explicit approval before launching. Never queue a battery of diagnostic runs on your own, and
never re-launch a failed run "to see if it happens again" without asking. Skills propose; the
user launches (see the OG family README → Approval gates).
