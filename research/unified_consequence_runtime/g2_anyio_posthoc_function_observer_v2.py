#!/usr/bin/env python3
"""Post-result AnyIO NONINTRUSIVE source observation V2. NO candidate repair or G2 promotion.

Reuses original V13 guard_nodes and original V14 authenticated V104 AST selectors.
Extends source observation from the V13 specialised IF_NOT_SELF_ATTRIBUTE branch
to function call events during original protected pytest failures. This extended
observer is UNQUALIFIED until independently checked; events imply execution,
not responsibility for a failure.
"""
from __future__ import annotations
import ast
from collections import Counter, defaultdict
import hashlib
import json
import pathlib
import subprocess
import sys
import xml.etree.ElementTree as ET

from research.unified_consequence_runtime import observed_branch_v13 as v13
from research.unified_consequence_runtime import observed_site_v14 as v14

OWN=pathlib.Path(__file__).resolve().parents[2]
PATH="research/unified_consequence_runtime/G2_ANYIO_POSTHOC_OBSERVATION_PROTOCOL_V1.json"
FREEZE="cb958e9c03bfcc7eb17e193c8d63d22edaf96f1e"


def digest(raw):return hashlib.sha256(raw).hexdigest()
def git(repo,*args,raw=False):
    z=subprocess.check_output(["git","--no-replace-objects","-C",str(repo),*args])
    return z if raw else z.decode().strip()


