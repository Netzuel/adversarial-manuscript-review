# Native host adapters

## Codex

Use the native collaboration/spawn-agent tool exposed by this session. Select installed `amr-review-math`, `amr-review-methods`, `amr-review-evidence`, `amr-review-communication`, `amr-student`, and `amr-final-auditor` when agent selection is available. If the tool lacks an agent-type parameter, give a fresh general child the corresponding role from roles.md; record this procedural tool restriction accurately. Never invent unsupported tool parameters.

Use `fork_turns="none"` or `fork_context=false` when those parameters exist. Do not fork negotiation history into initial reviewers or the final auditor. Omit model and effort overrides. If separate contexts cannot be verified, continue useful supported work, mark independence unverified, and block PASS_INTERNAL. Runtime sandbox overrides may supersede read-only agent defaults: record effective tools/permissions, and use the hash guards. Read-only declarations alone are not security evidence.

Native tools may cap active children below three. Run waves or one at a time, close completed children if supported, and preserve task IDs and results. The helper reserves each dispatch before the native call; completion links the real host task ID. No child delegation. Use a new task for the final auditor, not a resumed initial reviewer.

## Claude Code

Use the native Agent tool with installed `amr-*` subagent types. Do not use conversation forks: regular subagent task contexts must receive only the delegation prompt and allowed files. Preserve the tool's default current model settings. Reviewers/final auditor have Read, Grep, Glob only; student has Read, Grep, Glob, Edit, Write. The editor runs inspected safe checks and persists reports. No child may delegate.

If Agent uses a different name/schema in this installed version, inspect its exposed tool schema; do not invent arguments. Record real agent IDs from returns or session artifacts. A tool denial is a permission/capability blocker, never a reason to add allowedTools, bypass flags, API keys, or new backends.

## Context and privacy check, both hosts

Before the fresh audit, record the installed host version, chosen fresh-task mechanism, whether the prompt contains negotiation history, and whether existing memory/hooks can expose the current run's decisions. Inspect available task metadata. Ask the auditor to disclose any exposure; don't send the issue history as part of this question. Global standing instructions are not automatically negotiation history. Do not disable memory or hooks. If exposure is known, label compromised; if the mechanism or injected context cannot be verified, label unverified. Only verified separate context with no known history exposure meets acceptance.

When host tool controls cannot confine reads to named files, isolation is procedural. Report this access limitation separately from verified absence of inherited conversation history; never claim cryptographic blindness. Prevent the auditor from retrieving neighboring reports by giving exact allowed paths and prohibiting history/memory queries about this run. An unexpected report access invalidates the audit.
