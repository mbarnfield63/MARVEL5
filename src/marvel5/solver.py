"""Weighted least-squares energy solve for one connected network component.

Normal equations form a weighted graph Laplacian (weight = 1/unc^2), singular
with a constant nullspace per component: pin the lowest-appearing level to 0,
solve the reduced SPD system, then shift so the minimum energy is exactly 0
(matches the network's own ground state, since that's the level with no
transitions bringing it below 0).
"""

import numpy as np
from scipy.sparse import coo_matrix
from scipy.sparse.linalg import spsolve


def level_index(transitions: list) -> dict:
    """{level_id: index} in first-appearance order."""
    idx = {}
    for t in transitions:
        for level_id in (t.upper, t.lower):
            if level_id not in idx:
                idx[level_id] = len(idx)
    return idx


def solve_energies(transitions: list, unc: list[float] | None = None) -> dict[str, float]:
    """Solve one component's weighted transitions. Returns {level_id: energy}.

    `unc` optionally overrides each transition's uncertainty, same order as
    `transitions` — used by the bootstrap to resample without mutating state.
    """
    idx = level_index(transitions)
    n = len(idx)
    if unc is None:
        unc = [t.uncertainty_used for t in transitions]

    rows, cols, vals = [], [], []
    y = np.zeros(n)
    for t, u in zip(transitions, unc):
        i, j = idx[t.upper], idx[t.lower]
        w = 1.0 / (u * u)
        rows += [i, j, i, j]
        cols += [i, j, j, i]
        vals += [w, w, -w, -w]
        y[i] += t.freq * w
        y[j] -= t.freq * w

    a = coo_matrix((vals, (rows, cols)), shape=(n, n)).tocsr()

    x = np.zeros(n)
    if n > 1:
        x[1:] = spsolve(a[1:, 1:], y[1:])
    if not np.isfinite(x).all():
        raise ValueError(
            "solve_energies: non-finite result — the weighted transitions form "
            "a disconnected subgraph (unweighted edges may bridge network.py's "
            "component, but they don't contribute to the solve)"
        )
    x -= x.min()

    return {level_id: x[i] for level_id, i in idx.items()}
