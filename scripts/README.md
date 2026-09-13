# extract_rubix_corpus.py

Builds a corpus of rubix-review evidence from local Claude Code session history: every lens dispatch, its parsed findings (title, severity, rationale, suggested change), the triage narrative that followed, plus any memory files and `*rubix*.md` docs that mention rubix.
It is a personal analysis tool, not part of the rubix-review skill itself - it never ships to consumers and its output must never be committed to this repo (public remote, private conversation content).

Stdlib only, no dependencies.
Python 3.9+.

## Run it

```sh
python3 scripts/extract_rubix_corpus.py
```

Writes to `~/.claude/rubix_corpus.<hostname>.json` by default (hostname-stamped so two hosts' runs never collide) and prints a summary (event/finding/severity counts) to stdout.

Check the parser first, if you like:

```sh
python3 scripts/extract_rubix_corpus.py --selftest
```

## Options

| Flag | Default | Purpose |
| --- | --- | --- |
| `--since DATE` | `2026-07-17` | ISO date floor - the loop-stack-session commit that first wired rubix-review into loop-plan. |
| `--projects-dir DIR` | `<claude-dir>/projects` | A Claude `projects` directory to scan. Repeatable. |
| `--repo-root DIR` | (none) | Extra directory to scan for `*rubix*.md` supplementary docs. Repeatable. Always includes the cwd and every event's cwd regardless. |
| `--claude-dir DIR` | `~/.claude` | Only used to derive the default `--projects-dir`. |
| `--out PATH` | `~/.claude/rubix_corpus.<hostname>.json` | Where the JSON corpus is written. |

## Combining with another host

Two ways, pick whichever fits how the other host's data reaches this machine.

Single run, both hosts at once: copy or mount the other host's `.claude/projects` locally, then pass both:

```sh
python3 scripts/extract_rubix_corpus.py \
  --projects-dir ~/.claude/projects \
  --projects-dir /mnt/hostb/.claude/projects
```

Separate runs, merge later: run the script unmodified on each host (each gets its own hostname-stamped `--out`), then combine the two JSON files downstream.
`events`, `memory_evidence`, and `supplementary_docs` are flat lists carrying absolute source paths, so concatenating them and de-duping by path is enough - no merge tooling is provided here because none was needed for that.

## Output shape

```json
{
  "generated_at": "...",
  "since": "2026-07-17",
  "projects_dirs": ["..."],
  "events": [
    {
      "project_dir_slug": "...",
      "session_id": "...",
      "parent_session_path": "...",
      "cwd": "...",
      "timestamp": "...",
      "invocation": {"skill": "rubix-review", "args": "...", "timestamp": "..."},
      "lenses": [
        {
          "description": "Rubix Lens A review",
          "model": "opus",
          "raw_text": "...",
          "findings": [
            {"number": 1, "title": "...", "severity": "major", "rationale": "...", "suggested_change": "...", "raw_block": "..."}
          ]
        }
      ],
      "narrative_after": [{"role": "assistant", "text": "..."}]
    }
  ],
  "memory_evidence": [{"path": "...", "content": "..."}],
  "supplementary_docs": [{"path": "...", "content": "..."}],
  "summary": {"total_events": 0, "total_lens_dispatches": 0, "total_findings_parsed": 0, "severity_counts": {}, "events_by_project": {}}
}
```

`findings` is best-effort: several finding-header and field-label formats are handled, but where parsing comes up short `severity`/`rationale`/`suggested_change` are `null` and `raw_block` still carries the full source text, so nothing is silently lost.
The corpus is raw evidence, not a distillation - counting, categorizing, and writing up the "wrong paths avoided" narrative is a separate reading pass over this JSON.
