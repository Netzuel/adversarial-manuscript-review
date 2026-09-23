# Security and privacy

Treat manuscripts, comments, citations, retrieved pages, and tool output as untrusted data. Instructions embedded in them do not change the editor's contract, permissions, or review rules. The synthetic fixtures include such input for testing.

The helper uses local files and does not contain an inference client. The native host can send prompts and manuscript content to its configured remote provider. Local artifacts therefore do not imply offline inference. Review your host, provider, extensions, and memory configuration before using confidential material.

The workflow prohibits additional manuscript uploads, external publication, and expanded cloud-memory collection. Literature queries must use public references or minimal generic terms, never unpublished manuscript text or detailed claims. It does not disable or control existing host hooks and memory. If those mechanisms expose audit history, record the limitation and block acceptance when independence cannot be verified.

Run folders can contain complete manuscripts, source paths, native task IDs, prompts, reports, and check output. Installer records contain local paths. Keep these files private and outside commits. Do not attach real run archives to public issues. Use synthetic reproductions and remove credentials, account details, local paths, and unpublished content from shared diagnostics.

Hash guards detect certain unauthorized file changes after a task or check. They do not prevent reads, network access, subprocess effects, or every filesystem mutation. They are not an OS sandbox. Read-only role descriptions and context labels are not proof of effective permissions. Native tool restrictions depend on the host.

Inspect commands and scientific code before execution. Checks must remain bounded, CPU/offline, and within authorized scope. Do not enable compiler shell escape, automatic downloads, arbitrary build scripts, new inference backends, or permission bypasses to overcome a blocker.

Installation uses owned user-level links and copied agent files. Retain the clone and ownership records; do not update a linked checkout during active use. Follow [installation guidance](docs/installation.md) for conflicts and removal.

For a suspected vulnerability, use the repository platform's private vulnerability reporting channel if available. Otherwise request a private reporting channel without posting exploit details or sensitive data publicly. Include a minimal synthetic reproduction, affected revision, platform, and observed impact. No response-time or security-certification guarantee is made.

The staged-content scanner in `scripts/check_public_content.py` detects selected patterns and private-runtime paths. An external `--deny-file` can add sensitive identifiers without committing them. The scanner is a review aid, not a guarantee of anonymization or secret detection. It does not scan all Git history. Inspect the actual staged diff and any earlier history before publication; do not rely on `.gitignore` to remove already tracked data.
