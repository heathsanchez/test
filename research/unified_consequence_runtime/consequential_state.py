"""Read-only normalization of existing qualified developmental evidence.

Does not re-run verifiers or promote historical pointers into fresh warrants.
The underlying runtime remains research.unified_consequence_runtime.integrate.
"""
from __future__ import annotations
from dataclasses import dataclass
from typing import Literal
from pathlib import Path
import json

State = Literal["WARRANTED_BOUNDED", "REJECTED", "UNKNOWN"]
@dataclass(frozen=True)
class Receipt:
    name: str
    source: str
    run: str
    status: State
    claim: str
    limitation: str

RECEIPTS = (
    Receipt("depth4", "heathsanchez/test@94116303cf81aae92251cf8caa588bc084d104dd",
            "https://github.com/heathsanchez/test/actions/runs/37585043969",
            "WARRANTED_BOUNDED", "Residual-driven synthesis, 19/19 protected",
            "Finite human-supplied semantic operator library"),
    Receipt("depth5", "heathsanchez/test@c9092fa57c8943e638f95689cd36e6a63310f41e",
            "https://github.com/heathsanchez/test/actions/runs/37699595758",
            "WARRANTED_BOUNDED", "Five-generation retained consequences 22/22",
            "One newly induced representation; no open-ended growth"),
    Receipt("mda", "heathsanchez/test@13325089c471996b8b68f46540fd4ad449df752c",
            "https://github.com/heathsanchez/test/actions/runs/38043019010",
            "WARRANTED_BOUNDED", "Dependent proof capability acquisition and 16/16 retention",
            "Role transport human-written; executable-ledger comparator ties"),
    Receipt("runtime", "heathsanchez/test@research/unified-consequence-runtime-20261013",
            "https://github.com/heathsanchez/test/actions/runs/38498825850",
            "WARRANTED_BOUNDED", "13 events, 11 live scoped capabilities, cold restart",
            "No autonomous meta-generator invention"),
    Receipt("full_system", "cross-repository",
            "", "UNKNOWN", "Prospective unified cross-model capability genesis",
            "Separate verified experiments do not constitute one integrated run"),
)

def normalized_state(receipts=RECEIPTS):
    assert len({r.name for r in receipts}) == len(receipts)
    assert all(r.status in ("WARRANTED_BOUNDED", "REJECTED", "UNKNOWN") for r in receipts)
    return {"capabilities": [r.__dict__ for r in receipts if r.status == "WARRANTED_BOUNDED"],
            "residuals": [r.__dict__ for r in receipts if r.status == "UNKNOWN"],
            "rejections": [r.__dict__ for r in receipts if r.status == "REJECTED"],
            "authority": "HISTORICAL_RECEIPTS_ONLY",
            "fresh_independent_verification": False,
            "action_authorization": "NONE"}

def withdraw(state, name):
    """Fail closed for withdrawn historical support; do not affect unrelated entries."""
    state = json.loads(json.dumps(state))
    kept = []
    for item in state["capabilities"]:
        if item["name"] == name:
            item["status"] = "UNKNOWN"
            item["limitation"] += "; support withdrawn"
            state["residuals"].append(item)
        else:
            kept.append(item)
    state["capabilities"] = kept
    return state

if __name__ == "__main__":
    print(json.dumps(normalized_state(), indent=2))
