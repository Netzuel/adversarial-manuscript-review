"""Additive user installation; ownership is checked before every removal."""

import argparse
import hashlib
import fcntl
import json
import os
from pathlib import Path

NAME = "adversarial-manuscript-review"


def fingerprint(path):
    if path.is_symlink():
        return {"kind": "link", "target": os.readlink(path)}
    if path.is_file():
        return {"kind": "file", "sha256": hashlib.sha256(path.read_bytes()).hexdigest()}
    return {"kind": "missing"} if not path.exists() else {"kind": "other"}


def manage(action, home, source, host="all"):
    source = Path(source).resolve()
    lock_path = source / "installation-records" / ".installer.lock"
    lock_path.parent.mkdir(parents=True, exist_ok=True)
    with lock_path.open("a") as lock:
        try:
            fcntl.flock(lock.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError as exc:
            raise ValueError("Another installer is active") from exc
        return _manage(action, home, source, host)


def _manage(action, home, source, host="all"):
    home, source = Path(home).resolve(), Path(source).resolve()
    hosts = ["codex", "claude"] if host == "all" else [host]
    record_path = (
        source
        / "installation-records"
        / (hashlib.sha256(str(home).encode()).hexdigest()[:16] + ".json")
    )
    record = (
        json.loads(record_path.read_text())
        if record_path.exists()
        else {"home": str(home), "owned": {}}
    )
    desired = {}
    wrappers = []
    for current in hosts:
        wrapper = source / "adapters" / f"{current}-skill"
        if not (wrapper / "SKILL.md").is_file():
            raise ValueError(f"Missing host wrapper: {wrapper}")
        wrappers.append(wrapper)
        skill_path = (
            home / (".agents" if current == "codex" else ".claude") / "skills" / NAME
        )
        desired[str(skill_path)] = {
            "host": current,
            "kind": "link",
            "target": str(wrapper),
        }
        for agent in sorted((source / "adapters" / f"{current}-agents").glob("amr-*")):
            target = (
                home
                / (".codex" if current == "codex" else ".claude")
                / "agents"
                / agent.name
            )
            desired[str(target)] = {
                "host": current,
                "kind": "file",
                "sha256": hashlib.sha256(agent.read_bytes()).hexdigest(),
                "source": str(agent),
            }
    selected = {p: v for p, v in record["owned"].items() if v["host"] in hosts}
    for path in set(desired) | set(selected):
        target = Path(path)
        if not target.is_relative_to(
            home
        ) or not target.parent.resolve().is_relative_to(home):
            raise ValueError(f"Installation path escapes selected home: {path}")

    def matches(path, item):
        return fingerprint(Path(path)) == {
            k: v for k, v in item.items() if k in {"kind", "target", "sha256"}
        }

    problems = []
    for path, item in selected.items():
        if fingerprint(Path(path))["kind"] != "missing" and not matches(path, item):
            problems.append(f"Owned path changed: {path}")
    if action == "diagnose":
        missing = [
            p for p, v in desired.items() if p not in selected or not matches(p, v)
        ]
        return {
            "healthy": not problems and not missing,
            "problems": problems,
            "missing_or_disabled": missing,
            "record": str(record_path),
            "owned": selected,
        }
    if problems:
        raise ValueError("; ".join(problems))
    if action == "install":
        for path in desired:
            if fingerprint(Path(path))["kind"] != "missing" and path not in selected:
                raise ValueError(f"Unowned collision: {path}")
        for path, item in desired.items():
            if (
                path in selected
                and fingerprint(Path(path))["kind"] != "missing"
                and not matches(path, item)
            ):
                raise ValueError(
                    f"Installed content differs; uninstall before upgrade: {path}"
                )
        # Wrapper assets share the sole provider-neutral source tree.
        for wrapper in wrappers:
            for name in ["scripts", "references", "templates"]:
                asset = wrapper / name
                expected = source / "skill" / name
                if asset.is_symlink() and asset.resolve() == expected:
                    continue
                if asset.exists() or asset.is_symlink():
                    raise ValueError(f"Wrapper asset collision: {asset}")
        for wrapper in wrappers:
            for name in ["scripts", "references", "templates"]:
                asset = wrapper / name
                if not asset.is_symlink():
                    asset.symlink_to(
                        Path("..") / ".." / "skill" / name, target_is_directory=True
                    )
        for path, item in desired.items():
            target = Path(path)
            target.parent.mkdir(parents=True, exist_ok=True)
            if path in selected and matches(path, item):
                continue
            if fingerprint(target)["kind"] != "missing":
                # Source changes require explicit uninstall first; no silent upgrades.
                raise ValueError(
                    f"Installed content differs; uninstall before upgrade: {path}"
                )
            if item["kind"] == "link":
                target.symlink_to(item["target"], target_is_directory=True)
            else:
                with target.open("xb") as stream:
                    stream.write(Path(item["source"]).read_bytes())
            record["owned"][path] = item
            record_path.parent.mkdir(parents=True, exist_ok=True)
            temporary = record_path.with_suffix(".tmp")
            temporary.write_text(json.dumps(record, indent=2) + "\n")
            temporary.replace(record_path)
    elif action in {"disable", "uninstall"}:
        for path, item in selected.items():
            if action == "disable" and item["kind"] != "link":
                continue
            target = Path(path)
            if target.exists() or target.is_symlink():
                if not matches(path, item):
                    raise ValueError(f"Concurrent modification: {path}")
                target.unlink()
            del record["owned"][path]
        record_path.parent.mkdir(parents=True, exist_ok=True)
        temporary = record_path.with_suffix(".tmp")
        temporary.write_text(json.dumps(record, indent=2) + "\n")
        temporary.replace(record_path)
    else:
        raise ValueError(f"Unknown action: {action}")
    return {
        "action": action,
        "home": str(home),
        "record": str(record_path),
        "owned": record["owned"],
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "action", choices=["install", "diagnose", "disable", "uninstall"]
    )
    parser.add_argument("--home", type=Path, default=Path.home())
    parser.add_argument("--host", choices=["codex", "claude", "all"], default="all")
    args = parser.parse_args()
    try:
        result = manage(
            args.action, args.home, Path(__file__).resolve().parent, args.host
        )
    except (ValueError, OSError) as exc:
        parser.exit(1, f"{exc}\n")
    print(json.dumps(result, indent=2))
    return 0 if result.get("healthy", True) else 1


if __name__ == "__main__":
    raise SystemExit(main())
