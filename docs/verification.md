# Check the workflow at the right level

A passing helper test, an installed skill, and a successful native review establish different things. Use the checks below together and report their limits.

## Deterministic checks

From the repository root, use the development setup in [CONTRIBUTING.md](../CONTRIBUTING.md), then run:

```sh
python -m pytest -q
python -m ruff check .
python -m ruff format --check .
python -m pyright
```

| Area | Evidence in the suite |
|---|---|
| Source handling | Temporary candidate copies, dependency boundaries, snapshots, and original protection |
| Review state | All-severity closure, report-to-ledger reconciliation, complete student responses, source-linked fixes, false-fix rejection, premature-stop rejection, and evidenced blockers |
| Bounded execution | Dispatch/check limits, interruption, ownership, and recovery rules |
| Installation | Both host layouts in a disposable home, collision refusal, relative asset links, and launcher execution |
| Public content | Staged-content scanning, private filename redaction, environment files, and selected credential/path patterns |

These tests do not call a model. Synthetic task records exercise validation; they do not prove native delegation or independent contexts. The source files under `tests/` define the exact coverage.

## Check an installed host

1. Install and diagnose the selected host as described in its [Codex](README.codex.md) or [Claude Code](README.claude.md) guide.
2. Start a new conversation and confirm skill discovery.
3. Invoke the [synthetic quickstart](quickstart.md) on a temporary copy.
4. Confirm real native task IDs and separate reviewer tasks. Inspect the student's source changes, preserved original, and recorded checks.
5. Confirm the final auditor is a new task with the required context restrictions. Record any unknown or exposed context.
6. Read the terminal status and unresolved issues. Missing support or capability must remain visible; a test is not improved by forcing `PASS_INTERNAL`.

A TeX run also needs the required compiler, dependencies, and visual checks. Do not download missing assets or weaken permissions solely to turn a blocker into a pass. The [live-artifact verifier](../verify_live.py) checks recorded synthetic decay-fixture runs; it is not a general manuscript verifier, and artifact checks alone cannot authenticate native model execution.

## Before sharing changes

Stage the intended files, run `python scripts/check_public_content.py`, and inspect the staged diff. An external `--deny-file` can add private identifiers. Keep installation records, real manuscripts, native transcripts, and local verification logs out of commits. The scanner is a bounded aid, not proof of universal secret detection.

The prepared GitHub Actions workflow runs only on manual dispatch. Its configuration alone is not a CI result. Report platform and host evidence separately; do not infer Linux or fresh-session compatibility from local unit tests.

[Documentation index](README.md) · [Security and privacy](../SECURITY.md)
