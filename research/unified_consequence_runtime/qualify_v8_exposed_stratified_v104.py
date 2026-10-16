"""V8 source-exposed stratified enumeration of ORIGINAL V104 AST programs.

This diagnostic changes which original operations are sampled, not the
source-pinned V104 generator, low-level grammar, tests, verifier or MSI policy.
The first candidate of each distinct original builder/signature is chosen
BEFORE looking at new native outcomes. All exposed Click results remain
nonprospective; G2/G3/G4 UNKNOWN.
"""
from __future__ import annotations
import json
import os
import ast
import copy
import hashlib
import subprocess
import traceback
from pathlib import Path
import sys
import time

from . import qualify_typed_v104_prospective_v7 as old
from . import typed_v104_msi_bridge_v7 as bridge
from . import qualify_v7_exposed_protected_scope as diagnosis
from .developmental_choice import profile_binding, choose_verified_profiles

SCHEMA="UDM_V8_EXPOSED_STRATIFIED_ORIGINAL_V104_CENSUS"
TOTAL_NATIVE_BUDGET=130
HORIZON=64


def status(row):
    if row.get("native_calls")!=2:
        return "UNKNOWN"
    one=row["first"];two=row["second"]
    if (one["native_calls"]!=two["native_calls"] or
            one.get("executed")!=two.get("executed") or
            one.get("imported_project_files")!=two.get("imported_project_files")
            or one.get("required")!=two.get("required")
            or one.get("deselected") or two.get("deselected")):
        return "UNKNOWN"
    if one["status"]==two["status"]=="FAIL_NATIVE_PROTECTED":
        return "VERIFIED_SCOPED_FAIL"
    if one["status"]==two["status"]=="PASS_SCOPED_NATIVE":
        return "VERIFIED_SCOPED_PASS"
    return "UNKNOWN"


def profile(order,events):
    if len(order)<HORIZON or any(x not in events for x in order[:HORIZON]):
        return None
    for pos,ident in enumerate(order[:HORIZON]):
        observed=events[ident]
        if observed=="VERIFIED_SCOPED_PASS":
            if all(events[x]=="VERIFIED_SCOPED_FAIL" for x in order[:pos]):
                return [0,2*(pos+1)]
            return None
        if observed!="VERIFIED_SCOPED_FAIL":
            return None
    return [1,2*HORIZON]



def _original_program_namespace(triskelion):
    """Load exactly authenticated original V104 AST definitions, no extensions."""
    from .qualify_recursive_frontier import PINS
    pin=PINS["constructor_language"]
    raw=subprocess.check_output(
        ["git","--no-replace-objects","-C",str(triskelion),
         "show",pin["commit"]+":"+pin["path"]],stderr=subprocess.PIPE,timeout=45)
    if hashlib.sha256(raw).hexdigest()!=pin["sha256"]:
        raise ValueError("original V104 method source differs from frozen pin")
    tree=ast.parse(raw)
    definitions=[node for node in tree.body if (
        isinstance(node,ast.FunctionDef) and node.name in pin["definitions"]
        or isinstance(node,ast.Assign) and any(
          isinstance(t,ast.Name) and t.id in pin["assignments"] for t in node.targets))]
    names={node.name for node in definitions if isinstance(node,ast.FunctionDef)}
    if names!=set(pin["definitions"]):
        raise ValueError("missing authentic original generator definitions")
    ns={"ast":ast,"copy":copy,"hashlib":hashlib}
    exec(compile(ast.Module(body=definitions,type_ignores=[]),pin["path"],"exec"),ns)
    return ns,pin


