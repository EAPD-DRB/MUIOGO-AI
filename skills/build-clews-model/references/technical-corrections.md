# Permitted technical corrections

A technical correction repairs reproducible software behavior. It must not be
selected because it moves a country result closer to an observation.

## Acceptance test

Apply a correction only when all are true:

1. The defect is reproduced on the pinned upstream revision.
2. Expected behavior follows from upstream configuration, schema, code intent,
   or a general geographic/computational invariant.
3. The fix is minimal and would be correct for another country with the same
   technical condition.
4. A regression check fails before the fix and passes after it.
5. No historical model outcome is used to choose a numerical parameter.
6. The patch, rationale, affected files, and validation are retained.

## Valid correction classes

### Geography and spatial processing

- Handle antimeridian-crossing and multipart countries without dropping,
  duplicating, or spanning the wrong polygon components.
- Generate cells separately for disconnected polygon components when required.
- Use an appropriate equal-area projection for area calculations.
- Clip or normalize longitudes deterministically.
- Correct map rendering across the date line. Keep visualization-only longitude
  shifts out of model geometries.
- Cache immutable downloaded rasters without changing their values.

### Removal of example-country assumptions

- Replace hard-coded sample-country names, ISO codes, nodes, paths, acronyms,
  time slices, or modes with values derived from configuration.
- Generate end-use electricity carriers from each unique configured grid-node
  value, not from a land-region key. Do not synthesize a parallel transmission
  when OSeMOSYS Global already supplies that grid-node conversion.
- Remove stale sample-country values from generated files.
- Fix comparisons or inverted conditions that cause generated country values to
  be replaced by example values.

### Schema and data-pipeline integrity

- Prevent the same crop or proxy code from being counted in both an explicit
  crop and an aggregate category.
- Fix data joins, missing-value handling, unit parsing, and index construction
  when behavior is defined by source schemas.
- Prevent duplicate OSeMOSYS parameter indices at the producer. If a final
  de-duplication guard is necessary, use documented deterministic precedence;
  never choose the retained value based on historical fit.
- Make reruns idempotent by replacing previously generated country rows rather
  than appending them repeatedly.
- Remove stale generated technologies or parameters when the generating set has
  changed.

### Execution and dependency integrity

- Propagate non-zero status from downloads, preprocessing, conversion, model
  generation, solving, and result export.
- Pin a dependency version when the pinned upstream source has a reproducible
  compatibility failure.
- Correct paths, encodings, line endings, or platform behavior without changing
  parameter values.

Run a dependency preflight before the workflow. It must import the required
Python modules, invoke Snakemake and otoole version commands, locate an open
solver, and load the MUIO importer/registry/formulation without mutating them.
Record the interpreter path, exact versions, and every compatibility pin.

## Minimum regression-fixture catalogue

Create only the fixtures relevant to corrections actually applied, but retain
each fixture and command in the country package. The reusable catalogue is:

| Failure class | Minimum fixture assertion |
|---|---|
| Multipart/island boundary | Every component is retained once |
| Missing coastal raster cells | Missing values are handled deterministically without overwriting measured cells |
| Constant raster column | Normalization is finite and deterministic |
| Cache contamination | Unexpected country/crop/scenario files are rejected |
| Crop/proxy duplication | Explicit and aggregate groups contain no duplicated physical proxy |
| Exact crop join | Similar names do not match accidentally |
| Duplicate parameter index | Producer emits a unique full index |
| Rerun idempotence | A second run does not append duplicate rows |
| Excel worksheet truncation | A nondefault probe row survives import/export |
| Temporal import | Every timeslice matches all authoritative conversion matrices |
| Unsupported reserve tags | Native support is proven or the documented checker blocks stale data |

The fixture must fail on the pinned uncorrected revision and pass after the
patch. Do not accept a fixture that only checks a country result.

## Not technical corrections

Do not describe any of the following as bug fixes:

- changing capacity, demand, generation, availability, capacity factors,
  efficiency, costs, emissions, or yields to match observations;
- adding minimum/maximum constraints around historical values;
- adjusting a parameter until an infeasible historical lock becomes feasible;
- removing a technology because doing so improves a historical generation mix;
- smoothing the first free model year after a forced historical year;
- selecting among conflicting data values according to which produces the
  preferred result.

Those belong to later calibration, scenario design, or policy analysis.

## Required patch record

For each correction, record:

- upstream repository and commit;
- submodule commit when applicable;
- defect and reproduction command;
- expected versus observed behavior;
- modified files and concise rationale;
- regression check;
- whether model parameter values or only software behavior changed;
- known limitations and upstream issue/PR, if any.
