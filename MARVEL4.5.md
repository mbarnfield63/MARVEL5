# MARVEL 4.5 — reference notes

Notes from an audit of the original authors' MARVEL 4.5, done 2026-09-09. Reference
material only: v5 does not depend on it. Recorded here so the work does not have to be
repeated if we return to it.

## What it is

Upstream: <https://github.com/FurtEd/MARVEL> (Tibor Furtenbacher). Cloned locally to
`C:\Code\versions_MARVEL\MARVEL4.5`, alongside the existing 3.0/3.1/4.1 copies.

The repo itself holds only a README and three test inputs — **no source code**. The
application ships as a release-tab zip (`MARVEL4.5.zip`, release tag `v4.5`, 2026-09-01).

4.5 is **the MARVEL 4.1 C++ engine compiled to WebAssembly** (Emscripten) and wrapped in
a Vue 3 + Bootstrap single-page app that runs from `file://` with no server and no
network. It is a repackaging of 4.1 for distribution, not a new algorithm.

Local layout after the clone:

- `release_v4.5/extracted/MARVEL4.5/` — the current release, unpacked
- `history/` — all 8 historical zips, recovered from git blobs (the authors delete each
  zip when uploading the next, so history is only reachable via `git show <sha>:<file>`)

## Engine genealogy

The numerical core is 4.1 carried over with high fidelity — verified by exact matches
between strings embedded in `marvel.wasm` and our 4.1 source at
`C:\Code\MARVEL_GNN\Source_Code_CPP\MARVEL4.1.cpp`:

- weighted normal equations solved with Eigen `SimplicialLDLT`
- hand-rolled Dijkstra for network traversal (`functions.cpp`)
- `mt19937` bootstrap uncertainty loop
- `getCategory()` bad-line classifier (`" VERY BAD_1000"`, `" WRONG"`, etc.)

Genuinely new in 4.5, on top of 4.1:

- an embind API (`processInputFile`, `runMARVEL`, `ResultStorage`, `BadLine`,
  `deletedLine`) replacing 4.1's `main(argc, argv)` — this is what makes the engine
  callable and re-runnable rather than one-shot
- a unit-aware segment parser (cm-1, MHz, GHz, kHz, Hz, THz) with column-count
  validation and line-numbered error messages
- a `Components.txt` connectivity report, surfaced as a UI tab

`marvel.wasm` was recompiled three times (2026-08-10, 08-14, 08-24). The current release
(09-01) is the 08-24 build with every file byte-identical; the only change is a
top-level `MARVEL4.5/` folder added inside the zip.

## Verdict for v5

Nothing here needs adopting, and nothing blocks us. Relevant conclusions:

- **The engine runs headless under Node.** `marvel.js` is a plain (non-MODULARIZE)
  Emscripten build that `require()`s directly; mount inputs into the Emscripten FS at
  `/segment` and `/transition`, then call `processInputFile(...)` and `runMARVEL()`. Note
  the shipped HO35Cl files have two uncertainty columns, so the `unc` argument must be
  `2`. This makes 4.5 usable as a **second oracle** for v5 alongside the CO one.
- **Practical scale ceiling is ~10-15k levels**, driven by level count, not transition
  count (50k transitions over 2k levels ran in 36 s; 15k levels took 342 s; ~20k levels
  dies with `RangeError: Maximum call stack size exceeded`). The module reserves 1 GiB at
  page load against a 2 GiB wasm32 cap. CO2-scale networks are out of reach for 4.5 — v5
  is not competing with it at scale.
- **No licence** on the upstream repo, so the code is not legally reusable. Behaviour can
  be compared against; source cannot be copied.
- v5's existing choices around disconnected and tree-shaped components (tickets #17/#18)
  target real weaknesses: 4.1's solver panics via `system("pause"); exit(-1)`
  (`MARVEL4.1.cpp:1056-1068`) on decomposition failure, which in the browser surfaces as
  a bare "Program terminated with exit(-1)" with no diagnosis.

Wrapper-layer defects were found (a precision round-trip through a rounded DOM cell, a
`sw.js` syntax error that has kept the service worker from ever registering, an
`endsWith()` reference match that can hit the wrong line, and a pre-flight validation
guard the authors added then deleted). None affect the science in a way worth reporting
upstream, and none were filed. Details are in this session's log entry if needed.

## Negative wavenumbers — already handled in v5

In MARVEL input, **a negative frequency marks a deactivated transition**: 4.1 pushes it
onto `badlines` and `continue`s (`MARVEL4.1.cpp:432`), excluding it from the solve
entirely. Upstream's own clean HO35Cl test file contains 147 such lines.

v5 already implements this. `resolve_uncertainty` in `combination_differences.py` sets
`removed = True, removed_reason = "negative_freq_excluded"`, `run.py:57` gates the solve
on `not t.removed`, and `tests/test_combination_differences.py:29-37` covers the
`user_removed > negative_freq_excluded > no_uncertainty_excluded` priority order. The
docstring records that it was confirmed necessary against the CO oracle, where leaving
hot-band negative-frequency lines weighted pulls every energy in the network off by
10^2-10^3 cm-1.

(This was initially mis-reported as a live v5 bug during the audit — traced from
`parse.py:74` into `solver.py:44-45` without checking what sets `removed` in between.
Filed as ticket #20 and closed as already-implemented.)

What v5 does **not** do is re-examine those lines afterwards. MARVEL 3.1 and 4.1 both
compare each deactivated line against the energies its assignment got from the rest of
the network and write a Revive / BAD TR / UNKNOWN verdict to `reviveTRs.txt`
(`MARVEL4.1.cpp:830-836`) — the reasoning being that a line deactivated against an older,
smaller network may agree fine with the current one. That gap is a genuine open decision,
tracked as [ticket #21](https://github.com/mbarnfield63/MARVEL5/issues/21).

## Recovered test fixtures

Upstream deleted `tests/results/` in commit `8747d31` (2026-07-17), removing the
expected outputs for the HO35Cl test case. They are still recoverable from the clone:

```
git show 8747d31^:tests/results/energies_unc_HO35Cl_2023.txt
git show 8747d31^:tests/results/energies_unc_HO35Cl_2023_bad.txt
git show 8747d31^:tests/results/transitions_bad_HO35Cl_2023_bad.txt
git show 8747d31^:tests/results/transitions_converted_report_HO35Cl_2023.txt
git show 8747d31^:tests/results/transitions_converted_report_HO35Cl_2023_bad.txt
```

The energies files hold 5760 levels each as `<6 quantum numbers> | <energy, cm-1> |
<uncertainty, cm-1>`. The `_bad` variants correspond to
`tests/inputs/transitions_HO35Cl_2023_bad.txt`, which differs from the clean file by
exactly one line — line 270, ref `95BeNaFuMo.33`, frequency shifted by +1 cm-1. The
validation report flags it at `Diff = 0.001261` against `UncM = 0.000003`.

That is a ready-made corruption-injection fixture with published expected output, for a
molecule we do not otherwise have an oracle for. Worth pulling into `tests/data/` if we
want a second end-to-end oracle beyond CO.
