"""Existing runs keep their original helper when a local update supplies a pin."""

import importlib.util
import json
from pathlib import Path

import pytest

spec = importlib.util.spec_from_file_location(
    "amr_compat", Path(__file__).parents[1] / "skill/scripts/amr_compat.py"
)
assert spec and spec.loader
compat = importlib.util.module_from_spec(spec)
spec.loader.exec_module(compat)


def test_new_run_does_not_use_legacy_runtime(tmp_path):
    run = tmp_path / "run"
    run.mkdir()
    (run / "state.json").write_text(json.dumps({"feedback_policy": 2}))
    assert compat.legacy_run(["--run", str(run), "status"]) is None
    assert compat.legacy_run(["init", str(tmp_path / "paper.md")]) is None


def test_legacy_explicit_and_resume_run_are_found(tmp_path):
    source = tmp_path / "paper.md"
    source.write_text("original")
    run = tmp_path / "paper.review" / "one"
    run.mkdir(parents=True)
    (run / "state.json").write_text(json.dumps({"source": str(source), "status": None}))
    assert compat.legacy_run(["--run", str(run), "status"]) == run
    assert compat.legacy_run(["init", "--resume", str(source)]) == run


def test_ambiguous_resume_does_not_choose_a_run(tmp_path):
    source = tmp_path / "paper.md"
    source.write_text("original")
    for name in ["one", "two"]:
        run = tmp_path / "paper.review" / name
        run.mkdir(parents=True)
        (run / "state.json").write_text(
            json.dumps({"source": str(source), "status": None})
        )
    assert compat.legacy_run(["init", str(source), "--resume"]) is None


def test_legacy_exec_uses_literal_argv_and_verified_helper(tmp_path, monkeypatch):
    run = tmp_path / "literal $(not-a-command)"
    run.mkdir()
    (run / "state.json").write_text("{}")
    helper = tmp_path / "old.py"
    helper.write_text("original helper")
    pin = tmp_path / "legacy-runtime.json"
    pin.write_text(
        json.dumps(
            {
                "runtime": str(helper),
                "sha256": compat.file_hash(helper),
                "workflow": "original instructions",
            }
        )
    )
    monkeypatch.setattr(compat, "PIN_PATH", pin)
    captured = []
    monkeypatch.setattr(
        compat.os, "execv", lambda exe, args: captured.append((exe, args))
    )
    args = ["--run", str(run), "status"]
    compat.route_legacy(args)
    assert captured[0][1][1:] == [str(helper), *args]
    helper.write_text("changed helper")
    with pytest.raises(ValueError, match="changed"):
        compat.route_legacy(args)


def test_no_pin_has_no_routing_side_effect(tmp_path, monkeypatch):
    monkeypatch.setattr(compat, "PIN_PATH", tmp_path / "absent.json")
    compat.route_legacy(["--help"])


def test_pending_explains_legacy_workflow_without_exec(tmp_path, monkeypatch, capsys):
    run = tmp_path / "run"
    run.mkdir()
    (run / "state.json").write_text("{}")
    helper = tmp_path / "old.py"
    helper.write_text("original helper")
    pin = tmp_path / "legacy-runtime.json"
    pin.write_text(
        json.dumps(
            {
                "runtime": str(helper),
                "sha256": compat.file_hash(helper),
                "workflow": "original instructions",
            }
        )
    )
    monkeypatch.setattr(compat, "PIN_PATH", pin)
    with pytest.raises(SystemExit) as result:
        compat.route_legacy(["--run", str(run), "pending"])
    assert result.value.code == 0
    assert json.loads(capsys.readouterr().out)["legacy_run"] is True


def test_legacy_run_without_pin_fails_before_mutation(tmp_path, monkeypatch):
    run = tmp_path / "run"
    run.mkdir()
    state = run / "state.json"
    state.write_text("{}")
    monkeypatch.setattr(compat, "PIN_PATH", tmp_path / "absent.json")
    with pytest.raises(ValueError, match="original runtime"):
        compat.route_legacy(["--run", str(run), "status"])
    assert state.read_text() == "{}"
