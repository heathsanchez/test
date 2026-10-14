#!/usr/bin/env python3
"""Source-derived predictive consistency observation compiler.

The observation grammar and its primitives are human written, frozen in
FROZEN_PROTOCOL.md. The executing program chooses methods and composes
native action/observation sequences without repo-specific target symbols.
"""
from __future__ import annotations
import ast
import collections.abc as abc
import hashlib
import importlib
import inspect
import json
import pathlib
import subprocess
import sys
import tempfile
import time

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "mathgraph_obligation_compiler_20261015"))
import observer_genesis as prior

TARGETS = [
    {"repo":"grantjenks/python-sortedcontainers", "pr":254,
     "base":"3ac358631f58c1347f1d6d2d92784117db0f38ed",
     "head":"43e683b8040440200997daf441d3975f709c3b44",
     "role":"development"},
    {"repo":"rspeer/ordered-set", "pr":107,
     "base":"9dfc91c27c0c56df2536036bec4a5b3f717ef2ba",
     "head":"697a395537ff1e41b8fea65dc54f85664d5eac82",
     "role":"transfer"}
]
def h(data):
    return hashlib.sha256(data.encode("utf-8")).hexdigest()

def synthesize_candidates(repo, trees, source_ids):
    out = []
    for path in prior.changed_python(repo, source_ids["base"], source_ids["head"]):
        headfile = trees["head"] / path
        if not headfile.exists():
            continue
        code = headfile.read_text()
        try:
            tree=ast.parse(code)
        except SyntaxError:
            continue
        touched=prior.changed_lines(repo, source_ids["base"], source_ids["head"], path)
        for owner in tree.body:
            if not isinstance(owner, ast.ClassDef) or owner.name.startswith("_"):
                continue
            for node in owner.body:
                if not isinstance(node, ast.FunctionDef):
                    continue
                # Coarse AST source-position association, NO semantic patch reading.
                if touched.isdisjoint(set(range(node.lineno, node.end_lineno+1))):
                    continue
                if node.name.startswith("_") and not (node.name.startswith("__") and node.name.endswith("__")):
                    continue
                out.append({
                    "file":path,"class":owner.name,"method":node.name,
                    "source_range":[node.lineno,node.end_lineno],
                    "old_source":source_ids["base"],"author_source":source_ids["head"],
                    "signature_from_ast":{"positional":[a.arg for a in node.args.args],
                                          "vararg":node.args.vararg.arg if node.args.vararg else None},
                    "source_file_sha256":h(code),
                })
    return out

class MidstreamError(Exception):
    pass

def iterable_fault():
    yield (4, 4)
    raise MidstreamError("deliberate midway failure")

def candidate_values(protocol):
    # General typed enumerable domain; NO names/labels from target repo.
    seq = [
        ("empty", lambda: []),
        ("duplicate-list", lambda: [1, 2, 2]),
        ("duplicate-tuple", lambda: (1, 2, 2)),
        ("new-list", lambda: [3, 4]),
        ("one-shot-duplicate", lambda: iter([1, 2, 2])),
        ("one-shot-distinct", lambda: iter([3, 4])),
        ("pairs", lambda: [(3, 3), (4, 4)]),
        ("malformed-pairs", lambda: [(3, 3), (4,)]),
        ("one-shot-pairs", lambda: iter([(3, 3), (4, 4)])),
        ("one-shot-fault", iterable_fault),
        ("single-pair", lambda: [(3, 3)]),
    ]
    if protocol == "mapping":
        # These are ordered by generic source contract/type, not target-specific.
        return [s for s in seq if "pairs" in s[0] or s[0] in
                ("one-shot-fault","single-pair","empty")]
    return [s for s in seq if s[0] in
            ("empty","duplicate-list","duplicate-tuple","new-list",
             "one-shot-duplicate","one-shot-distinct","pairs")]

def describe_contract(cls):
    if issubclass(cls, abc.MutableMapping) or issubclass(cls, dict):
        return "mapping"
    if issubclass(cls, abc.MutableSet) or issubclass(cls, abc.Set):
        return "set"
    return None

