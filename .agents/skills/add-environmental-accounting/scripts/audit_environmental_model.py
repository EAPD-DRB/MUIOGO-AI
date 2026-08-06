#!/usr/bin/env python3
"""Inventory environmental flows and accounting constructs in a MUIO case.

This script is read-only. It inspects JSON sources plus saved annual activity
results when available and emits either a human-readable report or JSON.
"""

from __future__ import annotations

import argparse
import csv
import json
import re
from collections import defaultdict
from pathlib import Path
from typing import Any


CATEGORY_PATTERNS = {
    "water": re.compile(
        r"WAT|WTR|GWT|SUR|PRC|RAIN|EVT|EVAP|DES|SEA|BRN|WASTE.?WATER|EFFLUENT",
        re.IGNORECASE,
    ),
    "land": re.compile(
        r"LND|LAND|FOREST|GRASS|PASTURE|SAVAN|BARREN|CROP|BUILT.?UP",
        re.IGNORECASE,
    ),
    "biomass": re.compile(r"BIO|BIOMASS|RESIDUE|WOOD|CHARCOAL", re.IGNORECASE),
}


def load_json(path: Path) -> dict[str, Any]:
    with path.open(encoding="utf-8-sig") as handle:
        return json.load(handle)


def resolve_model(model: str, datastorage: Path) -> Path:
    direct = Path(model).expanduser()
    if direct.is_dir():
        return direct.resolve()
    candidate = (datastorage / model).expanduser()
    if candidate.is_dir():
        return candidate.resolve()
    available = sorted(
        path.name for path in datastorage.glob("*") if (path / "genData.json").exists()
    )
    raise SystemExit(
        f"Model not found: {model}. Available under {datastorage}: {available}"
    )


def classify(code: str, description: str) -> list[str]:
    text = f"{code} {description}"
    return [name for name, pattern in CATEGORY_PATTERNS.items() if pattern.search(text)]


def result_activity(model: Path) -> dict[str, dict[str, dict[str, float]]]:
    summaries: dict[str, dict[str, dict[str, float]]] = {}
    for path in sorted(
        model.glob("res/*/csv/TotalAnnualTechnologyActivityByMode.csv")
    ):
        by_technology: dict[str, list[float]] = defaultdict(list)
        with path.open(newline="", encoding="utf-8-sig") as handle:
            for row in csv.DictReader(handle):
                technology = row.get("t") or row.get("Technology") or ""
                value = row.get("TotalAnnualTechnologyActivityByMode")
                if technology and value not in (None, ""):
                    by_technology[technology].append(float(value))
        summaries[path.parents[1].name] = {
            technology: {
                "min": min(values),
                "max": max(values),
                "sum": sum(values),
            }
            for technology, values in by_technology.items()
        }
    return summaries


def saved_result_regions(model: Path) -> list[str]:
    regions = set()
    for path in model.glob("res/*/csv/TotalAnnualTechnologyActivityByMode.csv"):
        with path.open(newline="", encoding="utf-8-sig") as handle:
            for row in csv.DictReader(handle):
                region = row.get("r") or row.get("r_x") or row.get("Region")
                if region:
                    regions.add(region)
    return sorted(regions)


def base_parameter_rows(
    model: Path, filename: str, parameter: str, base_scenario: str
) -> dict[str, dict[str, Any]]:
    path = model / filename
    if not path.exists():
        return {}
    rows = load_json(path).get(parameter, {}).get(base_scenario, []) or []
    return {row["TechId"]: row for row in rows if "TechId" in row}


def summarize_year_row(row: dict[str, Any], years: list[str]) -> dict[str, Any]:
    values = [row.get(year) for year in years if row.get(year) is not None]
    if not values:
        return {}
    return {
        "first": row.get(years[0]) if years else None,
        "last": row.get(years[-1]) if years else None,
        "min": min(values),
        "max": max(values),
    }


