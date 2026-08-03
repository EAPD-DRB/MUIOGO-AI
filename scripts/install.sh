#!/usr/bin/env bash
# ──────────────────────────────────────────────────────────────────────────────
# MUIOGO-AI composed installer (macOS / Linux).
#
# Executes the three components' OWN upstream installers in turn — never
# reimplements them — then verifies the whole stack headless:
#
#   1. MUIOGO        via EAPD-DRB/MUIOGO scripts/install.sh   (app + solvers + demo)
#   2. OG model(s)   via PSLmodels/OG-Core scripts/install.sh (one env per model)
#   3. ogclews-link  via its scripts/setup.sh                 (own env, registers models)
#
# Then: registers OG models with MUIOGO (/ogc API), writes <workspace>/manifest.json,
# and refuses to call itself done until a verification battery passes (MUIOGO serves
# and solves the demo case with CBC; each OG model imports from its own venv;
# link --check passes).
#
# Zero-input and resume-safe: every step skips itself when already done.
#
# Usage:
#   ./scripts/install.sh [options]
# Options:
#   --dest DIR          Master directory for everything. Asked interactively
#                       when not given; the default is the already-registered
#                       installation if one exists, otherwise ~/muiogoai.
#   --country ISO3s     Comma-separated countries (PHL,...). Resolves BOTH sides
#                       by the ISO3 join: the OG model (og-<iso3>) via the
#                       upstream catalog AND the CLEWs case via clews/ manifests.
#   --og KEYS           Comma-separated OG models to install (og-phl,og-eth,...)
#                       from the upstream catalog. Default: none.
#   --clews KEYS        Comma-separated CLEWs countries (clews-phl,...) from
#                       clews/clews-repos.json; installs the recommended portable
#                       case into MUIOGO via its /uploadCase endpoint.
#   --case NAME         Override the recommended case (single --clews/--country only)
#   --og-home DIR       Where OG models and their registry live (default: inside
#                       --dest, keeping this installation self-contained)
#   --no-link           Skip ogclews-link
#   --no-demo-data      Pass through to the MUIOGO installer
#   --no-verify         Skip the final verification battery (discouraged)
#   --no-skills         Don't offer to install the skills at the end
#   --skills-tool KEY   Which assistant gets the skills: claude, codex, or both
#   -y, --yes           Auto-confirm every prompt (non-interactive). Skills are
#                       installed only when --skills-tool is also given.
#   --port N            Port for this installation (default 5102, so it never
#                       contends with a MUIOGO you run manually on 5002)
#   -h, --help          This message
# ──────────────────────────────────────────────────────────────────────────────
set -uo pipefail

MUIOGO_INSTALLER_URL="https://raw.githubusercontent.com/EAPD-DRB/MUIOGO/main/scripts/install.sh"
OG_INSTALLER_URL="https://raw.githubusercontent.com/PSLmodels/OG-Core/master/scripts/install.sh"
OG_CATALOG_URL="https://raw.githubusercontent.com/PSLmodels/OG-Core/master/scripts/repos.json"
LINK_REPO_URL="https://github.com/marcelolafleur/ogclews-link.git"
MUIOGO_AI_REPO_URL="https://github.com/EAPD-DRB/MUIOGO-AI.git"

DEST=""           # resolved in preflight: flag > prompt > registered world > ~/muiogoai
OG_KEYS=""
CLEWS_KEYS=""
COUNTRIES=""
CASE_OVERRIDE=""
OG_HOME=""      # defaults to the workspace; see below
WITH_LINK=1
NO_DEMO_DATA=0
NO_VERIFY=0
NO_SKILLS=0
SKILLS_TOOL=""
ASSUME_YES=0
PORT=5102        # the installed world; MUIOGO's own default 5002 is left to
                 # checkouts used for live work, so the two never contend

usage() {
    cat <<EOF
MUIOGO-AI composed installer (macOS and Linux).

Runs each component's own upstream installer in turn, then verifies the stack.

Usage:
  $0 [options]

Options:
  -h, --help              Show this message and exit.
  -y, --yes               Auto-confirm every prompt (non-interactive).
      --dest DIR          Master directory holding MUIOGO, the OG models, the
                          link and their registries. Asked interactively when
                          not given; defaults to the already-registered
                          installation if one exists, otherwise ~/muiogoai.
                          Kept separate from repos you use for live work.
      --country ISO3s     Countries to set up, comma-separated (e.g. PHL).
                          Resolves BOTH sides from the one key: the OG model
                          (og-<iso3>) and the CLEWs case.
      --og KEYS           OG models only (og-phl,og-eth,...); 'none' for none.
      --clews KEYS        CLEWs countries only (clews-phl,...).
      --case NAME         Use a specific CLEWs case instead of the recommended one.
      --og-home DIR       Where OG models and their registry live
                          (default: inside --dest, so nothing is shared).
      --no-link           Skip ogclews-link.
      --no-demo-data      Don't install MUIOGO's demo data.
      --no-verify         Skip the final verification battery (discouraged).
      --no-skills         Don't offer to install the skills at the end.
      --skills-tool KEY   Assistant for the skills: claude, codex, or both.
      --port N            Port for this installation (default 5102). MUIOGO's own
                          default 5002 is left free for checkouts you run yourself.

Examples:
  $0                                          # MUIOGO + solvers + demo data
  $0 --country PHL                            # add the Philippine OG + CLEWs pair
  $0 --country PHL --yes --skills-tool claude # hands-free, skills installed
  $0 --og og-zaf,og-idn --no-link             # two OG models, no link
EOF
}

while [[ $# -gt 0 ]]; do
    case "$1" in
        --dest)         DEST="$2";      shift 2 ;;
        --og)           OG_KEYS="$2";   shift 2 ;;
        --clews)        CLEWS_KEYS="$2"; shift 2 ;;
        --country)      COUNTRIES="$2"; shift 2 ;;
        --case)         CASE_OVERRIDE="$2"; shift 2 ;;
        --og-home)      OG_HOME="$2";   shift 2 ;;
        --no-link)      WITH_LINK=0;    shift ;;
        --no-demo-data) NO_DEMO_DATA=1; shift ;;
        --no-verify)    NO_VERIFY=1;    shift ;;
        --no-skills)    NO_SKILLS=1;    shift ;;
        --skills-tool)  SKILLS_TOOL="$2"; shift 2 ;;
        -y|--yes)       ASSUME_YES=1;   shift ;;
        --port)         PORT="$2";      shift 2 ;;
        -h|--help)      usage; exit 0 ;;
        *) echo "Unknown option: $1 (see --help)" >&2; exit 1 ;;
    esac
done
[[ "$OG_KEYS" == "none" ]] && OG_KEYS=""

# ── Colors (detect before any stdout redirect) ────────────────────────────────
if [[ -t 1 ]]; then
    BOLD="\033[1m"; DIM="\033[2m"
    RED="\033[91m"; GREEN="\033[92m"; YELLOW="\033[93m"; RESET="\033[0m"
else
    BOLD=""; DIM=""; RED=""; GREEN=""; YELLOW=""; RESET=""
fi

# ── Helpers ───────────────────────────────────────────────────────────────────
hr()       { printf '%s\n' "──────────────────────────────────────────────────────────────"; }
hr_thick() { printf '%s\n' "══════════════════════════════════════════════════════════════"; }

print_pass() { printf "  ${GREEN}[PASS]${RESET} %s%s\n" "$1" "${2:+  ${DIM}($2)${RESET}}"; }
print_fail() { printf "  ${RED}[FAIL]${RESET} %s%s\n" "$1" "${2:+  ${DIM}($2)${RESET}}"; }
print_warn() { printf "  ${YELLOW}[WARN]${RESET} %s%s\n" "$1" "${2:+  ${DIM}($2)${RESET}}"; }
print_skip() { printf "  ${YELLOW}[SKIP]${RESET} %s%s\n" "$1" "${2:+  ${DIM}($2)${RESET}}"; }
echo_cmd()   { printf "  ${DIM}$ %s${RESET}\n" "$*"; }

