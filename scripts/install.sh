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
#   --dest DIR          Workspace directory (default: ~/muiogo-ai-workspace)
#   --country ISO3s     Comma-separated countries (PHL,...). Resolves BOTH sides
#                       by the ISO3 join: the OG model (og-<iso3>) via the
#                       upstream catalog AND the CLEWs case via clews/ manifests.
#   --og KEYS           Comma-separated OG models to install (og-phl,og-eth,...)
#                       from the upstream catalog. Default: none.
#   --clews KEYS        Comma-separated CLEWs countries (clews-phl,...) from
#                       clews/clews-repos.json; installs the recommended portable
#                       case into MUIOGO via its /uploadCase endpoint.
#   --case NAME         Override the recommended case (single --clews/--country only)
#   --og-home DIR       Where OG models/state live (default: ~/.muiogo, MUIOGO's
#                       own default, so the GUI, the link, and skills all see them)
#   --no-link           Skip ogclews-link
#   --no-demo-data      Pass through to the MUIOGO installer
#   --no-verify         Skip the final verification battery (discouraged)
#   --no-skills         Don't offer to install the skills at the end
#   --skills-tool KEY   Which assistant gets the skills: claude, codex, or both
#   -y, --yes           Auto-confirm every prompt (non-interactive). Skills are
#                       installed only when --skills-tool is also given.
#   --port N            Port for MUIOGO during install/verify (default 5002)
#   -h, --help          This message
# ──────────────────────────────────────────────────────────────────────────────
set -uo pipefail

MUIOGO_INSTALLER_URL="https://raw.githubusercontent.com/EAPD-DRB/MUIOGO/main/scripts/install.sh"
OG_INSTALLER_URL="https://raw.githubusercontent.com/PSLmodels/OG-Core/master/scripts/install.sh"
OG_CATALOG_URL="https://raw.githubusercontent.com/PSLmodels/OG-Core/master/scripts/repos.json"
LINK_REPO_URL="https://github.com/marcelolafleur/ogclews-link.git"
MUIOGO_AI_REPO_URL="https://github.com/EAPD-DRB/MUIOGO-AI.git"

DEST="${HOME}/muiogo-ai-workspace"
OG_KEYS=""
CLEWS_KEYS=""
COUNTRIES=""
CASE_OVERRIDE=""
OG_HOME="${HOME}/.muiogo"
WITH_LINK=1
NO_DEMO_DATA=0
NO_VERIFY=0
NO_SKILLS=0
SKILLS_TOOL=""
ASSUME_YES=0
PORT=5002

usage() {
    cat <<EOF
MUIOGO-AI composed installer (macOS and Linux).

Runs each component's own upstream installer in turn, then verifies the stack.

Usage:
  $0 [options]

Options:
  -h, --help              Show this message and exit.
  -y, --yes               Auto-confirm every prompt (non-interactive).
      --dest DIR          Workspace directory (default: ~/muiogo-ai-workspace).
      --country ISO3s     Countries to set up, comma-separated (e.g. PHL).
                          Resolves BOTH sides from the one key: the OG model
                          (og-<iso3>) and the CLEWs case.
      --og KEYS           OG models only (og-phl,og-eth,...); 'none' for none.
      --clews KEYS        CLEWs countries only (clews-phl,...).
      --case NAME         Use a specific CLEWs case instead of the recommended one.
      --og-home DIR       Where OG models and state live (default: ~/.muiogo).
      --no-link           Skip ogclews-link.
      --no-demo-data      Don't install MUIOGO's demo data.
      --no-verify         Skip the final verification battery (discouraged).
      --no-skills         Don't offer to install the skills at the end.
      --skills-tool KEY   Assistant for the skills: claude, codex, or both.
      --port N            Port for MUIOGO during install and verify (default 5002).

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

# No-op `open`/`xdg-open` shim so the MUIOGO installer's auto-start can't pop
# a browser. The auto-start itself is absorbed as our health probe.
SHIM_DIR="$(mktemp -d)"
for cmd in open xdg-open; do
    printf '#!/bin/sh\nexit 0\n' > "$SHIM_DIR/$cmd" && chmod +x "$SHIM_DIR/$cmd"
done

server_pid() { lsof -ti ":$PORT" 2>/dev/null | head -1; }
stop_server() { local pid; pid="$(server_pid)"; [[ -n "$pid" ]] && kill "$pid" 2>/dev/null && sleep 1; }
api() { curl -s -m "${2:-10}" "http://127.0.0.1:${PORT}${1}"; }
wait_api() { # wait_api SECONDS — until /getCases answers
    local deadline=$(( $(date +%s) + $1 ))
    while [[ $(date +%s) -lt $deadline ]]; do
        [[ -n "$(api /getCases 5)" ]] && return 0
        sleep 2
    done
    return 1
}

# ── preflight ─────────────────────────────────────────────────────────────────
CURRENT_STEP="preflight"
section "Preflight"
for tool in git curl python3 lsof; do
    command -v "$tool" >/dev/null || die "'$tool' is required — install it and re-run."
done
[[ -n "${VIRTUAL_ENV:-}${CONDA_DEFAULT_ENV:-}" ]] && warn "active venv/conda detected — component installers run with a cleaned environment"
[[ -n "$(server_pid)" ]] && die "port $PORT is already in use — stop that server or pass --port"
mkdir -p "$DEST"
DEST="$(cd "$DEST" && pwd)"
mkdir -p "$OG_HOME/og-models" "$OG_HOME/og-state"
OG_HOME="$(cd "$OG_HOME" && pwd)"
ok "workspace: $DEST"
record preflight OK "$DEST"

# ── 1. MUIOGO-AI (this repo: client + skills) ────────────────────────────────
CURRENT_STEP="muiogo-ai"
step_banner "1" "MUIOGO-AI (client + skills)"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]:-$0}")" && pwd)"
if [[ -f "$SCRIPT_DIR/../client/pyproject.toml" ]]; then
    AI_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
    ok "running from checkout: $AI_DIR"
