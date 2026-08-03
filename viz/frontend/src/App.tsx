import { useState } from "react";
import type { ProjectSummary } from "./api";
import { LoadForm } from "./LoadForm";
import { TableView } from "./TableView";
import "./App.css";

function App() {
  const [summary, setSummary] = useState<ProjectSummary | null>(null);

  return summary ? <TableView summary={summary} /> : <LoadForm onLoaded={setSummary} />;
}

export default App;
