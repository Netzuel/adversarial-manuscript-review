#!/usr/bin/env python3
"""Local review records and structural gates; no inference or scientific certification."""

import argparse
import fcntl
import hashlib
import json
import os
import platform
import shutil
import signal
import subprocess
import sys
import time
import uuid
from pathlib import Path

from amr_files import ingest, manifest, promote

SCHEMA = 1
DEFAULTS_PATH = Path(__file__).resolve().parents[1] / "defaults.json"
TERMINAL = {
    "PASS_INTERNAL",
    "REVISION_REQUIRED",
    "BLOCKED_EVIDENCE",
    "BLOCKED_INPUT",
    "BLOCKED_PERMISSION",
    "BLOCKED_CAPABILITY",
    "STOPPED_BUDGET",
    "STOPPED_NO_PROGRESS",
    "INTERRUPTED",
    "ERROR",
}
FLOW = {
    "CONTRACT": ["SNAPSHOT"],
    "SNAPSHOT": ["INDEPENDENT_REVIEW"],
    "INDEPENDENT_REVIEW": ["EDITORIAL_TRIAGE"],
    "EDITORIAL_TRIAGE": ["STUDENT_REVISION", "FRESH_AUDIT"],
    "STUDENT_REVISION": ["VALIDATION"],
    "VALIDATION": ["RE_REVIEW"],
    "RE_REVIEW": ["STUDENT_REVISION", "FRESH_AUDIT"],
    "FRESH_AUDIT": ["STUDENT_REVISION", "FINALIZE"],
}
ROLES = {"R1", "R2", "R3", "R4", "student", "auditor"}
ISSUE_FIELDS = "id originating_reviewer round snapshot_hash location affected_claim_ids category severity confidence allegation_type problem supporting_evidence scientific_consequence resolution_condition verification_method student_response related_changes verification_artifacts status closure_author closure_reason history".split()
STATUSES = {
    "open",
    "in_progress",
    "pending_verification",
    "resolved_verified",
    "rebutted_verified",
    "blocked",
    "accepted_minor_limitation",
    "reopened",
}


class ReviewError(RuntimeError):
    pass


def digest(value):
    return hashlib.sha256(
        json.dumps(value, sort_keys=True, ensure_ascii=False).encode()
    ).hexdigest()


def hash_file(path):
    value = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            value.update(chunk)
    return value.hexdigest()


def check_provenance(plan, working_directory):
    argv = plan["argv"]
    executable = argv[0]
    if "/" not in executable:
        executable = shutil.which(executable)
    if not executable:
        raise ReviewError("check executable unavailable")
    executable_path = Path(executable)
    if not executable_path.is_absolute():
        executable_path = working_directory / executable_path
    files = {executable_path.resolve(strict=True)}
    for argument in argv[1:]:
        path = Path(argument)
        if not path.is_absolute():
            path = working_directory / path
        try:
            if path.is_file():
                files.add(path.resolve(strict=True))
        except OSError:
            # Inline code and long option values are not necessarily paths.
            continue
    declared = plan.get("referenced_inputs", [])
    if not isinstance(declared, list) or not all(
        isinstance(path, str) for path in declared
    ):
        raise ReviewError("referenced inputs must be a list of file paths")
    for argument in declared:
        path = Path(argument)
        if not path.is_absolute():
            path = working_directory / path
        if not path.is_file():
            raise ReviewError("missing referenced input: " + argument)
        files.add(path.resolve(strict=True))
    environment = {
        "system": platform.system(),
        "release": platform.release(),
        "machine": platform.machine(),
        "helper_python_executable": sys.executable,
        "helper_python_version": platform.python_version(),
        "thread_limits": {
            key: os.environ[key]
            if os.environ[key].isdigit()
            else "non-numeric value omitted"
            for key in (
                "OMP_NUM_THREADS",
                "OPENBLAS_NUM_THREADS",
                "MKL_NUM_THREADS",
                "VECLIB_MAXIMUM_THREADS",
                "NUMEXPR_NUM_THREADS",
                "PYTHONHASHSEED",
            )
            if key in os.environ
        },
    }
    return {
        "code_input_hashes": {str(path): hash_file(path) for path in sorted(files)},
        "command_hash": digest(argv),
        "environment": environment,
    }


def read(path):
    return json.loads(Path(path).read_text())


def atomic(path, value):
    path = Path(path)
    if path.is_symlink():
        raise ReviewError("symlink output rejected")
    temporary = path.with_name(path.name + "." + uuid.uuid4().hex + ".tmp")
    with temporary.open("w") as stream:
        json.dump(value, stream, ensure_ascii=False, indent=2, sort_keys=True)
        stream.write("\n")
        stream.flush()
        os.fsync(stream.fileno())
    os.replace(temporary, path)


def original_ok(path):
    for name, expected in read(path / "input-manifest.json")["files"].items():
        p = Path(name)
        if not p.is_file() or hashlib.sha256(p.read_bytes()).hexdigest() != expected:
            raise ReviewError("original input changed: " + name)


