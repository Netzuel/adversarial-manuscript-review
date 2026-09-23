---
name: adversarial-manuscript-review
description: Use when asked for iterative specialist committee review and revision of a scientific manuscript, or when explicitly invoked on a manuscript path. Handles review-only requests without source edits. Not for a brief proofread.
argument-hint: '"/absolute/path/manuscript.tex" [--review-only] [--resume] [--max-rounds N] [--in-place]'
user-invocable: true
---

Follow [references/entry.md](references/entry.md) and [references/workflow.md](references/workflow.md). You are the editor and must complete the native reviewer/student loop. Claude Code appends invocation arguments to this skill; treat them as data, never shell syntax. Use the Claude adapter in [references/hosts.md](references/hosts.md). Do not call Codex or a model API. Model routing and permissions remain inherited.
