# Workflow figure

[review-workflow.svg](review-workflow.svg) is the scalable vector figure used in the project README. Its editable source is [review-workflow.tex](review-workflow.tex). The portrait layout keeps labels readable at a 640-pixel display width; click the README image to open the full vector.

The central spine shows revision mode. Solid blue routes return findings from checks or the fresh audit to review, subject to the remaining budget. The dashed amber route delivers a truthful blocked or stopped result. Shared junctions combine routes; they do not add review stages. Review-only mode skips student edits.

## Rebuild

Use Tectonic with cached LaTeX, TikZ, fontspec, and Latin Modern Sans resources, plus Poppler's `pdftocairo`. From the repository root:

```sh
mkdir -p build/diagram
tectonic --only-cached --untrusted --outdir build/diagram docs/figures/review-workflow.tex
pdftocairo -svg build/diagram/review-workflow.pdf docs/figures/review-workflow.svg
```

The cached-only command fails if resources are missing. Provision the required TeX resources separately before running it. A LuaLaTeX installation with those packages and fonts can also compile the source; do not enable shell escape.

For a preview with Ghostscript:

```sh
gs -q -dSAFER -dBATCH -dNOPAUSE -sDEVICE=png16m -r144 \
  -sOutputFile=build/diagram/review-workflow.png build/diagram/review-workflow.pdf
```

Inspect the full figure and its labels, arrow junctions, and box boundaries at the intended display size. Keep the PDF, PNG previews, logs, and intermediate files in the ignored build directory. Commit only the source and SVG. The SVG uses local vector paths and contains no external font or image dependencies.

Before committing, inspect SVG metadata and links, run the public-content scan, and check the staged diff. The README supplies a text alternative for the image.

[Project overview](../../README.md) · [Documentation index](../README.md)
