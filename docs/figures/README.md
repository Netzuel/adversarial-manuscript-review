# Workflow figure

The README uses two transparent vector exports: [light](review-workflow.svg) and [dark](review-workflow-dark.svg). GitHub selects the appropriate image through its [theme-aware `picture` support](https://github.blog/changelog/2022-08-15-specify-theme-context-for-images-in-markdown-ga/). The canvas has no fill; stage boxes retain their semantic colors. Text, arrows, and boxes use contrasting palettes for each theme.

The editable source is [review-workflow.tex](review-workflow.tex). The [dark entry point](review-workflow-dark.tex) selects the dark palette and includes the same geometry and labels. The portrait layout keeps labels readable at a 640-pixel display width. Full-size links below the README figure open either variant.

The central spine shows revision mode. Solid blue routes return findings from checks or the fresh audit to review, subject to the remaining budget. The dashed amber route delivers a truthful blocked or stopped result. Shared junctions combine routes; they do not add review stages. Review-only mode skips student edits.

## Rebuild

Use Tectonic with cached LaTeX, TikZ, fontspec, and Latin Modern Sans resources, plus Poppler's `pdftocairo`. From the repository root:

```sh
mkdir -p build/diagram
tectonic --only-cached --untrusted --outdir build/diagram docs/figures/review-workflow.tex
pdftocairo -svg build/diagram/review-workflow.pdf docs/figures/review-workflow.svg
tectonic --only-cached --untrusted --outdir build/diagram docs/figures/review-workflow-dark.tex
pdftocairo -svg build/diagram/review-workflow-dark.pdf docs/figures/review-workflow-dark.svg
```

The cached-only command fails if resources are missing. Provision the required TeX resources separately before running it. A LuaLaTeX installation with those packages and fonts can also compile the source; do not enable shell escape.

For a preview with Ghostscript:

```sh
gs -q -dSAFER -dBATCH -dNOPAUSE -sDEVICE=pngalpha -r144 \
  -sOutputFile=build/diagram/review-workflow.png build/diagram/review-workflow.pdf
```

Repeat the preview command for `review-workflow-dark.pdf`. Inspect both transparent previews against their intended light or dark background. Check labels, arrow junctions, and box boundaries at the intended display size. Keep the PDF, PNG previews, logs, and intermediate files in the ignored build directory. Commit only the sources and SVGs. Both SVGs use local vector paths and contain no external font or image dependencies.

Before committing, inspect SVG metadata and links, run the public-content scan, and check the staged diff. The README supplies a text alternative for the image.

[Project overview](../../README.md) · [Documentation index](../README.md)
