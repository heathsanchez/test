#!/usr/bin/env python3
"""Compositional bounded H11 nonempty-preservation and cached-impact verifier.

The AST edit grammar is finite and human-authored. Test-session historical
non-observation and Boolean finite models are NOT global Python equivalence.
"""
import ast, hashlib, itertools, json, os, pathlib, statistics, subprocess, sys, tempfile, time
ROOT=pathlib.Path(__file__).resolve().parents[2]
UP=ROOT/"upstream"
HERE=pathlib.Path(__file__).resolve().parent
SOURCE=UP/"h11/_receivebuffer.py"
OWNER=UP/"h11/tests/test_receivebuffer.py"
HEADER=UP/"h11/tests/test_headers.py"
REPORT=HERE/"result.json"
OLD="        return bool(len(self))"
PIN="62c5068c971579d61fa1b55373390e12f25fd856"
BLOBS={
 "h11/_receivebuffer.py":"e5c4e08a56f5081e87103f38b4add6ce1b730204",
 "h11/tests/test_receivebuffer.py":"21a3870b6be9a6a365037326c2085ff2715022cc",
 "h11/tests/test_headers.py":"b57274cbbfee8fce3e89f012b6d0f4206f768f67"
}
BASES=("len(self)","len(self._data)")
POSITIVE=("bool({x})","({x} > 0)","({x} != 0)","({x} >= 1)","(not ({x} == 0))","(not ({x} <= 0))")
NEGATIVE=("({x} >= 0)","({x} == 0)")
TRACER=HERE/"tracer.py"
def git(*args):
    return subprocess.check_output(["git",*args],cwd=UP,text=True).strip()
def authenticate():
    assert git("rev-parse","HEAD")==PIN
    for path,sha in BLOBS.items():assert git("rev-parse","HEAD:"+path)==sha
    orig=SOURCE.read_text();header=HEADER.read_text()
    assert orig.count(OLD)==1
    tree=ast.parse(orig)
    klass=next(x for x in tree.body if isinstance(x,ast.ClassDef) and x.name=="ReceiveBuffer")
    length=next(x for x in klass.body if isinstance(x,ast.FunctionDef) and x.name=="__len__")
    assert len(length.body)==1 and isinstance(length.body[0],ast.Return)
    assert ast.unparse(length.body[0].value)=="len(self._data)"
    return orig,header
def finite_model(base,template):
    results=[]
    for n in tuple(range(257))+(1024,):
        # Independent two allowed length inputs are equivalent by original
        # H11 source-defined __len__, not by arbitrary external source syntax.
        measured=n
        if template=="bool({x})":val=bool(measured)
        elif template=="({x} > 0)":val=(measured>0)
        elif template=="({x} != 0)":val=(measured!=0)
        elif template=="({x} >= 1)":val=(measured>=1)
        elif template=="(not ({x} == 0))":val=not(measured==0)
        elif template=="(not ({x} <= 0))":val=not(measured<=0)
        elif template=="({x} >= 0)":val=(measured>=0)
        elif template=="({x} == 0)":val=(measured==0)
        else:raise AssertionError("UNKNOWN_CONSTRUCTOR")
        results.append(val==bool(measured))
    return {"checked_lengths":len(results),"passes_all":all(results),
            "first_counterexample_length":next((x for x,ok in zip(tuple(range(257))+(1024,),results) if not ok),None)}
def run_test(path,label):
    with tempfile.NamedTemporaryFile(suffix=".json",delete=False) as tmp:
        audit=tmp.name
    env=os.environ.copy();env["PYTHONPATH"]=str(UP)
    t=time.perf_counter()
    result=subprocess.run([sys.executable,str(TRACER),
            str(path.relative_to(UP)),audit],cwd=UP,env=env,
            text=True,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,timeout=120)
    elapsed=round(time.perf_counter()-t,6)
    try:observation=json.loads(pathlib.Path(audit).read_text())
    except Exception:observation={"trace_status":"UNAVAILABLE"}
    pathlib.Path(audit).unlink(missing_ok=True)
    return {"scenario":label,"suite":str(path.relative_to(UP)),
            "ok":result.returncode==0,"exit":result.returncode,
            "seconds":elapsed,"trace":observation,
            "tail":result.stdout.strip().splitlines()[-3:]}
def shape(original,candidate,header,pinned_header,generated):
    if header!=pinned_header:return False,"SOURCE_TEST_IDENTITY_CHANGED"
    if candidate!=original.replace(OLD,"        return "+generated,1):
        return False,"SOURCE_CHANGE_OUTSIDE_DECLARED_METHOD_EXPRESSION"
    try:ast.parse(candidate)
    except SyntaxError:return False,"INVALID_PYTHON_AST"
    return True,"EXACT_DECLARED_RETURN_CHANGE"
def warrant(admitted):
    sys.path.insert(0,str(ROOT/"mathgraph_pinned"))
    from mathgraph_check.warrant_resolution import Claim,Receipt,Route,resolve_graph
    scope="h11:exact-source-generated-predicate-v10:documentary"
    labels=("source","historic","finite_contract","owning_native","policy")
    claims=[Claim(x,"documentary",scope) for x in ("source","contract","native","protected_skip","independent","full_release")]
    receipts=[Receipt(x,"documentary",scope) for x in labels+("independent",)]
    routes=[Route("source",("source","historic")),
            Route("contract",("finite_contract",),("source",)),
            Route("native",("owning_native",)),
            Route("protected_skip",("policy",),("contract","native")),
            Route("independent",("independent",))]
    withdrawn=frozenset() if admitted else frozenset({"finite_contract"})
    state=dict(resolve_graph(claims,routes,receipts,withdrawn=withdrawn).states)
    assert state["full_release"]=="UNKNOWN" and state["independent"]=="SOURCE_DOCUMENTED"
    if admitted:
        assert state["protected_skip"]=="SOURCE_DOCUMENTED"
        for id_ in labels:
            changed=dict(resolve_graph(claims,routes,receipts,withdrawn=frozenset({id_})).states)
            assert changed["protected_skip"]=="UNKNOWN"
    else:assert state["protected_skip"]=="UNKNOWN"
    return state["protected_skip"]
