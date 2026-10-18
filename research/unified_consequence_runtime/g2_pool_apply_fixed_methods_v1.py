#!/usr/bin/env python3
"""Apply only previously qualified, byte-frozen methods after native admission.

Does NOT make a new repair grammar, retarget after results, access sealed future,
or promote G2 from training. Uses actual original author tests for authority.
"""
from __future__ import annotations
import hashlib,json,os,pathlib,subprocess,sys,traceback
ROOT=pathlib.Path(__file__).resolve().parents[2]
U="research/unified_consequence_runtime/"
LOCK=U+"G2_NATIVE_FIRST_FAIL_POOL_V2_ROLE_FREEZE.json"
PINS=[
 ("mutable", "094e2ddc3ba601a00eaf368151172a361e5542da",
   U+"g2_anyio_mutable_closure_equivalence_fix_v2.py"),
 ("projection", "b9d175d0b129c843bc5885aec77082f07f2b0601",
   U+"attrs_residual_observation_genesis_v1.py"),
]
def sha(b):return hashlib.sha256(b).hexdigest()
def git_show(commit,name):
    return subprocess.check_output(["git","-C",str(ROOT),"show",commit+":"+name],timeout=40)
def frozen():
    assert (ROOT/LOCK).read_bytes()==git_show("57c400ea49881e440f7895acaeebeee5854363e3",LOCK)
    signatures={}
    for label,commit,name in PINS:
        raw=(ROOT/name).read_bytes()
        if raw!=git_show(commit,name):raise ValueError("QUALIFIED_METHOD_CHANGED:"+label)
        signatures[label]=sha(raw)
    return json.loads((ROOT/LOCK).read_text()),signatures
def check_pass(r):
    c=r["counts"]
    return r["returncode"]==0 and c["tests"]>=1 and c["failures"]==0 and c["errors"]==0
def check_fail(r):
    c=r["counts"]
    return r["returncode"]==1 and c["tests"]>=1 and c["failures"]>=1 and c["errors"]==0
def controls(run,world,production,original,repaired,nodes,dest):
    attempts=[]
    try:
        (world/production).write_bytes(repaired)
        for label in ("repair-native-a","repair-native-b"):
            attempts.append((label,run(world,nodes,dest/label,timeout=120)))
        full=run(world,[nodes[0].split("::")[0]],dest/"full-author-file",timeout=120)
        verified=all(check_pass(x) for _,x in attempts) and check_pass(full)
        if not verified:
            return {"status":"REJECTED_NATIVE_REPAIR_CANDIDATE","attempts":attempts,"full_author_file":full}
        (world/production).write_bytes(original)
        withdrawn=run(world,nodes,dest/"physical-withdrawal",timeout=120)
        if not check_fail(withdrawn):
            return {"status":"UNKNOWN_WITHDRAWAL_DID_NOT_RESTORE_FAIL","attempts":attempts,"withdrawn":withdrawn}
        (world/production).write_bytes(repaired)
        restored=run(world,nodes,dest/"byte-exact-restoration",timeout=120)
        if not check_pass(restored) or sha((world/production).read_bytes())!=sha(repaired):
            return {"status":"UNKNOWN_RESTORATION_NOT_CONFIRMED","attempts":attempts,"withdrawn":withdrawn,"restored":restored}
        return {"status":"WARRANTED_BOUNDED_TRAINING_REPAIR_ONLY","attempts":attempts,"full_author_file":full,
                "withdrawn":withdrawn,"restored":restored,"source_sha256":sha(repaired)}
    finally:
        (world/production).write_bytes(original)