def build_report(model: Path) -> dict[str, Any]:
    general = load_json(model / "genData.json")
    technologies = general.get("osy-tech", []) or []
    commodities = general.get("osy-comm", []) or []
    emissions = general.get("osy-emis", []) or []
    constraints = general.get("osy-constraints", []) or []
    scenarios = general.get("osy-scenarios", []) or []
    years = [str(year) for year in (general.get("osy-years", []) or [])]
    modes = general.get("osy-mo")
    base_scenario = next(
        (
            scenario["ScenarioId"]
            for scenario in scenarios
            if scenario.get("Scenario") == "SC_0"
        ),
        scenarios[0]["ScenarioId"] if scenarios else "SC_0",
    )

    technology_by_id = {row["TechId"]: row for row in technologies}
    commodity_by_id = {row["CommId"]: row for row in commodities}
    constraints_by_technology: dict[str, list[str]] = defaultdict(list)
    for constraint in constraints:
        for technology_id in constraint.get("CM", []) or []:
            constraints_by_technology[technology_id].append(
                constraint.get("Con", constraint.get("ConId", ""))
            )

    producers: dict[str, list[str]] = defaultdict(list)
    consumers: dict[str, list[str]] = defaultdict(list)
    capacity_consumers: dict[str, list[str]] = defaultdict(list)
    for technology in technologies:
        for commodity_id in technology.get("OAR", []) or []:
            producers[commodity_id].append(technology["Tech"])
        for commodity_id in technology.get("IAR", []) or []:
            consumers[commodity_id].append(technology["Tech"])

    capacity_ratio_path = model / "RYTC.json"
    if capacity_ratio_path.exists():
        capacity_ratios = load_json(capacity_ratio_path)
        for parameter in ("INCR", "ITCR"):
            for scenario_rows in capacity_ratios.get(parameter, {}).values():
                for row in scenario_rows or []:
                    technology = technology_by_id.get(row.get("TechId", ""), {})
                    if technology:
                        capacity_consumers[row.get("CommId", "")].append(
                            technology.get("Tech", row.get("TechId", ""))
                        )

    annual_demand: set[str] = set()
    annual_commodity_path = model / "RYC.json"
    if annual_commodity_path.exists():
        annual_commodity = load_json(annual_commodity_path)
        for parameter in ("SAD", "AAD"):
            for scenario_rows in annual_commodity.get(parameter, {}).values():
                for row in scenario_rows or []:
                    if any(
                        isinstance(row.get(year), (int, float)) and row.get(year) != 0
                        for year in years
                    ):
                        annual_demand.add(row.get("CommId", ""))

    environmental_commodities = []
    for commodity in commodities:
        categories = classify(commodity.get("Comm", ""), commodity.get("Desc", ""))
        if not categories:
            continue
        commodity_id = commodity["CommId"]
        environmental_commodities.append(
            {
                "code": commodity.get("Comm", ""),
                "description": commodity.get("Desc", ""),
                "unit": commodity.get("UnitId", ""),
                "categories": categories,
                "producers": sorted(producers.get(commodity_id, [])),
                "consumers": sorted(consumers.get(commodity_id, [])),
                "capacity_consumers": sorted(
                    set(capacity_consumers.get(commodity_id, []))
                ),
                "has_demand": commodity_id in annual_demand,
                "stranded": bool(producers.get(commodity_id))
                and not consumers.get(commodity_id)
                and not capacity_consumers.get(commodity_id)
                and commodity_id not in annual_demand,
                "diagram_missing_target": bool(producers.get(commodity_id))
                and not consumers.get(commodity_id)
                and commodity_id not in annual_demand,
            }
        )

    environmental_commodity_ids = {
        commodity["CommId"]
        for commodity in commodities
        if classify(commodity.get("Comm", ""), commodity.get("Desc", ""))
    }
    ratio_overrides = []
    base_input_modes_by_technology: dict[str, list[dict[str, Any]]] = defaultdict(
        list
    )
    activity_ratio_path = model / "RYTCM.json"
    if activity_ratio_path.exists():
        activity_ratios = load_json(activity_ratio_path)
        for row in activity_ratios.get("IAR", {}).get(base_scenario, []) or []:
            values = [
                row.get(year)
                for year in years
                if isinstance(row.get(year), (int, float))
            ]
            if not values or not any(value != 0 for value in values):
                continue
            base_input_modes_by_technology[row.get("TechId", "")].append(
                {
                    "mode": row.get("MoId"),
                    "commodity": commodity_by_id.get(
                        row.get("CommId", ""), {}
                    ).get("Comm", row.get("CommId", "")),
                    "first": row.get(years[0]) if years else None,
                    "last": row.get(years[-1]) if years else None,
                    "min": min(values),
                    "max": max(values),
                }
            )
        for parameter in ("IAR", "OAR"):
            for scenario_id, scenario_rows in activity_ratios.get(parameter, {}).items():
                if scenario_id == base_scenario:
                    continue
                for row in scenario_rows or []:
                    if row.get("CommId") not in environmental_commodity_ids:
                        continue
                    changed_years = [
                        year for year in years if row.get(year) is not None
                    ]
                    if not changed_years:
                        continue
                    ratio_overrides.append(
                        {
                            "scenario": scenario_id,
                            "parameter": parameter,
                            "technology": technology_by_id.get(
                                row.get("TechId", ""), {}
                            ).get("Tech", row.get("TechId", "")),
                            "commodity": commodity_by_id.get(
                                row.get("CommId", ""), {}
                            ).get("Comm", row.get("CommId", "")),
                            "years": changed_years,
                        }
                    )

    dummy_and_backstop = []
    terminals = []
    activity = result_activity(model)
    activity_by_technology: dict[str, dict[str, dict[str, float]]] = defaultdict(dict)
    for case, technologies_in_case in activity.items():
        for technology, summary in technologies_in_case.items():
            activity_by_technology[technology][case] = summary

    lower_bounds = base_parameter_rows(model, "RYT.json", "TAL", base_scenario)
    upper_bounds = base_parameter_rows(model, "RYT.json", "TAU", base_scenario)
    activity_change_limits = {
        parameter: base_parameter_rows(model, "RYTM.json", parameter, base_scenario)
        for parameter in ("TADML", "TAIML")
    }
    activity_change_emissions = base_parameter_rows(
        model, "RYTEM.json", "EACR", base_scenario
    )
    constraint_names = {
        row.get("ConId", ""): row.get("Con", row.get("ConId", ""))
        for row in constraints
    }
    constraint_coefficients: dict[str, list[dict[str, Any]]] = defaultdict(list)
    constraint_multiplier_path = model / "RYTCn.json"
    if constraint_multiplier_path.exists():
        multiplier_rows = (
            load_json(constraint_multiplier_path)
            .get("CAM", {})
            .get(base_scenario, [])
            or []
        )
        for row in multiplier_rows:
            values = [row.get(year) for year in years if row.get(year) is not None]
            constraint_coefficients[row.get("TechId", "")].append(
                {
                    "constraint": constraint_names.get(
                        row.get("ConId", ""), row.get("ConId", "")
                    ),
                    "first": row.get(years[0]) if years else None,
                    "last": row.get(years[-1]) if years else None,
                    "min": min(values) if values else None,
                    "max": max(values) if values else None,
                }
            )
    for technology in technologies:
        code = technology.get("Tech", "")
        description = technology.get("Desc", "")
        text = f"{code} {description}"
        record = {
            "code": code,
            "description": description,
            "inputs": [
                commodity_by_id.get(cid, {}).get("Comm", cid)
                for cid in technology.get("IAR", []) or []
            ],
            "outputs": [
                commodity_by_id.get(cid, {}).get("Comm", cid)
                for cid in technology.get("OAR", []) or []
            ],
            "input_modes": sorted(
                base_input_modes_by_technology.get(technology["TechId"], []),
                key=lambda row: (
                    row["mode"] is None,
                    row["mode"] if row["mode"] is not None else 0,
                    row["commodity"],
                ),
            ),
            "constraints": constraints_by_technology.get(technology["TechId"], []),
            "constraint_coefficients": constraint_coefficients.get(
                technology["TechId"], []
            ),
            "activity_decrease_limit": summarize_year_row(
                activity_change_limits["TADML"].get(technology["TechId"], {}),
                years,
            ),
            "activity_increase_limit": summarize_year_row(
                activity_change_limits["TAIML"].get(technology["TechId"], {}),
                years,
            ),
            "activity_change_emission_ratio": summarize_year_row(
                activity_change_emissions.get(technology["TechId"], {}),
                years,
            ),
            "saved_activity": activity_by_technology.get(code, {}),
        }
        if re.search(r"(^DUM|DUMMY|^BST|BACKSTOP|DEFICIT|UNMET)", text, re.I):
            dummy_and_backstop.append(record)
        if re.search(r"(^ENV|ENVIRONMENT|TERMINAL)", text, re.I):
            terminals.append(record)

    land_bounds = []
    for technology in technologies:
        if "land" not in classify(technology.get("Tech", ""), technology.get("Desc", "")):
            continue
        technology_id = technology["TechId"]
        lower = lower_bounds.get(technology_id, {})
        upper = upper_bounds.get(technology_id, {})
        if not lower and not upper:
            continue
        land_bounds.append(
            {
                "code": technology.get("Tech", ""),
                "lower_first": lower.get(years[0]) if years else None,
                "lower_last": lower.get(years[-1]) if years else None,
                "upper_first": upper.get(years[0]) if years else None,
                "upper_last": upper.get(years[-1]) if years else None,
                "saved_activity": activity_by_technology.get(
                    technology.get("Tech", ""), {}
                ),
            }
        )

    return {
        "model": str(model),
        "case_name": general.get("osy-casename", model.name),
        "years": years,
        "modes": modes,
        "saved_result_regions": saved_result_regions(model),
        "scenarios": [
            {
                "id": row.get("ScenarioId"),
                "name": row.get("Scenario"),
                "description": row.get("Desc"),
            }
            for row in scenarios
        ],
        "counts": {
            "technologies": len(technologies),
            "commodities": len(commodities),
            "emissions": len(emissions),
            "constraints": len(constraints),
        },
        "emissions": [
            {
                "code": row.get("Emis", ""),
                "description": row.get("Desc", ""),
                "unit": row.get("UnitId", ""),
            }
            for row in emissions
        ],
        "environmental_commodities": environmental_commodities,
        "environmental_ratio_scenario_overrides": ratio_overrides,
        "dummy_and_backstop_technologies": dummy_and_backstop,
        "existing_environmental_terminals": terminals,
        "land_bounds": land_bounds,
        "saved_result_cases": sorted(activity),
    }