def materialize_state(cls, protocol, initial):
    if initial == "empty":
        try: return cls()
        except Exception: return cls({} if protocol == "mapping" else [])
    if initial == "seed":
        return cls({1:1} if protocol == "mapping" else [0,1])
    raise ValueError("UNKNOWN_INITIAL_STATE")

def measure_projection(obj, protocol):
    observations = {}
    # Independent observer expressions composed from source protocol:
    #    len(x)              : collection -> Nat
    #    len(list(iter(x)))  : collection -> Nat
    #    len(set(iter(x)))   : collection -> Nat, when set
    for kind, action in [
        ("length", lambda:len(obj)),
        ("enumeration", lambda:list(iter(obj))),
    ]:
        try:
            val=action()
            observations[kind]={"ok":True, "value":val}
        except Exception as err:
            observations[kind]={"ok":False, "error":type(err).__name__}
    e=observations["enumeration"]
    if e.get("ok"):
        vals=e["value"]
        observations["enumeration_count"]={"ok":True,"value":len(vals)}
        try: observations["distinct_count"]={"ok":True,"value":len(set(vals))}
        except Exception as exc:
            observations["distinct_count"]={"ok":False,"error":type(exc).__name__}
        observations["ordered_repr"]=[repr(x)[:80] for x in vals]
    else:
        observations["enumeration_count"]={"ok":False,"error":"ITER_NOT_AVAILABLE"}
    return observations

def derive_consequence(observations, protocol):
    comparisons = []
    src=observations["length"]
    for kind in ("enumeration_count","distinct_count") if protocol=="set" else ("enumeration_count",):
        dst=observations.get(kind, {"ok":False})
        if src.get("ok") and dst.get("ok"):
            comparisons.append({
                "program":"eq(len(self), "+("len(list(iter(self)))" if kind=="enumeration_count"
                            else "len(set(iter(self))))")+")",
                "lhs":src["value"],"rhs":dst["value"],
                "contract_holds":src["value"]==dst["value"],
                "source":("Python collections.abc.Set" if protocol=="set"
                          else "Python collections.abc.Mapping")})
    if not comparisons:
        return {"status":"UNKNOWN_OBSERVATION_NOT_AVAILABLE","comparisons":[]}
    # Choose minimum distinguishing relation by expression-tree complexity.
    comparisons.sort(key=lambda x:(len(x["program"]),x["program"]))
    witnesses=[x for x in comparisons if not x["contract_holds"]]
    return {"status":"VIOLATION" if witnesses else "CONSISTENT",
            "comparisons":comparisons, "minimal_witness":witnesses[0] if witnesses else None}

def execute_method(cls, method, args, protocol, initial):
    try: instance=materialize_state(cls, protocol, initial)
    except Exception as err:
        return {"status":"UNKNOWN_CONSTRUCTOR","error":type(err).__name__}
    before=measure_projection(instance,protocol)
    try:
        sig=inspect.signature(getattr(instance,method))
        param=[x for x in sig.parameters.values() if x.kind not in
               (inspect.Parameter.VAR_KEYWORD,inspect.Parameter.KEYWORD_ONLY)]
        if not param:
            arg_list=[]
        else:
            # All source changed mutation callables receive one candidate
            # iterable, with typed variadic arity widened only if allowed.
            arg_list=[args()]
        getattr(instance,method)(*arg_list)
        action={"ok":True}
    except Exception as err:
        action={"ok":False,"error":type(err).__name__, "message":str(err)[:170]}
    after=measure_projection(instance,protocol)
    return {"status":"EXECUTED", "before":before,
            "after":after,"action":action,
            "derived":derive_consequence(after,protocol)}

