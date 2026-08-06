# CLEWs Global to MUIO import

Use this workflow after the upstream raw CLEWs Global model solves. Keep all
country-specific helpers and artifacts inside the country package. Do not
modify shared MUIO code for a one-country import.

## 1. Inspect version-specific compatibility

Record:

- CLEWs Global, submodule, otoole, and MUIO revisions;
- the active MUIO parameter registry and OSeMOSYS formulation;
- importer-required workbook sheets and columns;
- solver availability;
- importer and formulation checksums.

Do not assume that a parameter appearing in an OSeMOSYS data file is supported
by MUIO. Support requires all of:

1. a registered parameter and JSON storage mapping;
2. import/export handling;
3. an active declaration in the formulation; and
4. an active equation that uses it.

Create a compatibility inventory before conversion.

For every populated parameter, record explicit and nondefault row counts,
registry/storage/import/export/formulation support, worksheet name and alias,
and probe evidence. Cache this inventory only while importer, registry,
formulation, and otoole-configuration checksums remain unchanged. Follow
`import-quality-gates.md`.

## 2. Convert the CLEWs CSVs

Use otoole with the configuration matching the generated CLEWs data:

```bash
otoole convert csv excel INPUT_DIRECTORY OUTPUT.xlsx \
  --config CLEWS_OTOOL_CONFIG.yaml
```

Preserve this unmodified workbook. Fail if conversion drops populated files,
duplicates indices, or changes values.

Before the full import, calculate the actual Excel worksheet name for every
populated parameter. Excel limits names to 31 characters. Test every uncertain
full or truncated alias with a nondefault probe row and fail if the importer
does not recognize it.

## 3. Prepare a MUIO workbook

Create a country-local script that:

- copies rather than overwrites the otoole workbook;
- adds `TECHGROUP` and assigns every technology exactly once;
- uses structural categories such as power generation, networks, supply,
  demand, land/crops, and water;
- fails on an unclassified technology rather than guessing silently;
- adds descriptions for technologies and temporal sets;
- preserves all OSeMOSYS parameter values;
- inserts `DiscountRate = 0.05` only when the source sheet has no data rows;
- omits empty optional sheets only when required by the installed importer.

Technology groups and descriptions are MUIO interface metadata. They are not
model calibration.

Do not hard-code Fiji time names in a different country. Derive descriptions
from the country configuration and conversion sets.

## 4. Run the unmodified importer

Use a one-off driver that:

1. hashes `API/Classes/Case/ImportTemplate.py`;
2. copies the prepared workbook to MUIO's expected staging location;
3. invokes the existing `ImportTemplate` interface;
4. refuses to overwrite an existing case;
5. verifies that the case folder was created; and
6. checks the importer hash again.

Keep the driver in the country package. Do not retouch `ImportTemplate.py`.

Use a case description that says `raw` and `uncalibrated`. Preserve the
workbook and import log.

## 5. Repair temporal mappings

Some MUIO importer versions assign all imported timeslices to the first season,
day type, and daily bracket. Repair only the generated country case:

1. back up `genData.json` and `RYDtb.json`;
2. map each `TIMESLICE` to the unique active `SEASON` in
   `Conversionls.csv`;
3. map each `TIMESLICE` to the unique active `DAYTYPE` in
   `Conversionld.csv`;
4. map each `TIMESLICE` to the unique active `DAILYTIMEBRACKET` in
   `Conversionlh.csv`;
5. populate `DaySplit` from `DaySplit.csv`; and
6. assert exact timeslice, bracket, and year coverage.

Accept only binary conversion memberships with exactly one active member.
Never infer mappings from row order or names when authoritative conversion
files exist.

## 6. Generate and solve a pre-workaround run

Create a named diagnostic run such as `Raw_PreWorkaround`. Generate its MUIO
data file and solve it. Preserve:

- generated data;
- processed data;
- solver log and solution;
- exported result CSVs;
- objective and status.

This run proves that the imported representation is executable before adding a
formulation workaround.

## 7. Check input parity

Create an analysis-only copy of the MUIO data file:

- rename MUIO's `COMMODITY` set to otoole's `FUEL` only in the copy;
- remove MUIO-only sets and UDC parameters from the copy;
- retain only parameters declared by the otoole configuration and populated in
  the source;
- convert the copy back to CSV with otoole.

Compare source rows by full index and value. Normalize only known equivalent
region labels such as `GLOBAL` and `RE1`.

Classify every source row:

| Class | Meaning |
|---|---|
| Exact | Same explicit index and value |
| Implicit default | Missing row equals the declared default |
| Transformed | Deliberately represented through documented MUIO structure |
| Unsupported | No active native MUIO representation |
| Error | Unexpected loss or numerical change |

Errors block completion. Unsupported non-default values require a documented
active representation or the specific reserve-margin workaround defined by
this skill. Otherwise the whole-country import is blocked.

Also compare source and imported technology-mode, technology-commodity,
input/output, emission, and scenario association counts. Stop on unexplained
dense Cartesian expansion.

## 8. Check result parity

Compare overlapping upstream and MUIO result CSVs by full index. Compare:

- demand;
- capacity and investment;
- activity and production;
- emissions;
- objective components and objective.

Exact result parity is not always possible. Inspect both active formulations
before explaining differences. Examples include different salvage treatment,
unsupported constraints, defaults, or parameter declarations. Do not change
model inputs merely to make results agree.

Run result parity again after any formulation workaround and label each report
with the run it assesses.

Keep the authoritative upstream solve, complete MUIO import, and final MUIO
solve statuses separate. A later success must not overwrite an earlier
capability, parity, or import failure.

## 9. Package for another laptop

The country handoff must include:

- MUIO-ready workbook;
- otoole configuration;
- import, temporal-repair, parity, reserve-check, and export scripts;
- pre-repair backups;
- compatibility inventory;
- worksheet-alias probe report;
- association-expansion report;
- resource estimate and actual measurements;
- input and result parity reports;
- pre-workaround and final solve statuses;
- `documentation/MUIO_IMPORT.md`;
- portable MUIO case ZIP.

Use MUIO's backup directory layout. Omit files that MUIO's own backup omits,
such as a regenerable LP file when applicable. Test the ZIP for corruption and
confirm that it contains the final case metadata and solver outputs.

## Required handoff warning

State which aspects are:

- native imports;
- one-off repairs of importer-created references;
- MUIO display metadata;
- unsupported;
- represented by a workaround.

Do not call a successful import result-equivalent unless input and formulation
parity establish that claim.