def stratified_catalog(repo,base,production_paths,triskelion,msi,*,cap=64):
    """One first original generator witness per source-pinned program signature.

    This is an enumerator comparison, not native acquisition, and never
    synthesizes a builder or changes the frozen V104 grammar.
    """
    if not isinstance(cap,int) or not 1<=cap<=64:
        raise ValueError("bounded diagnostic candidate cap required")
    if not production_paths or not isinstance(production_paths,(tuple,list)):
        raise ValueError("frozen source production files required")
    ns,pin=_original_program_namespace(triskelion)
    signatures=[(sel,builder) for sel in ns["SELECTORS"] for builder in ns["BUILDERS"]]
    # Python equality merges ('CONST', False) with ('CONST', 0) and
    # ('CONST', True) with ('CONST', 1). These are declared original
    # signatures but not separately discriminable by V104's allowed set.
    # Retain all 75 declared source signatures and require an exact repr
    # match before treating any original emission as that signature.
    if len(signatures)!=75:
        raise ValueError("original V104 signature grammar changed")
    signatures.sort(key=lambda t:ns["h"]("program|"+repr(t)))
    snap,regular=bridge._blobs(repo,base)
    rows=[];seen=set()
    for path in production_paths:
        bridge.typed._path(path)
        if path not in regular or bridge.original.is_test(path) or not path.endswith(".py"):
            raise ValueError("V104 production path absent from authenticated typed Git source")
        raw=bridge.typed._git(repo,"cat-file","blob",regular[path]["oid"])
        src=raw.decode("utf-8")
        for sig in signatures:
            candidates=ns["program_candidates"](src,allowed={sig},cap=1)
            if not candidates:
                continue
            selector,builder,text=candidates[0]
            if repr((selector,builder))!=repr(sig) or text==src or text in seen:
                continue
            seen.add(text)
            locations=bridge.original.changed_lines(src,text)
            mean=sum(locations)/len(locations) if locations else 0
            variance=sum((x-mean)**2 for x in locations)/len(locations) if locations else 0
            candidate={"replacements":[{"path":path,
                      "original_sha256":regular[path]["sha256"],
                      "replacement":text}]}
            rows.append({"id":bridge.verifier.fingerprint(candidate),
                         "candidate":candidate,"selector":selector,
                         "builder":builder,"path":path,"changed_lines":locations,
                         "features":{"K":1000000,"c":max(1,len(locations)),"v":variance}})
            if len(rows)>=cap:break
        if len(rows)>=cap:break
    if not rows:raise ValueError("source-pinned original grammar emitted no valid finite candidates")
    orders=bridge.original.orders(rows,msi)
    if len(orders)!=37 or any(
        set(order)!={r["id"] for r in rows} for order in orders.values()):
        raise ValueError("unchanged original MSI policy orders do not cover emitted source")
    return {"schema":"UDM_V8_STRATIFIED_ORIGINAL_V104_CATALOG",
            "rows":rows,"orders":orders,
            "original_typed_source_sha256":snap["manifest_sha256"],
            "source":{"v104_language":"ORIGINAL_PINNED_V104",
                      "msi_policy":"ORIGINAL_PINNED_MSI_V10",
                      "search_variant":"ROUND_ROBIN_ONE_PER_ORIGINAL_SIGNATURE",
                      "v104_signature_count":len(signatures),
                      "v104_equality_distinct_signature_count":len(set(signatures)),
                      "source_python_bool_int_signature_aliases":len(signatures)-len(set(signatures)),
                      "original_method_pin":pin,
                      "additional_operators":0},
            "budget_horizon":"64 max distinct one-per-signature emitted, two native runs each"}

