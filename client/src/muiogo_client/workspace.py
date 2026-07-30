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

# ── How a command knows which world it is acting on ──────────────────────────
#
# Not from a stored pointer. A pointer is shared mutable state: anything can
# change it, it persists across shells and days, and a command that reads it
# cannot tell whether the value was meant for this invocation. The world is
# instead a property of the launcher you executed. The installer generates
# <install>/bin/muiogo-ai carrying this variable as an absolute literal, so the
# world travels to every child process — including a skill's python script,
# which is where the writes that matter actually happen.
WORLD_FILE_ENV = "MUIOGO_WORLD_FILE"

# Each world also keeps its own run-state. These used to be one shared
# directory under ~/.muiogo, which made pidfiles, the OG registry and the model
# directory common property between the user's manual setup and the automated
# runtime — the exact collision the two-world split exists to prevent.
STATE_HOME_ENV = "MUIOGO_HOME"

# Two worlds are expected to coexist on one machine and must not contend:
#   - an ADOPTED world: checkouts someone uses for live work, on its own branches
#   - an INSTALLED world: a self-contained runtime the installer built
# They get different default ports so a command can never silently drive the wrong
# server, and each manifest records which kind it is.
LIVE_PORT = 5002        # adopted world: MUIOGO's own default
RUNTIME_PORT = 5102     # installed world: deliberately not MUIOGO's default

CANONICAL_DIR = Path.home() / ".muiogo"

# The install directory is deliberately NOT called muiogo-ai. This repository is
# MUIOGO-AI, and on a case-insensitive filesystem — macOS's default — the two
# names are one directory. Cloning the repo into $HOME then made the installer
# unpack MUIOGO and several gigabytes of models into the git checkout, where a
# later `git clean` would delete them. "muiogoai" cannot collide, and is kept
# all-lowercase because mixed case works on macOS and fails on Linux.
DEFAULT_WORKSPACE = Path.home() / "muiogoai"
LEGACY_WORKSPACES = (Path.home() / "muiogo-ai",
                     Path.home() / "muiogo-ai-workspace")
LEGACY_WORKSPACE = LEGACY_WORKSPACES[0]      # kept for older callers

# One record PER WORLD, never one shared slot. A single canonical manifest meant
# that installing a runtime overwrote the only record of the adopted world — and
# re-adopting to recover clobbered the runtime's record in the other direction,
# with no way out but hand-editing JSON. Each world now owns a file, and a
# separate pointer says which is active.
WORLDS_DIR = CANONICAL_DIR / "worlds"          # default only; see worlds_dir()
_ACTIVE_NAME = "active"
LEGACY_MANIFEST = CANONICAL_DIR / MANIFEST_NAME


def state_root():
    """This world's own state directory. Never assume the shared default."""
    override = os.environ.get(STATE_HOME_ENV)
    return Path(override).expanduser() if override else CANONICAL_DIR


def worlds_dir():
    """Where world RECORDS live — machine-wide, deliberately not per-world.

    The catalogue must be shared even though every world's contents are
    isolated. A world that can only see its own record cannot tell that a path
    belongs to another world, so the cross-world guard silently passes and the
    crossing it exists to stop goes through. Isolation belongs to state
    (pidfiles, the OG registry, models) — not to the list of what exists.
    """
    return CANONICAL_DIR / "worlds"


def servers_dir():
    return state_root() / "servers"


def pinned_world_file():
    """The manifest a launcher baked in, if we were launched by one."""
    raw = os.environ.get(WORLD_FILE_ENV)
    if not raw:
        return None
    path = Path(raw).expanduser()
    if not path.is_file():
        raise WorkspaceError(
            f"{WORLD_FILE_ENV} points at {path}, which does not exist. This is "
            f"set by a generated launcher; if you moved or removed the "
            f"installation, re-run the installer or unset {WORLD_FILE_ENV}.")
    return path


