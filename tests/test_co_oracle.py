"""Oracle validation: the solver vs published CO isotopologue levels
(Grigorev et al., ApJS 283, 2026), per wayfinder ticket #9.

Same dataset and tolerances MARVEL_GNN's independent port validated against;
where the deposited input's single uncertainty column can't reproduce the
paper's optimized-uncertainty resolve, the tolerance documents that gap.
"""

from pathlib import Path

import pytest

from marvel5.network import split_components
from marvel5.parse import parse_mrt_transitions
from marvel5.solver import solve_energies

CO_DIR = Path(r"C:\Code\MARVEL_scraping\molecules\CO")

TOLERANCE = {
    "12C17O": 5e-9,
    "13C16O": 2e-8,
    "13C17O": 5e-8,
    "12C18O": 1e-6,   # optimized-unc gap, systematic ~6.5e-7
    "13C18O": 5e-8,   # excluding "1 0", handled separately below
}

pytestmark = pytest.mark.skipif(not CO_DIR.exists(), reason="CO oracle data not present")


def _parse_published_levels(path):
    """{iso: {"v J": (energy, unc)}} from the published MRT levels table."""
    out = {}
    lines = Path(path).read_text().splitlines()
    dividers = [i for i, l in enumerate(lines) if l.startswith("-" * 40)]
    for line in lines[dividers[-1] + 1:]:
        t = line.split()
        if not t:
            continue
        out.setdefault(t[0], {})[f"{t[2]} {t[3]}"] = (float(t[4]), float(t[5]))
    return out


@pytest.fixture(scope="module")
def oracle():
    transitions = parse_mrt_transitions(CO_DIR / "CO_isotopologues_all_input.txt")
    by_iso: dict[str, list] = {}
    for t in transitions:
        if t.freq < 0.0:
            continue  # legacy MARVEL exclusion; see combination_differences.resolve_uncertainty
        t.uncertainty_used = t.orig_unc  # bypass MarvelRun edit-tracking for a pure solver check
        by_iso.setdefault(t.iso, []).append(t)
    published = _parse_published_levels(CO_DIR / "CO_isotopologues_all_output.txt")
    return by_iso, published


@pytest.mark.parametrize("iso", sorted(TOLERANCE))
def test_energies_match_published(oracle, iso):
    by_iso, published = oracle
    components = split_components(by_iso[iso])
    computed_full = solve_energies(components[0])  # published set = largest component only
    computed = {level_id.split(" ", 1)[1]: e for level_id, e in computed_full.items()}
    pub = {a: e for a, (e, _) in published[iso].items()}

    assert set(computed) == set(pub)
    assert computed["0 0"] == 0.0 and pub["0 0"] == 0.0

    known_gap = {"13C18O": {"1 0"}}.get(iso, set())
    diffs = {a: abs(computed[a] - pub[a]) for a in pub if a not in known_gap}
    worst = max(diffs, key=diffs.get)
    assert diffs[worst] < TOLERANCE[iso], f"worst level {worst}: {diffs[worst]:.3e}"

    for a in known_gap:
        assert abs(computed[a] - pub[a]) < 5e-4
