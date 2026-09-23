# Troubleshooting

| Symptom | Action |
|---|---|
| Skill is not visible | Run `install.py diagnose` with the same `--host` and `--home`; confirm the linked clone remains in place, then follow the host's reload procedure |
| Installer reports an unowned collision | Inspect the existing installation; do not overwrite it or delete records to force ownership |
| Installer reports changed owned files | Compare the local agent file with its recorded/source version; preserve intentional edits and resolve the conflict before removal or upgrade |
| Launcher cannot find Python | Install/select Python 3.10+ and set `AMR_PYTHON` to one interpreter executable if needed |
| Native child tools are unavailable or denied | Retain useful supported review and report the capability or permission blocker; do not simulate a committee |
| Audit context separation is unknown | Record the actual host mechanism and limitation; do not claim verified independence or acceptance |
| Ingestion reports a missing or escaping dependency | Supply a self-contained supported source tree within the entry file's parent directory; do not bypass confinement |
| Required rendering or checks are unavailable | Record the missing capability and blocked result; a successful compile alone does not prove visual correctness |
| Resume reports an owned or ambiguous run | Inspect checkpoints and native task liveness using the recovery protocol; never steal a lease based only on elapsed time |
| A write guard fails | Preserve the error and evidence; reconcile native tasks before terminal delivery |

The installer can inspect paths but cannot prove that the host discovered roles. The record helper can validate structured evidence but cannot authenticate a native task from a supplied ID alone. Report these distinctions when filing a synthetic reproduction.

See [installation](installation.md), [formats](formats.md), and [recovery](recovery.md) for the detailed procedures.
