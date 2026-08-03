"""Writes levels.csv / transitions.csv from MarvelRun.levels / .transitions."""

import csv
from pathlib import Path

LEVELS_FIELDS = ["level_id", "energy", "uncertainty", "consistency_flag", "n_transitions", "network_id"]
TRANSITIONS_FIELDS = [
    "transition_id", "iso", "tag", "freq", "upper_qn", "lower_qn", "orig_unc",
    "removed", "removed_reason", "uncertainty_used", "uncertainty_altered",
    "uncertainty_source", "consistency_flag", "residual",
]


def _write_csv(path: Path, fieldnames: list[str], rows: list[dict]) -> None:
    with open(path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def write_output(output_dir, run_name: str, levels: list[dict], transitions: list[dict]) -> None:
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    _write_csv(output_dir / f"{run_name}_levels.csv", LEVELS_FIELDS, levels)
    _write_csv(output_dir / f"{run_name}_transitions.csv", TRANSITIONS_FIELDS, transitions)
