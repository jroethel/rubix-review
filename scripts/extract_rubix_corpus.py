#!/usr/bin/env python3
"""Build a corpus of rubix-review evidence from local Claude Code session history.

Walks ~/.claude/projects/**/subagents/*.meta.json, keeps the ones whose
`description` names a rubix lens dispatch (the reliable marker: loop-plan and
rubix-review both launch lenses via the Agent tool with a "Rubix ..."
description, regardless of which skill triggered them), and pulls each lens's
final findings text plus its parent session's invocation/triage narrative.

Default time floor is 2026-07-17, the loop-stack-session commit that first
wired rubix-review into loop-plan (01993a1). Output defaults to a
hostname-stamped path outside any git repo, since the corpus quotes private,
cross-project session content that must never land in a git-tracked (and
here, public-remote) repo, and the stamp keeps two hosts' outputs from
colliding when gathered into one place.

To combine with another host's history: either point --projects-dir at that
host's copied/mounted `.claude/projects` (repeatable, one run covers both),
or run this script on each host separately (each gets its own hostname-
stamped --out) and merge the `events` / `memory_evidence` /
`supplementary_docs` lists downstream - they carry absolute source paths so
duplicates are easy to spot.

Usage:
    python3 scripts/extract_rubix_corpus.py [--since 2026-07-17] [--out PATH]
    python3 scripts/extract_rubix_corpus.py --projects-dir /mnt/hostb/.claude/projects
    python3 scripts/extract_rubix_corpus.py --selftest
"""
import argparse
import collections
import json
import re
import socket
import sys
from datetime import datetime, timezone
from pathlib import Path

DEFAULT_CLAUDE_DIR = Path.home() / ".claude"
DEFAULT_SINCE = "2026-07-17"
DEFAULT_OUT = Path.home() / ".claude" / f"rubix_corpus.{socket.gethostname()}.json"

HEADER_RE = re.compile(
    r"(?m)^(?:\*\*(?:Finding\s*)?(\d+)[.):]|#{2,4}\s*(\d+)[.):]|(\d+)\.\s+\*\*)"
)
FIELD_LABELS = {
    "severity": ["severity"],
    "rationale": ["rationale", "why", "explanation"],
    "suggested_change": [
        "concrete suggested change",
        "suggested change",
        "recommended fix",
        "recommendation",
        "fix",
    ],
}


def parse_ts(s):
    if not s:
        return None
    try:
        return datetime.fromisoformat(s.replace("Z", "+00:00"))
    except ValueError:
        return None


def load_jsonl(path):
    records = []
    try:
        with open(path, encoding="utf-8", errors="ignore") as fh:
            for line in fh:
                line = line.strip()
                if not line:
                    continue
                try:
                    records.append(json.loads(line))
                except json.JSONDecodeError:
                    continue
    except OSError:
        return []
    return records


def assistant_texts(records):
    out = []
    for i, rec in enumerate(records):
        msg = rec.get("message")
        if not isinstance(msg, dict) or msg.get("role") != "assistant":
            continue
        for block in msg.get("content") or []:
            if isinstance(block, dict) and block.get("type") == "text" and block.get("text", "").strip():
                out.append((i, rec.get("timestamp"), block["text"]))
    return out


def iter_tool_uses(records):
    for i, rec in enumerate(records):
        msg = rec.get("message")
        if not isinstance(msg, dict):
            continue
        for block in msg.get("content") or []:
            if isinstance(block, dict) and block.get("type") == "tool_use":
                yield i, rec.get("timestamp"), block.get("name"), (block.get("input") or {})


def find_rubix_dispatches(records):
    return [
        (i, ts, inp)
        for i, ts, name, inp in iter_tool_uses(records)
        if name == "Agent" and "rubix" in (inp.get("description") or "").lower()
    ]


def find_skill_invocation(records, skill_name):
    for i, ts, name, inp in iter_tool_uses(records):
        if name == "Skill" and inp.get("skill") == skill_name:
            return i, ts, inp.get("args")
    return None


def human_text(content):
    if isinstance(content, str):
        s = content.strip()
        return s if s and not s.startswith("<") else None
    if isinstance(content, list):
        parts = [b.get("text", "") for b in content if isinstance(b, dict) and b.get("type") == "text"]
        s = "\n".join(p for p in parts if p.strip())
        return s or None
    return None


def narrative_after(records, after_index, cap=10):
    out = []
    for i in range(after_index + 1, len(records)):
        if len(out) >= cap:
            break
        msg = records[i].get("message")
        if not isinstance(msg, dict):
            continue
        if msg.get("role") == "assistant":
            for block in msg.get("content") or []:
                if isinstance(block, dict) and block.get("type") == "text" and block.get("text", "").strip():
                    out.append({"role": "assistant", "timestamp": records[i].get("timestamp"), "text": block["text"]})
        elif msg.get("role") == "user":
            txt = human_text(msg.get("content"))
            if txt:
                out.append({"role": "user", "timestamp": records[i].get("timestamp"), "text": txt})
    return out


