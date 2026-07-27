#!/usr/bin/env python3
"""Validate CLEWs country-package structure, provenance, and raw baselines."""

from __future__ import annotations

import argparse
import csv
import fnmatch
import hashlib
import json
import re
import sys
import zipfile
from pathlib import Path
from typing import Any


SCHEMAS = {
    "data_sources/SOURCES.csv": (
        "source_id",
        "provider",
        "product",
        "edition",
        "reference_period",
        "variable",
        "source_unit",
        "geography",
        "model_use",
        "selection",
        "transformation",
        "quality",
        "proxy",
        "official_url",
        "license",
        "national_alternative",
        "review_owner",
        "local_evidence_path",
        "sha256",
        "status",
        "notes",
    ),
    "data_sources/ASSUMPTIONS.csv": (
        "assumption_id",
        "sector",
        "description",
        "used_for",
        "status",
        "source_or_reason",
        "review_need",
    ),
    "data_sources/CALCULATIONS.csv": (
        "calculation_id",
        "sector",
        "question",
        "formula",
        "inputs",
        "output",
        "units",
        "model_location",
        "source_ids",
        "assumption_ids",
        "status",
        "notes",
    ),
    "data_sources/MODEL_DATA_MAP.csv": (
        "map_id",
        "sector",
        "model_entity",
        "parameter_or_file",
        "coverage_patterns",
        "modes",
        "years",
        "meaning",
        "source_ids",
        "assumption_ids",
        "calculation_ids",
        "representation_status",
        "notes",
    ),
}
REQUIRED_FILES = (
    "README.md",
    "config/upstream_versions.json",
    "config/baseline_manifest.json",
    "data_sources/SOURCES.csv",
    "data_sources/DATA_SOURCES.md",
    "data_sources/ASSUMPTIONS.csv",
    "data_sources/CALCULATIONS.csv",
    "data_sources/MODEL_DATA_MAP.csv",
    "documentation/CURRENT_MODEL.md",
    "documentation/MODEL_STRUCTURE.md",
    "documentation/KNOWN_LIMITATIONS.md",
    "documentation/HISTORY.md",
    "documentation/CALIBRATION_HANDOFF.md",
    "documentation/MUIO_IMPORT.md",
    "documentation/REPRODUCE.md",
    "diagnostics/validation_summary.json",
)
FULL_COMMIT = re.compile(r"^[0-9a-f]{40}$")
SHA256 = re.compile(r"^[0-9a-f]{64}$")
INACTIVE_WORDS = (
    "planned",
    "diagnostic",
    "candidate",
    "scenario",
    "context",
    "inactive",
    "retired",
    "superseded",
)
CATCH_ALL_PATTERNS = {
    "*",
    "**",
    "**/*",
    "model/inputs/*",
    "model/inputs/*.csv",
    "model/inputs/**",
}


