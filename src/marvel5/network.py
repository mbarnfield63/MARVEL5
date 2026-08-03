"""Spectroscopic-network decomposition: connected components over level_ids.

Isotopologues never share a level_id (parse.py prefixes it), so components
never merge across isotopologues without any special-casing here.
"""

import networkx as nx


def split_components(transitions: list) -> list[list]:
    """Group transitions into connected components, largest first.

    Considers every transition passed in (weighted or not) — components must
    include unweighted edges too, or the solver and combination-differences
    step could disagree about which levels are actually reachable together.
    """
    g = nx.Graph()
    for i, t in enumerate(transitions):
        g.add_edge(t.upper, t.lower, idx=i)

    components = []
    for nodes in sorted(nx.connected_components(g), key=len, reverse=True):
        components.append([t for t in transitions if t.upper in nodes])
    return components