class World:
    """One world, resolved once. Every path a command needs comes from here.

    The point of the class is that url, port, DataStorage and the OG registry
    are read off a SINGLE manifest. They used to be resolved independently,
    which let one command act on two worlds at once: --url pointed the HTTP
    calls at one server while the filesystem reads still came from whichever
    world a pointer happened to name.
    """

    def __init__(self, data, path):
        self.data = data
        self.path = Path(path)

    @property
    def name(self):
        recorded = self.data.get("name")
        if recorded:
            return recorded
        stem = self.path.stem
        # A manifest inside an install directory is named for the install, not
        # for the file: "manifest" tells a reader nothing about which world.
        if stem in ("manifest", "world"):
            return self.path.parent.name
        return stem

    @property
    def kind(self):
        return describe_kind(self.data)[0]

    @property
    def muiogo_path(self):
        p = (self.data.get("muiogo") or {}).get("path")
        return Path(p) if p else None

    @property
    def port(self):
        return (self.data.get("muiogo") or {}).get("port")

    @property
    def url(self):
        u = (self.data.get("muiogo") or {}).get("url")
        if u:
            return u
        if self.port:
            return f"http://127.0.0.1:{self.port}"
        raise WorkspaceError(
            f"world {self.name!r} ({self.path}) records no port or url, so there "
            f"is nothing safe to talk to. Re-run the installer, or `muiogo adopt`.")

    @property
    def data_storage(self):
        if not self.muiogo_path:
            raise WorkspaceError(
                f"world {self.name!r} records no MUIOGO path, so its cases "
                f"cannot be located.")
        return self.muiogo_path / "WebAPP" / "DataStorage"

    @property
    def og_state_dir(self):
        d = (self.data.get("muiogo") or {}).get("og_state_dir")
        return Path(d) if d else state_root() / "og-state"

    @property
    def og_models_dir(self):
        d = (self.data.get("muiogo") or {}).get("og_models_dir")
        return Path(d) if d else state_root() / "og-models"

    def describe(self):
        return f"{self.name} ({self.kind}, port {self.port})"


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


def active_file():
    return state_root() / _ACTIVE_NAME


def world_file(name):
    return worlds_dir() / f"{name}.json"


def active_world():
    """Name of the world the tooling is currently pointed at, or None."""
    try:
        name = active_file().read_text(encoding="utf-8").strip()
    except OSError:
        return None
    return name if name and world_file(name).is_file() else None


def known_worlds():
    """Every registered world: {name: path}, newest naming wins."""
    if not worlds_dir().is_dir():
        return {}
    return {p.stem: p for p in sorted(worlds_dir().glob("*.json"))}


def register_world(name, manifest, make_active=True):
    """Record a world under its own name. Never disturbs another world's record."""
    worlds_dir().mkdir(parents=True, exist_ok=True)
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
    active_file().write_text(f"{name}\n", encoding="utf-8")
    # Kept in step for anything still reading the old single-slot location.
    try:
        LEGACY_MANIFEST.write_text(world_file(name).read_text(encoding="utf-8"),
                                   encoding="utf-8")
    except OSError:
        pass
    return name


def resolve(start=None):
    """The one place a world is chosen. Returns a World.

    Order: the launcher's baked-in manifest, then $MUIOGO_WORKSPACE, then the
    active pointer and the search path. There is deliberately no "whatever
    single world exists" fallback and no default port: losing a world record
    used to mean silently switching to the live world, which is the user's own
    manual setup.
    """
    pinned = pinned_world_file()
    if pinned is not None:
        return World(_read_manifest(pinned), pinned)
    data, path = load(start)
    return World(data, path)


POSIX_LAUNCHER = """#!/bin/sh
# Generated by MUIOGO-AI. Do not edit — re-run the installer to regenerate.
#
# This file IS the world. The two paths below are absolute literals, so every
# command run through this launcher — and every child process it starts,
# including a skill's python script — acts on this installation and no other.
# Nothing outside this file can retarget it: there is no pointer to change.
MUIOGO_WORLD_FILE={world_file}
MUIOGO_HOME={state_home}
export MUIOGO_WORLD_FILE MUIOGO_HOME
exec {muiogo} "$@"
"""

WINDOWS_LAUNCHER = """@echo off
rem Generated by MUIOGO-AI. Do not edit — re-run the installer to regenerate.
rem This file IS the world: the paths below are absolute literals.
set "MUIOGO_WORLD_FILE={world_file}"
set "MUIOGO_HOME={state_home}"
"{muiogo}" %*
"""


def write_launcher(path, world_file, state_home, muiogo_exe=None):
    """Write a launcher that pins one world, and return the path written.

    A launcher beats every other way of selecting a world because the choice is
    made by WHICH FILE YOU RAN, before any code executes. An environment
    variable can be stale, a working directory can be wrong, and a stored
    pointer is shared mutable state — but the literal inside this file cannot be
    anything other than what the installer wrote.
    """
    import shutil
    import sys as _sys
    path = Path(path)
    exe = muiogo_exe or shutil.which("muiogo") or (Path(_sys.prefix) / "bin" / "muiogo")
    body = (WINDOWS_LAUNCHER if os.name == "nt" else POSIX_LAUNCHER).format(
        world_file=_quote(world_file), state_home=_quote(state_home),
        muiogo=_quote(exe) if os.name != "nt" else exe)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(body)
    if os.name != "nt":
        path.chmod(0o755)
    return path


