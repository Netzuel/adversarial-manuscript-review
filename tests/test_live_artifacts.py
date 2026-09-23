"""Deterministic checker tests only: synthetic records are not live model evidence."""

import hashlib
import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from verify_live import inspect_run


def put(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value))


@pytest.fixture
def synthetic(tmp_path):
    original = tmp_path / "source.md"
    original.write_text(
        "For y(t)=exp(-2t), y'(t)=+2 exp(-2t).\nThe table gives y(1)=0.5.\nControl: y(0)=1.\n"
    )
    run = tmp_path / "run"
    put(
        run / "input-manifest.json",
        {
            "source_root": str(tmp_path),
            "entrypoint": original.name,
            "files": {original.name: hashlib.sha256(original.read_bytes()).hexdigest()},
        },
    )
    put(
        run / "state.json",
        {"status": "PASS_INTERNAL", "completed": {}, "snapshot": "final"},
    )
    (run / "events.jsonl").write_text("")
    delivery = run / "deliverables/revised-project/source.md"
    delivery.parent.mkdir(parents=True)
    delivery.write_text(
        "For y(t)=exp(-2t), y'(t)=-2 exp(-2t).\nThe table gives y(1)=0.135335.\nControl: y(0)=1.\n"
    )
    return run, original, delivery


def test_status_alone_does_not_prove_live_run(synthetic):
    run, original, _ = synthetic
    result = inspect_run(run, original)
    assert result["gates"]["original_preserved"]
    assert result["gates"]["corrected_derivative"]
    assert result["gates"]["corrected_table_prose"]
    assert result["gates"]["control_preserved"]
    assert not result["all_observed_gates"]
    assert result["reported_status"] == "PASS_INTERNAL"
    assert result["classification"] != "PASS_INTERNAL"


def test_changed_original_rejected(synthetic):
    run, original, _ = synthetic
    original.write_text("concurrent change")
    assert not inspect_run(run, original)["gates"]["original_preserved"]


def test_false_fix_and_reference_decoy_rejected(synthetic):
    run, original, delivery = synthetic
    delivery.write_text(original.read_text() + "\nReference: -2 exp(-2t), 0.135335.\n")
    result = inspect_run(run, original)
    assert not result["gates"]["corrected_derivative"]
    assert not result["gates"]["corrected_table_prose"]


def test_missing_delivery_rejected(synthetic):
    run, original, delivery = synthetic
    delivery.unlink()
    assert not inspect_run(run, original)["gates"]["delivered_editable_exists"]


def test_control_regression_rejected(synthetic):
    run, original, delivery = synthetic
    delivery.write_text(delivery.read_text().replace("y(0)=1", "y(0)=2"))
    assert not inspect_run(run, original)["gates"]["control_preserved"]


def test_latex_equivalents(synthetic):
    run, original, delivery = synthetic
    delivery.write_text(
        r"For $y(t)=\exp(-2t)$, $y'(t)=-2\exp(-2t)$."
        + "\n"
        + r"The table gives $y(1)\approx0.135335$."
        + "\nControl: $y(0)=1$.\n"
    )
    result = inspect_run(run, original)
    assert result["gates"]["corrected_derivative"]
    assert result["gates"]["corrected_table_prose"]
    assert result["gates"]["control_preserved"]


def test_manifest_escape_rejected(synthetic):
    run, original, _ = synthetic
    manifest = json.loads((run / "input-manifest.json").read_text())
    manifest["files"]["../escape"] = "bad"
    put(run / "input-manifest.json", manifest)
    assert not inspect_run(run, original)["gates"]["original_preserved"]


def add_synthetic_records(run, delivery):
    """Build clearly synthetic records to test parser behavior, never live proof."""
    state = json.loads((run / "state.json").read_text())
    state["delivered_manifest"] = {
        "source.md": hashlib.sha256(delivery.read_bytes()).hexdigest()
    }
    events = []
    for index, role in enumerate(["R1", "R2", "R3", "R4", "student", "auditor"]):
        key = str(index)
        context = "deterministic-fake-context-" + key
        metadata = "evidence/context-" + key + ".txt"
        (run / metadata).parent.mkdir(exist_ok=True)
        (run / metadata).write_text(
            "DETERMINISTIC TEST ONLY native separate context " + context
        )
        report_path = "rounds/results/" + key + ".json"
        put(
            run / report_path,
            {
                "context_evidence": [metadata],
                "independent": True,
                "negotiation_exposed": False,
                "snapshot_hash": "final",
                "verdict": "pass",
            },
        )
        state["completed"][key] = {
            "role": role,
            "context_id": context,
            "result_path": report_path,
            "candidate_before": {"source.md": "old"},
            "candidate_after": {"source.md": "new"},
        }
        events.extend(
            [
                {
                    "kind": "dispatch",
                    "sequence": 2 * index + 1,
                    "data": {"reservation": key, "role": role},
                },
                {
                    "kind": "complete",
                    "sequence": 2 * index + 2,
                    "data": {"reservation": key},
                },
            ]
        )
    evidence = run / "evidence/check.txt"
    evidence.write_text("DETERMINISTIC TEST ONLY")
    put(
        run / "issues.json",
        [
            {
                "id": str(i),
                "status": "resolved_verified",
                "verification_snapshot": "final",
                "related_changes": ["source.md"],
                "history": ["open", "resolved_verified"],
                "verification_artifacts": {
                    "evidence/check.txt": hashlib.sha256(
                        evidence.read_bytes()
                    ).hexdigest()
                },
            }
            for i in range(2)
        ],
    )
    put(run / "state.json", state)
    (run / "events.jsonl").write_text("".join(json.dumps(e) + "\n" for e in events))


