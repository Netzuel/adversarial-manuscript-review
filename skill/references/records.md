# Helper interface and records

Use the executable `scripts/amr` launcher. It uses `python3` (Python 3.10+) by default and forwards literal arguments. `AMR_PYTHON` may select one executable, never a command string. Set AMR to the single resolved launcher path, for example `AMR="$HOME/.agents/skills/adversarial-manuscript-review/scripts/amr"` in Codex or `AMR="$HOME/.claude/skills/adversarial-manuscript-review/scripts/amr"` in Claude Code. Invoke it as `"$AMR"`; do not put an entire command string in the variable. For programmatic calls use `subprocess.run([launcher_path, ...])`, never eval. JSON payload files are editor staging files OUTSIDE the run, so guards cannot confuse editor writes with child changes.

```text
"$AMR" init SOURCE [--resume] [--review-only] [--in-place] [--max-rounds N]
"$AMR" --run RUN --session TOKEN contract /absolute/staging/contract.json
"$AMR" --run RUN --session TOKEN snapshot
"$AMR" --run RUN --session TOKEN transition INDEPENDENT_REVIEW
"$AMR" --run RUN --session TOKEN dispatch R1 --context unique-reservation-label
"$AMR" --run RUN --session TOKEN complete RESERVATION /absolute/staging/report.json
"$AMR" --run RUN --session TOKEN issues /absolute/staging/issues.json
"$AMR" --run RUN --session TOKEN maps /absolute/staging/maps.json
"$AMR" --run RUN --session TOKEN close I001 /absolute/staging/closure.json
"$AMR" --run RUN --session TOKEN check /absolute/staging/check-plan.json
"$AMR" --run RUN --session TOKEN pending
"$AMR" --run RUN --session TOKEN gate
"$AMR" --run RUN --session TOKEN finalize PASS_INTERNAL
"$AMR" --run RUN --session TOKEN release
```

`init` returns `run` and `session`; preserve both. `snapshot` returns the content hash. State is not an editable API. `status` inspects persisted state. Use `pending` after each completed wave and before finalization. It reports unresolved_ids, missing_finding_ids, redisposition_ids, blocked_ids, actionable_ids, stale_closure_ids, verification_errors, and next_action. Findings repeated after closure appear in redisposition_ids and require explicit reopening or a new inspected disposition after the latest report. Follow the unfinished work instead of ending with a partial review. Ordinary revision-enabled runs cannot finalize REVISION_REQUIRED. Review-only runs can deliver that status without student edits. Do not reset a STOPPED budget or edit a state file to force acceptance.

Contract: start from `../templates/contract.json`; required keys are research_question, claims (list of IDs), required_areas, required_checks (check IDs), acceptance_conditions, allowed_actions, limitations. Include all substantive scope fields described in workflow.md. Budgets/output policy are resolved by the helper. Keep all four specialist areas. Add the entrypoint and full coverage inventory.

Issues: `issues` accepts a JSON list matching `../templates/issue.json`. New issues are open and current. Add duplicates as linked records without losing history. To reopen or mark blocked, use `close` with the corresponding status and evidence; the name covers all audited issue-status changes. Do not reduce severity to conceal a major/critical issue.

## Dispatch and native evidence

Reserve FIRST. Then call the native tool, record its actual returned ID, and complete the reservation. The reservation label is NOT proof that a child exists. Save the actual native task prompt, tool return/ID and output in an external staging transcript file; do not manufacture a transcript or a successful tool call. A copied visible tool return is admissible provenance when the host does not expose a transcript export; label its source. Reviewer/auditor reports require an explicit `findings` list of objects with unique stable `id` and nonempty `problem`; use `[]` only when there are none. Every finding in every completed report must be represented in the issue ledger. Import them only after the active wave finishes, so coordinator writes do not invalidate another child guard. Preserve IDs when linking duplicates or rebutting mistaken comments.

Review report completion example:

```json
{
  "snapshot_hash": "SUPPLIED_HASH",
  "context_id": "ACTUAL_NATIVE_TASK_ID",
  "verdict": "pass",
  "coverage": ["Exact inspected locations"],
  "findings": [],
  "independent": true,
  "negotiation_exposed": false,
  "context_record": {
    "host": "codex",
    "context_id": "ACTUAL_NATIVE_TASK_ID",
    "separate_context": true,
    "negotiation_exposed": false,
    "mechanism": "Actual fresh native spawn mechanism and inspected inheritance",
    "transcript_source": "/absolute/staging/native-tool-record.txt"
  }
}
```

The helper imports provenance after checking write guards. Set host to `claude` there. Don't assert independence from a role prompt alone. Re-review reports can declare negotiation_exposed=true; initial review and fresh audit must not receive history. If isolation cannot be verified, set independent=false, record the limitation, and finalize BLOCKED_CAPABILITY rather than fabricate evidence.

Student completion uses the PRE-edit snapshot_hash and actual context_id, plus plan/responses/changed files from `../templates/response.json`; pass context_record with truthful exposure (student receives issues). Each response must contain `id`, nonempty `response`, `changed_files` (list), and `evidence` (list). The helper captures assigned issue IDs when reserving the student and requires exactly one response per ID. Missing or duplicate responses leave the reservation incomplete: recover or correct its report without replaying the edit. Student has no pass verdict or closure authority. Existing evidence is immutable. New student outputs go ONLY under `evidence/student-output/`. Capture the actual diff, not the student's assertion.

