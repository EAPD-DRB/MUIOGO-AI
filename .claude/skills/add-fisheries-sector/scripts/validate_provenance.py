#!/usr/bin/env python3
"""Validate linked Fisheries source, calculation, and parameter registers."""

from __future__ import annotations

import argparse
import csv
import json
import sys
from pathlib import Path
from typing import Iterable


SCHEMAS = {
    "sources": {
        "id": "source_id",
        "required": {
            "source_id",
            "provider",
            "title",
            "edition",
            "publication_date",
            "reference_period",
            "geography",
            "variable",
            "exact_locator",
            "original_unit",
            "url",
            "access_date",
            "quality_grade",
        },
    },
    "assumptions": {
        "id": "assumption_id",
        "required": {
            "assumption_id",
            "statement",
            "rationale",
            "central_value",
            "unit",
            "sensitivity_required",
            "owner",
            "review_status",
        },
    },
    "calculations": {
        "id": "calculation_id",
        "required": {
            "calculation_id",
            "output_description",
            "formula",
            "input_values",
            "input_units",
            "method",
            "output_value",
            "output_unit",
            "review_status",
        },
    },
    "parameters": {
        "id": "parameter_record_id",
        "required": {
            "parameter_record_id",
            "model_file",
            "parameter",
            "entity",
            "year_start",
            "year_end",
            "value_expression",
            "model_unit",
            "evidence_type",
        },
    },
    "boundaries": {
        "id": "boundary_record_id",
        "required": {
            "boundary_record_id",
            "flow",
            "include_status",
            "origin_statistical_sector",
            "destination_model_service",
            "baseline_value",
            "unit",
            "double_count_action",
        },
    },
    "completeness": {
        "id": "item_id",
        "required": {
            "item_id",
            "subsector",
            "parameter_or_flow",
            "applicability",
            "status",
            "priority",
        },
    },
}

ALLOWED_EVIDENCE = {"direct", "derived", "proxy", "estimated"}
ALLOWED_COMPLETENESS = ALLOWED_EVIDENCE | {"data_gap", "not_applicable"}
ALLOWED_GRADES = {"A", "B", "C", "D"}
YES_NO = {"yes", "no"}


def split_ids(value: str | None) -> list[str]:
    return [item.strip() for item in (value or "").split(";") if item.strip()]


def load_register(path: Path, name: str) -> tuple[list[dict[str, str]], set[str], list[str]]:
    errors: list[str] = []
    schema = SCHEMAS[name]
    if not path.is_file():
        return [], set(), [f"{name}: file not found: {path}"]

    with path.open(newline="", encoding="utf-8-sig") as handle:
        reader = csv.DictReader(handle)
        headers = set(reader.fieldnames or [])
        missing_headers = set(schema["required"]) - headers
        if missing_headers:
            errors.append(
                f"{name}: missing required columns: {', '.join(sorted(missing_headers))}"
            )
        rows = [
            {key: (value or "").strip() for key, value in row.items() if key is not None}
            for row in reader
        ]

    if not rows:
        errors.append(f"{name}: register contains no data rows")

    id_field = str(schema["id"])
    ids: set[str] = set()
    for line_number, row in enumerate(rows, start=2):
        record_id = row.get(id_field, "")
        if not record_id:
            errors.append(f"{name}:{line_number}: missing {id_field}")
        elif record_id in ids:
            errors.append(f"{name}:{line_number}: duplicate {id_field} {record_id!r}")
        else:
            ids.add(record_id)

        for field in sorted(schema["required"]):
            if not row.get(field, ""):
                errors.append(f"{name}:{line_number}: {record_id or '<no id>'} missing {field}")

    return rows, ids, errors


def check_refs(
    rows: Iterable[dict[str, str]],
    register_name: str,
    field: str,
    valid_ids: set[str],
    errors: list[str],
) -> None:
    id_field = str(SCHEMAS[register_name]["id"])
    for row in rows:
        record_id = row.get(id_field, "<no id>")
        for ref in split_ids(row.get(field)):
            if ref not in valid_ids:
                errors.append(
                    f"{register_name}:{record_id}: {field} references unknown ID {ref!r}"
                )


