---
name: add-fisheries-sector
description: Add a technically complete, source-traceable, non-forcing Fisheries sector to an existing solved OSeMOSYS, CLEWs, or MUIO country model. Use when adding fishing-fleet propulsion, aquaculture operations, fish production, cold chain, or processing; estimating existing equipment stock and residual capacity; reconciling Fisheries with Industry, Agriculture, Transport, land, water, food, or energy accounts; documenting the exact source and derivation of every number for policymaker review; regenerating all scenarios with the unchanged solver; or packaging a verified portable country case.
---

# Add Fisheries Sector

Build the most complete Fisheries representation that defensible direct data,
derived data, proxies, and transparent estimates permit. Do not reproduce the
omissions of existing sectors, and do not force historical technology outcomes.

## Non-negotiable rules

1. Confirm that the original model solves before editing. Preserve a recoverable
   source and results backup.
2. Inspect the target model only to learn its technical interfaces: files,
   identifiers, units, years, scenarios, timeslices, commodities, and execution
   path. Never use another sector's missing fields as a reason to omit Fisheries
   data.
3. Include every material Fisheries parameter supported by evidence or a
   defensible estimate. Record unresolved items as explicit data gaps.
4. Represent pre-base-year physical equipment as residual capacity. Estimate it
   transparently when a direct stock inventory is unavailable.
5. Keep historical utilization separate from technical availability. Use
   utilization to estimate stock, not to force annual operation.
6. Prohibit exact historical technology activity, carrier-share locks,
   artificial deployment dates, calibration-only UDCs, fabricated pre-base
   years, and one-year historical technologies.
7. Keep the solver and configured scenarios unchanged. Never change solver
   settings to conceal an overconstrained formulation.
8. Change unrelated sectors only for an auditable accounting-boundary
   correction. Prefer direct physical or useful-service subtraction to a
   coefficient inferred from a saved optimization result.
9. Make every final model value traceable from model parameter to calculation,
   source observation, conversion, proxy, and assumption.

## Required references

Read:

- [references/sector-boundary-and-parameters.md](references/sector-boundary-and-parameters.md)
  before defining the sector, data requirements, technologies, residual stock,
  projections, or nexus links;
- [references/source-traceability.md](references/source-traceability.md) before
  collecting data or writing any model number;
- [references/muio-workflow-and-validation.md](references/muio-workflow-and-validation.md)
  before editing a MUIO case, regenerating results, auditing freedom, or
  packaging delivery.

Copy the templates in `assets/` into the country work package before entering
data. Do not edit the templates inside the installed skill.

## Required workflow

### 1. Establish the technical baseline

- Read repository instructions and locate the authoritative model source.
- Record model version, years, regions, timeslices, scenarios, solver, saved
  runs, units, parameter defaults, and generation commands.
- Solve or verify every required baseline run. Record objectives, solver status,
  runtime, source hashes, and result hashes.
- Create a timestamped backup before editing.
- Stop if the baseline cannot be generated or solved. Diagnose it separately;
  do not attribute a pre-existing failure to Fisheries.

### 2. Define a complete Fisheries boundary

- Investigate capture fishing, aquaculture, hatcheries, fleet propulsion,
  landing and ice, cold storage, processing, feed, waste, trade, water, land,
  emissions, and resource limits.
- Include material flows supported by evidence. Mark excluded flows, the reason,
  and the sector retaining them.
- Decide whether to model useful services, physical fish production, or both.
  Prefer production-linked pathways when reliable production and intensity data
  exist; use useful-service demands when they are the defensible representation.
- Build the boundary register before changing model files.
- Identify existing aggregate demands or flows that already contain Fisheries.
  Define the exact double-counting correction and its units.

### 3. Build the provenance package first

- Populate `source-register.csv`, `assumption-register.csv`,
  `calculation-register.csv`, `parameter-register.csv`,
  `boundary-register.csv`, and `completeness-register.csv`.
- Give every source, assumption, calculation, and parameter record a stable ID.
- Record exact locators: table, sheet, cell/range, page, figure, API query,
  dataset variable, or database filter—not merely a report title or homepage.
- Record original values and units before conversion.
- Record formulas, intermediate values, unit conversions, interpolation,
  currency basis, rounding, scripts, and source IDs for every derived value.
- Use the same parameter record IDs in model documentation and validation
  reports.
- Run `scripts/validate_provenance.py` and resolve every error before solving.

### 4. Construct demands and projections

- Reconcile the base-year energy, production, and carrier balance inside the
  declared boundary.
- Convert final inputs to useful service only with documented efficiencies.
- Keep observed history, normalized base-year estimates, projections, and
  scenarios clearly separated.
- Use documented drivers for projections: production, population, consumption,
  exports, aquaculture expansion, fleet change, intensity change, or technology
  learning.
- Treat demand as a service requirement, not as a technology or carrier-share
  constraint.
- Label every extrapolation and sensitivity range.

