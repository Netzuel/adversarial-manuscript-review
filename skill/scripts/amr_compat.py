"""Optional local update pin for existing runs; never routes model inference."""

import argparse
import hashlib
import json
import os
import sys
from pathlib import Path

PIN_PATH = Path(__file__).resolve().parents[2] / "legacy-runtime.json"


def file_hash(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def legacy_run(argv: list[str]) -> Path | None:
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument("--run", type=Path)
    known, remaining = parser.parse_known_args(argv)
    run = known.run
    if run is None and remaining and remaining[0] == "init" and "--resume" in remaining:
        init = argparse.ArgumentParser(add_help=False)
        init.add_argument("source", nargs="?", type=Path)
        init.add_argument("--resume", action="store_true")
        init.add_argument("--review-only", action="store_true")
        init.add_argument("--in-place", action="store_true")
        init.add_argument("--max-rounds")
        options, _ = init.parse_known_args(remaining[1:])
        if options.source is None:
            return None
        source = options.source.absolute()
        choices = []
        for path in (source.parent / (source.stem + ".review")).glob("*/state.json"):
            state = json.loads(path.read_text())
            if state.get("source") == str(source) and state.get("status") in (
                None,
                "INTERRUPTED",
            ):
                choices.append(path.parent)
        if len(choices) != 1:
            return (
                None  # Normal initialization reports ambiguity; never choose silently.
            )
        run = choices[0]
    if run is None or not (run / "state.json").is_file():
        return None
    state = json.loads((run / "state.json").read_text())
    return run if "feedback_policy" not in state else None


def route_legacy(argv: list[str]) -> None:
    run = legacy_run(argv)
    if run is None:
        return
    if not PIN_PATH.is_file():
        raise ValueError(
            "legacy run requires its original runtime; no verified local pin exists"
        )
    pin = json.loads(PIN_PATH.read_text())
    runtime = Path(pin["runtime"])
    if (
        not runtime.is_absolute()
        or not runtime.is_file()
        or file_hash(runtime) != pin["sha256"]
    ):
        raise ValueError(
            "pinned legacy runtime missing or changed; do not migrate a live run"
        )
    if "pending" in argv:
        print(
            json.dumps(
                {
                    "legacy_run": True,
                    "runtime": str(runtime),
                    "workflow": pin["workflow"],
                    "next_action": "Continue with the original run workflow and budgets.",
                }
            )
        )
        raise SystemExit(0)
    print(
        "Continuing legacy run with its original workflow: " + pin["workflow"],
        file=sys.stderr,
    )
    os.execv(sys.executable, [sys.executable, str(runtime), *argv])
