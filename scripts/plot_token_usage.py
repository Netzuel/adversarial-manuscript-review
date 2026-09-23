"""Reproduce the token study from sanitized data; no inference or network calls."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

COLORS = ["#0072B2", "#D55E00", "#009E73", "#CC79A7", "#E69F00"]
LABEL_FS, TICK_FS, LEGEND_FS = 11, 10, 10
ROLES = ["editor", "math", "methods", "evidence", "communication", "student", "auditor"]


def save(fig: Any, directory: Path, name: str) -> None:
    for extension in ("png", "pdf", "eps", "svg"):
        metadata = {"Creator": "AMR token study"} if extension == "pdf" else None
        path = directory / f"{name}.{extension}"
        fig.savefig(path, dpi=200, metadata=metadata)
        if extension == "svg":
            path.write_text(
                "\n".join(line.rstrip() for line in path.read_text().splitlines())
                + "\n"
            )
    plt.close(fig)


def setup_axis(ax: Any) -> None:
    ax.set_axisbelow(True)
    ax.grid(axis="y", color="0.9", linewidth=0.6, zorder=0)
    ax.spines[["top", "right"]].set_visible(False)


def analyze(data: dict[str, Any]) -> dict[str, Any]:
    sessions = data["sessions"]
    totals = data["totals"]
    by_role = {}
    for role in ROLES:
        selected = [s for s in sessions if s["role"] == role]
        by_role[role] = {
            "sessions": len(selected),
            "responses": sum(len(s["calls"]) for s in selected),
            **{k: sum(s["totals"][k] for s in selected) for k in totals},
        }
    by_phase = {
        phase: sum(s["totals"]["total_tokens"] for s in sessions if s["phase"] == phase)
        for phase in ("all", "initial", "revision", "verification", "audit")
    }
    count_phase = {
        phase: sum(len(s["calls"]) for s in sessions if s["phase"] == phase)
        for phase in by_phase
    }
    scenarios = []
    for rounds in range(1, 5):
        base = (
            by_phase["all"] * rounds / 2
            + by_phase["initial"]
            + (rounds - 1) * (by_phase["revision"] + by_phase["verification"])
            + by_phase["audit"]
        )
        calls = (
            count_phase["all"] * rounds / 2
            + count_phase["initial"]
            + (rounds - 1) * (count_phase["revision"] + count_phase["verification"])
            + count_phase["audit"]
        )
        for added in (0, 4000, 8000, 16000):
            for fraction in (0.25, 0.5, 1.0):
                scenarios.append(
                    dict(
                        rounds=rounds,
                        added_manuscript_tokens=added,
                        exposure_fraction=fraction,
                        child_dispatches=5 * rounds,
                        modeled_responses=calls,
                        total_tokens=base + calls * fraction * added,
                    )
                )
    return dict(
        totals=totals,
        by_role=by_role,
        by_phase=by_phase,
        responses=sum(len(s["calls"]) for s in sessions),
        cache_read_fraction=totals["cached_input_tokens"] / totals["input_tokens"],
        editor_total_fraction=by_role["editor"]["total_tokens"]
        / totals["total_tokens"],
        uncached_input_tokens=totals["input_tokens"]
        - totals["cached_input_tokens"]
        - totals["cache_write_input_tokens"],
        sensitivity_scenarios=scenarios,
    )


def plot(data: dict[str, Any], directory: Path) -> dict[str, Any]:
    plt.rcParams.update(
        {
            "font.family": "STIXGeneral",
            "mathtext.fontset": "stix",
            "axes.labelsize": LABEL_FS,
            "xtick.labelsize": TICK_FS,
            "ytick.labelsize": TICK_FS,
            "legend.fontsize": LEGEND_FS,
            "axes.axisbelow": True,
            "lines.linewidth": 1.6,
            "patch.linewidth": 0.6,
            "legend.framealpha": 1.0,
            "savefig.facecolor": "white",
        }
    )
    directory.mkdir(parents=True, exist_ok=True)
    summary = analyze(data)
    roles = summary["by_role"]
    fig, ax = plt.subplots(figsize=(7.2, 4.2))
    fig.subplots_adjust(left=0.17, right=0.97, bottom=0.16, top=0.76)
    setup_axis(ax)
    bottom = np.zeros(len(ROLES))
    for label, color, values in (
        (
            "Cache-read input",
            COLORS[0],
            [roles[r]["cached_input_tokens"] for r in ROLES],
        ),
        (
            "Other input",
            COLORS[1],
            [roles[r]["input_tokens"] - roles[r]["cached_input_tokens"] for r in ROLES],
        ),
        (
            "Output (includes reasoning)",
            COLORS[2],
            [roles[r]["output_tokens"] for r in ROLES],
        ),
    ):
        values = np.asarray(values) / 1e6
        ax.barh(ROLES, values, left=bottom, label=label, color=color, zorder=3)
        bottom += values
    ax.invert_yaxis()
    ax.set_xlabel("Reported tokens (millions)")
    fig.legend(loc="upper center", ncol=2, bbox_to_anchor=(0.53, 0.99))
    ax.set_title("Observed fixture: usage by role", fontsize=12, pad=10)
    save(fig, directory, "roles")

    fig, axes = plt.subplots(2, 1, figsize=(7.2, 6.2), sharex=True)
    fig.subplots_adjust(left=0.13, right=0.97, bottom=0.10, top=0.88, hspace=0.32)
    for ax in axes:
        setup_axis(ax)
    for group, color in (("editor", COLORS[0]), ("children", COLORS[1])):
        calls = sorted(
            [
                c
                for s in data["sessions"]
                if (s["role"] == "editor") == (group == "editor")
                for c in s["calls"]
            ],
            key=lambda c: c["elapsed_seconds"],
        )
        times = [c["elapsed_seconds"] / 60 for c in calls]
        axes[0].step(
            times,
            np.cumsum([c["total_tokens"] for c in calls]) / 1e6,
            where="post",
            label=group.capitalize(),
            color=color,
        )
        axes[1].scatter(
            times,
            [c["input_tokens"] / 1000 for c in calls],
            s=18,
            color=color,
            zorder=3,
        )
    axes[0].set_ylabel("Cumulative tokens (M)")
    axes[1].set_ylabel("Input per response (k)")
    axes[1].set_xlabel("Minutes after first recorded response")
    axes[0].set_title("Observed fixture: context accumulation", fontsize=12)
    handles, labels = axes[0].get_legend_handles_labels()
    fig.legend(handles, labels, loc="upper center", ncol=2)
    save(fig, directory, "timeline")

    fig, ax = plt.subplots(figsize=(6.5, 4.2))
    fig.subplots_adjust(left=0.13, right=0.97, bottom=0.16, top=0.78)
    setup_axis(ax)
    for added, color in zip((0, 4000, 8000, 16000), COLORS):
        rows = [
            s
            for s in summary["sensitivity_scenarios"]
            if s["added_manuscript_tokens"] == added and s["exposure_fraction"] == 1
        ]
        ax.plot(
            [r["rounds"] for r in rows],
            [r["total_tokens"] / 1e6 for r in rows],
            marker="o",
            color=color,
            label=f"+{added // 1000}k tokens",
        )
    ax.set_xticks([1, 2, 3, 4])
    ax.set_xlabel("Review rounds (assumed full specialist waves)")
    ax.set_ylabel("Modeled total tokens (millions)")
    ax.set_title("Sensitivity only: added text in every modeled response", fontsize=12)
    fig.legend(loc="upper center", ncol=4, bbox_to_anchor=(0.54, 0.98))
    save(fig, directory, "sensitivity")

    fig, ax = plt.subplots(figsize=(6.5, 4.2))
    fig.subplots_adjust(left=0.13, right=0.97, bottom=0.17, top=0.72)
    setup_axis(ax)
    totals = data["totals"]
    h = np.linspace(0, 1, 101)
    for ratio, color in zip((0.1, 0.25, 0.5), COLORS):
        # A dimensionless what-if, not a tariff or measured bill. Write volume is zero.
        cost = (
            totals["input_tokens"] * (1 - h + ratio * h) + 6 * totals["output_tokens"]
        ) / 1e6
        ax.plot(h * 100, cost, color=color, label=f"Cache rate = {ratio:g} × input")
    ax.axvline(summary["cache_read_fraction"] * 100, color="0.35", linestyle=":")
    ax.text(
        summary["cache_read_fraction"] * 100 - 2,
        4.5,
        "Observed hit fraction",
        ha="right",
        va="top",
        fontsize=10,
    )
    ax.set_xlabel("Cache-read fraction of input (%)")
    ax.set_ylabel("Relative cost units")
    ax.set_title(
        "Sensitivity only: fixed token counts; output rate = 6 × input", fontsize=12
    )
    fig.legend(loc="upper center", ncol=1, bbox_to_anchor=(0.55, 1.01))
    save(fig, directory, "cache")
    return summary


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--data", type=Path, default=Path("docs/data/token-usage/observed.json")
    )
    parser.add_argument("--output", type=Path, default=Path("docs/figures/token-usage"))
    parser.add_argument(
        "--summary", type=Path, default=Path("docs/data/token-usage/summary.json")
    )
    args = parser.parse_args()
    data = json.loads(args.data.read_text())
    result = plot(data, args.output)
    args.summary.parent.mkdir(parents=True, exist_ok=True)
    args.summary.write_text(json.dumps(result, indent=2) + "\n")


if __name__ == "__main__":
    main()
