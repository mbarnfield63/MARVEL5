// Ticket #12: sidebar checklist, one row per experiment + transition count.
// A tag like "79Guelachvili.37" is one table within the "79Guelachvili" experiment;
// grouping strips the trailing ".N" so the whole experiment toggles as one unit.
// Toggling off hides every transition from that experiment entirely — view filter
// only, never touches the engine/data. Individual-transition removal stays a
// separate action in the transitions table.
export function ExperimentSidebar({
  experimentCounts,
  visibleExperiments,
  onToggle,
}: {
  experimentCounts: Map<string, number>;
  visibleExperiments: Set<string>;
  onToggle: (experiment: string) => void;
}) {
  return (
    <aside className="experiment-sidebar">
      <h3>Experiments</h3>
      <ul>
        {[...experimentCounts.entries()].map(([experiment, count]) => (
          <li key={experiment}>
            <label>
              <input
                type="checkbox"
                checked={visibleExperiments.has(experiment)}
                onChange={() => onToggle(experiment)}
              />
              {experiment} <span className="experiment-count">({count})</span>
            </label>
          </li>
        ))}
      </ul>
    </aside>
  );
}