TOTAL_STEPS=5
step_banner() { echo; hr; printf "  ${BOLD}Step %s of %s: %s${RESET}\n" "$1" "$TOTAL_STEPS" "$2"; hr; }
section()     { echo; hr; printf "  ${BOLD}%s${RESET}\n" "$1"; hr; }

# Kept as short aliases so the step bodies stay readable.
ok()   { print_pass "$*"; }
skip() { print_skip "$*" "already done"; }
warn() { print_warn "$*"; }
die()  { printf "${RED}ERROR:${RESET} %s\n" "$*" >&2; record "$CURRENT_STEP" FAIL "$*"; report; exit 1; }

STEP_NAMES=(); STEP_STATES=(); STEP_DETAILS=(); CURRENT_STEP="preflight"
record() { STEP_NAMES+=("$1"); STEP_STATES+=("$2"); STEP_DETAILS+=("${3:-}"); }
report() {
    echo; hr_thick; printf "  ${BOLD}Install report${RESET}\n"; hr_thick
    local i
    for i in "${!STEP_NAMES[@]}"; do
        case "${STEP_STATES[$i]}" in
            OK)   print_pass "${STEP_NAMES[$i]}" "${STEP_DETAILS[$i]}" ;;
            SKIP) print_skip "${STEP_NAMES[$i]}" "${STEP_DETAILS[$i]}" ;;
            FAIL) print_fail "${STEP_NAMES[$i]}" "${STEP_DETAILS[$i]}" ;;
            *)    print_warn "${STEP_NAMES[$i]}" "unknown state" ;;
        esac
    done
}

# Ask a yes/no question on the terminal. --yes auto-confirms; with no terminal
# the caller's default stands (writing into someone's home is never implicit).
prompt_yn() {
    local prompt="$1" default="${2:-n}" opts ans
    if [ "$default" = "y" ]; then opts="[Y/n]"; else opts="[y/N]"; fi
    if [[ $ASSUME_YES -eq 1 ]]; then
        printf "  %s %s ${DIM}(auto: yes)${RESET}\n" "$prompt" "$opts"
        return 0
    fi
    if [ ! -r /dev/tty ]; then
        return 1
    fi
    while true; do
        printf "  %s %s " "$prompt" "$opts" > /dev/tty
        IFS= read -r ans < /dev/tty || ans="$default"
        [[ -z "$ans" ]] && ans="$default"
        case "$(echo "$ans" | tr '[:upper:]' '[:lower:]')" in
            y|yes) return 0 ;;
            n|no)  return 1 ;;
            *)     printf "  Please answer Y or N.\n" > /dev/tty ;;
        esac
    done
}

# Run a command with venv/conda markers stripped: both upstream installers
# refuse (or misbehave) inside an active environment.
clean_env() { env -u VIRTUAL_ENV -u CONDA_DEFAULT_ENV -u CONDA_PREFIX -u CONDA_SHLVL "$@"; }

# The cleanup lists exist before anything is created, so nothing can be added
# to them and then wiped by a later declaration.
CLEANUP_PATHS=()
CLEANUP_FILES=()

# No-op `open`/`xdg-open` shim so the MUIOGO installer's auto-start can't pop
# a browser. The auto-start itself is absorbed as our health probe.
SHIM_DIR="$(mktemp -d)"
CLEANUP_PATHS+=("$SHIM_DIR")
for cmd in open xdg-open; do
    printf '#!/bin/sh\nexit 0\n' > "$SHIM_DIR/$cmd" && chmod +x "$SHIM_DIR/$cmd"
    CLEANUP_FILES+=("$SHIM_DIR/$cmd")
done

# Port checks go through python3 (already a requirement) rather than lsof, which
# does not exist on Windows or in Git Bash.
port_busy() {
    python3 - "$PORT" <<'PYEOF' 2>/dev/null
import socket, sys
s = socket.socket()
s.settimeout(1)
sys.exit(0 if s.connect_ex(("127.0.0.1", int(sys.argv[1]))) == 0 else 1)
PYEOF
}
server_pid() { lsof -ti ":$PORT" 2>/dev/null | head -1; }
stop_server() {
    # Prefer the pid we recorded; fall back to a port lookup only where lsof exists.
    local pidfile="$HOME/.muiogo/servers/port-$PORT.pid"
    if [[ -f "$pidfile" ]]; then
        kill "$(cat "$pidfile")" 2>/dev/null && rm -f "$pidfile" && sleep 1 && return 0
    fi
    if command -v lsof >/dev/null; then
        local pid; pid="$(server_pid)"
        [[ -n "$pid" ]] && kill "$pid" 2>/dev/null && sleep 1
    fi
    return 0
}

# Nothing we create should outlive a failure: not the verification server, not the
# scratch directories. die() exits without unwinding, so this has to be a trap.
# Scratch dirs are removed with rmdir, never recursively. rmdir refuses to touch
# a non-empty directory, so a wrong path here cannot destroy anything: the worst
# case is a leftover directory, which is reported rather than forced.
cleanup() {
    stop_server
    local f p
    for f in ${CLEANUP_FILES[@]+"${CLEANUP_FILES[@]}"}; do
        [[ -n "$f" && -f "$f" ]] && rm -f "$f"
    done
    for p in ${CLEANUP_PATHS[@]+"${CLEANUP_PATHS[@]}"}; do
        [[ -n "$p" && -d "$p" ]] || continue
        rmdir "$p" 2>/dev/null || printf '  note: left %s in place (not empty)\n' "$p" >&2
    done
    return 0
}
trap cleanup EXIT
api() { curl -s -m "${2:-10}" "http://127.0.0.1:${PORT}${1}"; }
wait_api() { # wait_api SECONDS — until /getCases answers
    local deadline=$(( $(date +%s) + $1 ))
    while [[ $(date +%s) -lt $deadline ]]; do
        [[ -n "$(api /getCases 5)" ]] && return 0
        sleep 2
    done
    return 1
}

# shasum is on macOS, sha256sum on most Linux; python3 is already required, so
# it is the one thing guaranteed present on both.
sha256_of() {
    [[ -f "$1" ]] || { echo "absent"; return 0; }
    python3 - "$1" <<'PYHASH'
import hashlib, sys
h = hashlib.sha256()
with open(sys.argv[1], "rb") as fh:
    for chunk in iter(lambda: fh.read(1 << 20), b""):
        h.update(chunk)
print(h.hexdigest())
PYHASH
}

# Two paths can name ONE directory. macOS's default filesystem is
# case-insensitive, so $HOME/muiogo-ai and $HOME/MUIOGO-AI are the same place —
# but `cd` + `pwd` echoes back whichever case you asked for, so comparing the
# strings says they differ. Only the device+inode tells the truth.
same_dir() {
    [[ -d "$1" && -d "$2" ]] || return 1
    python3 - "$1" "$2" <<'PYSAME'
import os, sys
try:
    sys.exit(0 if os.path.samefile(sys.argv[1], sys.argv[2]) else 1)
except OSError:
    sys.exit(1)
PYSAME
}

# Is this path inside a git working tree? Installing gigabytes of model data into
# one is a trap: `git clean -fdx` in that checkout would delete every model, and
# the repo's .gitignore was never written to cover them.
git_tree_of() {
    git -C "$1" rev-parse --show-toplevel 2>/dev/null
}