def print_report(report: dict[str, Any]) -> None:
    counts = report["counts"]
    print("HEURISTIC READ-ONLY INVENTORY — verify classifications against model equations")
    print(f"MODEL: {report['case_name']} ({report['model']})")
    print(
        "  "
        f"years={len(report['years'])} modes={report['modes']} "
        f"technologies={counts['technologies']} commodities={counts['commodities']} "
        f"emissions={counts['emissions']} constraints={counts['constraints']}"
    )
    print(
        "  regions from saved activity results:",
        ", ".join(report["saved_result_regions"]) or "none (verify implicit region)",
    )
    if len(report["saved_result_regions"]) > 1:
        print("  WARNING: activity summaries below aggregate regions; inspect row-level results")
    print("  scenarios:", ", ".join(row["name"] or row["id"] for row in report["scenarios"]))
    print("  saved results:", ", ".join(report["saved_result_cases"]) or "none")

    print("\nENVIRONMENTAL COMMODITIES")
    for row in report["environmental_commodities"]:
        flags = []
        if row["stranded"]:
            flags.append("STRANDED")
        elif row["diagram_missing_target"]:
            flags.append("DIAGRAM-MISSING-TARGET")
        if row["has_demand"]:
            flags.append("DEMAND")
        print(
            f"  {row['code']}: {row['unit']} [{','.join(row['categories'])}] "
            f"P={row['producers'] or '-'} C={row['consumers'] or '-'} "
            f"Ccap={row['capacity_consumers'] or '-'} "
            f"{' '.join(flags)}"
        )

    print("\nNON-BASE ENVIRONMENTAL RATIO OVERRIDES")
    if not report["environmental_ratio_scenario_overrides"]:
        print("  none detected")
    for row in report["environmental_ratio_scenario_overrides"]:
        print(
            f"  {row['scenario']} {row['parameter']} {row['technology']} "
            f"{row['commodity']}: {len(row['years'])} explicit year(s)"
        )

    print("\nDUMMIES AND BACKSTOPS")
    if not report["dummy_and_backstop_technologies"]:
        print("  none detected")
    for row in report["dummy_and_backstop_technologies"]:
        nonzero_cases = {
            case: values
            for case, values in row["saved_activity"].items()
            if values["max"] != 0 or values["min"] != 0
        }
        print(
            f"  {row['code']}: in={row['inputs'] or '-'} out={row['outputs'] or '-'} "
            f"constraints={row['constraint_coefficients'] or row['constraints'] or '-'} "
            f"decrease_limit={row['activity_decrease_limit'] or '-'} "
            f"change_emissions={row['activity_change_emission_ratio'] or '-'} "
            f"nonzero={nonzero_cases or '-'}"
        )

    print("\nEXISTING ENVIRONMENTAL TERMINALS")
    if not report["existing_environmental_terminals"]:
        print("  none detected")
    for row in report["existing_environmental_terminals"]:
        print(
            f"  {row['code']}: in={row['inputs'] or '-'} out={row['outputs'] or '-'} "
            f"modes={row['input_modes'] or '-'} "
            f"constraints={row['constraints'] or '-'}"
        )

    print("\nEMISSIONS")
    if not report["emissions"]:
        print("  none defined")
    for row in report["emissions"]:
        print(f"  {row['code']}: {row['unit']} — {row['description']}")

    print("\nLAND BOUNDS AND SAVED ACTIVITY")
    for row in report["land_bounds"]:
        print(
            f"  {row['code']}: lower={row['lower_first']}..{row['lower_last']} "
            f"upper={row['upper_first']}..{row['upper_last']} "
            f"results={row['saved_activity'] or '-'}"
        )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--model", required=True, help="case folder or case name")
    parser.add_argument(
        "--datastorage",
        type=Path,
        default=Path("WebAPP/DataStorage"),
        help="MUIO DataStorage folder when --model is a case name",
    )
    parser.add_argument("--json", action="store_true", help="emit JSON")
    args = parser.parse_args()

    model = resolve_model(args.model, args.datastorage)
    report = build_report(model)
    if args.json:
        print(json.dumps(report, indent=2))
    else:
        print_report(report)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
