#!/usr/bin/env python3
"""Inspect staged content; report rule names, never matching private values."""

import argparse
import posixpath
import re
import subprocess
from pathlib import Path

RULES = {
    "personal-home-path": re.compile(
        r"/(?:Users|home)/[A-Za-z0-9_.-]+(?:/|\b)|[A-Za-z]:\\Users\\[^\\\s]+\\"
    ),
    "access-token": re.compile(
        r"\b(?:gh[pousr]_[A-Za-z0-9]{20,}|github_pat_[A-Za-z0-9_]{30,}|sk-[A-Za-z0-9_-]{20,}|AKIA[A-Z0-9]{16})\b"
    ),
    "private-key": re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----"),
    "url-credentials": re.compile(r"https?://[^\s/:@]+:[^\s/@]+@"),
}
PRIVATE_DIRS = {"installation-records", "audit", "live", ".venv", "__pycache__"}


def private_name(path: str, denied: list[str]) -> bool:
    return any(pattern.search(path) for pattern in RULES.values()) or any(
        value.casefold() in path.casefold() for value in denied if value
    )


def display_name(path: str, denied: list[str]) -> str:
    return "<redacted-path>" if private_name(path, denied) else repr(path)


def inspect_blob(path: str, data: bytes, mode: str, denied: list[str]) -> list[str]:
    label = display_name(path, denied)
    findings = [f"{label}: private-filename"] if private_name(path, denied) else []
    parts = Path(path).parts
    if (
        any(part in PRIVATE_DIRS or part.endswith(".review") for part in parts)
        or Path(path).suffix in {".pem", ".key", ".sqlite", ".db"}
        or Path(path).name == ".env"
        or Path(path).name.startswith(".env.")
    ):
        findings.append(f"{label}: private-runtime-file")
    try:
        content = data.decode("utf-8")
    except UnicodeDecodeError:
        return findings + [f"{label}: non-text-content-requires-review"]
    if mode == "120000":
        target = posixpath.normpath(posixpath.join(posixpath.dirname(path), content))
        if content.startswith("/") or target == ".." or target.startswith("../"):
            findings.append(f"{label}: external-symlink")
    for number, line in enumerate(content.splitlines(), 1):
        for name, pattern in RULES.items():
            if pattern.search(line):
                findings.append(f"{label}:{number}: {name}")
        if any(value.casefold() in line.casefold() for value in denied if value):
            findings.append(f"{label}:{number}: private-identifier")
    return findings


def scan_index(root: Path, denied: list[str]) -> list[str]:
    entries = subprocess.check_output(
        ["git", "-C", str(root), "ls-files", "--stage", "-z"]
    ).split(b"\0")
    findings = []
    count = 0
    for entry in entries:
        if not entry:
            continue
        metadata, raw_path = entry.split(b"\t", 1)
        mode, oid, stage = metadata.decode().split()
        path = raw_path.decode("utf-8")
        count += 1
        if stage != "0" or mode not in {"100644", "100755", "120000"}:
            findings.append(f"{display_name(path, denied)}: unsupported-index-entry")
            continue
        data = subprocess.check_output(
            ["git", "-C", str(root), "cat-file", "blob", oid]
        )
        findings.extend(inspect_blob(path, data, mode, denied))
    return findings if count else ["index: empty-index-is-not-verified"]


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path.cwd())
    parser.add_argument(
        "--deny-file",
        type=Path,
        help="Private newline-separated identifiers; keep outside the repository.",
    )
    args = parser.parse_args()
    denied = args.deny_file.read_text().splitlines() if args.deny_file else []
    findings = scan_index(args.root, denied)
    if findings:
        print("\n".join(findings))
        return 1
    print(
        "Staged content passed configured privacy checks; manual review is still required."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
