#!/usr/bin/env python3
"""Create a structural and constraint inventory for one MUIOGO model folder.

This is a screening tool. Its findings must be spot-checked before grading.
It uses only the Python standard library.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from collections import defaultdict
from pathlib import Path
from typing import Any


PLACEHOLDERS = {"", "default commodity", "default technology"}
SECTOR_CODES = {
    "energy": ("PWR", "ELC", "COA", "DSL", "SOL", "WND", "HYD", "NGS", "HFO", "GSL", "KER", "LPG", "BIO"),
    "land": ("LND", "CRP", "LVS", "AGR", "FOR", "GRS", "PAS"),
    "water": ("WAT", "WTR", "GWT", "SUR", "PRC", "DES", "EVT"),
}
BOUND_PAIRS = (
    ("TMPAL", "TMPAU", "model-period activity"),
    ("TAL", "TAU", "annual activity"),
    ("TAMinC", "TAMaxC", "annual capacity"),
    ("TAMinCI", "TAMaxCI", "annual capacity investment"),
)


def load_json(path: Path) -> Any:
    with path.open(encoding="utf-8") as handle:
        return json.load(handle)


def finding(level: str, code: str, message: str, evidence: Any = None) -> dict[str, Any]:
    item: dict[str, Any] = {"level": level, "code": code, "message": message}
    if evidence is not None:
        item["evidence"] = evidence
    return item


def records_by_parameter(model_dir: Path) -> tuple[dict[str, dict[str, list[dict[str, Any]]]], list[str]]:
    parameters: dict[str, dict[str, list[dict[str, Any]]]] = {}
    errors: list[str] = []
    for path in sorted(model_dir.glob("*.json")):
        if path.name == "genData.json":
            continue
        try:
            payload = load_json(path)
        except (OSError, json.JSONDecodeError) as exc:
            errors.append(f"{path.name}: {exc}")
            continue
        if not isinstance(payload, dict):
            continue
        for parameter_id, scenarios in payload.items():
            if not isinstance(scenarios, dict):
                continue
            normalized: dict[str, list[dict[str, Any]]] = {}
            for scenario_id, rows in scenarios.items():
                if rows is None:
                    normalized[str(scenario_id)] = []
                elif isinstance(rows, list):
                    normalized[str(scenario_id)] = [row for row in rows if isinstance(row, dict)]
            parameters[parameter_id] = normalized
    return parameters, errors


def exact_bound_matches(
    parameters: dict[str, dict[str, list[dict[str, Any]]]], years: list[str]
) -> list[dict[str, Any]]:
    matches: list[dict[str, Any]] = []
    year_set = set(years)

    def expanded(rows: list[dict[str, Any]]) -> dict[tuple[tuple[tuple[str, str], ...], str], float]:
        result: dict[tuple[tuple[tuple[str, str], ...], str], float] = {}
        for row in rows:
            identity = tuple(
                sorted(
                    (str(key), str(value))
                    for key, value in row.items()
                    if key not in year_set and value is not None
                )
            )
            for year in years:
                value = row.get(year)
                if isinstance(value, (int, float)):
                    result[(identity, year)] = float(value)
        return result

    for lower_id, upper_id, kind in BOUND_PAIRS:
        lower = parameters.get(lower_id, {})
        upper = parameters.get(upper_id, {})
        for scenario_id in sorted(set(lower) & set(upper)):
            low_values = expanded(lower[scenario_id])
            high_values = expanded(upper[scenario_id])
            for key in sorted(set(low_values) & set(high_values)):
                low = low_values[key]
                high = high_values[key]
                if abs(low - high) <= max(1e-9, 1e-9 * max(abs(low), abs(high))):
                    identity, year = key
                    matches.append(
                        {
                            "kind": kind,
                            "lower_parameter": lower_id,
                            "upper_parameter": upper_id,
                            "scenario": scenario_id,
                            "year": year,
                            "identity": dict(identity),
                            "value": low,
                        }
                    )
    return matches


def audit(model_dir: Path) -> dict[str, Any]:
    gen_path = model_dir / "genData.json"
    if not gen_path.is_file():
        raise ValueError(f"genData.json not found in {model_dir}")
    gen = load_json(gen_path)
    if not isinstance(gen, dict):
        raise ValueError("genData.json must contain a JSON object")

    tech_rows = gen.get("osy-tech") or []
    comm_rows = gen.get("osy-comm") or []
    emission_rows = gen.get("osy-emis") or []
    scenario_rows = gen.get("osy-scenarios") or []
    years_raw = gen.get("osy-years") or []
    years = [str(year) for year in years_raw]
    techs = {str(row.get("TechId")): row for row in tech_rows if isinstance(row, dict) and row.get("TechId")}
    comms = {str(row.get("CommId")): row for row in comm_rows if isinstance(row, dict) and row.get("CommId")}
    emissions = {
        str(row.get("EmisId")): row for row in emission_rows if isinstance(row, dict) and row.get("EmisId")
    }
    scenarios = {
        str(row.get("ScenarioId")): row
        for row in scenario_rows
        if isinstance(row, dict) and row.get("ScenarioId")
    }
    parameters, parse_errors = records_by_parameter(model_dir)
    findings: list[dict[str, Any]] = []
    for error in parse_errors:
        findings.append(finding("fail", "json_parse", "Could not parse model data file", error))

    serialized = "\n".join(
        path.read_text(encoding="utf-8", errors="replace")
        for path in sorted(model_dir.glob("*.json"))
        if path.name != "genData.json"
    )
    patterns = {
        "technology": (re.compile(r"TEC_[0-9A-Za-z_-]+"), set(techs)),
        "commodity": (re.compile(r"COM_[0-9A-Za-z_-]+"), set(comms)),
        "emission": (re.compile(r"EMI_[0-9A-Za-z_-]+"), set(emissions)),
        "scenario": (re.compile(r"SC_[0-9A-Za-z_-]+"), set(scenarios)),
    }
    reference_counts: dict[str, int] = {}
    for category, (pattern, defined) in patterns.items():
        used = set(pattern.findall(serialized))
        reference_counts[category] = len(used)
        unknown = sorted(used - defined)
        if unknown:
            findings.append(
                finding(
                    "fail",
                    f"unknown_{category}_references",
                    f"{len(unknown)} referenced {category} IDs are not defined",
                    unknown[:25],
                )
            )

    for category, rows, description_key in (
        ("technology", techs, "Desc"),
        ("commodity", comms, "Desc"),
    ):
        placeholders = [
            key
            for key, row in rows.items()
            if str(row.get(description_key, "")).strip().lower() in PLACEHOLDERS
        ]
        if placeholders:
            level = "fail" if len(placeholders) == len(rows) else "warn"
            findings.append(
                finding(
                    level,
                    f"placeholder_{category}_descriptions",
                    f"{len(placeholders)}/{len(rows)} {category} descriptions are blank or placeholders",
                    placeholders[:25],
                )
            )

    io_techs: set[str] = set()
    for parameter_id in ("IAR", "OAR"):
        for rows in parameters.get(parameter_id, {}).values():
            io_techs.update(str(row["TechId"]) for row in rows if row.get("TechId"))
    dangling = sorted(set(techs) - io_techs)
    if dangling:
        findings.append(
            finding(
                "warn",
                "dangling_technologies",
                f"{len(dangling)} technologies have neither input nor output activity ratios",
                dangling[:25],
            )
        )

    year_split_issues: list[dict[str, Any]] = []
    for scenario_id, rows in parameters.get("YS", {}).items():
        for year in years:
            values = [row.get(year) for row in rows if isinstance(row.get(year), (int, float))]
            if values:
                total = float(sum(values))
                if abs(total - 1.0) > 1e-6:
                    year_split_issues.append({"scenario": scenario_id, "year": year, "sum": round(total, 9)})
    if year_split_issues:
        findings.append(
            finding(
                "warn",
                "year_split_not_normalized",
                f"{len(year_split_issues)} scenario-year YearSplit sums differ from 1",
                year_split_issues[:25],
            )
        )

    labels = " ".join(
        str(value)
        for row in list(techs.values()) + list(comms.values())
        for value in (row.get("Tech"), row.get("Comm"), row.get("Desc"))
        if value
    ).upper()
    domains = {domain: any(code in labels for code in codes) for domain, codes in SECTOR_CODES.items()}
    domains["climate"] = bool(emissions)
    domains["nexus"] = sum(domains.values()) >= 3 and bool(parameters.get("IAR") or parameters.get("OAR"))

    result_statuses: list[dict[str, Any]] = []
    result_dir = model_dir / "res"
    if result_dir.is_dir():
        for result_file in sorted(result_dir.glob("*/results.txt")):
            try:
                first_line = result_file.open(encoding="utf-8", errors="replace").readline().strip()
            except OSError as exc:
                first_line = f"ERROR: {exc}"
            result_statuses.append(
                {
                    "label": result_file.parent.name,
                    "first_line": first_line,
                    "appears_optimal": first_line.lower().startswith("optimal"),
                }
            )
    if not result_statuses:
        findings.append(finding("warn", "no_saved_results", "No saved solve results were found"))
    elif not any(item["appears_optimal"] for item in result_statuses):
        findings.append(finding("fail", "no_optimal_result", "No saved result appears optimal"))
    elif any(not item["appears_optimal"] for item in result_statuses):
        findings.append(finding("warn", "nonoptimal_saved_results", "Some saved results do not appear optimal"))

    fixed_matches = exact_bound_matches(parameters, years)
    if fixed_matches:
        findings.append(
            finding(
                "warn",
                "exact_bound_pairs",
                f"{len(fixed_matches)} exact lower/upper bound matches may history-fix outcomes",
                fixed_matches[:25],
            )
        )

    return {
        "schema_version": 1,
        "model_path": str(model_dir.resolve()),
        "metadata": {
            "case_name": gen.get("osy-casename"),
            "description": gen.get("osy-desc"),
            "version": gen.get("osy-version"),
            "date": gen.get("osy-date"),
        },
        "dimensions": {
            "years": years,
            "technologies": len(techs),
            "commodities": len(comms),
            "emissions": len(emissions),
            "scenarios": len(scenarios),
            "time_slices": len(gen.get("osy-ts") or []),
            "technology_groups": len(gen.get("osy-techGroups") or []),
            "parameters_found": len(parameters),
        },
        "domain_signals": domains,
        "reference_counts": reference_counts,
        "saved_results": result_statuses,
        "potential_history_fixed_bounds": fixed_matches,
        "findings": findings,
        "screening_warning": (
            "Heuristic inventory only. Spot-check domain detection, saved-result freshness, "
            "and every exact-bound finding before using them in a calibration grade."
        ),
    }


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("model_folder", type=Path)
    parser.add_argument("--output", type=Path, help="write JSON here instead of stdout")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    try:
        report = audit(args.model_folder)
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2
    payload = json.dumps(report, indent=2, ensure_ascii=False) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(payload, encoding="utf-8")
    else:
        print(payload, end="")
    return 1 if any(item["level"] == "fail" for item in report["findings"]) else 0


if __name__ == "__main__":
    raise SystemExit(main())
