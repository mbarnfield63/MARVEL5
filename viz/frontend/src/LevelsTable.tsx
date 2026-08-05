import type { Level } from "./api";

export function LevelsTable({
  levels,
  selectedLevel,
  flagReasons,
  onSelect,
}: {
  levels: Level[];
  selectedLevel: string | null;
  flagReasons: Map<string, string[]>;
  onSelect: (levelId: string) => void;
}) {
  return (
    <table className="data-table">
      <thead>
        <tr>
          <th>Level ID</th>
          <th>Energy</th>
          <th>Uncertainty</th>
          <th># Transitions</th>
          <th>Network</th>
          <th>Flag</th>
          <th>Unverified</th>
        </tr>
      </thead>
      <tbody>
        {levels.map((lvl) => {
          const reasons = flagReasons.get(lvl.level_id) ?? [];
          return (
            <tr
              key={lvl.level_id}
              className={
                (lvl.consistency_flag ? "row-flagged " : "") +
                (lvl.unverified ? "row-unverified " : "") +
                (lvl.level_id === selectedLevel ? "row-selected" : "")
              }
              onClick={() => onSelect(lvl.level_id)}
            >
              <td>{lvl.level_id}</td>
              <td>{lvl.energy.toFixed(6)}</td>
              <td>{lvl.uncertainty.toFixed(6)}</td>
              <td>{lvl.n_transitions}</td>
              <td>{lvl.network_id}</td>
              <td>
                {lvl.consistency_flag && (
                  <span title={`Inconsistent with: ${reasons.join(", ")}`}>
                    ⚠ ({reasons.length})
                  </span>
                )}
              </td>
              <td>
                {lvl.unverified && (
                  <span title="Tree-shaped component: no combination-differences redundancy to cross-check against">
                    tree
                  </span>
                )}
              </td>
            </tr>
          );
        })}
      </tbody>
    </table>
  );
}
