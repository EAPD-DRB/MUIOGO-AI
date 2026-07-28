#!/usr/bin/env python3
"""Compare CLEWs/OSeMOSYS results with aligned historical observations.

History-fixed (H) rows are described but excluded from reproduction scores.
The script uses only the Python standard library.
"""

from __future__ import annotations

import argparse
import csv
import json
import math
import sys
from collections import defaultdict
from pathlib import Path
from typing import Any


REQUIRED = {"domain", "metric", "observed", "modeled", "tolerance", "forcing_class"}
DOMAINS = {"energy", "land", "water", "climate", "nexus"}
PHASES = {"calibration", "validation"}
FORCING = {"E", "J", "H"}


def number(row: dict[str, str], field: str, row_number: int, required: bool = True) -> float | None:
    value = (row.get(field) or "").strip()
    if not value:
        if required:
            raise ValueError(f"row {row_number}: {field} is required")
        return None
    try:
        result = float(value)
    except ValueError as exc:
        raise ValueError(f"row {row_number}: {field} must be numeric, got {value!r}") from exc
    if not math.isfinite(result):
        raise ValueError(f"row {row_number}: {field} must be finite")
    return result


def fit_score(error_ratio: float) -> float:
    """Continuous 0-100 score relative to the reviewer's declared tolerance."""
    anchors = ((0.0, 100.0), (0.5, 100.0), (1.0, 80.0), (1.5, 60.0), (2.0, 30.0), (4.0, 0.0))
    if error_ratio >= anchors[-1][0]:
        return 0.0
    for (x0, y0), (x1, y1) in zip(anchors, anchors[1:]):
        if x0 <= error_ratio <= x1:
            fraction = (error_ratio - x0) / (x1 - x0)
            return y0 + fraction * (y1 - y0)
    return 0.0


def weighted_average(pairs: list[tuple[float, float]]) -> float | None:
    total = sum(weight for _, weight in pairs)
    if total <= 0:
        return None
    return sum(value * weight for value, weight in pairs) / total


def rounded(value: float | None) -> float | None:
    return None if value is None else round(value, 3)


def load_rows(path: Path) -> list[dict[str, Any]]:
    with path.open(newline="", encoding="utf-8-sig") as handle:
        reader = csv.DictReader(handle)
        fields = set(reader.fieldnames or [])
        missing = REQUIRED - fields
        if missing:
            raise ValueError(f"missing required CSV columns: {', '.join(sorted(missing))}")
        result: list[dict[str, Any]] = []
        for row_number, source in enumerate(reader, start=2):
            if not any((value or "").strip() for value in source.values()):
                continue
            domain = (source.get("domain") or "").strip().lower()
            if domain not in DOMAINS:
                raise ValueError(f"row {row_number}: domain must be one of {sorted(DOMAINS)}")
            metric = (source.get("metric") or "").strip()
            if not metric:
                raise ValueError(f"row {row_number}: metric is required")
            phase = (source.get("phase") or "calibration").strip().lower()
            if phase not in PHASES:
                raise ValueError(f"row {row_number}: phase must be calibration or validation")
            forcing_class = (source.get("forcing_class") or "").strip().upper()
            if forcing_class not in FORCING:
                raise ValueError(f"row {row_number}: forcing_class must be E, J, or H")

            observed = number(source, "observed", row_number)
            modeled = number(source, "modeled", row_number)
            tolerance = number(source, "tolerance", row_number)
            tolerance_absolute = number(source, "tolerance_absolute", row_number, required=False)
            weight = number(source, "weight", row_number, required=False)
            weight = 1.0 if weight is None else weight
            assert observed is not None and modeled is not None and tolerance is not None
            if tolerance <= 0:
                raise ValueError(f"row {row_number}: tolerance must be greater than zero")
            if weight <= 0:
                raise ValueError(f"row {row_number}: weight must be greater than zero")
            if observed == 0 and (tolerance_absolute is None or tolerance_absolute <= 0):
                raise ValueError(
                    f"row {row_number}: a zero observation requires positive tolerance_absolute"
                )
            allowed_absolute_error = (
                tolerance_absolute if observed == 0 else abs(observed) * tolerance
            )
            assert allowed_absolute_error is not None
            error = abs(modeled - observed)
            relative_error = None if observed == 0 else error / abs(observed)
            error_ratio = error / allowed_absolute_error
            point_score = fit_score(error_ratio)
            result.append(
                {
                    "row": row_number,
                    "domain": domain,
                    "metric": metric,
                    "phase": phase,
                    "year": (source.get("year") or "").strip() or None,
                    "period": (source.get("period") or "").strip() or None,
                    "region": (source.get("region") or "").strip() or None,
                    "unit": (source.get("unit") or "").strip() or None,
                    "source": (source.get("source") or "").strip() or None,
                    "observed": observed,
                    "modeled": modeled,
                    "absolute_error": rounded(error),
                    "relative_error": rounded(relative_error),
                    "tolerance": tolerance,
                    "tolerance_absolute": tolerance_absolute,
                    "error_to_tolerance_ratio": rounded(error_ratio),
                    "within_tolerance": error_ratio <= 1.0,
                    "fit_score": rounded(point_score),
                    "weight": weight,
                    "forcing_class": forcing_class,
                    "credited": forcing_class in {"E", "J"},
                    "constraint_refs": (source.get("constraint_refs") or "").strip() or None,
                    "notes": (source.get("notes") or "").strip() or None,
                }
            )
    if not result:
        raise ValueError("comparison CSV has no data rows")
    return result


