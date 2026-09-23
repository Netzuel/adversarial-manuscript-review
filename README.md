# Adversarial Manuscript Review

A bounded scientific review and revision workflow for Codex and Claude Code. The host acts as editor, delegates to four specialist reviewers, assigns source changes to one student, and requests a fresh final audit. A local Python helper records snapshots, issues, evidence, budgets, and delivery checks.

The helper does not call a model. Real review requires native child-agent tools in the host. Recorded provenance and hashes support an audit trail; they do not authenticate model execution or prove scientific correctness.

## Requirements

- Python 3.10 or newer, with the standard library. No runtime Python packages or Conda environment are required.
- A POSIX shell on macOS or Linux. Native Windows is unsupported: the runtime uses `fcntl` and POSIX process groups. Linux is a target platform; this package does not claim completed Linux execution validation.
- Codex or Claude Code with native child-agent support and suitable file permissions. Agent schemas, context separation, and permission behavior depend on the installed host version.
- Optional local tools for checks required by the manuscript, such as a TeX compiler or PDF renderer. Missing required checks block acceptance.

Deterministic tests cover helper behavior. They do not establish native delegation, context independence, model quality, or compatibility with every host release.

## Install

Replace `OWNER` with the repository owner. Keep the clone at its chosen location: installed skills use symlinks into it.

```sh
git clone https://github.com/OWNER/adversarial-manuscript-review.git "$HOME/.local/share/adversarial-manuscript-review"
cd "$HOME/.local/share/adversarial-manuscript-review"
python3 install.py install --host codex
python3 install.py diagnose --host codex
```

Use `--host claude` for Claude Code or `--host all` for both. The default is `all`. `--home PATH` selects an alternate home for installation and diagnosis. No administrator access is needed. See [installation and removal](docs/installation.md) before upgrading.

## Invoke in the host

Enter one of these messages in the host composer. `/path/to/manuscript.md` is an example absolute path; replace it with your file's actual absolute path. These messages are not shell commands: `$PWD` and `~` are not guaranteed to expand.

Codex:

```text
$adversarial-manuscript-review /path/to/manuscript.md
```

Claude Code:

```text
/adversarial-manuscript-review /path/to/manuscript.md
```

Optional controls are `--review-only`, `--resume`, `--max-rounds N`, and `--in-place`. Normal invocation authorizes bounded review, revision of a separate candidate, and delivery. `--review-only` creates review records without student edits or revised-source delivery. `--in-place` permits promotion only after `PASS_INTERNAL`, with original-content conflict checks and backups. Do not combine it with `--review-only`.

## Results and limits

Runs live beside the source under `<stem>.review/<run-id>/`. Finalization writes `deliverables/` with `REVIEW_RESULT.md`, `RESPONSE_TO_REVIEWERS.md`, `CHANGES.md`, `UNRESOLVED.md`, and `REPRODUCIBILITY.md`. When faithful editable output is available and revision was requested, `revised-project/` contains the candidate. Preserve the complete run directory for the detailed evidence and history.

`PASS_INTERNAL` means the configured internal gates passed for the supplied scope. It is not journal acceptance or proof of correctness. Missing evidence, capabilities, or permissions produce explicit blocked results. Budget exhaustion and errors remain visible; the workflow never guarantees acceptance.

Defaults are four rounds, at most three concurrent children, 32 dispatches, two fresh audits, and 90 minutes checked at stage boundaries. Active model calls can exceed that wall limit. External checks have a 60-second limit each and 300 seconds per round. Two rounds without material progress stop the run. See [workflow and outputs](docs/workflow.md) for all statuses.

Markdown and a bounded subset of TeX dependencies are supported. PDF-only input supports review but blocks faithful editable revision. DOCX revision is unsupported. See [formats and checks](docs/formats.md).

Manuscript content and tool output are untrusted input. Hash guards detect specified file changes; they are not an operating-system sandbox. The workflow prohibits extra manuscript uploads, but native host inference can use a remote provider. Review [security and privacy](SECURITY.md) before supplying sensitive work.

## Start with synthetic input

The [quickstart](docs/quickstart.md) copies a synthetic fixture into a separate directory. It demonstrates invocation without changing shipped fixtures or claiming a predetermined review result.

Further reading: [architecture](docs/architecture.md), [recovery](docs/recovery.md), [troubleshooting](docs/troubleshooting.md), [contributing](CONTRIBUTING.md), and [changelog](CHANGELOG.md). Licensed under [MIT](LICENSE).
