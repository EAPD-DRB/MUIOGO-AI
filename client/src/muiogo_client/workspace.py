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
  3. ~/muiogo-ai/manifest.json                -- the installer's master directory
     (and ~/muiogo-ai-workspace, its former name)
  4. ./manifest.json, walking up to the root  -- you are inside a workspace
"""
import json
import os
from pathlib import Path

MANIFEST_NAME = "manifest.json"

# Two worlds are expected to coexist on one machine and must not contend:
#   - an ADOPTED world: checkouts someone uses for live work, on its own branches
#   - an INSTALLED world: a self-contained runtime the installer built
# They get different default ports so a command can never silently drive the wrong
# server, and each manifest records which kind it is.
LIVE_PORT = 5002        # adopted world: MUIOGO's own default
RUNTIME_PORT = 5102     # installed world: deliberately not MUIOGO's default

CANONICAL_DIR = Path.home() / ".muiogo"
DEFAULT_WORKSPACE = Path.home() / "muiogo-ai"
LEGACY_WORKSPACE = Path.home() / "muiogo-ai-workspace"

# One record PER WORLD, never one shared slot. A single canonical manifest meant
# that installing a runtime overwrote the only record of the adopted world — and
# re-adopting to recover clobbered the runtime's record in the other direction,
# with no way out but hand-editing JSON. Each world now owns a file, and a
# separate pointer says which is active.
WORLDS_DIR = CANONICAL_DIR / "worlds"
ACTIVE_FILE = CANONICAL_DIR / "active"
LEGACY_MANIFEST = CANONICAL_DIR / MANIFEST_NAME


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


def world_file(name):
    return WORLDS_DIR / f"{name}.json"


def active_world():
    """Name of the world the tooling is currently pointed at, or None."""
    try:
        name = ACTIVE_FILE.read_text(encoding="utf-8").strip()
    except OSError:
        return None
    return name if name and world_file(name).is_file() else None


def known_worlds():
    """Every registered world: {name: path}, newest naming wins."""
    if not WORLDS_DIR.is_dir():
        return {}
    return {p.stem: p for p in sorted(WORLDS_DIR.glob("*.json"))}


def register_world(name, manifest, make_active=True):
    """Record a world under its own name. Never disturbs another world's record."""
    WORLDS_DIR.mkdir(parents=True, exist_ok=True)
    path = world_file(name)
    path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    if make_active:
        set_active(name)
    return path


def set_active(name):
    """Point the tooling at a registered world."""
    if not world_file(name).is_file():
        raise WorkspaceError(f"no world named {name!r} (have: {', '.join(known_worlds()) or 'none'})")
    CANONICAL_DIR.mkdir(parents=True, exist_ok=True)
    ACTIVE_FILE.write_text(f"{name}\n", encoding="utf-8")
    # Kept in step for anything still reading the old single-slot location.
    try:
        LEGACY_MANIFEST.write_text(world_file(name).read_text(encoding="utf-8"),
                                   encoding="utf-8")
    except OSError:
        pass
    return name


def candidate_paths(start=None):
    """Every place a manifest might live, in search order."""
    paths = []
    env = os.environ.get("MUIOGO_WORKSPACE", "").strip()
    if env:
        paths.append(Path(env).expanduser() / MANIFEST_NAME)
    active = active_world()
    if active:
        paths.append(world_file(active))
    paths.extend(known_worlds().values())
    paths.append(LEGACY_MANIFEST)
    paths.append(DEFAULT_WORKSPACE / MANIFEST_NAME)
    paths.append(LEGACY_WORKSPACE / MANIFEST_NAME)
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


