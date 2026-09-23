# Installation and removal

The installer uses Python 3.10+ and the standard library. Run it from a stable, writable clone on macOS or Linux. Do not use `sudo`. Native Windows is unsupported.

```sh
cd "$HOME/.local/share/adversarial-manuscript-review"
python3 install.py install --host all
python3 install.py diagnose --host all
```

`--host` accepts `codex`, `claude`, or `all` (default). `--home PATH` selects a different user-home directory. Use the same home and host selection for later operations. A disposable home can test installation layout without modifying the current user's host configuration:

```sh
AMR_TEST_HOME=$(mktemp -d)
python3 install.py install --host all --home "$AMR_TEST_HOME"
python3 install.py diagnose --host all --home "$AMR_TEST_HOME"
python3 install.py uninstall --host all --home "$AMR_TEST_HOME"
```

Installation links the skill into `.agents/skills/` for Codex or `.claude/skills/` for Claude Code. It copies role definitions into `.codex/agents/` or `.claude/agents/`. Wrapper asset links refer to the shared `skill/` tree. Records under the clone's `installation-records/` identify owned links and file hashes. Keep these records private: they contain local paths. Keep the clone and records until uninstall is complete.

The installer rejects unowned collisions and modified owned files. Inspect a conflict; do not overwrite another installation or delete its ownership record to bypass the check. `diagnose` checks installation records and paths. It does not test a live host or prove that the host loaded the skill. Follow your host's normal skill discovery/reload procedure.

## Python selection

The POSIX `skill/scripts/amr` launcher uses `python3` by default. `AMR_PYTHON` can name one executable, including a virtual-environment interpreter:

```sh
AMR_PYTHON="$HOME/.venvs/amr/bin/python" ./skill/scripts/amr --help
```

It cannot contain an interpreter plus arguments. Do not set it to a shell command such as `conda run ...` or `python3 -I`. The installer itself uses the interpreter with which you invoke `install.py`.

## Disable, uninstall, and upgrade

```sh
python3 install.py disable --host all
python3 install.py uninstall --host all
```

`disable` removes owned skill links but retains agent definitions. `install` restores the links. `uninstall` removes owned skill links and unchanged owned agent files. It preserves the source clone, installation records, and manuscript runs.

There is no safe live upgrade of an active installation. Skill links expose source changes immediately. Finish or safely interrupt runs, reconcile active child tasks, and uninstall before changing the clone revision. Then update the clone, reinstall, diagnose, and start a new host session. Do not update or move an active linked checkout. A changed copied agent file requires conflict resolution before uninstall can proceed.
