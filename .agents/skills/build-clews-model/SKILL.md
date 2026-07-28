---
name: build-clews-model
description: Build from scratch a technically valid, uncalibrated OSeMOSYS/CLEWs whole-country full-nexus model with the upstream CLEWs Global workflow, then import, repair, verify, solve, and package it as a usable MUIO case with standardized source, assumption, calculation, model-map, version-pin, history, and frozen-baseline traceability. Use when creating a new country CLEWs model; adapting CLEWs Global or GeoCLEWs; preparing country configuration and geospatial inputs; documenting exact sources and crop proxies; converting complete CLEWs CSV sets through otoole and MUIO; checking importer capabilities, temporal mappings, parity, provenance coverage, and resource requirements; handling unsupported reserve-margin tags with a documented UDC workaround; or delivering a solved portable MUIO country case for later calibration. Never tune parameters or impose constraints to reproduce historical observations during this build stage.
---

# Build a CLEWs country model through MUIO

Create, in one continuous workflow:

1. a reproducible raw CLEWs Global country model; and
2. a solved, portable MUIO case representing that model as faithfully as the
   installed MUIO version permits; and
3. a machine-validated provenance package following the standard country
   layout.

Preserve GeoCLEWs spatial processing, OSeMOSYS Global energy inputs, `clewsy`
nexus integration, the upstream OSeMOSYS formulation, and an open solver.
Treat MUIO import as a separate representation and verification phase. Do not
describe MUIO conversion fixes or formulation workarounds as country
calibration.

The authoritative deliverables are the complete solved upstream country model,
its complete MUIO representation, and their linked provenance and frozen raw
baseline. Keep them reusable for later, separately scoped modelling work.

## Non-negotiable boundary

Do not use historical observations to make model results match history.

Never add or tune:

- historical generation-share or activity locks;
- equal historical lower/upper activity constraints;
- historical minimum/maximum capacity locks;
- capacity, demand, availability, capacity-factor, efficiency, cost, fuel,
  emissions, or yield overrides selected to reduce historical error;
- hydro, biomass, fuel-supply, land, crop, or water parameters inferred solely
  by solving backward from an observed outcome;
- smoothing or ramp constraints introduced only to conceal a historical-to-
  forecast discontinuity.

Do not call the result calibrated, validated against history, or policy-ready.
Record calibration data needs and suspicious outputs for the later calibration
stage without changing the raw model to fix them.

Before delivery, run `scripts/audit_no_forcing.py` and resolve every failure.
Read [references/non-forcing-rules.md](references/non-forcing-rules.md) whenever
an observed country value might influence a model parameter or constraint.

The MUIO phase does not weaken this boundary. A user-defined constraint is
permitted only when it faithfully ports an upstream formulation feature or
implements the reserve-margin workaround defined below. Never use a UDC to
lock historical capacity, activity, generation, land, water, or emissions.

## Required references

Read:

- [references/provenance-and-layout.md](references/provenance-and-layout.md)
  before creating or modifying the country package;
- [references/country-adaptations.md](references/country-adaptations.md) before
  changing country structure, technology applicability, time definitions, or
  crop mappings;
- [references/technical-corrections.md](references/technical-corrections.md)
  before patching CLEWs Global, a submodule, otoole, or a generated pipeline;
- [references/muio-import.md](references/muio-import.md) before preparing the
  MUIO workbook or touching a MUIO case;
- [references/reserve-margin-workaround.md](references/reserve-margin-workaround.md)
  whenever reserve-margin tags are present or native support is uncertain;
- [references/source-and-government-review.md](references/source-and-government-review.md)
  before recording source data, crop selections, proxies, or questions for
  national reviewers;
- [references/geospatial-preflight.md](references/geospatial-preflight.md)
  before running GeoCLEWs or reusing a raster cache;
- [references/import-quality-gates.md](references/import-quality-gates.md)
  before creating the import workbook, capability inventory, or parity report;
- [references/resource-and-packaging.md](references/resource-and-packaging.md)
  before full MUIO data generation and final packaging;
- [references/handoff-templates.md](references/handoff-templates.md) when
  creating the mandatory delivery artifacts and validation summary.

## Required workflow

