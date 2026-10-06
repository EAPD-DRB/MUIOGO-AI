---
name: calibrate-clews-model
description: "Calibrates a solved MUIO/OSeMOSYS country CLEWs model from traceable national evidence, never by fitting outcomes. Use when the user explicitly asks for a calibration change, or when localizing a complete sector, closed resource account, or coupled interface. Not for unrequested value refreshes (record them in the calibration backlog), initial builds (build-clews-model), value-neutral cleanup (clews-model-fix), or grading (assess-clews-calibration)."
---

# Calibrate a CLEWs country model

Refine an existing solved country model with defensible evidence and physical
structure. Calibration here means country localization and physical calibration
from evidence independent of model-output error; it does not mean tuning inputs
until outputs resemble history.

## Boundary

Require a solved country baseline. Use `build-clews-model` if none exists and
`clews-model-fix` for edits that cannot change any model value.

Use this workflow only when the user invokes it explicitly or the work closes a
complete sector, resource account, or coupled interface. Put unrequested
isolated value updates, citation refreshes, and minor calibration fixes in
`calibration-backlog.csv` and batch them into the next coherent wave.

Apply the counterfactual test in
[references/non-forcing.md](references/non-forcing.md):

> Would this exact change still be made if no historical outcome were known?

Use observations as physical inputs, demand, initial stock, availability,
documented real-world constraints, or diagnostic benchmarks. Never select a
parameter merely to reduce historical error; record unresolved mismatches as gaps.
A change that fails the counterfactual test is outcome fitting. Refuse it and
record it as a gap; no route through this skill makes it acceptable.

### Explicit single change

When the user asks for one specific parameter change, run it as a one-change
wave. Gates the changed family cannot affect may be `not_applicable` with a
stated reason. [references/gate-scoping.md](references/gate-scoping.md) sets
which ones. Beyond the always-optional gates, that covers only
`connectivity_review`, and only when the family row allows it. Declare
`scope.mode = "explicit_single_change"` in the package; the validator then
requires exactly one `parameter_update`. Every other gate, the single solve and
the comparison still apply.

## Calibration package

Put a completed copy of `assets/calibration-package.template.json` at
`CASE_DIR/documentation/calibration-package.json`. Maintain the backlog at
`CASE_DIR/documentation/calibration-backlog.csv`. All package paths are relative to
`CASE_DIR`; override inference explicitly with `--case-dir`. Script paths in
this skill are relative to this skill's folder; pass absolute `CASE_DIR` and
`LEDGER_DIR` paths:

```bash
python scripts/validate_calibration_package.py \
  CASE_DIR/documentation/calibration-package.json \
  --case-dir CASE_DIR --stage design
```

The package validator compares the baseline and candidate source JSON directories,
derives the allowlist from `changes[].source_file`, resolves lineage against the
six CSV ledgers, verifies
the inherited ledger and retained evidence against the predecessor, reads JSON
gate reports, and checks connectivity dispositions. A passed gate needs a JSON
artifact whose top-level status is `pass`. Only `matrix_check` and
`stock_resource_account_checks`, plus `connectivity_review` for a declared
explicit single change, may be `not_applicable`, with a reason (see
[references/gate-scoping.md](references/gate-scoping.md)). Do not solve while
the design gate fails.

## Wave checklist

Copy this into the working notes and tick it off:

```text
[ ] 1. Baseline and inventory recorded; stored baseline passes identity and hash checks
[ ] 2. Connectivity audit run; every active finding has a disposition
[ ] 3. Representation designed; each changed parameter checked against gate-scoping.md
[ ] Design stage: validate_calibration_package.py --stage design
      If this stage fails, return to step 1 or 3; do not solve.
[ ] 4. Provenance recorded and source implemented; regenerated through UpdateCase
[ ] Source-input-patch stage (only for a source-only handoff)
      If this stage fails, return to step 4; do not solve.
[ ] 5. Gate reports attached; no-forcing audit run
[ ] Pre-solve stage: validate_calibration_package.py --stage pre-solve
      If this stage fails, return to step 2, 3 or 4 for the failing gate; do not solve.
[ ] 6. One wave solve; at most three repair re-solves
[ ] 7. Comparison classified; live case regenerated; archive identity checked
[ ] Promotion stage: validate_calibration_package.py --stage promotion
      If this stage fails, return to step 6 or 7; do not promote.
```

## Workflow

### 1. Establish the baseline and inventory

