from pathlib import Path

import pytest

from test_state import issue, setup_run


def test_minor_and_unreported_findings_block(tmp_path):
    a, info = setup_run(tmp_path)
    with a.Run(Path(info["run"]), info["session"]) as r:
        record = issue(r.state["snapshot"])
        record["severity"] = "minor"
        r.issues([record])
        assert any("unresolved" in e and "I1" in e for e in r.acceptance_errors())
        d = r.dispatch("R1", "review")
        r.complete(
            d,
            {
                "snapshot_hash": r.state["snapshot"],
                "verdict": "revise",
                "findings": [{"id": "I2", "problem": "omitted detail"}],
            },
        )
        with pytest.raises(a.ReviewError, match="I2"):
            r.transition("EDITORIAL_TRIAGE")


def test_student_partial_response_retains_reservation(tmp_path):
    a, info = setup_run(tmp_path)
    with a.Run(Path(info["run"]), info["session"]) as r:
        r.issues([issue(r.state["snapshot"])])
        r.transition("EDITORIAL_TRIAGE")
        r.transition("STUDENT_REVISION")
        d = r.dispatch("student", "student")
        with pytest.raises(a.ReviewError, match="response"):
            r.complete(d, {"snapshot_hash": r.state["snapshot"], "responses": []})
        assert d in r.state["active"]


@pytest.mark.parametrize(
    "status",
    [
        "REVISION_REQUIRED",
        "STOPPED_BUDGET",
        "STOPPED_NO_PROGRESS",
        "BLOCKED_PERMISSION",
        "BLOCKED_CAPABILITY",
        "BLOCKED_INPUT",
        "ERROR",
    ],
)
def test_premature_stop_rejected(tmp_path, status):
    a, info = setup_run(tmp_path)
    with a.Run(Path(info["run"]), info["session"]) as r:
        with pytest.raises(a.ReviewError):
            r.finalize(status)


def test_legitimate_blocker_waits_for_independent_correction(tmp_path):
    a, info = setup_run(tmp_path)
    with a.Run(Path(info["run"]), info["session"]) as r:
        first = issue(r.state["snapshot"])
        second = dict(first, id="I2", severity="minor")
        r.issues([first, second])
        (r.path / "evidence/block.txt").write_text(
            "Inspected supplied data; measurement unavailable."
        )
        proof = {
            "status": "BLOCKED_EVIDENCE",
            "reason": "measurement unavailable",
            "inspected": True,
            "artifacts": ["evidence/block.txt"],
            "blocked_issue_ids": ["I1"],
        }
        r.close(
            "I1",
            {
                "author": "editor",
                "status": "blocked",
                "reason": proof["reason"],
                "inspected": True,
                "artifacts": proof["artifacts"],
                "snapshot_hash": r.state["snapshot"],
            },
        )
        r.stop_proof(proof)
        with pytest.raises(a.ReviewError, match="actionable"):
            r.finalize("BLOCKED_EVIDENCE")
        r.close(
            "I2",
            {
                "author": "editor",
                "status": "rebutted_verified",
                "reason": "definition supplies requested detail",
                "inspected": True,
                "artifacts": proof["artifacts"],
                "snapshot_hash": r.state["snapshot"],
            },
        )
        assert r.finalize("BLOCKED_EVIDENCE")["status"] == "BLOCKED_EVIDENCE"


def test_reports_require_findings_and_retain_old_ids(tmp_path):
    a, info = setup_run(tmp_path)
    with a.Run(Path(info["run"]), info["session"]) as r:
        d = r.dispatch("R1", "first")
        report = {"snapshot_hash": r.state["snapshot"], "verdict": "revise"}
        with pytest.raises(a.ReviewError, match="findings"):
            r.complete(d, report)
        r.complete(
            d, dict(report, findings=[{"id": "omitted", "problem": "missing term"}])
        )
        d = r.dispatch("R1", "second")
        r.complete(d, dict(report, verdict="pass", findings=[]))
        assert r.pending()["missing_finding_ids"] == ["omitted"]


