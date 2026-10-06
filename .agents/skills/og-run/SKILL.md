---
name: og-run
description: Runs an OG-Core country macroeconomic model the way its example scripts do - baseline and reform from the model's own environment, in parallel, with the Anderson solver - builds a multi-industry calibration, monitors the run and collects the output. Use when asked to run, solve or re-run an OG country model (OG-USA/PHL/ZAF/IDN/BRA/ETH), to produce a baseline or reform, or when another skill needs OG output that does not exist yet.
---

# Run an OG-Core country model

An OG solve is a different animal from a CLEWs solve: minutes rather than seconds, parallel
worker processes, and a two-stage structure (steady state, then transition path). Treat
launching one as a decision the user makes.

The model owner's run rules (2026-08-12), which win over anything older:

- A healthy baseline solve takes **under ten minutes**. Much longer means something is wrong
  (the worker pool, the solver settings, or the calibration), not that the model is slow.
- Run from the country repo's own environment, **the way the example scripts do it**.
  Nothing bespoke.
- Always run in parallel.
- Use the **Anderson** solver every time (`TPI_outer_method="anderson"`, available since
  ogcore 0.16.4), with a low `nu` (0.2 or lower). OG-Core's default is still damped iteration
  (`"picard"`, `nu` 0.4), and the shipped examples do not change it.

The repos' AGENTS.md files still say a full example run takes "~35 min – 2 hr"; that figure
predates these rules.

## Which world

This skill acts on **one** world: the runtime installation reached by `muiogo-ai`,
unless the user explicitly asked for their own live one (`muiogo-live`). Never use
bare `muiogo`, and never fall back to it. Every command prints a `world:` line to
stderr — read it, and name that world when you report a run or a number. Worlds
hold different OG model registries, so a model installed in one is invisible in
the other. Full rules: `../WORLD_DISCIPLINE.md`.

Orient first with `muiogo-ai status` (see `muiogo-workspace`) to find the installed
country models. Each lives in its own checkout with its own `.venv`.

## The rule that matters most

**Run the model from its own environment, from its own directory.** Never import
an OG package into another environment, and never run a country model with
another checkout's interpreter — the packages shadow each other and you will
solve the wrong model without any error.

Before launching anything, run the preflight in `og-run-preflight`. It exists
because a battery once ran silently against stale code. A passing preflight is a
precondition, never an authorization.

Minimum check by hand:

```bash
cd <og-models>/OG-PHL
git rev-parse --abbrev-ref HEAD && git rev-parse --short=8 HEAD
.venv/bin/python -c "import ogphl; print(ogphl.__file__)"
```

The printed package path must be inside the checkout you intend to run. If it
points elsewhere, stop — that is the finding.

## Launching a run

Country models ship example scripts that define the baseline and the reform:

```bash
cd <og-models>/OG-PHL
ls examples/
#   run_og_phl.py                   single-industry baseline + reform
#   run_og_phl_multi_industry.py    multi-industry calibration
```

They take no arguments; the reform is expressed inside the script as parameter
updates. Run one with the model's own environment:

```bash
uv run python examples/run_og_phl.py
```

What it does: starts a pool of worker processes (`min(cpu_count, 7)`, one thread each),
solves the **baseline** into `examples/OG-PHL-Example/OUTPUT_BASELINE/`, applies the
reform's parameter changes, solves the **reform** into `.../OUTPUT_REFORM/`, and closes the
pool. The paths are built from the script's own location, so they do not depend on the
working directory. Each stage writes `SS/SS_vars.pkl`, `TPI/TPI_vars.pkl` and
`model_params.pkl` under its output directory.

Set the solver the way the owner's rules require: `TPI_outer_method="anderson"` and a `nu` of
0.2 or lower belong in the repo's packaged parameters, not in a one-off script
(`og-country-calibration` covers this). If the repo does not set them yet, say so and ask
whether to propose that change first; running with a copy of the example that sets them is
the fallback, and say that you did it.

Propose the run with its expected duration (under ten minutes for a healthy baseline, the
reform about the same) and let the user launch it. There is no cheap smoke version: the
repo's `test_run_example.py` only checks the process is still alive after five minutes and
produces no usable output.

Two things that bite in a headless session:

- **The UN population token.** Recent ogcore (0.20 and later) looks for it in the
  `UN_API_TOKEN` environment variable, then a per-user file, then a deprecated
  `un_api_token.txt` in the working directory. It never prompts when no one is at the
  keyboard: it falls back to the EAPD-DRB Population-Data archive instead. Older ogcore
  reads only the working-directory file and can prompt. If a run seems to hang early with
  no output, check this first.
