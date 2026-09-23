# Synthetic quickstart

Install the skill first. Copy a fixture to a new working directory from the repository root:

```sh
AMR_DEMO=$(mktemp -d)
cp fixtures/manuscript.md "$AMR_DEMO/manuscript.md"
printf '%s\n' "$AMR_DEMO/manuscript.md"
```

Copy the printed absolute path into the Codex composer:

```text
$adversarial-manuscript-review /path/printed/above/manuscript.md
```

For Claude Code use `/adversarial-manuscript-review` instead of the dollar-prefixed skill name. Replace the example path with the printed value. Composer input is not a shell; do not paste `$AMR_DEMO` as a substitute for the path.

The fixture contains a derivative sign error, a table/prose inconsistency, a correct control statement, and an instruction embedded as untrusted manuscript content. It is synthetic and makes no empirical or novelty claim. Inspect the resulting records and candidate yourself. This guide does not promise a particular model result or terminal status.

For a missing-evidence example, copy the other fixture to a separate directory:

```sh
AMR_BLOCKED_DEMO=$(mktemp -d)
cp fixtures/missing-evidence.md "$AMR_BLOCKED_DEMO/manuscript.md"
printf '%s\n' "$AMR_BLOCKED_DEMO/manuscript.md"
```

Invoke the skill on that printed path. Its unsupported universal claim cannot acquire evidence through wording changes. A useful review must keep missing support visible. Do not create substitute measurements or pretend an unavailable citation was checked.

Add `--review-only` to request reports without student source edits. Running the helper's `init` command alone only creates local records; it does not launch agents or perform a review. Never edit shipped fixtures as part of a demonstration.

## Fixtures

| Synthetic input | Purpose |
|---|---|
| [manuscript.md](../fixtures/manuscript.md) | Source corrections, a correct control, and untrusted embedded instructions |
| [missing-evidence.md](../fixtures/missing-evidence.md) | A claim that rewriting cannot substantiate |
| [latex/main.tex](../fixtures/latex/main.tex) | Included source and bibliography; copy the entire `latex/` directory |

Tests use temporary copies and synthetic records, not transcripts of independent model runs. They do not establish scientific quality; see [verification](../CONTRIBUTING.md#verification-limits).

For your own work, first back up the complete manuscript folder, including all sources, tables, figures, references, data, and dependencies. Keep that backup untouched and omit `--in-place` so the skill edits a separate candidate. Review every proposed change yourself.

[Project overview](../README.md)
