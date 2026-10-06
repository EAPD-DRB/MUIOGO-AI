# Solving and tuning

The run rules themselves are in SKILL.md ("Running the model: the owner's rules"). This file holds the
detail behind them. For a solve that will not converge, diverges or oscillates, use
og-solver-diagnosis before touching any solver setting; for the go/no-go check before a solve, use
og-run-preflight.

Contents
- Environment
- Run engineering: detail and evidence
- The in-model tuning loop
- Tuning-loop order: sourced parameters first
- Warm-starting the steady state
- Initial-guess fragility: nearness is not solvability
- Triage an RC_error by where in time it happens
- Running against an unreleased ogcore
- Derived parameters regenerate together

## Environment

- **uv, not conda.** `uv sync --extra dev`, then `uv run <cmd>`. `AGENTS.md` is the source of truth
  for setup; `docs/book/content/contributing/contributor_guide.md` is stale (still conda) in most
  repos. **[family]**
- **Never commit a `uv.lock` change from calibration work.** The lock is Dependabot-managed; if a
  local `uv sync` touches it, `git restore uv.lock`. Confirm `uv.lock` and `.python-version` are not
  in the PR diff. **[family among EAPD-DRB repos: PHL/ZAF/IDN/ETH; PSLmodels repos BRA/USA differ]**
- **Check the resolved ogcore in `uv.lock`, not the `pyproject.toml` floor.** The `ogcore>=` floors
  are not synced across repos, and the resolved versions have not converged either (on the last
  check they spanned 0.16 to 0.20). To compare a repo with its siblings, grep `name = "ogcore"` in
  `uv.lock`. A parameter this skill relies on (`TPI_outer_method`, `r_gov_floor`, the
  `initial_guess_b_SS` family) may be missing from an older resolved ogcore; check with `hasattr`
  and treat an ogcore bump as its own change.
- **Preflight** (og-run-preflight): print branch + HEAD of every repo involved and `sys.executable`;
  assert imports resolve inside the intended checkout
  (`uv run python -c "import ogXXX, ogcore; print(ogXXX.__file__, ogcore.__file__)"`). Editable
  installs, script-dir shadowing and cwd shadowing silently run another checkout's code; this has
  caught real contamination. **[emerging: a house rule in OG-ETH's informality work; the full combo
  net-new]**
- **The example run is a smoke test, not a correctness check.** `test_run_example.py`
  (`@pytest.mark.local`) only checks the process is still alive after ~5 minutes; it never checks SS or
  TPI values. Numeric validation is the
  dashboard. **[family]**
- **CI-equivalent suite:** `uv run python -m pytest -m 'not local' -q`. **[family]**

## Run engineering: detail and evidence

- **The example pattern.** Every sibling `run_og_<country>.py` does
  `num_workers = min(cpu_count(), 7)`, one `Client(n_workers=num_workers, threads_per_worker=1)`,
  and one `runner(p, time_path=True, client=client)` per scenario. The steady state solves through
  the client too. Official runs use exactly this, so the model is invoked the way the family invokes
  it rather than through a hand-rolled driver that can differ subtly from the shipped path.
- **Why seven workers.** `SS.py` and `TPI.py` both call `client.submit` inside
  `for j in range(p.J)`, so workers beyond `J` idle. Seven is maximum parallelism when `J = 7` (the
  ports); OG-USA ships `J = 10`.
- **Parallel, not serial, for the steady state too.** Older measurements found the SS slower
  through the client than serial (~38s vs ~6s per GE evaluation **[JPN]**; 12+ min vs 66s **[PHL]**).
  Both predate ogcore 0.20.1, which scatters the parameters object once per SS solve instead of once
  per residual evaluation. The owner's rule is to follow the example scripts with everything as
  parallel as possible (2026-08-10), so do not build a serial driver on the strength of those
  numbers; if the SS through the client is slow on a current ogcore, report it as a finding.
- **The trap that looks like an optimisation.** `runner` always re-solves the steady state, so
  `runner(time_path=False)` followed by `runner(time_path=True, client=client)` solves it twice, the
  second time the slow way. A two-phase hand driver (SS serial → pickle → TPI with the client) was
  used on PHL for speed; it is not the example pattern and is not used for official runs.
- **Anderson every time.** `TPI_outer_method = "anderson"` with `nu` 0.2 or lower, in the packaged
  parameters, not the script; available since ogcore 0.16.4. Evidence: the M=1 PHL transition went
  from ~30–70 damped iterations (~20 min) to 11–12 (~2–2.5 min) with monotonically falling distances
  **[PHL]**; OG-Core's own changelog reports a stiff multi-industry reform converging in 53 outer
  iterations vs 126 under constant `nu = 0.1`. Watch the distance series the first time; if it
  oscillates or stalls, fall back to damped `nu`. It is TPI-only (zero occurrences in `SS.py`), so it
  does nothing for a steady-state problem, and it never fixes a fiscal runaway.
- **Stall detection.** Recent ogcore logs a diagnosis when the TPI outer loop stops improving over
  `TPI_stall_window` iterations, distinguishing a cycling loop (lower `nu` or Anderson) from a
  diverging economy (usually an inconsistent fiscal block). `TPI_stall_action = "stop"` ends a
  hopeless run early. Check `hasattr(p, "TPI_stall_window")`.