def main(world,triskelion,dest):
    world=pathlib.Path(world).resolve(strict=True)
    dest=pathlib.Path(dest).resolve()
    dest.mkdir(parents=True,exist_ok=False)
    result={
        "schema":"UDM_ANYIO_POSTHOC_FUNCTION_CALL_OBSERVATION_V2",
        "status":"UNKNOWN_NOT_EXECUTED","native_calls":0,
        "G2":"UNKNOWN","G3":"UNKNOWN","G4":"UNKNOWN",
        "G5":"UNKNOWN","G6":"UNKNOWN","future_source":"UNOPENED",
        "method_generation":"NOT_PERFORMED","native_repair_trials":0,
        "scientific_boundary":"EXPOSED_SOURCE_POSTHOC_DIAGNOSTIC_ONLY"}
    try:
        frozen=git(OWN,"show",FREEZE+":"+PATH,raw=True)
        assert frozen==(OWN/PATH).read_bytes(),"PROTOCOL_MUTATION"
        p=json.loads(frozen)
        v2proto=OWN/"research/unified_consequence_runtime/G2_ANYIO_POSTHOC_OBSERVER_V2_PROTOCOL.json"
        new_freeze=git(OWN,"show","31e0188a21d54aca5e74a942d946a06fc88f9b92:"+str(v2proto.relative_to(OWN)),raw=True)
        assert new_freeze==v2proto.read_bytes(),"V2_PROTOCOL_MUTATED"
        assert json.loads(new_freeze)["status"]=="FROZEN_BEFORE_V2_CODE_OR_NATIVE_OUTCOME"
        assert p["original_source"].split("@")[-1]==git(world,"rev-parse","HEAD"),"WRONG_BASE"
        assert git(world,"rev-parse","HEAD^{tree}")=="c6465ce4b900e2f21aa73ebbe16c779f5c6ae9bf"
        production=p["source_file"];author=p["author_test_file"]
        source=(world/production).read_bytes()
        assert source==git(world,"show","HEAD:"+production,raw=True),"SOURCE_CHANGED"
        assert digest(source)==p["source_sha256"]
        assert git(world,"rev-parse",p["original_test_head"]+":"+author)==p["original_test_blob"]
        tests=(world/author).read_bytes()
        assert tests==git(world,"show",p["original_test_head"]+":"+author,raw=True)
        assert digest(tests)==p["test_sha256"]
        assert git(world,"diff","--name-only")==author,"UNEXPECTED_STAGED_MUTATION"
        assert git(triskelion,"rev-parse","HEAD")=="426c54f7c774560e0fabe7213c5ef333b1327c71"
        tree=ast.parse(source,filename=production)
        guard=v13.guard_nodes(production,source)
        assert len(guard)==0,"ORIGINAL_V13_MISMATCH"
        result["v13_original_eligible_guards"]=len(guard)
        # Historical original V14 only accepts a verified V13 IF_NOT_SELF_ATTRIBUTE event.
        # It cannot be invoked legitimately with a forged/hand-written event here.
        original_functions=[n for n in tree.body if isinstance(n,(ast.FunctionDef,ast.AsyncFunctionDef))]
        functions={f.name:f for f in original_functions}
        # Original source-pinned V104 grammar and selector language, not a new builder.
        methods,method_pin=v14.original_programs(triskelion)
        result["v104_method_sha256"]=method_pin["sha256"]
        original_positions={}
        for sel in methods["SELECTORS"]:
            slots=methods["nodes_for_selector"](tree,sel)
            for index,(node,field,arg) in enumerate(slots):
                line=getattr(node,"lineno",None)
                if not isinstance(line,int):continue
                owning=[f for f in original_functions if f.lineno<=line<=f.end_lineno]
                if len(owning)!=1:continue
                original_positions.setdefault(owning[0].name,[]).append(
                    {"function":owning[0].name,"line":line,
                     "selector":list(sel),"slot_index":index})
        result["all_original_v104_source_slot_counts"]={
            k:len(v) for k,v in sorted(original_positions.items())}
        import pytest
        # Use exactly the original project-supplied pytest configuration and
        # two already-exposed protected author tests, without test/production edits.
        # This source-path computation occurs ONCE, outside protected tests.
        # The original V1 profiler called Path.resolve() per function call.
        # Blockbuster correctly identified that as a forbidden blocking syscall
        # and it *changed* the original protected Hypothesis failure.
        # V2 performs only code-string equality and bounded in-memory counters.
        source_filename=str((world/production).resolve())
        class NativeObservation:
            def __init__(self):
                self.executed=[];self.deselected=[]
                self.collect=[];self.outcomes=[];self.function_calls=defaultdict(Counter)
                self.current=None
                self.failure_longrepr={}
                self.target_filename=source_filename
            def profile(self,frame,event,arg):
                if event!="call":return
                if frame.f_code.co_filename!=self.target_filename:
                    return
                name=frame.f_code.co_name
                self.function_calls[self.current][(name,frame.f_code.co_firstlineno)]+=1
            @pytest.hookimpl(hookwrapper=True,tryfirst=True)
            def pytest_runtest_call(self,item):
                name=item.nodeid
                if name not in p["protected"]:
                    yield;return
                old=sys.getprofile();self.current=name
                sys.setprofile(self.profile)
                try:yield
                finally:
                    sys.setprofile(old);self.current=None
            def pytest_collection_modifyitems(self,session,config,items):
                self.collect=[item.nodeid for item in items]
            def pytest_deselected(self,items):
                self.deselected.extend(item.nodeid for item in items)
            def pytest_runtest_logreport(self,report):
                if report.when=="call":
                    self.outcomes.append({"nodeid":report.nodeid,"outcome":report.outcome})
                    if report.failed and report.nodeid in p["protected"]:
                        self.failure_longrepr[report.nodeid]=str(report.longreprtext)
        monitor=NativeObservation()
        import os
        # pytest.main() follows V6's in-process native execution; this tracer
        # is an observation layer and NOT the unchanged source-native verifier.
        sys.path[:0]=[str(world/"src"),str(world)]
        junit=dest/"instrumented-native.xml"
        argv=["-q","-p","no:cacheprovider","-p","pytest_cov",
              "--junitxml="+str(junit),"--rootdir="+str(world),
              "-c",str(world/"pyproject.toml")]
        argv += [str(world/prefix) for prefix in []] # no implicit suite widening
        argv += [str(world/p["author_test_file"])+ "::"+node.split("::",1)[1]
                 for node in p["protected"]]
        result["native_calls"]=1
        result["pytest_argv"]=argv
        code=pytest.main(argv,plugins=[monitor])
        result["native_exit"]=int(code)
        result["actual_calls"]=monitor.outcomes
        result["failure_signatures"]={
            k:{"native_one_pass_one_fail":("'passed': 1" in v and "'failed': 1" in v),
               "blocking_error":("BlockingError" in v),
               "assertion_failure":("AssertionError" in v),
               "sha256":digest(v.encode()),"short_tail":v[-700:]}
            for k,v in sorted(monitor.failure_longrepr.items())}
        result["profiling_mode"]="CODE_FILENAME_STRING_EQUALITY_NO_PATH_IO"
        result["collected"]=monitor.collect
        result["deselected"]=monitor.deselected
        result["production_call_events"]={
            key:[{"function":name,"line":line,"count":count}
                 for (name,line),count in sorted(items.items())]
            for key,items in monitor.function_calls.items() }
        suite=ET.parse(junit).getroot()
        ts=suite if suite.tag=="testsuite" else next(suite.iter("testsuite"))
        counts={k:int(ts.get(k,0)) for k in ("tests","failures","errors","skipped")}
        result["junit"]=counts
        assert (world/production).read_bytes()==source
        assert (world/author).read_bytes()==tests
        result["source_test_bytes_preserved"]=True
        outcomes={row["nodeid"]:row["outcome"] for row in monitor.outcomes}
        valid=(int(code)==1 and counts=={"tests":2,"failures":2,"errors":0,"skipped":0}
               and set(monitor.collect)==set(p["protected"])
               and not monitor.deselected and
               outcomes=={key:"failed" for key in p["protected"]} and
               len(result["failure_signatures"])==len(p["protected"]) and
               all(v["native_one_pass_one_fail"] and v["assertion_failure"]
                   and not v["blocking_error"]
                   for v in result["failure_signatures"].values()))
        if not valid:
            result["status"]="UNKNOWN_INSTRUMENTED_NATIVE_AUTHORITY"
            return result
        called=Counter()
        reached=defaultdict(list)
        for test,events in monitor.function_calls.items():
            for (name,line),count in events.items():
                called[(name,line)]+=count
                reached[(name,line)].append(test)
        event_functions=[]
        for f in original_functions:
            # Exact function entry and source-line binding, no alias matching.
            if (f.name,f.lineno) not in called:continue
            event_functions.append({"function":f.name,"line":f.lineno,
                "native_call_count":called[(f.name,f.lineno)],
                "protected_test_count":len(set(reached[(f.name,f.lineno)])),
                "v104_eligible_original_AST_slots":original_positions.get(f.name,[])})
        event_functions.sort(key=lambda item:(-item["protected_test_count"],
                                  -item["native_call_count"],item["line"]))
        result["observed_functions"]=event_functions
        result["observed_function_count"]=len(event_functions)
        result["eligible_function_count"]=sum(bool(x["v104_eligible_original_AST_slots"])
                                           for x in event_functions)
        result["eligible_source_slot_count"]=sum(
            len(x["v104_eligible_original_AST_slots"]) for x in event_functions)
        result["other_source_locations_eligible"]=[
            x["function"] for x in event_functions
            if x["function"]!="_is_auto_mode" and x["v104_eligible_original_AST_slots"]]
        result["status"]=("WARRANTED_BOUNDED_INSTRUMENTED_SOURCE_FUNCTION_OBSERVATION"
            if result["other_source_locations_eligible"] else
            "UNKNOWN_NO_INSTRUMENTED_ADDITIONAL_V104_SITE")
    except BaseException as err:
        import traceback
        result["status"]="UNKNOWN_APPARATUS_OR_OBSERVER"
        result["reason"]=type(err).__name__+": "+str(err)
        result["traceback"]=traceback.format_exc(limit=9)[-3200:]
    finally:
        (dest/"RESULT.json").write_text(json.dumps(result,indent=2,sort_keys=True)+"\n")
    return result

if __name__=="__main__":
    if len(sys.argv)!=4:
        raise SystemExit("usage: g2_anyio_posthoc_function_observer_v1.py ANYIO_BASE V104_REPO FRESH_OUTPUT")
    r=main(*(pathlib.Path(x) for x in sys.argv[1:]))
    print(json.dumps({k:r.get(k) for k in (
        "status","v13_original_eligible_guards","observed_function_count",
        "eligible_function_count","eligible_source_slot_count",
        "other_source_locations_eligible","junit","native_exit","reason","G2"
    )},sort_keys=True),flush=True)
    raise SystemExit(0 if r["status"] in (
        "WARRANTED_BOUNDED_INSTRUMENTED_SOURCE_FUNCTION_OBSERVATION",
        "UNKNOWN_NO_INSTRUMENTED_ADDITIONAL_V104_SITE") else 2)
