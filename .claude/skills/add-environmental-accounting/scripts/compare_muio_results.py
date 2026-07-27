#!/usr/bin/env python3
"""Compare MUIO result trees while excluding explicitly new account rows."""

from __future__ import annotations

import argparse
import csv
import json
import math
import re
from collections import defaultdict
from pathlib import Path
from typing import Any


def read_csv(path: Path) -> tuple[list[str], list[list[str]]]:
    with path.open(newline="", encoding="utf-8-sig") as handle:
        rows = list(csv.reader(handle))
    return (rows[0], rows[1:]) if rows else ([], [])


def excluded(
    row: list[str],
    header: list[str],
    exclusions: list[tuple[str, str]],
    tokens: list[str],
) -> bool:
    by_column = dict(zip(header, row))
    return any(by_column.get(column) == value for column, value in exclusions) or any(
        token in cell for token in tokens for cell in row
    )


def records(
    rows: list[list[str]],
    header: list[str],
    value_index: int,
    exclusions: list[tuple[str, str]],
    ignored_tokens: list[str],
) -> dict[tuple[str, ...], list[float]]:
    result: dict[tuple[str, ...], list[float]] = defaultdict(list)
    for row in rows:
        if excluded(row, header, exclusions, ignored_tokens):
            continue
        try:
            value = float(row[value_index])
        except (ValueError, IndexError):
            continue
        if not math.isfinite(value):
            raise ValueError(f"non-finite result value in row: {row}")
        key = tuple(cell for index, cell in enumerate(row) if index != value_index)
        result[key].append(value)
    return dict(result)


def discover_cases(root: Path) -> set[str]:
    if (root / "csv").is_dir():
        return {"."}
    return {path.parent.name for path in root.glob("*/csv") if path.is_dir()}


def case_folder(root: Path, case: str) -> Path:
    return root if case == "." else root / case


def solver_status(root: Path, case: str, optimal_pattern: re.Pattern[str]) -> dict[str, Any]:
    path = case_folder(root, case) / "results.txt"
    if not path.exists():
        return {"status": "missing", "first_line": ""}
    first_line = path.open(encoding="utf-8-sig", errors="replace").readline().strip()
    return {
        "status": "optimal" if optimal_pattern.search(first_line) else "non-optimal",
        "first_line": first_line,
    }


