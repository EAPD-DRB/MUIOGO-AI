#!/usr/bin/env python3
"""Estimate structural CLEWs/MUIO dimensions before full model generation."""

from __future__ import annotations

import argparse
import csv
import json
import math
import os
import shutil
import sys
from pathlib import Path
from typing import Any


SET_FILES = {
    "regions": "REGION.csv",
    "years": "YEAR.csv",
    "timeslices": "TIMESLICE.csv",
    "technologies": "TECHNOLOGY.csv",
    "commodities": "FUEL.csv",
    "modes": "MODE_OF_OPERATION.csv",
    "emissions": "EMISSION.csv",
    "storage": "STORAGE.csv",
}

LINK_FILES = (
    "InputActivityRatio.csv",
    "OutputActivityRatio.csv",
    "EmissionActivityRatio.csv",
)


def read_rows(path: Path) -> list[dict[str, str]]:
    if not path.is_file() or path.stat().st_size == 0:
        return []
    with path.open(newline="", encoding="utf-8-sig") as handle:
        return list(csv.DictReader(handle))


def set_count(path: Path) -> int:
    rows = read_rows(path)
    if not rows:
        return 0
    column = next(iter(rows[0]))
    return len({row.get(column, "") for row in rows if row.get(column, "")})


def active_pairs(inputs: Path) -> tuple[set[tuple[str, str]], bool]:
    pairs: set[tuple[str, str]] = set()
    for path in inputs.glob("*.csv"):
        rows = read_rows(path)
        if not rows:
            continue
        fields = set(rows[0])
        if {"TECHNOLOGY", "MODE_OF_OPERATION"} <= fields:
            pairs.update(
                (row["TECHNOLOGY"], row["MODE_OF_OPERATION"])
                for row in rows
                if row.get("TECHNOLOGY") and row.get("MODE_OF_OPERATION")
            )
    if pairs:
        return pairs, False

    technology_count = set_count(inputs / SET_FILES["technologies"])
    mode_count = set_count(inputs / SET_FILES["modes"])
    return {
        (f"<technology-{technology}>", f"<mode-{mode}>")
        for technology in range(technology_count)
        for mode in range(mode_count)
    }, True


def link_count(inputs: Path) -> int:
    links: set[tuple[str, ...]] = set()
    for name in LINK_FILES:
        for row in read_rows(inputs / name):
            key = (
                name,
                row.get("REGION", ""),
                row.get("TECHNOLOGY", ""),
                row.get("MODE_OF_OPERATION", ""),
                row.get("FUEL", row.get("EMISSION", "")),
            )
            links.add(key)
    return len(links)


def available_memory_bytes() -> int | None:
    try:
        pages = os.sysconf("SC_PHYS_PAGES")
        page_size = os.sysconf("SC_PAGE_SIZE")
        return int(pages) * int(page_size)
    except (AttributeError, OSError, ValueError):
        return None


def gb(value: float) -> float:
    return round(value / 1_000_000_000, 3)


