# MUIOGO model data

Inside a MUIOGO installation, cases are laid out as `WebAPP/DataStorage/<model>/`. That is a layout description, not a path to type: a machine can carry more than one installation, so ask the launcher for the folder — `CASE="$(muiogo-ai case-path --case '<case>')"` returns the absolute path inside the current world and fails loudly if the case is not there.

## Main files

- `genData.json` contains metadata and sets: technologies, commodities, emissions, scenarios, technology groups, years, time slices, constraints, and model options.
- Parameter files are named from OSeMOSYS index sets, such as `RYTCM.json`, `RYTC.json`, `RYC.json`, and `RYTs.json`.
- Their general shape is `{parameter_id: {scenario_id: [records]}}`.
- `SC_0` is normally the base scenario. Other scenarios may use `null` values to inherit base values.
- `res/<label>/results.txt` stores a solve result; an `Optimal` first line supports the executable-case gate but does not prove calibration.
- `Parameters.json` maps parameter IDs to names, dimensions, defaults, and units. It sits beside the case folders — reach it as `"$(dirname "$CASE")/Parameters.json"`.

## Calibration-relevant parameters

Inspect at least:

- residual capacity and inherited assets;
- specified and accumulated demand;
- capacity and activity lower/upper bounds;
- capacity factors and availability;
- input/output activity ratios and conversion chains;
- capital, fixed, and variable costs;
- operational lives;
- resource, land, water, emissions, reserve, and policy constraints;
- scenario overrides and inheritance;
- year split and time-slice profiles.

Search parameter IDs through `Parameters.json` instead of assuming file locations.

## Structural inventory

`audit_muiogo_model.py` checks objective precursors to calibration:

- metadata and model dimensions;
- set/reference integrity;
- scenario-ID consistency;
- placeholder descriptions;
- dangling technologies;
- year-split normalization;
- broad domain signals;
- saved solve status;
- exact lower/upper bound pairs that may indicate history-fixing.

These are screening checks. Code-prefix domain detection is heuristic, saved results may be stale, and exact bounds may be legitimate. Spot-check every decision-relevant finding.

## Relationship to the existing Claude skill

MUIOGO may also contain `.claude/skills/clews-model-review`. That skill focuses on structure and data consistency against a project benchmark. This Codex skill is complementary: it uses structural integrity as a gate and then evaluates historical fit, forcing independence, held-out validation, robustness, and fitness for purpose.

Do not infer country calibration from similarity to the Namibia case. A benchmark can reveal missing structure or conventions, but country tailoring requires country evidence.