1. **Define the build**
   - Initialize the standard package before acquiring or transforming data:
     `python scripts/init_country_package.py PACKAGE_ROOT --country COUNTRY
     --iso3 ISO`.
   - Run `python scripts/validate_provenance.py PACKAGE_ROOT --stage scaffold`
     and resolve every failure.
   - Record country, ISO3 code, intended horizon, administrative resolution,
     climate pathway, requested use, CLEWs Global location, and MUIO location.
   - When the user supplies only the country, proceed with documented
     upstream-supported raw defaults and evidence-based structural assumptions.
     Ask only when a missing choice or inaccessible resource would materially
     change the model architecture or prevent completion.
   - Label the scenario `raw` or `uncalibrated`.
   - Separate build questions from future calibration and policy questions.
   - Confirm that the authoritative build target represents the complete
     upstream CLEWs country model.
   - Define three separately reported targets: a solved upstream model, a
     complete and explained MUIO import, and a solved portable MUIO case.

2. **Pin and inspect both codebases**
   - Clone CLEWs Global recursively and record the root and every submodule
     repository and full commit in `config/upstream_versions.json`.
   - Locate or obtain MUIO and record its commit/version plus checksums of the
     importer, parameter registry, and active formulation.
   - Read the upstream README, configuration, Snakefile, environment files,
     licenses, otoole configuration, MUIO importer, MUIO parameter registry,
     active MUIO formulation, and expected input/output paths.
   - Preserve an untouched upstream reference or reproducible clean checkout.
     Do not archive the whole checkout when the pins reproduce it.
   - Record checksums of shared MUIO importer/formulation files that the
     country workflow must not modify.
   - Run a dependency preflight for Python, Snakemake, otoole, geospatial
     libraries, open solvers, and required MUIO modules. Record exact versions
     and justified compatibility pins.
   - Cache importer capability results by the importer, registry, formulation,
     and otoole-configuration checksums. Recompute them when any checksum
     changes.
   - Never copy a previously calibrated country model as the hidden starting
     point.
   - Record exact editions and checksums for actual downloaded input files;
     code pins do not freeze data behind mutable URLs.

3. **Prepare authoritative structural inputs**
   - Obtain country boundaries and required administrative layers.
   - Populate `data_sources/SOURCES.csv`. For every external dataset, record
     provider, exact product, edition, reference period/scenario, variable,
     unit, geography, model use, selection, transformation, quality, proxy,
     URL, license, national replacement, evidence path, checksum, and status.
   - Record every modeller choice in `data_sources/ASSUMPTIONS.csv`, every
     implemented transformation in `data_sources/CALCULATIONS.csv`, and every
     active parameter or coherent parameter family in
     `data_sources/MODEL_DATA_MAP.csv`.
   - Retain permitted extracts under `data_sources/evidence/` and require their
     checksums. For restricted or copyrighted data, retain metadata, access
     conditions, extraction instructions, and an authorized checksum without
     redistributing the source.
   - Register unavailable lineage explicitly as `documentation_gap`; never
     leave an active value silently undocumented.
   - Include a government-review table identifying consequential source and
     proxy choices, the agency that could validate them, and the parameters
     that would change if a better national source is supplied.
   - Use observed geography, time zone, seasons, administrative structure, and
     technology applicability only as structural inputs.
   - Keep historical performance data in a calibration-candidate inventory;
     do not apply it.

4. **Configure the country**
   - Use native CLEWs Global configuration wherever possible.
   - Set country identifiers, nodes, horizon, seasons, dayparts, climate
     pathway, clustering resolution, projections, trade topology, and
     structurally applicable technologies.
   - Complete `documentation/CURRENT_MODEL.md`,
     `documentation/MODEL_STRUCTURE.md`, and
     `documentation/KNOWN_LIMITATIONS.md`; make each consequential choice
     explicit and link it through the provenance ledgers.
   - Add a dated record to `documentation/HISTORY.md`.

5. **Run preflights before the expensive workflow**
   - Inspect the raster cache for stale country/crop/scenario files, zero-byte
     or corrupt files, missing crop-variable-water-input combinations, and
     metadata inconsistent with the country configuration.
   - Measure raster coverage over all boundary components. Report missing-cell
     and missing-area shares by raster and cluster candidate.
   - Detect multipart, island, coastal, antimeridian, invalid-geometry,
     constant-column, and missing-value conditions before clustering.
   - Produce a configuration-level resource estimate using years, timeslices,
     clusters, crops, technologies, and modes. Run
     `python scripts/estimate_resources.py` when its input assumptions apply.
   - Stop on failed structural inputs. Do not discover a missing raster or
     incompatible environment late in model generation.

