#!/usr/bin/env python3
"""Validate one CLEWs country package with the canonical six-ledger schema."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

import provenance
from validate_package import REQUIRED_FILES, validate_package


def _config_mapping_failure(root: Path, stage: str) -> str | None:
    if stage == "scaffold" or not (root / "config" / "config.yaml").is_file():
        return None
    map_path = root / "data_sources" / "MODEL_MAP.csv"
    if not map_path.is_file():
        return None
    try:
        _, rows = provenance.read_table(map_path)
    except (OSError, UnicodeDecodeError):
        return None
    active = [row for row in rows if not row.get("superseded_by", "")]
    if any(
        row.get("model_file", "").replace("\\", "/").lstrip("./")
        == "config/config.yaml"
        for row in active
    ):
        return None
    return (
        "MODEL_MAP.csv has no active row for config/config.yaml; "
        "country configuration choices need the same lineage as model input CSVs"
    )


def validate(root: Path, stage: str = "build") -> dict[str, Any]:
    root = root.expanduser().resolve()
    package_report = validate_package(root, stage)
    model_inputs = root / "model" / "inputs" if stage != "scaffold" else None
    ledger_report = provenance.validate(
        root / "data_sources",
        stage=stage,
        model_inputs=model_inputs,
    )

    failures = [
        *(f"Package: {item}" for item in package_report.get("failures", [])),
        *(f"Ledger: {item}" for item in ledger_report.get("failures", [])),
    ]
    warnings = [
        *(f"Package: {item}" for item in package_report.get("warnings", [])),
        *(f"Ledger: {item}" for item in ledger_report.get("warnings", [])),
    ]
    config_failure = _config_mapping_failure(root, stage)
    if config_failure:
        failures.append(f"Ledger: {config_failure}")

    counts = ledger_report.get("row_counts", {})
    coverage = ledger_report.get("model_inputs", {})
    return {
        "package_root": str(root),
        "stage": stage,
        "status": "fail" if failures else "pass",
        "failure_count": len(failures),
        "warning_count": len(warnings),
        "source_count": counts.get("SOURCES.csv", 0),
        "assumption_count": counts.get("ASSUMPTIONS.csv", 0),
        "calculation_count": counts.get("CALCULATIONS.csv", 0),
        "model_map_count": counts.get("MODEL_MAP.csv", 0),
        "covered_input_count": coverage.get("covered_input_count", 0),
        "populated_input_count": coverage.get("populated_input_count", 0),
        "pinned_repository_count": package_report.get(
            "pinned_repository_count", 0
        ),
        "failures": failures,
        "warnings": warnings,
        "ledger": ledger_report,
        "package": package_report,
    }


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Validate a traceable CLEWs country-build package."
    )
    parser.add_argument("package_root", type=Path)
    parser.add_argument(
        "--stage",
        choices=("scaffold", "build", "delivery"),
        default="build",
    )
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    report = validate(args.package_root, args.stage)
    rendered = json.dumps(report, indent=2)
    if args.output:
        output = args.output.expanduser().resolve()
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(rendered + "\n", encoding="utf-8")
    print(rendered)
    return 1 if report["failure_count"] else 0


if __name__ == "__main__":
    sys.exit(main())
