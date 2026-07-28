# Country package and provenance contract

Use this contract from the first build step. Do not retrofit provenance after
the model is solved.

## Required package layout

```text
<Country>_CLEWs_build/
├── README.md
├── backups/
├── config/
│   ├── config.yaml
│   ├── upstream_versions.json
│   └── baseline_manifest.json
├── data_sources/
│   ├── SOURCES.csv
│   ├── DATA_SOURCES.md
│   ├── ASSUMPTIONS.csv
│   ├── CALCULATIONS.csv
│   ├── MODEL_DATA_MAP.csv
│   ├── evidence/
│   └── calculation_notes/
├── diagnostics/
├── documentation/
│   ├── CURRENT_MODEL.md
│   ├── MODEL_STRUCTURE.md
│   ├── KNOWN_LIMITATIONS.md
│   ├── HISTORY.md
│   ├── CALIBRATION_HANDOFF.md
│   ├── MUIO_IMPORT.md
│   ├── REPRODUCE.md
│   └── history/
├── geospatial/
│   ├── boundary/
│   └── summary_stats/
├── licenses/
├── model/
│   ├── inputs/
│   └── results/
├── muio/
├── patches/
└── scripts/
```

Create the package with:

```bash
python scripts/init_country_package.py PACKAGE_ROOT \
  --country "Country name" --iso3 ISO
```

The command refuses to overwrite an existing package. Use `--allow-existing`
only to add missing scaffold files; it never replaces existing files.

The active MUIO runtime case may contain a short README that points back to this
canonical package. Do not duplicate the canonical ledgers inside the runtime
case.

## Canonical ledgers

`SOURCES.csv` is the machine-readable source catalogue. `DATA_SOURCES.md`
provides narrative, conflicts, government-review questions, and context; it is
not the canonical identifier store.

Use stable IDs:

- sources: `DS-...`;
- assumptions: `A-...`;
- calculations: `C-...`;
- model-map rows: `M-...`.

Separate multiple IDs or coverage patterns with semicolons.

### `SOURCES.csv`

Use one row per externally sourced variable or coherent product slice. Record:

```text
source_id,provider,product,edition,reference_period,variable,source_unit,
geography,model_use,selection,transformation,quality,proxy,official_url,
license,national_alternative,review_owner,local_evidence_path,sha256,status,
notes
```

Use `status=active` when the source affects the raw model. Use `diagnostic`,
`calibration_candidate`, or `scenario_context` when it does not. Use
`documentation_gap` only when lineage is genuinely unavailable; explain the
gap in `notes`.

When `local_evidence_path` names a retained file, record its SHA-256. Do not
redistribute restricted or copyrighted source files merely to fill the folder.
For restricted evidence, record exact metadata, access conditions, extraction
instructions, and the checksum held by the authorized team.

### `ASSUMPTIONS.csv`

Record modeller choices separately from published facts:

```text
assumption_id,sector,description,used_for,status,source_or_reason,review_need
```

Every `active` assumption must be referenced from `MODEL_DATA_MAP.csv`.

### `CALCULATIONS.csv`

Record transformations that actually determine model values:

```text
calculation_id,sector,question,formula,inputs,output,units,model_location,
source_ids,assumption_ids,status,notes
```

Every `active` calculation must be referenced from `MODEL_DATA_MAP.csv`.
Place longer derivations in `calculation_notes/`.

### `MODEL_DATA_MAP.csv`

Connect the active model to its lineage:

```text
map_id,sector,model_entity,parameter_or_file,coverage_patterns,modes,years,
meaning,source_ids,assumption_ids,calculation_ids,representation_status,notes
```

`coverage_patterns` contains package-relative exact paths or glob patterns.
At delivery, every populated `model/inputs/*.csv` and `config/config.yaml` must
match at least one active map row. Prefer exact files or coherent families over
one catch-all pattern. A source ID may identify an upstream database when
row-level original lineage is unavailable, but mark that limitation explicitly.

## What validation proves

Run:

```bash
python scripts/validate_provenance.py PACKAGE_ROOT --stage build
python scripts/validate_provenance.py PACKAGE_ROOT --stage delivery
```

The validator proves:

- required files and schemas exist;
- identifiers are unique and references resolve;
- active sources, assumptions, and calculations are mapped;
- populated raw input files are covered;
- retained evidence checksums match;
- repositories are pinned to full commits;
- the final raw baseline artifacts match their manifest.

It does not prove that a cited source is true, unbiased, or suitable for the
model boundary. Record source conflicts and quality limitations rather than
silently resolving them.

## Frozen raw baseline

After all raw-build and MUIO delivery checks pass, create one frozen source
package and register the existing portable raw MUIO ZIP:

```bash
python scripts/freeze_raw_baseline.py PACKAGE_ROOT \
  --muio-archive muio/COUNTRY_raw_MUIO.zip
```

The source archive excludes `backups/`, LP/MPS files, Python caches,
`config/baseline_manifest.json`, and portable MUIO ZIPs so the two baseline
artifacts are not duplicated. The command refuses to overwrite an existing
archive or a completed manifest.

`baseline_manifest.json` records artifact paths, byte sizes, SHA-256 values,
the complete archived-package content tree, and separate raw input/result tree
hashes. “Frozen” is a process rule: never edit or overwrite a registered
baseline. Create a new dated milestone instead.

Pinning code removes the need to archive whole upstream Git checkouts. Pinning
does not freeze mutable downloaded datasets; record editions and checksums for
the actual inputs used.
