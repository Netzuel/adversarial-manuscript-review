# Contributing

Keep changes provider-neutral in `skill/` where possible. Put host-specific tool and role configuration in `adapters/`. Runtime code uses the Python standard library and targets Python 3.10+, macOS, and Linux. Native Windows is unsupported.

Use a development virtual environment from the repository root:

```sh
python3 -m venv .venv
. .venv/bin/activate
python -m pip install -r requirements-dev.txt
python -m pytest tests
python -m ruff check .
python -m ruff format --check .
python -m pyright
```

Run the repository's privacy check as documented in its script help before preparing a public change. Do not install into an actual host home merely to test layout: use `install.py --home` with a disposable directory. Do not overwrite another installed skill or agent.

Tests must use synthetic manuscripts and temporary directories. Preserve shipped fixtures. Add meaningful regression coverage for state transitions, ingestion boundaries, ownership, guards, or recovery changes. Do not fabricate native transcripts to claim real-agent validation. Synthetic provenance in tests exercises structure only.

Report exact commands and outcomes, including unperformed checks. Deterministic test success does not prove scientific quality, native context isolation, or host-version compatibility. Separate any authorized live-host experiment from the deterministic test suite and keep its private artifacts out of the repository.

Do not commit installation records, generated review runs, local configuration, unpublished manuscripts, personal identifiers, or transcripts. Document behavior changes and limitations in the changelog. Proposed acceptance-rule changes must preserve original-source protection, truthful blocked states, evidence-linked closure, bounded budgets, and the distinction between model review and executed checks.

Use concise pull-request descriptions: state the problem, resulting behavior, validation performed, and remaining limitations. Submission does not authorize publication of private evidence. Contributions are provided under the repository's MIT license.

## Public-content check and CI

After staging the intended files, inspect that exact index:

```sh
python scripts/check_public_content.py
```

Optionally supply `--deny-file /path/to/private-identifiers.txt` with one sensitive identifier per line. Keep that file outside the repository. The scanner reports rule names and locations without printing matching private values. It checks tracked index blobs, selected sensitive paths, common credential patterns, personal-home paths, and unsafe symlinks. It does not inspect all history or prove that arbitrary prose and identifiers are safe to publish. Review the staged diff manually as well.

The GitHub Actions workflow is prepared for manual `workflow_dispatch` runs on Ubuntu with Python 3.10 and 3.13. It is not automatically triggered by a push or pull request. It installs development dependencies and runs deterministic tests, lint, format, type, and public-content checks. The workflow definition is not evidence of a completed CI run; no Linux or remote CI execution result is claimed here. Dependency installation requires network access; tests must not require model calls or private data.
