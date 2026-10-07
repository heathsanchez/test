#!/usr/bin/env python3
from __future__ import annotations
import json
from pathlib import Path
from webarena_verified.api import WebArenaVerified
from webarena_verified.types.config import WebArenaVerifiedConfig
from webarena_verified.types.tracing import NetworkTrace

root=Path("artifacts/chollet_depth6")
wa=WebArenaVerified(config=WebArenaVerifiedConfig.from_file(root/"config.json"))
empty=NetworkTrace.model_construct(is_playwright=False,src_file=Path("<none>"),events=())

def score(group: str) -> dict:
    results={}
    for task_id in (305,306,307):
        p=root/group/str(task_id)/"agent_response.json"
        r=wa.evaluate_task(task_id=task_id,agent_response=p,network_trace=empty)
        results[str(task_id)]={"score":float(r.score),"status":r.status.value}
    return {"results":results,"success_count":sum(v["score"]==1.0 and v["status"]=="success" for v in results.values())}

frozen=json.loads((root/"f_frozen.json").read_text())
selected=score("f_selected")
ablation=score("f_ablation")
result={
    "epistemic_state":"WARRANTED_BOUNDED" if selected["success_count"]==3 and ablation["success_count"]<3 else "REJECTED",
    "experiment":"second schema-induced representation F transfer",
    "source_run":37700138868,
    "source_artifact":11517940519,
    "selected_representation":frozen["selected_representation"],
    "candidate_count":frozen["candidate_count"],
    "passing_candidate_count":frozen["passing_candidate_count"],
    "freeze_sha256":frozen["freeze_sha256"],
    "heldout":selected,
    "temporal_ablation":ablation,
}
(root/"f_qualified.json").write_text(json.dumps(result,indent=2)+"\n")
print(json.dumps(result,indent=2))
assert result["epistemic_state"]=="WARRANTED_BOUNDED",result
