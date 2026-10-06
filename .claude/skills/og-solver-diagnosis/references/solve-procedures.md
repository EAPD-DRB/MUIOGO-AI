# Steady-state and transition procedures

The detailed procedures behind taxonomy classes H (cold-start seed), I (resource-constraint error
by timing) and C (stalls), plus the pattern for testing against an unreleased ogcore, which the
"Validating an OG-Core change" section of SKILL.md relies on.

Contents
- Warm-starting the steady state
- Initial-guess fragility: nearness is not solvability
- Triage an RC_error by where in time it happens
- Stall detection
- Running against an unreleased ogcore

## Warm-starting the steady state

**If a country's steady state will not converge, suspect the cold start before the calibration.**
OG-Core seeds the household problem from constants (savings 0.07 for every age and group, labour
0.35), with the bequest guesses derived from them. Older ogcore hard-coded them; newer versions expose
them as parameters (`initial_guess_b_SS` and relatives). Each is still one scalar across all ages and
types, so the problem below remains, though the scalar can be raised. For a wealthy, ageing, high-saving
population a uniform seed is not imprecise, it is catastrophic:

- the bequest seed lands two orders of magnitude low (JPN: 134× in aggregate, 349× for the top income
  group, against solved savings of ~6.1 vs the seed's 0.07);
- domestic capital `K_d = B − D_d` therefore starts negative (wealth near zero against domestically
  held government debt), so `SS_fsolve` clamps it and substitutes `1e9` residuals, destroying the
  finite-difference Jacobian the default `hybr` root-finder depends on;
- `initial_guess_factor_SS` is validated to a maximum of 500,000, while a low-unit currency needs far
  more (JPN ~7e6, IDN worse), so the right seed cannot be entered as a parameter.

**The failure disguises itself.** `run_SS` does not report failure. It silently restarts down a
ladder of rescaled seeds (`ogcore.constants.DEV_FACTOR_LIST`), making a separate `opt.root`
call per rung. What looks like "hundreds of slow iterations" is several failed solves end to end.
Count restarts, not iterations: a jump of 50× or more in the residual between consecutive evaluations
is a new rung starting, not progress.

**The fix.** Seed from a state that has already solved: the household matrices `b` and `n` and every
outer unknown together, so they are mutually consistent. Pass `factor` directly, which bypasses the
validator cap. Measured on JPN, identical parameters, same 7-worker client:

| | evaluations | restarts | residual |
|---|---:|---:|---:|
| cold start | >175 | several | never converged |
| warm start | 18–22 | none | 5.5e-11 |

`b` and `n` are in model units, so a seed stays valid across changes to the currency scale, the
demographic window and modest parameter moves. Ship the seed with the repo (~9 KB) and regenerate it
after any large recalibration; without it a fresh checkout may not solve. Reference implementation:
OG-JPN's `ogjpn/warm_start.py` + `examples/save_warm_start.py`. Code shipped in the country repo,
like this, is part of how that repo runs, so it does not break the owner's "nothing bespoke" rule;
an ad-hoc driver or patch outside the repo would. When an ogcore release ships the same fix, retire the
repo's patch: grep the repo for patched ogcore
functions after each ogcore bump and compare with its changelog.

**Warm-starting is not retuning the seed parameters.** Setting `initial_guess_r_SS`/`TR_SS` to their
solved values was tried on JPN and made things worse (the next section).
The scalars are 3 of 14 unknowns; the household matrices are 560 numbers and are what the bequest seed
is computed from. Warm-start the matrices; leave the scalar parameters alone.

**Worth automating.** Every country repo will hit this. Writing the seed on every successful solve
and reusing it by default makes reruns cheap; a shared helper saves each repo re-deriving it. The
proper fix is upstream: seeds derived from parameters ogcore already has (`b ≈ (K/Y + D_d/Y)·Y`).
**[net-new: JPN]**

## Initial-guess fragility: nearness is not solvability

**[PHL]** Guesses retuned to the exact solved values (factor to 5 digits) sent the solver through a
`K_d < 0` region and failed the steady state, while older, farther guesses converged cleanly. Choose
packaged guesses by solve-path robustness; keep the set that works, do not chase proximity. Transient
"K_d has negative elements" warnings during iteration are benign only if the identities hold in the
saved pickle (`K = K_d + K_f`, `K_d = B − D_d`). Check the pickle, not the console: `get_K_splits`
floors a negative `K_d` at `0.05·B`, and a floored value in the final solution breaks the identity.

## Triage an RC_error by where in time it happens

**[net-new: JPN]** ogcore pickles TPI output before it raises, so read
`TPI_vars.pkl["resource_constraint_error"]` even from a failed run (recent ogcore also prints the
maximum error, its period and the tolerance). The location is the diagnosis:

- **smooth and decaying over the first several periods** → the initial condition, i.e. initial
  wealth (the PHL windfall; og-country-calibration's macro-open-economy.md);
- **isolated single-period spikes** → a discontinuity in a time-varying input at exactly that period.
  Check `rho`, `imm_rates`, `omega`, `retire`, `etr_params` for a jump; this is how the
  demographic-window and `fixper` problems surfaced (og-country-calibration's households-demographics.md);
- **growing along the path with debt rising** → the fiscal runaway (taxonomy class A; og-country-calibration's fiscal-consistency.md).

Check the outer-loop distance series first: if it fell monotonically and debt is flat, the solver is
fine and the problem is an input. Do this triage before any tuning.

## Stall detection

Recent ogcore logs a diagnosis when the TPI outer loop stops improving over
  `TPI_stall_window` iterations, distinguishing a cycling loop (lower `nu` or Anderson) from a
  diverging economy (usually an inconsistent fiscal block). `TPI_stall_action = "stop"` ends a
  hopeless run early. Check `hasattr(p, "TPI_stall_window")`.

## Running against an unreleased ogcore

**[PHL]** `uv run --with-editable <ogcore-checkout>` can silently resolve ogcore from the uv cache,
and probing with `python -c` from the checkout root masks it through cwd shadowing, so do not use
it. The pattern: put the unreleased ogcore in its own worktree, built from the released base plus
the one PR's diff (not a branch carrying unrelated upstream merges, which once broke the steady
state through an unrelated payroll change). Give the country repo its own worktree and venv,
install that ogcore into it editable, invoke `.venv/bin/python` (never `uv run`, which re-syncs to
the lock), and `assert <ogcore worktree> in ogcore.__file__` before anything else; the assert has
caught real contamination. og-run-preflight's ogcore line should then report that local build. This is a development pattern for
testing an upstream change, not a way to make official runs. Keep the packaged JSON loadable on
released ogcore too: tests that build a `Specifications` strip not-yet-released parameters when absent
(`hasattr` guard), so the suite stays green on both.