def main(result_path: pathlib.Path,output:pathlib.Path):
    output.mkdir(parents=True,exist_ok=False)
    admission=json.loads(result_path.read_text())
    report={"schema":"G2_FIRST_NATIVE_FAILURE_FIXED_METHOD_APPLICATION_V2",
            "status":"UNKNOWN_NO_EARNED_TRAINING_FAILURE",
            "trained_methods":[],"heldout":"SEALED_UNOPENED",
            "future_native":"NOT_EXECUTED","agent_comparator":"NOT_EXECUTED",
            "ledger_comparator":"NOT_EXECUTED","G2":"UNKNOWN","G3":"UNKNOWN",
            "G4":"UNKNOWN","G5":"UNKNOWN","G6":"UNKNOWN"}
    try:
        manifest,method_hashes=frozen()
        report["method_sha256"]=method_hashes
        selected=admission.get("selected")
        if not selected:
            return report
        assert admission["status"]=="QUALIFIED_TRAINING_FAILURE_FUTURE_SEALED"
        assert selected["status"]=="ADMITTED_FIRST_AUTHENTIC_PROTECTED_NATIVE_FAILURE"
        task=manifest["training_candidates"][selected["order"]]
        assert task["repo"]==selected["repo"] and task["pr"]==selected["pr"]
        world=pathlib.Path(selected["work_dir"]).resolve()
        production=task["production"]
        original=(world/production).read_bytes()
        assert sha(original)==selected["source_sha256"]
        nodes=selected["protected_nodes"]
        assert nodes and all(x.startswith(task["author_test"]+"::") for x in nodes)
        assert (world/task["author_test"]).read_bytes() and (
             sha((world/task["author_test"]).read_bytes())==selected["head_test_sha256"])
        assert subprocess.check_output(["git","-C",str(world),"rev-parse","HEAD"],text=True).strip()==task["base"]
        report.update(status="UNKNOWN_NO_APPLICABLE_QUALIFIED_METHOD",
                      training=task["repo"]+"#"+str(task["pr"]),
                      source_sha256=sha(original),selected_source=production)
        # Invoke the immutable, source-neutral closure observer/repair only.
        from research.unified_consequence_runtime import g2_anyio_mutable_closure_equivalence_fix_v2 as mutable
        patterns=mutable.scan_patterns(production,original)
        report["methods"]={"mutable":{"patterns":len(patterns),"status":"UNKNOWN_NO_PATTERN"},
                           "projection":{"status":"UNKNOWN_NOT_EXECUTED"}}
        if patterns:
            observed=mutable.run_pytest(world,nodes,output/"closure-observation",
                patterns=patterns,timeout=120)
            assert sha((world/production).read_bytes())==sha(original),"OBSERVER_MUTATED_SOURCE"
            report["methods"]["mutable"]["native_observation"]={
                k:observed.get(k) for k in ("returncode","counts")}
            qualifying=[p for p in patterns if mutable.trace_has_stale_capture(p,observed["trace_events"])["pass"]]
            report["methods"]["mutable"]["qualified_patterns"]=len(qualifying)
            for i,p in enumerate(qualifying[:8]):
                repaired=mutable.repair_source(original,p)
                outcome=controls(mutable.run_pytest,world,production,original,repaired,nodes,
                                 output/("mutable-"+str(i)))
                report["trained_methods"].append({"family":"mutable",
                    "pattern_id":p["pattern_id"],"result":outcome})
                if outcome["status"]=="WARRANTED_BOUNDED_TRAINING_REPAIR_ONLY":
                    report["methods"]["mutable"]["status"]="WARRANTED_BOUNDED_TRAINING_REPAIR_ONLY"
                    break
        # Unchanged attrs primitive-projection operation: its own frozen preconditions.
        # It is NOT generalized by writing a new observer or classifier selection rule.
        if not any(x["result"]["status"]=="WARRANTED_BOUNDED_TRAINING_REPAIR_ONLY" for x in report["trained_methods"]):
            from research.unified_consequence_runtime import attrs_residual_observation_genesis_v1 as projection
            try:
                direct=projection.derive_classifier_and_cases(world/task["author_test"])
                clf=direct["classifier"]
                import inspect
                file=inspect.getsourcefile(clf)
                if file is None or pathlib.Path(file).resolve()!=(world/production).resolve():
                    raise ValueError("QUALIFIED_PROJECTION_CLASSIFIER_NOT_FROM_PRODUCTION")
                base,failing,candidates,classes=projection.enumerate_projection_observations(
                    clf,direct["cases"],direct["expected"])
                report["methods"]["projection"]={"status":"SOURCE_RELATIVE_CANDIDATES",
                    "failed_cases":len(failing),"observation_classes":len(classes)}
                for group in classes[:8]:
                    repaired=projection.generate_repair(original,direct["classifier_name"],
                        direct["argument_name"],group["representative"])
                    outcome=controls(projection.run_pytest,world,production,original,repaired,nodes,
                        output/("projection-"+group["class_id"].split(":")[-1]))
                    report["trained_methods"].append({"family":"projection",
                        "class_id":group["class_id"],"result":outcome})
                    if outcome["status"]=="WARRANTED_BOUNDED_TRAINING_REPAIR_ONLY":
                        report["methods"]["projection"]["status"]="WARRANTED_BOUNDED_TRAINING_REPAIR_ONLY"
                        break
            except Exception as e:
                report["methods"]["projection"]={"status":"UNKNOWN_SOURCE_PATTERN_NOT_APPLICABLE",
                         "reason":type(e).__name__+": "+str(e)[:250]}
        good=[x for x in report["trained_methods"] if x["result"]["status"]=="WARRANTED_BOUNDED_TRAINING_REPAIR_ONLY"]
        report["status"]="WARRANTED_BOUNDED_TRAINING_ONLY_FUTURE_SEALED" if good else "UNKNOWN_NO_VERIFIED_FIXED_METHOD_TRAINING_REPAIR"
        report["applied_methods"]=len(report["trained_methods"])
        return report
    except Exception as e:
        report["status"]="UNKNOWN_METHOD_APPARATUS"
        report["error"]=type(e).__name__+": "+str(e)[:650]
        report["traceback_tail"]=traceback.format_exc(limit=8)[-2100:]
        return report
    finally:
        (output/"RESULT.json").write_text(json.dumps(report,indent=2,sort_keys=True,default=repr)+"\n")
if __name__=="__main__":
    if len(sys.argv)!=3:raise SystemExit("usage: apply_frozen_methods.py ADMISSION.json FRESH_OUT")
    r=main(pathlib.Path(sys.argv[1]).resolve(),pathlib.Path(sys.argv[2]).resolve())
    print("METHOD_GATE",r.get("status"),"FUTURE",r.get("heldout"),"G2",r.get("G2"),flush=True)
