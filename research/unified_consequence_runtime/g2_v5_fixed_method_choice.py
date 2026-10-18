#!/usr/bin/env python3
"""V5 typed choice between prequalified operations; no target-specific repair.

This code was written after V5 roles were frozen. Only the two already frozen
methods can be applied. Stop UNKNOWN if neither / both apply. The held-out
future is never inspected here; training alone never promotes G2.
"""
from __future__ import annotations
import hashlib, json, pathlib, subprocess, sys, traceback
from research.unified_consequence_runtime import g2_anyio_mutable_closure_equivalence_fix_v2 as mutable
from research.unified_consequence_runtime import residual_projection_method_v1 as projection
from research.unified_consequence_runtime import attrs_residual_observation_genesis_v1 as pcore

ROOT=pathlib.Path(__file__).resolve().parents[2]
U="research/unified_consequence_runtime/"
PINS=[
 ("mutable","094e2ddc3ba601a00eaf368151172a361e5542da",U+"g2_anyio_mutable_closure_equivalence_fix_v2.py"),
 ("projection","d83de24d3b5bb4352cd6991a85a0fbc1e72f6deb",U+"residual_projection_method_v1.py"),
 ("projection-dependency","b9d175d0b129c843bc5885aec77082f07f2b0601",U+"attrs_residual_observation_genesis_v1.py"),
]
def h(raw):return hashlib.sha256(raw).hexdigest()
def show(commit,path):
    return subprocess.check_output(["git","-C",str(ROOT),"show",commit+":"+path])
def good_pass(r):
    c=r.get("counts",{})
    return r.get("returncode")==0 and c.get("tests",0)>=1 and c.get("failures")==0 and c.get("errors")==0 and c.get("skipped")==0
def good_fail(r):
    c=r.get("counts",{})
    return r.get("returncode")==1 and c.get("failures",0)>=1 and c.get("errors")==0 and c.get("skipped")==0
def native(world,nodes,out):
    return pcore.run_pytest(world,nodes,out,timeout=120)