- **Time budget.** A healthy baseline solve takes under 10 minutes (owner's rule). Past that,
  diagnose; do not wait it out.

## The in-model tuning loop

**[PHL]** The tuning loop is cheap: use real solves, not algebra. A warm-guess SS solve takes
seconds, so *solve → read the revenue dashboard → adjust dials → re-solve* converges in 3–5
iterations for half a dozen simultaneous dials (GS φ2, `tau_c`, CIT adjustment, `p_wealth`,
`r_gov_shift`, `zeta_K`). Keep a small driver that loads the packaged JSON plus an overrides dict,
builds the same worker pool as the example script, calls `runner(..., time_path=False,
client=client)`, and prints model vs target by instrument. Two things it is not:

- not an official run: once the dials settle, fold the overrides into the JSON and run the example
  script through the client;
- not the last solve: always finish with a standalone solve of the packaged JSON itself (no
  overrides). It catches schema errors and seed problems the overrides path hides. If it fails, go
  back to the overrides you just folded in.

## Tuning-loop order: sourced parameters first

**[net-new: JPN]** The loop converges in 3–5 rounds only once the sourced parameters are settled. Any
change to a sourced parameter invalidates every tuned dial below it, because they were fitted against
the old base. Work in this order and expect one full retune per upstream correction:

1. sourced structurals: `gamma`, `delta`, `g_y`, the demographic window, spending shares;
2. tuned tax dials against the revenue targets;
3. `beta` against `K/Y`;
4. retune (2) if (3) moved the bases.

JPN took fourteen rounds because `gamma`, `delta`, `g_y`, `alpha_T` and the window were each
corrected after the tax dials were tuned. Audit the whole parameter surface before starting the loop,
not one parameter at a time. After any tax change, re-tune `zeta_K` (macro-open-economy.md).

## Warm-starting the steady state

**If a country's steady state will not converge, suspect the cold start before the calibration.**
OG-Core seeds the household problem from constants. Through ogcore 0.20.1 these were hard-coded in
`SS.py` (savings 0.07 for every age and group on the no-zeta path, with its own
`TODO: remove hardcode`; labour 0.35), with the bequest guesses derived from them. Recent ogcore makes
them parameters (`initial_guess_b_SS`, `initial_guess_n_SS` and their `_no_zeta` versions; check
`hasattr(p, "initial_guess_b_SS")`). Each is still one scalar across all ages and types, so the
problem below remains, though the scalar can now be raised. For a wealthy, ageing, high-saving
population a uniform seed is not imprecise, it is catastrophic:

- the bequest seed lands two orders of magnitude low (JPN: 134× in aggregate, 349× for the top income
  group, against solved savings of ~6.1 vs the seed's 0.07);
- domestic capital `K_d = B − D_d` therefore starts negative (wealth near zero against domestically
  held government debt), so `SS_fsolve` clamps it and substitutes `1e9` residuals, destroying the
  finite-difference Jacobian the default `hybr` root-finder depends on;
- `initial_guess_factor_SS` is validated to a maximum of 500,000, while a low-unit currency needs far
  more (JPN ~7e6, IDN worse), so the right seed cannot be entered as a parameter.

**The failure disguises itself.** `run_SS` does not report failure. It silently restarts down a
39-rung ladder of rescaled seeds (`ogcore.constants.DEV_FACTOR_LIST`), making a separate `opt.root`
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
OG-JPN's `ogjpn/warm_start.py` + `examples/save_warm_start.py`.

**Warm-starting is not retuning the seed parameters.** Setting `initial_guess_r_SS`/`TR_SS` to their
solved values was tried on JPN and made things worse (the "nearness is not solvability" rule below).
The scalars are 3 of 14 unknowns; the household matrices are 560 numbers and are what the bequest seed
is computed from. Warm-start the matrices; leave the scalar parameters alone.

**To do: automate this.** Every country repo will hit it. The seed should be produced and reused
without hand-holding: a `--save-warm-start` flag on the standard example that writes the seed on every
successful solve, an `enable()` called by default, then a shared helper so each repo does not
re-derive the same shim. The proper fix is upstream (ogcore deriving its seeds from parameters it
already has, `b ≈ (K/Y + D_d/Y)·Y` from the firm FOC and the debt parameters, and accepting a warm
start), but the repo-side helper is worth having regardless, because it also makes reruns cheap.
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
  wealth (the PHL windfall; macro-open-economy.md);
- **isolated single-period spikes** → a discontinuity in a time-varying input at exactly that period.
  Check `rho`, `imm_rates`, `omega`, `retire`, `etr_params` for a jump; this is how the
  demographic-window and `fixper` problems surfaced (households-demographics.md);
- **growing along the path with debt rising** → the fiscal runaway (fiscal-consistency.md).

Check the outer-loop distance series first: if it fell monotonically and debt is flat, the solver is
fine and the problem is an input. Do this triage before any tuning.

## Running against an unreleased ogcore

**[PHL]** `uv run --with-editable <ogcore-checkout>` can silently resolve ogcore from the uv cache,
and probing with `python -c` from the checkout root masks it through cwd shadowing. The working
pattern: run from the ogcore checkout's env with the country repo overlaid
(`cd OG-Core && uv run --with-editable ../OG-XXX python driver.py`), pin
`sys.path.insert(0, <ogcore-checkout>)` in the driver, and `assert <checkout> in ogcore.__file__`
before anything else; the assert has caught real contamination. This is a development pattern for
testing an upstream change, not a way to make official runs. Keep the packaged JSON loadable on
released ogcore too: tests that build a `Specifications` strip not-yet-released parameters when absent
(`hasattr` guard), so the suite stays green on both.

## Derived parameters regenerate together

**[PHL]** Anything computed from demographics (the model-consistent `g_RM` path from `g_n`, the
`eta_RM` matrix from `omega_SS`) belongs in the demographics-regeneration tool, so a demographics
rebuild cannot leave it stale. Add a test asserting packaged value == constructor(packaged inputs).
