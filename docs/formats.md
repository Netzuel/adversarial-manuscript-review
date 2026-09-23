# Formats and required checks

| Input | Support and limitations |
|---|---|
| Markdown (`.md`) | Editable candidate; bounded parsing copies recognized relative links and image dependencies |
| TeX (`.tex`) | Editable candidate; bounded parsing follows supported static includes, bibliography, graphics, classes, and packages |
| PDF (`.pdf`) | Copied for review; no faithful editable revision or acceptance without verified corresponding editable source |
| DOCX | Rejected by the helper; a faithful preservation adapter is unavailable |

The source's parent directory is the dependency boundary. Dependencies cannot escape it. Candidate symlinks are rejected. Ingestion limits are 50 MiB per file, 200 MiB total, and 512 files. Missing required dependencies, ambiguous paths, and recognized dynamic TeX search paths fail ingestion. This parser is not a complete Markdown or TeX interpreter. Reviewers must record uninspected content and unresolved dependencies.

System TeX packages can be reported as uncopied and unverified; their absence from the copy is not proof that a build will work. Do not execute macros, project build scripts, or source code during ingestion. Inspect any command and its inputs before a bounded check.

For PDF input, the editor can inspect the supplied project for corresponding editable source. A matching basename is insufficient: establish correspondence from content and rendering, then initialize from the verified editable entry point. Initializing directly from a PDF sets an input blocker; do not clear it by editing state or invent a reconstructed source file.

Checks run locally with recorded commands, hashes, outputs, exit status, and elapsed time. No compiler or renderer is installed automatically. Use safe options, no shell escape or automatic downloads, and disposable output directories. Compilation does not constitute visual inspection. Required unavailable rendering or checks block acceptance; only genuinely irrelevant checks may be excluded with a reason in the frozen contract.
