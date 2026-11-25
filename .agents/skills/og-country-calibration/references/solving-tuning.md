# Solving, tuning and the environment

How to run the model is in og-run-rules.md (a copy ships with this skill). This file holds the
tuning loop, how to spend runs while exploring, and environment checks. When a solve misbehaves (a
steady state that will not converge, a resource-constraint error on the transition, a stall), use
og-solver-diagnosis.

Contents
- Settle the inputs, then tune once
- The tuning loop
- Spending runs while exploring
- Watch a run; do not wait on it
- Measuring what a change does
- The environment
- Derived parameters regenerate together

Each lesson gives the rule, the check, why, and where it was learned (`[CODE]`; the case is in
`lessons/<CODE>.md`).

## Settle the inputs, then tune once

**Rule.** Agree the targets, settle every sourced input from data (one decision at a time, each
logged with its source and the alternatives considered), then tune the dials once: the tax dials
against their revenue lines, `r_gov_shift` against the effective rate, `zeta_K` against the foreign
share, patience last (macro-open-economy.md). Validate with the example script, steady state and
transition.

**Check.** Before tuning, every parameter is in one of three states: sourced, tuned to a named
moment, or defaulted with a written reason. After a tax change, re-tune `zeta_K`; after a sourced
input changes, redo the tax dials, then `zeta_K`, then patience. A sourced value is never moved to hit a
target.

**Why.** Every tuned dial is fitted against the inputs below it; correcting inputs after tuning
cost fourteen rounds on one country and many on others. [JPN, ETH, PHL]

## The tuning loop

**Rule.** Tune with real solves through the repo's tuning script: it loads the packaged JSON plus
an overrides file, solves, prints model against target, and writes the next round's overrides with
every setting carried forward. Several repos have one (for example `examples/tune.py` or
`examples/tune_ss.py`); if yours has none, add one as its own change. [ZAF,
ETH, PHL] Static dials (the income-tax scale; `tau_c`, an effective rate matched in the model
because its base is the model's own consumption; the corporate factor; `p_wealth`; `tau_bq`;
`r_gov_shift`; `zeta_K`) are tuned on warm-started steady states with secant steps, usually in three
to five rounds; spend transition rounds only on what the transition judges (patience, initial
wealth, spending paths). When the dials settle, fold them into the JSON (and any scales into the
code that builds it), commit, re-install, and solve the packaged JSON with no overrides.

**Check.**
- Every solve logs to a named file with its settings first. [KOR]
- Each solve is seeded from the last converged one; after a large change (preferences, the capital
  stock) regenerate the warm-start seed, if the repo keeps one. A move that breaks a warm-started solve is a
  calibration signal; one that breaks a cold start is usually the seed. [KOR, ETH]
- A parameter made a constant is no longer steered by the tuning script.
- The final reported numbers come from the example script on the packaged JSON.

**Why.** A warm-started steady state takes seconds where a cold one took minutes; the no-overrides
solve catches schema and seed errors the overrides hide. [KOR, PHL]

## Spending runs while exploring

**Rule.** One probe per idea, at a bound, read for what it buys and what it costs on the other
moments; then decide. Before tuning an idea in full, test it on the smallest object that can fail
it (one household's lifetime, one steady state).

**Check.** Rounds per idea while exploring: one. A mechanism stated to the user is computed from the
saved output, with the number; a guess is labelled as one.

**Why.** Exploring with full tuning rounds and transition solves for each idea cost hours, and
confident explanations not computed from the output sent the work the wrong way. [ETH]

## Watch a run; do not wait on it

**Rule.** From launch, read the log and the workers' CPU. Stop early when the log shows restarts
or the steady state runs far longer than expected, and diagnose (og-solver-diagnosis).

**Check.** CPU near the number of workers; the steady state in seconds to a couple of minutes; no
repeated "initial guess" restarts in the log.

**Why.** Stalled runs left unwatched for an hour were read afterwards as one long attempt when they
were a ladder of restarts. [ETH]

## Measuring what a change does

**Rule.** Calibrate the best version first; then measure what one choice does with a single run
that switches it off, from the finished calibration.

**Why.** Tuning a control and a treatment in parallel doubles every round and measures the
difference between two unfinished calibrations. [ETH]

## The environment

- **What the packaged JSON carries.** `Calibration(p, update_from_api=False)` fetches nothing and
  sets only identity values; the packaged JSON is the calibration. Count what differs from your
  ogcore's `default_parameters.json`: every key left at the default is unexamined unless
  documented. [JPN]
- **Which ogcore.** Read the resolved ogcore in the lockfile, not the `pyproject.toml` floor. A
  parameter a lesson relies on may be missing or renamed in your build: check with
  `hasattr(Specifications(), name)` in that environment, and load the packaged JSON against a new
  ogcore before anything else. Treat an ogcore upgrade as its own change.
- **Before a long tuning campaign,** look for OG-Core changes that speed the solve (open or merged)
  and run on a version that carries them, installed the official way (og-run).
- **The repo's setup instructions** (`AGENTS.md`, contributor guide) and its lockfile conventions
  apply; calibration work does not change dependencies.

## Derived parameters regenerate together

Anything computed from the demographics (a `g_RM` path from `g_n`, an `eta` or `eta_RM` built from
the population) belongs in the code that regenerates the demographics, so a rebuild cannot leave it
stale. If the repo regenerates its packaged JSON, a test that the packaged values equal the
regenerated ones covers all of them at once. [PHL, ETH]
