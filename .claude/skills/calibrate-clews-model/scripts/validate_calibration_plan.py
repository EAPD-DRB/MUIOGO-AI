#!/usr/bin/env python3
"""Validate the mandatory design and evidence gates for CLEWs calibration."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from pathlib import Path
from typing import Any


OBSERVATION_ROLES = {
    "initial_stock",
    "final_demand",
    "real_world_constraint",
    "benchmark_only",
}
TECHNOLOGY_ROLES = {
    "physical_stock",
    "pass_through",
    "accounting",
    "backstop",
    "conversion",
    "demand",
    "resource_supply",
}
FULL_PRECISION = {"full_precision", "source_native", "exact"}
SHA256_RE = re.compile(r"^[0-9a-fA-F]{64}$")
PRE_SOLVE_GATES = (
    "source_diff_allowlist",
    "identifier_integrity",
    "initial_year_equation_replay",
    "all_year_capacity_service_envelope",
    "generated_data_inspection",
    "matrix_check",
)
PROMOTION_GATES = PRE_SOLVE_GATES + (
    "cbc_solve",
    "baseline_comparison",
    "timestamp_identity",
    "constraint_residuals_duals",
    "documentation",
)
ACTIVITY_BOUND_PARAMETERS = {
    "TAL",
    "TAU",
    "TotalTechnologyAnnualActivityLowerLimit",
    "TotalTechnologyAnnualActivityUpperLimit",
}


def load_json(path: Path) -> Any:
    with path.open(encoding="utf-8") as stream:
        return json.load(stream)


def require_text(
    container: dict[str, Any],
    field: str,
    location: str,
    errors: list[str],
) -> None:
    if not isinstance(container.get(field), str) or not container[field].strip():
        errors.append(f"{location}.{field} must be non-empty text")


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def verify_precision_input(
    item: dict[str, Any],
    location: str,
    stage: str,
    base_dir: Path,
    errors: list[str],
) -> None:
    """Recompute a precision input's digest and compare it with the record."""
    recorded = str(item.get("sha256", "")).strip().lower()
    # Cheap pre-filter: a value that cannot be a digest is rejected before I/O.
    if not SHA256_RE.fullmatch(recorded):
        errors.append(
            f"{location}.sha256 must be a 64-character checksum at {stage}"
        )
        return
    path_value = item.get("path")
    if not isinstance(path_value, str) or not path_value.strip():
        return
    candidate = Path(path_value.strip()).expanduser()
    if not candidate.is_absolute():
        candidate = base_dir / candidate
    if not candidate.is_file():
        errors.append(
            f"{location}.path is missing at {stage}, so its recorded checksum "
            f"cannot be verified: {path_value}"
        )
        return
    try:
        actual = sha256_file(candidate)
    except OSError as error:
        errors.append(f"{location}.path cannot be read at {stage}: {error}")
        return
    if actual != recorded:
        errors.append(
            f"{location}.sha256 does not match {path_value}: recorded "
            f"{recorded}, actual {actual}"
        )


