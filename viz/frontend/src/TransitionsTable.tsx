import type { Transition } from "./api";
import type { PendingEdit } from "./TableView";

export function TransitionsTable({
  transitions,
  pending,
  onToggleRemove,
  onEditUncertainty,
}: {
  transitions: Transition[];
  pending: Map<string, PendingEdit>;
  onToggleRemove: (transitionId: string) => void;
  onEditUncertainty: (transitionId: string, value: number) => void;
}) {
  return (
    <table className="data-table">
      <thead>
        <tr>
          <th>Transition ID</th>
          <th>Tag</th>
          <th>Freq</th>
          <th>Upper</th>
          <th>Lower</th>
          <th>Uncertainty</th>
          <th>Residual</th>
          <th>Flag</th>
          <th>Unverified</th>
          <th></th>
          <th>Removed reason</th>
        </tr>
      </thead>
      <tbody>
        {transitions.map((t) => {
          const edit = pending.get(t.transition_id);
          const pendingRemoved = edit?.remove ?? t.removed;
          return (
            <tr
              key={t.transition_id}
              className={
                (t.consistency_flag ? "row-flagged " : "") +
                (t.unverified ? "row-unverified " : "") +
                (edit ? "row-pending " : "") +
                (pendingRemoved ? "row-removed" : "")
              }
            >
              <td>{t.transition_id}</td>
              <td>{t.tag}</td>
              <td>{t.freq.toFixed(6)}</td>
              <td>{t.upper}</td>
              <td>{t.lower}</td>
              <td>
                <input
                  type="number"
                  step="any"
                  defaultValue={edit?.uncertainty ?? t.uncertainty_used ?? ""}
                  onBlur={(e) => {
                    const value = parseFloat(e.target.value);
                    if (!Number.isNaN(value) && value !== t.uncertainty_used) {
                      onEditUncertainty(t.transition_id, value);
                    }
                  }}
                />
              </td>
              <td>{t.residual !== null ? t.residual.toExponential(3) : "—"}</td>
              <td>{t.consistency_flag ? "⚠" : ""}</td>
              <td>{t.unverified ? "tree" : ""}</td>
              <td>
                <button type="button" onClick={() => onToggleRemove(t.transition_id)}>
                  {pendingRemoved ? "Undo" : "Remove"}
                </button>
              </td>
              <td>{t.removed_reason ?? ""}</td>
            </tr>
          );
        })}
      </tbody>
    </table>
  );
}