def validate(args: argparse.Namespace) -> dict[str, object]:
    paths = {
        "sources": Path(args.sources),
        "assumptions": Path(args.assumptions),
        "calculations": Path(args.calculations),
        "parameters": Path(args.parameters),
        "boundaries": Path(args.boundaries),
        "completeness": Path(args.completeness),
    }
    rows: dict[str, list[dict[str, str]]] = {}
    ids: dict[str, set[str]] = {}
    errors: list[str] = []
    warnings: list[str] = []

    for name, path in paths.items():
        rows[name], ids[name], register_errors = load_register(path, name)
        errors.extend(register_errors)

    for row in rows["sources"]:
        source_id = row.get("source_id", "<no id>")
        grade = row.get("quality_grade", "").upper()
        if grade and grade not in ALLOWED_GRADES:
            errors.append(f"sources:{source_id}: quality_grade must be A, B, C, or D")
        url = row.get("url", "")
        if url and ":" not in url:
            warnings.append(
                f"sources:{source_id}: URL has no scheme; document whether it is public or restricted"
            )
        checksum = row.get("sha256", "")
        if checksum and (len(checksum) != 64 or any(c not in "0123456789abcdefABCDEF" for c in checksum)):
            errors.append(f"sources:{source_id}: sha256 must contain 64 hexadecimal characters")

    for row in rows["assumptions"]:
        assumption_id = row.get("assumption_id", "<no id>")
        sensitivity = row.get("sensitivity_required", "").lower()
        if sensitivity and sensitivity not in YES_NO:
            errors.append(
                f"assumptions:{assumption_id}: sensitivity_required must be yes or no"
            )

    for row in rows["calculations"]:
        calculation_id = row.get("calculation_id", "<no id>")
        if (
            not split_ids(row.get("source_ids"))
            and not split_ids(row.get("assumption_ids"))
            and not split_ids(row.get("input_calculation_ids"))
        ):
            errors.append(
                f"calculations:{calculation_id}: supply at least one source_id, "
                "assumption_id, or input_calculation_id"
            )
        if row.get("script_path") and not row.get("script_version"):
            errors.append(
                f"calculations:{calculation_id}: script_version is required when script_path is used"
            )

    for row in rows["parameters"]:
        parameter_id = row.get("parameter_record_id", "<no id>")
        evidence = row.get("evidence_type", "").lower()
        if evidence and evidence not in ALLOWED_EVIDENCE:
            errors.append(
                f"parameters:{parameter_id}: evidence_type must be one of "
                f"{', '.join(sorted(ALLOWED_EVIDENCE))}"
            )
        source_refs = split_ids(row.get("source_ids"))
        calculation_ref = row.get("calculation_id", "").strip()
        if not source_refs and not calculation_ref:
            errors.append(
                f"parameters:{parameter_id}: provide direct source_ids or calculation_id"
            )
        if calculation_ref and ";" in calculation_ref:
            errors.append(
                f"parameters:{parameter_id}: calculation_id must identify one calculation"
            )
        if evidence == "direct" and not source_refs:
            errors.append(f"parameters:{parameter_id}: direct evidence requires source_ids")
        if evidence in {"derived", "proxy", "estimated"} and not calculation_ref:
            errors.append(
                f"parameters:{parameter_id}: {evidence} evidence requires calculation_id"
            )

    for row in rows["boundaries"]:
        boundary_id = row.get("boundary_record_id", "<no id>")
        if not split_ids(row.get("source_ids")) and not row.get("calculation_id", ""):
            errors.append(
                f"boundaries:{boundary_id}: provide source_ids or calculation_id"
            )

    for row in rows["completeness"]:
        item_id = row.get("item_id", "<no id>")
        status = row.get("status", "").lower()
        if status and status not in ALLOWED_COMPLETENESS:
            errors.append(
                f"completeness:{item_id}: invalid status {status!r}; use "
                f"{', '.join(sorted(ALLOWED_COMPLETENESS))}"
            )
        parameter_refs = split_ids(row.get("parameter_record_ids"))
        if status in ALLOWED_EVIDENCE and not parameter_refs:
            errors.append(
                f"completeness:{item_id}: populated status {status!r} requires parameter_record_ids"
            )
        if status == "data_gap" and not row.get("data_gap", ""):
            errors.append(f"completeness:{item_id}: data_gap status requires an explanation")
        if status == "not_applicable" and not row.get("notes", ""):
            errors.append(
                f"completeness:{item_id}: not_applicable status requires a reason in notes"
            )

    check_refs(rows["assumptions"], "assumptions", "evidence_source_ids", ids["sources"], errors)
    check_refs(rows["calculations"], "calculations", "source_ids", ids["sources"], errors)
    check_refs(
        rows["calculations"], "calculations", "assumption_ids", ids["assumptions"], errors
    )
    check_refs(
        rows["calculations"],
        "calculations",
        "input_calculation_ids",
        ids["calculations"],
        errors,
    )
    check_refs(rows["parameters"], "parameters", "source_ids", ids["sources"], errors)
    check_refs(
        rows["parameters"], "parameters", "assumption_ids", ids["assumptions"], errors
    )
    check_refs(rows["boundaries"], "boundaries", "source_ids", ids["sources"], errors)
    check_refs(
        rows["completeness"],
        "completeness",
        "parameter_record_ids",
        ids["parameters"],
        errors,
    )

    for row in rows["parameters"]:
        calc = row.get("calculation_id", "")
        if calc and calc not in ids["calculations"]:
            errors.append(
                f"parameters:{row.get('parameter_record_id', '<no id>')}: "
                f"calculation_id references unknown ID {calc!r}"
            )

    calculation_dependencies = {
        row.get("calculation_id", ""): split_ids(row.get("input_calculation_ids"))
        for row in rows["calculations"]
        if row.get("calculation_id", "")
    }
    visiting: set[str] = set()
    visited: set[str] = set()

    def detect_cycle(calculation_id: str, chain: list[str]) -> None:
        if calculation_id in visiting:
            cycle_start = chain.index(calculation_id) if calculation_id in chain else 0
            cycle = chain[cycle_start:] + [calculation_id]
            errors.append(
                "calculations: dependency cycle detected: " + " -> ".join(cycle)
            )
            return
        if calculation_id in visited:
            return
        visiting.add(calculation_id)
        for dependency in calculation_dependencies.get(calculation_id, []):
            if dependency in calculation_dependencies:
                detect_cycle(dependency, chain + [calculation_id])
        visiting.remove(calculation_id)
        visited.add(calculation_id)

    for calculation_id in sorted(calculation_dependencies):
        detect_cycle(calculation_id, [])
    for row in rows["boundaries"]:
        calc = row.get("calculation_id", "")
        if calc and calc not in ids["calculations"]:
            errors.append(
                f"boundaries:{row.get('boundary_record_id', '<no id>')}: "
                f"calculation_id references unknown ID {calc!r}"
            )

    return {
        "status": "pass" if not errors else "fail",
        "counts": {name: len(register_rows) for name, register_rows in rows.items()},
        "errors": errors,
        "warnings": warnings,
        "files": {name: str(path.resolve()) for name, path in paths.items()},
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Validate Fisheries provenance register schemas and cross-references."
    )
    parser.add_argument("--sources", required=True)
    parser.add_argument("--assumptions", required=True)
    parser.add_argument("--calculations", required=True)
    parser.add_argument("--parameters", required=True)
    parser.add_argument("--boundaries", required=True)
    parser.add_argument("--completeness", required=True)
    parser.add_argument("--output", help="Optional JSON report path")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    report = validate(args)
    rendered = json.dumps(report, indent=2, sort_keys=True)
    if args.output:
        Path(args.output).write_text(rendered + "\n", encoding="utf-8")
    print(rendered)
    return 0 if report["status"] == "pass" else 1


if __name__ == "__main__":
    sys.exit(main())
