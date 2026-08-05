import pytest

from marvel5.parse import Transition
from marvel5.solver import solve_energies


def _t(tag: str, upper: str, lower: str, freq: float = 10.0, unc: float = 0.01) -> Transition:
    return Transition(
        transition_id=f"X:{tag}", iso="X", freq=freq, orig_unc=unc,
        upper=upper, lower=lower, upper_qn=(), lower_qn=(), tag=tag,
        uncertainty_used=unc,
    )


def test_disconnected_weighted_subgraph_raises():
    """network.split_components() groups by ALL transitions (weighted + not),
    so a component's *weighted* subset alone can still be disconnected —
    e.g. bridged only by an unweighted transition. Must fail loudly instead
    of silently returning garbage energies for the orphaned half."""
    transitions = [_t("a", "X 1", "X 0"), _t("b", "X 3", "X 2")]
    with pytest.raises(ValueError):
        solve_energies(transitions)
