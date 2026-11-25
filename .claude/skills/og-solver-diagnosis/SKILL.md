---
name: og-solver-diagnosis
description: "Diagnoses OG-Core solver trouble by finding the root cause before any fix: a steady-state or transition-path solve that does not converge, diverges, oscillates, crashes, runs away, warns about NaN or negative values, runs far longer than expected, or lands on a suspicious answer; also result drift between runs and failing expected-output tests. Use before changing any solver setting (nu, maxiter, Anderson) or proposing a fix."
---

# OG solver diagnosis

Adapted from obra/superpowers `systematic-debugging` (MIT, https://github.com/obra/superpowers) for
OG-Core solves, with the failure classes seen across the country models.

Find the root cause before changing anything: solver settings are the last step, not the first.
Most "solver failures" in this family were fiscal inconsistencies, calibration placeholders or the
wrong code running.

Everything here runs the way og-run describes: installed copies, the repo's own example or tuning
script, and reading saved output (`references/og-run-rules.md`). A run built any other way cannot
confirm or rule out anything.

## Phase 0 — Rule out contamination

First establish that the failure comes from a run made the user's way: an installed copy running
the repo's example script unchanged. A failure seen only in a test fixture, a saved pickle, or a
partial or serial run is a lead until it is reproduced that way. Measure a run from its saved
output, never by altering it.

If the result is surprising, or reproduces a number from a run known to be buggy, suspect the wrong
code ran before suspecting the model: do og-run's checks before a run (branch and commit, where the
packages import from, the environment). Continue only once the environment is clean.

## Phase 1 — Read the log, characterize the failure

Read the actual solve log before forming any theory. Extract, with grep:

```bash
grep -n "Iteration\|Distance" <log> | tail -20     # convergence trajectory
grep -n "K_d has negative\|Traceback\|RuntimeError\|Key lost\|Falling back" <log>   # known signatures
grep -n "Time path iteration complete" <log>   # did the transition path finish?
tail -30 <log>
```

The steady state has no single completion line: its `Iteration: … Distance: …` lines stop once
it converges, and the transition path then starts its own `Iteration:` / `Distance:` pairs.

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
classes, their signatures, and the known remedy for each). The step-by-step procedures for the
common ones (warm-starting a steady state that will not converge, triaging a transition-path
resource-constraint error by when it happens, reading a stall diagnosis) are in
`references/solve-procedures.md`.

**Keep every run's log.** Send each run's output to a named log, with its settings at the top. Once,
the decisive comparison was printed only to a console and lost; and a log's filename once named a
different variant than the one it printed, so check the settings inside, not the name.

## Phase 2 — Check the two big non-solver causes

Before any bisection, eliminate the two causes that mimic solver failure and that no knob fixes:

1. **Fiscal inconsistency** (the single most destabilizing error): spending ratios + actual tax
   revenue + `debt_ratio_ss` must satisfy the primary-balance identity, or debt balloons on the
   transition and the convex debt premium runs it to infinity. The SS *always* solves and looks
   fine — only the TPI blows up. Symptom match: baseline TPI diverges/overshoots, worse with
   `r_gov_DY2 > 0`. Neither damping nor Anderson fixes this. Also check the premium is centred
   at `debt_ratio_ss` (taxonomy class A). See the fiscal-consistency reference of the
   `og-country-calibration` skill for the identity and the audit-by-instrument procedure.
   Setting the standard solver settings (Anderson, `nu` 0.2 or lower; `references/og-run-rules.md`) is fine at any
   time; expecting them to fix a runaway is not.
2. **Calibration placeholders binding constraints**: `zeta_K = 0.9`-style placeholders drive
   `K_d = B − D_d` negative and break the transition; the `K_d has negative elements` guard is the
   tell. Grep the JSON for the known placeholder values before blaming the solver.

## Phase 3 — Bisect (one variable at a time)

State one hypothesis ("I think X because Y"), then test it with the smallest change that can decide
it. In increasing depth:

- **Change one input at a time.** From a configuration that solves, apply the failing
  configuration's changes one at a time (or in halves) through the repo's tuning script and an
  overrides file, until the failure appears. The first change that breaks it is the suspect.
- **Compare functions without solving.** In the installed environment, call each aggregator
  (`get_L`, `get_K`, `get_B`, `get_BQ`, `get_C`, `get_I`) with identical fixed inputs (e.g.
  `n=0.4, b=1.0`) under the good and bad configurations and compare the outputs. This finds the
  function that differs without a solve.
- **Control and treatment.** Install the two sides as separate copies (the difference is a branch
  of the repo, or an overrides file its own script reads), run the example in each, and compare the
  saved outputs against an explicit threshold (0.1% has been the standard), recording the verdict in
  the log. Repeating the pair on two or three countries tells you whether an effect is
  country-specific (calibration) or engine-wide (OG-Core).

Two auxiliary techniques from the mined history:

- **Equivalent-config comparison**: when a test failure might be a *stale expected pickle* rather
  than a bug, build a mathematically equivalent configuration (e.g. J=1 vs J=2 with identical
  types) and compare full solved paths — agreement within 1% means the code is fine and the
  fixture is stale.
- **Suspect-block substitution** (pattern: `test_zaf_substitute_e.py`): to test whether a specific
  calibration block causes ill-conditioning, substitute the generic OG-Core default for just that
  block and see if the symptom disappears.

Before reporting a cause, confirm it with the example script in an installed copy, and call
anything not yet confirmed that way a lead. Hand-built environments, another ogcore installed into a
copy, and wrapped or patched scripts are how invalid results arose in the first place (history:
ETH). Time runs one at a time.

**Re-decide after every probe.** Two failed fixes on the same hypothesis = the diagnosis is wrong;
go back to Phase 1 with the new evidence. Three failed fixes: question the setup itself
(calibration, model version or test fixture) and talk it through with the person you are working
with before a fourth.

## Phase 4 — Remedies, in order of legitimacy

Only after the class is identified. Before writing any fix, check it does not already exist:
search history and other branches (`git log --all -S<symbol>`, `git branch -a --contains`) and
the repo's open PRs. A fix that already landed, or is waiting in a PR, changes the job.

1. **Fix the cause** (calibration value, fiscal balance, code bug, stale fixture) — always
   preferred. Add the cheapest regression guard that would have caught it (a value-pinning test, a
   drift check).
2. **Oscillation/stall knobs** (treat oscillation, never runaway): first confirm the standard
   settings, Anderson (`TPI_outer_method="anderson"`) with `nu` 0.2 or lower; then heavier damping, lowering `nu` further;
   for a multi-industry cold start, the continuation solve (flat anchor → morph gamma/Z; see the
   `og-multi-industry-calibration` skill).
3. **Convergence-criteria honesty**: loosening `mindist` or raising `maxiter` is masking, not
   fixing, unless you can show the iterate is genuinely near a solution (Distance decaying, Euler
   errors small).

Report the diagnosis with the evidence chain: log lines → class → hypothesis → probe result →
fix → verification run. Separate what you verified from what you assume.

## Validating an OG-Core change

Checking that an OG-Core change keeps every country solving is og-run's "Testing a code change";
this skill takes over when one of those runs fails or differs.

## What costs time

Reading logs and output and calling aggregator functions take seconds: do them freely. Anything that
solves takes minutes, and a battery takes hours: say which runs, why and how long before starting,
and do not relaunch a failed run just to see whether it fails again.
