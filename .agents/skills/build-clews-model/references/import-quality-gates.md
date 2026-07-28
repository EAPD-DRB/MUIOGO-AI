# Whole-country MUIO import quality gates

Apply these gates when producing the complete MUIO representation of the solved
upstream country model.

## Capability inventory

Create one row for every populated CLEWs parameter:

| Field | Meaning |
|---|---|
| Parameter | Source parameter name |
| Source rows | Explicit row count |
| Nondefault rows | Rows differing from the otoole default |
| Registered | Present in the MUIO registry |
| Stored | Has a JSON storage mapping |
| Imported/exported | Handled in both directions |
| Declared | Present in the active formulation |
| Enforced | Used by an active equation |
| Worksheet | Prepared Excel sheet name |
| Alias recognized | Importer recognizes the full/truncated alias |
| Representation | Native, default, transformed, workaround, unsupported |
| Test | Probe or case-level evidence |

Cache the inventory by checksums of the importer, parameter registry,
formulation, and otoole configuration. Re-run probe tests only when one changes.

## Workbook-name gate

Excel limits worksheet names to 31 characters. Before the full import:

1. calculate the actual output sheet name for every populated parameter;
2. compare it with importer-recognized names and aliases;
3. run a minimal probe containing at least one nondefault row for every
   uncertain alias; and
4. fail if the row does not survive import and export.

Never infer successful support from an empty or all-default sheet.

## Nondefault parity gate

Compare every source row by full index and value. Use the source otoole
configuration to determine defaults.

- `Exact`: explicit row and value match.
- `Implicit default`: omitted row equals the declared default.
- `Transformed`: an explicit, documented, tested formulation representation.
- `Workaround`: a permitted, validated workaround such as reserve margin.
- `Unsupported`: no active representation.
- `Error`: unexpected loss, index change, or numerical difference.

Any `Error` blocks completion. Any unsupported nondefault row also blocks the
whole-country import unless this skill defines a safe formulation workaround.
Do not delete the parameter, relax the model, or continue with a partial
representation.

## Association-expansion gate

Compare source and imported counts for:

- technology-mode membership;
- input and output activity links;
- technology-commodity links;
- technology-emission links;
- scenario/UDC rows; and
- dense parameter arrays generated from sparse defaults.

Report the expansion ratio and largest contributors. Stop on unexplained
Cartesian expansion. An intentionally dense default representation must be
documented and included in the resource estimate.

## Temporal gate

After repair, compare every imported value with:

- `Conversionls.csv`;
- `Conversionld.csv`;
- `Conversionlh.csv`;
- `DaySplit.csv`; and
- `YearSplit.csv`.

Require exactly one season, day type, and daily bracket per timeslice when the
source uses binary membership. Require exact set and year coverage. A feasible
solve does not override a temporal failure.

## Separate statuses

Store these independently in `diagnostics/validation_summary.json`:

```json
{
  "upstream_raw": {"status": "pass", "solver_status": "optimal"},
  "muio_import": {"status": "pass", "nondefault_errors": 0},
  "muio_final": {"status": "pass", "solver_status": "optimal"}
}
```

Do not overwrite an earlier failure with a later success. Explain unsupported,
transformed, and workaround rows in `documentation/MUIO_IMPORT.md`.