6. **Apply only necessary technical corrections**
   - First reproduce the defect on the pinned upstream version.
   - For pinned CLEWs Global revisions containing the sample-country
     transmission block, run `python
     scripts/fix_clewsy_grid_mapping.py
     CHECKOUT/workflow/scripts/clewsy.py`. This makes end-use electricity
     carriers use each unique configured grid node and avoids adding a parallel
     transmission already supplied by OSeMOSYS Global.
   - Prefer a minimal, general correction over a country-result override.
   - Add a minimal fixture and regression check that fail before the correction
     and pass after it. Cover the applicable failure class listed in
     `references/technical-corrections.md`.
   - Retain the patch/diff, fixture, command, and before/after result.
   - Store revision-specific changes under `patches/` and map every
     parameter-affecting change through the provenance ledgers.
   - Prove that the correction addresses software behavior, not historical fit.

7. **Run the native workflow**
   - Build GeoCLEWs outputs.
   - Use NaN-aware normalization and explicit constant-column handling.
   - When defensible, impute only missing island/coastal raster attributes from
     the nearest valid projected land cell. Never overwrite measured cells.
     Report the affected cell and area shares and stop when they exceed the
     declared acceptance threshold.
   - Permit a documented sample for dendrogram visualization only. Use every
     retained land cell in production clustering.
   - Select crops by exact source-item joins. Write a machine-readable crop
     mapping containing source rank/value/quality flag, explicit or aggregate
     membership, GAEZ code, proxy rationale, and expected limitation. Reject
     duplicate proxy rasters and explicit/aggregate double counting.
   - Build OSeMOSYS Global inputs.
   - Integrate the full model with `clewsy`.
   - Update `MODEL_DATA_MAP.csv` as files and parameter families are generated;
     do not postpone coverage mapping until delivery.
   - Convert the data, generate the optimization problem, solve it, and export
     results using the upstream workflow and supported tools.
   - Stop on non-zero subprocess status. Never continue from a partially failed
     stage.

8. **Validate technical and nexus integrity**
   - Confirm solver feasibility/optimality, schema conformance, unique parameter
     indices, complete sets, valid units, balanced time slices, and sensible
     bounds.
   - Verify that energy, land, crop, water, and climate components are present
     and physically linked, not merely colocated files.
   - Check land conservation, crop production/use, water accounting, energy
     balances, emissions accounting, and cross-sector input/output ratios.
   - Inspect year-to-year discontinuities and report them as raw-model behavior.
     Do not suppress them with historical constraints.
   - Compare with observations only to create a transparent gap table. Mark
     every comparison as **diagnostic—not fitted**.
   - Run `python scripts/validate_provenance.py PACKAGE_ROOT --stage build`.
     Require unique IDs, resolved links, mapped active records, matching
     evidence checksums, full code pins, and provenance coverage for every
     populated model input.

9. **Package the upstream raw model**
   - Include the pinned commits, country configuration, generated raw inputs,
     results, geospatial outputs, technical patches, source manifest, solver
     status, technical QA, model card, and reproduction commands.
   - Complete all scaffolded documentation and ledgers. The calibration
     handoff must list historical datasets, mismatches, suspected drivers, and
     candidate future parameters. Apply none of them.
   - Preserve a machine-readable no-forcing audit.

10. **Build the MUIO capability inventory and import workbook**
    - Create a capability inventory for every populated source parameter. Prove
     registration, JSON storage mapping, import/export handling, active
     formulation declaration, and an equation that uses it.
    - Test the installed workbook sheet aliases before the full import. Account
     for Excel's 31-character worksheet-name limit and fail on an unrecognized
     truncated name.
    - Convert the complete CLEWs CSV input folder to Excel using otoole and the
     matching CLEWs/otoole configuration.
    - Add MUIO-required `TECHGROUP` definitions and assign every technology.
     Grouping is interface metadata and must not alter parameters.
    - Add deterministic time-set descriptions.
    - If CLEWs Global supplies no `DiscountRate` row, insert an explicit
     `GLOBAL, 0.05` fallback and document it. Preserve any supplied value.
    - Omit empty optional parameter sheets when the installed importer
     misinterprets an empty sheet as populated.
    - Save the untouched otoole workbook and the prepared MUIO workbook.

11. **Import the complete country model without modifying shared MUIO code**
    - Use a country-local one-off import driver around MUIO's existing
      `ImportTemplate.py`.
    - Hash the importer before and after and fail if it changes.
    - Refuse to overwrite an existing case silently.
    - Store every import helper inside the country package so the workflow is
     portable to another laptop.
    - Add a short README to the active MUIO case pointing to the canonical
     country package; do not duplicate the ledgers inside the runtime case.
    - Do not change `ImportTemplate.py`, `Parameters.json`, or the shared
      OSeMOSYS formulation merely to accommodate this country.

