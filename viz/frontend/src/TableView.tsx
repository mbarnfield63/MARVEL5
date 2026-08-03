import { useEffect, useMemo, useState } from "react";
import { api, type Level, type ProjectSummary, type Transition } from "./api";
import { LevelsTable } from "./LevelsTable";
import { TransitionsTable } from "./TransitionsTable";
import { ExperimentSidebar } from "./ExperimentSidebar";

export interface PendingEdit {
  remove?: boolean;
  uncertainty?: number;
}

type Layout = "tabs" | "split";
type Tab = "levels" | "transitions";

// "79Guelachvili.37" -> "79Guelachvili": a tag is one table within an experiment.
function experimentOf(tag: string): string {
  return tag.replace(/\.\d+$/, "");
}

export function TableView({ summary }: { summary: ProjectSummary }) {
  const [levels, setLevels] = useState<Level[]>([]);
  const [transitions, setTransitions] = useState<Transition[]>([]);
  const [layout, setLayout] = useState<Layout>("tabs");
  const [tab, setTab] = useState<Tab>("levels");
  const [selectedLevel, setSelectedLevel] = useState<string | null>(null);
  const [visibleExperiments, setVisibleExperiments] = useState<Set<string>>(new Set());
  const [pending, setPending] = useState<Map<string, PendingEdit>>(new Map());
  const [rerunning, setRerunning] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function reload() {
    const [lvls, trans] = await Promise.all([api.getLevels(), api.getTransitions()]);
    setLevels(lvls);
    setTransitions(trans);
    setVisibleExperiments((prev) => {
      const experiments = new Set(trans.map((t) => experimentOf(t.tag)));
      // ponytail: first-load-only reset (prev.size === 0); if a user hides every
      // experiment then reruns this wrongly shows all again — fine at current scale, revisit if it bites.
      if (prev.size === 0) return experiments;
      const next = new Set(prev);
      for (const experiment of experiments) if (!prev.has(experiment)) next.add(experiment);
      return next;
    });
  }

  useEffect(() => {
    reload().catch((err) => setError(err instanceof Error ? err.message : String(err)));
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [summary]);

  const experimentCounts = useMemo(() => {
    const counts = new Map<string, number>();
    for (const t of transitions) {
      const experiment = experimentOf(t.tag);
      counts.set(experiment, (counts.get(experiment) ?? 0) + 1);
    }
    return counts;
  }, [transitions]);

  // Why a level is flagged: the ids of its own flagged transitions, for a tooltip.
  const levelFlagReasons = useMemo(() => {
    const reasons = new Map<string, string[]>();
    for (const t of transitions) {
      if (!t.consistency_flag) continue;
      for (const levelId of [t.upper, t.lower]) {
        const list = reasons.get(levelId) ?? [];
        list.push(t.transition_id);
        reasons.set(levelId, list);
      }
    }
    return reasons;
  }, [transitions]);

  const visibleTransitions = useMemo(() => {
    return transitions.filter((t) => {
      if (!visibleExperiments.has(experimentOf(t.tag))) return false;
      if (selectedLevel && t.upper !== selectedLevel && t.lower !== selectedLevel) return false;
      return true;
    });
  }, [transitions, visibleExperiments, selectedLevel]);

  function onToggleExperiment(experiment: string) {
    setVisibleExperiments((prev) => {
      const next = new Set(prev);
      if (next.has(experiment)) next.delete(experiment);
      else next.add(experiment);
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
      <ExperimentSidebar
        experimentCounts={experimentCounts}
        visibleExperiments={visibleExperiments}
        onToggle={onToggleExperiment}
      />
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
            <div className="table-scroll">
              {tab === "levels" ? (
                <LevelsTable
                  levels={levels}
                  selectedLevel={selectedLevel}
                  flagReasons={levelFlagReasons}
                  onSelect={onSelectLevel}
                />
              ) : (
                <TransitionsTable
                  transitions={visibleTransitions}
                  pending={pending}
                  onToggleRemove={onToggleRemove}
                  onEditUncertainty={onEditUncertainty}
                />
              )}
            </div>
          </>
        ) : (
          <div className="split">
            <div className="split-pane">
              <h3>Levels</h3>
              <div className="table-scroll">
                <LevelsTable
                  levels={levels}
                  selectedLevel={selectedLevel}
                  flagReasons={levelFlagReasons}
                  onSelect={onSelectLevel}
                />
              </div>
            </div>
            <div className="split-pane">
              <h3>Transitions</h3>
              <div className="table-scroll">
                <TransitionsTable
                  transitions={visibleTransitions}
                  pending={pending}
                  onToggleRemove={onToggleRemove}
                  onEditUncertainty={onEditUncertainty}
                />
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
