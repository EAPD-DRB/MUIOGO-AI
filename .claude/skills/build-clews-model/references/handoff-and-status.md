# Handoff and status requirements

The templates under `assets/country-package/` are authoritative for the package
documents. This file adds what the delivered package must say about calibration
handoff, MUIO import and machine-readable status. The ledgers are the six tables
in [SCHEMA.md](SCHEMA.md).

## Calibration handoff requirements

`documentation/CALIBRATION_HANDOFF.md` records diagnostic comparisons and later
data needs. Its diagnostic table has these columns:

| Sector/metric | Observed source ID | Geography/period/unit | Observed value | Raw model value | Difference | Suspected cause | Candidate future parameter | Applied in raw model |
|---|---|---|---:|---:|---:|---|---|---|

Every `Applied in raw model` value is `No`. The observed source ID is a `SRC_`
ID in `SOURCES.csv`. Keep historical performance data apart from the structural
evidence the raw build uses.

## MUIO import requirements

Report the three stages separately in `documentation/MUIO_IMPORT.md`:

| Stage | Status | Solver status | Evidence |
|---|---|---|---|
| Authoritative upstream raw model | | | |
| Complete MUIO import | | n/a | |
| Final MUIO model | | | |

Also report:

- capability coverage and worksheet alias probes;
- technology grouping and discount-rate handling;
- temporal mapping;
- input and result parity;
- association expansion;
- reserve-margin representation and stale-check status;
- the exact import, repair, parity, estimate, generate, solve, validate,
  package and restore commands.

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

Change a status to `pass` only when its own evidence is complete.
`freeze_raw_baseline.py` refuses to run while any of the three is not `pass`.
