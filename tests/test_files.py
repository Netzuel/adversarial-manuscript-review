import importlib.util
from pathlib import Path
import pytest

spec = importlib.util.spec_from_file_location(
    "amr_files", Path(__file__).resolve().parents[1] / "skill/scripts/amr_files.py"
)
assert spec is not None and spec.loader is not None
f = importlib.util.module_from_spec(spec)
spec.loader.exec_module(f)


def test_markdown_unicode(tmp_path):
    src = tmp_path / "source"
    src.mkdir()
    p = src / "α space.md"
    p.write_text("![a](fig.png)\n[link](https://example.com)")
    (src / "fig.png").write_bytes(b"figure")
    result = f.ingest(p, tmp_path / "candidate")
    assert result["entrypoint"] == p.name
    assert len(result["files"]) == 2
    assert (
        f.manifest(tmp_path / "candidate")["fig.png"]
        == result["files"][str(src / "fig.png")]
    )


def test_tex_closure(tmp_path):
    p = tmp_path / "main.tex"
    p.write_text(
        r"\documentclass{article}\usepackage{local}\input{part}\bibliography{refs}\includegraphics{plot}"
    )
    for name in ["part.tex", "local.sty", "refs.bib", "plot.png"]:
        (tmp_path / name).write_text("data")
    (tmp_path / "unrelated").write_text("secret")
    result = f.ingest(p, tmp_path / "out")
    assert len(result["files"]) == 5
    assert not (tmp_path / "out/unrelated").exists()


@pytest.mark.parametrize("kind", ["missing", "escape", "symlink", "ambiguous"])
def test_bad_dependency(tmp_path, kind):
    src = tmp_path / "src"
    src.mkdir()
    p = src / "main.tex"
    if kind == "missing":
        p.write_text(r"\input{missing}")
    elif kind == "escape":
        p.write_text(r"\input{../outside}")
        (tmp_path / "outside.tex").write_text("x")
    elif kind == "symlink":
        p.write_text(r"\input{link}")
        (tmp_path / "outside.tex").write_text("x")
        (src / "link.tex").symlink_to(tmp_path / "outside.tex")
    else:
        p.write_text(r"\includegraphics{plot}")
        (src / "plot.png").write_text("a")
        (src / "plot.pdf").write_text("b")
    with pytest.raises(ValueError):
        f.ingest(p, tmp_path / "out")
    assert not (tmp_path / "out").exists()


def test_pdf_and_docx(tmp_path):
    p = tmp_path / "paper.pdf"
    p.write_bytes(b"%PDF")
    result = f.ingest(p, tmp_path / "out")
    assert result["blocked_input"] and result["limitations"]
    p = tmp_path / "paper.docx"
    p.write_bytes(b"zip")
    with pytest.raises(ValueError):
        f.ingest(p, tmp_path / "out2")


def test_promotion_conflict_and_backup(tmp_path):
    src = tmp_path / "src"
    src.mkdir()
    p = src / "paper.md"
    p.write_text("original")
    candidate = tmp_path / "candidate"
    record = f.ingest(p, candidate)
    (candidate / p.name).write_text("revised")
    p.write_text("concurrent")
    with pytest.raises(ValueError):
        f.promote(candidate, record, tmp_path / "backup", verified=True)
    assert p.read_text() == "concurrent"
    p.write_text("original")
    f.promote(candidate, record, tmp_path / "backup", verified=True)
    assert p.read_text() == "revised"
    assert (tmp_path / "backup" / p.name).read_text() == "original"


def test_local_bibliography_style(tmp_path):
    source = tmp_path / "paper.tex"
    source.write_text(r"\bibliographystyle{mine}")
    (tmp_path / "mine.bst").write_text("style")
    result = f.ingest(source, tmp_path / "candidate")
    assert str(tmp_path / "mine.bst") in result["files"]


def test_promotion_interruption_has_journal(tmp_path, monkeypatch):
    src = tmp_path / "src"
    src.mkdir()
    source = src / "paper.md"
    source.write_text("[appendix](appendix.md)")
    (src / "appendix.md").write_text("before")
    candidate = tmp_path / "candidate"
    record = f.ingest(source, candidate)
    (candidate / "appendix.md").write_text("after")
    original_replace = f.os.replace
    replacements = []

    def fail_second(source_path, destination):
        if Path(destination).parent == src:
            replacements.append(destination)
            if len(replacements) == 2:
                raise OSError("simulated interruption")
        return original_replace(source_path, destination)

    monkeypatch.setattr(f.os, "replace", fail_second)
    with pytest.raises(OSError):
        f.promote(candidate, record, tmp_path / "backup", verified=True)
    import json

    journal = json.loads((tmp_path / "backup/promotion.json").read_text())
    assert len(journal["changed"]) == 1
    assert journal["status"] == "in_progress"
    assert (tmp_path / "backup/appendix.md").read_text() == "before"


def test_system_bibliography_style_is_reported(tmp_path):
    source = tmp_path / "paper.tex"
    source.write_text(r"\bibliographystyle{plain}")
    result = f.ingest(source, tmp_path / "candidate")
    assert any("plain" in item for item in result["limitations"])


def test_source_parent_alias_preserves_scoped_dependencies(tmp_path):
    project = tmp_path / "real"
    project.mkdir()
    (project / "paper.md").write_text("![image](figure.png)")
    (project / "figure.png").write_bytes(b"figure")
    alias = tmp_path / "alias"
    alias.symlink_to(project, target_is_directory=True)
    result = f.ingest(alias / "paper.md", tmp_path / "candidate")
    assert result["source_root"] == str(project.resolve())
    assert set(result["files"]) == {
        str(project / "paper.md"),
        str(project / "figure.png"),
    }
