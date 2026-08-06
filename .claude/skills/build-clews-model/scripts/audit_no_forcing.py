#!/usr/bin/env python3
"""Audit a raw CLEWs build for common historical-forcing patterns."""

from __future__ import annotations

import argparse
import csv
import json
import math
import sys
from pathlib import Path
from typing import Any

HARD_FORCING_CONFIG_KEYS = {
    "historical_generation_shares",
    "historical_availability_factors",
    "power_capacity_calibration",
    "power_capacity_calibration_gw",
    "capacity_calibration",
    "calibrated_capacity",
}

FITTED_FACTOR_CONFIG_KEYS = {
    "crop_yield_factors",
    "yield_calibration_factors",
    "water_calibration_factors",
}

POLICY_OR_BOUND_CONFIG_KEYS = {
    "emission_limit",
    "emission_penalty",
    "fossil_capacity_targets",
    "max_availability_factors",
    "min_generation_factors",
    "re_targets",
    "reserve_margin",
    "user_defined_capacity",
    "user_defined_capacity_storage",
    "user_defined_capacity_transmission",
}

PAIR_CHECKS = (
    (
        "TotalTechnologyAnnualActivityLowerLimit.csv",
        "TotalTechnologyAnnualActivityUpperLimit.csv",
        "historical activity lock",
    ),
    (
        "TechnologyActivityByModeLowerLimit.csv",
        "TechnologyActivityByModeUpperLimit.csv",
        "historical activity-by-mode lock",
    ),
    (
        "TotalAnnualMinCapacity.csv",
        "TotalAnnualMaxCapacity.csv",
        "capacity lock",
    ),
    (
        "TotalAnnualMinCapacityInvestment.csv",
        "TotalAnnualMaxCapacityInvestment.csv",
        "capacity-investment lock",
    ),
)

REFERENCE_PARAMETERS = (
    "AvailabilityFactor.csv",
    "CapacityFactor.csv",
    "CapitalCost.csv",
    "EmissionActivityRatio.csv",
    "FixedCost.csv",
    "InputActivityRatio.csv",
    "OutputActivityRatio.csv",
    "ResidualCapacity.csv",
    "SpecifiedAnnualDemand.csv",
    "SpecifiedDemandProfile.csv",
    "VariableCost.csv",
)


def is_populated(value: Any) -> bool:
    if value is None or value is False:
        return False
    if isinstance(value, (list, tuple, dict, set, str)):
        return len(value) > 0
    return True


def contains_nonunity_number(value: Any) -> bool:
    if isinstance(value, dict):
        return any(contains_nonunity_number(item) for item in value.values())
    if isinstance(value, (list, tuple)):
        return any(contains_nonunity_number(item) for item in value)
    if isinstance(value, bool) or value is None:
        return False
    if isinstance(value, (int, float)):
        return not math.isclose(float(value), 1.0, abs_tol=1e-12)
    return True


def walk_mapping(value: Any, path: tuple[str, ...] = ()):
    if not isinstance(value, dict):
        return
    for key, child in value.items():
        child_path = path + (str(key),)
        yield child_path, child
        yield from walk_mapping(child, child_path)


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8-sig") as handle:
        return list(csv.DictReader(handle))


def numeric(value: str) -> float | None:
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def indexed_values(path: Path) -> dict[tuple[str, ...], float]:
    rows = read_csv(path)
    if not rows or "VALUE" not in rows[0]:
        return {}
    index_columns = [column for column in rows[0] if column != "VALUE"]
    values: dict[tuple[str, ...], float] = {}
    for row in rows:
        parsed = numeric(row.get("VALUE", ""))
        if parsed is None:
            continue
        values[tuple(row.get(column, "") for column in index_columns)] = parsed
    return values


def locate_inputs(root: Path) -> list[Path]:
    candidates: list[Path] = []
    direct = root / "model" / "inputs"
    if direct.is_dir():
        candidates.append(direct)
    for candidate in root.glob("results/*/clewsy"):
        if candidate.is_dir():
            candidates.append(candidate)
    if (root / "TECHNOLOGY.csv").is_file():
        candidates.append(root)
    unique: list[Path] = []
    for candidate in candidates:
        resolved = candidate.resolve()
        if resolved not in unique:
            unique.append(resolved)
    return unique


def locate_configs(root: Path) -> list[Path]:
    candidates = (
        root / "config" / "config.yaml",
        root / "config.yaml",
    )
    return [path for path in candidates if path.is_file()]


