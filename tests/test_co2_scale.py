"""CO2-scale performance validation, per wayfinder ticket #9 validation plan
step 2 (~167k transitions across 12 isotopologues) — scale/perf only, not an
oracle-correctness check (that's CO's job; see test_co_oracle.py).

MARVEL_scraping's CO2 deposit is native MARVEL4-style transitions files
(`freq orig_unc optim_unc <upper QNs> <lower QNs> tag`), not the CDS MRT
format `parse_mrt_transitions` reads — so this test carries its own minimal
parser rather than extending the engine's real parser for a one-off scale
check.

# ponytail: no unit-segment inference (unlike MARVEL_GNN's CO2 oracle port) —
# every value here reads at face value as cm-1. Fine for timing/crash
# coverage; would matter if this test ever asserted absolute energies.
"""

import time
from pathlib import Path

import pytest

from marvel5.parse import Transition
from marvel5.run import MarvelRun

CO2_DIR = Path(r"C:\Code\MARVEL_scraping\molecules\CO2")
ISOS = ["626", "627", "628", "636", "637", "638", "727", "728", "737", "738", "828", "838"]

pytestmark = pytest.mark.skipif(not CO2_DIR.exists(), reason="CO2 scale data not present")

SOLVE_TIME_CEILING_S = 300  # generous; catches catastrophic regressions, not tuned to a machine


def _find(iso: str) -> Path:
    for prefix in ("Transitions_", "transitions_"):
        p = CO2_DIR / f"{prefix}{iso}.txt"
        if p.exists():
            return p
    raise FileNotFoundError(iso)


def _parse_native(path: Path, iso: str) -> list[Transition]:
    out = []
    for lineno, line in enumerate(path.read_text().splitlines(), 1):
        tokens = line.split()
        if not tokens or tokens[0].startswith("#") or "&" in line:
            continue
        freq, orig_unc = float(tokens[0]), float(tokens[2])  # optim_unc column
        qn_tokens, tag = tokens[3:-1], tokens[-1]
        nqn = len(qn_tokens) // 2
        upper_qn, lower_qn = tuple(qn_tokens[:nqn]), tuple(qn_tokens[nqn:])
        out.append(Transition(
            transition_id=f"{iso}:{tag}:{lineno}",
            iso=iso,
            freq=freq,
            orig_unc=orig_unc or None,
            upper=f"{iso} {' '.join(upper_qn)}",
            lower=f"{iso} {' '.join(lower_qn)}",
            upper_qn=upper_qn,
            lower_qn=lower_qn,
            tag=tag,
        ))
    return out


@pytest.fixture(scope="module")
def transitions() -> list[Transition]:
    out = []
    for iso in ISOS:
        out += _parse_native(_find(iso), iso)
    return out


def test_dataset_scale(transitions):
    assert len(transitions) > 150_000  # ~167k across all 12 isotopologues


def test_full_solve_completes_within_ceiling(transitions):
    run = MarvelRun(transitions, run_name="co2_scale")

    start = time.perf_counter()
    run.solve(bootstrap_iterations=20)  # fewer bootstrap resamples than default 100; still full pipeline
    elapsed = time.perf_counter() - start

    assert elapsed < SOLVE_TIME_CEILING_S, f"solve() took {elapsed:.1f}s, ceiling {SOLVE_TIME_CEILING_S}s"
    assert len(run.levels) > 0
    assert len(run.transitions) == len(transitions)
