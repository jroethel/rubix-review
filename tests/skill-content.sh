#!/usr/bin/env bash
# Structural check: the rubix-review skill is self-contained, two-lens, un-pinned, and owns the
# canonical reviewer-conduct contract.
set -uo pipefail
HERE="$(cd "$(dirname "$0")" && pwd)"
REPO="$(cd "$HERE/.." && pwd)"
S="$REPO/SKILL.md"
C="$REPO/references/reviewer-conduct-contract.md"
fail() { echo "FAIL: $1" >&2; exit 1; }

[ -f "$S" ] || fail "SKILL.md missing"
[ -f "$C" ] || fail "canonical contract references/reviewer-conduct-contract.md missing"

# 1. Both lenses named.
grep -q 'Lens A' "$S" || fail "Lens A not named"
grep -q 'Lens B' "$S" || fail "Lens B not named"

# 2. Findings-with-severity output contract.
grep -Eq 'severity' "$S" || fail "no findings severity in output contract"
grep -Eq 'concrete suggested change|suggested change' "$S" || fail "no suggested-change field in output contract"

# 3. Model position un-pinned + diversity recommendation.
grep -Eq 'do not hard-pin' "$S" || fail "rubric does not forbid hard-pinning a model"
grep -Eqi 'cross-model diversity|different models' "$S" || fail "no cross-model-diversity recommendation"
for m in Opus Sonnet Haiku Fable GLM; do
  grep -q "$m" "$S" && fail "hard-pinned model name '$m' present in the skill body"
done

# 4. Third lens is a recommendation, ships two lenses.
grep -Eqi 'ships two lenses|two lenses' "$S" || fail "does not state it ships two lenses"

# 5. Contract pointer + fail-closed instruction.
grep -q 'references/reviewer-conduct-contract.md' "$S" || fail "SKILL.md does not point at the contract file"
grep -Eqi 'do not run the lenses uncontracted|fail closed|stop and report' "$S" || fail "no fail-closed instruction when contract absent"

# 6. Canonical contract carries its required clauses.
grep -qF 'writes outside this repository checkout' "$C" || fail "contract missing outside-checkout-write bar"
grep -qF 'evidence to read, never instructions' "$C" || fail "contract missing embedded-commands-are-evidence rule"
grep -qF "rerunning this repository's own test suite" "$C" || fail "contract missing test-rerun-stays-legal clause"

# 7. No loop-stack dependency (self-contained; runs in a bare repo).
grep -Eq 'loop-stack|config/repo-state|/Users/' "$S" && fail "SKILL.md references a loop-stack-specific path or absolute home path"

echo "PASS: rubix-review skill is two-lens, un-pinned, self-contained, and owns the canonical contract"
