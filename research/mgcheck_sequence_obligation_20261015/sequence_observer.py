#!/usr/bin/env python3
"""Source-to-contract minimal native observation program synthesis.

Two independent original Python libraries; one immutable typed sequence law
search grammar. Does NOT synthesize its own meta-language or a safe patch.
Original historical PR titles/body were viewed before freeze; not blind.
"""
from __future__ import annotations
import ast
import collections.abc
import hashlib
import importlib
import inspect
import itertools
import json
import pathlib
import re
import subprocess
import sys
import tempfile
import time

ROOT=pathlib.Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT.parent/"mathgraph_obligation_compiler_20261015"))
import observer_genesis as native

TARGETS=(
 {"repo":"sloria/TextBlob","base":"e8401fa714b33157c4fa8e2e9233d9fec6cb00ef",
  "head":"c0f27915bb25ece9fec6ef6ecea043bf04d6402b","role":"development"},
 {"repo":"mahmoud/boltons","base":"961dcff3f42e73b245aef65e377fe82763b257bb",
  "head":"d574813837f830fd59a2653213cc8f5f8bfc1a86","role":"transfer"},
)

# These are source-INDEPENDENT Python list/MutableSequence behavioral laws.
# They are not handwritten tests for either target library.
LAWS=("append_eq_insert_end","extend_eq_slice_assignment_end",
      "delete_slice_eq_builtin_list")
SEED_FAMILIES=(
 ("strings",["dogs","cats","birds"]),
 ("numbers",[0,1,2,3,4,5]),
)
SLICES=(
 ("empty_prefix",slice(None,0)),("negative_tail",slice(-1,None)),
 ("except_last",slice(None,-1)),("even",slice(None,None,2)),
 ("reverse_step",slice(None,None,-2)),("negative",slice(-4,-1)),
 ("all",slice(None,None)),
)

def hash_bytes(raw):
    return hashlib.sha256(raw).hexdigest()

def get_owner_method(tree,owner_name,method_name):
    for node in tree.body:
        if isinstance(node,ast.ClassDef) and node.name==owner_name:
            for m in node.body:
                if isinstance(m,(ast.FunctionDef,ast.AsyncFunctionDef)) and m.name==method_name:
                    return m
    return None

def source_candidates(repo,worktrees,subject):
    found=[]
    for path in native.changed_python(repo,subject["base"],subject["head"]):
        filepath=worktrees["head"]/path
        if not filepath.exists():continue
        src=filepath.read_text(encoding="utf-8")
        try:tree=ast.parse(src)
        except SyntaxError:continue
        lines=native.changed_lines(repo,subject["base"],subject["head"],path)
        for owner in tree.body:
            if not isinstance(owner,ast.ClassDef):continue
            methods={node.name:node for node in owner.body
                     if isinstance(node,(ast.FunctionDef,ast.AsyncFunctionDef))}
            affected=[m for m in methods.values() if
                      set(range(m.lineno,m.end_lineno+1)).intersection(lines)]
            # The changed implementation can be an internal helper; derive
            # its public initiating operation through the source call graph.
            edges={}
            for m in methods.values():
                deps=set()
                for node in ast.walk(m):
                    if isinstance(node,ast.Call) and isinstance(node.func,ast.Attribute):
                        obj=node.func.value
                        if isinstance(obj,ast.Name) and m.args.args and obj.id==m.args.args[0].arg:
                            deps.add(node.func.attr)
                edges[m.name]=deps
            entries={}
            standard_actions={"__delitem__","__setitem__","insert","append","extend"}
            for m in affected:
                if m.name in standard_actions:
                    entries[m.name]=[m.name]
                for public in standard_actions:
                    if public==m.name:continue
                    seen={public}
                    frontier=[(public,[public])]
                    while frontier:
                        cur,trace=frontier.pop()
                        if m.name in edges.get(cur,set()):
                            entries[public]=trace+[m.name]
                            break
                        for dep in edges.get(cur,set()):
                            if dep not in seen:
                                seen.add(dep)
                                frontier.append((dep,trace+[dep]))
            if not entries: continue
            found.append({
                "file":path,"class":owner.name,
                "changed_source_methods":sorted(m.name for m in affected),
                "public_entrypoints":entries,
                "source_file_sha256":hash_bytes(src.encode("utf-8")),
                "source_class_doc":ast.get_docstring(owner) or "",
                "source_entrypoint_count":len(entries),
            })
    return found