While children run, avoid editing protected run files. Place editor staging outside the run. Complete all children before importing issues/maps/checks or transitioning. Do not run a check against a manuscript macro or arbitrary script without inspecting its behavior. Scientific input files and contract remain immutable; guards detect deviations but are not an OS sandbox.

For a failed stage whose native task has demonstrably ended, use `abandon RESERVATION /absolute/staging/proof.json` to clear only that reservation for terminal delivery. Proof requires `host_tasks_inactive: true`, `inspected: true`, a concrete `reason`, `reservation_context` matching the stored reservation label, `native_context_id` from the actual host, and `artifacts` containing nonempty run-relative native inactivity evidence. Inspect the native completion/cancellation record first. The helper hashes the evidence; it does not authenticate a host from an assertion. Abandon preserves the full task, guards, evidence, error status and budgets; otherwise it marks INTERRUPTED. It permanently prevents PASS and new work for that run. Once every active task is reconciled, use `finalize ERROR` (or the existing truthful terminal status), then `release`. This is an error-delivery path, not ordinary `--resume` recovery. Never fabricate inactivity, discard an active child, or edit state to clear the guard.

## Closure and coverage

```json
{
  "author": "R1",
  "status": "resolved_verified",
  "reason": "Responsible reviewer inspected actual correction and evidence",
  "snapshot_hash": "CURRENT_HASH",
  "inspected": true,
  "artifacts": ["rounds/results/ACTUAL_RESULT.json"],
  "related_changes": ["manuscript.md"],
  "student_response": "Actual issue-linked response"
}
```

Only originating reviewer or editor can close. Close only after active tasks finish and the candidate matches its frozen snapshot. A resolved fix needs completed student provenance, a per-issue response, and changed source matching related_changes; a rebutted_verified issue needs actual evidence but no forced edit. All severities must be resolved_verified or rebutted_verified for acceptance; accepted_minor_limitation remains unresolved. Closed issues must be revalidated on a changed snapshot. Evidence paths are run-relative and must exist. Closure evidence must remain hash-identical.

`maps` replaces coverage/claim maps with:

```json
{
  "coverage": {
    "R1": {"snapshot_hash": "CURRENT_HASH", "locations": ["Exact locations"]},
    "R2": {"snapshot_hash": "CURRENT_HASH", "locations": ["Exact locations"]},
    "R3": {"snapshot_hash": "CURRENT_HASH", "locations": ["Exact locations"]},
    "R4": {"snapshot_hash": "CURRENT_HASH", "locations": ["Exact locations"]}
  },
  "claims": {
    "C1": {"snapshot_hash": "CURRENT_HASH", "status": "supported", "artifacts": ["rounds/results/ACTUAL_RESULT.json"], "location": "Exact claim location", "required_support": "What was required", "checks_performed": ["What was really inspected or executed"]}
  }
}
```

Use missing/unverified status for unavailable support; don't remove the claim. Actual citations distinguish metadata_found, text_inspected, supports_claim, mismatched and unverified in claim/report metadata.

## Safe checks and recovery

New-run defaults come from the real source package `skill/defaults.json`; never edit a run budget to extend a live run.

Check JSON: `{"id":"CHECK_ID","argv":["actual-executable","literal-argument"],"inspected":true,"safe_cpu_offline":true,"reason":"Specific check purpose and inspected command behavior","timeout":60}`. Helper runs in candidate cwd, captures stdout/stderr, records exit/time and hashes, enforces timeout. Use absolute output paths to disposable evidence scratch; don't let compilers change candidate manifests. For Tectonic use inspected source with `--untrusted --only-cached`, an evidence output directory, and no shell escape. Do not retry uncertain side effects. At most one transient retry; keep both records.

After interruption, inspect `RESUME.md`, state, hashes, active task IDs and host liveness. Reattach to live children. If the host confirms all old tasks inactive, `recover` accepts an external JSON record `{"host_tasks_inactive":true,"inspected":true,"reason":"Actual host/task liveness evidence"}` under the old recorded session token; it releases ownership without resetting counters. Then `init SOURCE --resume`. Use persisted pending output to complete the existing reservation; do not dispatch or revise again merely because a response was lost. If uncertain, retain INTERRUPTED with the checkpoint. Never use timeout alone to steal a live lease.

## Evidenced stopping

When an actual blocker prevents further permitted work, save a staging JSON with `status`, `reason`, `inspected: true`, run-relative `artifacts`, and `blocked_issue_ids`, then call `"$AMR" --run RUN --session TOKEN stop-proof /absolute/staging/stop.json`. Use the observed permission, capability, evidence, interruption, or error condition. Finish independent actionable issues before a blocked result. Artifact hashes preserve the supplied proof; an assertion is not independent authentication. Finalize the same truthful status. Budget and no-progress stops must reflect the helper's actual state, never a chosen label, and existing ERROR or stop statuses must not be relabeled.

New runs use feedback policy 2. An installation can retain a verified local legacy-runtime pin for older runs. If `pending` reports `legacy_run`, use its returned original helper/workflow for that run. Without a verified pin, the new helper rejects legacy runs before mutation; use the preserved original installation. New runs never use the legacy pin. Do not edit persisted policy or counters to migrate a live run.
