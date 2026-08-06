# Source traceability standard

> **Both are required.** The registers described below are what you author. The canonical
> six-table ledger in [SCHEMA.md](SCHEMA.md) — one validator, shared with every other CLEWs
> skill — is what you deliver. Nothing here is superseded: keep populating these registers,
> because they hold fisheries-specific fields the ledger has no column for, and they are
> where an analyst actually works.
>
> **Do not author the ledger twice.** These registers are a superset of the canonical
> columns, so `scripts/project_registers_to_ledger.py` generates it: `source-register` →
> `SOURCES`, `assumption-register` → `ASSUMPTIONS`, `calculation-register` →
> `CALCULATIONS`, `parameter-register` → `MODEL_MAP`, and `GAPS` from two places — the
> `data_gap` and `not_applicable` rows of `completeness-register` plus the excluded flows of
> `boundary-register`. An included boundary correction is already lineage, carried by the
> calculation its row cites. Register columns with no canonical home fold into `notes` as
> `key=value` pairs, with the original ID kept as `legacy_id=…`.
>
> `CHANGES.csv` is the one table with nothing to project from: it is an append-only log, so
> pass the `--change-*` arguments when you project. `policymaker-trace-test` and
> `residual-capacity-input` are not projected — the first is a pass/fail line in the delivery
> note and the second is a script input; neither carries lineage.
>
> Two vocabularies differ, and the projector records rather than hides it. The ledger has no
> `proxy` type and derives the type from lineage — a calculation makes a value `derived` even
> where §5 below calls it a proxy or an estimate — so the register's label is preserved as
> `declared_evidence_type=…` in the ledger's `notes`. The principles in this document — the
> lineage chain, exact locators, calculation lineage, proxy labelling, evidence grades, the
> trace test — are unchanged and apply to both.

## Contents

1. Traceability objective
2. Required registers
3. Source citation rules
4. Calculation lineage
5. Proxies and assumptions
6. Time series and projections
7. Model linkage
8. Policymaker trace test
9. Delivery and maintenance

## 1. Traceability objective

Make this question answerable without relying on the original analyst:

> Where did this exact model number come from, and how was it calculated?

Require this chain for every populated Fisheries value:

```text
model value
  -> parameter record
  -> direct source OR calculation record
  -> source observations + assumptions
  -> exact publication/dataset locator
```

A bibliography is not sufficient. A report URL without a table, page, sheet,
cell, dataset variable, or query is not sufficient. Narrative methodology
without the original input values and units is not sufficient.

## 2. Required registers

Copy and populate the six CSV templates in `assets/`.

### Source register

Create one row per publication, dataset, table extract, API result, or official
response. Record:

- stable `source_id`;
- provider and full title;
- edition/version and publication date;
- observation/reference period;
- geography;
- variable or series name;
- exact locator;
- original unit;
- direct URL and access date;
- license/access conditions;
- local filename and SHA-256 when a copy may legally be retained;
- archived URL when useful;
- quality grade and notes.

Split one publication into multiple source rows when different tables,
variables, units, or reference periods feed different calculations.

### Assumption register

Create one row per judgment not directly observed. Record:

- stable `assumption_id`;
- precise statement;
- rationale;
- supporting source IDs;
- lower, central, and upper values with unit;
- whether sensitivity analysis is required;
- owner/reviewer and review status.

Do not hide an assumption inside a formula or model description.

### Calculation register

Create one row per transformation that produces a model-ready number or series.
Record:

- stable `calculation_id`;
- output description;
- explicit formula;
- source IDs, assumption IDs, and upstream calculation IDs;
- original input values and units;
- conversion constants;
- method, interpolation, or retirement rule;
- script path and version/commit when code performs the calculation;
- rounding;
- output value and unit;
- review status.

Use a separate record when different technologies, years, modes, or scenarios
use materially different formulas.

### Parameter register

Create one row per direct value or homogeneous time-series segment written into
the model. Record:

- stable `parameter_record_id`;
- model file and parameter;
- entity, secondary entity, mode, scenario, and years;
- exact value or series expression;
- model unit;
- evidence type;
- direct source IDs or calculation ID;
- assumption IDs;
- uncertainty and confidence;
- `superseded_by` — blank while the row is live, and the `CHG_` ID that retired it once it
  is not. Retire rows this way instead of deleting them: the ledger keeps retired lineage so
  an earlier model version stays reconstructable, and a retired row stops counting as
  coverage.

If a row represents interpolation, identify the calculation record containing
both endpoints and the interpolation rule.

### Boundary register

Create one row per material flow crossing the Fisheries boundary. Record:

- inclusion/exclusion decision;
- original statistical sector;
- destination model service/pathway;
- baseline value and unit;
- double-counting action;
- calculation and source IDs.

### Completeness register

Create one row per material subsector parameter or flow investigated. Record
applicability and one of `direct`, `derived`, `proxy`, `estimated`, `data_gap`,
or `not_applicable`. Identify upgrade sources for weak or missing evidence.

## 3. Source citation rules

Prefer primary national sources:

1. statistical office, fisheries authority, energy ministry, environment/water
   authority, customs, port authority, or official registry;
2. official international datasets;
3. peer-reviewed country studies;
4. engineering standards, manufacturer data, or documented analogues;
5. analyst estimate.

