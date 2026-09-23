"""Export reconciled Codex per-response usage from an explicit private manifest.

No transcript text, local paths, native IDs, or account fields enter the export.
This supports the observed Codex 0.155.1 JSONL schema, not arbitrary host logs.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
from datetime import datetime
from pathlib import Path
from typing import Any

FIELDS = (
    "input_tokens",
    "cached_input_tokens",
    "cache_write_input_tokens",
    "output_tokens",
    "reasoning_output_tokens",
    "total_tokens",
)
ROLES = {"editor", "math", "methods", "evidence", "communication", "student", "auditor"}
PHASES = {"all", "initial", "revision", "verification", "audit"}
NATIVE_ROLES = {
    "math": "amr-review-math",
    "methods": "amr-review-methods",
    "evidence": "amr-review-evidence",
    "communication": "amr-review-communication",
    "student": "amr-student",
    "auditor": "amr-final-auditor",
}


def validate_usage(value: dict[str, Any]) -> dict[str, int]:
    """Require a complete disjoint accounting, with reasoning inside output."""
    if any(type(value.get(k)) is not int or value[k] < 0 for k in FIELDS):
        raise ValueError("missing, negative, or noninteger usage field")
    u = {k: value[k] for k in FIELDS}
    if u["cached_input_tokens"] + u["cache_write_input_tokens"] > u["input_tokens"]:
        raise ValueError("cache subsets exceed input")
    if u["reasoning_output_tokens"] > u["output_tokens"]:
        raise ValueError("reasoning exceeds output")
    if u["total_tokens"] != u["input_tokens"] + u["output_tokens"]:
        raise ValueError("total is not input plus output")
    return u


def sum_usage(values: list[dict[str, Any]]) -> dict[str, int]:
    return {k: sum(v[k] for v in values) for k in FIELDS}


def read_session(path: Path) -> dict[str, Any]:
    """Read one whole session; fail if response sums and final counters disagree."""
    raw = path.read_bytes()
    metadata: dict[str, Any] = {}
    calls: list[dict[str, Any]] = []
    seen: dict[str, dict[str, int]] = {}
    final: dict[str, int] | None = None
    model = None
    for line in raw.splitlines():
        event = json.loads(line)
        payload = event.get("payload", {})
        if event["type"] == "session_meta":
            if metadata:
                raise ValueError("multiple session metadata records")
            metadata = payload
        elif event["type"] == "turn_context":
            model = payload.get("model")
        elif event["type"] == "token_usage_record":
            if payload.get("thread_id") != metadata.get("id"):
                raise ValueError("usage belongs to another thread")
            rid = payload.get("response_id")
            if not isinstance(rid, str) or not rid:
                raise ValueError("missing response identity")
            usage = validate_usage(payload["usage"])
            if rid in seen:
                if seen[rid] != usage:
                    raise ValueError("conflicting repeated response")
                continue
            if not isinstance(model, str) or not re.fullmatch(
                r"[a-zA-Z0-9._-]+", model
            ):
                raise ValueError("missing or unsupported model label")
            seen[rid] = usage
            timestamp = datetime.fromisoformat(
                event["timestamp"].replace("Z", "+00:00")
            )
            if timestamp.tzinfo is None:
                raise ValueError("timestamp must have a timezone")
            calls.append(dict(timestamp=timestamp.timestamp(), model=model, **usage))
        elif event["type"] == "event_msg" and payload.get("type") == "token_count":
            if payload.get("info"):
                final = validate_usage(payload["info"]["total_token_usage"])
    if not calls:
        raise ValueError("no per-response usage records; no fabricated zero")
    totals = sum_usage(calls)
    if final is None or totals != final:
        raise ValueError("response usage does not reconcile with final session counter")
    version = metadata.get("cli_version", "")
    if not re.fullmatch(r"[0-9]+\.[0-9]+\.[0-9]+(?:[-.][a-zA-Z0-9.]+)?", version):
        raise ValueError("missing or unsupported client version")
    source = metadata.get("source", {})
    spawn = (
        source.get("subagent", {}).get("thread_spawn", {})
        if isinstance(source, dict)
        else {}
    )
    return dict(
        id=metadata["id"],
        parent=spawn.get("parent_thread_id"),
        native_role=metadata.get("agent_role") or spawn.get("agent_role"),
        source_sha256=hashlib.sha256(raw).hexdigest(),
        client_version=version,
        response_ids=set(seen),
        calls=calls,
        totals=totals,
    )


def export_sessions(manifest: list[dict[str, str]]) -> dict[str, Any]:
    """Export an allowlisted dataset; selection completeness is a caller audit."""
    sessions = []
    ids = set()
    response_ids = set()
    for entry in manifest:
        if entry["role"] not in ROLES or entry["phase"] not in PHASES:
            raise ValueError("unsupported role or phase")
        session = read_session(Path(entry["path"]))
        if session["id"] in ids:
            raise ValueError("duplicate session selection")
        ids.add(session["id"])
        if response_ids.intersection(session["response_ids"]):
            raise ValueError("response identity occurs in multiple sessions")
        response_ids.update(session["response_ids"])
        sessions.append(dict(session, role=entry["role"], phase=entry["phase"]))
    roots = [s for s in sessions if s["role"] == "editor"]
    if len(roots) != 1 or roots[0]["parent"] is not None:
        raise ValueError("select exactly one root editor session")
    root = roots[0]
    for session in sessions:
        if session is not root and (
            session["parent"] != root["id"]
            or session["native_role"] != NATIVE_ROLES[session["role"]]
        ):
            raise ValueError("child parent linkage or native role mismatch")
    start = min(c["timestamp"] for s in sessions for c in s["calls"])
    public = []
    for index, session in enumerate(sessions):
        calls = [
            dict(
                elapsed_seconds=round(c["timestamp"] - start, 3),
                model=c["model"],
                **{k: c[k] for k in FIELDS},
            )
            for c in session["calls"]
        ]
        public.append(
            dict(
                session=index + 1,
                role=session["role"],
                phase=session["phase"],
                source_sha256=session["source_sha256"],
                client_version=session["client_version"],
                calls=calls,
                totals=session["totals"],
            )
        )
    return dict(
        schema_version=1,
        evidence="observed_codex_usage",
        sessions=public,
        totals=sum_usage([s["totals"] for s in public]),
    )


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "manifest", type=Path, help="private JSON list of path/role/phase"
    )
    parser.add_argument(
        "output", type=Path, help="sanitized JSON output; inspect before sharing"
    )
    args = parser.parse_args()
    exported = export_sessions(json.loads(args.manifest.read_text()))
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(exported, indent=2) + "\n")
    print(json.dumps(exported["totals"], indent=2))


if __name__ == "__main__":
    main()