12. **Repair and verify temporal structure**
    - After import, reconstruct each MUIO timeslice's season, day type, and
      daily time bracket from `Conversionls.csv`, `Conversionld.csv`, and
      `Conversionlh.csv`.
    - Reconstruct `DaySplit` from the CLEWs CSV.
    - Back up every generated JSON file before one-off repair.
    - Assert one active member per timeslice per temporal dimension and exact
      set/year coverage.
    - Generate a MUIO data file and verify the resulting conversion matrices,
      `YearSplit`, and `DaySplit`.
    - Compare every imported membership and split against the authoritative
      CLEWs CSVs. Solver success does not excuse a temporal mismatch.

13. **Run import parity before adding workarounds**
    - Round-trip the generated MUIO data through otoole after removing only
      MUIO-only sets and parameters from an analysis copy.
    - Classify every source row as exact, implicit default, intentionally
      transformed representation, unsupported, or erroneous.
    - Treat every unexplained loss or change as an import failure. Any lost or
      changed nondefault source row is a hard failure unless it has an explicit,
      tested native or documented formulation representation.
    - Report the count and expansion ratio of technology-mode,
      technology-commodity, and parameter associations. Stop on unexplained
      dense Cartesian expansion.
    - Compare upstream and MUIO results on overlapping outputs. Explain
      formulation differences, defaults, units, and objectives; never tune the
      model to make parity pass.
    - Report `upstream_raw`, `muio_import`, and `muio_final` statuses separately.
      Never let a later solve overwrite or hide an earlier import failure.

14. **Handle reserve-margin tags**
    - First test whether the installed MUIO version supports native
      `ReserveMargin`, `ReserveMarginTagFuel`, and
      `ReserveMarginTagTechnology` parameters and an active reserve constraint.
      Use native support when it exists.
    - Otherwise apply the annual MUIO UDC workaround in
      [references/reserve-margin-workaround.md](references/reserve-margin-workaround.md).
    - Clearly label it a **workaround for unsupported reserve-margin tags**,
      not a native import and not calibration.
    - Use the source capacity credits and reserve-margin default/value. Do not
      substitute Input/Output Activity Ratios, CapacityFactor, or a single
      `ReserveMargin.csv` value for technology-specific credits.
    - Install a conspicuously named constraint, a model-local configuration,
      and a checker/updater that reports `STALE` with a nonzero exit when
      demand, demand profile, `YearSplit`, `CapacityToActivityUnit`, capacity
      credits, reserve margin, years, timeslices, or scenarios invalidate the
      derived UDC.
    - Require a `CURRENT` zero-mismatch check before solving.

15. **Estimate resources, solve, and validate the MUIO model**
    - Re-run the resource estimate using actual imported active modes,
      associations, scenario rows, and formulation dimensions before generating
      the full MUIO data and LP.
    - Report estimated rows, columns, nonzeros, memory, working disk, LP size,
      and a broad runtime range with assumptions and confidence. Use
      Green/Amber/Red thresholds from
      `references/resource-and-packaging.md`.
    - Never reduce years, timeslices, clusters, or technologies automatically.
      A structural simplification requires an explicit modelling decision.
    - Preserve a pre-workaround run for diagnosis and create a separate
      reserve-proxy run when the workaround is needed.
    - Generate MUIO data, solve with an available supported open solver, and
      require an optimal/feasible status.
    - Verify all UDC rows appear in generated data and results and that credited
      capacity satisfies the annual requirement within solver tolerance.
    - Re-run technical/no-forcing checks and the reserve-proxy stale check.
    - Record actual matrix, disk, generation, and solve measurements beside the
      estimate for later estimator improvement.

16. **Package and validate the delivery**
    - Export a MUIO-compatible case ZIP that includes the model JSON,
      configuration marker, check fingerprint, runs, and results while
      respecting MUIO's backup layout.
    - Exclude regenerable LP/MPS files from the portable archive unless the user
      explicitly requests them. Retain the generation command and solver log.
    - Include the prepared workbook, otoole config, one-off scripts, parity
     reports, solve status, canonical ledgers, current documentation, and
     diagnostics in the country package.
    - Run `python scripts/validate_provenance.py PACKAGE_ROOT --stage build`.
    - Freeze one source/build archive and register the existing portable MUIO
     ZIP with `python scripts/freeze_raw_baseline.py PACKAGE_ROOT
     --muio-archive muio/COUNTRY_raw_MUIO.zip`. Do not make a duplicate MUIO
     backup.
    - Run `python scripts/validate_provenance.py PACKAGE_ROOT --stage delivery`
     and then `python scripts/validate_delivery.py PACKAGE_ROOT`.
    - Verify provenance coverage, evidence and baseline checksums, archive
     integrity, machine-readable status separation, and exact reproduction,
     check, update, solve, package, and restore commands.

