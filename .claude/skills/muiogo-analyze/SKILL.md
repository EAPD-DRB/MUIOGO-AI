---
name: muiogo-analyze
description: Interpret and present results from a CLEWs/OSeMOSYS model run in MUIOGO — compare runs or scenarios, check whether a solve is trustworthy, chart trajectories, break results down by technology or fuel, and write short analytical notes. Use when asked what a CLEWs run shows, how two runs or scenarios differ, what drives a difference, whether results look right, or for a chart, table, summary, or policy write-up from CLEWs results. This is the CLEWs/MUIOGO side only: for OG-Core baseline-vs-reform output use og-scenario-report, and for bespoke OG exploration use og-analysis-studio.
---

# Interpret and present CLEWs results

Orient with `muiogo-ai status` if you do not know where the model data is (see
`muiogo-workspace`). Nothing here re-runs a model: it reads the result files a
solve already produced. If a run has no results, hand back to `muiogo-run`.

## Which world

Everything below acts on ONE world — the installed runtime, reached through the
pinned launcher `muiogo-ai`. Never bare `muiogo`, and never fall back to it.
Every command prints a `world:` line to stderr first: read it, and name that
world when you report a number, a chart, or a comparison. Exit code 3 means the
command refused a world crossing — stop, do not sidestep it. Full rules:
`../WORLD_DISCIPLINE.md`.

## Check the solve before believing the numbers

Interpreting a bad solve is worse than not interpreting at all.

```bash
muiogo-ai variables --case "<case>" --run <run>
```

That lists the result variables a run produced. If it reports no results, the run
was never solved or the solve failed — stop and say so. Then sanity-check:

- **Status.** The solver's verdict is the first line of `res/<run>/results.txt`
  inside the case. Locate the case absolutely rather than typing a relative
  path:

  ```bash
  CASE="$(muiogo-ai case-path --case '<case>')"
  head -1 "$CASE/res/<run>/results.txt"
  ```

  "Optimal" is what you want; anything else invalidates the analysis.
- **Provenance.** `muiogo-ai compare` warns when a run has no `RUN.json`, which
  means nobody can say what produced it. Pass that warning on to the user, or
  settle it with `muiogo-ai verify --case "<case>" --run <run> --resolve`, which
  re-solves and proves whether the stored numbers still hold.
- **Plausibility.** Demand met, no wild capacity spikes, costs and emissions in a
  believable range for the country's size.
- **Direction.** A policy run must move in the direction the policy implies. A
  carbon tax that raises emissions means the overlay did not apply — check with
  `muiogo-ai scenarios --case "<case>"` that the run activates what you think.
- **Structure.** If numbers look impossible, the model may be malformed rather
  than mis-solved — hand off to `clews-model-review`.

Report negative or zero values where they are surprising rather than smoothing
them over. They are usually informative: a negative emission total, for example,
means something in the system is acting as a sink.

## Compare runs

```bash
muiogo-ai compare --case "<case>" --runs REF,CO2TAX --var AnnualTechnologyEmission --filter e=CO2
```

It prints first year, last year, cumulative total, and percentage change against
the first series listed — so put the baseline first. Add `--table` for the full
year-by-year matrix.

Common variables (use `muiogo-ai variables` for the full list of a given run):

| Variable | Question it answers |
|---|---|
| `AnnualTechnologyEmission` | emissions by technology (filter `e=CO2`) |
| `TotalCapacityAnnual` | installed capacity over time |
| `NewCapacity` | what gets built, and when |
| `ProductionByTechnologyAnnual` | who produces what — the generation mix |
| `Demand` | demand served |
| `TotalDiscountedCost` | system cost, for cost-of-policy comparisons |
| `UseByTechnology` | fuel and resource consumption |

Filters and breakdowns take OSeMOSYS dimension letters: `r` region, `t`
technology, `f` fuel, `e` emission, `y` year, `l` timeslice, `m` mode, `s`
storage.

## Find what drives a difference

Totals tell you *whether*; a breakdown tells you *why*.

```bash
muiogo-ai compare --case "<case>" --runs CO2TAX --var AnnualTechnologyEmission \
    --filter e=CO2 --by t --top 8
```

That splits one run by technology, keeping the eight largest. Run it for the
baseline too and compare the composition: the technologies that shrink and the
ones that grow to replace them are the story.

## Charts

```bash
muiogo-ai compare --case "<case>" --runs REF,CO2TAX,HITAX \
    --var AnnualTechnologyEmission --filter e=CO2 --chart ./co2.png
```

`--kind line` (default) for trajectories, `area` for composition over time
(pair it with `--by`), `bar` for a small number of periods. Charting is headless
— no display needed — and writes a PNG you can hand to the user.

Keep a chart to one idea. If you are showing both emissions and cost, make two
charts rather than a double axis. State the units in your surrounding text: the
model's parameter files carry them, the result CSVs do not.

## Write it up

When asked for a note, brief, or summary, lead with the finding, then the
evidence, then the caveat. A worked example, from the demo model:

> Scaling the carbon price sharply reduces cumulative emissions, with clearly
> diminishing returns. At the current price (0.025), cumulative CO2 over
> 2020–2035 falls 29.8% against the reference case, from 730,895 to 513,337
> tonnes. Doubling the price roughly doubles the saving (−63.3%), while
> quadrupling it adds only a further seven points (−70.5%) and going to eight
> times adds almost nothing (−71.0%) — the cheap abatement is exhausted well
> before the top of that range.
>
> The reduction comes from displacing fossil generation with renewables, with
> capacity additions shifting accordingly from 2021 onward.
>
> This is the demo dataset, so the levels are illustrative; the shape of the
> response is the transferable result.

Rules for these write-ups:

- **Plain language.** Name the policy and the outcome, not the variable names.
  "Cumulative CO2 falls 29.8%", not "AnnualTechnologyEmission decreased".
- **Absolute and relative.** Give the percentage and the levels, with units.
- **Say what is uncertain.** Demo data, an uncalibrated model, or a single
  scenario is a caveat the reader needs.
- **Never invent a number.** Every figure comes from a command you ran. If you
  did not compute it, do not state it — and that includes results already
  sitting in a case. Stored results can predate the input data that is there
  now: MUIOGO's own demo ships a CO2TAX result of 600,590 that its current data
  reproduces as 513,337. If a comparison matters, re-solve first.

## Handing off

- No results, or a failed solve → `muiogo-run`.
- Need a different policy setting to compare → `muiogo-scenarios`.
- Results look structurally impossible → `clews-model-review`.
- Judging whether the model is fit for the question at all →
  `assess-clews-calibration`.
- OG-Core runs are a different family → `og-scenario-report`,
  `og-analysis-studio`.

## Approval gates

Propose, draft, and prepare; the user decides. Reading results and producing
charts and notes is free. Stop and ask before re-running anything (a re-run
deletes the previous results), and before pushing, PR-ing, or merging.