def safe_call(fn):
    try:
        value=fn()
        return {"ok":True,"value":repr(value)[:350]}
    except BaseException as exc:
        if isinstance(exc,(KeyboardInterrupt,SystemExit)):raise
        return {"ok":False,"error":type(exc).__name__,"message":str(exc)[:130]}

def view(obj):
    try:
        items=list(obj)
        return {"ok":True,"values":[str(v) for v in items],
                "types":[type(v).__module__+"."+type(v).__qualname__ for v in items],
                "length":len(obj)}
    except Exception as exc:
        return {"ok":False,"error":type(exc).__name__}

def new_sequence(cls,source):
    try:return cls(list(source))
    except Exception as err:return None

def law_programs(entries):
    # Infer candidate law programs from public operations and changed call graph.
    supported=[]
    if "insert" in entries:supported.append("append_eq_insert_end")
    if "__setitem__" in entries:supported.append("extend_eq_slice_assignment_end")
    if "__delitem__" in entries:supported.append("delete_slice_eq_builtin_list")
    return supported

def run_program(cls,law,seed_family,seed,slice_label=None,slicer=None):
    # Every first-class test is a PROGRAM containing a mutation and two
    # independently observed futures; never use contributor head as oracle.
    if law=="append_eq_insert_end":
        a,b=new_sequence(cls,seed),new_sequence(cls,seed)
        if a is None or b is None:return {"status":"UNKNOWN_CONSTRUCTOR"}
        value=seed[0] if seed else "element"
        x=safe_call(lambda:a.append(value))
        y=safe_call(lambda:b.insert(len(b),value))
        left,right=view(a),view(b)
    elif law=="extend_eq_slice_assignment_end":
        a,b=new_sequence(cls,seed),new_sequence(cls,seed)
        if a is None or b is None:return {"status":"UNKNOWN_CONSTRUCTOR"}
        value=[seed[0]] if seed else ["element"]
        x=safe_call(lambda:a.extend(value))
        y=safe_call(lambda:b.__setitem__(slice(len(b),None),value))
        left,right=view(a),view(b)
    elif law=="delete_slice_eq_builtin_list":
        a=new_sequence(cls,seed)
        if a is None:return {"status":"UNKNOWN_CONSTRUCTOR"}
        b=list(seed)
        x=safe_call(lambda:a.__delitem__(slicer))
        y=safe_call(lambda:b.__delitem__(slicer))
        left=view(a)
        right=view(b)
        # For a subtype, type-specific element type is not a deletion-contract
        # requirement; only visible values, length, exception shape.
        if left.get("ok"):left=dict(left,types=None)
        if right.get("ok"):right=dict(right,types=None)
    else:return {"status":"UNKNOWN_UNSUPPORTED_LAW"}
    if x["ok"]!=y["ok"]:
        verdict="VIOLATION"
    elif not x["ok"] and x.get("error")!=y.get("error"):
        verdict="VIOLATION"
    elif not left.get("ok") or not right.get("ok"):
        verdict="UNKNOWN_OBSERVATION"
    elif left!=right:
        verdict="VIOLATION"
    else:
        verdict="CONSISTENT"
    return {"status":verdict,"action_left":x,"action_right":y,
            "left":left,"right":right,
            "law":law,"input_family":seed_family,
            "slice":slice_label}

