<!-- Copy of EAPD-DRB/Model-tools skills/shared/og-run-rules.md. Edit there, then copy here.
     The OG skills reference it as ../OG_RUN_RULES.md, like WORLD_DISCIPLINE.md. -->

# OG run rules

The model owner's rules for running an OG-Core country model. They override older advice in the
OG repos, including the AGENTS.md estimate that a full example run takes "~35 min – 2 hr".

**A healthy baseline takes under ten minutes.** The steady state takes seconds to a minute or two;
the transition path about 5–7 minutes. Much longer means something is wrong (the worker pool, the
solver settings, a stale ogcore, a cold start, or the calibration), not that the model is slow.
Stop and diagnose (og-solver-diagnosis); do not wait it out.

**Run the way the example scripts do, from the repo's own environment.** `uv sync --extra dev`,
then `uv run python examples/run_og_<xxx>.py`. Nothing bespoke for an official run. Code the repo
itself ships (a warm-start helper, a multi-industry continuation solver in its example) is part of
how that repo runs; an ad-hoc driver or patch outside the repo is not. The lockfile is what the repo
runs: if the environment has drifted from it (an older ogcore in `.venv` than `uv.lock` names), sync
it with `uv sync --extra dev` and re-run the preflight; do not run the stale environment to avoid the
sync. The one exception is a deliberately installed unreleased ogcore (og-solver-diagnosis covers the pattern), which
uses `.venv/bin/python`, because `uv run` would re-sync it away.

**Everything as parallel as possible**, the steady state and tuning loops included. The examples
build one dask `Client(n_workers=min(cpu_count(), 7), threads_per_worker=1)` and call
`runner(p, time_path=True, client=client)` once per scenario. Workers beyond `J` idle, so seven is
full parallelism when `J = 7`. Do not build a serial steady-state driver for speed; a slow steady
state is a symptom. `runner` always re-solves the steady state, so `runner(time_path=False)`
followed by `runner(time_path=True, client=client)` solves it twice.

**Anderson every run, with `nu` 0.2 or lower**, set in the packaged parameters, not the script:
`TPI_outer_method = "anderson"`. OG-Core's default is still damped iteration with `nu` 0.4, and
some repos set Anderson but leave `nu` at 0.4, so check both. `nu` still matters under Anderson:
the trust region is anchored to the damped step. Solver field names change between ogcore
releases; check the installed version has the fields you set (`hasattr(Specifications(), ...)` in
that environment, not release tags or memory: some releases were published without a git tag), and
treat an ogcore bump as its own change. Watch the distance series the first time; if it oscillates or stalls, fall back to damped
iteration. Anderson works on the transition path only and never fixes a fiscal runaway. Evidence:
it cut PHL's single-industry transition from ~30–70 damped iterations to 11–12.

**Validation runs are offline:** `update_from_api=False`. Some example scripts call
`Calibration(p, update_from_api=True)` whenever the machine is online, which overwrites packaged
values from live sources; check the script, say whether a run was online, and record it.

**Preflight before every solve** (og-run-preflight): branch and HEAD of every repo involved,
imports resolving inside the intended checkout, its own environment. A GO is a precondition, never
an authorization.

**Launch only after the user's explicit go.** Propose the exact command, the expected duration,
and whether it runs online. One go can cover an itemised batch (the same example in five listed
countries); it never extends to runs that were not on the list. A steady-state check that takes
seconds, inside a calibration task the user has already started, does not need a separate go.

**Record what produced every output:** repo, branch and commit, ogcore version, script, the
parameters changed (solver settings included), online or not, and the date.