Record the source and candidate cases, scenario, horizon, intended use, stored
baseline identity, solver status, objective, runtime, and model dimensions.
Check the stored baseline's case, scenario and source hash against the source
case. If it fails those identity or hash checks, solve one unchanged control
through the normal application chain and use it as the baseline. Record why.
This is the only control solve the workflow allows. Start
the candidate with a complete copy of the current ledger and retained evidence.
Classify result surfaces as raw solver output, ordinary generated views, or
postprocessed reporting. Record each postprocessed layer in `reporting_layers`
with its publisher, version, raw inputs, published outputs, manifest, and rerun
requirement. Treat raw solver results as authoritative for optimizer behavior.

Use one complete, high-impact sector and its direct CLEWs interfaces as the
minimum implicit phase boundary. If the user has not selected the sector,
prioritize by national importance, current model weakness, cross-sector
influence, and public data availability. Inspect all material inputs within that
boundary and classify country specificity, currency, age, proxy use, missingness,
and connectivity.
Use the research hierarchy and trace rules in
[references/country-data-research.md](references/country-data-research.md).

Define whole-sector completion at the simplest defensible national level:
demand or service, historical accounting, stocks and turnover, applicable
technologies, costs and efficiencies, resource or infrastructure constraints,
direct emissions, and material interfaces with other modeled sectors. Group the
coupled changes needed to close that sector in one wave. A wave may contain
multiple packages, but they share one generated candidate, one solve, and one
set of verification artifacts. Record each package's completion test, evidence
period and post-evidence treatment, source and allocation boundary, calibration
claim, and measurable invariants. These declarations add no solve.

### 2. Audit connectivity

Start from `assets/connectivity-rules.template.json`. Declare roles and physical
links explicitly; never infer them from prefixes. Run:

```bash
python scripts/audit_clews_connectivity.py CASE_DIR \
  --rules CASE_DIR/documentation/connectivity-rules.json \
  --ledger-dir LEDGER_DIR \
  --output CASE_DIR/documentation/connectivity-audit.json
```

The audit fails closed on unknown rule entities and stale exemptions, checks free
routes year by year, and emits collision-free finding IDs. Resolve every active
finding by connecting or bounding it, declaring a sourced legitimate role, or
recording a consequential gap. Follow
[references/connectivity-audit.md](references/connectivity-audit.md).

When a branch is referenced but demonstrably inactive, use the conditional
retirement procedure in
[references/inactive-branch-retirement.md](references/inactive-branch-retirement.md).
Do not add dummy demand, supply, or disposal solely to silence a warning.

### 3. Design the representation

Read the exact local equation and export path for each changed parameter. Verify
ratio direction, units, indices, guards, defaults, generated-data behavior, and
national-versus-cluster scope. Use
[references/gate-scoping.md](references/gate-scoping.md) to find the
constraint blocks each family enters and the extra checks it needs. Use the
fewest objects needed for a defensible physical chain, leaving choices
endogenous beyond documented constraints.

Use transparent, bounded, and replaceable proxies when national evidence is
unavailable. Resolve conflicting evidence explicitly. For each material proxy,
record its central value, plausible range, transfer rationale, model consequence,
and the national authority or dataset that could replace it. A plausible range
documents uncertainty; do not run variants, sweeps, or sensitivity analysis to
select a value. Leave new `ASSUMPTIONS.csv` lower and upper bounds blank in this
workflow; carry inherited bounds forward unchanged.

For initial stocks, survival, retirement, or adoption, use
[references/stock-turnover-patterns.md](references/stock-turnover-patterns.md).
For annual technology entry, project pipelines, commissioning rates, or
`TotalAnnualMaxCapacityInvestment`, use
[references/deployment-envelopes.md](references/deployment-envelopes.md).
For land, water, biomass, fisheries, emissions, or another closed account, use
[references/resource-accounting.md](references/resource-accounting.md) and run:

```bash
python scripts/validate_resource_account.py RESOURCE_ACCOUNT.json \
  --ledger-dir LEDGER_DIR \
  --json CASE_DIR/documentation/resource-account-validation.json
```

### 4. Record provenance and implement

Use the six-ledger contract in [references/SCHEMA.md](references/SCHEMA.md).
Every package evidence ID, map ID, and change ID must resolve. Validate the ledger
and write its JSON report for the package gate:

```bash
python scripts/provenance.py LEDGER_DIR --stage build \
  --model-inputs MODEL_INPUT_DIR \
  --required-input AFFECTED_INPUT.csv \
  --allow-inherited-coverage-gaps \
  --json CASE_DIR/documentation/provenance.json
```

Modify source parameter JSON and `genData.json`, then regenerate through
`UpdateCase` and the normal application chain. Never promote generated-data, LP,
or solver-output-only edits. The package validator requires the actual changed
top-level source JSON files to equal `changes[].source_file`.
Formatting-only JSON churn is ignored. Record deterministic semantic regeneration
churn in `regeneration_changes` with before/after hashes and a reason; never use
that list to hide a numerical or structural model change. Record inherited
source-metadata corrections in `provenance.corrections`; create or supersede a
ledger record when a numerical claim or lineage changes.

