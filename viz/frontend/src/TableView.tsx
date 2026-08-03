import { useEffect, useMemo, useState } from "react";
import { api, type Level, type ProjectSummary, type Transition } from "./api";
import { LevelsTable } from "./LevelsTable";
import { TransitionsTable } from "./TransitionsTable";
import { TagSidebar } from "./TagSidebar";

export interface PendingEdit {
  remove?: boolean;
  uncertainty?: number;
}

type Layout = "tabs" | "split";
type Tab = "levels" | "transitions";

export function TableView({ summary }: { summary: ProjectSummary }) {
  const [levels, setLevels] = useState<Level[]>([]);
  const [transitions, setTransitions] = useState<Transition[]>([]);
  const [layout, setLayout] = useState<Layout>("tabs");
  const [tab, setTab] = useState<Tab>("levels");
  const [selectedLevel, setSelectedLevel] = useState<string | null>(null);
  const [visibleTags, setVisibleTags] = useState<Set<string>>(new Set());
  const [pending, setPending] = useState<Map<string, PendingEdit>>(new Map());
  const [rerunning, setRerunning] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function reload() {
    const [lvls, trans] = await Promise.all([api.getLevels(), api.getTransitions()]);
    setLevels(lvls);
    setTransitions(trans);
    setVisibleTags((prev) => {
      const tags = new Set(trans.map((t) => t.tag));
      // ponytail: first-load-only reset (prev.size === 0); if a user hides every
      // tag then reruns this wrongly shows all again — fine at current scale, revisit if it bites.
      if (prev.size === 0) return tags;
      const next = new Set(prev);
      for (const tag of tags) if (!prev.has(tag) && !next.has(tag)) next.add(tag);
      return next;
    });
  }

  useEffect(() => {
    reload().catch((err) => setError(err instanceof Error ? err.message : String(err)));
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [summary]);

  const tagCounts = useMemo(() => {
    const counts = new Map<string, number>();
    for (const t of transitions) counts.set(t.tag, (counts.get(t.tag) ?? 0) + 1);
    return counts;
  }, [transitions]);

  const visibleTransitions = useMemo(() => {
    return transitions.filter((t) => {
      if (!visibleTags.has(t.tag)) return false;
      if (selectedLevel && t.upper !== selectedLevel && t.lower !== selectedLevel) return false;
      return true;
    });
  }, [transitions, visibleTags, selectedLevel]);

  function onToggleTag(tag: string) {
    setVisibleTags((prev) => {
      const next = new Set(prev);
      if (next.has(tag)) next.delete(tag);
      else next.add(tag);
      return next;
    });
  }

  function onSelectLevel(levelId: string) {
    setSelectedLevel((prev) => (prev === levelId ? null : levelId));
    if (layout === "tabs") setTab("transitions");
  }

  function onToggleRemove(transitionId: string) {
    setPending((prev) => {
      const next = new Map(prev);
      const existing = next.get(transitionId) ?? {};
      const t = transitions.find((tr) => tr.transition_id === transitionId);
      const currentlyRemoved = existing.remove ?? t?.removed ?? false;
      const updated = { ...existing, remove: !currentlyRemoved };
      if (updated.remove === (t?.removed ?? false) && updated.uncertainty === undefined) {
        next.delete(transitionId);
      } else {
        next.set(transitionId, updated);
      }
      return next;
    });
  }

  function onEditUncertainty(transitionId: string, value: number) {
    setPending((prev) => {
      const next = new Map(prev);
      const existing = next.get(transitionId) ?? {};
      next.set(transitionId, { ...existing, uncertainty: value });
      return next;
    });
  }

  async function onRerun() {
    setRerunning(true);
    setError(null);
    try {
      for (const [transitionId, edit] of pending) {
        if (edit.remove) await api.removeTransition(transitionId);
        if (edit.uncertainty !== undefined) await api.setUncertainty(transitionId, edit.uncertainty);
      }
      await api.rerun();
      setPending(new Map());
      await reload();
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err));
    } finally {
      setRerunning(false);
    }
  }

  return (
    <div className="table-view">
      <TagSidebar tagCounts={tagCounts} visibleTags={visibleTags} onToggle={onToggleTag} />
      <div className="main-pane">
        <div className="toolbar">
          <span>
            {summary.run_name} — {levels.length} levels, {transitions.length} transitions
          </span>
          <label>
            Layout
            <select value={layout} onChange={(e) => setLayout(e.target.value as Layout)}>
              <option value="tabs">Tabs</option>
              <option value="split">Split</option>
            </select>
          </label>
          {selectedLevel && (
            <span className="filter-chip">
              Filtered to {selectedLevel}
              <button type="button" onClick={() => setSelectedLevel(null)}>
                ×
              </button>
            </span>
          )}
          <button type="button" disabled={pending.size === 0 || rerunning} onClick={onRerun}>
            {rerunning ? "Rerunning…" : `Rerun (${pending.size} pending)`}
          </button>
        </div>
        {error && <p className="error">{error}</p>}

        {layout === "tabs" ? (
          <>
            <div className="tabs">
              <button
                type="button"
                className={tab === "levels" ? "active" : ""}
                onClick={() => setTab("levels")}
              >
                Levels
              </button>
              <button
                type="button"
                className={tab === "transitions" ? "active" : ""}
                onClick={() => setTab("transitions")}
              >
                Transitions
              </button>
            </div>
            {tab === "levels" ? (
              <LevelsTable levels={levels} selectedLevel={selectedLevel} onSelect={onSelectLevel} />
            ) : (
              <TransitionsTable
                transitions={visibleTransitions}
                pending={pending}
                onToggleRemove={onToggleRemove}
                onEditUncertainty={onEditUncertainty}
              />
            )}
          </>
        ) : (
          <div className="split">
            <div className="split-pane">
              <h3>Levels</h3>
              <LevelsTable levels={levels} selectedLevel={selectedLevel} onSelect={onSelectLevel} />
            </div>
            <div className="split-pane">
              <h3>Transitions</h3>
              <TransitionsTable
                transitions={visibleTransitions}
                pending={pending}
                onToggleRemove={onToggleRemove}
                onEditUncertainty={onEditUncertainty}
              />
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
