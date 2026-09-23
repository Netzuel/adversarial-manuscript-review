"""Bounded manuscript dependency ingestion and conflict-checked promotion."""

import hashlib
import json
import os
import tempfile
import re
import shutil
from pathlib import Path
from urllib.parse import unquote, urlsplit

MAX_FILE = 50 * 1024 * 1024
MAX_TOTAL = 200 * 1024 * 1024


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def confined(path: Path, root: Path) -> Path:
    resolved = path.resolve()
    if not resolved.is_relative_to(root.resolve()):
        raise ValueError(f"Dependency escapes project: {path}")
    return resolved


def manifest(root: Path) -> dict:
    root = Path(root)
    result = {}
    for path in sorted(root.rglob("*")):
        confined(path, root)
        if path.is_symlink():
            raise ValueError(f"Symlink in candidate: {path}")
        if path.is_file():
            result[path.relative_to(root).as_posix()] = digest(path)
    return result


def ingest(source: Path, destination: Path) -> dict:
    source = Path(source).absolute()
    root = source.parent.resolve()
    source = root / source.name
    confined(source, root)
    if not source.is_file():
        raise ValueError(f"Missing manuscript: {source}")
    if source.suffix.lower() not in {".md", ".tex", ".pdf"}:
        raise ValueError(
            "Unsupported editable format; DOCX preservation adapter unavailable"
        )
    destination = Path(destination)
    if destination.exists() or destination.is_symlink():
        raise ValueError("Destination must not exist")
    pending = [source]
    files = {}
    total = 0
    limitations = []

    def dependency(name, extensions=("",), optional=False):
        if not name or any(char in name for char in ("\\", "#", "{", "}")):
            raise ValueError(f"Dynamic dependency cannot be resolved safely: {name}")
        path = root / name
        confined(path, root)
        candidates = (
            [path] if path.suffix else [Path(str(path) + ext) for ext in extensions]
        )
        found = [p for p in candidates if p.is_file()]
        if len(found) > 1:
            raise ValueError(f"Ambiguous dependency: {name}")
        if not found:
            if optional:
                limitations.append(
                    f"System TeX dependency not copied or verified: {name}"
                )
                return
            raise ValueError(f"Missing dependency: {name}")
        confined(found[0], root)
        pending.append(found[0])

    while pending:
        path = pending.pop()
        confined(path, root)
        relative = path.relative_to(root)
        if str(path) in files:
            continue
        size = path.stat().st_size
        total += size
        if size > MAX_FILE or total > MAX_TOTAL or len(files) >= 512:
            raise ValueError("Dependency copy size/count budget exceeded")
        files[str(path)] = digest(path)
        suffix = path.suffix.lower()
        if suffix in {".tex", ".sty", ".cls"}:
            content = re.sub(r"(?<!\\)%[^\n]*", "", path.read_text())
            if re.search(r"\\(?:graphicspath|import|subimport|input@path)\b", content):
                raise ValueError(
                    "Dynamic TeX search paths require explicit dependency resolution"
                )
            for command, names in re.findall(
                r"\\(input|include|bibliographystyle|bibliography|addbibresource|includegraphics|documentclass|usepackage|RequirePackage|LoadClass)\*?(?:\s*\[[^\]]*\])?\s*\{([^}]+)\}",
                content,
            ):
                extensions = {
                    "input": ("", ".tex"),
                    "include": ("", ".tex"),
                    "bibliography": (".bib",),
                    "bibliographystyle": (".bst",),
                    "addbibresource": (".bib",),
                    "includegraphics": (".pdf", ".png", ".jpg", ".jpeg", ".eps"),
                    "documentclass": (".cls",),
                    "LoadClass": (".cls",),
                    "usepackage": (".sty",),
                    "RequirePackage": (".sty",),
                }[command]
                for name in names.split(","):
                    dependency(
                        name.strip(),
                        extensions,
                        command
                        in {
                            "documentclass",
                            "LoadClass",
                            "usepackage",
                            "RequirePackage",
                            "bibliographystyle",
                        },
                    )
        elif suffix == ".md":
            content = path.read_text()
            links = re.findall(
                r"!?\[[^\]]*\]\(\s*(<[^>]+>|[^\s)]+)(?:\s+[^)]*)?\)", content
            )
            links += re.findall(r"^\s*\[[^\]]+\]:\s*(\S+)", content, re.M)
            for link in links:
                url = urlsplit(link.strip("<>"))
                if not url.scheme and not url.netloc and url.path:
                    dependency((relative.parent / unquote(url.path)).as_posix())
    destination.mkdir(parents=True)
    try:
        for original, expected in files.items():
            path = Path(original)
            confined(path, root)
            if digest(path) != expected:
                raise ValueError("Original changed during ingestion")
            target = destination / path.relative_to(root)
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(path, target)
            if digest(target) != expected:
                raise ValueError("Original changed during copy")
    except BaseException:
        shutil.rmtree(destination)
        raise
    blocked = source.suffix.lower() == ".pdf"
    if blocked:
        limitations.append(
            "BLOCKED_INPUT: PDF copied for review; editable-source correspondence is not established; faithful full revision is blocked"
        )
    return {
        "entrypoint": source.name,
        "source_root": str(root),
        "files": files,
        "limitations": limitations,
        "blocked_input": blocked,
    }