def native_worker(arg):
    src=pathlib.Path(arg["path"])
    git=native.call(["git","-C",str(src),"rev-parse","HEAD"])
    if git["code"] or git["stdout"].strip()!=arg["sha"]:
        print(json.dumps({"status":"UNKNOWN_SOURCE_IDENTITY"}));return
    if arg.get("delete_observer"):
        print(json.dumps({"status":"UNKNOWN_NO_OBSERVATION","executed_programs":0}));return
    if not arg.get("contract",True):
        print(json.dumps({"status":"UNKNOWN_CONTRACT_WITHDRAWN","executed_programs":0}));return
    subject=arg["candidate"]
    try:
        import_root,module=native.find_import_info(src,subject["file"])
        sys.path.insert(0,str(import_root))
        mod=importlib.import_module(module)
        cls=getattr(mod,subject["class"])
        origin=pathlib.Path(inspect.getfile(cls)).resolve()
        if not origin.is_relative_to(src.resolve()):
            raise ValueError("UNKNOWN_SOURCE_IMPORT_SUBSTITUTION")
        if not issubclass(cls,collections.abc.MutableSequence) and not issubclass(cls,list):
            # Source-documented list subtype is also normative evidence,
            # but do not guess for arbitrary collection types.
            desc=(inspect.getdoc(cls) or "").lower()
            if "list-like" not in desc and "subtype of the builtin" not in desc:
                raise ValueError("UNKNOWN_SEQUENCE_CONTRACT")
        laws=law_programs(subject["public_entrypoints"])
        if not laws:
            raise ValueError("UNKNOWN_NO_TYPED_LAW")
        records=[]
        for law in laws:
            for family,seed in SEED_FAMILIES:
                for tag,sl in SLICES if law=="delete_slice_eq_builtin_list" else ((None,None),):
                    observation=run_program(cls,law,family,seed,tag,sl)
                    if observation["status"] not in ("VIOLATION","CONSISTENT"):
                        continue
                    records.append(observation)
        if not records:
            print(json.dumps({"status":"UNKNOWN_NO_EXECUTED_PROGRAM","source_sha":git["stdout"].strip()}))
            return
        distinct=[r for r in records if r["status"]=="VIOLATION"]
        matching=[r for r in records if r["status"]=="CONSISTENT"]
        # A shortest program, by action count then witness-expression length.
        # All comparisons use same source-independent cost order.
        minimal=min(distinct,key=lambda r:(2 if r["law"]!="delete_slice_eq_builtin_list" else 1,
                                            len(json.dumps(r["left"]))+len(json.dumps(r["right"])),
                                            r["law"],r["input_family"],str(r["slice"]))) if distinct else None
        print(json.dumps({
            "status":"EXECUTED","subject":subject,"source_sha":git["stdout"].strip(),
            "witnesses":len(distinct),"controls":len(matching),
            "number_of_programs":len(records),"minimal":minimal,
            "law_counts":{law:{"violation":sum(r["law"]==law and r["status"]=="VIOLATION" for r in records),
                               "consistent":sum(r["law"]==law and r["status"]=="CONSISTENT" for r in records)}
                          for law in laws},
            "program_keys":[{"law":r["law"],"family":r["input_family"],"slice":r["slice"],
                             "status":r["status"]} for r in records]
        },sort_keys=True))
    except Exception as exc:
        print(json.dumps({"status":"UNKNOWN_WORKER","type":type(exc).__name__,
                          "message":str(exc)[:400]}))

def replay(checkout,candidate,sha,contract=True,delete_observer=False):
    arg={"path":str(checkout),"candidate":candidate,"sha":sha,
         "contract":contract,"delete_observer":delete_observer}
    cmd=[sys.executable,str(pathlib.Path(__file__).resolve()),"worker",json.dumps(arg)]
    start=time.monotonic()
    try:p=subprocess.run(cmd,text=True,capture_output=True,timeout=50)
    except subprocess.TimeoutExpired:return {"status":"UNKNOWN_TIMEOUT"}
    try:
        answer=json.loads(p.stdout)
        answer["seconds"]=round(time.monotonic()-start,4)
        return answer
    except Exception:
        return {"status":"UNKNOWN_WORKER_SERIALIZATION",
                "exit":p.returncode,"stderr_tail":p.stderr[-700:],
                "stdout_tail":p.stdout[-700:]}

