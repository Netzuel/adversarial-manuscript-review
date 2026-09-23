"""Verify dollar accounting and vector/theme export contracts."""

import importlib.util
import json
from pathlib import Path
import xml.etree.ElementTree as ET

import pytest

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location(
    "plot_usage", ROOT / "scripts/plot_token_usage.py"
)
assert spec and spec.loader
plots = importlib.util.module_from_spec(spec)
spec.loader.exec_module(plots)


def test_cost_partitions_and_context_gate():
    data = json.loads((ROOT / "docs/data/token-usage/observed.json").read_text())
    pricing = json.loads((ROOT / "docs/data/token-usage/pricing.json").read_text())
    costs = plots.price_workload(data, pricing)
    assert costs[0]["recorded_cache_usd"] == pytest.approx(8.690632)
    assert costs[0]["no_cache_usd"] == pytest.approx(46.73428)
    assert costs[2]["recorded_cache_usd"] == pytest.approx(0.08690632)
    pricing["models"][0]["input_limit"] = 10
    with pytest.raises(ValueError, match="context"):
        plots.price_workload(data, pricing)


def test_cache_writes_are_charged_once():
    data = {
        "totals": {
            "input_tokens": 1000000,
            "cached_input_tokens": 400000,
            "cache_write_input_tokens": 100000,
            "output_tokens": 10000,
        },
        "sessions": [{"calls": [{"input_tokens": 1000}]}],
    }
    pricing = {
        "models": [
            {
                "model": "test",
                "input": 2,
                "cache_read": 0.2,
                "cache_write": 2.5,
                "output": 10,
                "input_limit": 1000,
            }
        ]
    }
    cost = plots.price_workload(data, pricing)[0]
    assert cost["recorded_cache_usd"] == pytest.approx(1.43)
    assert cost["no_cache_usd"] == pytest.approx(2.1)


def test_transparent_vector_light_and_dark_exports(tmp_path):
    fig, ax = plots.plt.subplots()
    ax.plot([0, 1], [1, 2])
    ax.set_title("Theme test")
    plots.save(fig, tmp_path, "sample")
    ns = {"s": "http://www.w3.org/2000/svg"}
    for suffix, ink in (("", "#24292f"), ("-dark", "#e6edf3")):
        path = tmp_path / f"sample{suffix}.svg"
        tree = ET.parse(path)
        assert tree.findall(".//s:path", ns)
        assert not tree.findall(".//s:image", ns), "must not embed raster graphics"
        assert ink in path.read_text()
        for group in tree.findall(".//s:g", ns):
            if group.get("id") in {"patch_1", "patch_2"}:
                assert all(
                    "fill: none" in p.get("style", "")
                    for p in group.findall("s:path", ns)
                )
        rgba = plots.plt.imread(tmp_path / f"sample{suffix}.png")
        assert rgba[0, 0, 3] == 0


def test_study_wires_every_figure_to_both_themes():
    from html.parser import HTMLParser

    class Pictures(HTMLParser):
        def __init__(self):
            super().__init__()
            self.sources = []
            self.images = []

        def handle_starttag(self, tag, attrs):
            attrs = dict(attrs)
            if tag == "source":
                self.sources.append(attrs)
            elif tag == "img":
                self.images.append(attrs)

    parser = Pictures()
    parser.feed((ROOT / "docs/token-usage.md").read_text())
    assert len(parser.images) == 5
    assert len(parser.sources) == 10
    for image in parser.images:
        light = image["src"]
        dark = light.replace(".svg", "-dark.svg")
        for theme, target in (("light", light), ("dark", dark)):
            assert {
                "media": f"(prefers-color-scheme: {theme})",
                "srcset": target,
            } in parser.sources
            tree = ET.parse(ROOT / "docs" / target)
            assert not tree.findall(".//{http://www.w3.org/2000/svg}image")
            assert 'style="fill: none"' in (ROOT / "docs" / target).read_text()
    assert (
        "[concise study and model costs in USD](docs/token-usage.md)"
        in (ROOT / "README.md").read_text()
    )
