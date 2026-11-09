"""C82b post-process: exact source-owned failed-root reentry cost evidence.

Read only; C82 trial pins unchanged original source/verdicts. Owner measurements
are *local counter deltas* and not asserted independent cost savings: nesting,
owner replenishment and overlapping scopes prevent summing them as speedups.
"""
from pathlib import Path
import json,hashlib

original=json.loads(Path("reports/c82.json").read_text())
rows=[]
for arm in original["rows"]:
    budget=arm["budget"]
    resume=arm["resume"]
    label=f"{budget}-{'resume' if resume else 'baseline'}"
    path=Path("reports/c82-"+label+".stderr")
    lines=path.read_text(errors="replace").splitlines()
    events=[]
    for line in lines:
        if line.startswith("NUCLEUS_C82B_ENTER:"):
            events.append(dict(kind="enter",**json.loads(line.split(":",1)[1])))
        elif line.startswith("NUCLEUS_C82B_FAIL:"):
            events.append(dict(kind="failure",**json.loads(line.split(":",1)[1])))
    enters=[e for e in events if e["kind"]=="enter"]
    failures=[e for e in events if e["kind"]=="failure"]
    summary=arm["summary"]
    assert len(enters)==summary["entries"],(label,len(enters),summary)
    assert len(failures)==summary["c50_failure_site_events"],(label,len(failures),summary)
    seen_enter={}
    seen_fail={}
    first_failure_costs=[]
    retried=[]
    for i,e in enumerate(events):
        slot=e["exact_key_slot"]
        if slot is None:
            continue
        if e["kind"]=="enter":
            if e["previously_failed"]:
                prior=seen_fail.get(slot)
                retried.append({
                    "key_slot":slot,
                    "entry_seq":e["seq"],
                    "prior_failed_stage":prior["stage"] if prior else None,
                    "prior_failed_owner_remaining":prior["owner_remaining"] if prior else None,
                    "retry_effective_allowance":e["effective_allowance"],
                    "retry_incoming_owner":e["incoming_owner"],
                })
            seen_enter[slot]=e
        else:
            prior=seen_enter.get(slot)
            if prior is not None and e["owner_remaining"] is not None:
                spent=max(0,prior["effective_allowance"]-e["owner_remaining"])
                first_failure_costs.append({
                    "key_slot":slot,"failed_stage":e["stage"],
                    "entry_effective_allowance":prior["effective_allowance"],
                    "owner_remaining_on_failure":e["owner_remaining"],
                    "local_owner_decrease_before_failure":spent,
                    "nested_or_overlapping_work_possible":True,
                })
            seen_fail[slot]=e
    assert len(retried)==summary["exact_failed_then_retried"],(label,retried,summary)
    rows.append({
        "budget":budget,"resume":resume,"original_verdict":arm["verdict"],
        "owner_event_count":len(events),"retry_events":retried,
        "entry_to_failure_local_deltas":first_failure_costs,
        "events":events,
        "stderr_sha256":hashlib.sha256(path.read_bytes()).hexdigest(),
    })
    print("C82B_COST_ARM="+json.dumps({
        "budget":budget,"resume":resume,"verdict":arm["verdict"],
        "retries_after_failure":len(retried),
        "measured_deltas":[x["local_owner_decrease_before_failure"] for x in first_failure_costs],
    },sort_keys=True),flush=True)
out={
 "experiment":"C82b local owner costs at exact previously-failed root reentries",
 "parent_c82_source_branch":"research/nucleus-c82-exact-retry-census-20261109",
 "original_source_sha256":original["original_sha256"],
 "original_source_unchanged":True,
 "selected_checker_changed":False,
 "diagnostics_only":True,
 "new_proof_rules":False,
 "continuation_implemented":False,
 "standard_original_accepts":0,
 "protected_403_not_run":True,
 "interpretation":"Local owner decreases are not independently attributable speedups under nested/shared scopes.",
 "rows":rows,
}
Path("reports/c82b.json").write_text(json.dumps(out,indent=2,sort_keys=True)+"\n")
