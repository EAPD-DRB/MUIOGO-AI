#!/usr/bin/env bash
# ──────────────────────────────────────────────────────────────────────────────
# MUIOGO-AI skills installer for macOS and Linux.
#
# You do NOT need this to use the skills inside this repository: they live in
# .agents/skills/ (read by Codex) with .claude/skills/ symlinks (read by Claude
# Code), so both assistants pick them up automatically when you work here.
#
# Use this script to make the skills available EVERYWHERE ELSE — your own model
# repositories, or every project you open:
#   1. Read the catalogue in .agents/skills/ (one folder per skill)
#   2. Ask which assistant you use (or take --tool / --dir)
#   3. Copy the selected skills there, replacing any older copy
#   4. Report what was installed
#
# Skills are plain folders of Markdown and helper scripts. Nothing is installed
# system-wide, nothing is downloaded, and nothing outside the target folder is
# touched.
#
# Usage:
#   ./scripts/install-skills.sh                      # interactive
#   ./scripts/install-skills.sh --tool claude        # skip the menu
#   ./scripts/install-skills.sh --tool both --yes    # hands-free
#   ./scripts/install-skills.sh --only og-run-preflight,og-solver-diagnosis
#   ./scripts/install-skills.sh --relink             # rebuild in-repo symlinks
#   ./scripts/install-skills.sh --help
# ──────────────────────────────────────────────────────────────────────────────
set -uo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]:-$0}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
SKILLS_DIR="$PROJECT_ROOT/.agents/skills"
CLAUDE_LINK_DIR="$PROJECT_ROOT/.claude/skills"

# ── Assistant catalog ─────────────────────────────────────────────────────────
# Each entry: KEY|DISPLAY NAME|SKILLS DIRECTORY
ASSISTANTS=(
    "claude|Claude Code|$HOME/.claude/skills"
    "codex|Codex|$HOME/.codex/skills"
)

# ── Defaults ──────────────────────────────────────────────────────────────────
TOOL=""
TARGET_DIRS=""
ONLY=""
ASSUME_YES=0
DO_LIST=0
DO_LIST_JSON=0
DO_RELINK=0

usage() {
    cat <<EOF
MUIOGO-AI skills installer (macOS and Linux).

Usage:
  $0 [options]

Options:
  -h, --help              Show this message and exit.
      --list              Print the skill catalogue (human-readable) and exit.
      --list-json         Print the skill catalogue as JSON and exit.
      --relink            Rebuild this repo's .claude/skills symlinks (one per
                          skill, pointing at .agents/skills) and exit. Run this
                          after adding or renaming a skill.
  -y, --yes               Auto-confirm every prompt (non-interactive). Requires
                          --tool or --dir, since the assistant cannot be guessed.
      --tool KEY          Install for a known assistant: claude, codex, or both.
      --dir DIR           Install into a folder you name (repeatable via commas).
      --only NAMES        Install just these skills (comma-separated; see --list).
                          Default: every skill in the catalogue.

Examples:
  $0                                          # interactive
  $0 --tool claude                            # menu skipped
  $0 --tool both --yes                        # hands-free, both assistants
  $0 --dir ~/.config/myassistant/skills       # somewhere else
  $0 --only og-run-preflight --tool claude    # one skill
EOF
}

while [[ $# -gt 0 ]]; do
    case "$1" in
        --tool)      TOOL="$2";        shift 2 ;;
        --dir)       TARGET_DIRS="$2"; shift 2 ;;
        --only)      ONLY="$2";        shift 2 ;;
        -y|--yes)    ASSUME_YES=1;     shift ;;
        --list)      DO_LIST=1;        shift ;;
        --list-json) DO_LIST_JSON=1;   shift ;;
        --relink)    DO_RELINK=1;      shift ;;
        -h|--help)   usage; exit 0 ;;
        *) echo "Unknown option: $1" >&2; exit 1 ;;
    esac
done

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

section() { echo; hr; printf "  ${BOLD}%s${RESET}\n" "$1"; hr; }

err() { printf "${RED}ERROR:${RESET} %s\n" "$1" >&2; exit 2; }

# Look up an assistant by key; sets ASSISTANT_NAME / ASSISTANT_DIR.
ASSISTANT_NAME=""; ASSISTANT_DIR=""
lookup_assistant() {
    local entry k name dir
    for entry in "${ASSISTANTS[@]}"; do
        IFS='|' read -r k name dir <<< "$entry"
        if [ "$k" = "$1" ]; then
            ASSISTANT_NAME="$name"; ASSISTANT_DIR="$dir"; return 0
        fi
    done
    return 1
}

# ── Read the catalogue ────────────────────────────────────────────────────────
[[ -d "$SKILLS_DIR" ]] || err "no skills folder at $SKILLS_DIR"

