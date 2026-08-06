#!/usr/bin/env python3
"""Create the standard traceable CLEWs country-package scaffold."""

from __future__ import annotations

import argparse
import csv
import json
import shutil
from datetime import date
from pathlib import Path

from provenance import LEDGER_TABLES, REQUIRED_COLUMNS


SKILL_ROOT = Path(__file__).resolve().parents[1]
TEMPLATE_ROOT = SKILL_ROOT / "assets" / "country-package"
PACKAGE_DIRECTORIES = (
    "backups",
    "data_sources/evidence",
    "data_sources/calculation_notes",
    "documentation/history",
    "geospatial/boundary",
    "geospatial/summary_stats",
    "licenses",
    "model/inputs",
    "model/results",
    "muio",
    "patches",
    "scripts",
)
PACKAGE_SCRIPTS = (
    "audit_no_forcing.py",
    "estimate_resources.py",
    "freeze_raw_baseline.py",
    "provenance.py",
    "validate_delivery.py",
    "validate_package.py",
    "validate_provenance.py",
)


def render_template(text: str, country: str, iso3: str) -> str:
    return (
        text.replace("{{COUNTRY}}", country)
        .replace("{{ISO3}}", iso3)
        .replace("{{DATE}}", date.today().isoformat())
    )


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Initialize a traceable CLEWs country-build package."
    )
    parser.add_argument("package_root", type=Path)
    parser.add_argument("--country", required=True)
    parser.add_argument("--iso3", required=True)
    parser.add_argument(
        "--allow-existing",
        action="store_true",
        help="Add missing scaffold files without overwriting existing files.",
    )
    args = parser.parse_args()

    root = args.package_root.expanduser().resolve()
    iso3 = args.iso3.strip().upper()
    if len(iso3) != 3 or not iso3.isalpha():
        raise SystemExit("--iso3 must contain exactly three letters.")
    if not TEMPLATE_ROOT.is_dir():
        raise SystemExit(f"Template directory is missing: {TEMPLATE_ROOT}")
    if root.exists() and not root.is_dir():
        raise SystemExit(f"Package path exists and is not a directory: {root}")
    if root.exists() and any(root.iterdir()) and not args.allow_existing:
        raise SystemExit(
            f"Refusing to modify non-empty package: {root}. "
            "Use --allow-existing to add only missing files."
        )

    root.mkdir(parents=True, exist_ok=True)
    for relative in PACKAGE_DIRECTORIES:
        (root / relative).mkdir(parents=True, exist_ok=True)

    created: list[str] = []
    skipped: list[str] = []
    for template in sorted(TEMPLATE_ROOT.rglob("*.tmpl")):
        relative = template.relative_to(TEMPLATE_ROOT)
        destination = root / relative.with_name(relative.name.removesuffix(".tmpl"))
        if destination.exists():
            skipped.append(destination.relative_to(root).as_posix())
            continue
        destination.parent.mkdir(parents=True, exist_ok=True)
        rendered = render_template(
            template.read_text(encoding="utf-8"), args.country.strip(), iso3
        )
        destination.write_text(rendered, encoding="utf-8")
        created.append(destination.relative_to(root).as_posix())

    for table in LEDGER_TABLES:
        destination = root / "data_sources" / table
        if destination.exists():
            skipped.append(destination.relative_to(root).as_posix())
            continue
        with destination.open("w", newline="", encoding="utf-8") as handle:
            writer = csv.writer(handle, lineterminator="\n")
            writer.writerow(REQUIRED_COLUMNS[table])
        created.append(destination.relative_to(root).as_posix())

    for script_name in PACKAGE_SCRIPTS:
        source = Path(__file__).resolve().parent / script_name
        destination = root / "scripts" / script_name
        if destination.exists():
            skipped.append(destination.relative_to(root).as_posix())
            continue
        if not source.is_file():
            raise SystemExit(f"Required skill script is missing: {source}")
        shutil.copy2(source, destination)
        destination.chmod(destination.stat().st_mode | 0o111)
        created.append(destination.relative_to(root).as_posix())

    print(
        json.dumps(
            {
                "package_root": str(root),
                "country": args.country.strip(),
                "iso3": iso3,
                "created": created,
                "skipped_existing": skipped,
            },
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
