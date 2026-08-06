#!/usr/bin/env python3
"""Validate required whole-country CLEWs/MUIO delivery artifacts."""

from __future__ import annotations

import argparse
import json
import sys
import zipfile
from pathlib import Path
from typing import Any

from validate_provenance import REQUIRED_FILES as PROVENANCE_REQUIRED_FILES
from validate_provenance import validate as validate_provenance


# Everything the build stage already requires, plus the artifacts that only
# exist once the model has been audited, sized, and frozen for delivery.
DELIVERY_ONLY_FILES = (
    "diagnostics/no_forcing_audit.json",
    "diagnostics/resource_estimate.json",
)
REQUIRED_FILES = PROVENANCE_REQUIRED_FILES + DELIVERY_ONLY_FILES

REQUIRED_STATUS_KEYS = ("upstream_raw", "muio_import", "muio_final")


def read_json(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ValueError(f"Cannot read valid JSON from {path}: {exc}") from exc
    if not isinstance(value, dict):
        raise ValueError(f"Expected a JSON object in {path}")
    return value


def find_zip(root: Path, supplied: Path | None) -> tuple[Path | None, str | None]:
    if supplied:
        candidate = supplied.expanduser().resolve()
        return candidate, None
    manifest_path = root / "config" / "baseline_manifest.json"
    if manifest_path.is_file():
        try:
            manifest = read_json(manifest_path)
            record = manifest.get("muio_archive")
            if isinstance(record, dict) and record.get("path"):
                candidate = Path(str(record["path"])).expanduser()
                if not candidate.is_absolute():
                    candidate = root / candidate
                return candidate.resolve(), None
        except ValueError:
            pass
    candidates = sorted((root / "muio").glob("*.zip"))
    if len(candidates) == 1:
        return candidates[0], None
    if not candidates:
        return None, "No portable ZIP was found; pass --zip when stored elsewhere."
    return None, "Multiple ZIP files found; pass --zip to identify the final archive."


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Validate mandatory whole-country CLEWs/MUIO handoff artifacts."
    )
    parser.add_argument("package_root", type=Path)
    parser.add_argument("--zip", type=Path, dest="zip_path")
    parser.add_argument(
        "--allow-optimization-file",
        action="store_true",
        help="Allow regenerable LP/MPS files in the portable ZIP",
    )
    parser.add_argument("--output", type=Path, help="Write JSON validation report")
    args = parser.parse_args()

    root = args.package_root.expanduser().resolve()
    failures: list[str] = []
    warnings: list[str] = []

    if not root.is_dir():
        raise SystemExit(f"Package root does not exist: {root}")

    provenance = validate_provenance(root, "delivery")
    failures.extend(
        f"Provenance: {failure}" for failure in provenance.get("failures", [])
    )
    warnings.extend(
        f"Provenance: {warning}" for warning in provenance.get("warnings", [])
    )

    for relative in REQUIRED_FILES:
        if not (root / relative).is_file():
            failures.append(f"Missing required artifact: {relative}")

    no_forcing_path = root / "diagnostics/no_forcing_audit.json"
    if no_forcing_path.is_file():
        try:
            audit = read_json(no_forcing_path)
            if str(audit.get("status", "")).lower() != "pass":
                failures.append("No-forcing audit status is not pass.")
            if int(audit.get("failure_count", 0) or 0) != 0:
                failures.append("No-forcing audit contains failures.")
        except (ValueError, TypeError) as exc:
            failures.append(str(exc))

    summary_path = root / "diagnostics/validation_summary.json"
    if summary_path.is_file():
        try:
            summary = read_json(summary_path)
            for key in REQUIRED_STATUS_KEYS:
                stage = summary.get(key)
                if not isinstance(stage, dict):
                    failures.append(f"Validation summary lacks object: {key}")
                    continue
                if str(stage.get("status", "")).lower() != "pass":
                    failures.append(f"Validation stage is not pass: {key}")
            import_stage = summary.get("muio_import", {})
            if isinstance(import_stage, dict):
                if int(import_stage.get("nondefault_errors", 0) or 0) != 0:
                    failures.append("MUIO import has nondefault parity errors.")
                if (
                    int(import_stage.get("unsupported_nondefault_rows", 0) or 0)
                    != 0
                ):
                    failures.append(
                        "MUIO import has unsupported nondefault source rows."
                    )
        except (ValueError, TypeError) as exc:
            failures.append(str(exc))

    resource_path = root / "diagnostics/resource_estimate.json"
    if resource_path.is_file():
        try:
            estimate = read_json(resource_path)
            light = str(estimate.get("traffic_light", "")).lower()
            if light == "red":
                failures.append("Resource estimate is red.")
            elif light == "amber":
                warnings.append("Resource estimate is amber; document acceptance.")
            elif light != "green":
                failures.append("Resource estimate has no valid traffic light.")
            actual = estimate.get("actual")
            if not isinstance(actual, dict) or not any(
                actual.get(key) is not None
                for key in ("rows", "columns", "nonzeros", "solve_seconds")
            ):
                failures.append("Resource estimate does not record actual usage.")
        except ValueError as exc:
            failures.append(str(exc))

    archive, archive_error = find_zip(root, args.zip_path)
    if archive_error:
        failures.append(archive_error)
    elif archive is None or not archive.is_file():
        failures.append(f"Portable ZIP does not exist: {archive}")
    else:
        try:
            # validate_provenance already CRC-checks the archive recorded in
            # the baseline manifest, so this pass only inspects what the
            # archive contains.
            with zipfile.ZipFile(archive) as handle:
                members = handle.namelist()
                lowered = [member.lower() for member in members]
                if not members:
                    failures.append("Portable ZIP is empty.")
                if not any(member.endswith(".json") for member in lowered):
                    failures.append("Portable ZIP contains no model JSON.")
                if not any(
                    token in member
                    for member in lowered
                    for token in ("result", "solution", "solver", ".sol")
                ):
                    failures.append(
                        "Portable ZIP contains no recognizable result or solver output."
                    )
                optimization_files = [
                    member
                    for member in lowered
                    if member.endswith(".lp") or member.endswith(".mps")
                ]
                if optimization_files and not args.allow_optimization_file:
                    failures.append(
                        "Portable ZIP contains regenerable LP/MPS files; "
                        "remove them or pass --allow-optimization-file."
                    )
        except (OSError, zipfile.BadZipFile) as exc:
            failures.append(f"Cannot validate portable ZIP: {exc}")

    report = {
        "package_root": str(root),
        "portable_zip": str(archive) if archive else None,
        "status": "fail" if failures else "pass",
        "failure_count": len(failures),
        "warning_count": len(warnings),
        "failures": failures,
        "warnings": warnings,
        "provenance": provenance,
    }
    rendered = json.dumps(report, indent=2)
    if args.output:
        output = args.output.expanduser().resolve()
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(rendered + "\n", encoding="utf-8")
    print(rendered)
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