def compare(
    baseline: Path,
    candidate: Path,
    exclusions: list[tuple[str, str]],
    ignored_tokens: list[str],
    absolute_tolerance: float,
    relative_tolerance: float,
    tolerance_map: dict[str, dict[str, float]],
    optimal_pattern: re.Pattern[str],
    expected_cases: set[str],
) -> dict[str, Any]:
    baseline_cases = discover_cases(baseline)
    candidate_cases = discover_cases(candidate)
    if not baseline_cases or not candidate_cases:
        raise ValueError("no result cases with csv folders were discovered")
    required_cases = expected_cases or (baseline_cases | candidate_cases)
    report: dict[str, Any] = {
        "baseline": str(baseline),
        "candidate": str(candidate),
        "absolute_tolerance": absolute_tolerance,
        "relative_tolerance": relative_tolerance,
        "exclusions": [f"{column}={value}" for column, value in exclusions],
        "ignored_tokens": ignored_tokens,
        "missing_cases": sorted(
            (required_cases - baseline_cases) | (required_cases - candidate_cases)
        ),
        "cases": {},
    }

    for case in sorted(baseline_cases & candidate_cases):
        baseline_case = case_folder(baseline, case)
        candidate_case = case_folder(candidate, case)
        baseline_csv = baseline_case / "csv"
        candidate_csv = candidate_case / "csv"
        baseline_files = {path.name: path for path in baseline_csv.glob("*.csv")}
        candidate_files = {path.name: path for path in candidate_csv.glob("*.csv")}
        case_report: dict[str, Any] = {
            "baseline_solver": solver_status(baseline, case, optimal_pattern),
            "candidate_solver": solver_status(candidate, case, optimal_pattern),
            "missing_files": sorted(set(baseline_files) ^ set(candidate_files)),
            "variables": {},
        }

        for filename in sorted(set(baseline_files) & set(candidate_files)):
            stem = Path(filename).stem
            baseline_header, baseline_rows = read_csv(baseline_files[filename])
            candidate_header, candidate_rows = read_csv(candidate_files[filename])
            if baseline_header != candidate_header:
                case_report["variables"][stem] = {
                    "status": "header-mismatch",
                    "baseline_header": baseline_header,
                    "candidate_header": candidate_header,
                }
                continue
            if stem not in baseline_header:
                case_report["variables"][stem] = {
                    "status": "unverified-no-named-value-column"
                }
                continue
            value_index = baseline_header.index(stem)
            old = records(
                baseline_rows, baseline_header, value_index, exclusions, ignored_tokens
            )
            new = records(
                candidate_rows, candidate_header, value_index, exclusions, ignored_tokens
            )
            applied = tolerance_map.get(stem, {})
            variable_absolute_tolerance = float(
                applied.get("absolute", absolute_tolerance)
            )
            variable_relative_tolerance = float(
                applied.get("relative", relative_tolerance)
            )
            old_keys, new_keys = set(old), set(new)
            shared = old_keys & new_keys
            maximum_absolute = 0.0
            maximum_relative = 0.0
            changed = 0
            duplicate_keys = sum(len(values) > 1 for values in old.values()) + sum(
                len(values) > 1 for values in new.values()
            )
            multiplicity_mismatches = 0
            examples = []
            for key in sorted(shared):
                old_values = sorted(old[key])
                new_values = sorted(new[key])
                if len(old_values) != len(new_values):
                    multiplicity_mismatches += 1
                    if len(examples) < 5:
                        examples.append(
                            {
                                "key": key,
                                "baseline_values": old_values,
                                "candidate_values": new_values,
                            }
                        )
                    continue
                for old_value, new_value in zip(old_values, new_values):
                    absolute = abs(new_value - old_value)
                    scale = max(abs(old_value), abs(new_value))
                    relative = absolute / scale if scale else 0.0
                    maximum_absolute = max(maximum_absolute, absolute)
                    maximum_relative = max(maximum_relative, relative)
                    if not math.isclose(
                        old_value,
                        new_value,
                        abs_tol=variable_absolute_tolerance,
                        rel_tol=variable_relative_tolerance,
                    ):
                        changed += 1
                        if len(examples) < 5:
                            examples.append(
                                {
                                    "key": key,
                                    "baseline": old_value,
                                    "candidate": new_value,
                                    "absolute_difference": absolute,
                                    "relative_difference": relative,
                                }
                            )

            status = "same"
            if duplicate_keys:
                status = "duplicate-dimension-key"
            elif old_keys != new_keys or multiplicity_mismatches:
                status = "row-set-difference"
            elif changed:
                status = "numeric-difference"
            case_report["variables"][stem] = {
                "status": status,
                "baseline_rows": sum(map(len, old.values())),
                "candidate_rows": sum(map(len, new.values())),
                "baseline_only_keys": len(old_keys - new_keys),
                "candidate_only_keys": len(new_keys - old_keys),
                "multiplicity_mismatches": multiplicity_mismatches,
                "duplicate_keys": duplicate_keys,
                "applied_tolerance": {
                    "absolute": variable_absolute_tolerance,
                    "relative": variable_relative_tolerance,
                },
                "max_absolute_difference": maximum_absolute,
                "max_relative_difference": maximum_relative,
                "count_outside_tolerance": changed,
                "examples": examples,
            }
        report["cases"][case] = case_report
    return report


def print_report(report: dict[str, Any]) -> None:
    print(f"BASELINE:  {report['baseline']}")
    print(f"CANDIDATE: {report['candidate']}")
    print(
        f"TOLERANCE: abs={report['absolute_tolerance']} "
        f"rel={report['relative_tolerance']}"
    )
    if report["missing_cases"]:
        print("MISSING CASES:", ", ".join(report["missing_cases"]))
    for case, case_report in report["cases"].items():
        print(f"\nCASE: {case}")
        print(
            "  solver: "
            f"baseline={case_report['baseline_solver']['status']} "
            f"candidate={case_report['candidate_solver']['status']}"
        )
        if case_report["missing_files"]:
            print("  missing files:", ", ".join(case_report["missing_files"]))
        changed = 0
        for variable, result in case_report["variables"].items():
            if result["status"] == "same":
                continue
            changed += 1
            if "max_absolute_difference" in result:
                print(
                    f"  {variable}: {result['status']} "
                    f"max_abs={result['max_absolute_difference']:.12g} "
                    f"max_rel={result['max_relative_difference']:.12g} "
                    f"outside={result['count_outside_tolerance']} "
                    f"keys(-/+)={result['baseline_only_keys']}/"
                    f"{result['candidate_only_keys']} "
                    f"duplicates={result['duplicate_keys']} "
                    f"tolerance={result['applied_tolerance']}"
                )
                for example in result["examples"][:2]:
                    print(f"    example: {example}")
            else:
                print(f"  {variable}: {result['status']}")
        if not changed and not case_report["missing_files"]:
            print("  all comparable pre-existing rows match")


