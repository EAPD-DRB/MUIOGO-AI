---
name: muiogo-workspace
description: Orient yourself in a MUIOGO-AI installation before doing any CLEWs, OG-Core, or OG-CLEWS work — find where MUIOGO, the country models, the OG-CLEWs link, and the model data are installed, list what is available, and route the request to the right model family and skill. Use this FIRST whenever a request touches CLEWs/OSeMOSYS, MUIOGO, OG-Core, a country model, a scenario, a run, or model results and you do not already know the installation paths; when the user says "my model", "my country", "the Philippines model", or names a case or scenario without a path; when asked what you can do with these models; or when a path you were given does not exist.
---

# Orient yourself in a MUIOGO-AI installation

You are probably being asked to do modelling work in a directory that has
nothing to do with where the models are installed. Do not guess paths, and do
not ask the user where things are. Find out.

## Which world

This skill acts on ONE world at a time. Call the pinned launcher `muiogo-ai`
(the installed runtime), or `muiogo-live` only when the user explicitly asked for
their own live installation — never bare `muiogo`, and never fall back to it.
Every command prints a `world:` line to stderr as its first output: read it, and
name that world whenever you report anything. Exit code 3 means a world crossing
was refused — stop and say so. Full rules: [../WORLD_DISCIPLINE.md](../WORLD_DISCIPLINE.md).

## First move, always

```bash
muiogo-ai status
```

That prints the whole installation and needs no running server:

```
world: runtime (installed) · http://127.0.0.1:5102 · <workspace>/MUIOGO [pinned by launcher]
world         INSTALLED  (a self-contained runtime built by the installer)
manifest      /Users/<you>/.muiogo/manifest.json
workspace     /Users/<you>/muiogo-ai
installed     2026-07-28T11:09:12
MUIOGO        <workspace>/MUIOGO  (ref 3db8b816)
model data    <workspace>/MUIOGO/WebAPP/DataStorage
server URL    http://127.0.0.1:5102
server        not running   (start it: muiogo-ai serve)
  case        CLEWs Demo
  case        Philippines_v12_ENV_LAND_WATER_DIAGNOSTIC
  OG model    og-phl  /Users/<you>/.muiogo/og-models/OG-PHL
  link        <workspace>/ogclews-link
  solvers     glpk=True cbc=True
```

The first line goes to stderr and names the world; the rest is the installation
itself. `muiogo-ai status --json` gives the same thing machine-readably when you
are scripting rather than reading. `muiogo worlds` lists every workspace on the
machine and marks the active one — worth checking whenever a path looks
unfamiliar, because a machine may carry both a **live** world (adopted checkouts
someone runs manually, on their own branches, port 5002) and an **installed**
runtime (self-contained, port 5102). Never assume which one you are in, and use
`worlds` only to orient, never to pick a target: the target comes from the
launcher you called.

Take every path from that output. Never hardcode a path, and never reuse a path
from an example — including the examples in this or any other skill file. For a
case, ask for its absolute path rather than composing one:

```bash
CASE="$(muiogo-ai case-path --case '<case name>')"   # absolute, in this world
```

### If `muiogo-ai` is not found

Try its full path first — `~/.local/bin/muiogo-ai status` — because a launcher
that exists but is off PATH is the common case. Do not fall back to bare
`muiogo`. If it is not there either, the tooling is not installed; tell the user

> I can't find the `muiogo-ai` launcher, which means the MUIOGO-AI tooling isn't
> installed on this machine. From a MUIOGO-AI checkout, `uv tool install ./client`
> installs it, and `./scripts/install.sh` sets up the whole stack.

### If it reports no workspace

Check first whether the user already has the models — most people do, and
installing again would build a second multi-gigabyte copy:

```bash
muiogo adopt --scan      # what is already on this machine
muiogo adopt --auto      # record it as the live world, installing nothing
```

`adopt` and `worlds` are the only bare `muiogo` commands in this skill: they are
about the worlds themselves, not work inside one, and `adopt` registers the
user's own checkouts as the **live** world — so propose it and let the user say
yes. Everything else goes through `muiogo-ai`.

Only if that finds nothing:

> No MUIOGO-AI workspace is installed. `./scripts/install.sh` from a MUIOGO-AI
> checkout will build one, or set `MUIOGO_WORKSPACE` if it lives somewhere
> unusual.

### If the paths look wrong

If `muiogo-ai status` reports a workspace in a temporary directory, or a path the
user does not recognise, it is pointing at a stale installation. `muiogo adopt
--scan` shows the real checkouts and `--auto` re-points at them.

### If a component is missing

`muiogo-ai status` lists only what is installed. No OG model line means no OG
country model is installed; no link line means the OG-CLEWs link is absent. Say
so plainly rather than attempting the work — for example, a coupled OG-CLEWS run
is impossible without both an OG model and the link.

## Two model families, and how to tell which one is meant

This is the single most common way to get a request wrong. The same country
usually exists in **both** families, and they are completely different models:

