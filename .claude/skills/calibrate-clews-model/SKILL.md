---
name: calibrate-clews-model
description: "Implement or refine a country calibration in an existing MUIO/OSeMOSYS CLEWs model with equation-first, non-forcing, sourced changes: stocks, lifetimes, demand, costs, efficiencies, historical pins, calibration-induced infeasibility. Not for structural cleanup, dead-object removal, descriptions or technology grouping - use clews-model-fix. To grade instead, assess-clews-calibration."
---

# Calibrate a CLEWs model

Implement calibration as a reproducible model change, not as a search for a
solver result that resembles history. Read the repository instructions, the
active local formulation, and the application export code before editing.

## Triage before anything else

The evidence a change requires scales with what the change can affect — not with the
importance of the model. Classify first, then take the matching path:

| Class | Test | Path |
|---|---|---|
| **A — structural** | No parameter value changes and no source data changes | **Stop. Use `clews-model-fix`.** |
| **B — sourced parameter change** | A number changes, chosen *without* reference to an observed outcome | **The Class B short path below.** No plan. |
| **C — calibration** | A value chosen *with reference to* an observed outcome | This skill, in full |

The discriminator is the counterfactual test: *would this exact change still be made if no
historical outcome were known?* Yes → A or B. No → C. Full rules in
[references/non-forcing.md](references/non-forcing.md).

Deleting a dead technology, fixing a description, or regrouping technologies is Class A. It
does not need a calibration plan, a control run, an A/B test or a checksum register. Do not
run the gate below on it.

## The Class B short path

A sourced number that was not chosen by looking at an outcome does **not** need a calibration
plan, a control solve, or an A/B rollback. It needs six things:

1. **Provenance.** A source (or calculation) and assumption record, and a `MODEL_MAP` row —
   [references/SCHEMA.md](references/SCHEMA.md). This is the point of
   the exercise, and it is minutes.
2. **The equation and the units.** Read the local equation that consumes the parameter and
   confirm the unit and the direction (input/output ratios invert). This is lookup, not
   computation. It is where a good number gets written into the wrong parameter family.
3. **A clean diff.** Referential integrity holds and nothing else changed. Work on a
   disposable case; change source parameters only.
4. **Family-scoped pre-solve checks.** Run only the gates in step 5 that your parameter
   family can break — see the scoping table there. A fuel price and an initial stock are both
   "one number" and warrant very different scrutiny.
5. **One solve.** Unavoidable and not ceremony: a single number re-optimises the system, so
   the effect cannot be known without solving.
6. **Compare against the stored baseline** — not a freshly re-solved one. Objective, runtime,
   and the activities/capacities the parameter touches.

**Escalate to the full path** — control solve, A/B rollback, the whole gate set — only when
something moved that should not have, the runtime regresses, the solve is infeasible, or the
stored baseline turns out to be stale or mismatched. Escalation is a response to evidence,
not a precondition.

Record the change in `CHANGES.csv` with `class=B`.

## Mandatory design gate

**Class C only.** Class B uses the short path above and never creates a plan; do not run the
plan validator on a Class B change.

Before the first full solve:

1. Copy `assets/calibration-plan.template.json` into the case documentation
   and complete it.
2. Classify every observation as exactly one of:
   `initial_stock`, `final_demand`, `real_world_constraint`, or
   `benchmark_only`.
3. Map every changed parameter to its source JSON file, local formulation
   equations, generated-data representation, and physical effect.
4. List explicit technology roles. Never infer physical stock,
   pass-through, accounting, conversion, or backstop behavior from a name
   prefix alone.
5. Register full-precision initialization inputs and their checksums. Do not
   initialize source parameters from rounded display CSVs when lossless solver
   or source data exist.
6. Define the unchanged control, last known-good runtime, candidate time
   budget, and minimal A/B strategy.
7. Run:

   ```bash
   python scripts/validate_calibration_plan.py PLAN.json --stage design
   ```

Do not run a full optimization while this gate fails.

## Non-forcing rules

[references/non-forcing.md](references/non-forcing.md) is authoritative. Read it before
introducing any parameter or constraint. Two additions specific to calibration:

- Distinguish stock turnover from utilization. Capacity and lifetime assumptions can limit
  replacement speed; they do not guarantee smooth dispatch among already available
  technologies.