def test_minor_limitation_and_editor_only_fix_cannot_pass(tmp_path):
    a, info = setup_run(tmp_path)
    with a.Run(Path(info["run"]), info["session"]) as r:
        record = dict(issue(r.state["snapshot"]), severity="minor")
        r.issues([record])
        evidence = r.path / "evidence/inspection.txt"
        evidence.write_text("Inspected actual changed value.")
        close = {
            "author": "editor",
            "status": "accepted_minor_limitation",
            "reason": "small issue",
            "inspected": True,
            "artifacts": ["evidence/inspection.txt"],
            "snapshot_hash": r.state["snapshot"],
        }
        r.close("I1", close)
        assert any("unresolved issue I1" in e for e in r.acceptance_errors())
        candidate = r.path / "candidate/paper é.md"
        candidate.write_text(candidate.read_text().replace("Value: 3", "Value: 4"))
        r.snapshot()
        with pytest.raises(a.ReviewError, match="student"):
            r.close(
                "I1",
                dict(
                    close,
                    status="resolved_verified",
                    snapshot_hash=r.state["snapshot"],
                    related_changes=["paper é.md"],
                ),
            )


def passing_reviews(r, tmp_path, prefix):
    (r.path / "evidence/checked.txt").write_text(
        "Supplied definition checked against current candidate."
    )
    r.maps(
        {
            "coverage": {
                role: {
                    "snapshot_hash": r.state["snapshot"],
                    "locations": ["whole paper"],
                }
                for role in ("R1", "R2", "R3", "R4")
            },
            "claims": {
                "C1": {
                    "snapshot_hash": r.state["snapshot"],
                    "status": "supported",
                    "artifacts": ["evidence/checked.txt"],
                }
            },
        }
    )
    for role in ("R1", "R2", "R3", "R4"):
        complete_review(r, tmp_path, role, prefix + role)


def complete_review(r, tmp_path, role, context, findings=None):
    task = r.dispatch(role, context)
    transcript = tmp_path / (context + ".txt")
    transcript.write_text("Synthetic test native receipt " + context)
    r.complete(
        task,
        {
            "snapshot_hash": r.state["snapshot"],
            "verdict": "revise" if findings else "pass",
            "findings": findings or [],
            "coverage": ["whole paper"],
            "independent": True,
            "negotiation_exposed": False,
            "context_record": {
                "host": "codex",
                "context_id": context,
                "separate_context": True,
                "negotiation_exposed": False,
                "mechanism": "spawn_agent",
                "transcript_source": str(transcript),
            },
        },
    )


def student_fix(r, text, issue_id, context, author="R1"):
    task = r.dispatch("student", context)
    (r.path / "candidate/paper é.md").write_text(text)
    r.complete(
        task,
        {
            "snapshot_hash": r.state["snapshot"],
            "responses": [
                {
                    "id": issue_id,
                    "response": "Corrected requested value.",
                    "changed_files": ["paper é.md"],
                    "evidence": [],
                }
            ],
        },
    )
    r.transition("VALIDATION")
    r.snapshot()
    r.transition("RE_REVIEW")
    (r.path / "evidence/fix.txt").write_text(text)
    r.close(
        issue_id,
        {
            "author": author,
            "status": "resolved_verified",
            "reason": "Inspected changed source.",
            "snapshot_hash": r.state["snapshot"],
            "inspected": True,
            "related_changes": ["paper é.md"],
            "artifacts": ["evidence/fix.txt"],
        },
    )