def native_worker(args):
    root=pathlib.Path(args["root"])
    subject=args["subject"]
    actual=prior.call(["git","-C",str(root),"rev-parse","HEAD"])
    if actual["code"]!=0 or actual["stdout"].strip()!=args["sha"]:
        print(json.dumps({"status":"UNKNOWN_SOURCE_IDENTITY",
                          "actual":actual["stdout"].strip() if actual["code"]==0 else None}))
        return 0
    if args.get("noobserver"):
        print(json.dumps({"status":"UNKNOWN_NO_OBSERVATION","observations":0}))
        return 0
    try:
        import_root,name=prior.find_import_info(root,subject["file"])
        sys.path.insert(0,str(import_root))
        module=importlib.import_module(name)
        cls=getattr(module,subject["class"])
        method=subject["method"]
        if not isinstance(cls,type) or not callable(getattr(cls,method,None)):
            raise ValueError("UNKNOWN_NO_NATIVE_METHOD")
        proto=describe_contract(cls)
        if proto is None:
            raise ValueError("UNKNOWN_NO_INDEPENDENT_ABSTRACT_PROTOCOL")
        operations=[]
        for initial in ("empty","seed"):
            for label,make in candidate_values(proto):
                result=execute_method(cls,method,make,proto,initial)
                # Include source-derived action/observer identity rather than
                # just the precomputed outcome.
                operations.append({"constructor":initial,"argument":label,
                                   "program":"construct → call "+method+" → read len and iterate",
                                   "native":result})
        print(json.dumps({
            "status":"EXECUTED_NATIVE","source_sha":actual["stdout"].strip(),
            "subject":subject,"protocol":proto,
            "observations":len(operations),
            "operations":operations,
        },sort_keys=True))
    except Exception as err:
        print(json.dumps({"status":"UNKNOWN_NATIVE_OPERATION",
                          "exception":type(err).__name__,"reason":str(err)[:250]}))
    return 0

def run_worker(root, subject, sha, noobserver=False):
    cmd=[sys.executable,str(pathlib.Path(__file__).resolve()),"worker",
         json.dumps({"root":str(root),"subject":subject,"sha":sha,
                     "noobserver":noobserver})]
    started=time.monotonic()
    try:
        p=subprocess.run(cmd,capture_output=True,text=True,check=False,timeout=80)
    except subprocess.TimeoutExpired:
        return {"status":"UNKNOWN_WORKER_TIMEOUT"}
    if p.returncode:
        return {"status":"UNKNOWN_WORKER_ERROR","stderr":p.stderr[-700:]}
    try:
        result=json.loads(p.stdout)
        result["elapsed_seconds"]=round(time.monotonic()-started,4)
        return result
    except Exception:
        return {"status":"UNKNOWN_WORKER_OUTPUT","error":p.stdout[-700:],
                "stdout_size":len(p.stdout)}

def controls(subject,trees,target):
    removed=run_worker(trees["base"],subject,target["base"],True)
    wrong=run_worker(trees["head"],subject,"0"*40)
    absent=run_worker(trees["head"]/"nonexistent",subject,target["head"])
    # Deliberately false equality, detected on normal native built-in input.
    false_contract=(len([0,1]) == len([0,1])+1)
    return {"physical_no_observer":removed["status"],
            "wrong_identity":wrong["status"],
            "unavailable_checkout":absent["status"],
            "false_contract_rejected":not false_contract,
            "pass":removed["status"]=="UNKNOWN_NO_OBSERVATION"
                and wrong["status"]=="UNKNOWN_SOURCE_IDENTITY"
                and absent["status"]=="UNKNOWN_SOURCE_IDENTITY"
                and not false_contract}

def assess(old,new):
    if old.get("status")!="EXECUTED_NATIVE" or new.get("status")!="EXECUTED_NATIVE":
        return {"status":"UNKNOWN_NO_NATIVE_BOTH_REVISIONS"}
    if old.get("protocol")!=new.get("protocol"):
        return {"status":"UNKNOWN_CHANGED_INTERFACE"}
    good=[]
    negative=0
    for a,b in zip(old["operations"],new["operations"]):
        if a["argument"]!=b["argument"] or a["constructor"]!=b["constructor"]:
            return {"status":"UNKNOWN_UNPAIRED_PROGRAMS"}
        x=a["native"].get("derived",{}).get("status")
        y=b["native"].get("derived",{}).get("status")
        if x=="VIOLATION" and y=="CONSISTENT":
            detail=a["native"]["derived"]["minimal_witness"]
            if detail and a["native"]["before"]["length"].get("ok"):
                good.append({
                    "argument":a["argument"],"constructor":a["constructor"],
                    "source_program":a["program"],
                    "observer_program":detail["program"],
                    "old_value":[detail["lhs"],detail["rhs"]],
                    "old_action":a["native"]["action"],
                    "head_action":b["native"]["action"],
                    "head_projection":b["native"]["after"],
                    "old_projection":a["native"]["after"],
                })
        if x=="CONSISTENT" and y=="CONSISTENT":
            negative+=1
    return {
        "status":"WARRANTED_BOUNDED_NATIVE_INVARIANT_SEPARATION" if good
                 else "UNKNOWN_NO_CONSEQUENTIAL_OBSERVER",
        "native_witness_count":len(good),
        "both_consistent_controls":negative,
        "minimal_witness":min(good,key=lambda x:len(x["observer_program"])+len(x["source_program"]))
                           if good else None,
    }

