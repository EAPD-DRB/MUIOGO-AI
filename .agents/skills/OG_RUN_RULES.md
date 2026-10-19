<!-- Copy of EAPD-DRB/Model-tools skills/shared/og-run-rules.md. Edit there, then copy here.
     The OG skills reference it as ../OG_RUN_RULES.md, like WORLD_DISCIPLINE.md. -->

# OG run rules

The model owner's rules for running an OG-Core country model. They override older advice in the
OG repos, including the AGENTS.md estimate that a full example run takes "~35 min – 2 hr".

**A healthy baseline takes under ten minutes.** The steady state takes seconds to a minute or two;
the transition path about 5–7 minutes. Much longer means something is wrong (the worker pool, the
solver settings, a stale ogcore, a cold start, or the calibration), not that the model is slow.
Stop and diagnose (og-solver-diagnosis); do not wait it out.

**Install with the official installer.** Every OG model a run will report on is installed with
OG-Core's own installer, as `scripts/QUICK_INSTALL.md` in PSLmodels/OG-Core describes: download
`scripts/install.sh` (Windows: `install.ps1`) from OG-Core `master`, then
`bash install.sh --repo <key> --dest <new parent folder> --yes` (`--list` shows the keys: og-core,
og-eth, og-zaf, og-idn, og-phl, og-bra). It clones the repo, installs uv if needed, runs
`uv sync --extra dev`, and checks the import. To test a branch or a fork, install it the same way
into its own folder: `--repo-url <git URL> --branch <branch>`. A local clone works as the URL,
which is how a new country repo not yet in the catalog is installed. The installer names the
package from the last part of the URL (lowercased, hyphens dropped) and checks that it imports, so
install from a clone whose folder is named like the repo (`.../OG-<XXX>`, `.../OG-Core`), not from a
worktree or a demo folder (`OG-Core.fix`, `OG-<XXX>-demo`): those install but fail the import check.
Do not build an environment by hand
for a reported run: no conda environment, no `uv sync` inside an ad-hoc worktree, no `PYTHONPATH`
or `sys.path` shadowing, no `pip install` of another build. If the installer cannot produce what the
task needs, stop and ask.

**Run the shipped example script, unchanged.** From the installed folder, activate the environment
and run the example: `source .venv/bin/activate`, then `python examples/run_og_<xxx>.py`
(`uv run python examples/run_og_<xxx>.py` from that folder is equivalent). Nothing bespoke: no
driver script of your own, no edited copy of the example, no settings changed in the script, no
monkeypatching, and nothing injected into the run to observe it (wrappers, counters,
`sitecustomize`, worker plugins). Code the repo itself ships (a warm-start helper, a
multi-industry continuation solver in its example) is part of how that repo runs. If a task seems
to need a different setting or a change to the run, ask the user first, and say in the report
exactly what differed from the shipped example. The lockfile is what the repo runs: if the
environment has drifted from it, re-run the installer (or `uv sync --extra dev` in the installed
folder) and re-run the preflight; do not run the stale environment. The one remaining exception
is testing an unreleased ogcore under a country model (og-solver-diagnosis covers the pattern),
and only when the user asked for it.

**Calibration tuning runs through repo code too.** Tuning a dial takes many steady-state solves,
and the example always runs the full transition. So the repo ships a small tuning script (for
example `examples/tune_ss.py`): it loads the packaged JSON plus an overrides dict, builds the
example's worker pool, calls `runner(p, time_path=False, client=client)` and prints the dashboard.
Because the repo ships it, it runs from the installed copy like any repo code; it is never an
ad-hoc driver in a scratch folder. Its output sets dials and nothing more: fold the settled values
into the JSON, commit, re-install, and take every reported number from the shipped example.

**Tests run in an installer copy too.** Any OG test run whose result you will report (the CI
selection, the slow `local` tests, a single test file) runs inside a copy made by the installer,
for the exact commit under test: `bash install.sh --repo-url <git URL or local clone> --branch
<branch> --dest <new folder> --yes`, then `uv run python -m pytest ...` (or `pytest` with the
environment activated) from that copy's folder, with the repo's own command (the contributor
guide's `pytest`, CI's `-m "not local and not benchmark"`, or `-m local`). Not from a development
worktree, not from an environment you synced by hand. When the code changes, re-install before
re-testing; a copy is tied to one commit. Tests that solve the model use the example's
parallelism: OG-Core's test files build a smaller Dask pool (`test_TPI.py`: 4 workers x 2
threads), so in the test copy only, set it to the example's `min(cpu_count(), 7)` workers x 1
thread before launching, and say so in the report (the model owner's call, 2026-10-12). Never
commit that edit.

**Evidence about the model comes only from such a run.** A claim that the model fails, is wrong,
has a bug, or got faster must come from an installer-installed copy running its shipped example.
Test fixtures, saved test pickles, serial runs, partial reproductions and your own drivers give
leads, not findings: label them as leads and do not report a model failure from them. Measure
after the run, not during it: diagnostics read the saved output (`OUTPUT_BASELINE`,
`OUTPUT_REFORM`) with the installed package's own functions and change nothing in the run. To
compare a code change, install `master` and the branch separately with the installer, run the
same shipped example in each, and compare the saved outputs.

**Everything as parallel as possible**, the steady state and tuning loops included. The examples
build one dask `Client(n_workers=min(cpu_count(), 7), threads_per_worker=1)` and call
`runner(p, time_path=True, client=client)` once per scenario. Workers beyond `J` idle, so seven is
full parallelism when `J = 7`. Do not build a serial steady-state driver for speed; a slow steady
state is a symptom. `runner` always re-solves the steady state, so `runner(time_path=False)`
followed by `runner(time_path=True, client=client)` solves it twice.

**Anderson every run, with `nu` 0.2 or lower**, set in the packaged parameters, not the script
(if the repo does not set them, run the example as shipped and tell the user; change nothing
without their go):
`TPI_outer_method = "anderson"`. OG-Core's default is still damped iteration with `nu` 0.4, and
some repos set Anderson but leave `nu` at 0.4, so check both. `nu` still matters under Anderson:
the trust region is anchored to the damped step. Solver field names change between ogcore
releases; check the installed version has the fields you set (`hasattr(Specifications(), ...)` in
that environment, not release tags or memory: some releases were published without a git tag), and
treat an ogcore bump as its own change. Watch the distance series the first time; if it oscillates or stalls, fall back to damped
iteration to finish the run, and record the slower time per iteration (15–17 minutes per scenario
is normal for the fallback; it is not a failure). The shipped default stays Anderson: a stall that
comes with a drifting debt path points at the fiscal setup, so fix that, then retry Anderson before
changing the packaged parameters. Anderson works on the transition path only and never fixes a
fiscal runaway. Evidence:
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
