#!/usr/bin/env python3
"""Screen a MUIO model for Fisheries activity and investment forcing."""

from __future__ import annotations

import argparse
import json
import math
import re
import sys
from pathlib import Path
from typing import Any, Iterable


def load_json(path: Path) -> Any:
    with path.open(encoding="utf-8") as handle:
        return json.load(handle)


def is_number(value: Any) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(value)


def tech_metadata(gen_data: Any) -> dict[str, dict[str, str]]:
    metadata: dict[str, dict[str, str]] = {}

    def visit(value: Any) -> None:
        if isinstance(value, dict):
            tech_id = value.get("TechId")
            if isinstance(tech_id, str):
                metadata.setdefault(
                    tech_id,
                    {
                        "TechId": tech_id,
                        "Tech": str(value.get("Tech", "")),
                        "Desc": str(value.get("Desc", "")),
                    },
                )
            for child in value.values():
                visit(child)
        elif isinstance(value, list):
            for child in value:
                visit(child)

    visit(gen_data)
    return metadata


def parameter_records(ryt: dict[str, Any], parameter: str) -> dict[tuple[str, str], dict[str, Any]]:
    records: dict[tuple[str, str], dict[str, Any]] = {}
    scenarios = ryt.get(parameter, {})
    if not isinstance(scenarios, dict):
        return records
    for scenario, rows in scenarios.items():
        if not isinstance(rows, list):
            continue
        for row in rows:
            if isinstance(row, dict) and isinstance(row.get("TechId"), str):
                records[(str(scenario), row["TechId"])] = row
    return records


def year_values(record: dict[str, Any] | None) -> Iterable[tuple[str, float]]:
    if not record:
        return []
    return [
        (str(year), float(value))
        for year, value in record.items()
        if year != "TechId" and is_number(value)
    ]


def allow_key(allowlist: set[str], tech_id: str, year: str) -> bool:
    return tech_id in allowlist or f"{tech_id}:{year}" in allowlist


def add_finding(
    findings: list[dict[str, Any]],
    level: str,
    code: str,
    message: str,
    **evidence: Any,
) -> None:
    findings.append(
        {
            "level": level,
            "code": code,
            "message": message,
            "evidence": evidence,
        }
    )


def scan_udc_files(
    model_folder: Path,
    tech_ids: set[str],
    allow_udc: set[str],
    findings: list[dict[str, Any]],
) -> None:
    def visit(value: Any, path: list[str], filename: str) -> None:
        if isinstance(value, dict):
            tech_id = value.get("TechId")
            if tech_id in tech_ids and tech_id not in allow_udc:
                nonzero = {
                    str(key): number
                    for key, number in value.items()
                    if key != "TechId" and is_number(number) and float(number) != 0
                }
                if nonzero:
                    add_finding(
                        findings,
                        "error",
                        "fisheries_udc_coefficient",
                        "Fisheries technology has a nonzero user-constraint coefficient",
                        file=filename,
                        path="/".join(path),
                        technology=tech_id,
                        values=nonzero,
                    )
            for key, child in value.items():
                visit(child, path + [str(key)], filename)
        elif isinstance(value, list):
            for index, child in enumerate(value):
                visit(child, path + [str(index)], filename)

    for path in sorted(model_folder.glob("*Cn.json")):
        try:
            visit(load_json(path), [], path.name)
        except (OSError, json.JSONDecodeError) as exc:
            add_finding(
                findings,
                "error",
                "invalid_constraint_json",
                "Could not inspect constraint JSON",
                file=path.name,
                error=str(exc),
            )