def test_synthetic_metadata_is_classified_as_recorded_not_live(synthetic):
    run, original, delivery = synthetic
    add_synthetic_records(run, delivery)
    result = inspect_run(run, original)
    assert result["all_observed_gates"]
    assert result["classification"] == "RECORDED_GATES_OBSERVED"
    assert "not independent proof" in result["limitations"][0]


def test_missing_context_artifact_rejected(synthetic):
    run, original, delivery = synthetic
    add_synthetic_records(run, delivery)
    (run / "evidence/context-5.txt").unlink()
    assert not inspect_run(run, original)["gates"]["native_role_metadata_recorded"]


def test_reused_context_rejected(synthetic):
    run, original, delivery = synthetic
    add_synthetic_records(run, delivery)
    state = json.loads((run / "state.json").read_text())
    state["completed"]["5"]["context_id"] = state["completed"]["0"]["context_id"]
    put(run / "state.json", state)
    assert not inspect_run(run, original)["gates"]["native_role_metadata_recorded"]


def test_stale_post_edit_review_rejected(synthetic):
    run, original, delivery = synthetic
    add_synthetic_records(run, delivery)
    path = run / "rounds/results/5.json"
    report = json.loads(path.read_text())
    report["snapshot_hash"] = "old"
    put(path, report)
    assert not inspect_run(run, original)["gates"]["subsequent_review_recorded"]


def test_absolute_source_manifest_keys_supported(synthetic):
    run, original, _ = synthetic
    path = run / "input-manifest.json"
    data = json.loads(path.read_text())
    data["files"] = {str(original): data["files"][original.name]}
    put(path, data)
    result = inspect_run(run, original)
    assert result["gates"]["original_preserved"]
    assert result["gates"]["actual_source_changed"]


def test_absolute_manifest_escape_rejected(synthetic):
    run, original, _ = synthetic
    path = run / "input-manifest.json"
    data = json.loads(path.read_text())
    data["files"]["/etc/hosts"] = "not-an-authorized-input"
    put(path, data)
    assert not inspect_run(run, original)["gates"]["original_preserved"]


def test_student_history_exposure_is_expected(synthetic):
    run, original, delivery = synthetic
    add_synthetic_records(run, delivery)
    path = run / "rounds/results/4.json"
    report = json.loads(path.read_text())
    report.pop("independent")
    report.pop("negotiation_exposed")
    report["context_record"] = {
        "context_id": "deterministic-fake-context-4",
        "separate_context": True,
        "negotiation_exposed": True,
    }
    put(path, report)
    assert inspect_run(run, original)["gates"]["native_role_metadata_recorded"]


def test_exposed_auditor_rejected(synthetic):
    run, original, delivery = synthetic
    add_synthetic_records(run, delivery)
    path = run / "rounds/results/5.json"
    report = json.loads(path.read_text())
    report["negotiation_exposed"] = True
    put(path, report)
    assert not inspect_run(run, original)["gates"]["native_role_metadata_recorded"]


def test_rereview_history_allowed_with_separate_context(synthetic):
    run, original, delivery = synthetic
    add_synthetic_records(run, delivery)
    path = run / "rounds/results/0.json"
    report = json.loads(path.read_text())
    report["negotiation_exposed"] = True
    put(path, report)
    state = json.loads((run / "state.json").read_text())
    state["completed"]["0"]["stage"] = "RE_REVIEW"
    put(run / "state.json", state)
    assert inspect_run(run, original)["gates"]["native_role_metadata_recorded"]
    state["completed"]["0"]["stage"] = "INDEPENDENT_REVIEW"
    put(run / "state.json", state)
    assert not inspect_run(run, original)["gates"]["native_role_metadata_recorded"]


def test_context_hash_tampering_rejected(synthetic):
    run, original, delivery = synthetic
    add_synthetic_records(run, delivery)
    state = json.loads((run / "state.json").read_text())
    state["completed"]["5"]["context_hashes"] = {
        "evidence/context-5.txt": "invalid-hash"
    }
    put(run / "state.json", state)
    assert not inspect_run(run, original)["gates"]["native_role_metadata_recorded"]