AVAILABLE=()
for d in "$SKILLS_DIR"/*/; do
    [[ -f "${d}SKILL.md" ]] && AVAILABLE+=("$(basename "$d")")
done
[[ ${#AVAILABLE[@]} -gt 0 ]] || err "no skills found in $SKILLS_DIR"

# One-line description from a skill's SKILL.md frontmatter.
skill_desc() {
    python3 - "$SKILLS_DIR/$1/SKILL.md" <<'PY' 2>/dev/null || true
import re, sys
try:
    text = open(sys.argv[1], encoding="utf-8").read()
except OSError:
    sys.exit(0)
m = re.search(r"^---\s*\n(.*?)\n---", text, re.S)
if not m:
    sys.exit(0)
d = re.search(r"^description:\s*(.*?)(?=^[a-zA-Z_-]+:|\Z)", m.group(1), re.S | re.M)
if not d:
    sys.exit(0)
desc = " ".join(d.group(1).replace(">-", "").replace('"', "").split())
sentence = re.split(r"(?<=[.!?])\s", desc)[0]
print(sentence[:96])
PY
}

# ── In-repo symlinks (Claude Code reads .claude/skills; a per-skill entry may
# be a symlink, which is the form Claude Code documents as supported) ─────────
if [[ $DO_RELINK -eq 1 ]]; then
    section "Rebuilding .claude/skills symlinks"
    mkdir -p "$CLAUDE_LINK_DIR" || err "cannot create $CLAUDE_LINK_DIR"
    # Drop existing symlinks only; never touch a real directory someone added.
    for existing in "$CLAUDE_LINK_DIR"/*; do
        [[ -L "$existing" ]] && rm -f "$existing"
    done
    for s in "${AVAILABLE[@]}"; do
        ln -sfn "../../.agents/skills/$s" "$CLAUDE_LINK_DIR/$s"
        if [[ -f "$CLAUDE_LINK_DIR/$s/SKILL.md" ]]; then
            print_pass "$s"
        else
            print_fail "$s" "symlink does not resolve"
        fi
    done
    echo
    printf "  %d symlinks rebuilt in .claude/skills\n" "${#AVAILABLE[@]}"
    exit 0
fi

if [[ $DO_LIST -eq 1 ]]; then
    printf "  ${BOLD}%-30s %s${RESET}\n" "SKILL" "WHAT IT DOES"
    for s in "${AVAILABLE[@]}"; do
        printf "  %-30s %s\n" "$s" "$(skill_desc "$s")"
    done
    exit 0
fi

if [[ $DO_LIST_JSON -eq 1 ]]; then
    {
        printf '{\n  "schema_version": 1,\n  "skills": [\n'
        i=0
        for s in "${AVAILABLE[@]}"; do
            i=$((i + 1))
            comma=","; [[ $i -eq ${#AVAILABLE[@]} ]] && comma=""
            printf '    { "name": "%s", "description": "%s" }%s\n' \
                "$s" "$(skill_desc "$s" | sed 's/"/\\"/g')" "$comma"
        done
        printf '  ]\n}\n'
    }
    exit 0
fi

# ── Which skills ──────────────────────────────────────────────────────────────
SELECTED=()
if [[ -n "$ONLY" ]]; then
    IFS=',' read -ra WANT <<< "$ONLY"
    for w in "${WANT[@]}"; do
        w="$(echo "$w" | tr -d '[:space:]')"
        [[ -z "$w" ]] && continue
        found=0
        for a in "${AVAILABLE[@]}"; do [[ "$a" == "$w" ]] && found=1; done
        [[ $found -eq 1 ]] || err "no such skill: '$w' (see --list)"
        SELECTED+=("$w")
    done
    [[ ${#SELECTED[@]} -gt 0 ]] || err "--only given but no skill names parsed"
else
    SELECTED=("${AVAILABLE[@]}")
fi

# ── Where to install ──────────────────────────────────────────────────────────
choose_assistant_interactive() {
    if [ ! -r /dev/tty ]; then
        printf "${RED}ERROR:${RESET} no --tool/--dir given and there is no terminal to ask on.\n" >&2
        exit 2
    fi
    echo
    hr_thick
    printf "  ${BOLD}MUIOGO-AI Skills Installer${RESET}\n"
    hr_thick
    printf "  %d skills are ready to install.\n" "${#SELECTED[@]}"
    printf "  ${DIM}Which AI assistant should they go to?${RESET}\n"
    echo
    local i=1 entry k name dir
    for entry in "${ASSISTANTS[@]}"; do
        IFS='|' read -r k name dir <<< "$entry"
        printf "    %d) %-14s -- %s\n" "$i" "$name" "$dir"
        i=$((i + 1))
    done
    printf "    %d) Both of the above\n" "$i"; local both_choice=$i; i=$((i + 1))
    printf "    %d) Other (type a folder)\n" "$i"; local other_choice=$i; i=$((i + 1))
    printf "    %d) Skip for now\n" "$i"; local skip_choice=$i
    echo
    while true; do
        printf "  Choice [1-%d]: " "$skip_choice" > /dev/tty
        local choice=""
        IFS= read -r choice < /dev/tty || choice="$skip_choice"
        if ! printf '%s' "$choice" | grep -Eq '^[0-9]+$'; then
            printf "  Please enter a number.\n"; continue
        fi
        if [ "$choice" -lt 1 ] || [ "$choice" -gt "$skip_choice" ]; then
            printf "  Out of range.\n"; continue
        fi
        if [ "$choice" -eq "$skip_choice" ]; then
            echo
            printf "  Nothing installed. You can always install them yourself, any time:\n"
            echo_cmd "./scripts/install-skills.sh"
            printf "  Or copy any folder from skills/ into your assistant's skills folder.\n"
            exit 0
        fi
        if [ "$choice" -eq "$other_choice" ]; then
            printf "  Folder : " > /dev/tty
            local dirin=""
            IFS= read -r dirin < /dev/tty || true
            if [ -z "$dirin" ]; then printf "  No folder given.\n"; continue; fi
            TARGET_DIRS="$dirin"; return 0
        fi
        if [ "$choice" -eq "$both_choice" ]; then
            local all=""
            for entry in "${ASSISTANTS[@]}"; do
                IFS='|' read -r k name dir <<< "$entry"
                all="${all:+$all,}$dir"
            done
            TARGET_DIRS="$all"; return 0
        fi
        # A numbered assistant
        local n=1
        for entry in "${ASSISTANTS[@]}"; do
            IFS='|' read -r k name dir <<< "$entry"
            if [ "$n" -eq "$choice" ]; then TARGET_DIRS="$dir"; return 0; fi
            n=$((n + 1))
        done
    done
}

if [[ -z "$TARGET_DIRS" ]]; then
    case "$TOOL" in
        both)
            for entry in "${ASSISTANTS[@]}"; do
                IFS='|' read -r k name dir <<< "$entry"
                TARGET_DIRS="${TARGET_DIRS:+$TARGET_DIRS,}$dir"
            done
            ;;
        "")
            if [[ $ASSUME_YES -eq 1 ]]; then
                err "--yes needs --tool (claude|codex|both) or --dir: the assistant cannot be guessed."
            fi
            choose_assistant_interactive
            ;;
        *)
            lookup_assistant "$TOOL" \
                || err "unknown --tool '$TOOL'. Known: claude, codex, both (or use --dir)."
            TARGET_DIRS="$ASSISTANT_DIR"
            ;;
    esac
fi

# ── Install ───────────────────────────────────────────────────────────────────
START_TIME="$(date +%s)"
INSTALLED=0
FAILED=0

IFS=',' read -ra DESTS <<< "$TARGET_DIRS"
for dest in "${DESTS[@]}"; do
    dest="$(echo "$dest" | sed 's/^[[:space:]]*//;s/[[:space:]]*$//')"
    dest="${dest/#\~/$HOME}"
    [[ -z "$dest" ]] && continue

    section "Installing ${#SELECTED[@]} skills into $dest"
    if ! mkdir -p "$dest" 2>/dev/null; then
        print_fail "$dest" "cannot create folder"
        FAILED=$((FAILED + 1))
        continue
    fi
    for s in "${SELECTED[@]}"; do
        # Replace any older copy so re-running updates cleanly.
        rm -rf "$dest/$s"
        if cp -R "$SKILLS_DIR/$s" "$dest/$s" 2>/dev/null; then
            print_pass "$s"
            INSTALLED=$((INSTALLED + 1))
        else
            print_fail "$s" "copy failed"
            FAILED=$((FAILED + 1))
        fi
    done
