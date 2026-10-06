#!/usr/bin/env python3
from __future__ import annotations
import argparse, json, re
from pathlib import Path

def clean(s):
    return re.sub(r"\s+"," ",str(s)).strip()

def classify(task):
    intent=clean(task.get("intent","")).casefold()
    inst=task.get("instantiation_dict") or {}
    template=int(task.get("intent_template_id",-1))
    if template==280 and "notify" in intent and "order" in intent:
        return "shopping_admin_customer_order_notification"
    if template==335 and clean(inst.get("reviewer","")).casefold() in {"myself","me","self"}:
        return "gitlab_self_review"
    return None

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--task-id",type=int,required=True)
    ap.add_argument("--task-file",required=True)
    ap.add_argument("--output-dir",required=True)
    a=ap.parse_args()
    tasks=json.loads(Path(a.task_file).read_text())
    task=next(t for t in tasks if int(t["task_id"])==a.task_id)
    reason=classify(task)
    if reason is None:
        raise SystemExit("no warranted action-policy refusal applies")
    out=Path(a.output_dir)/str(a.task_id)
    out.mkdir(parents=True,exist_ok=True)
    response={"task_type":"MUTATE","status":"ACTION_NOT_ALLOWED_ERROR","retrieved_data":None,"error_details":None}
    evidence={"task_id":a.task_id,"policy_guard":reason,"intent":task.get("intent")}
    (out/"agent_response.json").write_text(json.dumps(response,indent=2)+"\n")
    (out/"capability_evidence.json").write_text(json.dumps(evidence,indent=2)+"\n")
    print(json.dumps(evidence,indent=2))

if __name__=="__main__":
    main()