def summarize(rows: list[dict[str, Any]]) -> dict[str, Any]:
    forcing_weights = {key: 0.0 for key in FORCING}
    groups: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)
    phase_groups: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        forcing_weights[row["forcing_class"]] += row["weight"]
        groups[(row["phase"], row["domain"])].append(row)
        phase_groups[row["phase"]].append(row)

    total_weight = sum(forcing_weights.values())

    def group_summary(items: list[dict[str, Any]]) -> dict[str, Any]:
        credited = [item for item in items if item["credited"]]
        score = weighted_average([(item["fit_score"], item["weight"]) for item in credited])
        observed_total = sum(abs(item["observed"]) * item["weight"] for item in credited)
        error_total = sum(item["absolute_error"] * item["weight"] for item in credited)
        return {
            "rows": len(items),
            "credited_rows": len(credited),
            "credited_weight": rounded(sum(item["weight"] for item in credited)),
            "within_tolerance_credited": sum(item["within_tolerance"] for item in credited),
            "fit_score": rounded(score),
            "weighted_absolute_percentage_error": (
                rounded(error_total / observed_total) if observed_total > 0 else None
            ),
        }

    by_phase = {phase: group_summary(items) for phase, items in sorted(phase_groups.items())}
    by_phase_domain: dict[str, dict[str, Any]] = {}
    for (phase, domain), items in sorted(groups.items()):
        by_phase_domain.setdefault(phase, {})[domain] = group_summary(items)

    return {
        "schema_version": 1,
        "row_count": len(rows),
        "forcing_weights": {key: rounded(value) for key, value in sorted(forcing_weights.items())},
        "forcing_shares": {
            key: rounded(value / total_weight) if total_weight else None
            for key, value in sorted(forcing_weights.items())
        },
        "history_fixed_rows_excluded_from_fit": True,
        "by_phase": by_phase,
        "by_phase_and_domain": by_phase_domain,
        "rows": rows,
    }


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("csv_file", type=Path, help="historical comparison CSV")
    parser.add_argument("--output", type=Path, help="write JSON here instead of stdout")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    try:
        report = summarize(load_rows(args.csv_file))
    except (OSError, ValueError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2
    payload = json.dumps(report, indent=2, ensure_ascii=False) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(payload, encoding="utf-8")
    else:
        print(payload, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
