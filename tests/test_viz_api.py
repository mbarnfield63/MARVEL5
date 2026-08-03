"""End-to-end check of the viz backend REST surface against a synthetic file."""

from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from marvel5.viz import api

MRT = """\
Title: synthetic test data
--------------------------------------------------------------------------------
IsoA 01     10.0        0.001  0   1  0   0 t1
IsoA 01     11.0        0.001  0   2  0   1 t2
IsoA 01     12.0        0.001  0   3  0   2 t3
"""


@pytest.fixture()
def client(tmp_path: Path):
    api._run = None  # each test gets a clean global project slot
    return TestClient(api.app)


def test_load_solve_edit_rerun_export(client: "TestClient", tmp_path: Path):
    path = tmp_path / "synthetic.mrt"
    path.write_text(MRT)

    r = client.post("/project/load", json={"path": str(path), "bootstrap_iterations": 10})
    assert r.status_code == 200
    assert r.json() == {"run_name": "synthetic", "n_levels": 4, "n_transitions": 3}

    levels = client.get("/project/levels").json()
    assert {lvl["level_id"] for lvl in levels} == {"IsoA 0 0", "IsoA 0 1", "IsoA 0 2", "IsoA 0 3"}

    r = client.post("/project/transitions/IsoA:t1/uncertainty", json={"value": 0.5})
    assert r.status_code == 200

    r = client.post("/project/transitions/IsoA:missing/remove")
    assert r.status_code == 404

    r = client.post("/project/rerun", json={"bootstrap_iterations": 10})
    assert r.status_code == 200

    transitions = {t["transition_id"]: t for t in client.get("/project/transitions").json()}
    assert transitions["IsoA:t1"]["uncertainty_source"] == "user_edited"
    assert transitions["IsoA:t1"]["uncertainty_used"] == pytest.approx(0.5)

    r = client.post("/project/export", json={"output_dir": str(tmp_path / "out")})
    assert r.status_code == 200
    assert (tmp_path / "out" / "synthetic_levels.csv").exists()


def test_endpoints_require_loaded_project(client: "TestClient"):
    assert client.get("/project/levels").status_code == 404
