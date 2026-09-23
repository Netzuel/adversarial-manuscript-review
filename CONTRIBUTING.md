# Contributing and verification

Keep common instructions and runtime code in `skill/`, host-specific configuration in `adapters/`, and tests in `tests/`. The runtime uses the Python standard library and targets Python 3.10+, macOS, and Linux; native Windows is unsupported. Contributions use the [MIT license](LICENSE).

## Development checks

From the repository root:

```sh
python3 -m venv .venv
. .venv/bin/activate
python -m pip install -r requirements-dev.txt
python -m pytest -q
python -m ruff check .
python -m ruff format --check .
python -m pyright
```

Use synthetic manuscripts and temporary directories. Preserve shipped fixtures. Add regression coverage for meaningful changes to state transitions, ingestion, ownership, guards, or recovery. Preserve original-source protection, bounded budgets, evidence-linked closure, and truthful blocked states.

Test installation in a disposable home, not an actual client configuration:

```sh
AMR_TEST_HOME=$(mktemp -d)
python install.py install --host all --home "$AMR_TEST_HOME"
python install.py diagnose --host all --home "$AMR_TEST_HOME"
python install.py uninstall --host all --home "$AMR_TEST_HOME"
```

## Verification limits

Tests cover source/dependency handling, all-severity closure, complete student responses, false fixes, repeated findings, stopping evidence, budgets, recovery, and both installation layouts. Synthetic provenance records test structure; they are not model transcripts or proof of scientific quality. The files in `tests/` define exact coverage.

For live-host validation, start a new conversation after installation and invoke a copied [fixture](docs/quickstart.md). Inspect real native task IDs and separate reviewer contexts, actual student edits, preserved originals, executed checks, and a new final auditor. Record unknown or exposed context and genuine blockers. A TeX run also requires appropriate rendering and visual inspection. Do not weaken permissions or fabricate evidence to obtain `PASS_INTERNAL`.

`verify_live.py` checks recorded synthetic decay-fixture artifacts; it is not a general manuscript verifier or proof of native execution. Report exact commands, results, platform, and unperformed checks separately. The manual GitHub Actions workflow installs dependencies and runs deterministic checks on Ubuntu/Python 3.10 and 3.13; its presence alone is not a completed CI or Linux validation result.

## Before sharing

Stage intended files, then run:

```sh
python scripts/check_public_content.py
```

An external `--deny-file /path/to/private-identifiers.txt` adds private identifiers. Keep it outside the repository. The scanner checks index blobs, selected sensitive paths, credential patterns, and unsafe symlinks without printing matched secrets. It does not scan all history or guarantee anonymization; inspect the staged diff and earlier commits as well.

Never commit real manuscripts, run archives, transcripts, installation records, local configuration, credentials, or personal identifiers. Use synthetic issue reports. Document behavior changes in [CHANGELOG.md](CHANGELOG.md); follow [SECURITY.md](SECURITY.md) for private vulnerability reports.
