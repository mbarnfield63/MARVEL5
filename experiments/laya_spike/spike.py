"""Laya spike: load the English checkpoint from a pre-fetched cache with no network, ask one choice question.

Pass = the checkpoint loads under HF_HUB_OFFLINE=1, the answer is one of the options, and the
probabilities form a distribution. Whether the answer is *right* is not tested here (base model,
no fine-tune); it is printed so step 3 has a baseline to compare against.
"""

import json
import os
import time

import torch
from laya import Router

assert os.environ.get("HF_HUB_OFFLINE") == "1", "spike must prove the offline load path"

STATE = (
    "Source 2003SmPeDe, FTS, resolution 0.002 cm-1, stated uncertainty 0.0005 cm-1. "
    "Transition 12C16O v=2-0 R(10) at 4294.0412 cm-1. "
    "Weighted least-squares residual after inserting this source: 0.0310 cm-1 (62 times the stated uncertainty). "
    "Combination-difference residual with 2003SmPeDe P(12): 0.0298 cm-1. "
    "Per-band J-fit residual: 0.0301 cm-1. Not a bridge; both levels have degree 6."
)
QUESTIONS = {
    "outlier": {
        "type": "choice",
        "instructions": "Should this measured transition be kept in the spectroscopic network?",
        "criteria": {
            "accept": "residuals are within a few times the stated uncertainty",
            "flag as outlier": "residuals are many times the stated uncertainty and agree across independent checks",
            "needs review": "the evidence conflicts or is insufficient to decide",
        },
    }
}

print(f"torch {torch.__version__}, cuda available: {torch.cuda.is_available()}")
if torch.cuda.is_available():
    sm = "sm_%d%d" % torch.cuda.get_device_capability(0)
    print(f"GPU {torch.cuda.get_device_name(0)} ({sm}), torch built for {torch.cuda.get_arch_list()}")
    assert sm in torch.cuda.get_arch_list(), f"torch wheel has no kernels for {sm}; change the torch index in pyproject.toml"
router = Router(device="cuda" if torch.cuda.is_available() else "cpu")

t0 = time.perf_counter()
result = router.predict(STATE, QUESTIONS)
t_first = time.perf_counter() - t0
t0 = time.perf_counter()
router.predict(STATE, QUESTIONS)
t_warm = time.perf_counter() - t0

ans = result["answers"]["outlier"]
print(json.dumps({"routing": result["routing"], "revisions": router.loaded_revisions, "answer": ans}, indent=2, default=str))
print(f"first call (incl. load) {t_first:.2f} s, warm call {t_warm * 1000:.1f} ms")

assert ans["choice"] in QUESTIONS["outlier"]["criteria"]
assert abs(sum(ans["probabilities"].values()) - 1) < 1e-3, ans["probabilities"]
print("SPIKE PASS")