def audit(args: argparse.Namespace) -> dict[str, Any]:
    model_folder = Path(args.model_folder).resolve()
    findings: list[dict[str, Any]] = []
    gen_path = model_folder / "genData.json"
    ryt_path = model_folder / "RYT.json"

    if not gen_path.is_file() or not ryt_path.is_file():
        missing = [str(path) for path in (gen_path, ryt_path) if not path.is_file()]
        return {
            "status": "fail",
            "model_folder": str(model_folder),
            "technology_ids": [],
            "findings": [
                {
                    "level": "error",
                    "code": "missing_model_files",
                    "message": "Required MUIO files are missing",
                    "evidence": {"files": missing},
                }
            ],
        }

    try:
        gen_data = load_json(gen_path)
        ryt = load_json(ryt_path)
    except (OSError, json.JSONDecodeError) as exc:
        return {
            "status": "fail",
            "model_folder": str(model_folder),
            "technology_ids": [],
            "findings": [
                {
                    "level": "error",
                    "code": "invalid_model_json",
                    "message": str(exc),
                    "evidence": {},
                }
            ],
        }

    pattern = re.compile(args.technology_pattern, re.IGNORECASE)
    metadata = tech_metadata(gen_data)
    tech_ids = {
        tech_id
        for tech_id, item in metadata.items()
        if pattern.search(" ".join((tech_id, item["Tech"], item["Desc"])))
    }

    for parameter_value in ryt.values():
        if not isinstance(parameter_value, dict):
            continue
        for records in parameter_value.values():
            if not isinstance(records, list):
                continue
            for row in records:
                tech_id = row.get("TechId") if isinstance(row, dict) else None
                if isinstance(tech_id, str) and pattern.search(tech_id):
                    tech_ids.add(tech_id)

    if not tech_ids:
        add_finding(
            findings,
            "error",
            "no_fisheries_technologies",
            "No Fisheries technologies matched the configured pattern",
            pattern=args.technology_pattern,
        )

    allow_exact = set(args.allow_exact)
    allow_investment = set(args.allow_investment)
    allow_udc = set(args.allow_udc)

    activity_lower = parameter_records(ryt, "TAL")
    activity_upper = parameter_records(ryt, "TAU")
    capacity_lower = parameter_records(ryt, "TAMinC")
    capacity_upper = parameter_records(ryt, "TAMaxC")
    investment_lower = parameter_records(ryt, "TAMinCI")
    investment_upper = parameter_records(ryt, "TAMaxCI")
    residual_capacity = parameter_records(ryt, "RC")
    availability = parameter_records(ryt, "AF")

    for scenario in sorted(
        {scenario for parameter in ryt.values() if isinstance(parameter, dict) for scenario in parameter}
    ):
        for tech_id in sorted(tech_ids):
            for kind, lower_records, upper_records in (
                ("annual_activity", activity_lower, activity_upper),
                ("annual_capacity", capacity_lower, capacity_upper),
            ):
                lower = dict(year_values(lower_records.get((scenario, tech_id))))
                upper = dict(year_values(upper_records.get((scenario, tech_id))))
                for year in sorted(set(lower) & set(upper)):
                    if lower[year] == upper[year] and not allow_key(allow_exact, tech_id, year):
                        add_finding(
                            findings,
                            "error",
                            "exact_lower_upper_bound",
                            f"Fisheries {kind} is fixed by equal lower and upper bounds",
                            scenario=scenario,
                            technology=tech_id,
                            year=year,
                            value=lower[year],
                        )

            for year, value in year_values(activity_lower.get((scenario, tech_id))):
                if value > 0 and not allow_key(allow_exact, tech_id, year):
                    add_finding(
                        findings,
                        "error",
                        "positive_activity_minimum",
                        "Fisheries technology has a positive annual activity minimum",
                        scenario=scenario,
                        technology=tech_id,
                        year=year,
                        value=value,
                    )

            for year, value in year_values(investment_lower.get((scenario, tech_id))):
                if value > 0 and not allow_key(allow_investment, tech_id, year):
                    add_finding(
                        findings,
                        "error",
                        "positive_investment_minimum",
                        "Fisheries technology has a positive minimum capacity investment",
                        scenario=scenario,
                        technology=tech_id,
                        year=year,
                        value=value,
                    )

            max_investment = dict(
                year_values(investment_upper.get((scenario, tech_id)))
            )
            for year, value in max_investment.items():
                if value == 0 and not allow_key(allow_investment, tech_id, year):
                    add_finding(
                        findings,
                        "error",
                        "zero_investment_maximum",
                        "Fisheries technology investment is prohibited",
                        scenario=scenario,
                        technology=tech_id,
                        year=year,
                        value=value,
                    )
                elif 0 < value < args.open_upper_threshold:
                    add_finding(
                        findings,
                        "warning",
                        "finite_investment_maximum",
                        "Finite Fisheries investment maximum requires independent provenance",
                        scenario=scenario,
                        technology=tech_id,
                        year=year,
                        value=value,
                    )

            ordered_investment = sorted(max_investment.items(), key=lambda item: item[0])
            if any(value == 0 for _, value in ordered_investment) and any(
                value > 0 for _, value in ordered_investment
            ):
                first_open = next(
                    (year for year, value in ordered_investment if value > 0), None
                )
                earlier_zero = any(
                    value == 0 and year < str(first_open)
                    for year, value in ordered_investment
                    if first_open is not None
                )
                if earlier_zero:
                    add_finding(
                        findings,
                        "error",
                        "staged_investment_opening",
                        "Fisheries investment is zero in early years and opens later",
                        scenario=scenario,
                        technology=tech_id,
                        first_open_year=first_open,
                    )

            for year, value in year_values(availability.get((scenario, tech_id))):
                if 0 < value < args.low_availability_threshold:
                    add_finding(
                        findings,
                        "warning",
                        "low_availability",
                        "Low Fisheries availability may encode historical utilization",
                        scenario=scenario,
                        technology=tech_id,
                        year=year,
                        value=value,
                    )

    positive_rc_techs = sorted(
        {
            tech_id
            for (_, tech_id), record in residual_capacity.items()
            if tech_id in tech_ids and any(value > 0 for _, value in year_values(record))
        }
    )
    zero_rc_techs = sorted(tech_ids - set(positive_rc_techs))
    if zero_rc_techs:
        add_finding(
            findings,
            "warning",
            "no_positive_residual_capacity",
            "Confirm whether these Fisheries technologies had no pre-base-year stock",
            technologies=zero_rc_techs,
        )

    scan_udc_files(model_folder, tech_ids, allow_udc, findings)

    error_count = sum(item["level"] == "error" for item in findings)
    warning_count = sum(item["level"] == "warning" for item in findings)
    return {
        "status": "pass" if error_count == 0 else "fail",
        "model_folder": str(model_folder),
        "technology_pattern": args.technology_pattern,
        "technology_ids": sorted(tech_ids),
        "technology_metadata": {
            tech_id: metadata.get(tech_id, {"TechId": tech_id, "Tech": "", "Desc": ""})
            for tech_id in sorted(tech_ids)
        },
        "residual_capacity": {
            "positive_technology_ids": positive_rc_techs,
            "zero_or_missing_technology_ids": zero_rc_techs,
        },
        "summary": {
            "errors": error_count,
            "warnings": warning_count,
            "findings": len(findings),
        },
        "findings": findings,
        "screening_warning": (
            "This is a structural screening tool. Review every finite physical "
            "limit and all reported UDC references against the provenance registers."
        ),
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Screen a MUIO model for Fisheries activity and investment forcing."
    )
    parser.add_argument("model_folder")
    parser.add_argument(
        "--technology-pattern",
        default=r"(?:^|_)FSH(?:_|$)|FISH",
        help="Case-insensitive regular expression for Fisheries technologies",
    )
    parser.add_argument(
        "--allow-exact",
        action="append",
        default=[],
        metavar="TECH[:YEAR]",
        help="Allow one independently justified exact activity/capacity bound",
    )
    parser.add_argument(
        "--allow-investment",
        action="append",
        default=[],
        metavar="TECH[:YEAR]",
        help="Allow one independently justified investment limit",
    )
    parser.add_argument(
        "--allow-udc",
        action="append",
        default=[],
        metavar="TECH",
        help="Allow one independently justified Fisheries UDC technology reference",
    )
    parser.add_argument("--open-upper-threshold", type=float, default=999999.0)
    parser.add_argument("--low-availability-threshold", type=float, default=0.2)
    parser.add_argument("--output", help="Optional JSON report path")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    report = audit(args)
    rendered = json.dumps(report, indent=2, sort_keys=True)
    if args.output:
        Path(args.output).write_text(rendered + "\n", encoding="utf-8")
    print(rendered)
    return 0 if report["status"] == "pass" else 1


if __name__ == "__main__":
    sys.exit(main())