def extract_field(block, labels):
    for label in labels:
        m = re.search(rf"\*{{0,2}}{re.escape(label)}\*{{0,2}}\s*:\s*\*{{0,2}}\s*(.+)", block, re.I)
        if m:
            return re.sub(r"\*+$", "", m.group(1).strip()).strip()
    return None


def clean_title(first_line):
    t = first_line.strip()
    t = re.sub(r"^\*+", "", t)
    t = re.sub(r"^#{2,4}\s*", "", t)
    t = re.sub(r"^(?:Finding\s*)?\d+[.):]\s*[-—]?\s*", "", t, flags=re.I)
    return re.sub(r"\*+$", "", t).strip()


def parse_findings(text):
    matches = list(HEADER_RE.finditer(text))
    findings = []
    for idx, m in enumerate(matches):
        start = m.start()
        end = matches[idx + 1].start() if idx + 1 < len(matches) else len(text)
        block = text[start:end]
        lines = block.splitlines()
        num = next((g for g in m.groups() if g), None)
        title = clean_title(lines[0]) if lines else ""
        if not title:
            title = extract_field(block, ["finding"]) or ""
        findings.append(
            {
                "number": int(num) if num else idx + 1,
                "title": title,
                "severity": extract_field(block, FIELD_LABELS["severity"]),
                "rationale": extract_field(block, FIELD_LABELS["rationale"]),
                "suggested_change": extract_field(block, FIELD_LABELS["suggested_change"]),
                "raw_block": block.strip(),
            }
        )
    return findings


def normalize_severity(raw):
    s = (raw or "").lower()
    if "critical" in s or "blocker" in s:
        return "critical"
    if "high" in s or "major" in s:
        return "high"
    if "med" in s or "moderate" in s:
        return "medium"
    if "low" in s or "minor" in s:
        return "low"
    return "other"


def scan_memory_evidence(projects_dirs):
    out = []
    for projects_dir in projects_dirs:
        for path in sorted(projects_dir.glob("*/memory/*.md")):
            try:
                content = path.read_text(encoding="utf-8", errors="ignore")
            except OSError:
                continue
            if "rubix" in content.lower():
                out.append({"path": str(path), "content": content})
    return out


def scan_supplementary_docs(roots):
    out, seen = [], set()
    skip_dirs = {".git", "node_modules", ".venv"}
    for root in roots:
        if not root.is_dir():
            continue
        for path in root.rglob("*"):
            if skip_dirs & set(path.parts):
                continue
            if path.is_file() and path.suffix in (".md", ".txt") and "rubix" in path.name.lower():
                rp = str(path.resolve())
                if rp in seen:
                    continue
                seen.add(rp)
                try:
                    out.append({"path": rp, "content": path.read_text(encoding="utf-8", errors="ignore")})
                except OSError:
                    continue
    return out


def build_events(projects_dirs):
    events_by_parent = {}
    for projects_dir in projects_dirs:
        for meta_path in sorted(projects_dir.glob("**/subagents/*.meta.json")):
            try:
                meta = json.loads(meta_path.read_text(encoding="utf-8", errors="ignore"))
            except (OSError, json.JSONDecodeError):
                continue
            if "rubix" not in (meta.get("description") or "").lower():
                continue

            agent_jsonl = meta_path.parent / f"{meta_path.name[:-len('.meta.json')]}.jsonl"
            records = load_jsonl(agent_jsonl)
            texts = assistant_texts(records)
            raw_text = texts[-1][2] if texts else ""

            session_dir = meta_path.parent.parent  # .../<session-id>
            project_dir = session_dir.parent
            parent_session_path = project_dir / f"{session_dir.name}.jsonl"

            lens = {
                "agent_file": str(agent_jsonl),
                "description": meta.get("description"),
                "model": meta.get("model"),
                "agent_type": meta.get("agentType"),
                "timestamp_first": records[0].get("timestamp") if records else None,
                "timestamp_last": records[-1].get("timestamp") if records else None,
                "raw_text": raw_text,
                "findings": parse_findings(raw_text) if raw_text else [],
            }

            key = str(parent_session_path)
            event = events_by_parent.setdefault(
                key,
                {
                    "parent_session_path": key,
                    "project_dir_slug": project_dir.name,
                    "session_id": session_dir.name,
                    "lenses": [],
                },
            )
            event["lenses"].append(lens)
    return events_by_parent


