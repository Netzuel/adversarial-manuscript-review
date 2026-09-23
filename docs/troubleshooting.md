# Troubleshooting

| Symptom | Action |
|---|---|
| Skill is not visible | Run `install.py diagnose` with the same `--host` and `--home`; confirm the linked clone remains in place, then follow the host's reload procedure |
| Installer reports an unowned collision | Inspect the existing installation; do not overwrite it or delete records to force ownership |
| Installer reports changed owned files | Compare the local agent file with its recorded/source version; preserve intentional edits and resolve the conflict before removal or upgrade |
| Launcher cannot find Python | Install/select Python 3.10+ and set `AMR_PYTHON` to one interpreter executable if needed |
| Native child tools are unavailable or denied | Retain useful supported review and report the capability or permission blocker; do not simulate a committee |
| Audit context separation is unknown | Record the actual host mechanism and limitation; do not claim verified independence or acceptance |
| Ingestion reports a missing or escaping dependency | Supply a self-contained supported source tree within the entry file's parent directory; do not bypass confinement |
| Required rendering or checks are unavailable | Record the missing capability and blocked result; a successful compile alone does not prove visual correctness |
| Resume reports an owned or ambiguous run | Inspect checkpoints and native task liveness using the recovery protocol; never steal a lease based only on elapsed time |
| A write guard fails | Preserve the error and evidence; reconcile native tasks before terminal delivery |

The installer can inspect paths but cannot prove that the host discovered roles. The record helper can validate structured evidence but cannot authenticate a native task from a supplied ID alone. Report these distinctions when filing a synthetic reproduction.

See [installation](installation.md) and [formats](formats.md) for setup and input requirements.

## Interruption and recovery

The workflow persists state, budgets, task reservations, and evidence. It does not continue after the host exits. Resume requires a later host invocation and a compatible incomplete run.

Add `--resume` to the original skill invocation. The editor must inspect `RESUME.md`, state, original hashes, pending output, active task IDs, and host liveness first. Exactly one compatible incomplete run must be found. Multiple candidates or changed originals require inspection; do not pick one silently.

Reattach to live child tasks when the host permits it. Complete an existing reservation from verified pending output instead of repeating its edit or check. An elapsed timeout does not prove a task is dead and does not authorize taking its lease.

If all recorded native tasks have demonstrably ended, the helper's `recover` command accepts an inspected inactivity record with the old session token. It releases ownership without resetting budgets. Then resume through `init SOURCE --resume`. Never edit `state.json` or `owner.json` to bypass ownership. See [the record protocol](../skill/references/records.md) for exact payload requirements.

### Terminal abandonment

`abandon` is a separate error-delivery procedure. Use it only for a reservation whose native task demonstrably ended, with the required inactivity proof and existing evidence artifacts. The helper hashes that evidence; it does not authenticate a host from a boolean assertion.

Abandonment retains the task, guards, evidence, and budgets. It preserves an error status where present and otherwise marks interruption. It permanently prevents acceptance and new work in that run. Reconcile every active reservation, finalize the truthful terminal result, and release ownership. Do not use abandonment for ordinary resumable interruption.

Guard failures remain visible. Preserve invalid evidence and the error result; do not delete protected reports or fabricate inactivity to make a run pass.

New runs use the complete-feedback policy. If an updated installation identifies a legacy run, keep its original helper and workflow until that run finishes. Do not rewrite its policy, ledger, or budget to adopt a newer release.

[Project overview](../README.md)
