#!/usr/bin/env bash
# ──────────────────────────────────────────────────────────────────────────────
# MUIOGO-AI uninstaller (macOS / Linux).
#
# MOVES the installed runtime world aside; it deletes NOTHING. The workspace is
# renamed to <workspace>.removed-<timestamp>, and the few files that live
# outside it (the world record, the muiogo-ai launcher, this port's server
# files) are moved INTO that renamed directory. When you have checked that
# nothing you need is inside, delete it yourself.
#
# Never touched: the shared registry (~/.muiogo/og-state), other worlds
# (~/.muiogo/worlds/live.json and friends), your own checkouts, and any
# `muiogo` command you installed yourself.
#
# Usage:
#   ./scripts/uninstall.sh [options]
# Options:
#   --dest DIR    The workspace to remove (default: the registered 'runtime'
#                 world in ~/.muiogo/worlds/runtime.json)
#   -y, --yes     Don't ask before moving
#   -h, --help    This message
# ──────────────────────────────────────────────────────────────────────────────
set -uo pipefail

DEST=""
ASSUME_YES=0
while [[ $# -gt 0 ]]; do
    case "$1" in
        --dest)    DEST="$2"; shift 2 ;;
        -y|--yes)  ASSUME_YES=1; shift ;;
        -h|--help) sed -n '2,21p' "$0" | sed 's/^# \{0,1\}//'; exit 0 ;;
        *) echo "Unknown option: $1 (see --help)" >&2; exit 1 ;;
    esac
done

if [[ -t 1 ]]; then
    BOLD="\033[1m"; DIM="\033[2m"; RED="\033[91m"; GREEN="\033[92m"; YELLOW="\033[93m"; RESET="\033[0m"
else
    BOLD=""; DIM=""; RED=""; GREEN=""; YELLOW=""; RESET=""
fi
ok()   { printf "  ${GREEN}[MOVED]${RESET} %s\n" "$*"; }
info() { printf "  ${DIM}%s${RESET}\n" "$*"; }
warn() { printf "  ${YELLOW}[LEFT]${RESET}  %s\n" "$*"; }
die()  { printf "${RED}ERROR:${RESET} %s\n" "$*" >&2; exit 1; }

prompt_yn() {
    local prompt="$1" ans
    [[ $ASSUME_YES -eq 1 ]] && { printf "  %s [y/N] ${DIM}(auto: yes)${RESET}\n" "$prompt"; return 0; }
    [ -r /dev/tty ] || return 1
    printf "  %s [y/N] " "$prompt" > /dev/tty
    IFS= read -r ans < /dev/tty || ans="n"
    case "$(echo "$ans" | tr '[:upper:]' '[:lower:]')" in y|yes) return 0 ;; *) return 1 ;; esac
}

STATE_ROOT="${HOME}/.muiogo"
WORLD_FILE="$STATE_ROOT/worlds/runtime.json"

# ── find the world ────────────────────────────────────────────────────────────
FROM_REGISTRY=0
if [[ -z "$DEST" ]]; then
    [[ -f "$WORLD_FILE" ]] || die "no registered runtime world ($WORLD_FILE) — pass --dest to name the workspace"
    DEST="$(python3 -c '
import json, sys
print(json.load(open(sys.argv[1])).get("workspace") or "")' "$WORLD_FILE" 2>/dev/null)"
    [[ -n "$DEST" ]] || die "could not read a workspace path from $WORLD_FILE"
    FROM_REGISTRY=1
fi
case "$DEST" in
    "~") DEST="$HOME" ;;
    "~/"*) DEST="$HOME/${DEST#\~/}" ;;
