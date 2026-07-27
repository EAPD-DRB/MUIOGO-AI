#!/usr/bin/env bash
# Install MUIOGO at the pinned ref for reproducible research runs.
#
# Clones (or updates) MUIOGO into ./muiogo-install/ (gitignored), checks out
# the ref in scripts/MUIOGO_PIN, and runs MUIOGO's own environment setup.
# Bump the pin deliberately, in its own commit, after checking runs still pass.
set -euo pipefail

REPO_URL="${MUIOGO_REPO_URL:-https://github.com/EAPD-DRB/MUIOGO.git}"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(dirname "$SCRIPT_DIR")"
PIN="$(tr -d '[:space:]' < "$SCRIPT_DIR/MUIOGO_PIN")"
TARGET="$ROOT_DIR/muiogo-install"

if [ ! -d "$TARGET/.git" ]; then
    git clone "$REPO_URL" "$TARGET"
fi

git -C "$TARGET" fetch origin
git -C "$TARGET" checkout --detach "$PIN"
echo "MUIOGO checked out at pinned ref: $(git -C "$TARGET" rev-parse --short=8 HEAD)"

cd "$TARGET"
uv sync
echo "Done. Start the server from $TARGET (see MUIOGO's scripts/start.sh)."
