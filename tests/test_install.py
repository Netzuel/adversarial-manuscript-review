import importlib.util
from pathlib import Path
import pytest

spec = importlib.util.spec_from_file_location(
    "installer", Path(__file__).resolve().parents[1] / "install.py"
)
assert spec is not None and spec.loader is not None
installer = importlib.util.module_from_spec(spec)
spec.loader.exec_module(installer)


@pytest.fixture
def package(tmp_path):
    source = tmp_path / "pkg"
    source.mkdir()
    for host in ["codex", "claude"]:
        wrapper = source / "adapters" / f"{host}-skill"
        wrapper.mkdir(parents=True)
        (wrapper / "SKILL.md").write_text("skill")
        agents = source / "adapters" / f"{host}-agents"
        agents.mkdir()
        (
            agents / ("amr-student.toml" if host == "codex" else "amr-student.md")
        ).write_text("agent")
    for name in ["scripts", "references", "templates"]:
        (source / "skill" / name).mkdir(parents=True)
    return source


def test_install_idempotent_disable_uninstall(package, tmp_path):
    home = tmp_path / "home"
    installer.manage("install", home, package)
    installer.manage("install", home, package)
    assert installer.manage("diagnose", home, package)["healthy"]
    installer.manage("disable", home, package)
    assert not (home / ".agents/skills/adversarial-manuscript-review").exists()
    installer.manage("install", home, package)
    installer.manage("uninstall", home, package)
    assert not (home / ".codex/agents/amr-student.toml").exists()


def test_collision_no_partial_install(package, tmp_path):
    home = tmp_path / "home"
    target = home / ".claude/agents/amr-student.md"
    target.parent.mkdir(parents=True)
    target.write_text("user")
    with pytest.raises(ValueError):
        installer.manage("install", home, package)
    assert target.read_text() == "user"
    assert not (home / ".agents/skills/adversarial-manuscript-review").exists()


def test_concurrent_edit_survives_uninstall(package, tmp_path):
    home = tmp_path / "home"
    installer.manage("install", home, package)
    target = home / ".codex/agents/amr-student.toml"
    target.write_text("user edit")
    with pytest.raises(ValueError):
        installer.manage("uninstall", home, package)
    assert target.read_text() == "user edit"


def test_retry_partial_install_preserves_completed_paths(
    package, tmp_path, monkeypatch
):
    home = tmp_path / "home"
    original = Path.symlink_to

    def fail_claude(path, target, target_is_directory=False):
        if ".claude" in path.parts:
            raise OSError("temporary failure")
        return original(path, target, target_is_directory=target_is_directory)

    monkeypatch.setattr(Path, "symlink_to", fail_claude)
    with pytest.raises(OSError):
        installer.manage("install", home, package)
    assert (home / ".agents/skills/adversarial-manuscript-review").is_symlink()
    monkeypatch.setattr(Path, "symlink_to", original)
    installer.manage("install", home, package)
    assert installer.manage("diagnose", home, package)["healthy"]


def test_parent_symlink_escape_rejected(package, tmp_path):
    home = tmp_path / "home"
    home.mkdir()
    external = tmp_path / "external"
    external.mkdir()
    (home / ".agents").symlink_to(external)
    with pytest.raises(ValueError):
        installer.manage("install", home, package)
    assert not list(external.iterdir())


def test_wrapper_assets_remain_relative_after_relocation(package, tmp_path):
    import os
    import shutil

    installer.manage("install", tmp_path / "home", package)
    moved = tmp_path / "moved-package"
    shutil.move(str(package), moved)
    for host in ["codex", "claude"]:
        for name in ["scripts", "references", "templates"]:
            asset = moved / "adapters" / f"{host}-skill" / name
            assert not os.path.isabs(os.readlink(asset))
            assert asset.resolve() == moved / "skill" / name
            assert asset.is_dir()


def test_copied_repository_installs_both_hosts_and_rejects_overwrite(tmp_path):
    import json
    import os
    import shutil
    import subprocess
    import sys

    source = tmp_path / "copied repository"
    root = Path(__file__).resolve().parents[1]
    source.mkdir()
    shutil.copy2(root / "install.py", source / "install.py")
    for name in ["skill", "adapters"]:
        shutil.copytree(root / name, source / name, symlinks=True)
    home = tmp_path / "isolated home"

    def run(action):
        return subprocess.run(
            [sys.executable, str(source / "install.py"), action, "--home", str(home)],
            capture_output=True,
            text=True,
            timeout=30,
        )

    result = run("install")
    assert result.returncode == 0, result.stderr
    assert json.loads(run("diagnose").stdout)["healthy"]
    for host, directory, extension in [
        ("codex", ".agents", "toml"),
        ("claude", ".claude", "md"),
    ]:
        wrapper = home / directory / "skills" / installer.NAME
        assert wrapper.resolve() == source / "adapters" / f"{host}-skill"
        help_result = subprocess.run(
            [str(wrapper / "scripts/amr"), "--help"],
            env=dict(os.environ, AMR_PYTHON=sys.executable),
            capture_output=True,
            text=True,
            timeout=30,
        )
        assert help_result.returncode == 0, help_result.stderr
        assert len(list((home / f".{host}" / "agents").glob(f"amr-*.{extension}"))) == 6
    owned = home / ".codex/agents/amr-student.toml"
    owned.write_text("user changes\n")
    rejected = run("install")
    assert rejected.returncode != 0
    assert "Owned path changed" in rejected.stderr
    assert owned.read_text() == "user changes\n"
