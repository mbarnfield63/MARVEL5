import { useState } from "react";
import { api, type ProjectSummary } from "./api";

export function LoadForm({ onLoaded }: { onLoaded: (summary: ProjectSummary) => void }) {
  const [path, setPath] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!path.trim()) return;
    setLoading(true);
    setError(null);
    try {
      const summary = await api.loadProject(path.trim());
      onLoaded(summary);
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err));
    } finally {
      setLoading(false);
    }
  }

  return (
    <form className="load-form" onSubmit={handleSubmit}>
      <h1>MARVEL5</h1>
      <label>
        MRT input file path
        <input
          type="text"
          value={path}
          onChange={(e) => setPath(e.target.value)}
          placeholder="C:\path\to\input.mrt"
          disabled={loading}
        />
      </label>
      <button type="submit" disabled={loading || !path.trim()}>
        {loading ? "Solving…" : "Load & Solve"}
      </button>
      {error && <p className="error">{error}</p>}
    </form>
  );
}
