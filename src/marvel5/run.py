"""MarvelRun: the public stateful session API.

    run = MarvelRun.from_file("input.mrt")
    run.solve()
    run.remove_transition(transition_id)
    run.set_uncertainty(transition_id, value)
    run.rerun()
    run.levels        # list[dict], matches levels.csv schema
    run.transitions    # list[dict], matches transitions.csv schema
    run.write_output(output_dir)
"""

from dataclasses import dataclass
from pathlib import Path

from .combination_differences import DEFAULT_CUTOFF, backfill_and_flag, flag_levels, resolve_uncertainty
from .network import split_components
from .output import write_output as _write_output
from .parse import parse_mrt_transitions
from .uncertainty import solve_with_uncertainty


@dataclass
class Level:
    level_id: str
    energy: float
    uncertainty: float
    consistency_flag: bool
    n_transitions: int
    network_id: int
    unverified: bool = False  # component is tree-shaped (dof == 0): no combination-differences redundancy


class MarvelRun:
    def __init__(self, transitions: list, run_name: str = "marvel"):
        self._transitions = {t.transition_id: t for t in transitions}
        self._levels: dict[str, Level] = {}
        self.run_name = run_name
        self.solved = False

    @classmethod
    def from_file(cls, path) -> "MarvelRun":
        path = Path(path)
        return cls(parse_mrt_transitions(path), run_name=path.stem)

    def solve(self, bootstrap_iterations: int = 100, cutoff: float = DEFAULT_CUTOFF) -> "MarvelRun":
        for t in self._transitions.values():
            resolve_uncertainty(t)

        network_transitions = [t for t in self._transitions.values() if not t.user_removed]
        components = split_components(network_transitions)

        self._levels = {}
        for network_id, comp in enumerate(components):
            weighted = [t for t in comp if not t.removed]
            energies = {}
            if weighted:
                for level_id, (energy, unc) in solve_with_uncertainty(weighted, bootstrap_iterations).items():
                    energies[level_id] = energy
                    self._levels[level_id] = Level(level_id, energy, unc, False, 0, network_id)
                # dof = weighted edges - (levels - 1); tree (dof == 0) means no
                # cycle to cross-check against, so nothing in the component is
                # independently verified by combination differences.
                dof = len(weighted) - (len(energies) - 1)
                unverified = dof == 0
                for level_id in energies:
                    self._levels[level_id].unverified = unverified
                for t in comp:
                    t.unverified = unverified
            backfill_and_flag(comp, energies, cutoff)

        flagged = flag_levels(network_transitions)
        counts: dict[str, int] = {}
        for t in network_transitions:
            if not t.removed:
                counts[t.upper] = counts.get(t.upper, 0) + 1
                counts[t.lower] = counts.get(t.lower, 0) + 1
        for level_id, level in self._levels.items():
            level.n_transitions = counts.get(level_id, 0)
            level.consistency_flag = level_id in flagged

        self.solved = True
        return self

    def rerun(self, bootstrap_iterations: int = 100, cutoff: float = DEFAULT_CUTOFF) -> "MarvelRun":
        """Re-solve with current edits. No re-parse — same transitions, fresh derived state."""
        return self.solve(bootstrap_iterations, cutoff)

    def remove_transition(self, transition_id: str) -> None:
        self._transitions[transition_id].user_removed = True

    def set_uncertainty(self, transition_id: str, value: float) -> None:
        self._transitions[transition_id].user_unc = value

    @property
    def levels(self) -> list[dict]:
        return [
            {
                "level_id": lvl.level_id,
                "energy": lvl.energy,
                "uncertainty": lvl.uncertainty,
                "consistency_flag": lvl.consistency_flag,
                "n_transitions": lvl.n_transitions,
                "network_id": lvl.network_id,
                "unverified": lvl.unverified,
            }
            for lvl in sorted(self._levels.values(), key=lambda x: x.level_id)
        ]

    @property
    def transitions(self) -> list[dict]:
        return [
            {
                "transition_id": t.transition_id,
                "iso": t.iso,
                "tag": t.tag,
                "freq": t.freq,
                "upper": t.upper,
                "lower": t.lower,
                "upper_qn": " ".join(t.upper_qn),
                "lower_qn": " ".join(t.lower_qn),
                "orig_unc": t.orig_unc,
                "removed": t.removed,
                "removed_reason": t.removed_reason,
                "uncertainty_used": t.uncertainty_used,
                "uncertainty_altered": t.uncertainty_altered,
                "uncertainty_source": t.uncertainty_source,
                "consistency_flag": t.consistency_flag,
                "residual": t.residual,
                "unverified": t.unverified,
            }
            for t in sorted(self._transitions.values(), key=lambda x: x.transition_id)
        ]

    def write_output(self, output_dir) -> None:
        _write_output(output_dir, self.run_name, self.levels, self.transitions)
