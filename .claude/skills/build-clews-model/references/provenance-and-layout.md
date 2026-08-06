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
│   ├── CALCULATIONS.csv
│   ├── ASSUMPTIONS.csv
│   ├── MODEL_MAP.csv
│   ├── GAPS.csv
│   ├── CHANGES.csv
│   ├── DATA_SOURCES.md
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

The command refuses to overwrite an existing package. `--allow-existing`
creates only missing files and never edits an existing CSV or document.

The active MUIO runtime case may contain a short README that points back to this
canonical package. Do not duplicate the canonical ledgers inside the runtime
case.

## Canonical ledgers

[SCHEMA.md](SCHEMA.md) defines the only ledger schemas. The scaffold creates
its six header-only CSVs directly from the same vendored Python schema used by
the validator, so the templates and checks cannot drift.

The invariant is:

> Every populated model value resolves to one active `MODEL_MAP.csv` row; every
> map row names source, calculation or assumption evidence; every referenced
> record resolves; every retained evidence file matches its recorded digest.

Use `DATA_SOURCES.md` only for source conflicts, access restrictions,
government-review questions and narrative context. It is not a seventh ledger.

`MODEL_MAP.model_file` names one exact package-relative file, never a glob. Map
`config/config.yaml` as well as every populated `model/inputs/*.csv`. Split a
map row when the source, calculation, assumption, model unit, scenario, mode or
value expression changes. Preserve retired rows with `superseded_by`; never
delete earlier lineage.

Put unavailable lineage in `GAPS.csv`. A gap is not evidence for an active
value: use a documented assumption when the model must carry a value, or leave
the value out when no defensible assumption exists.

### Successor model versions

For a new version of an existing model, copy the complete current canonical
ledger and retained evidence into the new package before adding or changing
records. Carry unchanged records forward, add new records, and update or
supersede changed records. Do not replace inherited records with a source row
or note that merely points to the previous version. Previous-version references
are supplementary chronology only; the new ledger must stand on its own.

This rule applies to every country and model family.

## Validation

Run:

```bash
python scripts/validate_provenance.py PACKAGE_ROOT --stage scaffold
python scripts/validate_provenance.py PACKAGE_ROOT --stage build
python scripts/validate_provenance.py PACKAGE_ROOT --stage delivery
```

The command combines two independent checks:

- `provenance.py` validates the canonical six ledgers, references,
  calculation dependencies, evidence files and populated input coverage;
- `validate_package.py` validates the country-package layout, repository pins,
  active configuration and frozen baseline.

Both scripts are vendored inside the installed skill and copied into each
country package. They use only the Python standard library, so a single copied
`build-clews-model` folder works in Claude and Codex without the repository's
`skills/shared/` directory.

Validation proves mechanical lineage and artifact integrity. It does not prove
that a source is true, unbiased or appropriate for the model boundary. Record
conflicts and quality limitations rather than silently resolving them.

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