def main() -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Estimate structural CLEWs/MUIO dimensions. Estimates are ranges, "
            "not formulation-exact guarantees."
        )
    )
    parser.add_argument("inputs", type=Path, help="Complete CLEWs CSV directory")
    parser.add_argument("--output", type=Path, help="Write JSON report")
    parser.add_argument(
        "--available-memory-gb",
        type=float,
        help="Override detected physical memory for traffic-light assessment",
    )
    parser.add_argument(
        "--available-disk-gb",
        type=float,
        help="Override detected free disk for traffic-light assessment",
    )
    parser.add_argument(
        "--generation-seconds-per-million-nonzeros",
        type=float,
        nargs=2,
        metavar=("LOW", "HIGH"),
        default=(5.0, 45.0),
        help="Empirical generation-time range; replace with local benchmarks",
    )
    parser.add_argument(
        "--solve-seconds-per-million-nonzeros",
        type=float,
        nargs=2,
        metavar=("LOW", "HIGH"),
        default=(5.0, 120.0),
        help="Empirical LP solve-time range; replace with local benchmarks",
    )
    args = parser.parse_args()

    inputs = args.inputs.expanduser().resolve()
    if not inputs.is_dir():
        raise SystemExit(f"Input directory does not exist: {inputs}")

    counts = {
        key: set_count(inputs / filename) for key, filename in SET_FILES.items()
    }
    pairs, used_cartesian_fallback = active_pairs(inputs)
    pair_count = len(pairs)
    links = link_count(inputs)

    r = max(counts["regions"], 1)
    y = counts["years"]
    l = counts["timeslices"]
    t = counts["technologies"]
    f = counts["commodities"]
    e = counts["emissions"]
    s = counts["storage"]

    activity = r * y * l * pair_count
    commodity_balance = r * y * l * f
    capacity_time = r * y * l * t
    annual_mode = r * y * pair_count
    annual_technology = r * y * t
    storage_time = r * y * l * s
    emission_annual = r * y * e

    column_base = (
        activity
        + annual_mode
        + 4 * annual_technology
        + 2 * storage_time
    )
    row_base = (
        commodity_balance
        + capacity_time
        + 4 * annual_technology
        + emission_annual
        + storage_time
    )
    average_links = links / pair_count if pair_count else 0.0
    nonzero_base = int(
        activity * max(3.0, 2.0 + average_links)
        + 2 * capacity_time
        + 4 * annual_technology
        + 2 * storage_time
    )

    ranges = {
        "rows": [row_base, math.ceil(row_base * 1.4)],
        "columns": [column_base, math.ceil(column_base * 1.5)],
        "nonzeros": [nonzero_base, math.ceil(nonzero_base * 2.0)],
    }
    matrix_memory = [
        gb(ranges["nonzeros"][0] * 24),
        gb(ranges["nonzeros"][1] * 64),
    ]
    peak_memory = [
        round(
            max(
                0.25,
                matrix_memory[0] * 3
                + (ranges["rows"][0] + ranges["columns"][0]) * 100
                / 1_000_000_000,
            ),
            3,
        ),
        round(
            max(
                0.5,
                matrix_memory[1] * 6
                + (ranges["rows"][1] + ranges["columns"][1]) * 300
                / 1_000_000_000,
            ),
            3,
        ),
    ]
    lp_disk = [
        gb(ranges["nonzeros"][0] * 40),
        gb(ranges["nonzeros"][1] * 90),
    ]
    working_disk = [
        round(lp_disk[0] * 2.0, 3),
        round(lp_disk[1] * 3.5, 3),
    ]
    generation_runtime = [
        round(
            ranges["nonzeros"][0]
            / 1_000_000
            * args.generation_seconds_per_million_nonzeros[0],
            1,
        ),
        round(
            ranges["nonzeros"][1]
            / 1_000_000
            * args.generation_seconds_per_million_nonzeros[1],
            1,
        ),
    ]
    solve_runtime = [
        round(
            ranges["nonzeros"][0]
            / 1_000_000
            * args.solve_seconds_per_million_nonzeros[0],
            1,
        ),
        round(
            ranges["nonzeros"][1]
            / 1_000_000
            * args.solve_seconds_per_million_nonzeros[1],
            1,
        ),
    ]

    detected_memory = available_memory_bytes()
    available_memory_gb = (
        args.available_memory_gb
        if args.available_memory_gb is not None
        else (gb(detected_memory) if detected_memory else None)
    )
    detected_disk = shutil.disk_usage(inputs).free
    available_disk_gb = (
        args.available_disk_gb
        if args.available_disk_gb is not None
        else gb(detected_disk)
    )

    ratios: list[float] = []
    if available_memory_gb:
        ratios.append(peak_memory[1] / available_memory_gb)
    if available_disk_gb:
        ratios.append(working_disk[1] / available_disk_gb)
    maximum_ratio = max(ratios, default=0.0)
    if maximum_ratio > 0.8:
        traffic_light = "red"
    elif maximum_ratio >= 0.5 or solve_runtime[1] > 3600:
        traffic_light = "amber"
    else:
        traffic_light = "green"

    warnings: list[str] = []
    if used_cartesian_fallback:
        warnings.append(
            "No explicit technology-mode associations were found; used the "
            "full technology × mode Cartesian product."
        )
    if not y or not l or not t or not f:
        warnings.append("One or more core sets are empty; estimate is incomplete.")

    report: dict[str, Any] = {
        "inputs": str(inputs),
        "traffic_light": traffic_light,
        "sets": counts,
        "active_technology_mode_pairs": pair_count,
        "technology_mode_cartesian_fallback": used_cartesian_fallback,
        "unique_source_links": links,
        "structural_combinations": {
            "time_resolved_activity": activity,
            "commodity_balance": commodity_balance,
            "capacity_time": capacity_time,
            "annual_mode": annual_mode,
            "storage_time": storage_time,
        },
        "estimated_matrix": ranges,
        "estimated_matrix_memory_gb": matrix_memory,
        "estimated_peak_memory_gb": peak_memory,
        "estimated_lp_disk_gb": lp_disk,
        "estimated_working_disk_gb": working_disk,
        "estimated_generation_seconds": generation_runtime,
        "estimated_solve_seconds": solve_runtime,
        "available_memory_gb": available_memory_gb,
        "available_disk_gb": available_disk_gb,
        "assumptions": {
            "matrix_bytes_per_nonzero": [24, 64],
            "peak_memory_multiplier_over_matrix": [3, 6],
            "row_column_overhead_bytes": [100, 300],
            "lp_bytes_per_nonzero": [40, 90],
            "row_range_factor": [1.0, 1.4],
            "column_range_factor": [1.0, 1.5],
            "nonzero_range_factor": [1.0, 2.0],
            "generation_seconds_per_million_nonzeros": list(
                args.generation_seconds_per_million_nonzeros
            ),
            "solve_seconds_per_million_nonzeros": list(
                args.solve_seconds_per_million_nonzeros
            ),
        },
        "actual": {
            "rows": None,
            "columns": None,
            "nonzeros": None,
            "lp_disk_gb": None,
            "working_disk_gb": None,
            "generation_seconds": None,
            "solve_seconds": None,
        },
        "warnings": warnings,
    }

    rendered = json.dumps(report, indent=2)
    if args.output:
        output = args.output.expanduser().resolve()
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(rendered + "\n", encoding="utf-8")
    print(rendered)
    return 2 if traffic_light == "red" else 0


if __name__ == "__main__":
    sys.exit(main())
