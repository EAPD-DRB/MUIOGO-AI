---
name: muiogo-scenarios
description: Create and run policy scenarios in a MUIOGO CLEWs case — build a new scenario such as a carbon tax, renewable target, or demand change; combine existing scenarios into runs; and sweep a scenario matrix. Use when asked to add, design, build, or modify a scenario; to test a policy, tax, target, subsidy, or constraint; to set up a "what if" case; to combine two scenarios; to run a sweep, matrix, or sensitivity over several scenario settings; or to change a model parameter and see the effect. This skill BUILDS and runs scenarios; to compare or chart the results afterwards use muiogo-analyze.
---

# Create and run scenarios in a MUIOGO CLEWs case

Orient first with `muiogo-ai status` if you do not know where the model data is
(see `muiogo-workspace`). All paths below come from that output.

## Which world

This skill acts on ONE MUIOGO installation. Use the pinned launcher `muiogo-ai`
throughout — never bare `muiogo`, and never fall back to it; `muiogo-live` only
when the user explicitly asked for their own checkouts. Every command prints a
`world:` line to stderr: read it, and name that world when you report a
scenario, a run, or a number. Scenario edits are permanent, so the wrong world
cannot be undone. Full rules: `../WORLD_DISCIPLINE.md`.

## The model you are working with

Three layers, and confusing them is the main source of mistakes:

1. **The case** — one country/system model. Its structure lives in
   `<data storage>/<case>/genData.json`: years, technologies, commodities,
   emissions, timeslices, and the scenario definitions under `osy-scenarios`.
2. **Scenarios** — named *parameter overlays*. Each has a `ScenarioId` (`SC_0`
   is always the base) and a `Scenario` name. Parameter values live in the
   `R*.json` files keyed **parameter code → ScenarioId → rows**, and every
   scenario carries a complete slice of every parameter, holding zeros where it
   does not override anything.
3. **Runs** — named *combinations* that switch scenarios on. The set lives in
   `<case>/view/resData.json`; each run lists every scenario with an `Active`
   flag. Solving a run merges the active overlays onto the base.

The paths above describe MUIOGO's internal layout — they are not paths to type.
Never address a case relatively; ask this world for it:
`CASE="$(muiogo-ai case-path --case '<case>')"` returns an absolute directory and
fails if the case is not in this world.

So on the demo case: `REF` activates only `SC_0`; `CO2TAX` activates `SC_0` plus
`CO2_tax`. The `CO2_tax` overlay is simply a non-zero emission penalty (`EP`) on
CO2 in that scenario's slice, while every other scenario has zeros there.

See what a case has:

```bash
muiogo-ai scenarios --case "CLEWs Demo"
```

## Combining existing scenarios (the easy, common job)

A new run is just a different activation set — no parameter editing at all:

```bash
muiogo-ai new-run --case "CLEWs Demo" --run COMBO --activate CO2_tax,RE_Target
muiogo-ai run     --case "CLEWs Demo" --run COMBO
```

The base scenario is always included; you name the overlays to add. This is how you answer "what if we did both?" — and the answer is often
instructive. On the demo case, the renewable target alone cuts cumulative CO2 by
3.2% (730,895 → 707,668) and the carbon tax alone by 29.8% (→ 513,337), but
combining them gives 513,337 — exactly the tax alone. The target is not binding
once the tax is in place, because the tax already drives more renewables than
the target requires. Report that kind of result; a combination that adds nothing
is a real finding, not a failed run.

## Creating a new scenario

Because every scenario needs a complete parameter slice, do not hand-write one.
Seed it from an existing scenario, then change only what defines your policy.
The bundled script does exactly that:

```bash
CASE="$(muiogo-ai case-path --case 'My Case')"
python3 <this skill>/scripts/new_scenario.py \
    --case "My Case" --name High_CO2_tax --desc "CO2 tax at 4x" \
    --copy-from CO2_tax \
    --set RYE.json:EP:EMI_6ku9o:x4 \
    --data-storage "$(dirname "$CASE")"
```

