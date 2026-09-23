# Small manuscripts, inspectable problems

These fixtures are synthetic. They let you try the review workflow without sharing research or changing your own manuscript. Always copy a fixture to a separate working directory before invoking the skill; see the [quickstart](../docs/quickstart.md).

| Fixture | What to inspect |
|---|---|
| [manuscript.md](manuscript.md) | A derivative sign error, a mismatch between the table and prose, a correct control, and an embedded instruction that must remain untrusted data |
| [missing-evidence.md](missing-evidence.md) | An unsupported claim that cannot be established through rewriting |
| [latex/main.tex](latex/main.tex) | A small TeX project with an included section and bibliography; copy the entire `latex/` directory |

A useful revision corrects the actual source, preserves correct statements, and records why each issue changed status. A useful blocked review says what evidence is missing. Neither fixture prescribes a model verdict or proves scientific quality.

The automated tests use temporary copies and synthetic records. Their provenance fields test structural validation; they are not transcripts of independent model runs. See [verification](../docs/verification.md) for that distinction and for live-host checks.

[Back to the documentation](../docs/README.md)
