"""The executable launcher preserves arguments without shell evaluation."""

import json
import os
import shlex
import shutil
import subprocess
import sys
from pathlib import Path

LAUNCHER = Path(__file__).resolve().parents[1] / "skill/scripts/amr"


def test_launcher_help():
    assert LAUNCHER.is_file(), "executable launcher missing"
    result = subprocess.run(
        [str(LAUNCHER), "--help"],
        env=dict(os.environ, AMR_PYTHON=sys.executable),
        capture_output=True,
        text=True,
        timeout=30,
    )
    assert result.returncode == 0, result.stderr
    assert "init" in result.stdout


def test_launcher_keeps_literal_manuscript_argument(tmp_path):
    assert LAUNCHER.is_file(), "executable launcher missing"
    source = tmp_path / "α paper $(touch OWNED) `touch ALSO_OWNED`; .md"
    source.write_text("# Literal argument\nA clean synthetic manuscript.\n")
    result = subprocess.run(
        [str(LAUNCHER), "init", str(source)],
        env=dict(os.environ, AMR_PYTHON=sys.executable),
        cwd=tmp_path,
        capture_output=True,
        text=True,
        timeout=30,
    )
    assert result.returncode == 0, result.stderr
    record = json.loads(result.stdout)
    run = Path(record["run"])
    assert (run / "candidate" / source.name).read_bytes() == source.read_bytes()
    assert not (tmp_path / "OWNED").exists()
    assert not (tmp_path / "ALSO_OWNED").exists()


def portable_env(tmp_path):
    binary = tmp_path / "bin"
    binary.mkdir()
    (binary / "python3").symlink_to(sys.executable)
    dirname = shutil.which("dirname")
    assert dirname is not None
    (binary / "dirname").symlink_to(dirname)
    env = dict(os.environ, PATH=str(binary))
    env.pop("AMR_PYTHON", None)
    return env


def test_launcher_defaults_to_python3_without_conda(tmp_path):
    result = subprocess.run(
        [str(LAUNCHER), "--help"],
        env=portable_env(tmp_path),
        capture_output=True,
        text=True,
        timeout=30,
    )
    assert result.returncode == 0, result.stderr
    assert "init" in result.stdout


def test_launcher_override_is_one_literal_executable(tmp_path):
    env = portable_env(tmp_path)
    executable = tmp_path / "python $(touch OWNED) `touch ALSO_OWNED`; binary"
    executable.symlink_to(sys.executable)
    env["AMR_PYTHON"] = str(executable)
    (tmp_path / "bin/python3").unlink()
    result = subprocess.run(
        [str(LAUNCHER), "--help"],
        env=env,
        cwd=tmp_path,
        capture_output=True,
        text=True,
        timeout=30,
    )
    assert result.returncode == 0, result.stderr
    assert not (tmp_path / "OWNED").exists()
    assert not (tmp_path / "ALSO_OWNED").exists()


def test_launcher_rejects_old_python_before_loading_runtime(tmp_path):
    env = portable_env(tmp_path)
    executable = tmp_path / "old-python"
    executable.write_text(
        "#!/bin/sh\nexec "
        + shlex.quote(sys.executable)
        + " -c 'import sys; sys.version_info = (3, 9, 0); exec(sys.argv[1])' \"$2\"\n"
    )
    executable.chmod(0o755)
    env["AMR_PYTHON"] = str(executable)
    result = subprocess.run(
        [str(LAUNCHER), "--help"],
        env=env,
        capture_output=True,
        text=True,
        timeout=30,
    )
    assert result.returncode != 0
    assert "Python 3.10 or newer" in result.stderr
    assert "Traceback" not in result.stderr


def test_launcher_does_not_evaluate_interpreter_override(tmp_path):
    env = portable_env(tmp_path)
    env["AMR_PYTHON"] = "python3; touch OWNED"
    result = subprocess.run(
        [str(LAUNCHER), "--help"],
        env=env,
        cwd=tmp_path,
        capture_output=True,
        text=True,
        timeout=30,
    )
    assert result.returncode != 0
    assert not (tmp_path / "OWNED").exists()