It registers the scenario, copies a full slice from `--copy-from` (default: the
base), applies any `--set` multipliers, and tells you the next commands. It
writes through MUIOGO's HTTP API and refuses to guess a world, so run it from a
shell a launcher started, or pass `--url` (the `world:` line any `muiogo-ai`
command prints carries this world's URL). Then:

```bash
muiogo-ai new-run --case "My Case" --run HITAX --activate High_CO2_tax
muiogo-ai run     --case "My Case" --run HITAX
```

**Work on a copy while experimenting.** `muiogo-ai copy --case "My Case"` makes
`My Case_copy`; scenario edits change the case's data for every future run, and
there is no undo.

Choose `--copy-from` deliberately: copying from a scenario that already has the
policy you want to scale (as above) means one `--set` finishes the job. Copying
from the base gives you a clean slate.

### Which parameter is your policy?

Row ids in a slice end in `Id` (`TechId`, `EmisId`, `CommId`, `StgId`) and the
year columns are plain years. The parameter codes, by file:

| File | Codes | What they are |
|---|---|---|
| `RYE.json` | `EP`, `AEL` | emission penalty (a carbon tax), annual emission limit |
| `RYC.json` | `SAD`, `AAD` | specified and accumulated annual demand |
| `RYT.json` | `CC`, `FC`, `AF`, `RC`, `TAMaxC`, `TAMinC`, `TAL`, `TAU` | capital cost, fixed cost, availability factor, residual capacity, capacity limits, activity limits |
| `RYTM.json` | `VC`, `TAMLL`, `TAMUL` | variable cost, mode activity limits |
| `RYTCM.json` | `IAR`, `OAR` | input and output activity ratios |
| `RYTEM.json` | `EAR`, `EACR` | emission activity ratios |
| `RYTC.json` | `INCR`, `ITCR` | capacity ratios |
| `RYS.json` | `CCS`, `RSC`, `MSC` | storage capacity and limits |
| `R.json` / `RT.json` | `DR`, `DRI`, `OL`, `CAU` | discount rate, operational life, capacity/activity unit |

To find the exact row id for the thing you care about — a technology, a
commodity, an emission — look it up in `genData.json` under `osy-tech`,
`osy-comm`, or `osy-emis`, matching the human name to its id.

Direct edits are also possible without the script, through
`POST /updateData` with `{param, data, dataJson}` where `data` is the whole
parameter block for that file. The script exists so you do not have to get the
completeness right by hand.

## Sweeping a matrix

For a dose-response or a two-factor grid, create one scenario per level, one run
per combination, then batch-solve:

```bash
# three tax levels seeded from the existing tax scenario
DS="$(dirname "$(muiogo-ai case-path --case 'My Case')")"
for f in 2 4 8; do
  python3 <skill>/scripts/new_scenario.py --case "My Case" --name Tax_x$f \
      --copy-from CO2_tax --set RYE.json:EP:EMI_6ku9o:x$f --data-storage "$DS"
  muiogo-ai new-run --case "My Case" --run TAX_X$f --activate Tax_x$f
done
muiogo-ai batch --case "My Case" --runs TAX_X2,TAX_X4,TAX_X8
```

Then check the response is monotonic and sensible before believing it. On the
demo case, scaling the carbon tax gives:

| Tax level | Cumulative CO2 | vs REF |
|---|---|---|
| 0 (REF) | 730,895 | — |
| 0.025 (shipped CO2TAX) | 513,337 | −29.8% |
| 0.050 (x2) | 268,245 | −63.3% |
| 0.100 (x4) | 215,949 | −70.5% |
| 0.200 (x8) | 212,259 | −71.0% |

Monotonically decreasing, with diminishing returns at the top — the shape you
should expect. A sweep that is flat, non-monotonic, or moves the wrong way means
the overlay did not apply or the parameter is not the one you think it is. Check
the scenario's slice actually holds your values before reporting results.

## Verify a scenario actually took effect

Do not trust `status: success` alone — a run can solve while your overlay did
nothing.

1. The new scenario appears: `muiogo-ai scenarios --case "<case>"`.
2. The run activates it: same command shows the run and its active scenarios.
3. The numbers moved in the expected direction, versus the run without it.

If results are identical to the base, the overlay is empty: confirm the row id
and parameter code, and that you edited the new scenario's slice.

## Handing off

- Solving, batching, failures, saving results → `muiogo-run`.
- Comparing runs, charts, write-ups → `muiogo-analyze`.
- The model will not solve, or a scenario makes it infeasible →
  `clews-model-review`.
- Adding a whole sector rather than a policy overlay → `add-fisheries-sector`
  or `add-environmental-accounting`.
- OG-Core reforms are a different family — see `og-analysis-studio`.

## Approval gates

Propose, draft, and prepare; the user decides. Scenario edits change a case
permanently, so say what you are about to change and work on a copy when
exploring. Stop and ask before launching a long batch (propose the runs and the
expected duration), deleting a case, scenario, or run, and before pushing,
PR-ing, or merging anything.
