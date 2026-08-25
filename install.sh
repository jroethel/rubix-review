#!/usr/bin/env bash
# Idempotent installer for the rubix-review skill.
# Materializes the skill at $RUBIX_INSTALL_DIR/rubix-review, preferring a
# symlink to this checkout and falling back to a copy when symlinks are
# unavailable (e.g. WSL/Windows filesystems), or when RUBIX_FORCE_COPY=1.
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
# Refuse a non-absolute destination so a relative or mistyped RUBIX_INSTALL_DIR
# can never turn the rm -rf below loose on the wrong tree.
case "$INSTALL_DIR" in
  /*) ;;
  *) echo "RUBIX_INSTALL_DIR must be an absolute path (got: $INSTALL_DIR)" >&2; exit 1;;
esac
[ "$DEST" != "/" ] || { echo "refusing to operate on /" >&2; exit 1; }
rm -rf "$DEST"

# RUBIX_FORCE_COPY forces the copy branch; LOOP_STACK_FORCE_COPY is the
# deprecated alias, honored for one release until loop-stack migrates.
FORCE_COPY="${RUBIX_FORCE_COPY:-${LOOP_STACK_FORCE_COPY:-0}}"
if [ "$FORCE_COPY" != "1" ] && can_symlink; then
  ln -sfn "$REPO" "$DEST"
  echo "installed rubix-review -> $DEST (symlink to $REPO)"
else
  cp -R "$REPO" "$DEST"
  echo "installed rubix-review -> $DEST (copy of $REPO)"
fi
