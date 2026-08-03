# MARVEL5

Measured Active Rotational Vibrational Energy Levels — v5.

An independent rewrite of the MARVEL algorithm (Furtenbacher, Császár & Tennyson 2007; Furtenbacher & Császár 2012), which inverts measured rotational-vibrational transitions into empirical energy levels with well-defined uncertainties, via a spectroscopic network (energy levels as nodes, transitions as edges).

v5 combines methods from across MARVEL's history:

- **Bootstrap + Dijkstra uncertainty estimation** (from MARVEL4)
- **Combination-differences consistency checking** (from MARVEL2/3 — Furtenbacher, Császár & Tennyson 2007; Furtenbacher & Császár 2012)

alongside a companion **interactive graph-visualization app** for exploring the resulting spectroscopic network: a rigid ladder of states and transitions (Obsidian-graph-view-like, but fixed rather than physics-based), ground state in green, inconsistent states/transitions flagged red, hover-to-highlight, and toggling by experiment tag.

## Status

Early planning. Two efforts are being charted as [wayfinder](https://github.com/mattpocock/skills/tree/main/skills/engineering/wayfinder) maps on this repo's issue tracker — open decisions and progress are visible there, not here:

- [MARVEL v5 Engine](https://github.com/mbarnfield63/MARVEL5/issues/3) — the parser/solver/uncertainty/combination-differences rewrite.
- [MARVEL v5 Viz App](https://github.com/mbarnfield63/MARVEL5/issues/4) — the graph-visualization app.

See `wayfinder/README.md` for how those maps and their tickets are organized.

## Related repos

- [`MARVEL_GNN`](https://github.com/mbarnfield63/MARVEL_GNN) — a separate, independent Python port of MARVEL4.1's core, extended with a graph neural network (uncertainty calibration, outlier detection, orphan-node linkage, label correction). Not a dependency of v5, but useful prior art.
- [`MARVEL_scraping`](https://github.com/mbarnfield63/scraping-for-marvel) — a sibling pipeline that turns published papers into MARVEL input files (MRT format). v5 aims to stay compatible with its output.

## Provenance

If you use this code, please cite the original MARVEL papers:

- Furtenbacher, T., Császár, A. G., & Tennyson, J. (2007). *J. Mol. Spectrosc.*, 245, 115–125.
- Furtenbacher, T., & Császár, A. G. (2012). *JQSRT*, 113, 929–935.