- Keep benchmark-only observations out of source parameters.

Read [references/stock-turnover-patterns.md](references/stock-turnover-patterns.md)
when stocks, lifetimes, turnover, adoption or free switching are in scope.

## Equation-first workflow

Written for Class C. A Class B change takes the short path above and touches only steps 2,
4, the always-gates in 5, and a single solve in 6.

### 1. Establish a trustworthy baseline

- Confirm case, run, scenario, horizon, solver status, result timestamp and
  source identity.
- Hash the baseline source, generated inputs and full-precision result.
- Reject stale or mismatched results. Solve a fresh unchanged control when
  necessary.
- Record objective, runtime, matrix dimensions and the affected baseline
  activities, capacities, demands, emissions, balances and backstops.

### 2. Trace the implementation path

- Locate `genData.json`, parameter JSON files, `Parameters.json`,
  `Variables.json`, the active solver formulation, `UpdateCase`,
  `DataFile.generateDatafile`, preprocessing and result export.
- For every proposed parameter, read the exact local equation that consumes
  it. Do not rely on parameter names or remembered OSeMOSYS behavior.
- Trace structural edits through `genData.json` and `UpdateCase`. Trace
  numerical edits from source JSON through generated data and derived sets.

### 3. Design from physical evidence

- Prefer observed stocks, commissioning or age cohorts, sales,
  registrations, retirements, survival curves, operational lives, service
  demands and utilization.
- Where no physical stock maps defensibly, use an effective initial stock only
  when its derivation preserves timeslice, availability and
  capacity-to-activity effects and is documented as an assumption.
- Separate official data, inherited model values, engineering assumptions and
  numerical safeguards.
- For each derived value record source IDs, units, geography, reference
  period, transformation, calculation ID, affected source cell and replacement
  evidence.

### 4. Implement in source

- Work on a disposable case.
- Change only source parameter JSON. Make structural changes in
  `genData.json` and regenerate with `UpdateCase`.
- Use an atomic generator with source fingerprints, an allowlisted diff,
  collision checks, invariant assertions and a recoverable backup.
- Never promote an edit made only to `data.txt`, processed data, an LP or
  solver output.

### 5. Pass deterministic pre-solve gates

Run the gates your change can actually break. Three always apply — they are cheap and catch
collateral damage:

- exact referential and scenario-ID integrity;
- source-diff allowlist and unchanged source hashes;
- no unintended restrictive `TAL`/`TAU`, exact activity pins, or arbitrary release years.

