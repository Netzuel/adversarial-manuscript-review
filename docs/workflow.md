# Workflow and outputs

1. Ingest the manuscript and supported dependencies into a separate candidate. Freeze the contract, coverage requirements, and claims.
2. Dispatch four native specialist reviews against the same snapshot without sibling reports.
3. Triage evidence-backed issues. For revision requests, dispatch the student to make supported changes to the candidate.
4. Freeze the changed candidate, perform inspected bounded checks, and obtain current specialist assessments. Preserve rebuttals and dissent.
5. Request a new final auditor with only the current snapshot, contract, and admissible evidence.
6. Finalize through the helper and report the exact output entry point, status, limits, and unresolved issues.

The original is preserved by default. Explicit `--in-place` allows promotion only after `PASS_INTERNAL`, original-hash/conflict checks, and backups. Review-only mode does not dispatch the student or produce a revised accepted candidate.

## Limits

| Limit | Default |
|---|---:|
| Rounds, including initial review | 4 |
| Concurrent children | 3, or a lower host limit |
| Total child dispatches | 32 |
| Fresh audit attempts | 2 |
| Wall time at stage boundaries | 90 minutes |
| Each external check | 60 seconds |
| Checks per round | 300 seconds |
| Consecutive rounds without material progress | 2 |

`--max-rounds N` sets the requested round limit at initialization. Other defaults come from `skill/defaults.json`; they do not authorize changing budgets of an existing run. Active model calls are not forcibly terminated at the wall boundary. Workflow instructions allow one safe transient retry; uncertain side effects must not be repeated. No expensive experiments, full training, hardware jobs, or external publication are authorized.

## Terminal statuses

| Status | Meaning |
|---|---|
| `PASS_INTERNAL` | Configured internal acceptance gates passed for the supplied scope |
| `REVISION_REQUIRED` | Substantive work remains |
| `BLOCKED_EVIDENCE` | Indispensable scientific support is unavailable |
| `BLOCKED_INPUT` | Required source or faithful editable input is unavailable |
| `BLOCKED_PERMISSION` | Required access is denied |
| `BLOCKED_CAPABILITY` | A required host, independence, or check capability is unavailable |
| `STOPPED_BUDGET` | A run budget prevents further work |
| `STOPPED_NO_PROGRESS` | Repeated rounds lack material progress |
| `INTERRUPTED` | Work stopped with an incomplete checkpoint; inspect recovery eligibility |
| `ERROR` | A runtime or integrity failure prevents normal completion |

A terminal label must reflect observed evidence. No vote, prose rewrite, or budget reset can replace required support. `PASS_INTERNAL` is not journal acceptance or universal correctness.

## Files

The run root is `<source-stem>.review/<run-id>/`, beside the source. It holds `candidate/`, immutable `snapshots/`, `checkpoints/`, `rounds/`, `evidence/`, manifests, contract, issue/coverage/claim records, state, and recovery instructions. Treat it as sensitive manuscript data.

Finalization produces these files in `deliverables/`:

- `REVIEW_RESULT.md`: status and editable entry point, when available.
- `RESPONSE_TO_REVIEWERS.md`: recorded issue-linked responses.
- `CHANGES.md`: text differences reported by the helper; compare manifests for complete file-level changes, including binary or added/deleted assets.
- `UNRESOLVED.md`: remaining recorded issues and limitations.
- `REPRODUCIBILITY.md`: recorded executed checks, distinct from model review.
- `revised-project/`: candidate files when revision was requested and faithful editable output is available.

Blocked results can include supported candidate progress. They must retain their blocked status. Keep the full run directory: the summary documents do not replace native provenance, detailed evidence, and history.
