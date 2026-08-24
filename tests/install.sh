#!/usr/bin/env bash
# Install into a throwaway AGENTS_SKILLS and assert the skill + canonical contract land there.
set -uo pipefail
HERE="$(cd "$(dirname "$0")" && pwd)"
REPO="$(cd "$HERE/.." && pwd)"
fail() { echo "FAIL: $1" >&2; exit 1; }

TMP="$(mktemp -d)"; trap 'rm -rf "$TMP"' EXIT
[ -x "$REPO/install.sh" ] || fail "install.sh missing or not executable"

RUBIX_INSTALL_DIR="$TMP/skills" bash "$REPO/install.sh" >/dev/null \
  || fail "install.sh exited non-zero"

DEST="$TMP/skills/rubix-review"
[ -e "$DEST/SKILL.md" ] || fail "SKILL.md not installed at $DEST"
CFILE="$DEST/references/reviewer-conduct-contract.md"
[ -e "$CFILE" ] || fail "canonical contract not present at $CFILE"
grep -qF 'writes outside this repository checkout' "$CFILE" \
  || fail "installed contract missing its required clause"

# Idempotent: a second run must also succeed.
RUBIX_INSTALL_DIR="$TMP/skills" bash "$REPO/install.sh" >/dev/null \
  || fail "install.sh not idempotent (second run failed)"

# Forced-copy path (the symlink-unavailable branch that WSL/Windows hit) must also land the contract.
COPYDIR="$TMP/copy"
LOOP_STACK_FORCE_COPY=1 RUBIX_INSTALL_DIR="$COPYDIR" bash "$REPO/install.sh" >/dev/null \
  || fail "forced-copy install failed"
[ -f "$COPYDIR/rubix-review/references/reviewer-conduct-contract.md" ] \
  || fail "forced-copy install did not materialize the contract as a real file"
[ -L "$COPYDIR/rubix-review" ] && fail "forced-copy install left a symlink, not a copy"

echo "PASS: rubix-review installs (symlink + forced-copy) with the canonical contract, idempotently"