| | CLEWs / OSeMOSYS | OG-Core |
|---|---|---|
| What it is | energy, land, water systems; a cost-minimising capacity/dispatch model | overlapping-generations macroeconomic model; fiscal and demographic policy |
| Lives in | MUIOGO's model data: `<data storage>/<case>/` | its own repo + venv: `<og-models>/OG-XXX/` |
| Driven by | the `muiogo-ai` command line (HTTP API) | that repo's own Python (`uv run …`), never imported here |
| Units of work | a **case**, its **scenarios**, and **runs** | a baseline and a reform |
| Results | `res/<run>/csv/*.csv` | `OUTPUT_BASELINE/` and `OUTPUT_REFORM/` |

So "run the Philippines model" is ambiguous whenever both are installed. Resolve
it from the request, not from the country name:

- Mentions electricity, generation, capacity, emissions, water, land, crops,
  demand, a carbon tax on the energy system → **CLEWs**.
- Mentions GDP, debt, deficit, taxes on labour or capital, pensions,
  demographics, wages, welfare, revenue → **OG-Core**.
- Mentions both, or "the effect of the energy plan on the economy" → this is a
  **coupled** OG-CLEWS question; you need the link.
- Genuinely unclear → ask one short question naming the two candidates from
  `muiogo-ai status`, e.g. *"the CLEWs energy model `Philippines_v12_…` or the
  macro model `OG-PHL`?"*

## Where to go next

Once you know the layout, hand off to the skill that owns the job:

| The user wants to… | Use |
|---|---|
| install a country model, import a case or workbook, export or validate | `muiogo-provision` |
| move model work between laptops or publish to the country repos | `pull-handoff`, `push-handoff` |
| solve a case, batch several, collect results | `muiogo-run` |
| build a policy scenario, combine scenarios, sweep a matrix | `muiogo-scenarios` |
| compare runs, check solution health, chart, write up findings | `muiogo-analyze` |
| judge whether a CLEWs model is calibrated well | `assess-clews-calibration` |
| check a CLEWs model's structure and data consistency | `clews-model-review` |
| build a new CLEWs country model from scratch | `build-clews-model` |
| add a fisheries sector / environmental accounting | `add-fisheries-sector`, `add-environmental-accounting` |
| understand a model, its calibration, the theory, the intuition | `muiogo-explain` |
| run a coupled OG-CLEWS analysis (energy policy → the economy) | `og-clews-linked-run` |
| run an OG country model (baseline, reform, multi-industry) | `og-run` |
| calibrate an OG country model | `og-country-calibration` |
| report on a finished OG baseline-vs-reform run | `og-scenario-report` |
| free-form OG scenario design and bespoke analysis | `og-analysis-studio` |
| check before launching a long OG solve | `og-run-preflight` |
| diagnose an OG solve that will not converge | `og-solver-diagnosis` |
| trace a calibrated parameter to its source | `calibration-provenance` |

If a skill in that table is not available to you, the user installed only some
of them; do the job directly and say which skill would have covered it.

## The model data layout (CLEWs side)

This describes how MUIOGO arranges a case on disk; it is not a path to type.
Everything sits under `<data storage>/<case>/`:

```
genData.json          the case: years, technologies, commodities, emissions,
                      timeslices, and osy-scenarios (the scenario definitions)
R*.json, RY*.json …   parameter values, keyed by parameter → ScenarioId → rows
view/resData.json     the runs: each names the scenarios it activates
res/<run>/            one solved run
  data.txt            generated model input
  results.txt         raw solver output (first line carries the status)
  csv/*.csv           parsed results, one file per output variable
```

A case with no `res/` has never been solved. A `res/<run>/` with no `csv/`
means that run failed. Case names contain spaces — always quote them.

To reach any of it, start from `muiogo-ai case-path --case '<name>'`, which
returns the absolute directory inside this world and fails if the case is not
here. Never write `WebAPP/DataStorage/<case>` as a command argument: it resolves
against whatever directory you happen to be in, which is how a same-named case
in the other world gets edited by accident.

## Working rules

- **Stay in the world you were called in.** If a case or model is not in the
  world `muiogo-ai` reports, say so — do not go looking for it in the live world,
  and do not switch worlds to make an error go away (`muiogo use` is not yours to
  call). Name the world in what you report.
- **Read through the command line, not the internals.** `muiogo` talks to
  MUIOGO's HTTP API, which is the same path its web interface uses, so results
  are identical. Never import MUIOGO's Python modules and never edit files
  under `res/` by hand.
- **Report what you observe.** If a solve fails, say so with the solver's
  message. A run that returns HTTP 200 can still have failed — the status field
  in the response body is what counts, and `muiogo` already checks it.
- **Approval gates.** Propose, draft, and prepare; the user decides. You may
  edit files and commit locally. Stop and ask before: pushing to a remote,
  opening a pull request, merging, launching a long computation (an OG solve, a
  large batch — propose the command and expected duration), acting across many
  repositories at once, or deleting anything. These gates bind every skill in
  this collection.
