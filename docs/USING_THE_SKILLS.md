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

**Simplest setup:** start your assistant in this repository (`cd MUIOGO-AI`,
then `claude` or `codex`). The skills load automatically, and you tell the
assistant where the models are — the examples below show how.

If you'd rather work from another folder, run `./scripts/install-skills.sh`
first so the skills come with you.

One caveat worth knowing: these skills expect you to say which model or folder
you mean. They don't yet read the workspace `manifest.json`, so include the path
the first time and the assistant will carry it through the conversation.

## Example 1 — Ask questions about a run you already have

The quickest way to see the value. Nothing needs to be running: solved results
sit on disk as CSV files. Ask:

> In ~/muiogo-ai-workspace/MUIOGO/WebAPP/DataStorage/CLEWs Demo, compare total
> CO2 emissions between the REF and CO2TAX runs. How much does the carbon tax
> save over the whole period?

The assistant reads the result files and answers. On the demo model that comes
with MUIOGO, the true answer is:

| Run | 2020 | 2035 | Total 2020–2035 |
|---|---|---|---|
| REF | 33,492 | 49,322 | 730,895 |
| CO2TAX | 21,248 | 43,122 | 600,590 |

So the carbon tax cuts cumulative CO2 by about 18%. Use this as a check that
your setup gives sensible answers before trusting it on your own country model.

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

```bash
client/.venv/bin/muiogo serve --root ~/muiogo-ai-workspace/MUIOGO
```

In a second terminal:

```bash
client/.venv/bin/muiogo run --case "CLEWs Demo" --run RETRG
```

It prints `status: success` and the solver's result line (about a second for
this small model). Then collect the outputs:

```bash
client/.venv/bin/muiogo results --case "CLEWs Demo" --run RETRG --out ./retrg-results
```

Or just ask your assistant: *"run the RETRG scenario on the CLEWs Demo case and
tell me how it differs from REF"* — it will use these same commands and then
read the results.

Note: no skill wraps scenario running yet. `muiogo-run` and `muiogo-scenarios`
are planned (see [SCOPE.md](SCOPE.md)); today the `muiogo` command line does
this job and your assistant drives it.

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
