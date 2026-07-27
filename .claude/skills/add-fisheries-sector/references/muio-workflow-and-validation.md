# MUIO implementation and validation

## Contents

1. Source-of-truth rules
2. Preflight and backup
3. JSON implementation
4. Scenario inheritance
5. Freedom audit
6. Solve and result validation
7. Scope audit
8. Packaging

## 1. Source-of-truth rules

Treat the MUIO case JSON and model-local reproducible generators as source.
Never hand-edit:

- `data.txt` or processed data;
- LP/MPS files;
- solver result text;
- result CSV files;
- Pivot/viewer output.

Regenerate all derived files through the repository's existing execution path.
Inspect its actual parameter registry, formulation, generator, and result
exporter before editing.

Common MUIO parameter families include:

- `RYC`: annual and accumulated demand;
- `RYT`: technology costs, residual capacity, availability, and bounds;
- `RYTCM`: input/output activity ratios by mode;
- `RYTEM`: emission activity ratios;
- `RT`: operating life and capacity-to-activity conversion;
- scenario, timeslice, capacity-factor, and UDC families.

Names vary by version. Confirm mappings from code and parameter definitions.

## 2. Preflight and backup

Before editing:

- identify the authoritative case and saved scenario runs;
- record model and MUIO versions;
- record solver executable/version;
- generate and solve a fresh unchanged control when saved results may be stale;
- record objective, solve status, runtime, matrix dimensions, and hashes;
- archive source separately from generated results;
- verify each archive.

Do not start Fisheries work on a baseline that does not solve.

## 3. JSON implementation

Use collision-free internal IDs and clear public names. Add descriptions that
identify the Fisheries boundary and relevant parameter/calculation record IDs.

Populate complete base-scenario records for:

- technologies, commodities, modes, and groups;
- costs and operating life;
- residual capacity and retirement;
- availability and capacity factors;
- input/output ratios;
- emissions;
- demand;
- activity and investment bounds;
- timeslice mappings where applicable.

Preserve all required dense/default rows expected by the installed generator.
Validate JSON after every edit. Generate data once before the expensive solve
and inspect Fisheries rows for units, scenario values, defaults, and missing
parameters.

## 4. Scenario inheritance

Determine how the installed MUIO version represents scenario inheritance.
Normally place baseline values in the base scenario and preserve null/inherited
rows in dependent scenarios unless Fisheries has an explicit scenario change.

Do not copy baseline Fisheries values into every scenario if doing so would
override inheritance. Do not silently give Fisheries a policy assumption in
only one existing scenario. Record every scenario-specific value in the
parameter and assumption registers.

## 5. Freedom audit

Run:

```bash
python scripts/audit_fisheries_freedom.py \
  WebAPP/DataStorage/<case>
```

Inspect reported findings manually. Require:

- no exact annual activity lower/upper pair for Fisheries;
- no minimum use of residual stock;
- no arbitrary initial investment prohibition followed by opening;
- no fixed carrier-share UDC;
- no Fisheries calibration-only constraint;
- no low availability whose only basis is historical utilization.

Finite physical limits are acceptable only when their parameter records resolve
to independent evidence. Add their record IDs to model descriptions and audit
notes.

A model may optimize to the historical mix without being forced. Structural
freedom is the primary proof. When doubt remains, solve a disposable copy after
a modest cost perturbation. If the mix cannot respond, locate the binding
constraint. Never retain the perturbation in the final case.

## 6. Solve and result validation

Use the unchanged normal solver and pipeline for Base and every configured
scenario. Require explicit optimal or accepted feasible status.

Verify by region, year, timeslice, technology, and mode as relevant:

- all Fisheries demands are met;
- physical fish mass balances close when production is modeled;
- fuel and electricity enter through the intended chains;
- no carrier cost or emissions factor is counted twice;
- residual capacity follows the declared retirement path;
- inherited stock can remain idle;
- new capacity respects operating life and physical limits;
- water, land, feed, waste, and emissions links balance;
- Industry/Agriculture/Transport boundary adjustments reconcile;
- objectives and material non-Fisheries aggregates remain explainable.

Compare model activity with historical evidence diagnostically. Do not make
historical agreement a pass/fail solve criterion.

## 7. Scope audit

Compare the edited source with the pre-change backup.

Allow:

- new Fisheries entities and parameters;
- explicit Fisheries-related changes;
- allowlisted cross-sector boundary records;
- model descriptions and version metadata;
- source, calculation, assumption, completeness, and validation artifacts.

Reject:

- unrelated technology or commodity changes;
- undocumented demand changes;
- shared-code modifications made only for this country;
- solver or formulation changes;
- generated outputs edited by hand.

Report the exact changed files and, for mixed files, the exact changed entity
IDs. Do not say “only Fisheries changed” when a boundary demand also changed;
name the exception.

## 8. Packaging

Deliver:

- final model source;
- solved required runs;
- viewer output;
- pre-change source and result backups;
- source, assumption, calculation, parameter, boundary, and completeness
  registers;
- retained source extracts or access instructions;
- stock-estimation inputs and outputs;
- freedom-audit output;
- scope-diff report;
- policymaker trace-test record;
- limitations and data-upgrade list;
- exact regenerate, solve, validate, and restore commands.

Create one portable archive in the layout expected by the installed MUIO
version. Exclude large regenerable LP/MPS files unless requested. Test archive
integrity and publish its SHA-256 checksum.
