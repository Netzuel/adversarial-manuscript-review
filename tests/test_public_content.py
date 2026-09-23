"""Privacy checks inspect the exact staged bytes and redact findings."""

import importlib.util
import subprocess
from pathlib import Path

MODULE = Path(__file__).resolve().parents[1] / "scripts/check_public_content.py"
spec = importlib.util.spec_from_file_location("public_content", MODULE)
assert spec and spec.loader
checker = importlib.util.module_from_spec(spec)
spec.loader.exec_module(checker)


def test_personal_paths_and_tokens_are_redacted():
    private_path = "/" + "Users/" + "exampleperson/private"
    token = "gh" + "p_" + "X" * 36
    findings = checker.inspect_blob(
        "README.md", (private_path + "\n" + token).encode(), "100644", []
    )
    assert len(findings) == 2
    assert private_path not in str(findings)
    assert token not in str(findings)


def test_safe_placeholders_and_relative_symlinks():
    assert not checker.inspect_blob(
        "README.md", b"$HOME/.agents/skills\n/path/to/manuscript.md", "100644", []
    )
    assert not checker.inspect_blob(
        "adapters/codex-skill/scripts", b"../../skill/scripts", "120000", []
    )
    assert checker.inspect_blob("escape", b"../outside", "120000", [])
    assert checker.inspect_blob("absolute", b"/tmp/outside", "120000", [])


def test_private_records_and_external_denylist():
    assert checker.inspect_blob("installation-records/record.json", b"{}", "100644", [])
    assert checker.inspect_blob(
        "README.md", b"private-identifier", "100644", ["private-identifier"]
    )


def test_scans_index_instead_of_worktree(tmp_path):
    subprocess.run(["git", "init", "-q", str(tmp_path)], check=True)
    path = tmp_path / "README.md"
    path.write_text("/" + "home/" + "exampleperson/private")
    subprocess.run(["git", "-C", str(tmp_path), "add", "."], check=True)
    path.write_text("safe working tree")
    assert checker.scan_index(tmp_path, [])


def test_empty_index_is_not_a_pass(tmp_path):
    subprocess.run(["git", "init", "-q", str(tmp_path)], check=True)
    assert checker.scan_index(tmp_path, [])


def test_private_filenames_are_detected_and_redacted():
    path = "private-identifier.md"
    findings = checker.inspect_blob(path, b"safe", "100644", ["private-identifier"])
    assert findings
    assert path not in str(findings)
    token = "gh" + "p_" + "Y" * 36
    findings = checker.inspect_blob(token + ".md", b"safe", "100644", [])
    assert findings
    assert token not in str(findings)


def test_environment_variants_are_private():
    assert checker.inspect_blob(".env.production", b"safe", "100644", [])


def test_home_root_without_trailing_slash_is_private():
    value = "/" + "Users/" + "exampleperson"
    assert checker.inspect_blob("README.md", value.encode(), "100644", [])
