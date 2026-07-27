#!/usr/bin/env python3
"""Validate and score a CLEWs/OSeMOSYS calibration assessment JSON.

The script applies transparent weights, gates, domain floors, and grade caps.
It does not verify whether the reviewer's evidence or judgment is true.
"""

from __future__ import annotations

import argparse
import json
import math
import sys
from pathlib import Path
from typing import Any


DIMENSION_WEIGHTS = {
    "evidence_provenance": 10,
    "country_representation": 10,
    "historical_initial_state": 10,
    "physical_accounting_integrity": 10,
    "historical_reproduction": 20,
    "nexus_fidelity": 10,
    "forcing_independence": 15,
    "heldout_validation": 10,
    "robustness_reproducibility": 5,
}
GATES = {
    "executable_case",
    "referential_integrity",
    "physical_accounting",
    "scope_integrity",
    "historical_evidence",
    "forcing_disclosure",
    "reproducibility",
}
CRITICAL_GATES = {
    "executable_case",
    "referential_integrity",
    "physical_accounting",
    "scope_integrity",
}
EVIDENCE_GATES = {"historical_evidence", "forcing_disclosure"}
SCOPE_TO_DOMAIN = {
    "energy": "energy",
    "land": "land",
    "water": "water",
    "climate": "climate",
    "nexus": "nexus",
}
GRADE_RANK = {"Unacceptable": 0, "Acceptable": 1, "Good": 2, "Excellent": 3}
CONFIDENCE = {"low", "medium", "high"}
FITNESS = {"suitable", "conditionally suitable", "unsuitable"}


def require_dict(payload: dict[str, Any], key: str) -> dict[str, Any]:
    value = payload.get(key)
    if not isinstance(value, dict):
        raise ValueError(f"{key} must be an object")
    return value


def require_list(payload: dict[str, Any], key: str) -> list[Any]:
    value = payload.get(key)
    if not isinstance(value, list):
        raise ValueError(f"{key} must be an array")
    return value


