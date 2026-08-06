#!/usr/bin/env python3
"""Estimate Fisheries effective residual capacity and retirement series."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import sys
from pathlib import Path


REQUIRED_COLUMNS = {
    "technology",
    "base_year",
    "end_year",
    "observed_useful_service",
    "service_unit",
    "capacity_to_activity_unit",
    "model_capacity_unit",
    "historical_utilization",
    "operating_life",
    "remaining_life",
    "retirement_method",
    "source_ids",
    "calculation_id",
}

METHODS = {"uniform_age", "linear_remaining_life", "fixed_until_retirement"}


def parse_float(row: dict[str, str], field: str, technology: str) -> float:
    try:
        value = float(row[field])
    except (KeyError, ValueError) as exc:
        raise ValueError(f"{technology}: {field} must be numeric") from exc
    if not math.isfinite(value):
        raise ValueError(f"{technology}: {field} must be finite")
    return value


def parse_int(row: dict[str, str], field: str, technology: str) -> int:
    value = parse_float(row, field, technology)
    if value != int(value):
        raise ValueError(f"{technology}: {field} must be an integer")
    return int(value)


def capacity_at_year(
    base_capacity: float,
    year: int,
    base_year: int,
    operating_life: int,
    remaining_life: int,
    method: str,
) -> float:
    offset = year - base_year
    if offset < 0:
        raise ValueError("year cannot precede base_year")
    if method == "uniform_age":
        return base_capacity * max(0.0, 1.0 - offset / operating_life)
    if method == "linear_remaining_life":
        return base_capacity * max(0.0, 1.0 - offset / remaining_life)
    if method == "fixed_until_retirement":
        return base_capacity if offset < remaining_life else 0.0
    raise ValueError(f"unsupported retirement method: {method}")


def estimate(input_path: Path, precision: int) -> tuple[list[dict[str, str]], dict[str, object]]:
    with input_path.open(newline="", encoding="utf-8-sig") as handle:
        reader = csv.DictReader(handle)
        headers = set(reader.fieldnames or [])
        missing = REQUIRED_COLUMNS - headers
        if missing:
            raise ValueError(f"missing input columns: {', '.join(sorted(missing))}")
        source_rows = [
            {key: (value or "").strip() for key, value in row.items() if key is not None}
            for row in reader
        ]

    if not source_rows:
        raise ValueError("input contains no data rows")

    output: list[dict[str, str]] = []
    technology_summaries: list[dict[str, object]] = []
    seen_technologies: set[str] = set()

    for row in source_rows:
        technology = row.get("technology", "") or "<unnamed>"
        base_year = parse_int(row, "base_year", technology)
        end_year = parse_int(row, "end_year", technology)
        service = parse_float(row, "observed_useful_service", technology)
        cau = parse_float(row, "capacity_to_activity_unit", technology)
        utilization = parse_float(row, "historical_utilization", technology)
        operating_life = parse_int(row, "operating_life", technology)
        method = row.get("retirement_method", "")
        remaining_life = (
            operating_life
            if not row.get("remaining_life", "")
            else parse_int(row, "remaining_life", technology)
        )

        if not row.get("technology"):
            raise ValueError("technology must not be blank")
        if technology in seen_technologies:
            raise ValueError(f"{technology}: duplicate technology row")
        seen_technologies.add(technology)
        if not row.get("service_unit"):
            raise ValueError(f"{technology}: service_unit must not be blank")
        if not row.get("model_capacity_unit"):
            raise ValueError(f"{technology}: model_capacity_unit must not be blank")
        if end_year < base_year:
            raise ValueError(f"{technology}: end_year precedes base_year")
        if service < 0:
            raise ValueError(f"{technology}: observed_useful_service cannot be negative")
        if cau <= 0:
            raise ValueError(f"{technology}: capacity_to_activity_unit must be positive")
        if utilization <= 0 or utilization > 1:
            raise ValueError(
                f"{technology}: historical_utilization must be greater than 0 and at most 1"
            )
        if operating_life <= 0 or remaining_life <= 0:
            raise ValueError(f"{technology}: life values must be positive")
        if remaining_life > operating_life:
            raise ValueError(f"{technology}: remaining_life cannot exceed operating_life")
        if method not in METHODS:
            raise ValueError(
                f"{technology}: retirement_method must be one of {', '.join(sorted(METHODS))}"
            )
        if not row.get("source_ids"):
            raise ValueError(f"{technology}: source_ids must not be blank")
        if not row.get("calculation_id"):
            raise ValueError(f"{technology}: calculation_id must not be blank")

        base_capacity = service / (cau * utilization)
        formula = (
            f"{service:.{precision}g}/"
            f"({cau:.{precision}g}*{utilization:.{precision}g})"
        )
        for year in range(base_year, end_year + 1):
            capacity = capacity_at_year(
                base_capacity,
                year,
                base_year,
                operating_life,
                remaining_life,
                method,
            )
            output.append(
                {
                    "technology": technology,
                    "year": str(year),
                    "residual_capacity": f"{capacity:.{precision}g}",
                    "model_capacity_unit": row.get("model_capacity_unit", ""),
                    "retirement_method": method,
                    "base_capacity_formula": formula,
                    "source_ids": row.get("source_ids", ""),
                    "calculation_id": row.get("calculation_id", ""),
                    "notes": row.get("notes", ""),
                }
            )

        technology_summaries.append(
            {
                "technology": technology,
                "base_capacity": base_capacity,
                "model_capacity_unit": row.get("model_capacity_unit", ""),
                "retirement_method": method,
                "last_nonzero_year": max(
                    (
                        year
                        for year in range(base_year, end_year + 1)
                        if capacity_at_year(
                            base_capacity,
                            year,
                            base_year,
                            operating_life,
                            remaining_life,
                            method,
                        )
                        > 0
                    ),
                    default=None,
                ),
            }
        )

    # Recorded so the output can be traced to the exact input it came from.
    # This is lineage, not a gate: nothing here verifies it.
    digest = hashlib.sha256(input_path.read_bytes()).hexdigest()
    summary: dict[str, object] = {
        "status": "pass",
        "input": str(input_path.resolve()),
        "input_sha256": digest,
        "technology_count": len(source_rows),
        "output_row_count": len(output),
        "technologies": technology_summaries,
    }
    return output, summary


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Estimate effective Fisheries residual capacity from observed useful "
            "service and produce a documented retirement series."
        )
    )
    parser.add_argument("input_csv")
    parser.add_argument("output_csv")
    parser.add_argument("--summary", help="Optional JSON summary path")
    parser.add_argument("--precision", type=int, default=12)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if args.precision < 3 or args.precision > 17:
        print("error: precision must be between 3 and 17", file=sys.stderr)
        return 2

    try:
        rows, summary = estimate(Path(args.input_csv), args.precision)
    except (OSError, ValueError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1

    output_path = Path(args.output_csv)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = [
        "technology",
        "year",
        "residual_capacity",
        "model_capacity_unit",
        "retirement_method",
        "base_capacity_formula",
        "source_ids",
        "calculation_id",
        "notes",
    ]
    with output_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    rendered = json.dumps(summary, indent=2, sort_keys=True)
    if args.summary:
        Path(args.summary).write_text(rendered + "\n", encoding="utf-8")
    print(rendered)
    return 0


if __name__ == "__main__":
    sys.exit(main())
