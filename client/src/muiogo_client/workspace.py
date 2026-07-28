"""Find an installed MUIOGO-AI workspace from anywhere on the machine.

This is what makes "launch your assistant and start interacting" possible: an
assistant running in an arbitrary directory has no idea where MUIOGO, the OG
models, or the link were installed. The composed installer records all of it in
a manifest; this module finds that manifest without being told where to look.

Search order (first hit wins):
  1. $MUIOGO_WORKSPACE/manifest.json          -- explicit override
  2. ~/.muiogo/manifest.json                  -- canonical: written by the
                                                 installer, alongside the
                                                 og-models/og-state that MUIOGO
                                                 itself already keeps there
  3. ~/muiogo-ai-workspace/manifest.json      -- the installer's default workspace
  4. ./manifest.json, walking up to the root  -- you are inside a workspace
"""
import json
import os
from pathlib import Path

MANIFEST_NAME = "manifest.json"
CANONICAL_DIR = Path.home() / ".muiogo"
DEFAULT_WORKSPACE = Path.home() / "muiogo-ai-workspace"


class WorkspaceError(RuntimeError):
    """No installed workspace could be found, or its manifest is unusable."""


def _looks_like_manifest(path):
    """True when the file parses as JSON and carries a muiogo section."""
    try:
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
    except (OSError, ValueError):
        return False
    return isinstance(data, dict) and "muiogo" in data


def candidate_paths(start=None):
    """Every place a manifest might live, in search order."""
    paths = []
    env = os.environ.get("MUIOGO_WORKSPACE", "").strip()
    if env:
        paths.append(Path(env).expanduser() / MANIFEST_NAME)
    paths.append(CANONICAL_DIR / MANIFEST_NAME)
    paths.append(DEFAULT_WORKSPACE / MANIFEST_NAME)
    here = Path(start or Path.cwd()).resolve()
    for parent in [here, *here.parents]:
        paths.append(parent / MANIFEST_NAME)
    return paths


def find_manifest(start=None):
    """Path of the first usable manifest, or None."""
    for path in candidate_paths(start):
        if path.is_file() and _looks_like_manifest(path):
            return path
    return None


def load(start=None):
    """Load the manifest and return (data, path). Raises WorkspaceError."""
    path = find_manifest(start)
    if path is None:
        raise WorkspaceError(
            "No MUIOGO-AI workspace found. Install one with MUIOGO-AI's "
            "scripts/install.sh, or set MUIOGO_WORKSPACE to a workspace folder."
        )
    with open(path, encoding="utf-8") as f:
        return json.load(f), path


def publish(manifest_path):
    """Copy a workspace manifest to the canonical ~/.muiogo/manifest.json.

    The installer calls this so later sessions can find the workspace from
    anywhere. Returns the canonical path, or None if it could not be written.
    """
    src = Path(manifest_path)
    try:
        CANONICAL_DIR.mkdir(parents=True, exist_ok=True)
        dest = CANONICAL_DIR / MANIFEST_NAME
        if src.resolve() == dest.resolve():
            return dest
        dest.write_text(src.read_text(encoding="utf-8"), encoding="utf-8")
        return dest
    except OSError:
        return None


def summary(start=None):
    """A flat, printable picture of the installation for orientation."""
    data, path = load(start)
    muiogo = data.get("muiogo") or {}
    link = data.get("ogclews_link") or {}
    return {
        "manifest": str(path),
        "workspace": data.get("workspace"),
        "generated": data.get("generated"),
        "muiogo_path": muiogo.get("path"),
        "muiogo_ref": muiogo.get("ref"),
        "muiogo_url": muiogo.get("url"),
        "muiogo_port": muiogo.get("port"),
        "data_storage": (
            str(Path(muiogo["path"]) / "WebAPP" / "DataStorage")
            if muiogo.get("path") else None
        ),
        "og_models": data.get("og_models") or [],
        "clews_cases": data.get("clews_cases") or [],
        "link_path": link.get("path"),
        "link_python": link.get("python"),
        "solvers": data.get("solvers") or {},
    }
