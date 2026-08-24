# rubix-review backlog

Seeded at repo creation.
Deferred on purpose, not forgotten.

- Variable lens count: make the lens count a knob.
  One lens is sometimes enough, a third is sometimes wanted, and the current fixed two should be the default rather than the law.
- Raw-idea entry point: a Rubix pass at the raw-idea moment, before any drafted artifact exists.
- Lens-default behaviors: defaults for which role takes Lens A, A+B seat combinations, and per-artifact-type presets.
- Native-Windows install, and an npx cross-platform installer.

## Hardening (from the 2026-08-23 Rubix pass on the extraction plan)

Evidence and file:line citations for every item: [docs/2026-08-23.extraction-rubix-findings.md](docs/2026-08-23.extraction-rubix-findings.md).
Severity in brackets.
Items marked (loop-stack) land in the consumer repo; they are tracked here because this pass surfaced them and the two repos version together.

- [High] Onboarding: README block + clone story. (both repos)
  The remote is being created by the owner.
  Once it exists: add a "Getting rubix-review" block to THIS repo's README (clone URL, `bash install.sh`, the `RUBIX_INSTALL_DIR` override), and mirror loop-stack's ringer onboarding block in loop-stack's README (clone URL, `LOOP_STACK_RUBIX_ROOT` override).
  Done when: a fresh host can go from nothing to a wired contract using only README text, no tribal knowledge.

- [Med-High] Fail-closed recovery text carries the literal fix. (loop-stack)
  Replace the abstract "install rubix-review and re-run install.sh" wording in three places - `skills/loop-review/SKILL.md` contract section, `skills/loop-drive/SKILL.md` contract section, and the `install.sh:213-215` no-installer WARNING - with the two exact commands:
  `git clone <remote-url> ~/create/skills/rubix-review` then `bash <loop-stack-root>/install.sh`.
  One command per line, copy-pasteable, no menu.
  Done when: the blocked operator's next action is a paste, not a diagnosis.

- [Medium] Drift guard: checksum, not substring grep; resolve configured paths. (loop-stack, touches this repo's release ritual)
  Two defects share a fix.
  (a) `install.sh:191-194` `_clauses_ok()` accepts any file containing three phrases, so injected instructions wire through into reviewer prompts; replace with a `sha256` compare of the contract body between the START/END markers against a pinned expected hash shipped in loop-stack, refusing to wire on mismatch.
  (b) `tests/gates/reviewer-contract.sh:55-66` check 5 probes only `~/.agents/skills` and `~/.claude/skills`; make it resolve the same `host.env` / `AGENTS_SKILLS` / `SKILLS_DIR` chain install.sh uses so non-default layouts are checked instead of skip-noted.
  Requires a documented ritual here: any legitimate contract change bumps the pinned hash in loop-stack in the same change set (the two repos version together; this is the version-drift open question from the brief, answered by pinning).
  Done when: a contract edit that is not mirrored by a hash bump fails the consumer's install and gate, loudly.

- [Medium] Copy-mode staleness detection. (both repos)
  On the copy path (`loop-stack/install.sh:204-205`, and this installer's copy branch), also write a sidecar hash file next to the copied contract.
  The reviewer-contract gate then treats a wired file that is NOT a symlink as copy-mode and compares its hash to the resolved canonical, failing on mismatch instead of passing a stale copy forever.
  install.sh prints "contract is a COPY on this host - re-sync is manual" so the degraded invariant is visible at install time.
  Done when: a stale copy is a red gate, not a silent divergence.
  Note: the checksum work above supplies the hashing; do the two together.

- [Medium] Guard the installer's `rm -rf`. (this repo)
  `install.sh:31` runs `rm -rf "$DEST"` unconditionally before both branches; empty `RUBIX_INSTALL_DIR` is already safe via the `:-` default, but a relative or mistyped path is not.
  Add before the `rm -rf`:
  `case "$INSTALL_DIR" in /*) ;; *) echo "RUBIX_INSTALL_DIR must be an absolute path (got: $INSTALL_DIR)" >&2; exit 1;; esac`
  and assert `[ "$DEST" != "/" ]` for belt-and-braces.
  Extend `tests/install.sh` with a relative-path invocation asserting the refusal message and non-zero exit.
  Done when: the destructive line cannot fire on a non-absolute destination.

- [Medium] Document the `rubix-autorun` mapping. (loop-stack)
  The brief's binary "off by default" (meaning: offer, don't auto-run) shipped as the three-value `ask | off | on` with default `ask`; the token `off` changed meaning (now: skip silently).
  Add the missing doctrine paragraph for `rubix-autorun` to loop-stack `config/conventions.md` "Committed keys" (precedent: `autonomy-default`, `tracker`), including one line stating the brief-to-shipped mapping so the rename is a recorded decision.
  Done when: conventions.md explains all three values and the mapping.

- [Low] Rename `LOOP_STACK_FORCE_COPY` to `RUBIX_FORCE_COPY`. (this repo)
  `install.sh:5,33` and `tests/install.sh` carry the caller's name inside the standalone repo.
  Rename, and honor the old name as a deprecated alias for one release (`FORCE_COPY="${RUBIX_FORCE_COPY:-${LOOP_STACK_FORCE_COPY:-0}}"`) so loop-stack's existing test invocation keeps passing until it migrates.
  Done when: no `LOOP_STACK_` identifier remains here except the alias line.

- [Low] Uninstall path. (both repos)
  Removing loop-stack leaves this skill self-installed plus two dangling `references/` symlinks in the consumer skills.
  Minimum: a README note here naming the three paths to delete.
  Better: an `uninstall.sh` that removes `$RUBIX_INSTALL_DIR/rubix-review` and any consumer `references/reviewer-conduct-contract.md` symlink that resolves into this repo.
  Done when: teardown is documented or automated, not archaeology.

- [Low] Wave-order note in the extraction plan. (loop-stack)
  One line before Task 1 of `docs/plans/2026-08-23.rubix-standalone-skill-plan.md`: tasks are ordered by wave, not ID.