def load_config(path: Path) -> Any:
    """Parse a YAML config, importing PyYAML only where it is actually needed.

    PyYAML is the one third-party dependency in this skill, and it is reached
    from this single call. Importing it at module scope made even ``--help``
    fail, and took the stdlib-only input checks down with it. Raises
    ``ImportError`` for the caller to turn into a failure finding — an unread
    config must never be reported as a clean one.
    """
    import yaml

    with path.open(encoding="utf-8") as handle:
        return yaml.safe_load(handle) or {}


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Audit a raw CLEWs model for historical forcing."
    )
    parser.add_argument("model_root", type=Path)
    parser.add_argument(
        "--reference-inputs",
        type=Path,
        help=(
            "Optional untouched upstream OSeMOSYS input directory. Changed "
            "overlapping parameter values are treated as failures."
        ),
    )
    parser.add_argument("--output", type=Path, help="Write JSON findings.")
    args = parser.parse_args()

    root = args.model_root.expanduser().resolve()
    findings: list[dict[str, str]] = []

    def finding(severity: str, rule: str, location: Path | str, detail: str):
        findings.append(
            {
                "severity": severity,
                "rule": rule,
                "location": str(location),
                "detail": detail,
            }
        )

    configs = locate_configs(root)
    if not configs:
        finding(
            "warning",
            "config-missing",
            root,
            "No config/config.yaml or config.yaml was found.",
        )

    for config_path in configs:
        try:
            config = load_config(config_path)
        except ImportError:
            finding(
                "failure",
                "config-unreadable",
                config_path,
                (
                    "PyYAML is not installed for this interpreter, so the "
                    "configuration was not audited for forcing. Install it "
                    "(python3 -m pip install pyyaml) or re-run with an "
                    "interpreter that has it; the input-file checks still ran. "
                    "This is a failure, not a warning: an unaudited config "
                    "cannot clear the non-forcing gate."
                ),
            )
            continue
        for key_path, value in walk_mapping(config):
            key = key_path[-1]
            dotted = ".".join(key_path)
            if key in HARD_FORCING_CONFIG_KEYS and is_populated(value):
                finding(
                    "failure",
                    "historical-override-config",
                    config_path,
                    f"{dotted} is populated.",
                )
            elif (
                key in FITTED_FACTOR_CONFIG_KEYS
                and is_populated(value)
                and contains_nonunity_number(value)
            ):
                finding(
                    "failure",
                    "fitted-factor-config",
                    config_path,
                    f"{dotted} contains non-unity fitted factors.",
                )
            elif key in POLICY_OR_BOUND_CONFIG_KEYS and is_populated(value):
                finding(
                    "warning",
                    "raw-scenario-constraint",
                    config_path,
                    (
                        f"{dotted} is populated. Verify it is not historical "
                        "forcing and belongs in the raw scenario."
                    ),
                )

    input_directories = locate_inputs(root)
    if not input_directories:
        finding(
            "warning",
            "inputs-missing",
            root,
            "No model/inputs or results/*/clewsy directory was found.",
        )

    for input_directory in input_directories:
        for lower_name, upper_name, label in PAIR_CHECKS:
            lower_path = input_directory / lower_name
            upper_path = input_directory / upper_name
            if not lower_path.is_file() or not upper_path.is_file():
                continue
            lower = indexed_values(lower_path)
            upper = indexed_values(upper_path)
            for key in sorted(lower.keys() & upper.keys()):
                lower_value = lower[key]
                upper_value = upper[key]
                if (
                    lower_value > 0
                    and upper_value > 0
                    and math.isclose(
                        lower_value, upper_value, rel_tol=1e-10, abs_tol=1e-12
                    )
                ):
                    finding(
                        "failure",
                        "equal-lower-upper-bound",
                        input_directory,
                        f"{label} at index {key} equals {lower_value}.",
                    )
            # Upper limits are guarded `<> -1` upstream, so 0 is a live bound that
            # pins the variable to zero on its own - no matching lower bound needed,
            # which is why the pair check above cannot see it. Warned rather than
            # failed: a zero cap is legitimate when a technology genuinely is not
            # available, and forcing only when it was chosen to match an idle history.
            for key, upper_value in sorted(upper.items()):
                if upper_value == 0:
                    finding(
                        "warning",
                        "zero-upper-bound",
                        input_directory,
                        f"{label} upper bound at index {key} is an active zero, "
                        "switching the object off; confirm this is a structural "
                        "availability limit and not a historical outcome.",
                    )

        if args.reference_inputs:
            reference = args.reference_inputs.expanduser().resolve()
            for name in REFERENCE_PARAMETERS:
                current_path = input_directory / name
                reference_path = reference / name
                if not current_path.is_file() or not reference_path.is_file():
                    continue
                current = indexed_values(current_path)
                original = indexed_values(reference_path)
                for key in sorted(current.keys() & original.keys()):
                    if not math.isclose(
                        current[key],
                        original[key],
                        rel_tol=1e-10,
                        abs_tol=1e-12,
                    ):
                        finding(
                            "failure",
                            "upstream-value-changed",
                            current_path,
                            (
                                f"Overlapping index {key} changed from "
                                f"{original[key]} to {current[key]}."
                            ),
                        )

    failures = sum(item["severity"] == "failure" for item in findings)
    warnings = sum(item["severity"] == "warning" for item in findings)
    report = {
        "model_root": str(root),
        "reference_inputs": (
            str(args.reference_inputs.expanduser().resolve())
            if args.reference_inputs
            else None
        ),
        "status": "fail" if failures else "pass",
        "failure_count": failures,
        "warning_count": warnings,
        "findings": findings,
    }

    rendered = json.dumps(report, indent=2)
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(rendered + "\n", encoding="utf-8")
    print(rendered)
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
