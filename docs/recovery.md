# Interruption and recovery

The workflow persists state, budgets, task reservations, and evidence. It does not continue after the host exits. Resume requires a later host invocation and a compatible incomplete run.

Add `--resume` to the original skill invocation. The editor must inspect `RESUME.md`, state, original hashes, pending output, active task IDs, and host liveness first. Exactly one compatible incomplete run must be found. Multiple candidates or changed originals require inspection; do not pick one silently.

Reattach to live child tasks when the host permits it. Complete an existing reservation from verified pending output instead of repeating its edit or check. An elapsed timeout does not prove a task is dead and does not authorize taking its lease.

If all recorded native tasks have demonstrably ended, the helper's `recover` command accepts an inspected inactivity record with the old session token. It releases ownership without resetting budgets. Then resume through `init SOURCE --resume`. Never edit `state.json` or `owner.json` to bypass ownership. See [the record protocol](../skill/references/records.md) for exact payload requirements.

## Terminal abandonment

`abandon` is a separate error-delivery procedure. Use it only for a reservation whose native task demonstrably ended, with the required inactivity proof and existing evidence artifacts. The helper hashes that evidence; it does not authenticate a host from a boolean assertion.

Abandonment retains the task, guards, evidence, and budgets. It preserves an error status where present and otherwise marks interruption. It permanently prevents acceptance and new work in that run. Reconcile every active reservation, finalize the truthful terminal result, and release ownership. Do not use abandonment for ordinary resumable interruption.

Guard failures remain visible. Preserve invalid evidence and the error result; do not delete protected reports or fabricate inactivity to make a run pass.

[Documentation index](README.md) · [Project overview](../README.md)