The rest are scoped by **which constraint block your parameter actually enters**. The table
below is derived from the upstream formulation
([`OSeMOSYS_GNU_MathProg/src/osemosys.txt`](https://github.com/OSeMOSYS/OSeMOSYS_GNU_MathProg/blob/master/src/osemosys.txt)),
not from parameter names. Verify against your **active local formulation** before relying on
it — step 2 exists for that reason, and MUIO builds do diverge.

| Parameter family | Constraint blocks it enters | Additional gates |
|---|---|---|
| `VariableCost`, `FixedCost`, `CapitalCost` | **none** — cost and salvage accounting only (`OC1`, `OC2`, `CC1`, `SV1`–`SV2`) | none. Three always-gates and one solve. Compare the objective. |
| `EmissionActivityRatio`, `EmissionsPenalty` | `E1` → penalty in the objective (`E3`); **and `E8`/`E9` limits, but only when `AnnualEmissionLimit` or `ModelPeriodEmissionLimit` is set** (both blocks are conditional on `<> -1`) | none if no limit is set. **If a limit is set, an emissions factor can make the model infeasible** — check emissions headroom before solving. |
| `InputActivityRatio`, `OutputActivityRatio` | commodity balance (`EBa1`–`EBa8`) | commodity-balance replay |
| `SpecifiedAnnualDemand`, `AccumulatedAnnualDemand` | `EQ_SpecifiedDemand`, `EBa9`, `EBb4` | commodity-balance replay |
| `ResidualCapacity` | `CAa2_TotalAnnualCapacity` — indexed over **every** year, feeding `CAa4` | **every-year** capacity envelope, not just the initial year |
| `OperationalLife` | `CAa1_TotalNewCapacity` (vintage accumulation) **and** `SV1`–`SV3` salvage | vintage survival + full-horizon replacement, **and** compare the objective — a lifetime change moves salvage value too |
| `CapacityFactor`, `AvailabilityFactor`, `CapacityToActivityUnit` | `CAa4_Constraint_Capacity`, `CAb1_PlannedMaintenance` (`CapacityToActivityUnit` also `RM1`) | every-year, every-timeslice capacity/service envelope |
| Initial/effective stock, turnover, adoption | `CAa1` vintage accumulation | nonnegative, dimensionally consistent stock/vintage profiles + full-horizon survival and replacement |
| `ReserveMargin` and its tags | `RM1`–`RM3` | reserve-margin check |
| `TotalAnnualMin/MaxCapacity`, activity limits | `TCC1`/`TCC2`, `NCC1`/`NCC2`, `AAC2`/`AAC3` | covered by the always-gate on pins |
| New or re-roled technologies, new modes or sets | structural | technology-role coverage, derived-set inspection, `glpsol --check` |

Two consequences worth stating plainly, because both are easy to get wrong:

- **A cost is genuinely cheap.** `VariableCost`, `FixedCost` and `CapitalCost` enter no
  constraint at all — they only move the objective. Three gates and one solve is right.
- **An emissions factor is not**, despite looking like a cost. It reaches a hard limit
  whenever one is set, so the same edit is cheap in a model with no emission cap and
  potentially infeasibility-inducing in one with a cap.

**Class C only**, once each artifact is recorded in the plan:

```bash
python scripts/validate_calibration_plan.py PLAN.json --stage pre-solve
```

Class B has no plan and must not run this.

Treat a deterministic failure as a design or data error. Do not ask CBC to
diagnose it.

### 6. Solve once, diagnose narrowly

- Run CBC through the normal application chain within the plan's time budget — or, for a
  Class B change with no plan, within twice the last known-good runtime.
- If presolve reports infeasibility, map the row back to the named local
  equation, indices, lower/upper values and source parameters before changing
  anything.
- If runtime regresses, stop near twice the known-good runtime unless the log
  shows credible convergence.
- Compare against the **stored** baseline result first. Only when something moved that
  should not have — or the baseline proves stale, the runtime regresses, or the solve is
  infeasible — spend a fresh unchanged control and one minimal A/B rollback. Never run a
  sequence of speculative formulations.
- A generated-file edit is permitted only in a disposable, clearly labelled
  diagnostic. Reproduce an accepted remedy in source and rerun the entire
  chain.
- Treat large aggregate constraint families and cross-technology coupling as
  formulation changes requiring a dedicated matrix-size and runtime A/B.

### 7. Validate behavior, not just optimality

- Compare objective and runtime with the accepted baseline.
- Check affected activity, capacity, demand, emissions, resource balances,
  backstops, constraint residuals and duals.
- Measure adjacent-year capacity and within-class activity-share changes.
  Report remaining discontinuities; do not hide them with pins.
- Inspect unexpected differences elsewhere and distinguish physical changes
  from alternate optima.
- Verify result freshness, case/run/scenario identity and artifact hashes.

### 8. Document and promote

- Maintain the ledgers in
  [references/SCHEMA.md](references/SCHEMA.md), including a
  `CHANGES.csv` row carrying this change's class.
- Update the case's `MODEL_FIXES*.md` with reason, equations, source changes,
  before/after values, diagnostics, baseline and exact passed/failed/timed-out
  checks.
- Promote only by regenerating the live case from the validated source state.
- Run one fresh live validation; do not copy disposable generated files or
  results.
- **Class C only** — complete the plan's promotion gates and run:

  ```bash
  python scripts/validate_calibration_plan.py PLAN.json --stage promotion
  ```

## Acceptance gate

**Both classes.** Do not claim completion unless the normal application chain solves
successfully, no gate that applies to your parameter family was omitted, and every material
data source, transformation and limitation is traceable through the ledgers. Record the
change in `CHANGES.csv` with its class.

**Class C additionally.** The plan validator must pass at `promotion`. Class B has no plan;
its equivalent evidence is the provenance records, the family-scoped gate results and the
baseline comparison.

## Related skills

- `build-clews-model` — build an uncalibrated country model.
- `assess-clews-calibration` — grade calibration quality and fitness for use.
- `clews-model-review` — audit structural and referential integrity.
- `add-environmental-accounting` — add environmental accounts without
  changing the economic model.