def main():
    start=time.perf_counter()
    original,head=authenticate()
    candidates=[]
    candidate_id=0
    try:
        for base,template in itertools.product(BASES,POSITIVE+NEGATIVE):
            candidate_id+=1
            expression=template.format(x=base)
            variant="        return "+expression
            changed=original.replace(OLD,variant,1)
            same=changed==original
            model=finite_model(base,template)
            eligible,reason=shape(original,changed,head,head,expression)
            assert eligible
            SOURCE.write_text(changed)
            owner=run_test(OWNER,f"c{candidate_id}:owner")
            # Pre-omission decision occurs now, before independent header audit.
            proposed=eligible and model["passes_all"] and owner["ok"]
            decision=warrant(proposed)
            header=run_test(HEADER,f"c{candidate_id}:headers_independent_audit")
            if proposed:
                assert header["ok"] and header["trace"].get("target_calls")==0,(
                    candidate_id,"CACHED_NONOBSERVATION_FALSIFIED")
            if not model["passes_all"]:
                assert not proposed and not owner["ok"],("NEGATIVE_NOT_DETECTED",candidate_id)
            candidates.append({"id":candidate_id,"expression":expression,
                "base":base,"template":template,"identity_control":same,
                "model":model,"source_admission":reason,"owner":owner,
                "header_independent_audit":header,
                "pre_header_warrant":decision,"would_skip":proposed,
                "conventional_cached_coverage_skip":proposed})
        # Any changed test file invalidates historical independent-test claim.
        injected=head+"\n\ndef test_new_header_calls_receivebuffer_bool_v10():\n"\
           "    from h11._receivebuffer import ReceiveBuffer\n"\
           "    assert bool(ReceiveBuffer()) is False\n"
        assert not shape(original,original.replace(OLD,"        return (len(self) >= 1)",1),injected,head,"(len(self) >= 1)")[0]
        HEADER.write_text(injected)
        SOURCE.write_text(original)
        injected_test=run_test(HEADER,"injected_future_test")
        assert injected_test["trace"].get("target_calls",0)>0
        # An unrelated source edit rejects even if Boolean model holds.
        badsource=original.replace(OLD,"        return (len(self) >= 1)",1)+"\nADDED_SIDE_EFFECT = True\n"
        assert not shape(original,badsource,head,head,"(len(self) >= 1)")[0]
    finally:
        SOURCE.write_text(original)
        HEADER.write_text(head)
    positive=[c for c in candidates if c["model"]["passes_all"]]
    negative=[c for c in candidates if not c["model"]["passes_all"]]
    assert len(positive)==12 and len(negative)==4
    assert sum(not c["identity_control"] for c in positive)==11
    assert all(c["would_skip"] for c in positive)
    assert all(not c["would_skip"] for c in negative)
    assert all(c["owner"]["ok"] for c in positive)
    assert all(not c["owner"]["ok"] for c in negative)
    native_time=sum(c["owner"]["seconds"]+c["header_independent_audit"]["seconds"] for c in candidates)
    header_avoided=sum(c["header_independent_audit"]["seconds"] for c in positive)
    report={
       "status":"PASS_GENERATED_FINITE_NONEMPTY_LAW_WITH_BOUNDED_REUSABLE_WARRANT",
       "source_commit":PIN,"source_git_blobs":BLOBS,
       "source_sha256":hashlib.sha256(original.encode()).hexdigest(),
       "candidate_grammar":{"base_expressions":list(BASES),
          "positive_templates":list(POSITIVE),"negative_templates":list(NEGATIVE)},
       "generated_positive_cases":len(positive),"genuine_source_edit_cases":11,
       "generated_negative_cases":len(negative),
       "first_preheader_proposal_before_audit":True,
       "candidates":candidates,"injected_dependency_native":injected_test,
       "unapproved_toplevel_change_rejected":True,
       "actual_mathgraph_warrant_resolver":"mathgraph_check.warrant_resolution.resolve_graph pinned at e48f094fa4",
       "conventional_cached_coverage":"TIE_ON_ALL_PREHEADER_DECISIONS",
       "hypothetical_header_test_seconds_avoided":round(header_avoided,6),
       "actual_all_candidate_test_process_seconds":round(native_time,6),
       "total_script_seconds":round(time.perf_counter()-start,6),
       "full_release":"UNKNOWN",
       "limitations":["human-authored finite algebra, not discovered semantic rule",
         "finite domain n=0..256 and 1024, not arbitrary Python semantics",
         "historical V8 test trace caller-admitted; no universally sound noninterference proof",
         "other method observables, frame reflection and future imports not certified",
         "all independent header tests re-executed during audit",
         "fair equal-information cached-coverage selector makes same decisions",
         "no full CI economic or unmatched competitor advantage"]
    }
    REPORT.write_text(json.dumps(report,indent=2,sort_keys=True)+"\n")
    print(json.dumps({"status":report["status"],
       "positive":len(positive),"real_changes":11,"negative":len(negative),
       "accepted_preheader":sum(c["would_skip"] for c in candidates),
       "injection_calls":injected_test["trace"].get("target_calls"),
       "hypothetical_header_seconds":round(header_avoided,6),
       "full_process_seconds":round(native_time,6),
       "conventional":"TIE","release":"UNKNOWN"},sort_keys=True))
if __name__=="__main__":main()
