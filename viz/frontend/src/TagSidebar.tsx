// Ticket #12: sidebar checklist, one row per experiment tag + transition count.
// Toggling off hides that tag's transitions entirely. View filter only — never touches the engine/data.
export function TagSidebar({
  tagCounts,
  visibleTags,
  onToggle,
}: {
  tagCounts: Map<string, number>;
  visibleTags: Set<string>;
  onToggle: (tag: string) => void;
}) {
  return (
    <aside className="tag-sidebar">
      <h3>Tags</h3>
      <ul>
        {[...tagCounts.entries()].map(([tag, count]) => (
          <li key={tag}>
            <label>
              <input
                type="checkbox"
                checked={visibleTags.has(tag)}
                onChange={() => onToggle(tag)}
              />
              {tag} <span className="tag-count">({count})</span>
            </label>
          </li>
        ))}
      </ul>
    </aside>
  );
}