else
    AI_DIR="$DEST/MUIOGO-AI"
    if [[ -d "$AI_DIR/.git" ]]; then skip "clone"; else
        git clone --quiet "$MUIOGO_AI_REPO_URL" "$AI_DIR" \
            || die "could not clone MUIOGO-AI (private repo: authenticate git/gh first)"
    fi
fi
command -v uv >/dev/null || { curl -LsSf https://astral.sh/uv/install.sh | sh >/dev/null 2>&1; export PATH="$HOME/.local/bin:$PATH"; }
( cd "$AI_DIR/client" && clean_env uv sync -q ) || die "uv sync failed in $AI_DIR/client"
record muiogo-ai OK "$AI_DIR"
ok "client env ready"

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
if [[ -x "$MUIOGO_DIR/.venv/bin/python" && -f "$MUIOGO_DIR/API/app.py" ]]; then
    skip "MUIOGO install"
    record muiogo SKIP "$MUIOGO_DIR"
else
    TMP_INST="$(mktemp -d)/muiogo-install.sh"
    curl -fsSL "$MUIOGO_INSTALLER_URL" -o "$TMP_INST" || die "could not fetch the MUIOGO installer"
    EXTRA=(); [[ $NO_DEMO_DATA -eq 1 ]] && EXTRA+=("--no-demo-data")
    # --yes auto-starts the app (no --no-start upstream yet). We absorb that:
    # browser suppressed by the shim; the serving port is our success probe.
    LOG="$DEST/muiogo-install.log"
    PATH="$SHIM_DIR:$PATH" PORT="$PORT" clean_env bash "$TMP_INST" --dest "$DEST" --yes ${EXTRA[@]+"${EXTRA[@]}"} > "$LOG" 2>&1 &
    INSTALL_BASH_PID=$!
    echo "  installing (log: $LOG) — this takes a few minutes on first run"
    if wait_api 900; then
        ok "installer finished; app answered on port $PORT"
    else
        kill "$INSTALL_BASH_PID" 2>/dev/null
        die "MUIOGO never answered on port $PORT — see $LOG"
    fi
    stop_server
    record muiogo OK "$MUIOGO_DIR"
fi
if [[ -f "$MUIOGO_PIN_FILE" ]]; then
    PIN="$(tr -d '[:space:]' < "$MUIOGO_PIN_FILE")"
    CUR="$(git -C "$MUIOGO_DIR" rev-parse --short=8 HEAD)"
    if [[ "$CUR" != "$PIN"* && "$PIN" != "$CUR"* ]]; then
        git -C "$MUIOGO_DIR" fetch --quiet origin
        git -C "$MUIOGO_DIR" checkout --quiet --detach "$PIN" || die "could not checkout MUIOGO pin $PIN"
        ( cd "$MUIOGO_DIR" && clean_env uv sync -q ) || die "uv sync at the pin failed"
        ok "MUIOGO pinned to $PIN"
    else
        ok "MUIOGO already at pin $PIN"
    fi
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
    curl -fsSL "$OG_INSTALLER_URL" -o "$OG_INST" || die "could not fetch the OG-Core installer"
    CATALOG_JSON="$(curl -fsSL "$OG_CATALOG_URL")" || die "could not fetch the OG catalog (repos.json)"
    IFS=',' read -ra KEYS <<< "$OG_KEYS"
    for key in "${KEYS[@]}"; do
        key="$(echo "$key" | tr -d '[:space:]')"
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
        if [[ -x "$MODEL_DIR/.venv/bin/python" ]]; then
            skip "$key ($MODEL_DIR)"
        else
            echo "  installing $key -> $MODEL_DIR (uv sync of a full model env — several minutes)"
            clean_env bash "$OG_INST" --repo "$key" --dest "$OG_HOME/og-models" --yes --no-log \
                > "$DEST/og-install-$key.log" 2>&1 \
                || die "OG installer failed for $key — see $DEST/og-install-$key.log"
        fi
        IMPORT_NAME="${PKG//-/_}"
        "$MODEL_DIR/.venv/bin/python" -c "import $IMPORT_NAME" 2>/dev/null \
            || die "$key installed but 'import $IMPORT_NAME' fails in $MODEL_DIR/.venv"
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
    VERIFIED="demo solve"
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
python3 - "$DEST" "$MUIOGO_DIR" "$AI_DIR" "${LINK_DIR:-}" "$OG_JSON" "$PORT" "$OG_HOME" "$CLEWS_JSON" <<'PY'
import json, subprocess, sys, datetime, shutil
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
out = f"{dest}/manifest.json"
with open(out, "w") as f:
    json.dump(manifest, f, indent=2)
print(f"  ok manifest: {out}")
PY
record manifest OK "$DEST/manifest.json"

report

# ── optional: skills into the user's AI assistant ────────────────────────────
# Always optional, never silent: writing into someone's home directory is their
# call, so a non-interactive run just prints how to do it later.
SKILL_COUNT="$(ls -d "$AI_DIR"/.agents/skills/*/ 2>/dev/null | wc -l | tr -d ' ')"
if [[ $NO_SKILLS -eq 0 && "$SKILL_COUNT" -gt 0 ]]; then
    echo ""
    printf "  ${BOLD}Modelling skills${RESET}\n"
    echo "  $SKILL_COUNT skills teach an AI assistant how to build, calibrate, run, and"
    echo "  review these models. They are already active inside this repository."
    echo "  Installing them makes them available in your other projects too."
    SKILL_ARGS=()
    [[ -n "$SKILLS_TOOL" ]] && SKILL_ARGS+=("--tool" "$SKILLS_TOOL")
    [[ $ASSUME_YES -eq 1 ]] && SKILL_ARGS+=("--yes")
    # --yes with no --skills-tool cannot proceed: the assistant is unguessable.
    if [[ $ASSUME_YES -eq 1 && -z "$SKILLS_TOOL" ]]; then
        print_skip "skills" "no --skills-tool given"
        SKILLS_DECISION=1
    elif prompt_yn "Install them into your AI assistant now?" n; then
        bash "$AI_DIR/scripts/install-skills.sh" ${SKILL_ARGS[@]+"${SKILL_ARGS[@]}"} \
            || warn "the skills installer did not finish -- run it again when convenient"
        SKILLS_DECISION=0
    else
        SKILLS_DECISION=1
    fi
    if [[ $SKILLS_DECISION -eq 1 ]]; then
        printf "  Skipped. You can always install them yourself, any time:\n"
        echo_cmd "$AI_DIR/scripts/install-skills.sh"
        printf "  ${DIM}or copy any folder from $AI_DIR/.agents/skills/ into your assistant's skills folder.${RESET}\n"
    fi
fi

echo ""
printf "  ${GREEN}${BOLD}MUIOGO-AI stack installed and verified.${RESET}\n"
echo    "  Workspace : $DEST"
echo    "  Manifest  : $DEST/manifest.json"
echo    "  Start MUIOGO headless:  $AI_DIR/client/.venv/bin/muiogo serve --root $MUIOGO_DIR"
exit 0