def initialize(
    source, resume=False, review_only=False, in_place=False, max_rounds=None
):
    source = Path(source).absolute()
    if not source.resolve(strict=True).is_relative_to(source.parent.resolve()):
        raise ReviewError("source symlink escapes project")
    if max_rounds is not None and max_rounds < 1:
        raise ReviewError("max-rounds must be positive")
    if review_only and in_place:
        raise ReviewError("review-only cannot promote")
    root = source.parent / (source.stem + ".review")
    if root.is_symlink():
        raise ReviewError("symlink run root rejected")
    root.mkdir(exist_ok=True)
    if resume:
        choices = [
            p.parent
            for p in root.glob("*/state.json")
            if read(p).get("source") == str(source)
            and read(p).get("status") in (None, "INTERRUPTED")
        ]
        if len(choices) != 1:
            raise ReviewError(
                "resume requires one compatible incomplete run; found "
                + str(len(choices))
            )
        path = choices[0]
        original_ok(path)
        owner = read(path / "owner.json")
        if owner.get("session"):
            # No timeout takeover while a host task could still be running.
            raise ReviewError(
                "run owned; release with recorded session token before resume"
            )
        token = uuid.uuid4().hex
        with Run(path, None, claim=token) as run:
            run.event("resume", {})
        return {"run": str(path), "session": token}
    limits = read(DEFAULTS_PATH)
    caps = {
        "max_rounds": 4,
        "max_dispatches": 32,
        "max_concurrent": 3,
        "max_audits": 2,
        "wall_seconds": 5400,
        "check_seconds": 60,
        "round_check_seconds": 300,
        "no_progress_rounds": 2,
    }
    if set(limits) != set(caps) or any(
        type(limits[k]) is not int or not 0 < limits[k] <= cap
        for k, cap in caps.items()
    ):
        raise ReviewError(
            "defaults must contain positive integer limits within documented caps"
        )
    if max_rounds is not None:
        limits["max_rounds"] = max_rounds
    path = root / (time.strftime("%Y%m%dT%H%M%S") + "-" + uuid.uuid4().hex[:8])
    path.mkdir()
    for folder in ["snapshots", "checkpoints", "rounds", "evidence", "deliverables"]:
        (path / folder).mkdir()
    inputs = ingest(source, path / "candidate")
    atomic(path / "input-manifest.json", inputs)
    for name, data in [
        ("issues.json", []),
        ("coverage.json", {}),
        ("claims-evidence.json", {}),
    ]:
        atomic(path / name, data)
    token = uuid.uuid4().hex
    atomic(path / "owner.json", {"session": token, "created": time.time()})
    atomic(
        path / "state.json",
        {
            "schema_version": SCHEMA,
            "source": str(source),
            "entrypoint": inputs.get("entrypoint"),
            "stage": "INGEST",
            "status": None,
            "created": time.time(),
            "session": token,
            "review_only": review_only,
            "in_place": in_place,
            "snapshot": None,
            "contract_hash": None,
            "round": 1,
            "no_progress": 0,
            "budget": {
                **limits,
                "dispatches": 0,
                "audit_attempts": 0,
                "check_used": {},
            },
            "active": {},
            "completed": {},
            "verdicts": {},
            "checks": {},
            "sequence": 0,
            "event_hash": None,
        },
    )
    with Run(path, token) as run:
        run.event("ingest", {"limitations": inputs.get("limitations", [])})
    return {"run": str(path), "session": token}