### 5. Construct existing stock

- Seek equipment nameplate capacity and commissioning dates first; then vessel
  horsepower, facility throughput, equipment counts, or engineering conversion.
- When direct stock is unavailable, estimate effective stock as:

```text
ResidualCapacity =
    ObservedUsefulService
    / (CapacityToActivityUnit × HistoricalUtilization)
```

- Record the utilization assumption only in the stock calculation.
- Set technical availability from physical performance evidence.
- Derive retirement from commissioning ages when possible. Otherwise use a
  documented age-distribution method over the operating life.
- Use `scripts/estimate_residual_capacity.py` for the standard straight-line
  uniform-age method and retain its input/output files.
- Allow residual stock to sit idle.

### 6. Implement complete pathways

- Add collision-free technologies, commodities, modes, groups, descriptions,
  and all scenario/year rows required by the target schema.
- Populate applicable demand, IAR, OAR, CAU, residual capacity, capital cost,
  fixed cost, variable cost, operating life, technical availability, capacity
  factor, direct emissions, losses, resource requirements, and physical limits.
- Connect electricity and fuels through the real upstream commodity chains.
  Do not duplicate carrier costs or emissions already represented upstream.
- Add water, land, feed, biomass, catch, waste, and processing links when they
  are material and defensibly quantified.
- Apply only evidence-based physical limits. Never tune a limit until a
  historical result matches.
- Make every model description identify the relevant parameter or calculation
  record IDs.

### 7. Reconcile accounting boundaries

- Use the boundary register to apply only the required cross-sector changes.
- When two demands represent the same service in the same unit, subtract the
  explicit Fisheries service directly from the aggregate demand.
- When units differ, build an external-data calculation. Do not use an optimized
  carrier mix or saved-solution intensity unless the user explicitly approves
  it as an unavoidable approximation.
- Prove that totals reconcile before and after the split.

### 8. Audit freedom and source scope

- Run `scripts/audit_fisheries_freedom.py` on the edited model.
- Require open technology activity and investment choices unless a limit is an
  independently sourced physical restriction.
- Inspect every Fisheries UDC and bound manually. Remove outcome-targeting
  constraints.
- Compare source files against the backup. Allow only Fisheries records,
  documented boundary corrections, metadata, and delivery documentation.
- Treat an optimized historical match as inconclusive. Prove freedom
  structurally; when necessary, run a disposable cost-perturbation test showing
  that the technology mix can change.

### 9. Regenerate and solve

- Regenerate data, processed data, optimization matrix, results, CSV exports,
  and viewer files through the repository's normal pipeline.
- Use the unchanged solver for Base and every configured scenario.
- Require optimal or explicitly accepted feasible status for every run.
- Verify demand satisfaction, commodity balances, residual-capacity retirement,
  physical limits, emissions, and nexus connections.
- Compare optimized activity with the historical stock-estimation evidence.
  Explain differences; do not remove them by calibration.

### 10. Validate and package

- Re-run provenance validation and the freedom audit.
- Perform the policymaker trace test in
  `references/source-traceability.md`: reconstruct a sample of model numbers
  without relying on personal memory.
- Deliver the complete model, solved runs, viewer data, pre-change backups,
  registers, calculation scripts, audit results, limitations, reproduction
  commands, and source-access notes.
- Create one portable archive and verify its integrity and checksum.

## Completion gates

Do not claim completion until:

- the baseline and final configured cases solve with the same solver;
- the completeness register has no unexplained blank status;
- every populated Fisheries model value has a parameter record;
- every parameter record resolves to a direct source or reproducible
  calculation;
- every calculation resolves to source observations and explicit assumptions;
- exact source locators and access dates are present;
- residual stock exists for every applicable pre-base-year technology;
- residual retirement and technical availability have independent meanings;
- no Fisheries historical activity or carrier share is forced;
- all cross-sector changes appear in the boundary register;
- unrelated source parameters are unchanged;
- every material uncertainty and data gap is visible;
- the policymaker trace test passes; and
- the portable archive passes integrity verification.

## Delivery language

State:

> The Fisheries sector is technically solved and source-traceable. It includes
> the most complete set of defensible direct, derived, proxy, and estimated
> inputs assembled for the declared boundary. Residual equipment stock is
> represented but may remain idle. No parameters or constraints were introduced
> to force historical technology activity or carrier shares. Each model number
> can be traced through the parameter, calculation, assumption, and source
> registers. Remaining data gaps and uncertainties are explicit.

Do not describe solver success as historical calibration or policy validation.

## Related skills

- `muiogo-scenarios` — for a POLICY overlay on an existing model rather than a new sector.
- `clews-model-review` — checking the model still hangs together afterwards.
- `muiogo-run`, `muiogo-analyze` — re-solving and quantifying what changed.

These live in the MUIOGO-AI collection; if one is not available to you,
do the job directly and say which skill would have covered it.
