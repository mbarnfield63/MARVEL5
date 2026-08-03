"""MRT (CDS machine-readable table) transition-file parsing.

QN-count-oblivious: the line layout is `Iso Name freq unc <upper QNs> <lower
QNs> Tag`, and the QN split point is inferred per-line as an even split of
the tokens between `unc` and `Tag` — works for diatomics (2 QN each) and
polyatomics alike without a molecule-specific schema.
"""

from dataclasses import dataclass
from pathlib import Path

UNC_FLOOR = 1e-6  # cm-1, floor applied to zero/backfilled uncertainties


@dataclass
class Transition:
    transition_id: str  # "{iso}:{tag}", unique
    iso: str
    freq: float          # observed wavenumber, cm-1 (signed)
    orig_unc: float | None  # stated uncertainty, cm-1; None if unparsable/absent
    upper: str            # upper level_id
    lower: str             # lower level_id
    upper_qn: tuple[str, ...]
    lower_qn: tuple[str, ...]
    tag: str

    # user edits, persist across MarvelRun.rerun()
    user_removed: bool = False
    user_unc: float | None = None

    # derived state, recomputed fresh by every MarvelRun.solve()/rerun()
    removed: bool = False
    removed_reason: str | None = None  # worst_offender | user_removed | no_uncertainty_excluded | None
    uncertainty_used: float | None = None
    uncertainty_altered: bool = False
    uncertainty_source: str = "original"  # original | backfilled | user_edited
    consistency_flag: bool = False
    residual: float | None = None  # Delta = obs - calc


def _level_id(iso: str, qn: tuple[str, ...]) -> str:
    return f"{iso} {' '.join(qn)}"


def _mrt_data_lines(path) -> list[str]:
    lines = Path(path).read_text().splitlines()
    dividers = [i for i, l in enumerate(lines) if l.startswith("-" * 40)]
    return lines[dividers[-1] + 1:] if dividers else lines


def parse_mrt_transitions(path) -> list[Transition]:
    """Parse a CDS MRT transitions table. Returns a flat list of Transitions."""
    out = []
    for line in _mrt_data_lines(path):
        tokens = line.split()
        if not tokens:
            continue
        iso, freq_s, unc_s, tag = tokens[0], tokens[2], tokens[3], tokens[-1]
        qn_tokens = tokens[4:-1]
        nqn = len(qn_tokens) // 2
        upper_qn, lower_qn = tuple(qn_tokens[:nqn]), tuple(qn_tokens[nqn:])

        try:
            unc = float(unc_s)
            if unc == 0.0:
                unc = None
        except ValueError:
            unc = None  # e.g. "REQUIRES" from an unresolved MARVEL_scraping row

        out.append(Transition(
            transition_id=f"{iso}:{tag}",
            iso=iso,
            freq=float(freq_s),
            orig_unc=unc,
            upper=_level_id(iso, upper_qn),
            lower=_level_id(iso, lower_qn),
            upper_qn=upper_qn,
            lower_qn=lower_qn,
            tag=tag,
        ))
    return out
