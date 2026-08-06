#!/usr/bin/env python3
"""Freeze a validated raw CLEWs package without duplicating its MUIO ZIP."""

from __future__ import annotations

import argparse
import json
import zipfile
from datetime import date
from pathlib import Path
from typing import Any

from validate_package import (
    selected_tree_hash,
    sha256_file,
    source_package_excluded,
    tree_hash,
)
from validate_provenance import validate as validate_provenance


def read_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"Expected a JSON object: {path}")
    return value


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Create and register immutable raw CLEWs baseline artifacts."
    )
    parser.add_argument("package_root", type=Path)
    parser.add_argument("--muio-archive", type=Path, required=True)
    parser.add_argument("--date", dest="archive_date", default=date.today().isoformat())
    parser.add_argument(
        "--exclude-glob",
        action="append",
        default=[],
        help="Additional package-relative glob to exclude from the source archive.",
    )
    args = parser.parse_args()

    root = args.package_root.expanduser().resolve()
    if not root.is_dir():
        raise SystemExit(f"Package root does not exist: {root}")
    provenance = validate_provenance(root, "build")
    if provenance["failure_count"]:
        raise SystemExit(
            "Cannot freeze baseline: build-stage provenance validation failed:\n- "
            + "\n- ".join(provenance["failures"])
        )
    manifest_path = root / "config" / "baseline_manifest.json"
    if not manifest_path.is_file():
        raise SystemExit(f"Baseline manifest template is missing: {manifest_path}")
    existing = read_json(manifest_path)
    if str(existing.get("status", "")).lower() == "complete":
        raise SystemExit("Refusing to overwrite a completed baseline manifest.")

    summary = read_json(root / "diagnostics" / "validation_summary.json")
    for key in ("upstream_raw", "muio_import", "muio_final"):
        stage = summary.get(key)
        if not isinstance(stage, dict) or str(stage.get("status", "")).lower() != "pass":
            raise SystemExit(f"Cannot freeze baseline: validation stage is not pass: {key}")
    no_forcing = read_json(root / "diagnostics" / "no_forcing_audit.json")
    if str(no_forcing.get("status", "")).lower() != "pass":
        raise SystemExit("Cannot freeze baseline: no-forcing audit is not pass.")
    if int(no_forcing.get("failure_count", 0) or 0) != 0:
        raise SystemExit("Cannot freeze baseline: no-forcing audit contains failures.")

    muio_archive = args.muio_archive.expanduser()
    if not muio_archive.is_absolute():
        muio_archive = root / muio_archive
    muio_archive = muio_archive.resolve()
    if not muio_archive.is_file() or not zipfile.is_zipfile(muio_archive):
        raise SystemExit(f"Portable MUIO ZIP is missing or invalid: {muio_archive}")

    backup_dir = root / "backups"
    backup_dir.mkdir(parents=True, exist_ok=True)
    source_archive = backup_dir / (
        f"{root.name}_source_raw_{args.archive_date}.zip"
    )
    if source_archive.exists():
        raise SystemExit(f"Refusing to overwrite baseline archive: {source_archive}")

    package_files = sorted(path for path in root.rglob("*") if path.is_file())
    included = [
        path
        for path in package_files
        if not source_package_excluded(path.relative_to(root), args.exclude_glob)
    ]
    with zipfile.ZipFile(
        source_archive, "x", compression=zipfile.ZIP_DEFLATED, compresslevel=9
    ) as handle:
        for path in included:
            handle.write(path, arcname=f"{root.name}/{path.relative_to(root).as_posix()}")

    try:
        muio_relative = muio_archive.relative_to(root).as_posix()
    except ValueError:
        muio_relative = str(muio_archive)
    manifest = {
        "schema_version": 1,
        "status": "complete",
        "model_status": "raw_uncalibrated",
        "created": date.today().isoformat(),
        "source_package": {
            "path": source_archive.relative_to(root).as_posix(),
            # Identity of the archive just written, so later runs can detect
            # that it was altered. ZIP members embed mtimes, so this digest
            # cannot be reproduced by rebuilding the archive; the reproducible
            # content check is tree_hashes.source_package_contents below.
            "sha256": sha256_file(source_archive),
            "size_bytes": source_archive.stat().st_size,
            "included_file_count": len(included),
            "excluded_defaults": [
                "backups/**",
                "**/__pycache__/**",
                "**/*.pyc",
                "**/*.lp",
                "**/*.mps",
                "config/baseline_manifest.json",
                "muio/*.zip",
            ],
            "additional_excludes": args.exclude_glob,
        },
        "muio_archive": {
            "path": muio_relative,
            "sha256": sha256_file(muio_archive),
            "size_bytes": muio_archive.stat().st_size,
        },
        "tree_hashes": {
            "source_package_contents": selected_tree_hash(root, included),
            "model_inputs": tree_hash(root / "model" / "inputs"),
            "model_results": tree_hash(root / "model" / "results"),
        },
    }
    manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(manifest, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