For a source-only handoff before solving, set `delivery.state` to
`source_input_patch`, update the history artifact, mark existing results `stale`
or `absent`, and record the command needed to recertify them. Regenerate the live
source, create its result-free archive, verify live/archive source identity, and
run the lightweight checkpoint:

```bash
python scripts/validate_calibration_package.py \
  CASE_DIR/documentation/calibration-package.json \
  --case-dir CASE_DIR --stage source-input-patch
```

This checkpoint certifies the source, provenance, and archive identity only; it
does not certify a solve or promote the case.

### 5. Pass pre-solve gates

Attach the machine reports named by the package's `gates` keys, resolve every
active connectivity finding, and run the mandatory non-forcing audit. Run the
extra checks the gate-scoping table lists for each changed family. A deferred
finding must cite its `GAPS.csv` item; it does not masquerade as evidence.

```bash
python scripts/audit_no_forcing.py CASE_DIR \
  --package CASE_DIR/documentation/calibration-package.json \
  --ledger-dir LEDGER_DIR \
  --output CASE_DIR/documentation/no-forcing-audit.json
```

Then run:

```bash
python scripts/validate_calibration_package.py \
  CASE_DIR/documentation/calibration-package.json \
  --case-dir CASE_DIR --stage pre-solve
```

Treat failures as data or design errors rather than solver diagnostics.

### 6. Solve and diagnose

Solve the complete wave through the normal application chain within the recorded
budget. All packages, inactive-branch retirements, and invariants ride this same
solve. Map
infeasible rows to equations, indices, bounds, and evidence before changing
anything. Inspect affected quantities, binding limits, resource balances,
backstops, residuals, adjacent sectors, and full-horizon behavior. Correct only
mapping, unit, scope, evidence, or formulation defects—not historical mismatch.
Allow at most three repair re-solves by default. At that point, consolidate the
diagnosis and park the unresolved package as a documented gap while continuing
independent work; run more only with explicit user authorization. Never run an
unchanged control, parameter sweep, scenario ranking, or calibration A/B. The
one exception is the single baseline control in step 1, when the stored
baseline fails its identity or hash checks.

After each retained feasible solve, run every declared postprocessed reporting
publisher, verify its manifest against the current raw-result hashes and
allowlisted outputs, and attach the `reporting_layers_current` report. Disclose
which displayed results depend on postprocessing. This adds publication and hash
checks, not another solve.

In the central run, inspect the historical-to-future seam, annual technology and
fuel shares, stock turnover, resource dominance, imports, electricity demand, and
emissions. Report what the sector can now represent, its historical scale and
future service path, and which material results remain proxy-driven.

### 7. Compare and promote

Compare core annual outcomes before row-level activity. Add project-specific
land, water, or resource tables with repeated `--structural` options when needed.
Use `--rules` to filter exact retired identifiers and aggregate explicitly
equivalent routes:

```bash
python scripts/compare_clews_runs.py BASELINE_CSV_DIR CANDIDATE_CSV_DIR \
  --rules CASE_DIR/documentation/comparison-rules.json \
  --output CASE_DIR/documentation/run-comparison.json
```

Investigate tables present on only one side, aggregate equivalent routes, and do
not mistake alternative-optimum dispatch reallocations for physical change.
Compare raw solver results for model behavior and refreshed published layers for
reporting; never compare a stale derived view with a current solver run.
Record the comparator's exact-parity, alternate-optimum-candidate, or
material-change classification. An alternate-optimum candidate requires an
explicit promotion acceptance with rationale and the comparison artifact.
Benchmarks remain diagnostic, never fitted.

Regenerate the live case from validated source and verify its source hash. Reuse
the successful wave solve when its recorded source hash is identical; otherwise
solve once fresh. Create the result-free archive, verify live/archive source
identity, run provenance at `--stage delivery`, set `delivery.state` to `promoted` and
`delivery.result_status` to `fresh`, and finish with:

```bash
python scripts/validate_calibration_package.py \
  CASE_DIR/documentation/calibration-package.json \
  --case-dir CASE_DIR --stage promotion
```

## Judgment at delivery

The scripts cannot decide whether evidence is substantively appropriate. Confirm
that each change passes the counterfactual test, physical roles and scopes are
defensible, no material free or disconnected route remains unexplained, and
limitations name the evidence needed to replace proxies. Solver success proves
technical validity only; use `assess-clews-calibration` to grade calibration and
fitness for purpose.