def publish(manifest_path, name=None, make_active=True):
    """Register a workspace as a named world so it can be found from anywhere.

    Registers under its own name rather than overwriting a shared slot, so
    installing a runtime can never destroy the record of an adopted world.
    Returns the registered path, or None if it could not be written.
    """
    src = Path(manifest_path)
    try:
        data = json.loads(src.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None
    if name is None:
        kind, _ = describe_kind(data)
        name = "runtime" if kind == "installed" else "live"
    try:
        return register_world(name, data, make_active=make_active)
    except OSError:
        return None


# OG country models are named OG-<ISO3> and hold a package og<iso3>; the library
# they all build on is OG-Core / ogcore. Anything that does not resolve to a
# three-letter country code is not a country model.
_NOT_A_COUNTRY = {"CORE", "USA-CORE"}


def country_code(path, package=None):
    """The ISO3 country code of an OG country model, or None if it isn't one."""
    for candidate in (package[2:] if package and len(package) > 2 else None,
                      Path(path).name.rsplit("-", 1)[-1]):
        if candidate and len(candidate) == 3 and candidate.isalpha():
            code = candidate.upper()
            if code not in _NOT_A_COUNTRY:
                return code
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
                 DEFAULT_WORKSPACE, LEGACY_WORKSPACE, Path.home()]
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


def build_manifest(muiogo_path, og_models=(), link_path=None, port=LIVE_PORT,
                   workspace=None, kind="adopted"):
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
        # OG-Core is the shared library every country model depends on, not a
        # country model. Splitting its name on "-" yields "core", which would
        # otherwise be recorded as a country with the code CORE and offered for
        # registration as if a country called Core existed.
        if not country_code(path, pkg):
            continue
        models.append({
            "key": f"og-{country_code(path, pkg).lower()}",
            "country_id": country_code(path, pkg),
            "repo": path.name, "package": pkg, "path": str(path),
            "ref": _git_ref(path), "python": str(venv_python(path) or ""),
        })
    data_storage = muiogo_path / "WebAPP" / "DataStorage"
    cases = sorted(p.name for p in data_storage.iterdir()
                   if (p / "genData.json").is_file()) if data_storage.is_dir() else []
    return {
        "generated": datetime.datetime.now().isoformat(timespec="seconds"),
        "workspace": str(workspace or muiogo_path.parent),
        "kind": kind,
        "adopted": kind == "adopted",
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


def adopt(muiogo_path, og_models=(), link_path=None, port=LIVE_PORT, name="live"):
    """Register existing installations as a named world. Returns (path, manifest).

    Writes only that world's own record, so an installed runtime registered
    separately is untouched.
    """
    manifest = build_manifest(muiogo_path, og_models, link_path, port)
    return register_world(name, manifest), manifest


def describe_kind(data):
    """A short, honest label for which world a manifest describes."""
    kind = data.get("kind") or ("adopted" if data.get("adopted") else "installed")
    if kind == "adopted":
        return "adopted", "your own checkouts, used for live work"
    return "installed", "a self-contained runtime built by the installer"


def list_workspaces(start=None):
    """Every workspace manifest on this machine, so the active one is visible.

    Without this, which world a command acts on is implicit — whichever manifest
    the search order happened to reach first.
    """
    active = find_manifest(start)
    names = {v.resolve(): k for k, v in known_worlds().items()}
    # The legacy single-slot file is a mirror of the active world, not a world of
    # its own — listing it would show a phantom duplicate.
    skip = {LEGACY_MANIFEST.resolve()} if names else set()
    seen, out = set(), []
    for path in candidate_paths(start):
        if not path.is_file() or not _looks_like_manifest(path):
            continue
        real = path.resolve()
        if real in seen or real in skip:
            continue
        seen.add(real)
        try:
            with open(path, encoding="utf-8") as f:
                data = json.load(f)
        except (OSError, ValueError):
            continue
        kind, _ = describe_kind(data)
        muiogo = data.get("muiogo") or {}
        out.append({
            "manifest": str(path),
            "name": names.get(real, "(unregistered)"),
            "kind": kind,
            "workspace": data.get("workspace"),
            "muiogo_path": muiogo.get("path"),
            "port": muiogo.get("port"),
            "active": active is not None and path.resolve() == active.resolve(),
        })
    return out


def summary(start=None):
    """A flat, printable picture of the installation for orientation."""
    data, path = load(start)
    muiogo = data.get("muiogo") or {}
    link = data.get("ogclews_link") or {}
    kind, kind_note = describe_kind(data)
    return {
        "manifest": str(path),
        "kind": kind,
        "kind_note": kind_note,
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
