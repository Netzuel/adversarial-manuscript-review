"""Read-only artifact checks for the synthetic decay live fixture.

This checks saved evidence, not the authenticity of model-service execution.
Deterministic fixtures must never be presented as live validation.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path
from typing import Any


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read(path: Path) -> Any:
    return json.loads(path.read_text())


def confined(root: Path, relative: str) -> Path:
    path = root / relative
    if Path(relative).is_absolute() or ".." in Path(relative).parts:
        raise ValueError("unsafe artifact path")
    if path.is_symlink() or not path.resolve().is_relative_to(root.resolve()):
        raise ValueError("artifact escapes scoped directory")
    return path


def normalized(text: str) -> str:
    text = text.replace("−", "-").replace("′", "'")
    text = re.sub(r"\\(?:left|right|,|!|;)", "", text)
    text = text.replace("\\exp", "exp").replace("\\approx", "≈")
    return re.sub(r"[\s${}]", "", text)


def numerical_control_preserved(texts: list[str]) -> bool:
    """Check this fixture's initial value in prose, not reference-only material."""
    prose = []
    for text in texts:
        text = re.sub(r"<!--.*?-->", "", text, flags=re.S)
        text = re.sub(r"(?<!\\)%[^\n]*", "", text)
        reference_section, fenced = False, False
        for line in text.splitlines():
            if line.lstrip().startswith(("```", "~~~")):
                fenced = not fenced
                continue
            if re.match(r"\s*#+\s", line):
                reference_section = bool(
                    re.search(r"reference|bibliograph", line, re.I)
                )
            if (
                fenced
                or reference_section
                or re.match(r"\s*(?:supplied\s+)?references?\s*:", line, re.I)
            ):
                continue
            prose.append(line)
    body = normalized("\n".join(prose))
    matches = list(
        re.finditer(r"(?<![/])y\(0\)=([+-]?\d+(?:\.\d*)?(?:[eE][+-]?\d+)?)", body)
    )
    return (
        bool(matches)
        and len(matches) == len(re.findall(r"(?<![/])y\(0\)=", body))
        and all(
            float(match.group(1)) == 1.0
            and not re.match(r"[/+*=-]|\\(?:times|cdot)", body[match.end() :])
            for match in matches
        )
    )


def author_metadata(text: str) -> list[tuple[str, str]]:
    """Compare literal braced identity commands; do not expand TeX or infer names."""
    text = re.sub(r"(?<!\\)%[^\n]*", "", text)
    values = []
    for match in re.finditer(
        r"\\(author|affiliation|email)\b(?:\s*\[[^\]]*\])?\s*\{", text
    ):
        depth, index = 1, match.end()
        while index < len(text) and depth:
            if text[index] in "{}" and (index == 0 or text[index - 1] != "\\"):
                depth += 1 if text[index] == "{" else -1
            index += 1
        if depth:
            raise ValueError("unclosed author metadata command")
        value = text[match.end() : index - 1].strip()
        if value:
            values.append((match.group(1), value))
    return sorted(values)


