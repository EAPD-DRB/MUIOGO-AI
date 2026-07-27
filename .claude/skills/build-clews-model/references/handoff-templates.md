# Required handoff templates

Initialize the package with `scripts/init_country_package.py`. Its templates
under `assets/country-package/` are authoritative; do not recreate an older
root-level handoff layout.

## Current documentation

Complete:

- `documentation/CURRENT_MODEL.md`: identity, separate build/import/final
  statuses, current representation, intended use, and unsuitable uses;
- `documentation/MODEL_STRUCTURE.md`: active systems, objects, cross-sector
  links, spatial/temporal structure, and accounting boundaries;
- `documentation/KNOWN_LIMITATIONS.md`: source gaps, proxies, unsupported
  parameters, formulation differences, raw behavior, and fitness limits;
- `documentation/HISTORY.md`: dated actions with evidence;
- `documentation/CALIBRATION_HANDOFF.md`: diagnostic comparisons and later data
  needs, none applied to the raw build;
- `documentation/MUIO_IMPORT.md`: checksums, capability inventory, workbook
  preparation, temporal repair, parity, workarounds, and exact commands;
- `documentation/REPRODUCE.md`: checkout through restore commands.

Keep dated or superseded evidence under `documentation/history/`. Current files
must not describe a retired formulation as active.

## Provenance ledgers

Use the schemas in `references/provenance-and-layout.md` and the generated:

- `data_sources/SOURCES.csv`;
- `data_sources/ASSUMPTIONS.csv`;
- `data_sources/CALCULATIONS.csv`;
- `data_sources/MODEL_DATA_MAP.csv`;
- `data_sources/DATA_SOURCES.md`.

The CSVs are machine-readable records. Use `DATA_SOURCES.md` for conflicts,
quality discussion, documentation gaps, and government-review questions.

## Calibration handoff requirements

The diagnostic table must record:

| Sector/metric | Observed source ID | Geography/period/unit | Observed value | Raw model value | Difference | Suspected cause | Candidate future parameter | Applied in raw model |
|---|---|---|---:|---:|---:|---|---|---|

Every `Applied in raw model` value must be `No`. Keep historical performance
data separate from structural evidence used by the raw build.

## MUIO import requirements

Report:

| Stage | Status | Solver status | Evidence |
|---|---|---|---|
| Authoritative upstream raw model | | | |
| Complete MUIO import | | n/a | |
| Final MUIO model | | | |

Include capability coverage, worksheet alias probes, technology grouping,
discount-rate handling, temporal mapping, input/result parity, association
expansion, reserve-margin representation, stale-check status, and exact import,
repair, parity, estimate, generate, solve, validate, package, and restore
commands.

## Machine-readable statuses

Maintain `diagnostics/validation_summary.json`:

```json
{
  "upstream_raw": {
    "status": "pending",
    "solver_status": null,
    "evidence": null
  },
  "muio_import": {
    "status": "pending",
    "nondefault_errors": null,
    "unsupported_nondefault_rows": null,
    "evidence": null
  },
  "muio_final": {
    "status": "pending",
    "solver_status": null,
    "evidence": null
  }
}
```

Change each status to `pass` only when its independent evidence is complete.