def test_latex_included_correction_and_all_original_files(synthetic):
    """Deterministic multi-file fixture, not a live LaTeX model run."""
    run, old_original, old_delivery = synthetic
    source_root = old_original.parent
    original = source_root / "main.tex"
    original.write_text(
        r"\documentclass{article}"
        + "\n"
        + r"\begin{document}\input{sections/result}\bibliography{references}\end{document}"
    )
    section = source_root / "sections/result.tex"
    section.parent.mkdir()
    section.write_text(
        r"For $y(t)=\exp(-2t)$, $y'(t)=+2\exp(-2t)$."
        + "\n"
        + r"The table gives $y(1)=0.5$."
        + "\n"
        + r"Control: $y(0)=1$."
        + "\n"
    )
    bibliography = source_root / "references.bib"
    bibliography.write_text("@misc{fixture, title={Supplied synthetic reference}}\n")
    files = [original, section, bibliography]
    put(
        run / "input-manifest.json",
        {
            "source_root": str(source_root),
            "entrypoint": "main.tex",
            "files": {
                str(p): hashlib.sha256(p.read_bytes()).hexdigest() for p in files
            },
        },
    )
    old_delivery.unlink()
    delivery_root = old_delivery.parent
    for path in files:
        output = delivery_root / path.relative_to(source_root)
        output.parent.mkdir(parents=True, exist_ok=True)
        content = path.read_text()
        if path == section:
            content = content.replace("+2\\exp", "-2\\exp").replace(
                "y(1)=0.5", "y(1)=0.135335"
            )
        output.write_text(content)
    result = inspect_run(run, original)
    for gate in (
        "original_preserved",
        "delivered_editable_exists",
        "corrected_derivative",
        "corrected_table_prose",
        "control_preserved",
        "actual_source_changed",
    ):
        assert result["gates"][gate], gate
    assert (delivery_root / "main.tex").read_bytes() == original.read_bytes()
    bibliography.write_text("concurrent bibliography change")
    assert not inspect_run(run, original)["gates"]["original_preserved"]


@pytest.mark.parametrize(
    "original_metadata,delivered_metadata,expected",
    [
        ("", r"\author{Invented Person}", False),
        ("", r"\author{}", True),
        ("", "", True),
        (
            r"\author{Supplied Author}\affiliation{Supplied Institute}\email{author@example.test}",
            r"\author{Supplied Author}\affiliation{Supplied Institute}\email{author@example.test}",
            True,
        ),
        (r"\author{Supplied Author}", r"\author{Other Author}", False),
        ("", r"\affiliation{Invented Institute}\email{invented@example.test}", False),
    ],
)
def test_tex_author_metadata_preserved(
    synthetic, original_metadata, delivered_metadata, expected
):
    run, old_original, old_delivery = synthetic
    original = old_original.with_suffix(".tex")
    original.write_text(original_metadata + "\n" + old_original.read_text())
    delivery = old_delivery.with_suffix(".tex")
    delivery.write_text(delivered_metadata + "\n" + old_delivery.read_text())
    old_delivery.unlink()
    put(
        run / "input-manifest.json",
        {
            "source_root": str(original.parent),
            "entrypoint": original.name,
            "files": {str(original): hashlib.sha256(original.read_bytes()).hexdigest()},
        },
    )
    assert inspect_run(run, original)["gates"]["author_metadata_preserved"] is expected


@pytest.mark.parametrize(
    "control,expected",
    [
        ("Controls: the initial value is y(0)=1.", True),
        (r"The normalisation check gives $y(0)=1$.", True),
        ("The initial value is y(0)=1.0.", True),
        ("No initial value is stated.", False),
        ("The initial value is y(0)=2.", False),
        ("The initial value is y(0)=1. Elsewhere y(0)=2.", False),
        ("Reference: y(0)=1.", False),
        ("## Supplied reference evidence\nThe reference gives y(0)=1.", False),
        ("<!-- Control: y(0)=1. -->", False),
        ("The initial value is y(0)=1/2.", False),
    ],
)
def test_numerical_control_without_fixed_label(synthetic, control, expected):
    run, original, delivery = synthetic
    delivery.write_text(delivery.read_text().replace("Control: y(0)=1.", control))
    assert inspect_run(run, original)["gates"]["control_preserved"] is expected


def test_ratio_denominator_is_not_initial_value_assignment(synthetic):
    run, original, delivery = synthetic
    delivery.write_text(
        delivery.read_text().replace(
            "Control: y(0)=1.",
            r"Normalisation: $y(0)=1$. The ratio is $y(1)/y(0)=0.135335<1$.",
        )
    )
    assert inspect_run(run, original)["gates"]["control_preserved"]
