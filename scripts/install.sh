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
#   --og KEYS           Comma-separated OG models to install (og-phl,og-eth,...)
#                       from the upstream catalog. Default: none.
#   --og-home DIR       Where OG models/state live (default: ~/.muiogo, MUIOGO's
#                       own default, so the GUI, the link, and skills all see them)
#   --no-link           Skip ogclews-link
#   --no-demo-data      Pass through to the MUIOGO installer
#   --no-verify         Skip the final verification battery (discouraged)
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
OG_HOME="${HOME}/.muiogo"
WITH_LINK=1
NO_DEMO_DATA=0
NO_VERIFY=0
PORT=5002

while [[ $# -gt 0 ]]; do
    case "$1" in
        --dest)         DEST="$2";      shift 2 ;;
        --og)           OG_KEYS="$2";   shift 2 ;;
        --og-home)      OG_HOME="$2";   shift 2 ;;
        --no-link)      WITH_LINK=0;    shift ;;
        --no-demo-data) NO_DEMO_DATA=1; shift ;;
        --no-verify)    NO_VERIFY=1;    shift ;;
        --port)         PORT="$2";      shift 2 ;;
        -h|--help)      grep '^#' "$0" | sed 's/^# \{0,1\}//'; exit 0 ;;
        *) echo "Unknown option: $1 (see --help)" >&2; exit 2 ;;
    esac
done
[[ "$OG_KEYS" == "none" ]] && OG_KEYS=""

if [ -t 1 ]; then B=$'\033[1m'; G=$'\033[32m'; Y=$'\033[33m'; R=$'\033[31m'; N=$'\033[0m'; else B=""; G=""; Y=""; R=""; N=""; fi
step() { printf "\n%s==> %s%s\n" "$B" "$*" "$N"; }
ok()   { printf "%s  ok%s %s\n" "$G" "$N" "$*"; }
skip() { printf "%s  --%s %s (already done)\n" "$Y" "$N" "$*"; }
warn() { printf "%s  ! %s %s\n" "$Y" "$N" "$*"; }
die()  { printf "%s  x %s %s\n" "$R" "$N" "$*" >&2; record "$CURRENT_STEP" FAIL "$*"; report; exit 1; }

STEP_NAMES=(); STEP_STATES=(); STEP_NOTES=(); CURRENT_STEP="preflight"
record() { STEP_NAMES+=("$1"); STEP_STATES+=("$2"); STEP_NOTES+=("${3:-}"); }
report() {
    printf "\n%s── install report ──────────────────────────────%s\n" "$B" "$N"
    local i
    for i in "${!STEP_NAMES[@]}"; do
        printf "  %-22s %-5s %s\n" "${STEP_NAMES[$i]}" "${STEP_STATES[$i]}" "${STEP_NOTES[$i]}"
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
step "Preflight"
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
step "1/5 MUIOGO-AI (client + skills)"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
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

# ── 2. MUIOGO via its upstream installer ─────────────────────────────────────
CURRENT_STEP="muiogo"
step "2/5 MUIOGO (upstream installer: app + solvers + demo data)"
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
    step "3/5 OG model(s): $OG_KEYS (upstream OG-Core installer)"
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
    step "3/5 OG model(s): none requested (--og to add)"
    record og-models SKIP "none requested"
fi

# ── 4. ogclews-link via its own setup.sh ─────────────────────────────────────
CURRENT_STEP="ogclews-link"
if [[ $WITH_LINK -eq 1 ]]; then
    step "4/5 ogclews-link (its own setup.sh)"
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
    step "4/5 ogclews-link: skipped (--no-link)"
    LINK_DIR=""
    record ogclews-link SKIP "--no-link"
fi

# ── 5. register OG models with MUIOGO + verify everything ────────────────────
CURRENT_STEP="verify"
step "5/5 Register with MUIOGO + verification battery"
start_muiogo() {
    MUIOGO_OG_MODELS_DIR="$OG_HOME/og-models" MUIOGO_OG_DATA_DIR="$OG_HOME/og-state" \
        PORT="$PORT" "$MUIOGO_DIR/.venv/bin/python" "$MUIOGO_DIR/API/app.py" \
        > "$DEST/muiogo-server.log" 2>&1 &
    SERVER_PID=$!
    wait_api 60 || die "MUIOGO did not start for verification — see $DEST/muiogo-server.log"
}
start_muiogo

# 5a. register each OG model in MUIOGO's registry (async job; env already synced)
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

# 5b. verification battery
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
    record verify OK "demo solve + imports + link check"
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
python3 - "$DEST" "$MUIOGO_DIR" "$AI_DIR" "${LINK_DIR:-}" "$OG_JSON" "$PORT" "$OG_HOME" <<'PY'
import json, subprocess, sys, datetime, shutil
dest, muiogo, ai, link, og_json, port, og_home = sys.argv[1:8]
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
    "solvers": {"glpsol": ver("glpsol", "--version"), "cbc": shutil.which("cbc")},
}
out = f"{dest}/manifest.json"
with open(out, "w") as f:
    json.dump(manifest, f, indent=2)
print(f"  ok manifest: {out}")
PY
record manifest OK "$DEST/manifest.json"

report
echo ""
echo -e "  ${G}${B}MUIOGO-AI stack installed and verified.${N}"
echo    "  Workspace : $DEST"
echo    "  Manifest  : $DEST/manifest.json"
echo    "  Start MUIOGO headless:  $AI_DIR/client/.venv/bin/muiogo serve --root $MUIOGO_DIR"
exit 0
