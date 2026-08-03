"""Known-bad-injection suite for combination-differences, per wayfinder ticket #9
validation plan step 3.

Unlike test_run.py's end-to-end fixture (real corruption fed through the whole
solve), these tests hand-craft `energies` directly and call
combination_differences functions in isolation — the residual/cutoff boundary
is exact here, not blurred by the least-squares solve redistributing a
corrupted edge's error across the rest of the network.
"""

import pytest

from marvel5.combination_differences import (
    DEFAULT_CUTOFF,
    backfill_and_flag,
    flag_levels,
    resolve_uncertainty,
)
from marvel5.parse import UNC_FLOOR, Transition


def _t(transition_id, freq, orig_unc, upper="X 1", lower="X 0", **kw) -> Transition:
    return Transition(
        transition_id=transition_id, iso="X", freq=freq, orig_unc=orig_unc,
        upper=upper, lower=lower, upper_qn=(), lower_qn=(), tag=transition_id, **kw)


def test_resolve_uncertainty_priority():
    """user_removed > negative_freq_excluded > no_uncertainty_excluded > none."""
    both = _t("t1", 10.0, 0.1, user_removed=True)
    both.freq = -1.0
    resolve_uncertainty(both)
    assert both.removed_reason == "user_removed"

    neg = _t("t2", -5.0, 0.1)
    resolve_uncertainty(neg)
    assert neg.removed_reason == "negative_freq_excluded"

    nounc = _t("t3", 10.0, None)
    resolve_uncertainty(nounc)
    assert nounc.removed_reason == "no_uncertainty_excluded"

    clean = _t("t4", 10.0, 0.1)
    resolve_uncertainty(clean)
    assert clean.removed is False and clean.removed_reason is None


@pytest.mark.parametrize("ratio, expect_flag", [
    (DEFAULT_CUTOFF - 0.5, False),
    (DEFAULT_CUTOFF + 0.5, True),
])
def test_backfill_flags_across_cutoff_boundary(ratio, expect_flag):
    unc = 0.01
    residual = ratio * unc
    t = _t("t_bad", freq=10.0 + residual, orig_unc=unc)
    resolve_uncertainty(t)
    energies = {"X 1": 10.0, "X 0": 0.0}  # calc = 10.0, so residual is exactly `residual`

    backfill_and_flag([t], energies, cutoff=DEFAULT_CUTOFF)

    assert t.residual == pytest.approx(residual)
    assert bool(t.consistency_flag) is expect_flag


def test_backfill_no_uncertainty_excluded_is_never_flagged():
    t = _t("t_nounc", freq=999.0, orig_unc=None)  # huge disagreement with the solved network
    resolve_uncertainty(t)
    assert t.removed_reason == "no_uncertainty_excluded"

    backfill_and_flag([t], {"X 1": 10.0, "X 0": 0.0}, cutoff=DEFAULT_CUTOFF)

    assert t.uncertainty_source == "backfilled"
    assert t.uncertainty_used == pytest.approx(max(abs(999.0 - 10.0), UNC_FLOOR))
    assert bool(t.consistency_flag) is False


def test_flag_levels_isolates_corruption_to_its_own_transitions():
    """One flagged transition pulls in both its endpoints; an unrelated clean
    transition elsewhere in the same component stays untouched."""
    bad = _t("t_bad", freq=10.0 + 100 * 0.01, orig_unc=0.01, upper="X 1", lower="X 0")
    clean = _t("t_clean", freq=5.0, orig_unc=0.01, upper="X 2", lower="X 0")
    for t in (bad, clean):
        resolve_uncertainty(t)

    energies = {"X 0": 0.0, "X 1": 10.0, "X 2": 5.0}
    backfill_and_flag([bad, clean], energies, cutoff=DEFAULT_CUTOFF)

    assert bool(bad.consistency_flag) is True
    assert bool(clean.consistency_flag) is False
    assert flag_levels([bad, clean]) == {"X 1", "X 0"}