def inspect_run(run: Path, original: Path) -> dict[str, Any]:
    run, original = Path(run).resolve(), Path(original).resolve()
    gates: dict[str, bool] = {}
    problems: list[str] = []
    try:
        state, inputs = read(run / "state.json"), read(run / "input-manifest.json")
    except (OSError, ValueError) as exc:
        return {
            "classification": "INCOMPLETE_EVIDENCE",
            "all_observed_gates": False,
            "reported_status": None,
            "gates": {},
            "problems": [str(exc)],
        }
    files: dict[str, str] = {}
    root = original.parent
    try:
        root = Path(inputs["source_root"]).resolve()
        # Source manifests use absolute source paths; artifact paths remain relative.
        for name, digest in inputs["files"].items():
            candidate = Path(name)
            relative = (
                str(candidate.relative_to(root)) if candidate.is_absolute() else name
            )
            confined(root, relative)
            files[relative] = digest
        gates["original_preserved"] = (
            bool(files)
            and original == confined(root, inputs["entrypoint"]).resolve()
            and all(
                confined(root, name).is_file() and sha(confined(root, name)) == digest
                for name, digest in files.items()
            )
        )
    except (KeyError, OSError, ValueError, TypeError) as exc:
        gates["original_preserved"] = False
        problems.append(str(exc))
    delivered = run / "deliverables/revised-project"
    try:
        entry = confined(delivered, inputs["entrypoint"])
        gates["delivered_editable_exists"] = entry.is_file()
        texts = [
            p.read_text()
            for p in delivered.rglob("*")
            if p.suffix in {".md", ".tex"}
            and p.is_file()
            and not p.is_symlink()
            and p.resolve().is_relative_to(delivered.resolve())
        ]
        text = normalized("\n".join(texts))
        original_tex = "\n".join(
            confined(root, name).read_text()
            for name in files
            if Path(name).suffix == ".tex"
        )
        delivered_tex = "\n".join(
            p.read_text()
            for p in delivered.rglob("*.tex")
            if p.is_file()
            and not p.is_symlink()
            and p.resolve().is_relative_to(delivered.resolve())
        )
        gates["author_metadata_preserved"] = author_metadata(
            original_tex
        ) == author_metadata(delivered_tex)
        gates["corrected_derivative"] = bool(
            re.search(r"y'\(t\)=-2exp\(-2t\)", text)
        ) and not bool(re.search(r"y'\(t\)=\+?2exp\(-2t\)", text))
        gates["corrected_table_prose"] = bool(
            re.search(
                r"y\(1\)(?:=|≈|approximately(?:equalto)?)0\.135335(?:[^0-9]|$)", text
            )
        ) and not bool(re.search(r"y\(1\)=0\.5(?:[^0-9]|$)", text))
        gates["control_preserved"] = numerical_control_preserved(texts)
        gates["actual_source_changed"] = any(
            name in files and sha(p) != files[name]
            for p in delivered.rglob("*")
            if p.is_file() and not p.is_symlink()
            for name in [str(p.relative_to(delivered))]
        )
        expected = state.get("delivered_manifest", {})
        actual = {
            str(p.relative_to(delivered)): sha(p)
            for p in delivered.rglob("*")
            if p.is_file() and not p.is_symlink()
        }
        gates["delivered_hashes_match"] = bool(expected) and actual == expected
    except (OSError, ValueError, KeyError, TypeError) as exc:
        problems.append(str(exc))
        for key in (
            "delivered_editable_exists",
            "author_metadata_preserved",
            "corrected_derivative",
            "corrected_table_prose",
            "control_preserved",
            "actual_source_changed",
            "delivered_hashes_match",
        ):
            gates[key] = False
    try:
        events = [
            json.loads(line)
            for line in (run / "events.jsonl").read_text().splitlines()
            if line.strip()
        ]
        completed = state.get("completed", {})
        contexts: set[str] = set()
        observed: set[str] = set()
        student_sequences: list[int] = []
        verified_sequences: list[int] = []
        for key, task in completed.items():
            role = task.get("role")
            report = read(confined(run, task["result_path"]))
            dispatches = [
                e
                for e in events
                if e.get("kind") == "dispatch"
                and e.get("data", {}).get("reservation") == key
                and e["data"].get("role") == role
            ]
            completions = [
                e
                for e in events
                if e.get("kind") == "complete"
                and e.get("data", {}).get("reservation") == key
            ]
            if (
                not dispatches
                or not completions
                or min(e["sequence"] for e in completions)
                <= min(e["sequence"] for e in dispatches)
            ):
                continue
            sequence = min(e["sequence"] for e in completions)
            context = (
                task.get("native_task_id")
                or report.get("native_task_id")
                or task.get("context_id")
            )
            evidence = report.get("context_evidence", [])
            metadata = "\n".join(confined(run, p).read_text() for p in evidence)
            mechanism = re.search(
                r"fork_turns|fork_context|fresh|separate.context|subagent|native",
                metadata,
                re.I,
            )
            record = report.get("context_record", {})
            separate = record.get("separate_context", report.get("independent")) is True
            exposed = record.get(
                "negotiation_exposed", report.get("negotiation_exposed")
            )
            stage = task.get("stage", "INDEPENDENT_REVIEW")
            history_free_required = role == "auditor" or (
                role in {"R1", "R2", "R3", "R4"} and stage != "RE_REVIEW"
            )
            independent = (
                separate
                and (role == "student" or report.get("independent") is True)
                and (not history_free_required or exposed is False)
            )
            if record and record.get("context_id") != context:
                independent = False
            for path, expected_hash in task.get("context_hashes", {}).items():
                if sha(confined(run, path)) != expected_hash:
                    independent = False
            if (
                context
                and context not in contexts
                and context in metadata
                and mechanism
                and independent
            ):
                contexts.add(context)
                observed.add(role)
            if (
                role == "student"
                and task.get("candidate_before")
                and task.get("candidate_after")
                and task["candidate_before"] != task["candidate_after"]
            ):
                student_sequences.append(sequence)
            if (
                role in {"R1", "R2", "R3", "R4", "auditor"}
                and report.get("snapshot_hash") == state.get("snapshot")
                and report.get("verdict") == "pass"
            ):
                verified_sequences.append(sequence)
        gates["native_role_metadata_recorded"] = {
            "R1",
            "R2",
            "R3",
            "R4",
            "student",
            "auditor",
        } <= observed
        gates["student_diff_recorded"] = bool(student_sequences)
        gates["subsequent_review_recorded"] = bool(student_sequences) and any(
            v > min(student_sequences) for v in verified_sequences
        )
        issues = read(run / "issues.json") if (run / "issues.json").exists() else []
        closed = [
            i
            for i in issues
            if i.get("status") == "resolved_verified"
            and i.get("verification_snapshot") == state.get("snapshot")
            and i.get("related_changes")
            and i.get("history")
            and i.get("verification_artifacts")
        ]
        gates["verified_issue_history_recorded"] = len(closed) >= 2 and all(
            all(
                confined(run, p).is_file() and sha(confined(run, p)) == h
                for p, h in i["verification_artifacts"].items()
            )
            for i in closed
        )
    except (OSError, ValueError, KeyError, TypeError) as exc:
        problems.append(str(exc))
        for key in (
            "native_role_metadata_recorded",
            "student_diff_recorded",
            "subsequent_review_recorded",
            "verified_issue_history_recorded",
        ):
            gates[key] = False
    observed_all = bool(gates) and all(gates.values())
    return {
        "classification": "RECORDED_GATES_OBSERVED"
        if observed_all
        else "INCOMPLETE_EVIDENCE",
        "all_observed_gates": observed_all,
        "reported_status": state.get("status"),
        "gates": gates,
        "problems": problems,
        "limitations": [
            "Saved metadata is not independent proof of native model execution.",
            "This fixture checker does not certify scientific acceptance or installation discovery.",
            "Author checking compares literal author/affiliation/email commands only; it does not expand TeX.",
            "Control preservation checks the fixture numerical initial value in prose, not verbatim wording; reference-section filtering is limited.",
        ],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("run", type=Path)
    parser.add_argument("original", type=Path)
    args = parser.parse_args()
    result = inspect_run(args.run, args.original)
    print(json.dumps(result, indent=2))
    return 0 if result["all_observed_gates"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
