# Source and government review

Build a source catalogue exact enough that country experts can accept a source
or propose a better national dataset. `data_sources/SOURCES.csv` is the
machine-readable register. `data_sources/DATA_SOURCES.md` holds the narrative,
the conflicts and the government-review table. The column rules are in
[SCHEMA.md](SCHEMA.md); this file says what to put in them and what review
adds on top.

## Source fields

One `SOURCES.csv` row per externally sourced variable or coherent product slice.

| Column | What to record |
|---|---|
| `source_id` | Stable `SRC_` identifier |
| `provider` | Institution responsible for the product |
| `product` | Exact dataset or product name |
| `edition` | Release, version or publication date |
| `reference_period` | Year, climatology, horizon or scenario |
| `geography` | Coverage and spatial resolution |
| `variable` | Exact variable or element used |
| `source_unit` | Unit as published, before conversion |
| `exact_locator` | Sheet, table, page, dataset variable or query that returns the number |
| `url` | Official landing page or catalogue entry, or a ledger-relative path when the only copy is retained locally |
| `access_date` | ISO `YYYY-MM-DD` |
| `license` | Reuse conditions |
| `sha256` | Digest of each retained local evidence file |

Selection (filters, ranks, categories), transformation (aggregation,
interpolation, conversion) and the model parameter affected do not get their own
columns. Selection and transformation go in `CALCULATIONS.csv`. The parameter
affected goes in `MODEL_MAP.csv`. Quality flags (official, estimated, imputed,
modelled, unknown) and the original item behind a proxy go in `notes`, and again
in the government-review table below. A gap in lineage goes in `GAPS.csv`.

Record enough to tell a historical low-input GAEZ layer from a future high-input
climate layer. Never write only `GAEZ`, `FAOSTAT` or `population data`.

## Crop source and proxy register

For each selected crop item, record:

- exact source item and code;
- harvested-area rank, value, unit, year and quality flag;
- production value, unit, year and quality flag when used as demand;
- explicit output or aggregate membership;
- exact GAEZ code and layer;
- irrigation or rain-fed, and high or low input, combinations;
- climate model, pathway and period;
- available-water-capacity assumption;
- proxy rationale and expected yield, water and climate differences.

Use exact item equality for joins. Reject substring matching, duplicate proxy
rasters, a crop that appears in both explicit and aggregate groups, and a proxy
code counted more than once.

## Government-review table

`DATA_SOURCES.md` is scaffolded with this table. Fill it in:

| Decision | Current source or assumption | Why it matters | Suggested reviewer | Better national data? | Status |
|---|---|---|---|---|---|

Cite the `SRC_` or `ASM_` ID in the second column. At minimum cover:

- administrative boundaries and model domain;
- seasons and time zone;
- crop selection, production anchors and quality flags;
- crop proxies and aggregate crops;
- land cover;
- crop suitability and potential yield;
- precipitation and evapotranspiration;
- irrigation requirements and groundwater and surface-water availability;
- population or other demand-growth series;
- energy resource and technology applicability inputs.

For status use one of: active, diagnostic, calibration candidate, scenario
context. Lineage that cannot be found is a row in `GAPS.csv`, not a status here.

The table is not calibration. It lists possible future source substitutions
without applying any of them to the raw build.

## Keep the files in step

Keep source choices consistent across `SOURCES.csv`, `MODEL_MAP.csv`,
`documentation/CURRENT_MODEL.md`, `config/config.yaml` and the generated
parameters. A citation records lineage, not truth. Keep quality flags, boundary
conflicts, revisions and independent cross-checks.