def _quote(value):
    """Shell-quote an absolute path so a space in it cannot split the command."""
    import shlex
    return shlex.quote(str(value))


def owning_world(path):
    """Which registered world's MUIOGO tree contains `path`, if any.

    Path containment is the only reliable test for "does this belong to another
    world". Ports do not distinguish worlds (two may share one) and names are
    labels. This is what lets a command notice it is about to touch someone
    else's installation before it does it.
    """
    try:
        target = Path(path).expanduser().resolve()
    except OSError:
        return None
    for name, record in known_worlds().items():
        try:
            world = World(_read_manifest(record), record)
        except WorkspaceError:
            continue
        root = world.muiogo_path
        if not root:
            continue
        try:
            root = root.resolve()
        except OSError:
            continue
        if target == root or root in target.parents:
            return world
    return None


def assert_same_world(path, world, what="that path"):
    """Refuse to touch a path that belongs to a DIFFERENT registered world.

    This is the backstop for the many ways a world can be crossed without the
    CLI's own resolution being involved at all — a skill addressing a case as a
    relative path, a --data-storage copied from another session, an absolute
    path pasted from notes. Crossing silently is the failure that matters,
    because the numbers still look right.
    """
    owner = owning_world(path)
    if owner is None or world is None:
        return
    if owner.path.resolve() == Path(world.path).resolve():
        return
    raise WorldCrossing(
        f"{what} is inside the {owner.describe()} world, but this command is "
        f"acting on {world.describe()}.\n"
        f"  path   {Path(path).expanduser()}\n"
        f"  owner  {owner.muiogo_path}\n"
        f"Refusing: work done here would be recorded against the wrong "
        f"installation. Use that world's own launcher instead.")


class WorldCrossing(RuntimeError):
    """A command was about to act on a different world's files."""


def world_for_root(root):
    """The registered world whose MUIOGO checkout is `root`, or None.

    Identity comes from the path on disk, which is the only thing that actually
    distinguishes two worlds. A port does not: both may use the same one.
    """
    root = Path(root).resolve()
    pinned = pinned_world_file()
    if pinned is not None:
        world = World(_read_manifest(pinned), pinned)
        if world.muiogo_path and world.muiogo_path.resolve() == root:
            return world
    for name, path in known_worlds().items():
        try:
            world = World(_read_manifest(path), path)
        except WorkspaceError:
            continue
        if world.muiogo_path and world.muiogo_path.resolve() == root:
            return world
    return None


def _read_manifest(path):
    try:
        return json.loads(Path(path).read_text())
    except (OSError, ValueError) as exc:
        raise WorkspaceError(f"cannot read the world record {path}: {exc}") from exc


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
    paths.extend(w / MANIFEST_NAME for w in LEGACY_WORKSPACES)
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


def _env_dir(muiogo_path, key, default):
    """What THIS checkout's .env says its OG registry is.

    MUIOGO reads these from its own .env via load_dotenv, so the checkout's file
    is the truth. Recording a guess here and then injecting it into the server
    is how an installed world ended up writing into the shared registry.
    """
    env = Path(muiogo_path) / ".env"
    if env.is_file():
        for line in env.read_text().splitlines():
            line = line.strip()
            if line.startswith(f"{key}=") and not line.startswith("#"):
                value = line.split("=", 1)[1].strip().strip('"').strip("'")
                if value:
                    return Path(value).expanduser()
    return Path(default)


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
            "og_models_dir": str(_env_dir(muiogo_path, "MUIOGO_OG_MODELS_DIR",
                                          state_root() / "og-models")),
            "og_state_dir": str(_env_dir(muiogo_path, "MUIOGO_OG_DATA_DIR",
                                         state_root() / "og-state")),
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
    """A flat, printable picture of THIS world, for orientation.

    Must go through resolve() so a launcher's baked-in world wins. Reading the
    search path directly meant `status` described one world while the same
    command's URL and DataStorage came from another — the most misleading
    failure available, because the output looks authoritative.
    """
    world = resolve(start)
    data, path = world.data, world.path
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