def read_json(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ValueError(f"Cannot read valid JSON from {path}: {exc}") from exc
    if not isinstance(value, dict):
        raise ValueError(f"Expected a JSON object in {path}")
    return value


def read_csv(path: Path) -> tuple[list[str], list[dict[str, str]]]:
    with path.open(newline="", encoding="utf-8-sig") as handle:
        reader = csv.DictReader(handle)
        fields = list(reader.fieldnames or [])
        rows = [
            {key: (value or "").strip() for key, value in row.items()}
            for row in reader
            if any((value or "").strip() for value in row.values())
        ]
    return fields, rows


def split_ids(value: str) -> set[str]:
    return {item.strip() for item in value.split(";") if item.strip()}


def is_active(value: str) -> bool:
    normalized = value.strip().lower()
    return bool(normalized) and not any(word in normalized for word in INACTIVE_WORDS)


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def tree_hash(root: Path) -> dict[str, Any]:
    digest = hashlib.sha256()
    files = sorted(path for path in root.rglob("*") if path.is_file())
    for path in files:
        relative = path.relative_to(root).as_posix()
        digest.update(relative.encode("utf-8"))
        digest.update(b"\0")
        digest.update(bytes.fromhex(sha256_file(path)))
    return {"sha256": digest.hexdigest(), "file_count": len(files)}


def source_package_excluded(relative: Path, extra_patterns: list[str]) -> bool:
    text = relative.as_posix()
    if relative.parts and relative.parts[0] == "backups":
        return True
    if "__pycache__" in relative.parts or relative.name == ".DS_Store":
        return True
    if relative.suffix.lower() in {".pyc", ".lp", ".mps"}:
        return True
    if text == "config/baseline_manifest.json":
        return True
    if relative.parts and relative.parts[0] == "muio" and relative.suffix == ".zip":
        return True
    return any(fnmatch.fnmatch(text, pattern) for pattern in extra_patterns)


def selected_tree_hash(root: Path, files: list[Path]) -> dict[str, Any]:
    digest = hashlib.sha256()
    for path in sorted(files):
        relative = path.relative_to(root).as_posix()
        digest.update(relative.encode("utf-8"))
        digest.update(b"\0")
        digest.update(bytes.fromhex(sha256_file(path)))
    return {"sha256": digest.hexdigest(), "file_count": len(files)}


def unique_ids(
    rows: list[dict[str, str]],
    column: str,
    prefix: str,
    failures: list[str],
) -> set[str]:
    values = [row.get(column, "") for row in rows]
    missing = sum(not value for value in values)
    if missing:
        failures.append(f"{column} has {missing} blank identifier(s).")
    invalid = sorted({value for value in values if value and not value.startswith(prefix)})
    if invalid:
        failures.append(f"{column} has invalid prefix: {', '.join(invalid)}")
    duplicates = sorted({value for value in values if values.count(value) > 1 and value})
    if duplicates:
        failures.append(f"{column} has duplicate IDs: {', '.join(duplicates)}")
    return {value for value in values if value}


def populated_csv(path: Path) -> bool:
    try:
        _, rows = read_csv(path)
    except (OSError, csv.Error):
        return False
    return bool(rows)


def resolve_package_path(root: Path, value: str) -> Path:
    candidate = Path(value).expanduser()
    if not candidate.is_absolute():
        candidate = root / candidate
    return candidate.resolve()


def validate_baseline(root: Path, failures: list[str]) -> None:
    manifest_path = root / "config" / "baseline_manifest.json"
    try:
        manifest = read_json(manifest_path)
    except ValueError as exc:
        failures.append(str(exc))
        return
    if str(manifest.get("status", "")).lower() != "complete":
        failures.append("Baseline manifest status is not complete.")
        return
    if manifest.get("model_status") != "raw_uncalibrated":
        failures.append("Baseline manifest does not identify a raw uncalibrated model.")

    for key in ("source_package", "muio_archive"):
        record = manifest.get(key)
        if not isinstance(record, dict):
            failures.append(f"Baseline manifest lacks object: {key}")
            continue
        path_value = str(record.get("path", ""))
        expected_sha = str(record.get("sha256", ""))
        expected_size = record.get("size_bytes")
        if not path_value:
            failures.append(f"Baseline artifact has no path: {key}")
            continue
        artifact = resolve_package_path(root, path_value)
        if not artifact.is_file():
            failures.append(f"Baseline artifact is missing: {path_value}")
            continue
        if not SHA256.fullmatch(expected_sha):
            failures.append(f"Baseline artifact has invalid SHA-256: {key}")
        elif sha256_file(artifact) != expected_sha:
            failures.append(f"Baseline artifact checksum mismatch: {path_value}")
        if artifact.stat().st_size != expected_size:
            failures.append(f"Baseline artifact size mismatch: {path_value}")
        if artifact.suffix.lower() == ".zip":
            try:
                with zipfile.ZipFile(artifact) as handle:
                    bad_member = handle.testzip()
                if bad_member:
                    failures.append(
                        f"Baseline ZIP has corrupt member {bad_member}: {path_value}"
                    )
            except zipfile.BadZipFile:
                failures.append(f"Baseline artifact is not a valid ZIP: {path_value}")

    expected_trees = manifest.get("tree_hashes")
    if not isinstance(expected_trees, dict):
        failures.append("Baseline manifest lacks tree_hashes.")
    else:
        source_record = manifest.get("source_package")
        additional_excludes = (
            source_record.get("additional_excludes", [])
            if isinstance(source_record, dict)
            else []
        )
        if not isinstance(additional_excludes, list) or not all(
            isinstance(pattern, str) for pattern in additional_excludes
        ):
            failures.append("Baseline source package has invalid additional_excludes.")
            additional_excludes = []
        selected_files = [
            path
            for path in root.rglob("*")
            if path.is_file()
            and not source_package_excluded(
                path.relative_to(root), additional_excludes
            )
        ]
        expected_source_tree = expected_trees.get("source_package_contents")
        actual_source_tree = selected_tree_hash(root, selected_files)
        if (
            not isinstance(expected_source_tree, dict)
            or expected_source_tree != actual_source_tree
        ):
            failures.append("Baseline source-package content tree has changed.")
        for key, relative in (
            ("model_inputs", "model/inputs"),
            ("model_results", "model/results"),
        ):
            expected = expected_trees.get(key)
            actual = tree_hash(root / relative)
            if not isinstance(expected, dict) or expected != actual:
                failures.append(f"Baseline tree hash mismatch: {relative}")

    records = manifest.get("records")
    if not isinstance(records, dict):
        failures.append("Baseline manifest lacks record checksums.")
    else:
        for key, relative in (
            ("upstream_versions_sha256", "config/upstream_versions.json"),
            ("no_forcing_audit_sha256", "diagnostics/no_forcing_audit.json"),
            ("validation_summary_sha256", "diagnostics/validation_summary.json"),
        ):
            path = root / relative
            expected = records.get(key)
            if not path.is_file() or expected != sha256_file(path):
                failures.append(f"Baseline record checksum mismatch: {relative}")


def validate(root: Path, stage: str) -> dict[str, Any]:
    failures: list[str] = []
    warnings: list[str] = []
    root = root.expanduser().resolve()
    if not root.is_dir():
        return {
            "package_root": str(root),
            "stage": stage,
            "status": "fail",
            "failure_count": 1,
            "warning_count": 0,
            "failures": [f"Package root does not exist: {root}"],
            "warnings": [],
        }

    for relative in REQUIRED_FILES:
        if not (root / relative).is_file():
            failures.append(f"Missing required provenance artifact: {relative}")

    tables: dict[str, list[dict[str, str]]] = {}
    for relative, schema in SCHEMAS.items():
        path = root / relative
        if not path.is_file():
            continue
        try:
            fields, rows = read_csv(path)
        except (OSError, csv.Error) as exc:
            failures.append(f"Cannot read {relative}: {exc}")
            continue
        missing_columns = [column for column in schema if column not in fields]
        if missing_columns:
            failures.append(
                f"{relative} lacks columns: {', '.join(missing_columns)}"
            )
        tables[relative] = rows

    if stage == "scaffold":
        return {
            "package_root": str(root),
            "stage": stage,
            "status": "fail" if failures else "pass",
            "failure_count": len(failures),
            "warning_count": len(warnings),
            "failures": failures,
            "warnings": warnings,
        }

    sources = tables.get("data_sources/SOURCES.csv", [])
    assumptions = tables.get("data_sources/ASSUMPTIONS.csv", [])
    calculations = tables.get("data_sources/CALCULATIONS.csv", [])
    mappings = tables.get("data_sources/MODEL_DATA_MAP.csv", [])
    if not sources:
        failures.append("SOURCES.csv contains no source records.")
    if not mappings:
        failures.append("MODEL_DATA_MAP.csv contains no model mappings.")

    source_ids = unique_ids(sources, "source_id", "DS-", failures)
    assumption_ids = unique_ids(assumptions, "assumption_id", "A-", failures)
    calculation_ids = unique_ids(calculations, "calculation_id", "C-", failures)
    unique_ids(mappings, "map_id", "M-", failures)

    referenced_sources: set[str] = set()
    referenced_assumptions: set[str] = set()
    referenced_calculations: set[str] = set()
    active_map_sources: set[str] = set()
    active_map_assumptions: set[str] = set()
    active_map_calculations: set[str] = set()
    active_mappings: list[dict[str, str]] = []

    for row in calculations:
        referenced_sources.update(split_ids(row.get("source_ids", "")))
        referenced_assumptions.update(split_ids(row.get("assumption_ids", "")))
    for row in mappings:
        row_sources = split_ids(row.get("source_ids", ""))
        row_assumptions = split_ids(row.get("assumption_ids", ""))
        row_calculations = split_ids(row.get("calculation_ids", ""))
        referenced_sources.update(row_sources)
        referenced_assumptions.update(row_assumptions)
        referenced_calculations.update(row_calculations)
        if is_active(row.get("representation_status", "")):
            active_mappings.append(row)
            active_map_sources.update(row_sources)
            active_map_assumptions.update(row_assumptions)
            active_map_calculations.update(row_calculations)
            if not (row_sources or row_assumptions or row_calculations):
                failures.append(
                    f"Active map {row.get('map_id')} has no lineage identifier."
                )
            if not split_ids(row.get("coverage_patterns", "")):
                failures.append(
                    f"Active map {row.get('map_id')} has no coverage pattern."
                )

    unresolved = sorted(
        (referenced_sources - source_ids)
        | (referenced_assumptions - assumption_ids)
        | (referenced_calculations - calculation_ids)
    )
    if unresolved:
        failures.append(f"Unresolved provenance IDs: {', '.join(unresolved)}")

    active_lineage_sources = set(active_map_sources)
    active_lineage_assumptions = set(active_map_assumptions)
    for row in calculations:
        if row.get("calculation_id", "") in active_map_calculations:
            active_lineage_sources.update(split_ids(row.get("source_ids", "")))
            active_lineage_assumptions.update(
                split_ids(row.get("assumption_ids", ""))
            )

    for row in sources:
        source_id = row.get("source_id", "")
        status = row.get("status", "").lower()
        if status == "documentation_gap":
            if not row.get("notes"):
                failures.append(f"Documentation gap lacks explanation: {source_id}")
            continue
        if is_active(status):
            for column in (
                "provider",
                "product",
                "reference_period",
                "variable",
                "model_use",
                "quality",
            ):
                if not row.get(column):
                    failures.append(f"Active source {source_id} lacks {column}.")
            if not row.get("official_url") and not row.get("local_evidence_path"):
                failures.append(
                    f"Active source {source_id} has neither URL nor retained evidence."
                )
            if not row.get("local_evidence_path") and not row.get("notes"):
                failures.append(
                    f"Active source {source_id} without retained evidence "
                    "must explain retrieval or access in notes."
                )
            if source_id not in active_lineage_sources:
                failures.append(f"Active source is not mapped: {source_id}")

        evidence_value = row.get("local_evidence_path", "")
        if evidence_value:
            evidence_path = Path(evidence_value)
            if evidence_path.is_absolute() or ".." in evidence_path.parts:
                failures.append(
                    f"Evidence path must be package-relative: {source_id}"
                )
                continue
            evidence = root / evidence_path
            expected_sha = row.get("sha256", "")
            if not evidence.is_file():
                failures.append(
                    f"Retained evidence is missing for {source_id}: {evidence_value}"
                )
            elif not SHA256.fullmatch(expected_sha):
                failures.append(f"Evidence SHA-256 is invalid or absent: {source_id}")
            elif sha256_file(evidence) != expected_sha:
                failures.append(f"Evidence checksum mismatch: {source_id}")

    for row in assumptions:
        if is_active(row.get("status", "")) and row.get(
            "assumption_id", ""
        ) not in active_lineage_assumptions:
            failures.append(
                f"Active assumption is not mapped: {row.get('assumption_id')}"
            )
    for row in calculations:
        if is_active(row.get("status", "")) and row.get(
            "calculation_id", ""
        ) not in active_map_calculations:
            failures.append(
                f"Active calculation is not mapped: {row.get('calculation_id')}"
            )

    config_path = root / "config" / "config.yaml"
    if not config_path.is_file():
        failures.append("Missing active country configuration: config/config.yaml")
    target_paths = [
        path.relative_to(root).as_posix()
        for path in sorted((root / "model" / "inputs").glob("*.csv"))
        if populated_csv(path)
    ]
    if config_path.is_file():
        target_paths.append("config/config.yaml")
    if not target_paths:
        failures.append("No populated model input files were found.")

    patterns: list[str] = []
    for row in active_mappings:
        for pattern in split_ids(row.get("coverage_patterns", "")):
            pattern_path = Path(pattern)
            if pattern_path.is_absolute() or ".." in pattern_path.parts:
                failures.append(
                    f"Coverage pattern must be package-relative: "
                    f"{row.get('map_id')}:{pattern}"
                )
                continue
            if pattern in CATCH_ALL_PATTERNS:
                failures.append(
                    f"Over-broad coverage pattern is not allowed: "
                    f"{row.get('map_id')}:{pattern}"
                )
            patterns.append(pattern)
            if not any(root.glob(pattern)):
                failures.append(
                    f"Coverage pattern matches no package file: "
                    f"{row.get('map_id')}:{pattern}"
                )
    uncovered = [
        path
        for path in target_paths
        if not any(fnmatch.fnmatch(path, pattern) for pattern in patterns)
    ]
    if uncovered:
        failures.append(
            "Populated model inputs lack provenance coverage: "
            + ", ".join(uncovered)
        )

    try:
        pins = read_json(root / "config" / "upstream_versions.json")
    except ValueError as exc:
        failures.append(str(exc))
        pins = {}
    pinned_repositories = 0

    def inspect_pins(value: Any, label: str) -> None:
        nonlocal pinned_repositories
        if isinstance(value, dict):
            repository = value.get("repository")
            if repository:
                pinned_repositories += 1
                commit = str(value.get("commit", ""))
                if not FULL_COMMIT.fullmatch(commit):
                    failures.append(f"Repository is not pinned to a full commit: {label}")
            for key, child in value.items():
                inspect_pins(child, f"{label}.{key}" if label else key)
        elif isinstance(value, list):
            for index, child in enumerate(value):
                inspect_pins(child, f"{label}[{index}]")

    inspect_pins(pins, "")
    if pinned_repositories == 0:
        failures.append("No pinned upstream repository was found.")
    muiogo = pins.get("muiogo") if isinstance(pins, dict) else None
    if not isinstance(muiogo, dict):
        failures.append("upstream_versions.json lacks a muiogo object.")
    elif stage == "delivery":
        if not muiogo.get("version") and not FULL_COMMIT.fullmatch(
            str(muiogo.get("commit", ""))
        ):
            failures.append("MUIO has neither a version nor a full pinned commit.")
        for key in (
            "importer_sha256",
            "parameter_registry_sha256",
            "formulation_sha256",
        ):
            if not SHA256.fullmatch(str(muiogo.get(key, ""))):
                failures.append(f"MUIO checksum is invalid or absent: {key}")
        if not pins.get("toolchain"):
            failures.append("Toolchain versions are absent from upstream_versions.json.")

    if (root / "DATA_SOURCE_REGISTER.md").exists():
        warnings.append(
            "Legacy root DATA_SOURCE_REGISTER.md exists; SOURCES.csv is canonical."
        )
    if stage == "delivery":
        validate_baseline(root, failures)

    return {
        "package_root": str(root),
        "stage": stage,
        "status": "fail" if failures else "pass",
        "failure_count": len(failures),
        "warning_count": len(warnings),
        "source_count": len(sources),
        "assumption_count": len(assumptions),
        "calculation_count": len(calculations),
        "model_map_count": len(mappings),
        "covered_input_count": len(target_paths) - len(uncovered),
        "populated_input_count": len(target_paths),
        "pinned_repository_count": pinned_repositories,
        "failures": failures,
        "warnings": warnings,
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
