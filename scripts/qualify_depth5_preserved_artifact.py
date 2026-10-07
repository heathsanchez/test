#!/usr/bin/env python3
from __future__ import annotations
import json
from pathlib import Path
from webarena_verified.api import WebArenaVerified
from webarena_verified.types.config import WebArenaVerifiedConfig
from webarena_verified.types.tracing import NetworkTrace

root = Path("artifacts/chollet_depth5")
wa = WebArenaVerified(config=WebArenaVerifiedConfig.from_file(root/"config.json"))
empty = NetworkTrace.model_construct(is_playwright=False, src_file=Path("<none>"), events=())

def score(group: str, ids: tuple[int, ...]) -> dict:
    results = {}
    for task_id in ids:
        p = root/group/str(task_id)/"agent_response.json"
        r = wa.evaluate_task(task_id=task_id, agent_response=p, network_trace=empty)
        results[str(task_id)] = {"score": float(r.score), "status": r.status.value}
    return {
        "results": results,
        "success_count": sum(v["score"] == 1.0 and v["status"] == "success" for v in results.values()),
    }

A=score("a",(194,195,196,197))
B=score("b",(12,13,14,15,344,345,346,347))
C=score("c",(164,165,166,167))
D=score("d",(168,169,172))
E=score("e",(62,64,65))
counts=(A["success_count"],B["success_count"],C["success_count"],D["success_count"],E["success_count"])
result={
    "epistemic_state":"WARRANTED_BOUNDED" if counts==(4,8,4,3,3) else "REJECTED",
    "experiment":"depth5 no-revisit retention after induced grouped-count representation",
    "source_run":37587520311,
    "source_artifact":11467013627,
    "source_artifact_digest":"sha256:2a8d2792cd605e4076e6b044a957ed49c913db692b71259e5320da5494d416e8",
    "A":A,"B":B,"C":C,"D":D,"E":E,
    "training_replayed":{"A":False,"B":False,"C":False,"D":False,"E":False},
    "combined_success_count":sum(counts),
    "combined_task_count":22,
    "claims":{
        "depth5_sequential_compounding_with_representation_invention":{"state":"WARRANTED_BOUNDED" if counts==(4,8,4,3,3) else "REJECTED"},
        "open_ended_nonmath_scaling":{"state":"UNKNOWN"},
    },
}
(root/"depth5_qualified.json").write_text(json.dumps(result,indent=2)+"\n")
print(json.dumps(result,indent=2))
assert result["epistemic_state"]=="WARRANTED_BOUNDED", result
