# Adversarial Manuscript Review

**Give your manuscript a review committee that follows through.**

One invocation starts specialist reviews, source revision, evidence checks, and a fresh final audit in **Codex** or **Claude Code**. You receive a revised working copy and a record of what changed, what was verified, and what still needs work. Your original stays intact by default.

> **Research support—not a substitute for peer review.** This skill aims to help improve research quality. Its AI agents simulate reviewer roles; their comments and proposed corrections are fallible feedback, not authoritative assessments. Use them to double-check caveats and areas that may need revision. Apply your own academic, scientific, and, where relevant, clinical judgment to every suggestion. The tool must never replace a real review process, a researcher's work, or professional responsibility.

> **Back up the complete manuscript folder before use.** Keep a separate, untouched copy of the main LaTeX file, included sources, tables, figures, bibliography, data, and other dependencies. Use the default working-copy mode and omit `--in-place`. Inspect all proposed changes before accepting them; the generated candidate is not a substitute for your own recoverable backup.

[Get started](#get-started) · [How it works](#how-it-works) · [Try an example](docs/quickstart.md) · [Guides](#guides-and-contributing) · [Contribute](CONTRIBUTING.md)

## Why this skill exists

A useful review should survive the revision. An equation corrected in a response must also be corrected in the source. A claim that needs data still needs data after a polished rewrite. A reviewer who objects should have their objection resolved with evidence or preserved in the final record.

This skill turns that process into a bounded workflow. Four specialists examine the same manuscript snapshot. The editor triages their findings. A student changes the candidate source. Verification checks the changes, and a new auditor examines the final snapshot without the earlier negotiation. The loop continues automatically for every unfinished comment, including minor corrections, suggestions, and new audit findings. Every item needs a verified fix or an evidence-based rebuttal; a partial revision is not completion.

Use it when you want a sustained technical review and revision of an editable manuscript. For a quick proofread, a normal editing request is usually enough.

## How it works

<p align="center">
  <picture>
    <source media="(prefers-color-scheme: dark)" srcset="docs/figures/review-workflow-dark.svg" />
    <source media="(prefers-color-scheme: light)" srcset="docs/figures/review-workflow.svg" />
    <img src="docs/figures/review-workflow.svg" width="640" alt="Vertical review workflow: manuscript, four specialist reviews, editor triage, student revision, evidence and source checks, fresh final audit, and delivery. Findings return to review within the remaining budget. Blockers or limits lead to delivery with a truthful status." />
  </picture>
</p>

*Revision mode shown; review-only skips student edits. Full-size: [light](docs/figures/review-workflow.svg) · [dark](docs/figures/review-workflow-dark.svg).*

The **host is the editor**. Reviewers, the student, and the final auditor are real native child-agent tasks. The local Python helper tracks files, evidence, and budgets; it does not call a model. Review-only mode skips student edits. Audit findings can require another bounded revision or a truthful stopped result.

| Who | What they examine |
|---|---|
| **R1 — Validity** | Mathematics, physics, and logical consistency, adapted to the discipline |
| **R2 — Methods** | Assumptions, controls, comparisons, and uncertainty |
| **R3 — Evidence** | Results, reproducibility, and provenance |
| **R4 — Contribution** | Literature support, scope, organization, and communication |
| **Student** | The source changes needed to address supported findings |
| **Fresh auditor** | Whether the final manuscript and admissible evidence satisfy the contract |

The workflow preserves dissent and checks proposed fixes against source artifacts. It keeps revising while permitted work remains; genuine evidence, permission, capability, or budget limits produce explicit non-acceptance results after independent supported work is complete. It never guarantees acceptance.

## Get started

You need **Python 3.10+**, a POSIX shell on macOS or Linux, and a host with native child-agent support. The runtime uses only the Python standard library. Native Windows is unsupported. Linux is a target platform; completed Linux validation is not claimed.

Clone into a stable location. Replace `OWNER` with the repository owner:

```sh
git clone https://github.com/OWNER/adversarial-manuscript-review.git "$HOME/.local/share/adversarial-manuscript-review"
cd "$HOME/.local/share/adversarial-manuscript-review"
```

Choose your client:

| Client | Install from the clone | Invoke in a new host conversation |
|---|---|---|
| [Codex guide](docs/README.codex.md) | `python3 install.py install --host codex` | `$adversarial-manuscript-review /path/to/manuscript.md` |
| [Claude Code guide](docs/README.claude.md) | `python3 install.py install --host claude` | `/adversarial-manuscript-review /path/to/manuscript.md` |

Use `--host all` to install both. Then run `python3 install.py diagnose --host all`, or select the single host you installed. Replace the example manuscript path with its actual absolute path. Invocation text belongs in the host composer; it is not a shell command.

Keep the clone in place: installed skills link to it. Finish active runs before updating or moving it. [Installation, upgrades, and removal →](docs/installation.md)

### Start with a small manuscript

The [synthetic quickstart](docs/quickstart.md) copies a fixture into a temporary working directory. It contains a derivative sign error, a table/prose mismatch, a correct control statement, and an embedded instruction that must be treated as untrusted text.

A second fixture lacks evidence for a broad claim. Its purpose is to exercise a blocker: the workflow must not invent measurements to make the review pass. [Explore the fixtures →](docs/quickstart.md#fixtures)

## What you receive

Each run creates `<stem>.review/<run-id>/` beside the source. Its `deliverables/` directory contains:

```text
deliverables/
├── REVIEW_RESULT.md          # Status and output entry point
├── RESPONSE_TO_REVIEWERS.md  # Issue-linked responses
├── CHANGES.md                # Recorded text differences
├── UNRESOLVED.md             # Remaining issues and limits
├── REPRODUCIBILITY.md        # Recorded executed checks
└── revised-project/          # Candidate source, when applicable
```

Keep the full run directory for detailed evidence, native task provenance, and history. Text differences alone do not describe every asset change. Review-only runs and inputs without faithful editable output do not produce a revised project.

`PASS_INTERNAL` means the configured internal gates passed for the supplied scope. It is not journal acceptance or proof of correctness. Blocked or stopped runs retain their status and can still deliver supported progress. [Statuses, budgets, and outputs →](docs/workflow.md)

## A few working principles

- **Protect the original.** Back up the entire project and use the default separate candidate. `--in-place` is an advanced opt-in; it promotes changes only after `PASS_INTERNAL`, conflict checks, and helper backups.
- **Make fixes inspectable.** A student assertion cannot close an issue. Each assigned comment needs a point-by-point response, actual student changes where required, and current verification evidence. No reported finding can disappear from the ledger.
- **Give the audit a fresh context.** Unknown or compromised context separation blocks acceptance; a role label alone does not prove independence.
- **Stop honestly.** Defaults allow four rounds, 32 dispatches, two audits, and 90 minutes checked at stage boundaries. Active model calls can exceed that wall limit.
- **Keep the host in control.** Use native delegation and existing model routing. Preserve permissions; do not add an inference backend.

Optional invocation controls: `--review-only`, `--resume`, `--max-rounds N`, and `--in-place`. Do not combine review-only with in-place promotion. Markdown and a bounded TeX dependency subset support revision. PDF-only input blocks faithful editable revision; DOCX revision is unsupported. [Formats](docs/formats.md) · [Recovery](docs/troubleshooting.md#interruption-and-recovery)

Native inference can use a remote provider. Local records do not imply offline inference, and hash guards are not an OS sandbox. Read [security and privacy](SECURITY.md) before supplying confidential work.

## Guides and contributing

- [Installation and removal](docs/installation.md), [Codex](docs/README.codex.md), and [Claude Code](docs/README.claude.md)
- [Quickstart and fixtures](docs/quickstart.md), [formats](docs/formats.md), and [workflow and outputs](docs/workflow.md)
- [Troubleshooting and recovery](docs/troubleshooting.md) and [verification limits](docs/verification.md)

`skill/` holds the shared instructions, templates, defaults, and local runtime. `adapters/` holds host entry points and agent definitions. `install.py` manages owned installation files; `tests/` and synthetic `fixtures/` check behavior. The detailed [editor protocol](skill/references/workflow.md), [record interface](skill/references/records.md), and [host adapter instructions](skill/references/hosts.md) support development; normal use needs only one skill invocation.

Contributions are welcome: a small synthetic failing case, a clearer review rule, or an accurate host-compatibility report can all help. Keep real manuscripts and private run histories out of issues and commits. See [CONTRIBUTING.md](CONTRIBUTING.md) and the [changelog](CHANGELOG.md).

Licensed under [MIT](LICENSE).