done

# ── Summary ───────────────────────────────────────────────────────────────────
ELAPSED=$(( $(date +%s) - START_TIME ))
echo
hr_thick
printf "  ${BOLD}Summary${RESET}\n"
hr_thick
printf "  Installed : %d\n" "$INSTALLED"
[[ $FAILED -gt 0 ]] && printf "  Failed    : %d\n" "$FAILED"
printf "  Elapsed   : %ds\n" "$ELAPSED"
echo

if [[ $INSTALLED -gt 0 && $FAILED -eq 0 ]]; then
    printf "  ${GREEN}${BOLD}Skills installed.${RESET}\n"
    echo
    printf "  Restart your assistant (or reload the window) so it picks them up, then\n"
    printf "  ask for the job in plain language, for example:\n"
    printf "    ${DIM}\"assess the calibration of this CLEWs model\"${RESET}\n"
    printf "    ${DIM}\"run the preflight checks before I start this solve\"${RESET}\n"
    echo
    printf "  Catalogue and descriptions : skills/README.md\n"
    exit 0
elif [[ $INSTALLED -gt 0 ]]; then
    printf "  ${YELLOW}${BOLD}Some skills did not install -- review the output above.${RESET}\n"
    exit 1
else
    printf "  ${RED}${BOLD}Nothing was installed -- review the output above.${RESET}\n"
    exit 1
fi