def promote(
    candidate: Path, input_manifest: dict, backup_dir: Path, *, verified=False
) -> dict:
    if not verified or input_manifest.get("blocked_input"):
        raise ValueError("Promotion requires verified editable final result")
    root = Path(input_manifest["source_root"])
    candidate = Path(candidate)
    backup_dir = Path(backup_dir)
    if backup_dir.exists():
        raise ValueError("Backup must not exist")
    actual = manifest(candidate)
    originals = input_manifest["files"]
    relative_files = {Path(p).relative_to(root).as_posix(): p for p in originals}
    if set(actual) != set(relative_files):
        raise ValueError("Promotion cannot add or remove source files automatically")
    for original, expected in originals.items():
        path = Path(original)
        confined(path, root)
        if path.is_symlink() or not path.is_file() or digest(path) != expected:
            raise ValueError(f"Concurrent original change: {path}")
    backup_dir.mkdir(parents=True)
    for relative, original in relative_files.items():
        backup = backup_dir / relative
        backup.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(original, backup)
    journal = {
        "status": "in_progress",
        "changed": [],
        "pending": None,
        "backup": str(backup_dir),
        "manifest": actual,
    }
    journal_path = backup_dir / "promotion.json"

    def save_journal():
        temporary = journal_path.with_suffix(".tmp")
        with temporary.open("w") as stream:
            json.dump(journal, stream, indent=2)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, journal_path)

    save_journal()
    for relative, original in relative_files.items():
        path = Path(original)
        confined(path, root)
        if path.is_symlink() or digest(path) != originals[original]:
            raise ValueError(
                f"Concurrent change during promotion; backups at {backup_dir}"
            )
        data = (candidate / relative).read_bytes()
        if hashlib.sha256(data).hexdigest() != actual[relative]:
            raise ValueError("Candidate changed during promotion")
        journal["pending"] = str(path)
        save_journal()
        descriptor, name = tempfile.mkstemp(prefix=".amr-promote-", dir=path.parent)
        staged = Path(name)
        try:
            with os.fdopen(descriptor, "wb") as stream:
                stream.write(data)
                stream.flush()
                os.fsync(stream.fileno())
            staged.chmod(path.stat().st_mode)
            confined(path, root)
            if path.is_symlink() or digest(path) != originals[original]:
                raise ValueError("Concurrent source change during promotion")
            os.replace(staged, path)
            journal["changed"].append(str(path))
            journal["pending"] = None
            save_journal()
        finally:
            staged.unlink(missing_ok=True)
    journal["status"] = "complete"
    save_journal()
    return journal
