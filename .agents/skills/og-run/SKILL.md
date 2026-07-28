---
name: og-run
description: Run an OG-Core country macroeconomic model — launch a baseline and reform solve from the model's own environment, build a multi-industry calibration, monitor progress, and collect the OUTPUT directories. Use when asked to run, solve, or execute an OG-Core or OG country model (OG-USA/PHL/ZAF/IDN/BRA/ETH), to produce a baseline or reform, to re-run after a calibration change, to build a multi-industry calibration, or when another skill needs OG output that does not exist yet.
---

# Run an OG-Core country model

An OG solve is a different animal from a CLEWs solve: 35 minutes to 2 hours
rather than seconds, parallel worker processes, and a two-stage structure (steady state, then
transition path). Treat launching one as a decision the user makes.

Orient first with `muiogo status` (see `muiogo-workspace`) to find the installed
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

What it does: starts a pool of worker processes (up to seven, one thread each),
solves the **baseline** into `OUTPUT_BASELINE/`, applies the reform's parameter
changes, solves the **reform** into `OUTPUT_REFORM/`, and closes the pool. Each
stage writes `SS/SS_vars.pkl`, `TPI/TPI_vars.pkl` and `model_params.pkl` under
its output directory.

**This takes roughly 35 minutes to 2 hours** (the repo's own AGENTS.md says so).
Propose it with that duration and let the user launch it. There is no cheap smoke
version: the repo's `test_run_example.py` only checks the process is still alive
after five minutes and produces no usable output.

Two things that bite in a headless session:

- **An interactive prompt can block the run.** Building demographics asks for a
  UN API token on standard input if `un_api_token.txt` is not in the working
  directory. It degrades gracefully when there is no terminal, and falls back to
  the EAPD-DRB Population-Data mirror if the API refuses — but if a run appears
  to hang early with no output, this is the first thing to check. Put the token
  file in the working directory beforehand, or accept the fallback knowingly.
- **The reform finds its baseline by a relative path.** `baseline_dir` defaults
  to the string `OUTPUT_BASELINE`, resolved against the working directory — so a
  reform launched from a different directory than its baseline will not find it.
  Keep both stages in one working directory, or set the paths explicitly.

For a background run, have the user launch it under `nohup` or a terminal
multiplexer, teeing output to a log so progress survives a disconnect:

```bash
nohup uv run python examples/run_og_phl.py > og-phl-run.log 2>&1 &
```

Then monitor rather than re-launching:

```bash
tail -f og-phl-run.log
```

To change what is solved, do not edit the shipped example in place. Copy it, or
better, write a small driver script of your own that imports the model, sets
`output_base` to wherever you want results, and applies your reform as a
parameter dictionary — verified to work from any working directory with absolute
paths, which keeps the model's checkout clean. Either way, say which parameters
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
and commit, which example script, which parameters were changed, and the run
date. Without that, a comparison months later cannot be defended — the same
discipline the CLEWs side gets automatically from its `RUN.json`.

Never edit files inside an OUTPUT directory. To redo a run, re-solve.

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