def main(admission,out):
    out.mkdir(parents=True,exist_ok=False)
    a=json.loads(admission.read_text())
    report={
       "schema":"UDM_G2_V5_TWO_FIXED_METHOD_NATIVE_CHOICE",
       "status":"UNKNOWN_NO_ADMITTED_TRAINING_FAILURE",
       "methods":{}, "generated_repair_count":0,
       "selected_method":None, "future":"SEALED_UNOPENED",
       "future_source":"UNOPENED","future_native":"NOT_EXECUTED",
       "G2":"UNKNOWN","G3":"UNKNOWN","G4":"UNKNOWN","G5":"UNKNOWN","G6":"UNKNOWN",
       "coding_agent":"NOT_EXECUTED","informed_ledger":"NOT_EXECUTED"
    }
    try:
        report["method_sha256"]={}
        for label,commit,path in PINS:
            data=(ROOT/path).read_bytes()
            if data!=show(commit,path):
                raise ValueError("METHOD_BYTE_FREEZE_CHANGED:"+label)
            report["method_sha256"][label]=h(data)
        role_path=U+"G2_OBSERVATION_CHOICE_V5_ROLE_FREEZE.json"
        if (ROOT/role_path).read_bytes()!=show("d96833fa8a41b4e5b67d5a9498ee1b1607c476e2",role_path):
            raise ValueError("ROLES_CHANGED_AFTER_SOURCE_ACCESS")
        selected=a.get("selected")
        if not selected:return report
        assert selected["status"]=="ADMITTED_FIRST_AUTHENTIC_PROTECTED_NATIVE_FAILURE"
        assert selected["repo"]=="pallets/flask" and selected["order"]==0
        assert good_fail(selected["native"])
        roles=json.loads((ROOT/role_path).read_text())["roles"]
        task=roles[selected["order"]]
        assert task["role"]=="TRAINING_0" and task["number"]==selected["pr"]
        world=pathlib.Path(selected["work_dir"]).resolve(strict=True)
        production=world/task["production"]
        original=production.read_bytes()
        assert h(original)==selected["source_sha256"]
        tests=world/task["author_test"]
        assert h(tests.read_bytes())==selected["head_test_sha256"]
        assert subprocess.check_output(["git","-C",str(world),"rev-parse","HEAD"],text=True).strip()==task["base"]
        nodes=selected["protected_nodes"]
        assert nodes and all(x.startswith(task["author_test"]+"::") for x in nodes)
        # Inspection is only performed now, after native admission.
        patterns=mutable.scan_patterns(task["production"],original)
        qualified=[]
        report["methods"]["mutable"]={"scan_patterns":len(patterns),"qualified_patterns":0}
        if patterns:
            obs=mutable.run_pytest(world,nodes,out/"closure-observation",patterns=patterns,timeout=120)
            assert h(production.read_bytes())==h(original),"OBSERVER_MUTATED_PRODUCTION"
            report["methods"]["mutable"]["observation_counts"]=obs["counts"]
            qualified=[row for row in patterns if mutable.trace_has_stale_capture(row,obs["trace_events"])["pass"]]
            report["methods"]["mutable"]["qualified_patterns"]=len(qualified)
        changed=[x.split("::",1)[1] for x in nodes]
        try:
            proposals=projection.propose(tests,changed,production)
            report["methods"]["projection"]={"proposals":len(proposals),
                  "observation_classes":sum(len(q["classes"]) for q in proposals)}
        except Exception as e:
            proposals=[]
            report["methods"]["projection"]={"proposals":0,"status":"UNKNOWN_PROJECTION_APPARATUS",
                 "detail":type(e).__name__+":"+str(e)[:200]}
        usable=int(bool(qualified))+int(bool(proposals))
        if usable==0:
            report["status"]="UNKNOWN_NO_APPLICABLE_QUALIFIED_METHOD"
            return report
        if usable>1:
            report["status"]="UNKNOWN_UNRESOLVED_TWO_METHOD_CHOICE"
            return report
        if qualified:
            # Qualified closure patterns are source-derived, not supplied patches.
            candidates=[("mutable",p["pattern_id"],mutable.repair_source(original,p)) for p in qualified[:8]]
        else:
            candidates=[]
            for proposal in proposals:
                rr=proposal["residual"]
                for cls in proposal["classes"][:8]:
                    candidates.append(("projection",cls["class_id"],
                        pcore.generate_repair(original,rr["classifier_name"],
                                              rr["argument_name"],cls["representative"])))
        for i,(family,key,repaired) in enumerate(candidates[:8]):
            assert repaired!=original
            report["generated_repair_count"]+=1
            row={"family":family,"observation":key,"repair_sha256":h(repaired)}
            report.setdefault("native_trials",[]).append(row)
            try:
                production.write_bytes(repaired)
                first=native(world,nodes,out/("trial-"+str(i)+"-a"))
                second=native(world,nodes,out/("trial-"+str(i)+"-b"))
                row.update(first=first,second=second)
                if not (good_pass(first) and good_pass(second)):
                    row["status"]="REJECTED_NATIVE_REPAIR"
                    continue
                production.write_bytes(original)
                withdrawn=native(world,nodes,out/("trial-"+str(i)+"-withdraw"))
                row["withdrawal"]=withdrawn
                if not good_fail(withdrawn):
                    row["status"]="UNKNOWN_NOT_CAUSAL"
                    continue
                production.write_bytes(repaired)
                restored=native(world,nodes,out/("trial-"+str(i)+"-restore"))
                row["restoration"]=restored
                if not good_pass(restored):
                    row["status"]="UNKNOWN_NOT_RESTORED"
                    continue
                row["status"]="WARRANTED_BOUNDED_TRAINING_REPAIR_ONLY"
                report["selected_method"]=family
                report["status"]="WARRANTED_BOUNDED_TRAINING_ONLY_FUTURE_SEALED"
                break
            finally:
                production.write_bytes(original)
        if report["status"]=="UNKNOWN_NO_ADMITTED_TRAINING_FAILURE":
            report["status"]="UNKNOWN_NO_VERIFIED_GENERATED_TRAINING_REPAIR"
        return report
    except Exception as e:
        report["status"]="UNKNOWN_METHOD_APPARATUS"
        report["error"]=type(e).__name__+":"+str(e)[:350]
        report["traceback_tail"]=traceback.format_exc(limit=4)[-1000:]
        return report
    finally:
        (out/"RESULT.json").write_text(json.dumps(report,indent=2,sort_keys=True,default=str)+"\n")
        print("V5_FIXED_METHOD_CHOICE",report["status"],"candidates",report["generated_repair_count"],
              "FUTURE",report["future"],"G2",report["G2"],flush=True)

if __name__=="__main__":
    if len(sys.argv)!=3:raise SystemExit("usage: g2_v5_fixed_method_choice.py ADMISSION.json OUT")
    main(pathlib.Path(sys.argv[1]).resolve(),pathlib.Path(sys.argv[2]).resolve())
