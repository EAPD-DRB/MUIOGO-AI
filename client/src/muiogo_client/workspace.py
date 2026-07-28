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


def looks_like_muiogo(path):
    p = Path(path)
    return (p / "API" / "app.py").is_file() and (p / "WebAPP" / "DataStorage").is_dir()


def looks_like_og_model(path):
    """An OG country model: an og* package beside its own virtual environment."""
    p = Path(path)
    if not venv_python(p):
        return False
    return any(
        d.is_dir() and d.name.startswith("og") and (d / "__init__.py").is_file()
        for d in p.iterdir()
    )


def looks_like_link(path):
    p = Path(path)
    return (p / "ogclews_link").is_dir() and venv_python(p) is not None


def venv_python(path):
    """The interpreter inside a checkout's own venv, or None."""
    for rel in ("bin/python", "Scripts/python.exe"):
        candidate = Path(path) / ".venv" / rel
        if candidate.exists():
            return candidate
    return None


def discover(roots=None):
    """Find MUIOGO, OG country models, and the link already installed on this machine.

    The installer creates its own workspace, but most people already have these
    checkouts somewhere. Adopting them avoids installing a second multi-gigabyte
    copy and pointing the tooling at the wrong one.
    """
    if roots is None:
        roots = [Path.home() / "Projects", CANONICAL_DIR / "og-models",
                 DEFAULT_WORKSPACE, Path.home()]
    found = {"muiogo": [], "og_models": [], "link": []}
    seen = set()
    for root in roots:
        root = Path(root).expanduser()
        if not root.is_dir():
            continue
        for child in sorted(root.iterdir()):
            try:
                if not child.is_dir() or child.resolve() in seen:
                    continue
                seen.add(child.resolve())
                if looks_like_muiogo(child):
                    found["muiogo"].append(child)
                elif looks_like_link(child):
                    found["link"].append(child)
                elif looks_like_og_model(child):
                    found["og_models"].append(child)
            except (OSError, PermissionError):
                continue
    return found


def _git_ref(path):
    import subprocess
    try:
        out = subprocess.run(["git", "-C", str(path), "rev-parse", "--short=8", "HEAD"],
                             capture_output=True, text=True, timeout=15)
        return out.stdout.strip() or None
    except (OSError, subprocess.SubprocessError):
        return None


def build_manifest(muiogo_path, og_models=(), link_path=None, port=5002, workspace=None):
    """A manifest describing installations that already exist on this machine."""
    import datetime
    import shutil
    muiogo_path = Path(muiogo_path)
    if not looks_like_muiogo(muiogo_path):
        raise WorkspaceError(f"{muiogo_path} does not look like a MUIOGO checkout "
                             f"(needs API/app.py and WebAPP/DataStorage)")
    models = []
    for path in og_models:
        path = Path(path)
        pkg = next((d.name for d in path.iterdir()
                    if d.is_dir() and d.name.startswith("og")
                    and (d / "__init__.py").is_file()), None)
        models.append({
            "key": f"og-{path.name.rsplit('-', 1)[-1].lower()}",
            "repo": path.name, "package": pkg, "path": str(path),
            "ref": _git_ref(path), "python": str(venv_python(path) or ""),
        })
    data_storage = muiogo_path / "WebAPP" / "DataStorage"
    cases = sorted(p.name for p in data_storage.iterdir()
                   if (p / "genData.json").is_file()) if data_storage.is_dir() else []
    return {
        "generated": datetime.datetime.now().isoformat(timespec="seconds"),
        "workspace": str(workspace or muiogo_path.parent),
        "adopted": True,
        "muiogo": {
            "path": str(muiogo_path), "ref": _git_ref(muiogo_path),
            "python": str(venv_python(muiogo_path) or ""),
            "url": f"http://127.0.0.1:{port}", "port": int(port),
            "og_models_dir": str(CANONICAL_DIR / "og-models"),
            "og_state_dir": str(CANONICAL_DIR / "og-state"),
        },
        "muiogo_ai": {"path": None, "ref": None, "client_python": None},
        "ogclews_link": ({"path": str(link_path), "ref": _git_ref(link_path),
                          "python": str(venv_python(link_path) or "")}
                         if link_path else {"path": None, "ref": None, "python": None}),
        "og_models": models,
        "clews_cases": [{"key": None, "case": c} for c in cases],
        "solvers": {"glpsol": shutil.which("glpsol"), "cbc": shutil.which("cbc")},
    }


def adopt(muiogo_path, og_models=(), link_path=None, port=5002):
    """Record existing installations as the workspace. Returns (path, manifest)."""
    manifest = build_manifest(muiogo_path, og_models, link_path, port)
    CANONICAL_DIR.mkdir(parents=True, exist_ok=True)
    dest = CANONICAL_DIR / MANIFEST_NAME
    dest.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    return dest, manifest


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