def run(out):
    root=Path(out).absolute()
    if root.exists():raise ValueError("new owned scope-limited output required")
    root.mkdir(parents=True)
    report={"schema":SCHEMA,"state":"EXPOSED_DIAGNOSTIC_ONLY",
            "status":"UNKNOWN","G2":"UNKNOWN","G3":"UNKNOWN","G4":"UNKNOWN",
            "source":"pallets/click PR3884, original baseline + head tests only",
            "preceding_complete_cap64_run":38978813909,
            "full_suite_red_run":38977284706,
            "first_scoped_native_run":38977751776,
            "futures_unopened":["jd/tenacity","pypa/packaging"],
            "no_prospective_claim":True,"native_calls":0,"policy_count":0,
            "native_evaluations":[]}
    started=time.monotonic()
    try:
        protocol,refs=old.sealed_metadata()
        task,ref=protocol["candidates"][0],refs["refs"][0]
        prepared=old.prepare_task(task,ref,root/"input")
        repo=prepared["repo"]
        catalog=stratified_catalog(
             repo,task["base"],task["production"],
             Path(os.environ["UDM_V7_TRISKELION"]),
             Path(os.environ["UDM_V7_MSI"]),cap=64)
        orders=catalog["orders"]
        rows={r["id"]:r for r in catalog["rows"]}
        # Bound the candidate candidate universe BEFORE looking at outcomes.
        plans={name:order[:HORIZON] for name,order in sorted(orders.items())}
        universe=sorted({ident for seq in plans.values() for ident in seq})
        report.update(policy_count=len(plans),row_count=len(rows),
                      builder_classes=sorted({str(r["builder"][0]) for r in rows.values()}),
                      distinct_signatures=len({str((r["selector"],r["builder"])) for r in rows.values()}),
                      eligible_original_operations=len(universe),
                      stratified_original_signatures=True,
                      frozen_plans_sha256=bridge.digest(bridge.canonical(plans).encode()),
                      original_policy_source=catalog["source"],
                      total_native_call_ceiling=TOTAL_NATIVE_BUDGET)
        (root/"POLICY_FRONTIER_BEFORE_NATIVE.json").write_text(json.dumps({
           "schema":"UDM_V8_STRATIFIED_SOURCE_FROZEN_POLICY_FRONTIER",
           "original_manifest_sha256":catalog["original_typed_source_sha256"],
           "original_policy_source":catalog["source"],
           "prefix_horizon":HORIZON,
           "plans":plans,"universe":universe},sort_keys=True,indent=2)+"\n")
        base=bridge.construct_candidate(repo,task["base"],[prepared["test"]],
                      {"replacements":[]},root/"baseline-worktree")
        baseline=diagnosis.measured(repo,base["candidate_commit"],tuple(base["required"]),
                                     root/"baseline-native",tuple(task["author_tests"]))
        report["baseline"]={"first":baseline["first"]["status"],
                             "second":baseline["second"]["status"],
                             "junit":baseline["first"]["junit"],
                             "native_calls":baseline["native_calls"]}
        report["native_calls"]+=baseline["native_calls"]
        if (baseline["first"]["status"]!="FAIL_NATIVE_PROTECTED" or
                baseline["second"]["status"]!="FAIL_NATIVE_PROTECTED"):
            report["status"]="UNKNOWN_NO_AUTHENTIC_PROTECTED_RESIDUAL"
            return report
        observed={}
        for i,ident in enumerate(universe):
            if report["native_calls"]+2>TOTAL_NATIVE_BUDGET:
                observed[ident]="UNKNOWN_BUDGET"
                break
            item=rows[ident]
            try:
                candidate=bridge.construct_candidate(repo,task["base"],[prepared["test"]],
                                item["candidate"],root/("candidate-worktree-"+str(i).zfill(3)))
                result=diagnosis.measured(repo,candidate["candidate_commit"],
                                tuple(candidate["required"]),root/("native-"+str(i).zfill(3)),
                                tuple(task["author_tests"]))
                outcome=status(result)
                record={"id":ident,"selector":item["selector"],"builder":item["builder"],
                        "status":outcome,"first":result["first"]["status"],
                        "second":result["second"]["status"],
                        "source_commit":candidate["candidate_commit"],
                        "elapsed_seconds":result["elapsed_seconds"],
                        "native_calls":result["native_calls"]}
            except (RuntimeError,ValueError,OSError) as error:
                outcome="UNKNOWN_CANDIDATE"
                record={"id":ident,"status":outcome,
                        "reason":type(error).__name__+": "+str(error),"native_calls":0}
            observed[ident]=outcome
            report["native_calls"]+=record["native_calls"]
            report["native_evaluations"].append(record)
        profiles={name:profile(sequence,observed) for name,sequence in plans.items()}
        report["profiles"]=profiles
        missing=[name for name,vector in profiles.items() if vector is None]
        report["complete_policy_count"]=len(profiles)-len(missing)
        report["incomplete_policy_count"]=len(missing)
        report["scope_native_status_counts"]={
            k:list(observed.values()).count(k) for k in sorted(set(observed.values()))}
        if missing:
            report["status"]="UNKNOWN_INCOMPLETE_SOURCE_BOUND_MSI_NATIVE_PROFILE_CENSUS"
            return report
        candidates=tuple(sorted(plans))
        futures=("EXPOSED_CLICK",)
        vectors={c:{"EXPOSED_CLICK":profiles[c]} for c in candidates}
        bound=profile_binding(candidates,futures,vectors,scope={
            "protocol_binding":bridge.digest(old.PROTOCOL.read_bytes()),
            "candidate_catalog_sha256":bridge.digest(bridge.canonical(
               list(rows)).encode()),
            "source_binding":catalog["original_typed_source_sha256"],
            "budget":HORIZON,
            "real_native_evidence_sha256":bridge.digest(bridge.canonical(observed).encode())})
        chooser=choose_verified_profiles(Path(__file__).resolve().parents[2],
                       candidates,futures,vectors,evidence_binding=bound)
        report["original_pareto"]=chooser
        successes=[(name,profiles[name]) for name in profiles if profiles[name][0]==0]
        report["successful_policies"]=successes
        cold=profiles["COLD_V104_ORDER"]
        if cold[0]==1 and not successes:
            report["status"]="EXPOSED_STRATIFIED_ORIGINAL_V104_CAP64_NO_PROTECTED_NATIVE_REPAIR"
        elif successes:
            report["status"]="EXPOSED_STRATIFIED_ORIGINAL_V104_CAP64_CONTAINS_SCOPED_NATIVE_REPAIR"
        else:
            report["status"]="UNKNOWN_STRATIFIED_CAP64_OUTCOME"
        return report
    except Exception as error:
        report.update(status="UNKNOWN_MSI_EXPOSED_DIAGNOSTIC_INTERFACE",
                      reason=type(error).__name__+": "+str(error),
                      traceback=traceback.format_exc(limit=15))
        return report
    finally:
        report["wall_seconds"]=time.monotonic()-started
        (root/"RESULT.json").write_text(json.dumps(report,indent=2,sort_keys=True)+"\n")


if __name__=="__main__":
    result=run(Path(os.environ["UDM_V7_MSI_CENSUS_OUT"]))
    print(json.dumps({"state":result["state"],"status":result["status"],
          "G2":result["G2"],"candidate_count":len(result["native_evaluations"]),
          "policies":result["policy_count"],"native_calls":result["native_calls"],
          "successes":result.get("scope_native_status_counts",{}).get("VERIFIED_SCOPED_PASS",0)},
          sort_keys=True))
    raise SystemExit(0 if result["status"] in (
        "EXPOSED_COMPLETE_V104_EMITTED_CAP64_NO_PROTECTED_NATIVE_REPAIR",
        "EXPOSED_V104_EMITTED_CAP64_CONTAINS_SCOPED_NATIVE_REPAIR") else 2)
