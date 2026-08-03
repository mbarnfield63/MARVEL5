import type { Level } from "./api";

export function LevelsTable({
  levels,
  selectedLevel,
  onSelect,
}: {
  levels: Level[];
  selectedLevel: string | null;
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
        </tr>
      </thead>
      <tbody>
        {levels.map((lvl) => (
          <tr
            key={lvl.level_id}
            className={
              (lvl.consistency_flag ? "row-flagged " : "") +
              (lvl.level_id === selectedLevel ? "row-selected" : "")
            }
            onClick={() => onSelect(lvl.level_id)}
          >
            <td>{lvl.level_id}</td>
            <td>{lvl.energy.toFixed(6)}</td>
            <td>{lvl.uncertainty.toFixed(6)}</td>
            <td>{lvl.n_transitions}</td>
            <td>{lvl.network_id}</td>
            <td>{lvl.consistency_flag ? "⚠" : ""}</td>
          </tr>
        ))}
      </tbody>
    </table>
  );
}