# `read` does not expand ~, and a relative answer means "relative to here".
expand_path() {
    local p="$1"
    case "$p" in
        "~")   p="$HOME" ;;
        "~/"*) p="$HOME/${p#\~/}" ;;
    esac
    case "$p" in
        /*) : ;;
        *)  p="$(pwd)/$p" ;;
    esac
    printf '%s\n' "$p"
}

# The workspace of an already-registered 'runtime' world, if it still exists.
# Installing somewhere new while one exists would not be a fresh install: it
# would build a second multi-gigabyte world AND repoint the 'runtime' name at
# it, quietly orphaning the first. So an existing world is the default answer —
# re-running into it is safe, finished steps skip themselves.
runtime_world_dir() {
    local wf="$HOME/.muiogo/worlds/runtime.json"
    [[ -f "$wf" ]] || return 1
    python3 - "$wf" <<'PYWORLD'
import json, os, sys
try:
    ws = json.load(open(sys.argv[1])).get("workspace") or ""
except (OSError, ValueError):
    sys.exit(1)
if ws and os.path.isdir(ws):
    print(ws)
else:
    sys.exit(1)
PYWORLD
}

# ── preflight ─────────────────────────────────────────────────────────────────
CURRENT_STEP="preflight"
section "Preflight"
for tool in git curl python3; do
    command -v "$tool" >/dev/null || die "'$tool' is required — install it and re-run."
done
[[ -n "${VIRTUAL_ENV:-}${CONDA_DEFAULT_ENV:-}" ]] && warn "active venv/conda detected — component installers run with a cleaned environment"
port_busy && die "port $PORT is already in use — stop that server or pass --port"

# ── where the installation lives ──────────────────────────────────────────────
# Flag > prompt > default. The default is the already-registered installation
# when one exists (see runtime_world_dir), otherwise ~/muiogoai. Every source of
# the answer — flag, typed, defaulted — flows through the same expansion and
# the same safety checks below.
DEFAULT_DEST="${HOME}/muiogoai"
PREV_WORLD="$(runtime_world_dir)" || PREV_WORLD=""
[[ -n "$PREV_WORLD" ]] && DEFAULT_DEST="$PREV_WORLD"
if [[ -z "$DEST" ]]; then
    if [[ $ASSUME_YES -eq 1 || ! -r /dev/tty ]]; then
        DEST="$DEFAULT_DEST"
        ok "install location: $DEST (default)"
    else
        echo "  Everything installs into one directory: MUIOGO, the country models,"
        echo "  and about 4 GB of data. The location is permanent — it cannot be"
        echo "  moved later without reinstalling."
        if [[ -n "$PREV_WORLD" ]]; then
            echo "  An installation is already registered at $PREV_WORLD —"
            echo "  press Enter to reuse it (finished steps are skipped)."
        fi
        printf "  Install where? [%s] " "$DEFAULT_DEST" > /dev/tty
        IFS= read -r DEST_ANSWER < /dev/tty || DEST_ANSWER=""
        DEST="${DEST_ANSWER:-$DEFAULT_DEST}"
    fi
fi
DEST="$(expand_path "$DEST")"

# A non-empty directory that is not a previous installation is somebody's data;
# unpacking an app tree into the middle of it is not ours to decide. A previous
# installation is recognised by its manifest, its MUIOGO checkout, or — for an
# install that died before either existed — the og-models/og-state pair this
# script creates first.
if [[ -d "$DEST" && -n "$(ls -A "$DEST" 2>/dev/null)" \
      && ! -f "$DEST/manifest.json" && ! -d "$DEST/MUIOGO" \
      && ! ( -d "$DEST/og-models" && -d "$DEST/og-state" ) ]]; then
    warn "$DEST already exists and does not look like a MUIOGO-AI installation:"
    ls -A "$DEST" 2>/dev/null | head -5 | sed 's/^/        /'
    if ! prompt_yn "Install into it anyway?" n; then
        echo "      Nothing installed. Pick another directory with --dest, or re-run and type one."
        exit 0
    fi
fi

# A full install writes roughly 4 GB. Finding that out after 20 minutes of
# cloning wastes the user's time and leaves a half-tree to clean up.
FREE_MB="$(df -Pm "$(dirname "$DEST")" 2>/dev/null | awk 'NR==2 {print $4}')"
if [[ -n "$FREE_MB" ]]; then
    if   (( FREE_MB < 5000 )); then die "only $((FREE_MB/1024)) GB free on $(dirname "$DEST") — a full install needs about 4 GB, plus room to work."
    elif (( FREE_MB < 8000 )); then warn "$((FREE_MB/1024)) GB free — enough to install, but tight for model runs."
    fi
fi

# Fingerprint the registry World 1 uses. The whole point of this installation is
# that it keeps its own; if that fingerprint changes, isolation has failed and
# the user's manual setup has been altered behind their back.
SHARED_REGISTRY="${HOME}/.muiogo/og-state/og_calibrations_installed.json"
SHARED_REGISTRY_BEFORE=""
[[ -f "$SHARED_REGISTRY" ]] && SHARED_REGISTRY_BEFORE="$(sha256_of "$SHARED_REGISTRY")"
mkdir -p "$DEST"
DEST="$(cd "$DEST" && pwd)"
# Everything this installer creates lives under one directory, so it never
# competes with checkouts you use for live work — including MUIOGO's OG registry,
# which holds only one entry per country and would otherwise displace yours.
# Derived HERE, after the prompt, so a typed destination carries the registry
# with it instead of leaving it pointing at the compile-time default.
[[ -z "$OG_HOME" ]] && OG_HOME="$DEST"
OG_HOME="$(expand_path "$OG_HOME")"
mkdir -p "$OG_HOME/og-models" "$OG_HOME/og-state"
OG_HOME="$(cd "$OG_HOME" && pwd)"
ok "workspace: $DEST"

# ── the installation must not land inside the source checkout ─────────────────
THIS_REPO="$(cd "$(dirname "${BASH_SOURCE[0]:-$0}")/.." && pwd)"
if same_dir "$DEST" "$THIS_REPO"; then
    err_lines=(
        "the install directory and this repository are the SAME directory."
        ""
        "  install target : $DEST"
        "  this checkout  : $THIS_REPO"
        ""
        "On macOS these differ only by capitalisation, and the filesystem treats"
        "them as one place. Installing here would unpack MUIOGO, the country"
        "models and about 4 GB of data straight into the git checkout, where a"
        "later \`git clean\` or \`git pull\` could destroy them."
        ""
        "Pick a separate directory — nothing is moved or deleted:"
        "    ./scripts/install.sh --dest ~/muiogoai-2 $*"
        ""
        "Or move this checkout somewhere else first, for example ~/Projects,"
        "and run it again from there."
    )
    printf '  %s\n' "${err_lines[@]}" >&2
    die "refusing to install into the source checkout"
fi

# Even a DIFFERENT directory is unsafe if it sits inside a git working tree.
DEST_TREE="$(git_tree_of "$DEST")"
if [[ -n "$DEST_TREE" ]]; then
    warn "$DEST is inside the git repository at $DEST_TREE"
    echo "        Model data does not belong in a checkout: \`git clean -fdx\` there"
    echo "        would delete it, and \`git status\` will be permanently noisy."
    echo "        A directory outside any repository is safer, e.g. --dest ~/muiogoai-2"
    if ! prompt_yn "Install into a git working tree anyway?" n; then
        echo "      Nothing installed."
        exit 0
    fi
fi

# Do not silently build a second copy of things the user already has. A country
# model is 1-3 GB, and two checkouts of the same model is worse than none: the
# tooling can end up pointing at whichever one you did not mean.
EXISTING="$(ls -d "$HOME"/Projects/MUIOGO "$HOME"/Projects/OG-* "$HOME"/Projects/ogclews-link 2>/dev/null | head -12)"
if [[ -n "$EXISTING" && ! -d "$DEST/MUIOGO" ]]; then
    warn "you already have model checkouts on this machine:"
    printf '%s\n' "$EXISTING" | sed 's/^/        /'
    echo "      Installing will create SEPARATE copies in $DEST."
    echo "      To use the ones you have instead, stop here and run:"
    echo_cmd "muiogo adopt --auto"
    if ! prompt_yn "Continue and install fresh copies anyway?" n; then
        echo "      Nothing installed. Adopt what you have with: muiogo adopt --auto"
        exit 0
    fi
fi
record preflight OK "$DEST"

# ── 1. MUIOGO-AI (this repo: client + skills) ────────────────────────────────
CURRENT_STEP="muiogo-ai"
step_banner "1" "MUIOGO-AI (client + skills)"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]:-$0}")" && pwd)"
if [[ -f "$SCRIPT_DIR/../client/pyproject.toml" ]]; then
    AI_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
    ok "running from checkout: $AI_DIR"
else
    AI_DIR=""
fi
command -v uv >/dev/null || { curl -LsSf https://astral.sh/uv/install.sh | sh >/dev/null 2>&1; export PATH="$HOME/.local/bin:$PATH"; }

# The installed world carries its OWN copy of this repo and its own client
# venv, and everything that drives the world runs from there. Nothing is
# installed into the user's shared tools: a `muiogo` command they already have
# is theirs and is never overwritten, and this world stays intact if their
# checkout or their tools change. `muiogo-ai` (written at the end) is the one
# handle on this installation.
RUNTIME_AI_DIR="$DEST/MUIOGO-AI"
if [[ -n "$AI_DIR" ]] && same_dir "$AI_DIR" "$RUNTIME_AI_DIR"; then
    RUNTIME_AI_DIR="$AI_DIR"
    skip "runtime copy (the installer already runs from it)"
elif [[ -d "$RUNTIME_AI_DIR/.git" ]]; then
    # Resuming: refresh from the invoking checkout when there is one, so the
    # runtime copy matches the installer that is running. Never force it.
    if [[ -n "$AI_DIR" && -d "$AI_DIR/.git" ]]; then
        git -C "$RUNTIME_AI_DIR" pull --ff-only --quiet "$AI_DIR" 2>/dev/null \
            || warn "could not fast-forward $RUNTIME_AI_DIR from $AI_DIR — continuing with what is there"
    fi
    skip "runtime copy"
else
    if [[ -n "$AI_DIR" && -d "$AI_DIR/.git" ]]; then
        git clone --quiet "$AI_DIR" "$RUNTIME_AI_DIR" \
            || die "could not clone the runtime copy from $AI_DIR"
        # The copy must outlive the checkout it came from: record the canonical
        # repository as origin, so the world stays self-describing even if the
        # checkout moves or disappears.
        git -C "$RUNTIME_AI_DIR" remote set-url origin "$MUIOGO_AI_REPO_URL"
        [[ -n "$(git -C "$AI_DIR" status --porcelain 2>/dev/null | head -1)" ]] \
            && warn "your checkout has uncommitted changes — they are not part of the runtime copy"
    else
        git clone --quiet "$MUIOGO_AI_REPO_URL" "$RUNTIME_AI_DIR" \
            || die "could not clone MUIOGO-AI (private repo: authenticate git/gh first)"
    fi
    ok "runtime copy: $RUNTIME_AI_DIR"
fi
# Config (the pin, the CLEWs manifests, the skills) reads from the invoking
# checkout so it matches this running installer; without one, from the copy.
[[ -z "$AI_DIR" ]] && AI_DIR="$RUNTIME_AI_DIR"
( cd "$RUNTIME_AI_DIR/client" && clean_env uv sync -q ) || die "uv sync failed in $RUNTIME_AI_DIR/client"
RUNTIME_MUIOGO="$RUNTIME_AI_DIR/client/.venv/bin/muiogo"
[[ -x "$RUNTIME_MUIOGO" ]] || RUNTIME_MUIOGO="$RUNTIME_AI_DIR/client/.venv/Scripts/muiogo.exe"
[[ -x "$RUNTIME_MUIOGO" ]] || die "client env has no muiogo command at $RUNTIME_AI_DIR/client/.venv"
ok "client env ready ($RUNTIME_MUIOGO)"
record muiogo-ai OK "$RUNTIME_AI_DIR"

# --country ISO3: resolve both sides by the join key. OG side becomes og-<iso3>
# (validated against the upstream catalog in step 3); CLEWs side requires a
# manifest at clews/countries/<ISO3>.json.
if [[ -n "$COUNTRIES" ]]; then
    IFS=',' read -ra CC <<< "$COUNTRIES"
    for c in "${CC[@]}"; do
        c="$(echo "$c" | tr -d '[:space:]' | tr '[:lower:]' '[:upper:]')"
        [[ -f "$AI_DIR/clews/countries/$c.json" ]] || die "no CLEWs manifest for $c (clews/countries/$c.json)"
        lc="$(echo "$c" | tr '[:upper:]' '[:lower:]')"
        OG_KEYS="${OG_KEYS:+$OG_KEYS,}og-$lc"
        CLEWS_KEYS="${CLEWS_KEYS:+$CLEWS_KEYS,}clews-$lc"
    done
    ok "country resolution: og=[$OG_KEYS] clews=[$CLEWS_KEYS]"
fi

# ── 2. MUIOGO via its upstream installer ─────────────────────────────────────
CURRENT_STEP="muiogo"
step_banner "2" "MUIOGO (upstream installer: app + solvers + demo data)"
MUIOGO_DIR="$DEST/MUIOGO"
MUIOGO_PIN_FILE="$AI_DIR/scripts/MUIOGO_PIN"
MUIOGO_WAS_HERE=0
if [[ -x "$MUIOGO_DIR/.venv/bin/python" && -f "$MUIOGO_DIR/API/app.py" ]]; then
    skip "MUIOGO install"
    MUIOGO_WAS_HERE=1
    record muiogo SKIP "$MUIOGO_DIR"
else
    TMP_INST="$(mktemp -d)/muiogo-install.sh"
    CLEANUP_FILES+=("$TMP_INST")
    CLEANUP_PATHS+=("$(dirname "$TMP_INST")")
    curl -fsSL "$MUIOGO_INSTALLER_URL" -o "$TMP_INST" || die "could not fetch the MUIOGO installer"
    EXTRA=(); [[ $NO_DEMO_DATA -eq 1 ]] && EXTRA+=("--no-demo-data")
    # --yes auto-starts the app (no --no-start upstream yet). We absorb that:
    # browser suppressed by the shim; the serving port is our success probe.
    LOG="$DEST/muiogo-install.log"
    PATH="$SHIM_DIR:$PATH" PORT="$PORT" clean_env bash "$TMP_INST" --dest "$DEST" --yes ${EXTRA[@]+"${EXTRA[@]}"} > "$LOG" 2>&1 &
    INSTALL_BASH_PID=$!
    echo "  installing (log: $LOG) — this takes a few minutes on first run"
    # Upstream only auto-starts the app when every one of its steps passed, so a
    # component failure means the port never binds. Watch the child too, or we sit
    # here for the full timeout and then report the wrong cause.
    INSTALL_OK=0
    DEADLINE=$(( $(date +%s) + 900 ))
    while [[ $(date +%s) -lt $DEADLINE ]]; do
        if port_busy; then INSTALL_OK=1; break; fi
        if ! kill -0 "$INSTALL_BASH_PID" 2>/dev/null; then
            die "the MUIOGO installer exited without starting the app — see $LOG"
        fi
        sleep 2
    done
    if [[ $INSTALL_OK -eq 1 ]]; then
        ok "installer finished; app answered on port $PORT"
    else
        # Signal the whole tree: killing only the top-level bash leaves uv and
        # python children writing into the master directory.
        pkill -P "$INSTALL_BASH_PID" 2>/dev/null || true
        kill "$INSTALL_BASH_PID" 2>/dev/null || true
        die "MUIOGO never answered on port $PORT within 15 minutes — see $LOG"
    fi
    stop_server
    record muiogo OK "$MUIOGO_DIR"
fi
if [[ -f "$MUIOGO_PIN_FILE" ]]; then
    PIN="$(tr -d '[:space:]' < "$MUIOGO_PIN_FILE")"
    CUR="$(git -C "$MUIOGO_DIR" rev-parse --short=8 HEAD)"
    BRANCH="$(git -C "$MUIOGO_DIR" rev-parse --abbrev-ref HEAD 2>/dev/null || echo '?')"
    DIRTY="$(git -C "$MUIOGO_DIR" status --porcelain 2>/dev/null | head -1)"
    if [[ "$CUR" == "$PIN"* || "$PIN" == "$CUR"* ]]; then
        ok "MUIOGO already at pin $PIN"
    elif [[ $MUIOGO_WAS_HERE -eq 1 ]]; then
        # Never move someone else's checkout. Detaching HEAD here would abandon
        # the branch they are working on, and discarding changes is not ours to do.
        warn "MUIOGO at $MUIOGO_DIR is $BRANCH ($CUR), not the pin $PIN — leaving it alone"
        [[ -n "$DIRTY" ]] && warn "  it also has uncommitted changes"
        echo "      This checkout was already here, so it is yours to manage."
        echo "      To run against the pin instead, use a separate --dest."
        record muiogo-pin SKIP "kept $BRANCH ($CUR)"
    elif [[ -n "$DIRTY" ]]; then
        die "MUIOGO at $MUIOGO_DIR has uncommitted changes; not touching it"
    else
        git -C "$MUIOGO_DIR" fetch --quiet origin
        git -C "$MUIOGO_DIR" checkout --quiet --detach "$PIN" || die "could not checkout MUIOGO pin $PIN"
        ( cd "$MUIOGO_DIR" && clean_env uv sync -q ) || die "uv sync at the pin failed"
        ok "MUIOGO pinned to $PIN"
    fi
fi
# Pin this installation's OG registry into its own .env. MUIOGO resolves
# MUIOGO_OG_DATA_DIR / MUIOGO_OG_MODELS_DIR through load_dotenv(), so writing them
# here makes the isolation hold however MUIOGO is started — our `muiogo serve`,
# its own start.sh, or the GUI. Without it, every MUIOGO on the machine shares
# ~/.muiogo/og-state, whose registry holds one entry per country and would
# displace a model you use for live work.
#
# Only for an installation THIS script created. A checkout that was already here
# keeps whatever registry its owner set up; we do not rewrite someone's .env.
# Run this EVERY time, not only on a fresh clone. It was gated on
# MUIOGO_WAS_HERE, which is inferred from disk artifacts — so any second run, or a
# resume after a partial first run, skipped it and left the installed world reading
# the shared user-level registry. That is exactly the two-worlds collision this
# exists to prevent, and nothing downstream would have caught it: the installer's
# own verification passes the variables explicitly, and the client injects them
# from the manifest. It would only surface later, when someone started the
# installed MUIOGO by its own start.sh.
#
# The per-key guard below is the idempotency test, so re-entering is safe. We only
# refuse when a key is already present with a DIFFERENT value — that is someone
# else's choice and not ours to overwrite.
ENV_FILE="$MUIOGO_DIR/.env"
[[ -f "$ENV_FILE" ]] || : > "$ENV_FILE"
# A file not ending in a newline would glue our first key onto the last line.
[[ -s "$ENV_FILE" && -n "$(tail -c1 "$ENV_FILE")" ]] && printf '\n' >> "$ENV_FILE"
ENV_OK=1
for pair in "MUIOGO_OG_DATA_DIR=$OG_HOME/og-state" "MUIOGO_OG_MODELS_DIR=$OG_HOME/og-models"; do
    key="${pair%%=*}"; want="${pair#*=}"
    existing="$(grep -m1 "^${key}=" "$ENV_FILE" 2>/dev/null | cut -d= -f2-)"
    if [[ -z "$existing" ]]; then
        printf '%s\n' "$pair" >> "$ENV_FILE"
    elif [[ "$existing" != "$want" ]]; then
        warn "$key in $ENV_FILE points at $existing, not $want — leaving it alone"
        warn "  this installation will share that registry; fix it if that is not what you want"
        ENV_OK=0
    fi
done
if [[ $ENV_OK -eq 1 ]]; then
    ok "OG registry isolated to this installation ($OG_HOME/og-state)"
    record og-registry OK "$OG_HOME/og-state"
else
    record og-registry FAIL "existing .env points elsewhere"
fi

for solver in glpsol cbc; do
    command -v "$solver" >/dev/null || warn "solver '$solver' not on PATH — MUIOGO resolves standard locations, but check the install log"
done

# ── 3. OG model(s) via the upstream OG-Core universal installer ──────────────
CURRENT_STEP="og-models"
declare -a OG_INSTALLED_KEYS=() OG_INSTALLED_REPOS=() OG_INSTALLED_PKGS=() OG_INSTALLED_NAMES=()
if [[ -n "$OG_KEYS" ]]; then
    step_banner "3" "OG model(s): $OG_KEYS (upstream OG-Core installer)"
    OG_INST="$(mktemp -d)/og-install.sh"
    CLEANUP_FILES+=("$OG_INST")
    CLEANUP_PATHS+=("$(dirname "$OG_INST")")
    curl -fsSL "$OG_INSTALLER_URL" -o "$OG_INST" || die "could not fetch the OG-Core installer"
    CATALOG_JSON="$(curl -fsSL "$OG_CATALOG_URL")" || die "could not fetch the OG catalog (repos.json)"
    IFS=',' read -ra KEYS <<< "$OG_KEYS"
    for key in "${KEYS[@]}"; do
        key="$(echo "$key" | tr -d '[:space:]')"
        # ogcore is a DEPENDENCY, not something to run. Every country model
        # already carries its own copy inside its venv — verified: OG-PHL imports
        # ogcore 0.18.0 from OG-PHL/.venv/.../site-packages, never from a checkout.
        # The OG-Core repo is 2.8 GB (1.9 GB of it git history) and is only needed
        # to develop OG-Core itself, which is not what this runtime is for.
        if [[ "$key" == "og-core" ]]; then
            print_skip "og-core" "a dependency of every country model, not a runtime component"
            echo "        Each country model already has ogcore in its own venv."
            echo "        Clone the OG-Core repo separately if you want to develop it."
            continue
        fi
        ENTRY="$(printf '%s' "$CATALOG_JSON" | python3 -c '
import json, sys
data = json.load(sys.stdin)
for r in data["repos"]:
    if r["key"] == sys.argv[1]:
        print(r["repo"], r["package"], r["description"].replace(" ", "_"))
        break
' "$key")"
        [[ -z "$ENTRY" ]] && die "OG key '$key' not in the upstream catalog"
        read -r REPO PKG DESC <<< "$ENTRY"
        MODEL_DIR="$OG_HOME/og-models/$REPO"
        IMPORT_NAME="${PKG//-/_}"
        MODEL_PY="$MODEL_DIR/.venv/bin/python"
        [[ -x "$MODEL_PY" ]] || MODEL_PY="$MODEL_DIR/.venv/Scripts/python.exe"

        # "A venv exists" is not "the model is installed". If a previous attempt
        # created the venv and then died mid-sync, skipping on the venv alone
        # meant every later run skipped the install and then failed the import
        # check below — wedged forever, fixable only by deleting the directory.
        # So the test is whether the package actually imports.
        if [[ -x "$MODEL_PY" ]] && "$MODEL_PY" -c "import $IMPORT_NAME" 2>/dev/null; then
            skip "$key ($MODEL_DIR)"
        else
            if [[ -d "$MODEL_DIR" ]]; then
                warn "$key is present but '$IMPORT_NAME' does not import — finishing the install"
                echo "        (a previous attempt stopped part-way; uv sync resumes where it left off)"
            fi
            echo "  installing $key -> $MODEL_DIR (uv sync of a full model env — several minutes)"
            clean_env bash "$OG_INST" --repo "$key" --dest "$OG_HOME/og-models" --yes --no-log \
                > "$DEST/og-install-$key.log" 2>&1 \
                || die "OG installer failed for $key — see $DEST/og-install-$key.log"
            MODEL_PY="$MODEL_DIR/.venv/bin/python"
            [[ -x "$MODEL_PY" ]] || MODEL_PY="$MODEL_DIR/.venv/Scripts/python.exe"
        fi
        if ! "$MODEL_PY" -c "import $IMPORT_NAME" 2>/dev/null; then
            warn "$key still cannot import '$IMPORT_NAME' after a full install attempt."
            echo "        Log: $DEST/og-install-$key.log"
            echo "        The environment at $MODEL_DIR looks broken. Move it"
            echo "        aside — not delete it — and re-run this installer:"
            echo_cmd "mv '$MODEL_DIR' '$MODEL_DIR.broken'"
            die "$key is not usable"
        fi
        ok "$key imports from its own venv"
        OG_INSTALLED_KEYS+=("$key"); OG_INSTALLED_REPOS+=("$REPO")
        OG_INSTALLED_PKGS+=("$PKG"); OG_INSTALLED_NAMES+=("${DESC//_/ }")
    done
    record og-models OK "$OG_KEYS -> $OG_HOME/og-models"
else
    step_banner "3" "OG model(s): none requested (--og to add)"
    record og-models SKIP "none requested"
fi

# ── 4. ogclews-link via its own setup.sh ─────────────────────────────────────
CURRENT_STEP="ogclews-link"
if [[ $WITH_LINK -eq 1 ]]; then
    step_banner "4" "ogclews-link (its own setup.sh)"
    LINK_DIR="$DEST/ogclews-link"
    if [[ -d "$LINK_DIR/.git" ]]; then skip "clone"; else
        git clone --quiet "$LINK_REPO_URL" "$LINK_DIR" || die "could not clone ogclews-link"
    fi
    ( cd "$LINK_DIR" && clean_env ./scripts/setup.sh ) > "$DEST/link-setup.log" 2>&1 \
        || die "ogclews-link setup failed — see $DEST/link-setup.log"
    ok "link env ready"
    for i in "${!OG_INSTALLED_KEYS[@]}"; do
        ( cd "$LINK_DIR" && clean_env ./scripts/setup.sh \
            --og-path "$OG_HOME/og-models/${OG_INSTALLED_REPOS[$i]}" \
            --key "${OG_INSTALLED_KEYS[$i]}" ) >> "$DEST/link-setup.log" 2>&1 \
            || die "link registration failed for ${OG_INSTALLED_KEYS[$i]} — see $DEST/link-setup.log"
        ok "registered ${OG_INSTALLED_KEYS[$i]} with the link"
    done
    record ogclews-link OK "$LINK_DIR"
else
    step_banner "4" "ogclews-link: skipped (--no-link)"
    LINK_DIR=""
    record ogclews-link SKIP "--no-link"
fi

# ── 5. register OG models with MUIOGO + verify everything ────────────────────
CURRENT_STEP="verify"
step_banner "5" "Register with MUIOGO + verification battery"
start_muiogo() {
    MUIOGO_OG_MODELS_DIR="$OG_HOME/og-models" MUIOGO_OG_DATA_DIR="$OG_HOME/og-state" \
        PORT="$PORT" "$MUIOGO_DIR/.venv/bin/python" "$MUIOGO_DIR/API/app.py" \
        > "$DEST/muiogo-server.log" 2>&1 &
    SERVER_PID=$!
    wait_api 60 || die "MUIOGO did not start for verification — see $DEST/muiogo-server.log"
}
start_muiogo

# 5a. install CLEWs country case(s) through MUIOGO's own /uploadCase endpoint
# (the same validated path the GUI's restore uses).
declare -a CLEWS_INSTALLED_CASES=() CLEWS_INSTALLED_KEYS=()
if [[ -n "$CLEWS_KEYS" ]]; then
    IFS=',' read -ra CKEYS <<< "$CLEWS_KEYS"
    for ckey in "${CKEYS[@]}"; do
        ckey="$(echo "$ckey" | tr -d '[:space:]')"
        ISO3="$(python3 -c '
import json, sys
data = json.load(open(sys.argv[1]))
for r in data["repos"]:
    if r["key"] == sys.argv[2]:
        print(r["iso3"]); break
' "$AI_DIR/clews/clews-repos.json" "$ckey")"
        [[ -z "$ISO3" ]] && die "CLEWs key '$ckey' not in clews/clews-repos.json"
        CMANIFEST="$AI_DIR/clews/countries/$ISO3.json"
        [[ -f "$CMANIFEST" ]] || die "missing CLEWs manifest: $CMANIFEST"
        SEL="$(python3 -c '
import json, sys
m = json.load(open(sys.argv[1])); want = sys.argv[2]
cases = m["cases"]
if want:
    match = [c for c in cases if c["case"] == want]
    if not match:
        sys.exit("case %s not in manifest for %s" % (want, m["iso3"]))
    c = match[0]
else:
    rec = [c for c in cases if c.get("recommended")]
    c = rec[0] if rec else cases[0]
s = m["source"]
print(c["case"], c["archive"], s["owner"], s["repo"], s["ref"], s["dir"], s.get("sha256sums",""))
' "$CMANIFEST" "$CASE_OVERRIDE")" || die "case selection failed for $ckey"
        read -r CCASE CARCHIVE COWNER CREPO CREF CDIR CSHAF <<< "$SEL"
        if api /getCases 30 | grep -q "\"$CCASE\""; then
            skip "$CCASE"
            CLEWS_INSTALLED_CASES+=("$CCASE"); CLEWS_INSTALLED_KEYS+=("$ckey")
            record "$ckey" SKIP "$CCASE"
            continue
        fi
        RAWBASE="https://raw.githubusercontent.com/$COWNER/$CREPO/$CREF/$CDIR"
        echo "  downloading $CARCHIVE from $COWNER/$CREPO@$CREF"
        curl -fsSL -o "$DEST/$CARCHIVE" "$RAWBASE/$CARCHIVE" || die "download failed: $RAWBASE/$CARCHIVE"
        if [[ -n "$CSHAF" ]]; then
            curl -fsSL -o "$DEST/$CARCHIVE.sums" "$RAWBASE/$CSHAF" || die "checksum file missing: $RAWBASE/$CSHAF"
            python3 -c '
import hashlib, sys
name, zpath, sums = sys.argv[1:4]
want = None
for line in open(sums):
    parts = line.split()
    if len(parts) >= 2 and parts[-1].lstrip("*./") == name:
        want = parts[0]
if want is None: sys.exit(f"{name} not listed in checksum file")
got = hashlib.sha256(open(zpath, "rb").read()).hexdigest()
sys.exit(0 if got == want else f"sha256 mismatch for {name}: {got} != {want}")
' "$CARCHIVE" "$DEST/$CARCHIVE" "$DEST/$CARCHIVE.sums" || die "checksum verification failed for $CARCHIVE"
            ok "sha256 verified"
        fi
        curl -s -m 300 -F "file=@$DEST/$CARCHIVE" "http://127.0.0.1:${PORT}/uploadCase" > "$DEST/upload-$ckey.log" 2>&1
        if api /getCases 30 | grep -q "\"$CCASE\""; then
            ok "case installed in MUIOGO: $CCASE"
            rm -f "$DEST/$CARCHIVE" "$DEST/$CARCHIVE.sums"
            CLEWS_INSTALLED_CASES+=("$CCASE"); CLEWS_INSTALLED_KEYS+=("$ckey")
            record "$ckey" OK "$CCASE"
        else
            warn "upload response: $(head -c 200 "$DEST/upload-$ckey.log")"
            die "case $CCASE not present after upload — see $DEST/upload-$ckey.log"
        fi
    done
fi

# 5b. register each OG model in MUIOGO's registry (async job; env already synced)
for i in "${!OG_INSTALLED_KEYS[@]}"; do
    CID="$(echo "${OG_INSTALLED_REPOS[$i]}" | awk -F- '{print toupper($NF)}')"
    BODY="$(python3 - "$CID" "${OG_INSTALLED_NAMES[$i]}" "$OG_HOME/og-models/${OG_INSTALLED_REPOS[$i]}" "${OG_INSTALLED_PKGS[$i]}" <<'PY'
import json, sys
print(json.dumps({"country_id": sys.argv[1], "country_name": sys.argv[2],
                  "local_path": sys.argv[3], "package_name": sys.argv[4],
                  "run_uv_sync": False}))
PY
)"
    RESP="$(curl -s -m 30 -H "Content-Type: application/json" -d "$BODY" "http://127.0.0.1:${PORT}/ogc/registerLocalCalibration")"
    INSTALL_ID="$(echo "$RESP" | python3 -c "import json,sys; print(json.load(sys.stdin).get('install_id',''))" 2>/dev/null)"
    if [[ -z "$INSTALL_ID" ]]; then
        warn "MUIOGO registration request failed for ${OG_INSTALLED_KEYS[$i]}: $RESP"
        record "register-${OG_INSTALLED_KEYS[$i]}" FAIL "$RESP"
        continue
    fi
    STATE="pending"
    for _ in $(seq 1 60); do
        STATE="$(api "/ogc/getInstallStatus?install_id=$INSTALL_ID" | python3 -c "import json,sys; print(json.load(sys.stdin).get('install_state',''))" 2>/dev/null)"
        [[ "$STATE" == "installed" || "$STATE" == "failed" ]] && break
        sleep 2
    done
    if [[ "$STATE" == "installed" ]]; then
        ok "MUIOGO registry: ${OG_INSTALLED_KEYS[$i]} installed"
        record "register-${OG_INSTALLED_KEYS[$i]}" OK "$CID"
    else
        warn "MUIOGO registry state for ${OG_INSTALLED_KEYS[$i]}: $STATE"
        record "register-${OG_INSTALLED_KEYS[$i]}" FAIL "state=$STATE"
    fi
done

# 5c. verification battery
if [[ $NO_VERIFY -eq 0 ]]; then
    CASES="$(api /getCases)"
    echo "$CASES" | grep -q "CLEWs Demo" && ok "MUIOGO serves; demo case present" \
        || { [[ $NO_DEMO_DATA -eq 1 ]] && warn "no demo case (--no-demo-data)" || die "demo case missing: $CASES"; }
    if echo "$CASES" | grep -q "CLEWs Demo"; then
        curl -s -m 60 -H "Content-Type: application/json" \
            -d '{"casename":"CLEWs Demo","caserunname":"REF"}' "http://127.0.0.1:${PORT}/generateDataFile" >/dev/null
        RUN_STATUS="$(curl -s -m 570 -H "Content-Type: application/json" \
            -d '{"casename":"CLEWs Demo","caserunname":"REF","solver":"cbc"}' "http://127.0.0.1:${PORT}/run" \
            | python3 -c "import json,sys; print(json.load(sys.stdin).get('status_code',''))" 2>/dev/null)"
        [[ "$RUN_STATUS" == "success" ]] && ok "demo case solves with CBC" || die "demo solve failed (status: $RUN_STATUS)"
    fi
    if [[ -n "$LINK_DIR" ]]; then
        ( cd "$LINK_DIR" && clean_env ./scripts/setup.sh --check ) >/dev/null 2>&1 \
            && ok "link --check passes" || die "ogclews-link --check failed"
    fi
    # Isolation is the reason this installation exists, and it is the one
    # property nothing else here would notice failing: a server reading the
    # shared registry serves and solves perfectly well.
    if [[ "$OG_HOME" != "${HOME}/.muiogo" ]]; then
        ACTIVE_STATE="$(grep -E '^MUIOGO_OG_DATA_DIR=' "$DEST/MUIOGO/.env" 2>/dev/null | cut -d= -f2-)"
        [[ "$ACTIVE_STATE" == "$OG_HOME/og-state" ]] \
            && ok "world isolation: configured registry is $OG_HOME/og-state" \
            || die "world isolation FAILED: this MUIOGO's registry is '${ACTIVE_STATE:-unset}', expected $OG_HOME/og-state"
        # Configuration can be right while the running server ignores it, so
        # check where registration actually landed rather than trusting .env.
        if [[ ${#OG_INSTALLED_KEYS[@]} -gt 0 ]]; then
            [[ -f "$OG_HOME/og-state/og_calibrations_installed.json" ]] \
                && ok "registrations landed in this world's registry" \
                || die "registered ${#OG_INSTALLED_KEYS[@]} model(s) but $OG_HOME/og-state/og_calibrations_installed.json does not exist — the server wrote its registry somewhere else"
        fi
        if [[ -n "$SHARED_REGISTRY_BEFORE" ]]; then
            [[ "$(sha256_of "$SHARED_REGISTRY")" == "$SHARED_REGISTRY_BEFORE" ]] \
                && ok "your existing registry is untouched" \
                || die "this install MODIFIED $SHARED_REGISTRY — that is your manual setup's registry. Stopping so you can check it."
        elif [[ -f "$SHARED_REGISTRY" ]]; then
            die "this install CREATED $SHARED_REGISTRY — it should only ever write $OG_HOME/og-state"
        fi
    fi
    VERIFIED="demo solve + world isolation"
    [[ ${#OG_INSTALLED_KEYS[@]} -gt 0 ]] && VERIFIED="$VERIFIED + OG imports"
    [[ -n "$LINK_DIR" ]] && VERIFIED="$VERIFIED + link check"
    record verify OK "$VERIFIED"
else
    record verify SKIP "--no-verify"
fi
stop_server

# ── manifest ──────────────────────────────────────────────────────────────────
CURRENT_STEP="manifest"
OG_JSON="[]"
for i in "${!OG_INSTALLED_KEYS[@]}"; do
    OG_JSON="$(python3 - "$OG_JSON" "${OG_INSTALLED_KEYS[$i]}" "${OG_INSTALLED_REPOS[$i]}" "${OG_INSTALLED_PKGS[$i]}" "$OG_HOME/og-models/${OG_INSTALLED_REPOS[$i]}" <<'PY'
import json, subprocess, sys
arr = json.loads(sys.argv[1]); path = sys.argv[5]
ref = subprocess.run(["git", "-C", path, "rev-parse", "--short=8", "HEAD"],
                     capture_output=True, text=True).stdout.strip()
arr.append({"key": sys.argv[2], "repo": sys.argv[3], "package": sys.argv[4],
            "path": path, "ref": ref, "python": f"{path}/.venv/bin/python"})
print(json.dumps(arr))
PY
)"
done
CLEWS_JSON="[]"
for i in "${!CLEWS_INSTALLED_CASES[@]}"; do
    CLEWS_JSON="$(python3 -c '
import json, sys
arr = json.loads(sys.argv[1])
arr.append({"key": sys.argv[2], "case": sys.argv[3]})
print(json.dumps(arr))' "$CLEWS_JSON" "${CLEWS_INSTALLED_KEYS[$i]}" "${CLEWS_INSTALLED_CASES[$i]}")"
done
python3 - "$DEST" "$MUIOGO_DIR" "$RUNTIME_AI_DIR" "${LINK_DIR:-}" "$OG_JSON" "$PORT" "$OG_HOME" "$CLEWS_JSON" <<'PY'
import json, subprocess, sys, datetime, shutil, os, glob
dest, muiogo, ai, link, og_json, port, og_home, clews_json = sys.argv[1:9]
def ref(path):
    if not path: return None
    r = subprocess.run(["git", "-C", path, "rev-parse", "--short=8", "HEAD"],
                       capture_output=True, text=True)
    return r.stdout.strip() or None
def ver(cmd, *args):
    exe = shutil.which(cmd)
    if not exe: return None
    r = subprocess.run([exe, *args], capture_output=True, text=True)
    return (r.stdout or r.stderr).splitlines()[0].strip() if (r.stdout or r.stderr) else exe
manifest = {
    "generated": datetime.datetime.now().isoformat(timespec="seconds"),
    "workspace": dest,
    "kind": "installed",          # a self-contained runtime, not adopted checkouts
    "adopted": False,
    "muiogo": {"path": muiogo, "ref": ref(muiogo), "python": f"{muiogo}/.venv/bin/python",
               "url": f"http://127.0.0.1:{port}", "port": int(port),
               "og_models_dir": f"{og_home}/og-models", "og_state_dir": f"{og_home}/og-state"},
    "muiogo_ai": {"path": ai, "ref": ref(ai), "client_python": f"{ai}/client/.venv/bin/python"},
    "ogclews_link": {"path": link or None, "ref": ref(link),
                     "python": f"{link}/.venv/bin/python" if link else None},
    "og_models": json.loads(og_json),
    "clews_cases": json.loads(clews_json),
    "solvers": {"glpsol": ver("glpsol", "--version"), "cbc": shutil.which("cbc")},
}

# Record what is ACTUALLY installed, not just what this run installed. A later
# run with different flags must not erase components that are still on disk.
seen = {m["key"] for m in manifest["og_models"]}
for path in sorted(glob.glob(os.path.join(og_home, "og-models", "*"))):
    name = os.path.basename(path)
    key = f"og-{name.rsplit('-', 1)[-1].lower()}"
    if key in seen or not os.path.isdir(os.path.join(path, ".venv")):
        continue
    manifest["og_models"].append({
        "key": key, "repo": name, "package": None, "path": path,
        "ref": ref(path), "python": f"{path}/.venv/bin/python",
    })
ds = manifest["muiogo"]["data_storage"] if "data_storage" in manifest["muiogo"] else None
ds = ds or os.path.join(muiogo, "WebAPP", "DataStorage")
known = {c["case"] for c in manifest["clews_cases"]}
for path in sorted(glob.glob(os.path.join(ds, "*"))):
    case = os.path.basename(path)
    if case in known or not os.path.isfile(os.path.join(path, "genData.json")):
        continue
    manifest["clews_cases"].append({"key": None, "case": case})

out = f"{dest}/manifest.json"
with open(out, "w") as f:
    json.dump(manifest, f, indent=2)
print(f"  ok manifest: {out}")

PY

# Publish to the canonical well-known path so an assistant running in ANY
# directory finds this installation. Uses the client's own interpreter: the
# package needs its dependencies, which the system python does not have.
#
# Registration is NOT activation. The active pointer is whichever world the
# user works in by default; installing a runtime must never steal it from an
# existing setup. It is taken only when nothing holds it — a fresh machine —
# so that bare `muiogo` still works out of the box there.
CLIENT_PY="$RUNTIME_AI_DIR/client/.venv/bin/python"
[[ -x "$CLIENT_PY" ]] || CLIENT_PY="$RUNTIME_AI_DIR/client/.venv/Scripts/python.exe"
if [[ -x "$CLIENT_PY" ]]; then
    PUB_OUT="$("$CLIENT_PY" - "$DEST/manifest.json" <<'PYPUB' 2>/dev/null
import sys
from muiogo_client import workspace
prev = workspace.active_world()
path = workspace.publish(sys.argv[1], name="runtime", make_active=(prev is None))
print(path or "")
print(prev or "")
PYPUB
)"
    PUBLISHED="$(printf '%s\n' "$PUB_OUT" | sed -n 1p)"
    PREV_ACTIVE="$(printf '%s\n' "$PUB_OUT" | sed -n 2p)"
    if [[ -n "$PUBLISHED" ]]; then
        if [[ -n "$PREV_ACTIVE" ]]; then
            ok "registered as world 'runtime' — your active world stays '$PREV_ACTIVE'"
        else
            ok "registered as world 'runtime' and made active (no other world was)"
        fi
    else
        warn "could not publish the manifest to ~/.muiogo — 'muiogo status' will need MUIOGO_WORKSPACE"
    fi
else
    warn "no client interpreter; skipped publishing the manifest"
fi
record manifest OK "$DEST/manifest.json"

# ── the launcher: how you get this world without switching to it ──────────────
# `muiogo-ai` carries this installation's manifest path as an absolute literal,
# so it cannot be retargeted by an environment variable, a working directory, or
# a stored pointer — there is nothing to change. Child processes inherit it,
# which is what makes a skill's own python script act on this world too.
CURRENT_STEP="launcher"
LAUNCHER_DIR="${HOME}/.local/bin"
LAUNCHER="$LAUNCHER_DIR/muiogo-ai"
if clean_env "$RUNTIME_MUIOGO" launcher runtime \
        --out "$LAUNCHER" --state-home "$OG_HOME" >/dev/null 2>&1; then
    ok "muiogo-ai command written ($LAUNCHER)"
    command -v muiogo-ai >/dev/null \
        || warn "$LAUNCHER_DIR is not on your PATH — add it, or call $LAUNCHER directly"
    record launcher OK "$LAUNCHER"
else
    warn "could not write the muiogo-ai launcher"
    echo "        Until that is fixed, target this world explicitly:"
    echo_cmd "$RUNTIME_MUIOGO --url http://127.0.0.1:$PORT"
    record launcher FAIL "see above"
fi

report
FAILED_STEPS=0
for _s in ${STEP_STATES[@]+"${STEP_STATES[@]}"}; do
    [[ "$_s" == "FAIL" ]] && FAILED_STEPS=$((FAILED_STEPS + 1))
done

# ── optional: skills into the user's AI assistant ────────────────────────────
# Always optional, never silent: writing into someone's home directory is their
# call, so a non-interactive run just prints how to do it later.
SKILL_COUNT="$(ls -d "$AI_DIR"/.agents/skills/*/ 2>/dev/null | wc -l | tr -d ' ')"
if [[ $NO_SKILLS -eq 0 && "$SKILL_COUNT" -gt 0 ]]; then
    echo ""
    printf "  ${BOLD}Modelling skills${RESET}\n"
    echo "  $SKILL_COUNT skills teach an AI assistant how to build, calibrate, run, and"
    echo "  review these models."
    echo ""
    echo "  They are ALREADY ACTIVE in this repository — open it in Claude Code or"
    echo "  Codex and they load automatically. Answering yes below only adds a copy"
    echo "  for your OTHER projects; answering no changes nothing here."
    SKILL_ARGS=()
    [[ -n "$SKILLS_TOOL" ]] && SKILL_ARGS+=("--tool" "$SKILLS_TOOL")
    [[ $ASSUME_YES -eq 1 ]] && SKILL_ARGS+=("--yes")
    # --yes with no --skills-tool cannot proceed: the assistant is unguessable.
    if [[ $ASSUME_YES -eq 1 && -z "$SKILLS_TOOL" ]]; then
        print_skip "skills" "no --skills-tool given"
        SKILLS_DECISION=1
    elif prompt_yn "Also install a copy for your other projects?" n; then
        bash "$AI_DIR/scripts/install-skills.sh" ${SKILL_ARGS[@]+"${SKILL_ARGS[@]}"} \
            || warn "the skills installer did not finish -- run it again when convenient"
        SKILLS_DECISION=0
    else
        SKILLS_DECISION=1
    fi
    if [[ $SKILLS_DECISION -eq 1 ]]; then
        printf "  Kept in the repository only — they work whenever you open it.\n"
        printf "  ${DIM}To add them to your other projects later:${RESET}\n"
        echo_cmd "$AI_DIR/scripts/install-skills.sh"
    fi
fi

echo ""
# The banner must reflect the recorded steps. It used to be unconditional, so a
# failed step still ended in a green "installed and verified" and exit 0.
if [[ $FAILED_STEPS -gt 0 ]]; then
    printf "  ${RED}${BOLD}%d step(s) failed — this installation is NOT verified.${RESET}\n" "$FAILED_STEPS"
    echo    "  Review the report above. Re-running is safe: finished steps are skipped."
    echo    "  Workspace : $DEST"
    exit 1
fi
printf "  ${GREEN}${BOLD}MUIOGO-AI stack installed and verified.${RESET}\n"
echo    "  Workspace : $DEST"
echo    "  Manifest  : $DEST/manifest.json"
echo    "  World     : runtime (port $PORT) — \`muiogo-ai worlds\` shows all of them"
echo    "  Start it:   muiogo-ai serve --detach"
echo    "  Remove it:  scripts/uninstall.sh — moves everything aside, deletes nothing"
exit 0
