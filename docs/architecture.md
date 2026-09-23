# Architecture and responsibility

The host is the editor and owns orchestration. The Python helper owns local records and structural gates. The helper has no inference client, model router, or background agent scheduler.

| Role | Responsibility |
|---|---|
| Editor | Freeze scope, reserve native tasks, triage findings, run inspected checks, verify closures, and deliver |
| R1 | Mathematical, physical, and logical validity, adapted to the discipline |
| R2 | Methods, controls, comparisons, uncertainty, and claim requirements |
| R3 | Evidence consistency, reproducibility, and provenance |
| R4 | Contribution, literature support, organization, and communication |
| Student | Sole writer of scientific candidate changes; return issue-linked responses |
| Fresh auditor | Inspect the final snapshot without prior verdicts or negotiation history |

The editor does not simulate reviewers or silently take over scientific edits. Children cannot delegate. The editor runs waves within the concurrent-child limit and records actual returned native task IDs. A reservation label is not evidence that an agent ran.

`skill/` contains the common workflow, role instructions, templates, defaults, and runtime. `adapters/` contains host entry points and agent definitions. `install.py` installs owned user-level links and agent files. `tests/` exercises deterministic behavior. Fixtures are synthetic.

Every review binds to an immutable snapshot. The contract freezes claims, required areas, checks, and acceptance conditions. Issue records retain evidence, provenance, status history, and closure reasons. Every report finding remains accountable in the ledger across rounds. A student reservation freezes its assigned issue IDs and cannot complete with omitted responses. A student assertion cannot close an issue. Acceptance requires verified closure at every severity, and current student provenance for claimed source fixes. Current coverage and artifact hashes must support acceptance.

Hash guards detect changes outside permitted paths and preserve invalidation evidence. Native permissions and context separation depend on the host. A read-only role description does not establish OS isolation. A fresh-context declaration alone does not prove independence. Unknown or exposed audit context blocks acceptance.

The detailed editor protocol is in [the skill workflow](../skill/references/workflow.md), [record interface](../skill/references/records.md), and [host adapters](../skill/references/hosts.md).

[Documentation index](README.md) · [Project overview](../README.md)
