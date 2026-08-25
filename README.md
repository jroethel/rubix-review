rubix-review is a standalone review skill for proposed artifacts - plans, specs, designs, PRDs, drafts - that runs a forward-looking two-lens pass before anything gets built: Lens A takes the seat of the professional most impacted by the artifact, Lens B does a cold craft read against best practice, and both run as parallel fresh-context subagents that see only the artifact and its optional spec, never the caller's conversation.
Invoke it ad hoc with "use the rubix review", "rubix this", or "rubix review on <artifact>".
Input is a required artifact path plus an optional spec/criteria path and an optional high-stakes flag, and with no spec it still runs and returns findings rather than erroring.
Output is side-by-side findings per lens, each finding carrying {finding, severity, rationale, concrete suggested change}, with the reviewer never rewriting the artifact and the caller picking what gets incorporated.

## Getting rubix-review

```sh
git clone https://github.com/jroethel/rubix-review.git ~/create/skills/rubix-review
cd ~/create/skills/rubix-review
./install.sh
```

`install.sh` materializes the skill at `$RUBIX_INSTALL_DIR/rubix-review` (default `~/.agents/skills`), preferring a symlink and falling back to a copy.
Override the destination with `RUBIX_INSTALL_DIR=/abs/path ./install.sh`; it must be an absolute path.

loop-stack self-installs rubix-review for you: its own `install.sh` runs this installer from `LOOP_STACK_RUBIX_ROOT` (default `~/create/skills/rubix-review`), so on a loop-stack host you only need the clone above at that path.

## Uninstall

Removing loop-stack does not remove this skill. To tear it down, delete:

- `$RUBIX_INSTALL_DIR/rubix-review` (the installed skill, default `~/.agents/skills/rubix-review`)
- any `references/reviewer-conduct-contract.md` symlink in a consumer skill (e.g. `loop-review`, `loop-drive`) that resolves into this repo
- this repo's own checkout, if you no longer need it
