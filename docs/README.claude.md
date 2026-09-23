# Use with Claude Code

Run the review inside Claude Code using native subagents and your existing model configuration. This adapter targets Claude Code, not the Claude web chat interface.

## Install

From a stable clone of this repository:

```sh
python3 install.py install --host claude
python3 install.py diagnose --host claude
```

The installer links the skill into `$HOME/.claude/skills/adversarial-manuscript-review` and copies six role definitions into `$HOME/.claude/agents/`. It refuses unowned collisions and does not change host settings. A healthy diagnosis verifies installation paths, not live delegation.

## Invoke

Start a new Claude Code conversation. Enter this in the composer, replacing the example with your manuscript's absolute path:

```text
/adversarial-manuscript-review /path/to/manuscript.md
```

For reports without source edits:

```text
/adversarial-manuscript-review /path/to/manuscript.md --review-only
```

The editor uses native `amr-*` subagents. Reviewers and the final auditor have read-oriented role definitions; the student can edit candidate source. The editor runs inspected checks and records the results. These declarations do not replace the host's effective permission controls.

## Verify discovery and first use

Confirm the slash command is available in the new conversation. Use the [synthetic quickstart](quickstart.md), then inspect real subagent activity, source changes, and delivered records. If delegation is denied or unavailable, preserve that blocker rather than expanding permissions or simulating reviewers.

The [host adapter](../skill/references/hosts.md) specifies fresh-task and context checks. Existing hooks and memory can affect audit independence; unknown or exposed context prevents acceptance.

[Shared installation and removal](installation.md) · [Troubleshooting](troubleshooting.md) · [Documentation index](README.md)
