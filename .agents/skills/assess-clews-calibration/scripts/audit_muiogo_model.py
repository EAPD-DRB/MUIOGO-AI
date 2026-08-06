#!/usr/bin/env python3
"""Structural and constraint inventory for one MUIOGO model folder.

This is now a thin delegate to ``clews-model-review/audit.py`` (``inventory()``
and ``inventory_main()``), which owns every check both skills share. The CLI,
the JSON schema and the exit codes are unchanged.

Why: this file used to reimplement six of that script's checks with copied
constants, and its own reference scan matched ``TEC_``/``COM_`` patterns in the
serialized JSON text. That truncated any ID containing a character outside the
pattern - ``TEC_env.land_v1`` was read as ``TEC_env`` and then reported as an
undefined reference - which is exactly the failure ``audit.py``'s scalar-parsing
``model_ids()`` was written to avoid. One implementation, one source of truth.

Usage:
    python audit_muiogo_model.py <model-folder> [--output <inventory.json>]

Screening tool: spot-check its findings before grading a calibration.
"""

from __future__ import annotations

import importlib.util
import os
import sys
from pathlib import Path
from typing import Any

# Set CLEWS_AUDIT_PY to override the search below (e.g. an unusual skill layout).
ENV_OVERRIDE = "CLEWS_AUDIT_PY"
_MODULE: Any = None


def audit_module() -> Any:
    """Import clews-model-review/audit.py from wherever the skills are installed."""
    global _MODULE
    if _MODULE is not None:
        return _MODULE
    here = Path(__file__).resolve()
    candidates = [Path(os.environ[ENV_OVERRIDE])] if os.environ.get(ENV_OVERRIDE) else []
    for parent in here.parents:
        for prefix in ((), ("skills",), (".claude", "skills")):
            candidates.append(parent.joinpath(*prefix, "clews-model-review", "audit.py"))
    for candidate in candidates:
        if candidate.is_file():
            spec = importlib.util.spec_from_file_location("clews_model_audit", candidate)
            module = importlib.util.module_from_spec(spec)
            assert spec.loader is not None
            spec.loader.exec_module(module)
            _MODULE = module
            return module
    raise FileNotFoundError(
        "clews-model-review/audit.py not found near "
        f"{here}; set {ENV_OVERRIDE} to its path"
    )


def audit(model_dir: Path | str) -> dict[str, Any]:
    """Backwards-compatible alias for audit.py's ``inventory()``."""
    return audit_module().inventory(model_dir)


def main(argv: list[str] | None = None) -> int:
    try:
        module = audit_module()
    except FileNotFoundError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2
    return module.inventory_main(argv)


if __name__ == "__main__":
    raise SystemExit(main())
