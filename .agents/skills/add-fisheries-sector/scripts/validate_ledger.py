#!/usr/bin/env python3
"""Validate the Fisheries canonical six-table ledger.

This runs the same ``provenance.py`` every other CLEWs skill runs, against the
ledger that ``project_registers_to_ledger.py`` writes. It does not replace
``validate_provenance.py``: that one checks the eight registers an analyst
authors, this one checks the canonical tables that get delivered. Run the
register validator first, fix what it reports, then project and run this.

Coverage caveat
---------------
The canonical invariant is that *every populated model value* resolves to exactly
one active ``MODEL_MAP`` row. Proving it needs ``--model-inputs``, and the shared
coverage check walks ``*.csv`` under that directory. A Fisheries sector built in
MUIO stores its values in case JSON, so no directory of input CSVs exists to walk
and coverage cannot be proven here. This script says so in its output rather than
letting a clean pass imply an invariant it did not test.

Usage
-----
    python scripts/validate_ledger.py data_sources
    python scripts/validate_ledger.py data_sources --stage delivery
    python scripts/validate_ledger.py data_sources --model-inputs model/inputs

Exit 0 passes, exit 1 fails.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

try:
    import provenance
except ImportError:  # pragma: no cover - the vendored copy sits beside this file
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    import provenance


def validate(
    ledger_dir: Path, stage: str = "build", model_inputs: Path | None = None
) -> dict[str, Any]:
    ledger_dir = ledger_dir.expanduser().resolve()
    report = provenance.validate(
        ledger_dir, stage=stage, model_inputs=model_inputs
    )
    counts = report.get("row_counts", {})
    coverage = report.get("model_inputs", {})
    return {
        "ledger_dir": str(ledger_dir),
        "stage": stage,
        "status": report.get("status"),
        "failure_count": len(report.get("failures", [])),
        "warning_count": len(report.get("warnings", [])),
        "source_count": counts.get("SOURCES.csv", 0),
        "assumption_count": counts.get("ASSUMPTIONS.csv", 0),
        "calculation_count": counts.get("CALCULATIONS.csv", 0),
        "model_map_count": counts.get("MODEL_MAP.csv", 0),
        "gap_count": counts.get("GAPS.csv", 0),
        "change_count": counts.get("CHANGES.csv", 0),
        "input_coverage_proven": bool(model_inputs),
        "covered_input_count": coverage.get("covered_input_count", 0),
        "populated_input_count": coverage.get("populated_input_count", 0),
        "failures": [f"Ledger: {item}" for item in report.get("failures", [])],
        "warnings": [f"Ledger: {item}" for item in report.get("warnings", [])],
        "ledger": report,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("ledger_dir", type=Path)
    parser.add_argument(
        "--stage", choices=("scaffold", "build", "delivery"), default="build"
    )
    parser.add_argument(
        "--model-inputs",
        type=Path,
        help="directory of model input CSVs; only then is input coverage proven",
    )
    parser.add_argument("--output", type=Path, help="write the JSON report here")
    parser.add_argument(
        "--json", action="store_true", help="print the JSON report instead of a summary"
    )
    args = parser.parse_args(argv)

    report = validate(args.ledger_dir, args.stage, args.model_inputs)
    rendered = json.dumps(report, indent=2)
    if args.output:
        output = args.output.expanduser().resolve()
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(rendered + "\n", encoding="utf-8")

    if args.json:
        print(rendered)
    else:
        print(f"{report['status'].upper()}  {report['ledger_dir']}  stage={args.stage}")
        print(
            "  rows: {0} sources, {1} assumptions, {2} calculations, "
            "{3} model_map, {4} gaps, {5} changes".format(
                report["source_count"],
                report["assumption_count"],
                report["calculation_count"],
                report["model_map_count"],
                report["gap_count"],
                report["change_count"],
            )
        )
        if report["input_coverage_proven"]:
            print(
                "  input coverage: {0}/{1} populated input files mapped".format(
                    report["covered_input_count"], report["populated_input_count"]
                )
            )
        else:
            print(
                "  input coverage: NOT PROVEN (no --model-inputs). Every row here is "
                "checked, but nothing verifies the ledger is complete."
            )
        for item in report["failures"]:
            print(f"  FAIL {item}")
        for item in report["warnings"]:
            print(f"  warn {item}")

    return 1 if report["failure_count"] else 0


if __name__ == "__main__":
    sys.exit(main())
