"""Shared-level cross-check: uncertainty backfill + consistency flagging.

Grounded in McKemmish et al. 2020 (MNRAS 497(1) 1081), not the original
2007/2012 papers (neither defines this algorithmically). Single post-solve
pass, no re-solve loop:

- Transitions with no usable uncertainty can't be weighted (w = 1/unc^2), so
  they're excluded from the WLS solve. Once *both* endpoint levels have a
  solved energy from the rest of the network, backfill an uncertainty from
  the residual against that solved network. They stay excluded this run
  (`removed_reason = "no_uncertainty_excluded"`) — they're advisory output,
  usable as ordinary weighted input on a future rerun.
- Every solved transition (weighted or freshly backfilled) gets a residual
  Delta = obs - calc and an offender ratio Delta/unc; over `cutoff` flags the
  transition and both endpoint levels as inconsistent.
"""

from .parse import UNC_FLOOR, Transition

DEFAULT_CUTOFF = 10.0  # 2007 paper's "stricter value"; suggested range 10-100


def resolve_uncertainty(t: Transition) -> None:
    """Reset derived uncertainty/removal state from user edits + parsed value.

    removed_reason priority: user_removed > negative_freq_excluded >
    no_uncertainty_excluded. Negative-frequency exclusion is the legacy
    MARVEL4.1.cpp convention (same one MARVEL_GNN's port applies to MRT
    tables) — confirmed necessary here against the CO oracle, where leaving
    hot-band negative-frequency lines in the weighted solve pulls every
    energy in the network off by 10^2-10^3 cm-1.
    """
    t.consistency_flag = False
    t.residual = None

    if t.user_unc is not None:
        t.uncertainty_used = t.user_unc
        t.uncertainty_altered = True
        t.uncertainty_source = "user_edited"
    elif t.orig_unc is not None:
        t.uncertainty_used = t.orig_unc
        t.uncertainty_altered = False
        t.uncertainty_source = "original"
    else:
        t.uncertainty_used = None
        t.uncertainty_altered = False
        t.uncertainty_source = "original"

    if t.user_removed:
        t.removed, t.removed_reason = True, "user_removed"
    elif t.freq < 0.0:
        t.removed, t.removed_reason = True, "negative_freq_excluded"
    elif t.uncertainty_used is None:
        t.removed, t.removed_reason = True, "no_uncertainty_excluded"
    else:
        t.removed, t.removed_reason = False, None


def backfill_and_flag(transitions: list[Transition], energies: dict[str, float],
                       cutoff: float = DEFAULT_CUTOFF) -> None:
    """Mutates each transition's residual/consistency_flag/uncertainty_used in place."""
    for t in transitions:
        if t.user_removed:
            continue  # user-removed transitions carry no solve-derived data

        e_upper, e_lower = energies.get(t.upper), energies.get(t.lower)
        if e_upper is None or e_lower is None:
            continue

        if t.removed_reason == "no_uncertainty_excluded" and t.uncertainty_source == "original":
            calc = e_upper - e_lower
            t.residual = t.freq - calc
            # ponytail: backfilled unc = |residual|, floored — the simplest reading
            # of "derive one from agreement across shared-level transitions"; makes
            # the transition non-flaggable this round by construction (it's advisory).
            t.uncertainty_used = max(abs(t.residual), UNC_FLOOR)
            t.uncertainty_source = "backfilled"
            t.consistency_flag = False
        elif not t.removed:
            t.residual = t.freq - (e_upper - e_lower)
            t.consistency_flag = bool(abs(t.residual) / t.uncertainty_used > cutoff)


def flag_levels(transitions: list[Transition]) -> set[str]:
    """Return the set of level_ids touching at least one flagged transition."""
    flagged = set()
    for t in transitions:
        if t.consistency_flag:
            flagged.add(t.upper)
            flagged.add(t.lower)
    return flagged