For PDFs, cite page and table/figure. For spreadsheets, cite workbook edition,
sheet, row label, column/year, and cell/range when stable. For databases, cite
dataset version, variable/item codes, filters, geography, and download date. For
APIs, preserve the endpoint, query parameters or request body, response date,
and result file hash.

Use a direct document/data URL rather than a search-results page. Record a
landing page as an additional URL when it explains versioning or licensing.
When links are temporary, retain an archived URL or legally permitted local
copy.

If a source requires login, records access restrictions, changes dynamically,
or was supplied privately, state how a reviewer can request or reproduce access.

## 4. Calculation lineage

Preserve original observations before transformations. Record every:

- energy conversion, such as ktoe to PJ;
- efficiency and whether it is input/output or output/input;
- useful-versus-final-energy transformation;
- mass, volume, power, or throughput conversion;
- currency year, exchange rate, deflator, and capacity basis;
- allocation among subsectors or carriers;
- normalization from observation year to model base year;
- interpolation and extrapolation;
- residual-capacity and retirement calculation;
- emission-factor basis;
- rounding step.

Avoid formulas such as “adjusted based on expert judgment.” State the numerical
operation and the assumption ID. Preserve sufficient precision to reproduce the
model value, then record final rounding separately.

When code performs a calculation, retain:

- script path;
- command;
- input filenames and hashes;
- code commit or script checksum;
- deterministic output;
- software version when it can affect the result.

## 5. Proxies and assumptions

Label a proxy explicitly. Record:

- source country/technology/year;
- target country/technology/year;
- transfer rationale;
- scaling or adjustment;
- known structural differences;
- uncertainty range;
- national agency or dataset that could replace it.

Do not present a proxy as observed national data. Do not convert lack of
evidence into a precise zero. Use zero only when “none” is an evidenced physical
statement or the parameter is genuinely not applicable.

Use evidence grades consistently:

| Grade | Meaning |
|---|---|
| A | Direct official national observation |
| B | Derived from official national observations |
| C | Authoritative international, peer-reviewed, or engineering proxy |
| D | Transparent analyst estimate with material uncertainty |

The grade describes evidence strength, not whether the parameter is allowed.
Grade D values may be necessary; expose them and sensitivity-test material ones.

## 6. Time series and projections

For each series, identify:

- observed years;
- missing years;
- normalized base year;
- interpolation rule;
- projection start;
- driver and formula;
- scenario modifications;
- endpoint assumptions.

Never cite a historical source as though it supplied projected values. Link
projected years to the calculation and assumption records that created them.
Distinguish policy targets from forecasts and model scenarios.

## 7. Model linkage

Put parameter record IDs in:

- technology and commodity descriptions when practical;
- sector methodology documents;
- calculation comments or generator configuration;
- validation reports.

Do not rely only on descriptions: machine-readable registers remain
authoritative. A single parameter record may cover a flat series, but different
sources, formulas, or scenarios require separate records.

Validate cross-references with:

```bash
python scripts/validate_provenance.py \
  --sources source-register.csv \
  --assumptions assumption-register.csv \
  --calculations calculation-register.csv \
  --parameters parameter-register.csv \
  --boundaries boundary-register.csv \
  --completeness completeness-register.csv
```

## 8. Policymaker trace test

Before delivery, sample **ten** populated model values — not a percentage, so the cost does
not scale with model size. Draw them to cover the categories below, one each where the model
has one. Include:

- at least one direct value;
- one unit conversion;
- one efficiency-derived service value;
- one residual-capacity value;
- one retirement year;
- one cost;
- one emissions factor;
- one projected value;
- one proxy or analyst estimate;
- one cross-sector boundary correction.

For each sample, reconstruct the model value from the registers and cited source
without using analyst memory. Confirm:

1. the source opens or its access route is documented;
2. the exact input is found at the stated locator;
3. original value and unit match;
4. formula and assumptions reproduce the result;
5. rounding explains any final difference;
6. the parameter record points to the correct model location.

Record the sample IDs, reviewer, date, and pass/fail result. Any failed trace is
a delivery failure.

## 9. Delivery and maintenance

Deliver the registers beside the model, not only in an analyst folder. Include
raw extracts when licensing permits; otherwise include access instructions,
query definitions, filenames, and hashes.

When a source is replaced:

- create a new source ID or version;
- update affected calculations and parameters;
- retain the superseded lineage;
- identify changed model values;
- record the replacement as a row in `CHANGES.csv` — re-project with the `--change-*`
  arguments, which fill `map_rows_affected` with the `MAP_` IDs actually in the ledger, and
  set `superseded_by` on a retired `parameter-register` row rather than deleting it.

**Then re-run only what the change touched.** Compare the new model values against the old
ones first:

- **No model value changed** — a better locator, a fixed URL, a corrected citation, a
  re-issued edition with identical numbers. This is a Class A change. Do **not** regenerate
  or re-solve anything. Record `resolve_status=objective_unchanged` and re-trace only the
  affected values.
- **Some model values changed.** Regenerate and re-solve the scenarios those values feed.
  Re-solve every scenario only when the change reaches a parameter every scenario shares.
- **The trace test** is re-run on the affected samples, not on all ten, unless the
  replacement touched more than a quarter of the sampled values.

A re-solve is worth tens of minutes to hours. Never spend one to prove that a number which
did not change did not change.

Never overwrite source provenance in a way that makes an earlier model version
unreconstructable.
