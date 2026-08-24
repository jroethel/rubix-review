#!/usr/bin/env bash
# Idempotent installer for the rubix-review skill.
# Materializes the skill at $RUBIX_INSTALL_DIR/rubix-review, preferring a
# symlink to this checkout and falling back to a copy when symlinks are
# unavailable (e.g. WSL/Windows filesystems), or when LOOP_STACK_FORCE_COPY=1.
set -euo pipefail

REPO="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd -P)"
INSTALL_DIR="${RUBIX_INSTALL_DIR:-$HOME/.agents/skills}"
DEST="$INSTALL_DIR/rubix-review"

mkdir -p "$INSTALL_DIR"

# Detect symlink support by trying a real link inside the install dir and
# checking the result (a link that both exists and is a link), not by OS.
can_symlink() {
  local target="$INSTALL_DIR/.rubix-probe.$$"
  local link="$INSTALL_DIR/.rubix-probe-link.$$"
  : > "$target"
  if ln -s "$target" "$link" 2>/dev/null; then
    local ok=0
    [ -L "$link" ] && [ -e "$link" ] && ok=1
    rm -f "$link"
  fi
  rm -f "$target"
  [ "${ok:-0}" -eq 1 ]
}

# Remove any prior install (ours alone; nothing else in INSTALL_DIR is touched)
# so both branches below are idempotent, including across mode switches.
rm -rf "$DEST"

if [ "${LOOP_STACK_FORCE_COPY:-0}" != "1" ] && can_symlink; then
  ln -sfn "$REPO" "$DEST"
  echo "installed rubix-review -> $DEST (symlink to $REPO)"
else
  cp -R "$REPO" "$DEST"
  echo "installed rubix-review -> $DEST (copy of $REPO)"
fi
