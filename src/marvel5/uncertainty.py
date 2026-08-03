"""Bootstrap + Dijkstra uncertainty estimation (MARVEL4 method).

1. Shortest-path: Dijkstra from the component's ground state (min energy)
   with edge weight unc^2; a level's uncertainty is sqrt of its path distance.
2. Bootstrap: resample each transition's uncertainty as U{1..10} x orig_unc,
   re-solve, repeat; bootunc = sqrt(2) * max(|E - median|, stdev).
3. Combined: Dijkstra again, edge cost = the *target level's*
   max(shortest-path unc, bootstrap unc)^2; final unc = sqrt(distance).
"""

import math

import networkx as nx
import numpy as np

from .solver import solve_energies


def _ground_state(energies: dict[str, float]) -> str:
    return min(energies, key=energies.get)


def shortest_path_unc(transitions: list, energies: dict[str, float]) -> dict[str, float]:
    g = nx.MultiGraph()
    g.add_weighted_edges_from(
        (t.upper, t.lower, t.uncertainty_used ** 2) for t in transitions)
    dist = nx.single_source_dijkstra_path_length(g, _ground_state(energies))
    return {level_id: math.sqrt(d) for level_id, d in dist.items()}


def bootstrap_unc(transitions: list, energies: dict[str, float],
                   iterations: int = 100, rng=None) -> dict[str, float]:
    rng = np.random.default_rng(rng)
    orig = np.array([t.orig_unc for t in transitions])
    samples = {level_id: [] for level_id in energies}
    for _ in range(iterations):
        resampled = rng.integers(1, 11, len(transitions)) * orig
        for level_id, e in solve_energies(transitions, unc=resampled).items():
            samples[level_id].append(e)

    out = {}
    for level_id, s in samples.items():
        s = np.asarray(s)
        diff = abs(energies[level_id] - np.median(s))
        out[level_id] = math.sqrt(2.0) * max(diff, s.std(ddof=1))
    return out


def combined_unc(transitions: list, energies: dict[str, float],
                  sp_unc: dict[str, float], boot_unc: dict[str, float]) -> dict[str, float]:
    cost = {level_id: max(sp_unc[level_id], boot_unc[level_id]) ** 2 for level_id in energies}
    g = nx.DiGraph()
    for t in transitions:
        g.add_edge(t.lower, t.upper, weight=cost[t.upper])
        g.add_edge(t.upper, t.lower, weight=cost[t.lower])
    dist = nx.single_source_dijkstra_path_length(g, _ground_state(energies))
    return {level_id: math.sqrt(d) for level_id, d in dist.items()}


def solve_with_uncertainty(transitions: list, bootstrap_iterations: int = 100,
                            rng=None) -> dict[str, tuple[float, float]]:
    """Full treatment of one component. Returns {level_id: (energy, uncertainty)}."""
    energies = solve_energies(transitions)
    sp = shortest_path_unc(transitions, energies)
    if bootstrap_iterations:
        boot = bootstrap_unc(transitions, energies, bootstrap_iterations, rng)
        unc = combined_unc(transitions, energies, sp, boot)
    else:
        unc = sp
    return {level_id: (energies[level_id], unc[level_id]) for level_id in energies}
