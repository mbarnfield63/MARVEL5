"""End-to-end smoke test over two small synthetic networks in one solve:

IsoA (4 levels, chain 0-1-2-3 plus a direct 0-2 check) has one deliberately
corrupted transition (t_bad) exercising consistency flagging — its residual
also pollutes the joint least-squares solve for the rest of IsoA, same as
real contaminated data would, so energy-precision assertions live in the
post-removal test instead.

IsoB (3 levels, chain 0-1-2) is clean and adds one uncertainty-less shortcut
transition (t_nounc) exercising the combination-differences backfill path in
isolation from IsoA's contamination.
"""

from pathlib import Path

import pytest

from marvel5.run import MarvelRun

MRT = """\
Title: synthetic test data
--------------------------------------------------------------------------------
IsoA 01     10.0        0.001  0   1  0   0 t1
IsoA 01     11.0        0.001  0   2  0   1 t2
IsoA 01     12.0        0.001  0   3  0   2 t3
IsoA 01     21.0        0.001  0   2  0   0 t4
IsoA 01    999.0        0.001  0   3  0   0 t_bad
IsoB 01     10.0        0.001  0   1  0   0 u1
IsoB 01     11.0        0.001  0   2  0   1 u2
IsoB 01     21.0        REQUIRES 0   2  0   0 t_nounc
"""


@pytest.fixture()
def run(tmp_path: Path) -> MarvelRun:
    path = tmp_path / "synthetic.mrt"
    path.write_text(MRT)
    return MarvelRun.from_file(path).solve(bootstrap_iterations=10)


def test_bad_transition_flagged(run):
    by_id = {t["transition_id"]: t for t in run.transitions}
    assert bool(by_id["IsoA:t_bad"]["consistency_flag"]) is True

    # t_bad's residual is so large it also drags every other IsoA transition's
    # fit off past the cutoff — same "one bad line poisons the network" effect
    # the offender-ratio flag exists to surface. Confirmed clean in the
    # post-removal test below.
    flagged_levels = {lvl["level_id"] for lvl in run.levels if lvl["consistency_flag"]}
    assert "IsoA 0 0" in flagged_levels and "IsoA 0 3" in flagged_levels


def test_uncertainty_backfilled(run):
    t = {t["transition_id"]: t for t in run.transitions}["IsoB:t_nounc"]
    assert bool(t["removed"]) is True
    assert t["removed_reason"] == "no_uncertainty_excluded"
    assert t["uncertainty_source"] == "backfilled"
    assert t["uncertainty_used"] == pytest.approx(1e-6, abs=1e-9)  # near-perfect agreement, floored
    assert bool(t["consistency_flag"]) is False  # advisory only, never flagged the round it's backfilled


def test_remove_and_rerun_fixes_energies(run):
    run.remove_transition("IsoA:t_bad")
    run.rerun(bootstrap_iterations=10)

    by_id = {t["transition_id"]: t for t in run.transitions}
    assert by_id["IsoA:t_bad"]["removed_reason"] == "user_removed"
    assert all(not lvl["consistency_flag"] for lvl in run.levels)

    energies = {lvl["level_id"]: lvl["energy"] for lvl in run.levels}
    assert energies["IsoA 0 0"] == pytest.approx(0.0)
    assert energies["IsoA 0 1"] == pytest.approx(10.0, abs=0.5)
    assert energies["IsoA 0 2"] == pytest.approx(21.0, abs=0.5)
    assert energies["IsoA 0 3"] == pytest.approx(33.0, abs=0.5)


def test_write_output(run, tmp_path):
    run.write_output(tmp_path)
    assert (tmp_path / "synthetic_levels.csv").exists()
    assert (tmp_path / "synthetic_transitions.csv").exists()