def enrich_event(event, since_dt):
    parent_path = Path(event["parent_session_path"])
    parent_records = load_jsonl(parent_path) if parent_path.exists() else []

    lens_times = [parse_ts(l["timestamp_first"]) for l in event["lenses"] if l["timestamp_first"]]
    anchor_ts = min(lens_times) if lens_times else None
    if anchor_ts is None and parent_path.exists():
        anchor_ts = datetime.fromtimestamp(parent_path.stat().st_mtime, tz=timezone.utc)
    if anchor_ts and anchor_ts < since_dt:
        return None

    cwd = next((rec.get("cwd") for rec in parent_records if rec.get("cwd")), None)
    invocation = {"skill": None, "args": None, "timestamp": None}
    hit = find_skill_invocation(parent_records, "rubix-review")
    if hit:
        invocation = {"skill": "rubix-review", "args": hit[2], "timestamp": hit[1]}

    dispatches = find_rubix_dispatches(parent_records)
    narrative = []
    if dispatches:
        if invocation["args"] is None:
            invocation["artifact_hint"] = dispatches[0][2].get("prompt", "")[:300]
        narrative = narrative_after(parent_records, max(d[0] for d in dispatches))

    event["cwd"] = cwd
    event["invocation"] = invocation
    event["narrative_after"] = narrative
    event["timestamp"] = anchor_ts.isoformat() if anchor_ts else None
    return event


def build_summary(events):
    findings = [f for e in events for l in e["lenses"] for f in l["findings"]]
    return {
        "total_events": len(events),
        "total_lens_dispatches": sum(len(e["lenses"]) for e in events),
        "total_findings_parsed": len(findings),
        "severity_counts": dict(collections.Counter(normalize_severity(f["severity"]) for f in findings)),
        "events_by_project": dict(collections.Counter(e["project_dir_slug"] for e in events)),
    }


def _selftest():
    sample = (
        "Findings below.\n\n"
        "**1. The highest-uncertainty premise is verified last**\n"
        "- Severity: major\n"
        "- Rationale: risk practice says probe it first.\n"
        "- Concrete suggested change: add a seam 0.\n\n"
        "### 2. Fail-closed message is a dead end\n"
        "- **Severity:** high\n"
        "- **Rationale:** no recovery command exists.\n"
        "- **Suggested change:** name the exact command.\n"
    )
    found = parse_findings(sample)
    assert len(found) == 2, found
    assert found[0]["title"] == "The highest-uncertainty premise is verified last", found[0]
    assert normalize_severity(found[0]["severity"]) == "high", found[0]  # "major" buckets to high
    assert found[1]["severity"].lower() == "high", found[1]
    assert found[1]["rationale"] == "no recovery command exists."
    assert found[1]["suggested_change"] == "name the exact command."
    print("selftest OK")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--claude-dir", default=str(DEFAULT_CLAUDE_DIR), help="used only to derive the default --projects-dir")
    ap.add_argument(
        "--projects-dir",
        action="append",
        default=None,
        help="a Claude `projects` directory to scan for rubix subagent transcripts and memory files; "
        "repeatable to combine hosts in one run (default: <claude-dir>/projects)",
    )
    ap.add_argument(
        "--repo-root",
        action="append",
        dest="repo_roots",
        default=None,
        help="extra directory to scan for *rubix*.md supplementary docs; repeatable; "
        "always includes cwd and every event's cwd regardless",
    )
    ap.add_argument("--since", default=DEFAULT_SINCE, help="ISO date floor (default: %(default)s)")
    ap.add_argument("--out", default=str(DEFAULT_OUT), help="default lives outside any git repo, hostname-stamped")
    ap.add_argument("--selftest", action="store_true", help="run the built-in parser check and exit")
    args = ap.parse_args()

    if args.selftest:
        _selftest()
        return

    claude_dir = Path(args.claude_dir).expanduser()
    since_dt = datetime.fromisoformat(args.since).replace(tzinfo=timezone.utc)
    projects_dirs = (
        [Path(p).expanduser() for p in args.projects_dir] if args.projects_dir else [claude_dir / "projects"]
    )

    events_by_parent = build_events(projects_dirs)
    events = [e for e in (enrich_event(ev, since_dt) for ev in events_by_parent.values()) if e]
    events.sort(key=lambda e: e["timestamp"] or "")

    extra_roots = {Path(p).expanduser() for p in (args.repo_roots or [])}
    roots = {Path.cwd()} | extra_roots | {Path(e["cwd"]) for e in events if e.get("cwd")}
    corpus = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "since": args.since,
        "projects_dirs": [str(p) for p in projects_dirs],
        "events": events,
        "memory_evidence": scan_memory_evidence(projects_dirs),
        "supplementary_docs": scan_supplementary_docs(roots),
        "summary": build_summary(events),
    }

    out_path = Path(args.out).expanduser()
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(corpus, indent=2), encoding="utf-8")

    print(f"wrote {out_path} ({out_path.stat().st_size:,} bytes)")
    print(json.dumps(corpus["summary"], indent=2))


if __name__ == "__main__":
    sys.exit(main())
