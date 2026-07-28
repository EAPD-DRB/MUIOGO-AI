# Using the skills

How to actually ask an AI assistant to do the modelling work, with three
worked examples you can copy. Every command and number below was run against a
real installation.

## How you invoke a skill

You don't call a skill like a command. You describe the job in plain language
and your assistant matches it to a skill by its description:

> assess how well this CLEWs model is calibrated

If you'd rather be explicit, name it directly:

- **Claude Code**: `/assess-clews-calibration`
- **Codex**: `$assess-clews-calibration`

The catalogue of what's available is [SKILLS.md](../SKILLS.md).

## Where you need to be

Three separate things, worth keeping straight:

| Thing | Where it lives |
|---|---|
| **The skills** | Active automatically inside this repository. For other projects, run `./scripts/install-skills.sh` once. |
| **MUIOGO and your models** | The workspace the installer created: `~/muiogo-ai-workspace/MUIOGO`, with model data under `WebAPP/DataStorage/`. |
| **Your assistant session** | Wherever you start Claude Code or Codex. |

**You don't have to keep these straight — the assistant does it.** The installer
records where everything is, and the first thing your assistant does is ask:

```bash
muiogo status
```

That prints the installation from any directory, with no server running, so you
can start your assistant wherever you like and simply describe what you want.
Working outside this repository just needs `./scripts/install-skills.sh` once, so
the skills come with you.

## Example 1 — Ask questions about a run you already have

The quickest way to see the value. Nothing needs to be running: solved results
sit on disk as CSV files. Ask:

> Compare total CO2 emissions between the REF and CO2TAX runs of the CLEWs Demo
> case. How much does the carbon tax save over the whole period?

The assistant reads the result files and answers. On the demo model that comes
with MUIOGO, the true answer is:

| Run | 2020 | 2035 | Total 2020–2035 |
|---|---|---|---|
| REF | 33,492 | 49,322 | 730,895 |
| CO2TAX | 21,248 | 32,950 | 513,337 |

So the carbon tax cuts cumulative CO2 by about 30%. Use this as a check that
your setup gives sensible answers before trusting it on your own country model.

One caveat that matters: **re-solve before comparing.** The results MUIOGO ships
inside the demo case are stale for CO2TAX — they report 600,590, which the
shipped input data no longer reproduces. `muiogo run --case "CLEWs Demo" --run
CO2TAX` gives 513,337, reproducibly. Numbers you did not generate yourself are
not evidence.

Follow-ups that work the same way: *"which technologies drive the difference?"*,
*"chart electricity generation by fuel for CO2TAX"*, *"write me two paragraphs
on this for a policy audience"*.

## Example 2 — Review a model's structure (a real skill)

This one uses the `clews-model-review` skill, which checks a model against a
reference for orphaned IDs, stranded commodities, unit slips, and solve status.
Ask:

> Review the CLEWs Demo model in ~/muiogo-ai-workspace/MUIOGO/WebAPP/DataStorage
> for structure and data consistency

The skill runs its bundled checker. You can also run it yourself:

```bash
python3 .agents/skills/clews-model-review/audit.py --datastorage ~/muiogo-ai-workspace/MUIOGO/WebAPP/DataStorage "CLEWs Demo"
```

On the demo model it reports 16 years (2020–2035), 30 technologies, 22
commodities, 4 scenarios all solving optimally — and one real finding: two water
commodities (`WTREVT`, `WTRGWT`) are produced but have no consumer, so they are
stranded. That is the kind of thing the skill exists to catch.

## Example 3 — Run a scenario

Start the server, then run one of the demo scenarios:

> Run the RETRG scenario on the CLEWs Demo case and tell me how it differs
> from REF

The `muiogo-run` skill handles it. By hand, the same thing is:

```bash
muiogo serve &                                        # start the server
muiogo run --case "CLEWs Demo" --run RETRG            # generate input + solve
muiogo results --case "CLEWs Demo" --run RETRG --out ./retrg-results
```

## Example 4 — Build a policy scenario of your own

The `muiogo-scenarios` skill covers this. Ask:

> Create a scenario on a copy of the CLEWs Demo case with the carbon tax at four
> times its current level, run it, and chart the emissions against the original

It will copy the case first (scenario edits are permanent), seed a new scenario
from the existing tax one, scale the emission penalty, create a run that
activates it, solve, and chart. On the demo model, scaling the tax gives a
monotonic response: 730,895 tonnes with no tax, 513,337 at the shipped level,
268,245 at double, 215,949 at quadruple.

## If the assistant ignores the skill

- Name it explicitly: `/skill-name` in Claude Code, `$skill-name` in Codex.
- Check it's there: `./scripts/install-skills.sh --list`.
- If you just installed or changed a skill, restart the assistant so it
  re-reads them.
- Working outside this repository? The skills need installing first.

## What the skills will and won't do on their own

Every skill in this repository proposes and prepares; you decide. A skill may
edit files and commit locally, but it stops and asks before pushing to a
remote, opening a pull request, merging, launching a long computation, acting
across many repositories at once, or deleting anything.
