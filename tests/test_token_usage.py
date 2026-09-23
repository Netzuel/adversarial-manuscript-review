"""Accounting must not inflate repeated events or hide missing sessions."""

import importlib.util
import json
from pathlib import Path
from typing import Any

import pytest

MODULE = Path(__file__).resolve().parents[1] / "scripts/token_usage.py"


def load_module():
    assert MODULE.exists(), "usage exporter is not implemented"
    spec = importlib.util.spec_from_file_location("token_usage", MODULE)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def usage(i=100, c=60, o=10, r=3):
    return dict(
        input_tokens=i,
        cached_input_tokens=c,
        cache_write_input_tokens=0,
        output_tokens=o,
        reasoning_output_tokens=r,
        total_tokens=i + o,
    )


def write_log(path, *, duplicate=False, total=None, records=True):
    events: list[dict[str, Any]] = [
        dict(
            type="session_meta",
            payload=dict(id="private-thread", source="exec", cli_version="0.155.1"),
        ),
        dict(type="turn_context", payload=dict(model="gpt-6-astra")),
    ]
    record = dict(
        type="token_usage_record",
        timestamp="2026-09-21T00:00:01Z",
        payload=dict(
            thread_id="private-thread", response_id="private-response", usage=usage()
        ),
    )
    if records:
        events.append(record)
        if duplicate:
            events.append(record)
    events.append(
        dict(
            type="event_msg",
            payload=dict(
                type="token_count", info=dict(total_token_usage=total or usage())
            ),
        )
    )
    events.append(dict(type="response_item", payload=dict(text="SECRET MANUSCRIPT")))
    path.write_text("\n".join(json.dumps(e) for e in events))


def test_deduplicates_and_exports_only_usage(tmp_path):
    module = load_module()
    path = tmp_path / "private.jsonl"
    write_log(path, duplicate=True)
    parsed = module.read_session(path)
    assert len(parsed["calls"]) == 1
    assert parsed["totals"] == usage()
    data = module.export_sessions([dict(path=str(path), role="editor", phase="all")])
    encoded = json.dumps(data)
    for secret in (
        "private-thread",
        "private-response",
        "SECRET MANUSCRIPT",
        str(path),
    ):
        assert secret not in encoded
    assert data["totals"]["total_tokens"] == 110
    assert data["sessions"][0]["calls"][0]["elapsed_seconds"] == 0


def test_rejects_incomplete_usage(tmp_path):
    module = load_module()
    path = tmp_path / "a.jsonl"
    write_log(path, total=usage(i=200))
    with pytest.raises(ValueError, match="reconcile"):
        module.read_session(path)
    write_log(path, records=False)
    with pytest.raises(ValueError, match="per-response"):
        module.read_session(path)


def test_rejects_invalid_subsets_and_double_selected_session(tmp_path):
    module = load_module()
    with pytest.raises(ValueError):
        module.validate_usage(usage(c=101))
    with pytest.raises(ValueError):
        module.validate_usage(usage(r=11))
    path = tmp_path / "a.jsonl"
    write_log(path)
    with pytest.raises(ValueError, match="duplicate session"):
        module.export_sessions([dict(path=str(path), role="editor", phase="all")] * 2)


def test_rejects_conflicting_response_and_foreign_thread(tmp_path):
    module = load_module()
    path = tmp_path / "a.jsonl"
    write_log(path, duplicate=True)
    events = [json.loads(line) for line in path.read_text().splitlines()]
    events[3]["payload"]["usage"] = usage(i=101)
    path.write_text("\n".join(json.dumps(e) for e in events))
    with pytest.raises(ValueError, match="conflicting"):
        module.read_session(path)
    events[3]["payload"] = dict(events[2]["payload"], thread_id="another-thread")
    path.write_text("\n".join(json.dumps(e) for e in events))
    with pytest.raises(ValueError, match="thread"):
        module.read_session(path)


def test_child_linkage_and_cross_session_response_identity(tmp_path):
    module = load_module()
    root = tmp_path / "root.jsonl"
    child = tmp_path / "child.jsonl"
    write_log(root)
    write_log(child)
    events = [json.loads(line) for line in child.read_text().splitlines()]
    events[0]["payload"]["id"] = "child"
    events[0]["payload"]["source"] = {
        "subagent": {
            "thread_spawn": {
                "parent_thread_id": "private-thread",
                "agent_role": "amr-review-math",
            }
        }
    }
    events[2]["payload"]["thread_id"] = "child"
    child.write_text("\n".join(json.dumps(e) for e in events))
    manifest = [
        dict(path=str(root), role="editor", phase="all"),
        dict(path=str(child), role="math", phase="initial"),
    ]
    with pytest.raises(ValueError, match="response.*sessions"):
        module.export_sessions(manifest)
    events[2]["payload"]["response_id"] = "different-response"
    child.write_text("\n".join(json.dumps(e) for e in events))
    assert module.export_sessions(manifest)["totals"]["total_tokens"] == 220
    events[0]["payload"]["source"]["subagent"]["thread_spawn"]["parent_thread_id"] = (
        "foreign"
    )
    child.write_text("\n".join(json.dumps(e) for e in events))
    with pytest.raises(ValueError, match="linkage"):
        module.export_sessions(manifest)


def test_public_dataset_reconciles_and_contains_all_study_sessions():
    module = load_module()
    root = MODULE.parents[1] / "docs/data/token-usage"
    observed = json.loads((root / "observed.json").read_text())
    summary = json.loads((root / "summary.json").read_text())
    sessions = observed["sessions"]
    assert len(sessions) == 11
    assert sum(len(s["calls"]) for s in sessions) == 87
    for session in sessions:
        assert module.sum_usage(session["calls"]) == session["totals"]
    assert module.sum_usage([s["totals"] for s in sessions]) == observed["totals"]
    assert summary["totals"] == observed["totals"]
    assert observed["totals"]["total_tokens"] == 4555808
    baseline = [
        s
        for s in summary["sensitivity_scenarios"]
        if s["rounds"] == 2 and s["added_manuscript_tokens"] == 0
    ]
    assert all(s["total_tokens"] == 4555808 for s in baseline)