- **A run makes live API calls.** Whenever the machine is online, the example calls
  `Calibration(p, update_from_api=True)`, which refreshes parameters from live sources and
  can overwrite curated values (`og-country-calibration` covers the risk). Say so when
  proposing the run, and note whether it ran online.
- **`uv run` re-syncs the environment to the lockfile.** If the run needs an ogcore that is
  not the locked release (a local build or a branch), `uv run` silently swaps it out.
  Invoke `.venv/bin/python examples/...` directly in that case, and check
  `import ogcore; print(ogcore.__version__, ogcore.__file__)` first.
- **Custom drivers and relative paths.** If you ever drive the model from your own script,
  note that `Specifications` defaults `baseline_dir` to the relative string
  `OUTPUT_BASELINE`. The shipped examples set absolute paths and are not affected.

For a background run, have the user launch it under `nohup` or a terminal
multiplexer, teeing output to a log so progress survives a disconnect:

```bash
nohup uv run python examples/run_og_phl.py > og-phl-run.log 2>&1 &
```

Then monitor rather than re-launching:

```bash
tail -f og-phl-run.log
```

To change what is solved, do not edit the shipped example in place. Copy it and change
only what the run needs: the reform's parameter dictionary, the solver settings above, and
the output folder. Keep the example's structure (the worker pool, the calibration call, the
runner), because the owner's rule is to run the way the examples do. Say which parameters
you changed. `og-country-calibration` covers which parameters are defensible to
change and the traps in each block.

## Building a multi-industry calibration

A freshly installed country model is single-industry. Coupled OG-CLEWS work needs
multi-industry, because a single-industry model has no electricity industry for an
energy price to act on — the link reports this as `couplable=0`. Build it with the
multi-industry example:

```bash
cd <og-models>/OG-PHL
uv run python examples/run_og_phl_multi_industry.py
```

Same rules: long, propose before launching, monitor by log. Afterwards register
it with the link and confirm the calibration is recognised (see
`og-clews-linked-run`).

## Collecting the results

A completed run leaves two directories, and they are what every downstream skill
consumes:

```
OUTPUT_BASELINE/    the baseline steady state and transition path
OUTPUT_REFORM/      the same under the reform
```

Keep them together and record what produced them: the country repo, its branch
and commit, the ogcore version, which example script, which parameters were changed
(solver settings included), whether it ran online, and the run date. Without that, a comparison months later cannot be defended — the same
discipline the CLEWs side gets automatically from its `RUN.json`.

Never edit files inside an OUTPUT directory. To redo a run, re-solve.

## Checklist

Copy this and work through it:

```
- [ ] og-run-preflight reports GO for the repo and branch the task names.
      If NO-GO: fix what it names and run it again. Do not launch.
- [ ] Solver set: TPI_outer_method="anderson", nu 0.2 or lower (repo default or the copy).
- [ ] Proposed to the user: exact command, expected duration, online or not. The user launches.
- [ ] Monitor the log. If it dies at once: back to the preflight (environment, not economics).
      If it runs far past ten minutes or the distance stops falling: og-solver-diagnosis.
- [ ] Provenance written next to the output folders (see above).
```

## When a solve misbehaves

Do not restart it and hope. A solve that fails to converge, oscillates, or
returns implausible aggregates has a diagnosable cause — hand off to
`og-solver-diagnosis`, which carries the protocol and a real failure taxonomy.
Re-running a long solve on a guess wastes hours.

If the run dies immediately, it is almost always environment rather than
economics: wrong interpreter, wrong branch, missing data. Re-run the preflight.

## Handing off

- Before launching: `og-run-preflight`.
- Which parameters to set, and why: `og-country-calibration`.
- Turning finished OUTPUT dirs into the standard deliverable: `og-scenario-report`.
- Bespoke exploration and figures: `og-analysis-studio`.
- A solve that will not converge: `og-solver-diagnosis`.
- Tracing a calibrated number to its source: `calibration-provenance`.
- Coupling to the energy system: `og-clews-linked-run`.
- Explaining what the model and its calibration mean: `muiogo-explain`.

## Approval gates

Propose, draft, and prepare; the user decides. Inspecting a model, running the
preflight, and reading finished output are free. **Stop and ask before launching
any solve** — state the command and the expected duration; the user launches it.
Never run solves across several country repos on one approval. Stop before
pushing, PR-ing, merging, or deleting anything.
