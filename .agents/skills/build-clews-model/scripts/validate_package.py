#!/usr/bin/env python3
"""Validate build-specific CLEWs country-package structure and frozen baselines."""

from __future__ import annotations

import argparse
import fnmatch
import hashlib
import json
import re
import sys
import zipfile
from pathlib import Path
from typing import Any

from provenance import LEDGER_TABLES


PACKAGE_REQUIRED_FILES = (
    "README.md",
    "config/upstream_versions.json",
    "config/baseline_manifest.json",
    "data_sources/DATA_SOURCES.md",
    "documentation/CURRENT_MODEL.md",
    "documentation/MODEL_STRUCTURE.md",
    "documentation/KNOWN_LIMITATIONS.md",
    "documentation/HISTORY.md",
    "documentation/CALIBRATION_HANDOFF.md",
    "documentation/MUIO_IMPORT.md",
    "documentation/REPRODUCE.md",
    "diagnostics/validation_summary.json",
)
LEDGER_REQUIRED_FILES = tuple(f"data_sources/{name}" for name in LEDGER_TABLES)
REQUIRED_FILES = PACKAGE_REQUIRED_FILES + LEDGER_REQUIRED_FILES

FULL_COMMIT = re.compile(r"^[0-9a-f]{40}$")
SHA256 = re.compile(r"^[0-9a-f]{64}$")


def read_json(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ValueError(f"Cannot read valid JSON from {path}: {exc}") from exc
    if not isinstance(value, dict):
        raise ValueError(f"Expected a JSON object in {path}")
    return value


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
        return
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
        and not source_package_excluded(path.relative_to(root), additional_excludes)
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


def validate_package(root: Path, stage: str = "build") -> dict[str, Any]:
    root = root.expanduser().resolve()
    failures: list[str] = []
    warnings: list[str] = []
    if not root.is_dir():
        failures.append(f"Package root does not exist: {root}")
        return {
            "package_root": str(root),
            "stage": stage,
            "status": "fail",
            "failure_count": len(failures),
            "warning_count": 0,
            "pinned_repository_count": 0,
            "failures": failures,
            "warnings": warnings,
        }

    for relative in REQUIRED_FILES:
        if not (root / relative).is_file():
            failures.append(f"Missing required package artifact: {relative}")

    if stage == "scaffold":
        return {
            "package_root": str(root),
            "stage": stage,
            "status": "fail" if failures else "pass",
            "failure_count": len(failures),
            "warning_count": len(warnings),
            "pinned_repository_count": 0,
            "failures": failures,
            "warnings": warnings,
        }

    config_path = root / "config" / "config.yaml"
    if not config_path.is_file():
        failures.append("Missing active country configuration: config/config.yaml")

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
                    failures.append(
                        f"Repository is not pinned to a full commit: {label}"
                    )
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
        if not pins.get("toolchain"):
            failures.append("Toolchain versions are absent from upstream_versions.json.")

    for legacy in (
        "data_sources/MODEL_DATA_MAP.csv",
        "DATA_SOURCE_REGISTER.md",
    ):
        if (root / legacy).exists():
            warnings.append(
                f"Legacy provenance artifact is not part of the canonical ledger: {legacy}"
            )

    if stage == "delivery":
        validate_baseline(root, failures)

    return {
        "package_root": str(root),
        "stage": stage,
        "status": "fail" if failures else "pass",
        "failure_count": len(failures),
        "warning_count": len(warnings),
        "pinned_repository_count": pinned_repositories,
        "failures": failures,
        "warnings": warnings,
    }


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Validate CLEWs country-package structure and frozen baselines."
    )
    parser.add_argument("package_root", type=Path)
    parser.add_argument(
        "--stage",
        choices=("scaffold", "build", "delivery"),
        default="build",
    )
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    report = validate_package(args.package_root, args.stage)
    rendered = json.dumps(report, indent=2)
    if args.output:
        output = args.output.expanduser().resolve()
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(rendered + "\n", encoding="utf-8")
    print(rendered)
    return 1 if report["failure_count"] else 0


if __name__ == "__main__":
    sys.exit(main())