def check(subject,root):
    start=time.monotonic()
    try:
        repo,trees=native.make_worktrees(root,subject)
        candidates=source_candidates(repo,trees,subject)
        results=[]
        for cand in candidates:
            base=replay(trees["base"],cand,subject["base"])
            head=replay(trees["head"],cand,subject["head"])
            neg_wrong=replay(trees["base"],cand,"0"*40)
            neg_observer=replay(trees["base"],cand,subject["base"],delete_observer=True)
            neg_contract=replay(trees["base"],cand,subject["base"],contract=False)
            absent=replay(root/"missing-reference",cand,subject["head"])
            required=[neg_wrong["status"]=="UNKNOWN_SOURCE_IDENTITY",
                      neg_observer["status"]=="UNKNOWN_NO_OBSERVATION",
                      neg_contract["status"]=="UNKNOWN_CONTRACT_WITHDRAWN",
                      absent["status"]=="UNKNOWN_SOURCE_IDENTITY"]
            source_pinned=base.get("source_sha")==subject["base"] and head.get("source_sha")==subject["head"]
            # Min witness is not enough: ensure base violations turn into
            # contract-compatible head outcomes under the EXACT same program.
            base_keys={(x["law"],x["family"],x["slice"]) for x in base.get("program_keys",[])
                       if x["status"]=="VIOLATION"}
            head_violations={(x["law"],x["family"],x["slice"]) for x in head.get("program_keys",[])
                             if x["status"]=="VIOLATION"}
            newly_introduced=head_violations-base_keys
            repaired=base_keys-head_violations
            qualified=bool(source_pinned and all(required) and repaired
                           and not newly_introduced and base.get("controls",0)>0)
            results.append({
                "candidate":cand,"base":base,"head":head,
                "repaired_specific_programs":len(repaired),
                "introduced_violations":len(newly_introduced),
                "identity_guards":{"wrong":neg_wrong["status"],"missing_ref":absent["status"],
                                   "delete_observer":neg_observer["status"],
                                   "withdraw_contract":neg_contract["status"]},
                "native_result":("WARRANTED_BOUNDED_SEQUENCE_LAW_SEPARATION"
                                 if qualified else "UNKNOWN_OR_REJECTED"),
                "qualified":qualified,
            })
        return {"repo":subject["repo"],"role":subject["role"],
                "base_sha":subject["base"],"head_sha":subject["head"],
                "source_candidates":len(candidates),
                "results":results,"qualified":any(x["qualified"] for x in results),
                "seconds":round(time.monotonic()-start,3)}
    except Exception as exc:
        return {"repo":subject["repo"],"qualified":False,
                "status":"UNKNOWN_NATIVE_HARNESS","error":type(exc).__name__,
                "message":str(exc)[:1400]}

def main():
    if len(sys.argv)>1 and sys.argv[1]=="worker":
        native_worker(json.loads(sys.argv[2]));return 0
    destination=pathlib.Path(sys.argv[1] if len(sys.argv)>1 else "evidence")
    destination.mkdir(parents=True,exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="mgcheck-seq-") as tmp:
        reports=[check(target,pathlib.Path(tmp)/("subject"+str(i)))
                 for i,target in enumerate(TARGETS)]
    verdict=("WARRANTED_BOUNDED_SOURCE_CONTRACT_NATIVE_SEQUENCE_TRANSFER"
             if all(x["qualified"] for x in reports) else
             "UNKNOWN_OR_REJECTED_SEQUENCE_TRANSFER")
    out={
        "status":verdict,"subject_reports":reports,
        "original_source_protocol_sha256":native.sha_file(ROOT/"FROZEN_PROTOCOL.md"),
        "generator_sha256":native.sha_file(__file__),
        "input_program_grammar_predeclared_by_human":True,
        "source_change_topics_previously_read":True,
        "inference_model_or_llm_not_used":True,
        "novel_unknown_upstream_bug":"NOT_CLAIMED",
        "strong_equal_information_coding_agent_baseline":"NOT_RUN",
        "fully_informed_stateless_differential_replay":"CAN_REPRODUCE_WITH_SAME_CONTRACT_AND_PROGRAMS",
        "meta_language_invention_L7":"UNKNOWN",
        "native_patch_qualification":"NOT_RUN",
        "no_upstream_changes":True
    }
    reportpath=destination/"report.json"
    reportpath.write_text(json.dumps(out,indent=2,sort_keys=True)+"\n")
    print(json.dumps({
        "status":verdict,
        "subjects":[{"repo":x["repo"],"qualified":x["qualified"],
                     "selected":[{"class":r["candidate"]["class"],
                                  "entrypoints":r["candidate"]["public_entrypoints"],
                                  "repaired":r["repaired_specific_programs"],
                                  "new_violations":r["introduced_violations"],
                                  "minimal":r["base"].get("minimal"),
                                  "status":r["native_result"]}
                                 for r in x.get("results",[]) if r["qualified"]]}
                    for x in reports],
        "report_sha256":native.sha_file(reportpath),
        "L7":"UNKNOWN"
    },sort_keys=True))
    return 0 if all(x["qualified"] for x in reports) else 1

if __name__=="__main__":
    raise SystemExit(main())
