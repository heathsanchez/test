"""Evidence-first composition of ORIGINAL qualified developmental and runtime artifacts.

No hardcoded PASS verdicts. Fail closed on missing/mismatched artifacts.
Historical source evidence is not a fresh end-to-end execution.
"""
from __future__ import annotations
import hashlib, json, zipfile
from pathlib import Path

EXPECTED = {
 "depth5": {"artifact":11517107016,"digest":"54916c29b2e89d2d922f5d6bd09273d45a4787c956340f7d6545d28cae5af73e",
            "source_run":37699595758},
 "runtime": {"artifact":11865380348,"digest":"39caaac32331e47b4ae858ee201d1a5f625f105e5b23aba8592a8e720609cef2",
             "source_run":38498825850},
}
def read_original(kind, path):
    cfg=EXPECTED[kind]
    path=Path(path)
    if hashlib.sha256(path.read_bytes()).hexdigest()!=cfg["digest"]:
        raise ValueError(f"{kind}: original archive digest mismatch")
    with zipfile.ZipFile(path) as z:
        names=z.namelist()
        if len(names)!=len(set(names)) or any(n.startswith("/") or ".." in Path(n).parts for n in names):
            raise ValueError("unsafe archive entries")
        candidates=[n for n in names if n.endswith("depth5_qualified.json" if kind=="depth5" else "closure.json")]
        if len(candidates)!=1: raise ValueError(f"{kind}: unique evidence record not found")
        return json.loads(z.read(candidates[0]))
def compose(depth5, runtime):
    if depth5.get("epistemic_state")!="WARRANTED_BOUNDED" or depth5.get("combined_success_count")!=22 or depth5.get("combined_task_count")!=22:
        raise ValueError("depth5 authority insufficient")
    if any(depth5.get("training_replayed",{}).get(k) is not False for k in "ABCDE"):
        raise ValueError("ancestor training replay not ruled out")
    if depth5.get("claims",{}).get("open_ended_nonmath_scaling",{}).get("state")!="UNKNOWN":
        raise ValueError("historical scope changed")
    flash=runtime.get("flash",{})
    if type(flash.get("events")) is not int or flash["events"] != 13:
        raise ValueError("runtime event count changed")
    if len(flash.get("active_capabilities",[]))!=11:
        raise ValueError("runtime live capability count changed")
    if runtime.get("scientific_closure")!="UNKNOWN":
        raise ValueError("runtime scientific authority changed")
    return {
      "schema":"metalogic.consequential-composition.v1",
      "evidence":{"depth5":EXPECTED["depth5"],"runtime":EXPECTED["runtime"]},
      "development":{"protected_successes":22,"protected_total":22,"no_training_replay":True},
      "runtime":{"source_events":13,"active_scoped_capabilities":11,"restart":flash.get("restart")},
      "composition_status":"HISTORICAL_EVIDENCE_JOIN_ONLY",
      "live_cross_system_capability_execution":"UNKNOWN",
      "cross_model_compilation":"UNKNOWN",
      "autonomous_meta_generator_invention":"UNKNOWN",
      "action_authorization":"NONE"}
def main():
    import argparse
    p=argparse.ArgumentParser()
    p.add_argument("--depth5",required=True)
    p.add_argument("--runtime",required=True)
    p.add_argument("--out",required=True)
    a=p.parse_args()
    result=compose(read_original("depth5",a.depth5),read_original("runtime",a.runtime))
    Path(a.out).write_text(json.dumps(result,indent=2)+"\n")
    print(json.dumps(result,indent=2))
if __name__=="__main__": main()