def score_value(value: Any, label: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError(f"{label} must be numeric")
    result = float(value)
    if not math.isfinite(result) or not 0 <= result <= 100:
        raise ValueError(f"{label} must be between 0 and 100")
    return result


def grade_for_score(score: float) -> str:
    if score < 50:
        return "Unacceptable"
    if score < 70:
        return "Acceptable"
    if score < 85:
        return "Good"
    return "Excellent"


def cap_grade(grade: str, maximum: str) -> str:
    return grade if GRADE_RANK[grade] <= GRADE_RANK[maximum] else maximum


def validate_text_list(payload: dict[str, Any], key: str) -> list[str]:
    values = require_list(payload, key)
    if any(not isinstance(item, str) or not item.strip() for item in values):
        raise ValueError(f"{key} must contain non-empty strings")
    return [item.strip() for item in values]


def validate(payload: dict[str, Any]) -> dict[str, Any]:
    model = require_dict(payload, "model")
    for key in ("name", "country", "claimed_scope", "intended_use"):
        if key not in model:
            raise ValueError(f"model.{key} is required")
    if not isinstance(model["claimed_scope"], list) or not model["claimed_scope"]:
        raise ValueError("model.claimed_scope must be a non-empty array")

    gates = require_dict(payload, "gates")
    missing_gates = GATES - set(gates)
    if missing_gates:
        raise ValueError(f"missing gates: {', '.join(sorted(missing_gates))}")
    gate_statuses: dict[str, str] = {}
    for gate in sorted(GATES):
        entry = gates[gate]
        if not isinstance(entry, dict):
            raise ValueError(f"gates.{gate} must be an object")
        status = str(entry.get("status", "")).lower()
        if status not in {"pass", "fail", "unknown", "partial"}:
            raise ValueError(f"gates.{gate}.status must be pass, fail, partial, or unknown")
        if not str(entry.get("evidence", "")).strip():
            raise ValueError(f"gates.{gate}.evidence is required")
        gate_statuses[gate] = status

    dimensions = require_dict(payload, "dimensions")
    missing_dimensions = set(DIMENSION_WEIGHTS) - set(dimensions)
    if missing_dimensions:
        raise ValueError(f"missing dimensions: {', '.join(sorted(missing_dimensions))}")
    dimension_scores: dict[str, float] = {}
    for dimension in DIMENSION_WEIGHTS:
        entry = dimensions[dimension]
        if not isinstance(entry, dict):
            raise ValueError(f"dimensions.{dimension} must be an object")
        dimension_scores[dimension] = score_value(entry.get("score"), f"dimensions.{dimension}.score")
        if not str(entry.get("rationale", "")).strip():
            raise ValueError(f"dimensions.{dimension}.rationale is required")
        evidence = entry.get("evidence")
        if not isinstance(evidence, list) or not evidence:
            raise ValueError(f"dimensions.{dimension}.evidence must be a non-empty array")

    domains = require_dict(payload, "domains")
    claimed_scope = [str(value).lower() for value in model["claimed_scope"]]
    required_domains = {SCOPE_TO_DOMAIN[value] for value in claimed_scope if value in SCOPE_TO_DOMAIN}
    missing_domains = required_domains - set(domains)
    if missing_domains:
        raise ValueError(f"missing claimed domains: {', '.join(sorted(missing_domains))}")
    domain_scores: dict[str, float] = {}
    for domain, entry in domains.items():
        if not isinstance(entry, dict):
            raise ValueError(f"domains.{domain} must be an object")
        domain_scores[domain] = score_value(entry.get("score"), f"domains.{domain}.score")
        if not str(entry.get("rationale", "")).strip():
            raise ValueError(f"domains.{domain}.rationale is required")

    forcing = require_dict(payload, "forcing")
    forcing_values: dict[str, float] = {}
    for key in ("endogenous_weight", "justified_weight", "history_fixed_weight"):
        value = forcing.get(key)
        if isinstance(value, bool) or not isinstance(value, (int, float)):
            raise ValueError(f"forcing.{key} must be numeric")
        value = float(value)
        if not math.isfinite(value) or value < 0:
            raise ValueError(f"forcing.{key} must be finite and nonnegative")
        forcing_values[key] = value
    forcing_total = sum(forcing_values.values())
    if forcing_total <= 0:
        raise ValueError("forcing weights must sum to more than zero")

    heldout_present = payload.get("heldout_validation_present")
    robustness_present = payload.get("robustness_tests_present")
    if not isinstance(heldout_present, bool):
        raise ValueError("heldout_validation_present must be boolean")
    if not isinstance(robustness_present, bool):
        raise ValueError("robustness_tests_present must be boolean")

    confidence = str(payload.get("confidence", "")).lower()
    if confidence not in CONFIDENCE:
        raise ValueError("confidence must be low, medium, or high")

    fitness = require_list(payload, "fitness")
    if not fitness:
        raise ValueError("fitness must contain at least one use assessment")
    for index, entry in enumerate(fitness):
        if not isinstance(entry, dict):
            raise ValueError(f"fitness[{index}] must be an object")
        if str(entry.get("rating", "")).lower() not in FITNESS:
            raise ValueError(f"fitness[{index}].rating is invalid")
        if not str(entry.get("use", "")).strip() or not str(entry.get("rationale", "")).strip():
            raise ValueError(f"fitness[{index}] requires use and rationale")

    strengths = validate_text_list(payload, "strengths")
    weaknesses = validate_text_list(payload, "weaknesses")
    improvements = validate_text_list(payload, "required_improvements")

    return {
        "model": model,
        "gates": gates,
        "gate_statuses": gate_statuses,
        "dimensions": dimensions,
        "dimension_scores": dimension_scores,
        "domains": domains,
        "domain_scores": domain_scores,
        "required_domains": sorted(required_domains),
        "forcing_values": forcing_values,
        "forcing_total": forcing_total,
        "heldout_present": heldout_present,
        "robustness_present": robustness_present,
        "confidence": confidence,
        "fitness": fitness,
        "strengths": strengths,
        "weaknesses": weaknesses,
        "improvements": improvements,
    }


def assess(data: dict[str, Any]) -> dict[str, Any]:
    weighted_score = sum(
        data["dimension_scores"][key] * weight for key, weight in DIMENSION_WEIGHTS.items()
    ) / 100.0
    preliminary_grade = grade_for_score(weighted_score)
    grade = preliminary_grade
    rules: list[str] = []

    unknown_critical = [gate for gate in CRITICAL_GATES if data["gate_statuses"][gate] in {"unknown", "partial"}]
    failed_critical = [gate for gate in CRITICAL_GATES if data["gate_statuses"][gate] == "fail"]
    unresolved_evidence = [gate for gate in EVIDENCE_GATES if data["gate_statuses"][gate] != "pass"]

    if unresolved_evidence or unknown_critical:
        final_grade = "Not assessable"
        if unresolved_evidence:
            rules.append("Historical evidence or forcing disclosure is unresolved.")
        if unknown_critical:
            rules.append("At least one critical technical gate is not evidenced.")
    else:
        if failed_critical:
            grade = "Unacceptable"
            rules.append("A critical technical gate failed.")

        required_scores = {
            domain: data["domain_scores"][domain] for domain in data["required_domains"]
        }
        if required_scores:
            minimum_domain = min(required_scores.values())
            if minimum_domain < 40:
                grade = "Unacceptable"
                rules.append("A claimed core domain scored below 40.")
            elif minimum_domain < 60:
                new_grade = cap_grade(grade, "Acceptable")
                if new_grade != grade:
                    rules.append("A claimed core domain below 60 caps the grade at Acceptable.")
                grade = new_grade
            elif minimum_domain < 70:
                new_grade = cap_grade(grade, "Good")
                if new_grade != grade:
                    rules.append("A claimed core domain below 70 caps the grade at Good.")
                grade = new_grade

        fixed_share = data["forcing_values"]["history_fixed_weight"] / data["forcing_total"]
        if fixed_share >= 0.50:
            grade = "Unacceptable"
            rules.append("History-fixed evidence is at least 50% of scored weight.")
        elif fixed_share >= 0.25:
            new_grade = cap_grade(grade, "Acceptable")
            if new_grade != grade:
                rules.append("History-fixed evidence at or above 25% caps the grade at Acceptable.")
            grade = new_grade
        elif fixed_share > 0:
            new_grade = cap_grade(grade, "Good")
            if new_grade != grade:
                rules.append("History-fixed evidence caps the grade at Good without an independent replacement test.")
            grade = new_grade

        if not data["heldout_present"]:
            new_grade = cap_grade(grade, "Good")
            if new_grade != grade:
                rules.append("No held-out historical validation caps the grade at Good.")
            grade = new_grade
        if data["gate_statuses"]["reproducibility"] != "pass":
            new_grade = cap_grade(grade, "Acceptable")
            if new_grade != grade:
                rules.append("Incomplete reproducibility caps the grade at Acceptable.")
            grade = new_grade
        if grade == "Excellent":
            if (
                data["confidence"] != "high"
                or not data["robustness_present"]
                or any(data["domain_scores"][domain] < 80 for domain in data["required_domains"])
            ):
                grade = "Good"
                rules.append(
                    "Excellent requires high confidence, robustness tests, and every claimed domain at 80 or above."
                )
        final_grade = grade

    forcing_shares = {
        key.replace("_weight", ""): round(value / data["forcing_total"], 4)
        for key, value in data["forcing_values"].items()
    }
    return {
        "schema_version": 1,
        "model": data["model"],
        "weighted_score": round(weighted_score, 2),
        "preliminary_grade": preliminary_grade,
        "calibration_grade": final_grade,
        "confidence": data["confidence"].title(),
        "applied_rules": rules,
        "gates": data["gates"],
        "dimension_scores": {
            key: {"score": data["dimension_scores"][key], "weight": weight}
            for key, weight in DIMENSION_WEIGHTS.items()
        },
        "domain_scores": data["domains"],
        "forcing_shares": forcing_shares,
        "heldout_validation_present": data["heldout_present"],
        "robustness_tests_present": data["robustness_present"],
        "fitness": data["fitness"],
        "strengths": data["strengths"],
        "weaknesses": data["weaknesses"],
        "required_improvements": data["improvements"],
        "method_warning": (
            "The scorecard makes reviewer judgments explicit but cannot verify source quality, "
            "constraint classification, tolerances, or the truth of supplied evidence."
        ),
    }


def markdown(report: dict[str, Any]) -> str:
    model = report["model"]
    lines = [
        f"# Calibration assessment — {model.get('name', 'Unnamed model')}",
        "",
        f"- **Country:** {model.get('country', 'Not stated')}",
        f"- **Calibration grade:** {report['calibration_grade']}",
        f"- **Weighted score:** {report['weighted_score']}/100 (preliminary band: {report['preliminary_grade']})",
        f"- **Confidence:** {report['confidence']}",
        f"- **Intended use:** {model.get('intended_use', 'Not stated')}",
        "",
        "## Critical gates",
        "",
        "| Gate | Status | Evidence |",
        "|---|---|---|",
    ]
    for gate, entry in report["gates"].items():
        evidence = str(entry.get("evidence", "")).replace("|", "\\|").replace("\n", " ")
        lines.append(f"| {gate.replace('_', ' ').title()} | {entry.get('status')} | {evidence} |")
    lines.extend(
        [
            "",
            "## Forcing profile",
            "",
            f"- Endogenous: {report['forcing_shares']['endogenous']:.1%}",
            f"- Justified constraint: {report['forcing_shares']['justified']:.1%}",
            f"- History-fixed: {report['forcing_shares']['history_fixed']:.1%}",
            "",
            "## Domain results",
            "",
            "| Domain | Score | Rationale |",
            "|---|---:|---|",
        ]
    )
    for domain, entry in report["domain_scores"].items():
        rationale = str(entry.get("rationale", "")).replace("|", "\\|").replace("\n", " ")
        lines.append(f"| {domain.title()} | {entry.get('score')} | {rationale} |")

    def section(title: str, values: list[str]) -> None:
        lines.extend(["", f"## {title}", ""])
        lines.extend(f"- {value}" for value in values)

    section("Strong points", report["strengths"])
    section("Weak points", report["weaknesses"])
    section("Required improvements", report["required_improvements"])
    lines.extend(["", "## Fitness for purpose", ""])
    for item in report["fitness"]:
        lines.append(f"- **{str(item['rating']).title()} — {item['use']}:** {item['rationale']}")
    if report["applied_rules"]:
        section("Grade rules applied", report["applied_rules"])
    lines.extend(["", f"> {report['method_warning']}", ""])
    return "\n".join(lines)


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("assessment_json", type=Path)
    parser.add_argument("--output-json", type=Path)
    parser.add_argument("--output-markdown", type=Path)
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    try:
        with args.assessment_json.open(encoding="utf-8") as handle:
            payload = json.load(handle)
        if not isinstance(payload, dict):
            raise ValueError("assessment JSON root must be an object")
        report = assess(validate(payload))
    except (OSError, json.JSONDecodeError, ValueError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2

    json_payload = json.dumps(report, indent=2, ensure_ascii=False) + "\n"
    if args.output_json:
        args.output_json.parent.mkdir(parents=True, exist_ok=True)
        args.output_json.write_text(json_payload, encoding="utf-8")
    if args.output_markdown:
        args.output_markdown.parent.mkdir(parents=True, exist_ok=True)
        args.output_markdown.write_text(markdown(report), encoding="utf-8")
    if not args.output_json and not args.output_markdown:
        print(json_payload, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