class Run:
    def __init__(self, path, session, claim=None):
        self.path = Path(path).resolve(strict=True)
        self.session = session
        self.claim = claim
        self.lock = None
        self.state = {}

    def __enter__(self):
        self.lock = (self.path / ".lock").open("a+")
        try:
            fcntl.flock(self.lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            self.lock.close()
            raise ReviewError("run command lock is held") from None
        try:
            owner = read(self.path / "owner.json")
            if self.claim:
                if owner.get("session"):
                    raise ReviewError("run already owned")
                atomic(
                    self.path / "owner.json",
                    {"session": self.claim, "created": time.time()},
                )
            elif owner.get("session") != self.session or not self.session:
                raise ReviewError("session ownership mismatch")
            self.state = read(self.path / "state.json")
            self.verify()
            return self
        except BaseException:
            self.__exit__(None, None, None)
            raise

    def __exit__(self, *_):
        if self.lock:
            fcntl.flock(self.lock, fcntl.LOCK_UN)
            self.lock.close()

    def verify(self):
        if self.state.get("schema_version") != SCHEMA:
            raise ReviewError("unsupported state version")
        events = self.path / "events.jsonl"
        previous = None
        count = 0
        last_entry = {}
        if events.exists():
            for line in events.read_text().splitlines():
                entry = json.loads(line)
                claimed = entry.pop("hash")
                if entry["previous"] != previous or digest(entry) != claimed:
                    raise ReviewError("event history integrity failure")
                previous = claimed
                count += 1
                last_entry = entry
        if previous != self.state["event_hash"] or count != self.state["sequence"]:
            raise ReviewError(
                "partial event commit: preserve records and inspect latest checkpoint; do not replay"
            )
        if count:
            checkpoint_path = self.path / "checkpoints" / f"{count:05d}.json"
            if not checkpoint_path.is_file():
                raise ReviewError("missing state checkpoint; inspect partial commit")
            checkpoint = read(checkpoint_path)
            if checkpoint != self.state or read(self.path / "state.json") != self.state:
                raise ReviewError("state differs from committed checkpoint")
            projection = dict(checkpoint)
            projection.pop("event_hash", None)
            # Older runs have an equal checkpoint but no event-bound digest.
            # The next ordinary event adds the digest without a migration.
            if (
                last_entry.get("checkpoint_hash")
                and digest(projection) != last_entry["checkpoint_hash"]
            ):
                raise ReviewError("checkpoint digest differs from committed event")
        if (
            self.state["contract_hash"]
            and digest(read(self.path / "review-contract.json"))
            != self.state["contract_hash"]
        ):
            raise ReviewError("contract changed outside editor protocol")
        for folder in (self.path / "snapshots").iterdir():
            if folder.is_dir() and digest(manifest(folder / "project")) != folder.name:
                raise ReviewError("immutable snapshot was altered")

    def event(self, kind, data):
        projection = dict(self.state, sequence=self.state["sequence"] + 1)
        projection.pop("event_hash", None)
        entry = {
            "sequence": self.state["sequence"] + 1,
            "time": time.time(),
            "stage": self.state["stage"],
            "round": self.state["round"],
            "kind": kind,
            "data": data,
            "previous": self.state["event_hash"],
            "checkpoint_hash": digest(projection),
        }
        entry["hash"] = digest(entry)
        with (self.path / "events.jsonl").open("a") as stream:
            stream.write(json.dumps(entry, sort_keys=True) + "\n")
            stream.flush()
            os.fsync(stream.fileno())
        self.state.update(sequence=entry["sequence"], event_hash=entry["hash"])
        atomic(self.path / "state.json", self.state)
        atomic(self.path / "checkpoints" / f"{entry['sequence']:05d}.json", self.state)
        (self.path / "RESUME.md").write_text(
            f"Stage: {self.state['stage']}\nStatus: {self.state['status']}\nRound: {self.state['round']}\nSnapshot: {self.state['snapshot']}\nContract: review-contract.json\nIssues: issues.json\nBudget: state.json\nActive reservations: {list(self.state['active'])}\nResume an active reservation; do not duplicate dispatch or edit.\n"
        )

    def boundary(self):
        if self.state.get("abandoned"):
            raise ReviewError(
                "run contains abandoned tasks; finalize a non-acceptance result"
            )
        if self.state["status"] and self.state["status"] != "INTERRUPTED":
            raise ReviewError("run is terminal")
        if time.time() - self.state["created"] > self.state["budget"]["wall_seconds"]:
            self.state["status"] = "STOPPED_BUDGET"
            self.event("wall_budget", {"soft": True})
            raise ReviewError("wall budget exhausted")

    def contract(self, data):
        if self.state["contract_hash"]:
            raise ReviewError(
                "contract is frozen; start a new explicitly scoped run for amendments"
            )
        required = [
            "research_question",
            "claims",
            "required_areas",
            "required_checks",
            "acceptance_conditions",
            "allowed_actions",
            "limitations",
        ]
        if (
            any(k not in data for k in required)
            or not data["claims"]
            or not data["required_areas"]
        ):
            raise ReviewError("missing contract criteria")
        data = dict(
            data,
            budget=self.state["budget"].copy(),
            output_policy={
                "review_only": self.state["review_only"],
                "in_place": self.state["in_place"],
            },
        )
        atomic(self.path / "review-contract.json", data)
        self.state.update(contract_hash=digest(data), stage="CONTRACT")
        self.event("contract", {})

    def snapshot(self):
        self.boundary()
        if not self.state["contract_hash"] or self.state["active"]:
            raise ReviewError("snapshot needs a contract and no active children")
        files = manifest(self.path / "candidate")
        key = digest(files)
        target = self.path / "snapshots" / key
        if not target.exists():
            target.mkdir()
            shutil.copytree(self.path / "candidate", target / "project", symlinks=False)
            atomic(target / "manifest.json", files)
        self.state.setdefault("initial_snapshot", key)
        self.state["snapshot"] = key
        if self.state["stage"] == "CONTRACT":
            self.state["stage"] = "SNAPSHOT"
        self.event("snapshot", {"hash": key})
        return key

    def transition(self, target):
        self.boundary()
        if target not in FLOW.get(self.state["stage"], []):
            raise ReviewError("invalid state transition")
        if self.state["active"]:
            raise ReviewError("active children must complete before transition")
        if self.state["stage"] == "RE_REVIEW":
            substantive = [
                (i["id"], i["status"])
                for i in read(self.path / "issues.json")
                if i["severity"] in ("major", "critical")
            ]
            self.progress(
                digest(
                    {
                        "issues": substantive,
                        "coverage": {
                            area: sorted(record.get("locations", []))
                            for area, record in read(
                                self.path / "coverage.json"
                            ).items()
                            if isinstance(record, dict)
                        },
                    }
                )
            )
            if self.state["status"] == "STOPPED_NO_PROGRESS":
                raise ReviewError("two rounds without material progress")
        if target == "STUDENT_REVISION":
            if self.state["review_only"]:
                raise ReviewError("review-only prohibits revision")
            if self.state["stage"] in ("EDITORIAL_TRIAGE", "RE_REVIEW", "FRESH_AUDIT"):
                if self.state["round"] >= self.state["budget"]["max_rounds"]:
                    self.state["status"] = "STOPPED_BUDGET"
                    self.event("round_budget", {})
                    raise ReviewError("round budget exhausted")
                self.state["round"] += 1
        self.state["stage"] = target
        self.event("transition", {"target": target})

    def protected(self, role):
        result = {}
        for p in self.path.rglob("*"):
            if p.is_symlink():
                raise ReviewError("symlink in run rejected")
            if not p.is_file():
                continue
            rel = p.relative_to(self.path).as_posix()
            if rel in (
                "state.json",
                "events.jsonl",
                "owner.json",
                ".lock",
                "RESUME.md",
            ) or rel.startswith(("checkpoints/", "rounds/guards/")):
                continue
            if role == "student" and rel.startswith("candidate/"):
                continue
            result[rel] = hashlib.sha256(p.read_bytes()).hexdigest()
        return result

    def dispatch(self, role, context):
        self.boundary()
        if role not in ROLES or not context:
            raise ReviewError("unknown role or missing native context ID")
        expected = {"student": {"STUDENT_REVISION"}, "auditor": {"FRESH_AUDIT"}}.get(
            role, {"INDEPENDENT_REVIEW", "RE_REVIEW"}
        )
        if self.state["stage"] not in expected:
            raise ReviewError("role invalid for current stage")
        b = self.state["budget"]
        if len(self.state["active"]) >= b["max_concurrent"]:
            raise ReviewError("concurrent dispatch budget exhausted")
        if b["dispatches"] >= b["max_dispatches"] or (
            role == "auditor" and b["audit_attempts"] >= b["max_audits"]
        ):
            self.state["status"] = "STOPPED_BUDGET"
            self.event("dispatch_budget", {})
            raise ReviewError("dispatch budget exhausted")
        if any(
            d["context_id"] == context
            for d in [*self.state["active"].values(), *self.state["completed"].values()]
        ):
            raise ReviewError("context ID must be new")
        if self.state["snapshot"] != digest(manifest(self.path / "candidate")):
            raise ReviewError("candidate changed; freeze a new snapshot")
        key = uuid.uuid4().hex[:12]
        protected = self.protected(role)
        guard = self.path / "rounds" / "guards" / key
        for rel in protected:
            dst = guard / rel
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(self.path / rel, dst)
        self.state["active"][key] = {
            "role": role,
            "context_id": context,
            "snapshot_hash": self.state["snapshot"],
            "protected": protected,
            "candidate_before": manifest(self.path / "candidate"),
            "stage": self.state["stage"],
        }
        b["dispatches"] += 1
        if role == "auditor":
            b["audit_attempts"] += 1
        self.event(
            "dispatch", {"reservation": key, "role": role, "context_id": context}
        )
        return key

    def complete(self, key, data):
        self.verify()
        if key not in self.state["active"]:
            raise ReviewError("unknown/completed reservation; do not repeat")
        task = self.state["active"][key]
        actual = self.protected(task["role"])
        # Reports saved by other completions are coordinator writes, not child writes.
        actual = {
            k: v
            for k, v in actual.items()
            if not k.startswith("rounds/results/")
            and not (k.startswith("evidence/context/") and k not in task["protected"])
            and not (
                task["role"] == "student"
                and k.startswith("evidence/student-output/")
                and k not in task["protected"]
            )
        }
        baseline = {
            k: v
            for k, v in task["protected"].items()
            if not k.startswith("rounds/results/")
        }
        if actual != baseline:
            changed = [
                p
                for p in set(actual) | set(baseline)
                if actual.get(p) != baseline.get(p)
            ]
            # Restore candidate only; retain altered protected reports as audit evidence.
            for rel in changed:
                if rel.startswith("candidate/"):
                    p = self.path / rel
                    if rel in baseline:
                        shutil.copy2(self.path / "rounds" / "guards" / key / rel, p)
                    elif p.is_file():
                        p.unlink()
            self.state["status"] = "ERROR"
            self.event("unauthorized_write", {"reservation": key, "paths": changed})
            raise ReviewError("unauthorized write detected; stage invalidated")
        if data.get("snapshot_hash") != task["snapshot_hash"]:
            raise ReviewError("stale snapshot report")
        if task["role"] != "student" and data.get("verdict") not in (
            "pass",
            "revise",
            "blocked",
        ):
            raise ReviewError("report needs pass/revise/blocked verdict")
        if data.get("context_record"):
            record = dict(data["context_record"])
            context_dir = self.path / "evidence" / "context" / key
            transcript = Path(record.pop("transcript_source")).resolve(strict=True)
            if transcript.is_relative_to(self.path):
                raise ReviewError("stage native transcript outside the guarded run")
            if not transcript.is_file():
                raise ReviewError("native transcript must be a regular file")
            context_dir.mkdir(parents=True, exist_ok=True)
            old_transcript = context_dir / "transcript.txt"
            if (
                old_transcript.exists()
                and old_transcript.read_bytes() != transcript.read_bytes()
            ):
                raise ReviewError(
                    "partial native transcript conflicts; inspect before retry"
                )
            shutil.copy2(transcript, context_dir / "transcript.txt")
            record["transcript_artifact"] = str(
                (context_dir / "transcript.txt").relative_to(self.path)
            )
            record["transcript_sha256"] = hashlib.sha256(
                transcript.read_bytes()
            ).hexdigest()
            atomic(context_dir / "context.json", record)
            data = dict(
                data,
                context_evidence=[
                    str((context_dir / "context.json").relative_to(self.path))
                ],
            )
        out = self.path / "rounds" / "results"
        out.mkdir(exist_ok=True)
        atomic(out / (key + ".json"), data)
        if data.get("context_id"):
            task["context_id"] = data["context_id"]
        task["context_hashes"] = (
            self.artifacts(data["context_evidence"])
            if data.get("context_evidence")
            else {}
        )
        task["result_hash"] = digest(data)
        task["result_path"] = "rounds/results/" + key + ".json"
        task["candidate_after"] = manifest(self.path / "candidate")
        self.state["completed"][key] = task
        del self.state["active"][key]
        if task["role"] != "student":
            self.state["verdicts"][task["role"]] = {
                "reservation": key,
                **data,
                "context_id": task["context_id"],
                "review_stage": task["stage"],
            }
            if task["stage"] == "INDEPENDENT_REVIEW":
                self.state.setdefault("initial_verdicts", {})[task["role"]] = (
                    self.state["verdicts"][task["role"]]
                )
        self.event("complete", {"reservation": key, "result_hash": digest(data)})

    def abandon(self, key, proof):
        self.verify()
        if key not in self.state["active"]:
            raise ReviewError("unknown/inactive reservation; do not repeat abandonment")
        task = self.state["active"][key]
        if (
            proof.get("host_tasks_inactive") is not True
            or proof.get("inspected") is not True
            or not proof.get("reason")
            or proof.get("reservation_context") != task["context_id"]
            or not isinstance(proof.get("native_context_id"), str)
            or not proof["native_context_id"].strip()
        ):
            raise ReviewError(
                "abandon requires inspected native inactivity evidence, reservation context, and native context ID"
            )
        hashes = self.artifacts(proof.get("artifacts", []))
        if any((self.path / name).stat().st_size == 0 for name in hashes):
            raise ReviewError("native inactivity evidence must not be empty")
        proof = dict(proof, artifact_hashes=hashes)
        self.state.setdefault("abandoned", {})[key] = {"task": task, "proof": proof}
        del self.state["active"][key]
        self.state["status"] = self.state["status"] or "INTERRUPTED"
        self.event("task_abandoned", {"reservation": key, "proof": proof})
        return {"status": self.state["status"], "abandoned": key}

    def issues(self, data):
        old = {i["id"]: i for i in read(self.path / "issues.json")}
        for item in data:
            if any(k not in item for k in ISSUE_FIELDS):
                raise ReviewError("missing issue fields")
            if (
                item["severity"] not in ("critical", "major", "minor", "suggestion")
                or item["status"] not in STATUSES
            ):
                raise ReviewError("invalid issue severity/status")
            if not all(
                item[k]
                for k in (
                    "location",
                    "problem",
                    "resolution_condition",
                    "verification_method",
                    "supporting_evidence",
                )
            ):
                raise ReviewError("issue lacks concrete evidence/condition")
            if item["id"] in old:
                raise ReviewError(
                    "issue already exists; use close or reopen without replacing history"
                )
            if (
                item["status"] != "open"
                or item["snapshot_hash"] != self.state["snapshot"]
            ):
                raise ReviewError("new issues must be open and current")
            old[item["id"]] = item
        atomic(self.path / "issues.json", list(old.values()))
        self.event("issues", {"ids": [i["id"] for i in data]})

    def artifacts(self, paths):
        if not paths:
            raise ReviewError("missing evidence artifacts")
        values = {}
        for rel in paths:
            p = self.path / rel
            if (
                p.is_symlink()
                or not p.resolve().is_relative_to(self.path)
                or not p.is_file()
            ):
                raise ReviewError("missing/unsafe evidence artifact: " + str(rel))
            values[rel] = hashlib.sha256(p.read_bytes()).hexdigest()
        return values

    def close(self, key, data):
        items = read(self.path / "issues.json")
        item = next((i for i in items if i["id"] == key), None)
        if not item:
            raise ReviewError("unknown issue")
        if data.get("author") not in (item["originating_reviewer"], "editor"):
            raise ReviewError("student cannot close issues")
        status = data.get("status")
        if status not in (
            "resolved_verified",
            "rebutted_verified",
            "accepted_minor_limitation",
            "reopened",
            "blocked",
        ):
            raise ReviewError("invalid closure status")
        if (
            not data.get("reason")
            or data.get("snapshot_hash") != self.state["snapshot"]
            or not data.get("inspected")
        ):
            raise ReviewError("closure needs current inspected evidence and reason")
        artifacts = self.artifacts(data.get("artifacts", []))
        if status == "accepted_minor_limitation" and item["severity"] in (
            "major",
            "critical",
        ):
            raise ReviewError(
                "substantive issue cannot be hidden as a minor limitation"
            )
        if status == "resolved_verified":
            original = read(
                self.path / "snapshots" / item["snapshot_hash"] / "manifest.json"
            )
            now = manifest(self.path / "candidate")
            changed = [
                p for p in set(original) | set(now) if original.get(p) != now.get(p)
            ]
            if not changed or not set(data.get("related_changes", [])).intersection(
                changed
            ):
                raise ReviewError("false fix: no matching actual diff")
        item["history"].append(data)
        item.update(
            student_response=data.get("student_response", item["student_response"]),
            status=status,
            closure_author=data["author"],
            closure_reason=data["reason"],
            verification_artifacts=artifacts,
            related_changes=data.get("related_changes", []),
            verification_snapshot=self.state["snapshot"],
        )
        atomic(self.path / "issues.json", items)
        self.event("issue_status", {"id": key, "status": status})

    def maps(self, data):
        if self.state["active"]:
            raise ReviewError("finish active work before importing evidence maps")
        for claim, record in data.get("claims", {}).items():
            if record.get("snapshot_hash") != self.state["snapshot"]:
                raise ReviewError("claim evidence is stale")
            if record.get("status") == "supported":
                record["artifact_hashes"] = self.artifacts(record.get("artifacts", []))
        atomic(self.path / "coverage.json", data.get("coverage", {}))
        atomic(self.path / "claims-evidence.json", data.get("claims", {}))
        self.event("evidence_maps", {"claims": list(data.get("claims", {}))})

    def acceptance_errors(self):
        errors = []
        if self.state.get("abandoned"):
            errors.append(
                "run has abandoned tasks; acceptance and replay are prohibited"
            )
        for role in ("R1", "R2", "R3", "R4"):
            initial = self.state.get("initial_verdicts", {}).get(role, {})
            if (
                not initial.get("independent")
                or initial.get("negotiation_exposed") is not False
                or not initial.get("context_evidence")
            ):
                errors.append("missing initial independent review " + role)
                continue
            try:
                record = read(self.path / initial["context_evidence"][0])
                task = self.state["completed"][initial["reservation"]]
                if (
                    record.get("context_id") != initial.get("context_id")
                    or record.get("separate_context") is not True
                    or record.get("negotiation_exposed") is not False
                    or self.artifacts(initial["context_evidence"])
                    != task.get("context_hashes")
                    or digest(read(self.path / task["result_path"]))
                    != task.get("result_hash")
                ):
                    errors.append("invalid initial independent review " + role)
            except (ReviewError, ValueError, KeyError):
                errors.append("invalid initial independent review " + role)
        if read(self.path / "input-manifest.json").get("blocked_input"):
            errors.append("faithful editable input unavailable")
        contract = read(self.path / "review-contract.json")
        snapshot = self.state["snapshot"]
        if snapshot != digest(manifest(self.path / "candidate")):
            errors.append("candidate differs from reviewed snapshot")
        coverage = read(self.path / "coverage.json")
        claims = read(self.path / "claims-evidence.json")
        for area in contract["required_areas"]:
            if (
                not isinstance(coverage.get(area), dict)
                or coverage[area].get("snapshot_hash") != snapshot
                or not coverage[area].get("locations")
            ):
                errors.append("missing current coverage: " + area)
        for claim in contract["claims"]:
            record = claims.get(claim, {})
            if (
                record.get("status") != "supported"
                or record.get("snapshot_hash") != snapshot
            ):
                errors.append("missing current claim evidence: " + claim)
            else:
                try:
                    if self.artifacts(record.get("artifacts", [])) != record.get(
                        "artifact_hashes"
                    ):
                        errors.append("changed claim evidence: " + claim)
                except ReviewError as e:
                    errors.append(str(e))
        for item in read(self.path / "issues.json"):
            if item["severity"] in ("critical", "major") and item["status"] not in (
                "resolved_verified",
                "rebutted_verified",
            ):
                errors.append("unresolved substantive issue " + item["id"])
            if item["status"] in ("resolved_verified", "rebutted_verified"):
                if item.get("verification_snapshot") != snapshot:
                    errors.append("stale issue closure " + item["id"])
                try:
                    if (
                        self.artifacts(list(item["verification_artifacts"]))
                        != item["verification_artifacts"]
                    ):
                        errors.append("changed closure evidence " + item["id"])
                except ReviewError as e:
                    errors.append(str(e))
        contexts = []
        for role in ["R1", "R2", "R3", "R4", "auditor"]:
            verdict = self.state["verdicts"].get(role, {})
            if (
                verdict.get("snapshot_hash") != snapshot
                or verdict.get("verdict") != "pass"
                or not verdict.get("coverage")
            ):
                errors.append("missing current passing verdict " + role)
            if (
                not verdict.get("independent")
                or (
                    role == "auditor"
                    and verdict.get("negotiation_exposed") is not False
                )
                or not verdict.get("context_evidence")
            ):
                errors.append("unverified separate context " + role)
            else:
                try:
                    hashes = self.artifacts(verdict["context_evidence"])
                    task = self.state["completed"][verdict["reservation"]]
                    if hashes != task.get("context_hashes"):
                        raise ReviewError("native context provenance changed")
                    record = read(self.path / verdict["context_evidence"][0])
                    if (
                        record.get("host") not in ("codex", "claude")
                        or record.get("context_id") != verdict.get("context_id")
                        or record.get("separate_context") is not True
                        or not record.get("mechanism")
                    ):
                        raise ReviewError("native context provenance is incomplete")
                    if (
                        role == "auditor"
                        or verdict.get("review_stage") == "INDEPENDENT_REVIEW"
                    ) and record.get("negotiation_exposed") is not False:
                        raise ReviewError(
                            "native context provenance exposes negotiation"
                        )
                    transcript = record.get("transcript_artifact")
                    if not transcript or self.artifacts([transcript])[
                        transcript
                    ] != record.get("transcript_sha256"):
                        raise ReviewError(
                            "native context provenance lacks unchanged transcript"
                        )
                except (ReviewError, ValueError, KeyError) as e:
                    errors.append("native context provenance: " + str(e))
            if verdict.get("context_id") in contexts:
                errors.append("context reused")
            contexts.append(verdict.get("context_id"))
            task = self.state["completed"].get(verdict.get("reservation"), {})
            if not task or digest(read(self.path / task["result_path"])) != task.get(
                "result_hash"
            ):
                errors.append("review report changed " + role)
        for check in contract["required_checks"]:
            record = self.state["checks"].get(check, {})
            if record.get("snapshot_hash") != snapshot or record.get("exit_code") != 0:
                errors.append("missing required check " + check)
            else:
                try:
                    if self.artifacts(record.get("artifacts", [])) != record.get(
                        "artifact_hashes"
                    ):
                        errors.append("changed check evidence " + check)
                except ReviewError as e:
                    errors.append(str(e))
        if self.state["active"]:
            errors.append("active children remain")
        if self.state["review_only"]:
            errors.append("review-only cannot claim a revised accepted candidate")
        return errors

    def check(self, plan):
        if self.state["active"]:
            raise ReviewError("complete active tasks before running checks")
        self.boundary()
        self.verify()
        if self.state["snapshot"] != digest(manifest(self.path / "candidate")):
            raise ReviewError("check requires the current frozen snapshot")
        protected_before = self.protected("reviewer")
        if (
            not plan.get("inspected")
            or not plan.get("reason")
            or not isinstance(plan.get("argv"), list)
            or not plan.get("argv")
            or not all(isinstance(s, str) for s in plan["argv"])
        ):
            raise ReviewError("external check requires inspected argv and reason")
        if plan.get("safe_cpu_offline") is not True:
            raise ReviewError("check must attest cheap CPU/offline scope")
        provenance = check_provenance(plan, self.path / "candidate")
        b = self.state["budget"]
        r = str(self.state["round"])
        used = b["check_used"].get(r, 0)
        timeout = min(
            b["check_seconds"], b["round_check_seconds"] - used, plan.get("timeout", 60)
        )
        if timeout <= 0:
            raise ReviewError("round check budget exhausted")
        # Reserve worst-case time before execution, so a crash never restores budget.
        b["check_used"][r] = used + timeout
        key = uuid.uuid4().hex[:12]
        self.event(
            "check_reserved",
            {"id": key, "plan": plan, "seconds": timeout, "provenance": provenance},
        )
        folder = self.path / "evidence" / ("check-" + key)
        folder.mkdir()
        start = time.time()
        with (
            (folder / "stdout.txt").open("w") as out,
            (folder / "stderr.txt").open("w") as err,
        ):
            process = subprocess.Popen(
                plan["argv"],
                cwd=self.path / "candidate",
                stdout=out,
                stderr=err,
                start_new_session=True,
            )
            try:
                code = process.wait(timeout=timeout)
            except subprocess.TimeoutExpired:
                os.killpg(process.pid, signal.SIGKILL)
                process.wait()
                code = 124
        self.verify()
        try:
            code_unchanged = all(
                hash_file(path) == value
                for path, value in provenance["code_input_hashes"].items()
            )
        except OSError:
            code_unchanged = False
        if not code_unchanged:
            self.event(
                "check_invalidated",
                {"id": key, "reason": "code or referenced input changed"},
            )
            raise ReviewError(
                "check code or referenced input changed; no verdict recorded"
            )
        protected_after = {
            name: value
            for name, value in self.protected("reviewer").items()
            if not name.startswith("evidence/check-" + key + "/")
        }
        if (
            self.state["snapshot"] != digest(manifest(self.path / "candidate"))
            or protected_before != protected_after
        ):
            self.event(
                "check_invalidated",
                {"id": key, "reason": "mutated candidate or protected evidence"},
            )
            raise ReviewError(
                "check mutated candidate or protected evidence; no verdict recorded"
            )
        result = {
            **provenance,
            "exit_code": code,
            "snapshot_hash": self.state["snapshot"],
            "seconds": time.time() - start,
            "plan": plan,
            "artifacts": [
                "evidence/check-" + key + "/stdout.txt",
                "evidence/check-" + key + "/stderr.txt",
            ],
        }
        result["artifact_hashes"] = self.artifacts(result["artifacts"])
        atomic(folder / "result.json", result)
        self.state["checks"][plan["id"]] = result
        self.event("check_complete", {"id": key, "exit_code": code})
        return result

    def progress(self, fingerprint):
        self.state["no_progress"] = (
            self.state["no_progress"] + 1
            if self.state.get("progress") == fingerprint
            else 0
        )
        self.state["progress"] = fingerprint
        if self.state["no_progress"] >= self.state["budget"].get(
            "no_progress_rounds", 2
        ):
            self.state["status"] = "STOPPED_NO_PROGRESS"
        self.event("progress", {"fingerprint": fingerprint})

    def finalize(self, status):
        if status not in TERMINAL:
            raise ReviewError("invalid terminal status")
        if self.state["active"]:
            raise ReviewError("active work must finish or be explicitly reconciled")
        if status == "PASS_INTERNAL":
            self.boundary()
            errors = self.acceptance_errors()
            if errors:
                raise ReviewError("; ".join(errors))
        destination = self.path / "deliverables"
        output = destination / "revised-project"
        if output.exists():
            raise ReviewError(
                "deliverables already exist; inspect instead of repeating finalize"
            )
        editable = not self.state["review_only"] and not read(
            self.path / "input-manifest.json"
        ).get("blocked_input")
        if editable and self.state["entrypoint"]:
            shutil.copytree(self.path / "candidate", output)
            if manifest(output) != manifest(self.path / "candidate"):
                raise ReviewError("delivery manifest mismatch")
        issues = read(self.path / "issues.json")
        entry = (
            ("revised-project/" + self.state["entrypoint"])
            if editable
            else "No faithful revised editable output; review artifacts only."
        )
        summary = f"# {status}\n\nInternal configured criteria only; not journal acceptance or proof of correctness.\n\nEditable entry point: {entry}\nSnapshot: {self.state['snapshot']}\nLimitations: {read(self.path / 'input-manifest.json').get('limitations', [])}\n"
        (destination / "REVIEW_RESULT.md").write_text(summary)
        (destination / "RESPONSE_TO_REVIEWERS.md").write_text(
            "# Responses\n\n"
            + "\n".join(
                f"{i['id']}: {i['student_response']} — {i['closure_reason']}"
                for i in issues
            )
        )
        (destination / "UNRESOLVED.md").write_text(
            "# Unresolved\n\n"
            + "\n".join(
                f"{i['id']}: {i['problem']} ({i['status']})"
                for i in issues
                if i["status"] not in ("resolved_verified", "rebutted_verified")
            )
        )
        import difflib

        before = (
            (self.path / "snapshots" / self.state["initial_snapshot"])
            if self.state.get("initial_snapshot")
            else None
        )
        changes = []
        if before:
            for name in manifest(self.path / "candidate"):
                new = self.path / "candidate" / name
                old = before / "project" / name
                if old.exists():
                    try:
                        changes.extend(
                            difflib.unified_diff(
                                old.read_text().splitlines(True),
                                new.read_text().splitlines(True),
                                fromfile=name,
                                tofile=name,
                            )
                        )
                    except UnicodeError:
                        pass
        (destination / "CHANGES.md").write_text(
            "# Changes\n\n```diff\n" + "".join(changes) + "\n```\n"
        )
        (destination / "REPRODUCIBILITY.md").write_text(
            "# Checks\n\nModel review is distinct from executed checks.\n\n"
            + json.dumps(self.state["checks"], indent=2)
        )
        self.state.update(
            status=status,
            stage="FINALIZE",
            delivered_manifest=manifest(output) if output.exists() else {},
        )
        self.event("finalize", {"status": status})
        if self.state["in_place"] and status == "PASS_INTERNAL":
            promotion = promote(
                self.path / "candidate",
                read(self.path / "input-manifest.json"),
                self.path / "backups",
                verified=True,
            )
            self.event("promote", {"result": promotion})
        return {"status": status, "deliverables": str(destination)}


def recover(path, session, proof):
    if (
        not proof.get("host_tasks_inactive")
        or not proof.get("inspected")
        or not proof.get("reason")
    ):
        raise ReviewError("recovery needs inspected native-host inactivity evidence")
    with Run(path, session) as run:
        run.event("ownership_recovery", proof)
        atomic(run.path / "owner.json", {"session": None, "released": time.time()})


def release(path, session):
    with Run(path, session) as run:
        run.event("release", {})
        atomic(run.path / "owner.json", {"session": None, "released": time.time()})


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run", type=Path)
    parser.add_argument("--session")
    sub = parser.add_subparsers(dest="command", required=True)
    init = sub.add_parser("init")
    init.add_argument("source", type=Path)
    for name in ("resume", "review-only", "in-place"):
        init.add_argument("--" + name, action="store_true")
    init.add_argument("--max-rounds", type=int)
    for command in ("status", "snapshot", "gate", "release"):
        sub.add_parser(command)
    for command in ("contract", "issues", "check", "maps"):
        sub.add_parser(command).add_argument("json", type=Path)
    sub.add_parser("transition").add_argument("stage")
    d = sub.add_parser("dispatch")
    d.add_argument("role")
    d.add_argument("--context", required=True)
    for command in ("complete", "close", "abandon"):
        d = sub.add_parser(command)
        d.add_argument("id")
        d.add_argument("json", type=Path)
    sub.add_parser("finalize").add_argument("status")
    sub.add_parser("progress").add_argument("fingerprint")
    sub.add_parser("recover").add_argument("json", type=Path)
    args = parser.parse_args()
    try:
        if args.command == "init":
            result = initialize(
                args.source,
                args.resume,
                args.review_only,
                args.in_place,
                args.max_rounds,
            )
        elif args.command == "recover":
            recover(args.run, args.session, read(args.json))
            result = {"recovered": True}
        elif args.command == "release":
            release(args.run, args.session)
            result = {"released": True}
        else:
            if not args.run or not args.session:
                raise ReviewError("--run and --session are required")
            with Run(args.run, args.session) as run:
                if args.command == "status":
                    result = run.state
                elif args.command == "snapshot":
                    result = {"snapshot_hash": run.snapshot()}
                elif args.command == "gate":
                    result = {"errors": run.acceptance_errors()}
                elif args.command in ("contract", "issues", "check", "maps"):
                    result = getattr(run, args.command)(read(args.json))
                elif args.command == "transition":
                    result = run.transition(args.stage)
                elif args.command == "dispatch":
                    result = {"reservation": run.dispatch(args.role, args.context)}
                elif args.command in ("complete", "close", "abandon"):
                    result = getattr(run, args.command)(args.id, read(args.json))
                elif args.command == "finalize":
                    result = run.finalize(args.status)
                else:
                    result = run.progress(args.fingerprint)
        print(json.dumps(result if result is not None else {"ok": True}, indent=2))
    except (ReviewError, OSError, ValueError, KeyError) as error:
        parser.exit(2, "amr: " + str(error) + "\n")


if __name__ == "__main__":
    main()