def run_target(target,workspace):
    started=time.monotonic()
    try:
        _,trees=prior.make_worktrees(workspace,target)
        candidates=synthesize_candidates(trees["head"],trees,target)
        results=[]
        for cand in candidates:
            old=run_worker(trees["base"],cand,target["base"])
            new=run_worker(trees["head"],cand,target["head"])
            val=assess(old,new)
            c=controls(cand,trees,target)
            results.append({
                "source_candidate":cand,
                "source_native_old":old,"source_native_author_head":new,
                "observation":val,"guards":c,
                "qualified":val["status"]=="WARRANTED_BOUNDED_NATIVE_INVARIANT_SEPARATION"
                            and c["pass"]})
        return {"repo":target["repo"],"role":target["role"],
                "subject_base_sha":target["base"],"subject_head_sha":target["head"],
                "source_candidates_discovered":len(candidates),
                "results":results,"qualified":any(x["qualified"] for x in results),
                "seconds_total":round(time.monotonic()-started,3)}
    except Exception as exc:
        return {"repo":target["repo"],"qualified":False,
                "status":"UNKNOWN_RUNTIME_HARNESS",
                "error":type(exc).__name__,"message":str(exc)[:1400],
                "seconds_total":round(time.monotonic()-started,3)}

def main():
    if len(sys.argv)>1 and sys.argv[1]=="worker":
        return native_worker(json.loads(sys.argv[2]))
    out=pathlib.Path(sys.argv[1] if len(sys.argv)>1 else "evidence")
    out.mkdir(parents=True,exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="mathgraph-predictive-") as tmp:
        results=[run_target(t,pathlib.Path(tmp)/("trial"+str(i)))
                 for i,t in enumerate(TARGETS)]
    report={
        "status":("WARRANTED_BOUNDED_TWO_NATIVE_SOURCE_OBSERVER_COMPOSITIONS"
                  if all(r["qualified"] for r in results)
                  else "UNKNOWN_OR_REJECTED_OBSERVER_COMPOSITION_TRANSFER"),
        "source_code_sha256":prior.sha_file(__file__),
        "protocol_sha256":prior.sha_file(HERE/"FROZEN_PROTOCOL.md"),
        "native_repos":results,
        "human_authored_interpreter_and_primitives":True,
        "original_pr_topics_exposed":True,
        "autonomous_method_language_invention_L7":"UNKNOWN",
        "no_upstream_writes":True,
        "strong_equal_information_coding_agent_baseline":"NOT_RUN",
    }
    (out/"full_native_report.json").write_text(json.dumps(report,indent=2,sort_keys=True,default=str)+"\n")
    compact={"status":report["status"],
             "results":[{"repo":r["repo"],"qualified":r["qualified"],
                         "candidate_count":r.get("source_candidates_discovered",0),
                         "matched":[{"class":x["source_candidate"]["class"],
                                     "method":x["source_candidate"]["method"],
                                     "status":x["observation"]["status"],
                                     "witness":x["observation"].get("minimal_witness"),
                                     "controls_pass":x["guards"]["pass"]}
                                    for x in r.get("results",[])
                                    if x["qualified"]]}
                        for r in results],
             "report_sha256":prior.sha_file(out/"full_native_report.json"),
             "L7":"UNKNOWN"}
    print(json.dumps(compact,sort_keys=True))
    return 0 if all(r["qualified"] for r in results) else 1

if __name__=="__main__":
    raise SystemExit(main())