## Permitted changes

Permit:

- reproducible technical corrections listed in the technical reference;
- documented country adaptations listed in the country reference;
- deterministic compatibility changes that do not target model outcomes;
- diagnostic comparisons that do not feed values back into the raw model;
- performance or visualization changes proven not to change model parameters;
- MUIO-only technology groups and descriptions;
- one-off repair of importer-created time references using authoritative CLEWs
  conversion matrices;
- sampled diagnostic plots when production computations retain all data;
- nearest-valid-land-cell imputation only under the documented geospatial
  coverage rules and thresholds;
- an explicit 5% discount-rate fallback only when CLEWs Global supplies no
  value;
- the documented reserve-margin UDC workaround when native MUIO support is
  absent and its structural preconditions are proven.

When a proposed change is both structural and potentially calibrating, use the
counterfactual test:

> Would this exact change still be made if no historical outcome were known?

If no, defer it to calibration.

## Completion gates

Do not call the task complete until:

- the native CLEWs Global workflow solves;
- nexus and technical integrity checks pass;
- the no-forcing audit has zero failures;
- all country corrections and adaptations are documented;
- the exact source catalogue and government-review questions are complete;
- the standard package scaffold and canonical current/history separation are
  complete;
- every source, assumption, calculation, and model-map ID is unique and every
  cross-reference resolves;
- every active source, assumption, and calculation is mapped;
- every populated raw input and the active country configuration has
  provenance coverage;
- every retained local evidence file matches its recorded checksum;
- missing lineage is registered as a documented gap rather than left blank;
- the geospatial cache, coverage, multipart/island, missing-value, and area
  preflights pass;
- each applied technical correction has a retained regression fixture;
- the dependency preflight and resource estimate pass or have an explicitly
  accepted Amber warning;
- the MUIO capability inventory covers every populated source parameter;
- all populated worksheet names are recognized after Excel truncation;
- MUIO contains the complete sets and parameters expected after supported
  defaults and documented transformations;
- no nondefault source row is lost or changed without an explicit tested
  representation;
- association expansion ratios contain no unexplained dense import;
- timeslice season/day/bracket mappings exactly match CLEWs conversions;
- unsupported inputs are explicitly inventoried;
- reserve tags are either imported natively or represented by a validated,
  clearly labelled workaround;
- the reserve workaround checker reports `CURRENT` with zero mismatches;
- the final MUIO run solves;
- upstream, import, and final MUIO statuses are reported separately;
- parity differences are explained rather than hidden;
- actual resource use is recorded against the preflight estimate;
- the portable MUIO ZIP passes an archive integrity check;
- the frozen raw source archive and portable MUIO ZIP match
  `config/baseline_manifest.json`;
- the current raw input and result tree hashes still match the frozen baseline;
- `python scripts/validate_provenance.py PACKAGE_ROOT --stage delivery` passes;
- `python scripts/validate_delivery.py` passes with every required handoff
  artifact; and
- shared MUIO code checksums are unchanged unless the user separately
  authorized a general MUIO software change.

## Delivery language

State:

> This is a technically solved, uncalibrated CLEWs Global country model. It uses
> upstream defaults plus documented technical corrections and country
> adaptations, and it has been imported into MUIO with documented
> representation repairs. No parameters or constraints were introduced to
> force agreement with historical outcomes. Any reserve-margin UDC is a
> labelled workaround for unsupported native tags, not calibration. Historical
> calibration and policy constraints are separate later stages. Active inputs
> and modelling choices are linked through the package source, assumption,
> calculation, and model-map ledgers; documented provenance does not by itself
> prove that a source is accurate or fit for a particular boundary.

Report solver success as technical validity only. Never present it as evidence
of country calibration.

## Related skills

- `muiogo-provision` — importing an already-built case archive instead of building one.
- `clews-model-review`, `assess-clews-calibration` — checking what you built.
- `muiogo-run`, `muiogo-scenarios`, `muiogo-analyze` — running it and reading the results.

These live in the MUIOGO-AI collection; if one is not available to you,
do the job directly and say which skill would have covered it.