def test_two_minor_revision_cycles_then_audit_finding(tmp_path):
    a, info = setup_run(tmp_path)
    original = (tmp_path / "paper é.md").read_bytes()
    with a.Run(Path(info["run"]), info["session"]) as r:
        passing_reviews(r, tmp_path, "initial")
        first = dict(issue(r.state["snapshot"]), severity="minor")
        r.issues([first])
        r.transition("EDITORIAL_TRIAGE")
        r.transition("STUDENT_REVISION")
        student_fix(r, "Value: 4. Correct section.\n", "I1", "student1")
        passing_reviews(r, tmp_path, "review1")
        second = dict(
            issue(r.state["snapshot"]),
            id="I2",
            severity="suggestion",
            problem="Clarify the exact value.",
        )
        r.issues([second])
        r.transition("STUDENT_REVISION")
        student_fix(r, "Value: 4 exactly. Correct section.\n", "I2", "student2")
        # The older fix remains attributable after another student modifies the same file.
        r.close(
            "I1",
            {
                "author": "R1",
                "status": "resolved_verified",
                "reason": "The corrected value remains 4.",
                "snapshot_hash": r.state["snapshot"],
                "inspected": True,
                "related_changes": ["paper é.md"],
                "artifacts": ["evidence/fix.txt"],
            },
        )
        passing_reviews(r, tmp_path, "review2")
        assert not r.acceptance_errors(preaudit=True)
        r.transition("FRESH_AUDIT")
        complete_review(
            r,
            tmp_path,
            "auditor",
            "audit",
            [{"id": "A1", "problem": "Missing definition."}],
        )
        with pytest.raises(a.ReviewError, match="A1"):
            r.transition("FINALIZE")
        with pytest.raises(a.ReviewError, match="A1"):
            r.finalize("PASS_INTERNAL")
        assert r.pending()["missing_finding_ids"] == ["A1"]
        r.issues(
            [
                dict(
                    issue(r.state["snapshot"]),
                    id="A1",
                    originating_reviewer="auditor",
                    severity="minor",
                    problem="Missing definition.",
                    resolution_condition="Define the stated quantity.",
                )
            ]
        )
        r.transition("STUDENT_REVISION")
        final_text = "Value: 4 exactly. Value denotes the count. Correct section.\n"
        student_fix(r, final_text, "A1", "student3", author="auditor")
        for issue_id in ("I1", "I2"):
            r.close(
                issue_id,
                {
                    "author": "R1",
                    "status": "resolved_verified",
                    "reason": "The exact corrected value remains 4 after the definition was added.",
                    "snapshot_hash": r.state["snapshot"],
                    "inspected": True,
                    "related_changes": ["paper é.md"],
                    "artifacts": ["evidence/fix.txt"],
                },
            )
        passing_reviews(r, tmp_path, "review3")
        r.transition("FRESH_AUDIT")
        complete_review(r, tmp_path, "auditor", "final-audit")
        assert not r.pending()["unresolved_ids"]
        assert not r.acceptance_errors()
        assert r.state["round"] == 4
        assert r.state["budget"]["audit_attempts"] == 2
        assert r.finalize("PASS_INTERNAL")["status"] == "PASS_INTERNAL"
        assert (
            r.path / "deliverables/revised-project/paper é.md"
        ).read_text() == final_text
        responses = (r.path / "deliverables/RESPONSE_TO_REVIEWERS.md").read_text()
        assert all(issue_id + ":" in responses for issue_id in ("I1", "I2", "A1"))
        assert (tmp_path / "paper é.md").read_bytes() == original


def test_repeated_closed_finding_requires_new_disposition(tmp_path):
    a, info = setup_run(tmp_path)
    with a.Run(Path(info["run"]), info["session"]) as r:
        passing_reviews(r, tmp_path, "initial")
        r.issues([issue(r.state["snapshot"])])
        closure = {
            "author": "editor",
            "status": "rebutted_verified",
            "reason": "Definition establishes 3.",
            "snapshot_hash": r.state["snapshot"],
            "inspected": True,
            "artifacts": ["evidence/checked.txt"],
        }
        r.close("I1", closure)
        r.transition("EDITORIAL_TRIAGE")
        r.transition("FRESH_AUDIT")
        complete_review(
            r,
            tmp_path,
            "auditor",
            "first-audit",
            [{"id": "I1", "problem": "The issue recurs."}],
        )
        complete_review(r, tmp_path, "auditor", "second-audit")
        assert "I1" in r.pending()["unresolved_ids"]
        with pytest.raises(a.ReviewError, match="I1"):
            r.finalize("PASS_INTERNAL")
        r.close(
            "I1",
            dict(
                closure,
                reason="Inspected the repeated allegation against the same supplied definition.",
            ),
        )
        assert not r.acceptance_errors()
        assert r.finalize("PASS_INTERNAL")["status"] == "PASS_INTERNAL"