def validate_plan(
    plan: Any, stage: str, plan_dir: Path | None = None
) -> list[str]:
    errors: list[str] = []
    base_dir = Path(plan_dir).expanduser() if plan_dir is not None else Path.cwd()
    if not isinstance(plan, dict):
        return ["plan root must be a JSON object"]
    if plan.get("schema_version") != 1:
        errors.append("schema_version must equal 1")

    case = plan.get("case")
    if not isinstance(case, dict):
        errors.append("case must be an object")
    else:
        for field in (
            "source_case",
            "candidate_case",
            "baseline_run",
            "scenario",
        ):
            require_text(case, field, "case", errors)
        if case.get("source_case") == case.get("candidate_case"):
            errors.append(
                "case.candidate_case must be disposable and distinct from "
                "case.source_case"
            )

    intent = plan.get("intent")
    observations: list[Any] = []
    if not isinstance(intent, dict):
        errors.append("intent must be an object")
    else:
        require_text(intent, "purpose", "intent", errors)
        observations = intent.get("observations")
        if not isinstance(observations, list) or not observations:
            errors.append("intent.observations must be a non-empty list")
            observations = []

    observed_parameters: set[str] = set()
    needs_technology_roles = False
    for index, observation in enumerate(observations):
        location = f"intent.observations[{index}]"
        if not isinstance(observation, dict):
            errors.append(f"{location} must be an object")
            continue
        require_text(observation, "name", location, errors)
        role = observation.get("role")
        if role not in OBSERVATION_ROLES:
            errors.append(
                f"{location}.role must be one of "
                f"{sorted(OBSERVATION_ROLES)}"
            )
        sources = observation.get("source_ids")
        if not isinstance(sources, list) or not sources or not all(
            isinstance(item, str) and item.strip() for item in sources
        ):
            errors.append(
                f"{location}.source_ids must contain traceable source IDs"
            )
        parameters = observation.get("affected_parameters")
        if not isinstance(parameters, list) or not all(
            isinstance(item, str) and item.strip() for item in parameters
        ):
            errors.append(
                f"{location}.affected_parameters must be a list of names"
            )
            parameters = []
        observed_parameters.update(parameters)
        if role == "benchmark_only" and parameters:
            errors.append(
                f"{location} is benchmark_only and cannot affect parameters"
            )
        if role == "initial_stock":
            needs_technology_roles = True
        if role != "real_world_constraint" and (
            set(parameters) & ACTIVITY_BOUND_PARAMETERS
        ):
            errors.append(
                f"{location} uses an activity-bound parameter without a "
                "real_world_constraint role"
            )
        if observation.get("temporary_pin") is not False:
            errors.append(
                f"{location}.temporary_pin must be false"
            )
        if observation.get("release_year") is not None:
            errors.append(
                f"{location} defines a release_year; use a physical "
                "full-horizon dynamic instead"
            )
        horizon = observation.get("constraint_horizon")
        if horizon not in {
            "initial_year",
            "full_horizon",
            "not_applicable",
        }:
            errors.append(
                f"{location}.constraint_horizon is invalid"
            )
        if role == "real_world_constraint" and horizon != "full_horizon":
            errors.append(
                f"{location} real_world_constraint must have a full_horizon"
            )

    equation_map = plan.get("equation_map")
    mapped_parameters: set[str] = set()
    if not isinstance(equation_map, list) or not equation_map:
        errors.append("equation_map must be a non-empty list")
        equation_map = []
    for index, mapping in enumerate(equation_map):
        location = f"equation_map[{index}]"
        if not isinstance(mapping, dict):
            errors.append(f"{location} must be an object")
            continue
        for field in (
            "parameter",
            "source_file",
            "export_path",
            "physical_effect",
        ):
            require_text(mapping, field, location, errors)
        parameter = mapping.get("parameter")
        if isinstance(parameter, str):
            if parameter in mapped_parameters:
                errors.append(
                    f"{location}.parameter duplicates {parameter}"
                )
            mapped_parameters.add(parameter)
        equations = mapping.get("local_equations")
        if not isinstance(equations, list) or not equations or not all(
            isinstance(item, str) and item.strip() for item in equations
        ):
            errors.append(
                f"{location}.local_equations must list inspected equations"
            )
    missing_maps = sorted(observed_parameters - mapped_parameters)
    if missing_maps:
        errors.append(
            "affected parameters missing from equation_map: "
            f"{missing_maps}"
        )

    technology_roles = plan.get("technology_roles")
    if not isinstance(technology_roles, list):
        errors.append("technology_roles must be a list")
        technology_roles = []
    if needs_technology_roles and not technology_roles:
        errors.append(
            "initial_stock observations require explicit technology_roles"
        )
    seen_technologies: set[str] = set()
    for index, item in enumerate(technology_roles):
        location = f"technology_roles[{index}]"
        if not isinstance(item, dict):
            errors.append(f"{location} must be an object")
            continue
        require_text(item, "technology", location, errors)
        require_text(item, "basis", location, errors)
        technology = item.get("technology")
        if isinstance(technology, str):
            if technology in seen_technologies:
                errors.append(
                    f"{location}.technology duplicates {technology}"
                )
            seen_technologies.add(technology)
        if item.get("role") not in TECHNOLOGY_ROLES:
            errors.append(
                f"{location}.role must be one of "
                f"{sorted(TECHNOLOGY_ROLES)}"
            )

    precision_inputs = plan.get("precision_inputs")
    if not isinstance(precision_inputs, list) or not precision_inputs:
        errors.append("precision_inputs must be a non-empty list")
        precision_inputs = []
    for index, item in enumerate(precision_inputs):
        location = f"precision_inputs[{index}]"
        if not isinstance(item, dict):
            errors.append(f"{location} must be an object")
            continue
        for field in ("name", "path", "sha256"):
            require_text(item, field, location, errors)
        if stage != "design":
            verify_precision_input(item, location, stage, base_dir, errors)
        if (
            item.get("used_for_initialization")
            and item.get("precision") not in FULL_PRECISION
        ):
            errors.append(
                f"{location} initializes the model without a "
                "full-precision source"
            )

    runtime = plan.get("runtime_incident")
    if not isinstance(runtime, dict):
        errors.append("runtime_incident must be an object")
    else:
        for field in ("control_artifact", "minimal_ab_change"):
            require_text(runtime, field, "runtime_incident", errors)
        known_good = runtime.get("known_good_seconds")
        budget = runtime.get("candidate_budget_seconds")
        multiplier = runtime.get("maximum_budget_multiplier", 2)
        if not isinstance(known_good, (int, float)) or known_good <= 0:
            errors.append(
                "runtime_incident.known_good_seconds must be positive"
            )
        if not isinstance(budget, (int, float)) or budget <= 0:
            errors.append(
                "runtime_incident.candidate_budget_seconds must be positive"
            )
        if not isinstance(multiplier, (int, float)) or multiplier < 1:
            errors.append(
                "runtime_incident.maximum_budget_multiplier must be >= 1"
            )
        if all(
            isinstance(value, (int, float))
            for value in (known_good, budget, multiplier)
        ) and budget > known_good * multiplier:
            errors.append(
                "candidate runtime budget exceeds the declared maximum "
                "multiple of the known-good runtime"
            )

    gates = plan.get("gates")
    if not isinstance(gates, dict):
        errors.append("gates must be an object")
        gates = {}
    required_gates = (
        ()
        if stage == "design"
        else PRE_SOLVE_GATES
        if stage == "pre-solve"
        else PROMOTION_GATES
    )
    for gate_name in PROMOTION_GATES:
        gate = gates.get(gate_name)
        if not isinstance(gate, dict):
            errors.append(f"gates.{gate_name} must be an object")
            continue
        if gate.get("status") not in {
            "pending",
            "passed",
            "failed",
            "not_applicable",
        }:
            errors.append(f"gates.{gate_name}.status is invalid")
        if gate_name in required_gates:
            if gate.get("status") != "passed":
                errors.append(
                    f"gates.{gate_name}.status must be passed at {stage}"
                )
            if not isinstance(gate.get("artifact"), str) or not gate[
                "artifact"
            ].strip():
                errors.append(
                    f"gates.{gate_name}.artifact must identify evidence at "
                    f"{stage}"
                )
    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("plan", type=Path)
    parser.add_argument(
        "--stage",
        choices=("design", "pre-solve", "promotion"),
        default="design",
    )
    args = parser.parse_args()
    plan_path = args.plan.expanduser().resolve()
    try:
        plan = load_json(plan_path)
    except (OSError, json.JSONDecodeError) as error:
        print(json.dumps({"status": "failed", "errors": [str(error)]}))
        return 1
    errors = validate_plan(plan, args.stage, plan_path.parent)
    result = {
        "plan": str(args.plan),
        "stage": args.stage,
        "status": "passed" if not errors else "failed",
        "error_count": len(errors),
        "errors": errors,
    }
    print(json.dumps(result, indent=2))
    return 0 if not errors else 1


if __name__ == "__main__":
    sys.exit(main())