def has_differences(report: dict[str, Any]) -> bool:
    if report["missing_cases"]:
        return True
    for case in report["cases"].values():
        if case["missing_files"]:
            return True
        if case["baseline_solver"]["status"] != "optimal":
            return True
        if case["candidate_solver"]["status"] != "optimal":
            return True
        if any(result["status"] != "same" for result in case["variables"].values()):
            return True
    return False


def finite_nonnegative(parser: argparse.ArgumentParser, name: str, value: float) -> None:
    if not math.isfinite(value) or value < 0:
        parser.error(f"{name} must be a finite nonnegative number")


def parse_exclusion(parser: argparse.ArgumentParser, value: str) -> tuple[str, str]:
    if "=" not in value:
        parser.error("--exclude must use COLUMN=VALUE")
    column, expected = value.split("=", 1)
    if not column or not expected:
        parser.error("--exclude must use nonempty COLUMN=VALUE")
    return column, expected


def load_tolerance_map(parser: argparse.ArgumentParser, path: Path | None) -> dict[str, dict[str, float]]:
    if path is None:
        return {}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        parser.error(f"cannot read --tolerance-map: {error}")
    if not isinstance(data, dict):
        parser.error("--tolerance-map must contain a JSON object")
    for variable, rule in data.items():
        if not isinstance(rule, dict):
            parser.error(f"tolerance rule for {variable} must be an object")
        for kind in ("absolute", "relative"):
            if kind in rule:
                try:
                    finite_nonnegative(parser, f"{variable}.{kind}", float(rule[kind]))
                except (TypeError, ValueError):
                    parser.error(f"{variable}.{kind} must be numeric")
    return data


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("baseline", type=Path, help="baseline res folder")
    parser.add_argument("candidate", type=Path, help="candidate res folder")
    parser.add_argument(
        "--exclude",
        action="append",
        default=[],
        help="exclude rows with exact COLUMN=VALUE; repeat as needed",
    )
    parser.add_argument(
        "--ignore-token",
        action="append",
        default=[],
        help="exclude rows containing this substring; use only when exact values cannot work",
    )
    parser.add_argument("--absolute-tolerance", type=float, default=1e-6)
    parser.add_argument("--relative-tolerance", type=float, default=0.0)
    parser.add_argument(
        "--tolerance-map",
        type=Path,
        help='JSON mapping variable names to {"absolute": n, "relative": n}',
    )
    parser.add_argument(
        "--optimal-pattern",
        default=r"(?i)^optimal\b",
        help="regular expression matching an optimal solver-status first line",
    )
    parser.add_argument(
        "--expected-case",
        action="append",
        default=[],
        help="required result case name; repeat as needed",
    )
    parser.add_argument("--json", action="store_true", help="emit JSON")
    args = parser.parse_args()

    finite_nonnegative(parser, "--absolute-tolerance", args.absolute_tolerance)
    finite_nonnegative(parser, "--relative-tolerance", args.relative_tolerance)
    for root in (args.baseline, args.candidate):
        if not root.is_dir():
            parser.error(f"result folder not found: {root}")

    exclusions = [parse_exclusion(parser, value) for value in args.exclude]
    tolerance_map = load_tolerance_map(parser, args.tolerance_map)
    try:
        optimal_pattern = re.compile(args.optimal_pattern)
    except re.error as error:
        parser.error(f"invalid --optimal-pattern: {error}")
    try:
        report = compare(
            args.baseline.resolve(),
            args.candidate.resolve(),
            exclusions,
            args.ignore_token,
            args.absolute_tolerance,
            args.relative_tolerance,
            tolerance_map,
            optimal_pattern,
            set(args.expected_case),
        )
    except ValueError as error:
        parser.error(str(error))
    if args.json:
        print(json.dumps(report, indent=2))
    else:
        print_report(report)
    return 1 if has_differences(report) else 0


if __name__ == "__main__":
    raise SystemExit(main())
