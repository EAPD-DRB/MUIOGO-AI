#!/usr/bin/env python3
"""Structural and constraint inventory for one MUIOGO model folder.

This is a thin delegate to ``audit.py`` beside it (``inventory()`` and
``inventory_main()``), a generated copy of ``clews-model-review/audit.py``, which
owns every check both skills share. The copy keeps this skill self-contained. The CLI,
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

# Set CLEWS_AUDIT_PY to use a different audit.py than the copy beside this file.
ENV_OVERRIDE = "CLEWS_AUDIT_PY"
_MODULE: Any = None


def audit_module() -> Any:
    """Import the audit.py shipped beside this script (or CLEWS_AUDIT_PY)."""
    global _MODULE
    if _MODULE is not None:
        return _MODULE
    override = os.environ.get(ENV_OVERRIDE)
    candidate = Path(override) if override else Path(__file__).resolve().with_name("audit.py")
    if not candidate.is_file():
        raise FileNotFoundError(
            f"{candidate} not found; reinstall the whole skill folder or set {ENV_OVERRIDE}"
        )
    spec = importlib.util.spec_from_file_location("clews_model_audit", candidate)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    _MODULE = module
    return module


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