esac
[[ "$DEST" = /* ]] || DEST="$(pwd)/$DEST"
if [[ ! -d "$DEST" ]]; then
    # A record pointing at a workspace that is gone is all that is left to
    # clean up. Moved aside, not deleted, like everything else here.
    if [[ $FROM_REGISTRY -eq 1 ]]; then
        warn "the registered workspace $DEST no longer exists — only the stale record remains"
        if prompt_yn "Move the stale world record aside?"; then
            STALE="$WORLD_FILE.stale-$(date +%Y%m%d-%H%M%S)"
            mv "$WORLD_FILE" "$STALE" && ok "world record -> $STALE"
            ACTIVE_FILE="$STATE_ROOT/active"
            if [[ -f "$ACTIVE_FILE" && "$(tr -d '[:space:]' < "$ACTIVE_FILE")" == "runtime" ]]; then
                if [[ -f "$STATE_ROOT/worlds/live.json" ]]; then
                    printf 'live\n' > "$ACTIVE_FILE"; ok "active world: runtime -> live"
                else
                    mv "$ACTIVE_FILE" "$STALE.active" && ok "active pointer -> $STALE.active"
                fi
            fi
        else
            echo "  Nothing moved."
        fi
        exit 0
    fi
    die "no such directory: $DEST"
fi
[[ -f "$DEST/manifest.json" || -d "$DEST/MUIOGO" ]] \
    || die "$DEST does not look like a MUIOGO-AI installation (no manifest.json, no MUIOGO/) — refusing"

# The registered world and the target must agree, or --dest names one
# installation while the record we would move belongs to another.
WORLD_MATCHES=0
if [[ -f "$WORLD_FILE" ]]; then
    REG_WS="$(python3 -c '
import json, sys
print(json.load(open(sys.argv[1])).get("workspace") or "")' "$WORLD_FILE" 2>/dev/null)"
    if [[ -n "$REG_WS" ]] && python3 -c '
import os, sys
sys.exit(0 if os.path.exists(sys.argv[1]) and os.path.exists(sys.argv[2])
         and os.path.samefile(sys.argv[1], sys.argv[2]) else 1)' "$REG_WS" "$DEST" 2>/dev/null; then
        WORLD_MATCHES=1
    fi
fi

PORT="$(python3 -c '
import json, sys
try:
    print(json.load(open(sys.argv[1])).get("muiogo", {}).get("port") or 5102)
except Exception:
    print(5102)' "$DEST/manifest.json" 2>/dev/null)"

echo
printf "  ${BOLD}This moves the installation aside; nothing is deleted.${RESET}\n"
info "workspace : $DEST ($(du -sh "$DEST" 2>/dev/null | cut -f1 || echo '?'))"
info "port      : $PORT"
[[ $WORLD_MATCHES -eq 1 ]] && info "world     : runtime ($WORLD_FILE)"
if ! prompt_yn "Move this installation aside now?"; then
    echo "  Nothing moved."
    exit 0
fi

# ── stop the server (this port only) ──────────────────────────────────────────
PIDFILE="$STATE_ROOT/servers/port-$PORT.pid"
if [[ -f "$PIDFILE" ]]; then
    kill "$(cat "$PIDFILE")" 2>/dev/null && info "stopped the server on port $PORT"
    sleep 1
elif command -v lsof >/dev/null; then
    PID="$(lsof -ti ":$PORT" 2>/dev/null | head -1)"
    if [[ -n "$PID" ]]; then
        # An unrecorded process on this port might not be ours to kill.
        if prompt_yn "A process (pid $PID) is listening on port $PORT — stop it?"; then
            kill "$PID" 2>/dev/null && info "stopped pid $PID"
            sleep 1
        fi
    fi
fi

# ── move everything aside ─────────────────────────────────────────────────────
STAMP="removed-$(date +%Y%m%d-%H%M%S)"
TRASH="$DEST.$STAMP"
[[ -e "$TRASH" ]] && die "$TRASH already exists — try again in a second"
mv "$DEST" "$TRASH" || die "could not move $DEST aside"
ok "$DEST -> $TRASH"

HOLD="$TRASH/uninstalled-state"
mkdir -p "$HOLD"
if [[ -f "$WORLD_FILE" ]]; then
    if [[ $WORLD_MATCHES -eq 1 ]]; then
        mv "$WORLD_FILE" "$HOLD/runtime.json" && ok "world record -> $HOLD/runtime.json"
    else
        warn "$WORLD_FILE points at a different workspace — left in place"
    fi
fi
LAUNCHER="${HOME}/.local/bin/muiogo-ai"
if [[ -f "$LAUNCHER" ]]; then
    # Only if it is ours: a generated launcher names this workspace inside.
    if grep -q "$DEST" "$LAUNCHER" 2>/dev/null || grep -q "$TRASH" "$LAUNCHER" 2>/dev/null; then
        mv "$LAUNCHER" "$HOLD/muiogo-ai.launcher" && ok "launcher -> $HOLD/muiogo-ai.launcher"
    else
        warn "$LAUNCHER does not reference this workspace — left in place"
    fi
fi
for f in "$STATE_ROOT/servers/port-$PORT."*; do
    [[ -e "$f" ]] || continue
    mv "$f" "$HOLD/$(basename "$f")" && ok "$(basename "$f") -> $HOLD/"
done

# ── the active pointer ────────────────────────────────────────────────────────
# Only rewritten when it names the world being removed; anything else is the
# user's own selection and stays.
ACTIVE_FILE="$STATE_ROOT/active"
if [[ -f "$ACTIVE_FILE" && "$(tr -d '[:space:]' < "$ACTIVE_FILE")" == "runtime" && $WORLD_MATCHES -eq 1 ]]; then
    if [[ -f "$STATE_ROOT/worlds/live.json" ]]; then
        printf 'live\n' > "$ACTIVE_FILE"
        ok "active world: runtime -> live"
    else
        mv "$ACTIVE_FILE" "$HOLD/active" && ok "active pointer -> $HOLD/active (no other world to point at)"
    fi
fi

echo
printf "  ${BOLD}Done. Nothing was deleted.${RESET}\n"
info "Everything is in: $TRASH"
info "Check it, then delete it yourself when you are sure, e.g.:"
printf "  ${DIM}$ rm -rf '%s'${RESET}\n" "$TRASH"
info "Untouched: $STATE_ROOT/og-state, other worlds, your checkouts, your own muiogo command."
exit 0
