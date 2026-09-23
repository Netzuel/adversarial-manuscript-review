# Use with Codex

Run the review in your existing Codex environment, with its current model routing and permissions. Native child-agent tools are required for the committee.

## Install

From a stable clone of this repository:

```sh
python3 install.py install --host codex
python3 install.py diagnose --host codex
```

The installer links the skill into `$HOME/.agents/skills/adversarial-manuscript-review` and copies six role definitions into `$HOME/.codex/agents/`. It refuses unowned collisions. A healthy diagnosis verifies installation paths, not live delegation.

## Invoke

Start a new conversation so the host can discover the installed skill and roles. Enter this in the composer, replacing the example with your manuscript's absolute path:

```text
$adversarial-manuscript-review /path/to/manuscript.md
```

For reports without source edits:

```text
$adversarial-manuscript-review /path/to/manuscript.md --review-only
```

The editor should start real reviewer tasks, send supported source changes to the student, and request a fresh auditor when ready. If the host cannot provide separate task contexts or required permissions, expect a documented blocker. Never treat a single response with several reviewer headings as native delegation.

## Verify discovery and first use

Check that the skill is available in the new conversation. Then use the [synthetic quickstart](quickstart.md), confirm actual child tasks ran, and inspect the candidate and review record. Model quality and effective permissions need live evidence; the Python test suite cannot establish them.

Codex tool names and agent-selection parameters vary by version. The [host adapter](../skill/references/hosts.md) requires the editor to inspect available capabilities and record limitations without inventing parameters or overriding model settings.

[Shared installation and removal](installation.md) · [Troubleshooting](troubleshooting.md) · [Documentation index](README.md)
