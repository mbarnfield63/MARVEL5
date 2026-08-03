"""FastAPI backend wrapping one in-process MarvelRun (ticket #8's tight-coupling
decision). pywebview wraps this for the desktop distribution; same backend
gets reused for later university hosting per ticket #10.

ponytail: one global project, no session/auth model — the desktop app only
ever has one window open on one file. Add real session management if/when
university hosting needs multiple concurrent users.
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from ..run import MarvelRun

app = FastAPI(title="MARVEL5 Viz Backend")

# ponytail: wide open for local dev (desktop app + Vite dev server on
# different ports); tighten before any hosted deployment.
app.add_middleware(
    CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"],
)

_run: MarvelRun | None = None


def _require_run() -> MarvelRun:
    if _run is None:
        raise HTTPException(404, "no project loaded — POST /project/load first")
    return _run


class LoadRequest(BaseModel):
    path: str
    bootstrap_iterations: int = 100
    cutoff: float = 10.0


class UncertaintyRequest(BaseModel):
    value: float


class RerunRequest(BaseModel):
    bootstrap_iterations: int = 100
    cutoff: float = 10.0


class ExportRequest(BaseModel):
    output_dir: str


def _summary(run: MarvelRun) -> dict:
    return {"run_name": run.run_name, "n_levels": len(run.levels), "n_transitions": len(run.transitions)}


@app.post("/project/load")
def load_project(req: LoadRequest) -> dict:
    global _run
    _run = MarvelRun.from_file(req.path).solve(
        bootstrap_iterations=req.bootstrap_iterations, cutoff=req.cutoff)
    return _summary(_run)


@app.get("/project/levels")
def get_levels() -> list[dict]:
    return _require_run().levels


@app.get("/project/transitions")
def get_transitions() -> list[dict]:
    return _require_run().transitions


@app.post("/project/transitions/{transition_id}/remove")
def remove_transition(transition_id: str) -> dict:
    try:
        _require_run().remove_transition(transition_id)
    except KeyError:
        raise HTTPException(404, f"unknown transition_id: {transition_id}")
    return {"ok": True}


@app.post("/project/transitions/{transition_id}/uncertainty")
def set_uncertainty(transition_id: str, req: UncertaintyRequest) -> dict:
    try:
        _require_run().set_uncertainty(transition_id, req.value)
    except KeyError:
        raise HTTPException(404, f"unknown transition_id: {transition_id}")
    return {"ok": True}


@app.post("/project/rerun")
def rerun_project(req: RerunRequest) -> dict:
    run = _require_run()
    run.rerun(bootstrap_iterations=req.bootstrap_iterations, cutoff=req.cutoff)
    return _summary(run)


@app.post("/project/export")
def export_project(req: ExportRequest) -> dict:
    run = _require_run()
    run.write_output(req.output_dir)
    return {"ok": True, "output_dir": req.output_dir}


def run() -> None:
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)
