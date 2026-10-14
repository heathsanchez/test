#!/usr/bin/env python3
"""Real source-native future-consequence observation transfer.

Native child is isolated for each exact public source SHA. Acquire the minimal
observation basis from source A alone using the byte-identical certified FLASH
V11 rank solver. Then test the frozen classifier on futures B and C.
Human-chosen operation/observation vocabulary; NOT L7, novel discovery, or
independent third-party user proof.
"""
from __future__ import annotations
import hashlib
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import tomllib

HERE = Path(__file__).resolve().parent
SOURCE_SOLVER = HERE.parent / "flash_genesis_v11" / "learned_repair.py"
SOURCE_BLOB = "0f7fb6b837cd65aa86b5fef7c097196fc0df4845"
OBS = ("mut_status", "native", "length", "render", "parse_status", "parsed", "coherence")
N = len(OBS)

def dump(obj):
    return json.dumps(obj, sort_keys=True, ensure_ascii=False, separators=(",", ":"))

def hashbytes(b):
    return hashlib.sha256(b).hexdigest()

def gitblob(b):
    return hashlib.sha1(b"blob "+str(len(b)).encode()+b"\0"+b).hexdigest()

def cases(family):
    # The vocabulary was explicitly frozen before inspecting any source patches.
    values=((), (1,), (1,2), (1,2,3), (1,2,3,4))
    out=[dict(id=f"{family}/noop/{len(v)}", op="noop", values=list(v)) for v in values]
    out += [dict(id=f"{family}/append/{len(v)}",op="append",values=list(v))
            for v in values]
    if family=="A":
        slices=((None,0,None),(-1,None,None),(1,3,None),(None,None,-1),
                (-2,None,None),(None,2,None))
        out += [dict(id=f"A/del/{len(v)}/{i}",op="del",values=list(v),
                     start=a,stop=b,step=c)
                for v in values for i,(a,b,c) in enumerate(slices)]
    elif family=="B":
        out += [dict(id=f"B/repeat/{len(v)}/{m}",op="repeat",values=list(v),mult=m)
                for v in values for m in (0,1,2)]
    elif family=="C":
        out += [dict(id=f"C/comment/{nl}/{n}",op="comment",values=[],
                     text="foo" if n==0 else "bar",newline=nl)
                for nl in (False,True) for n in (0,1)]
    else:
        raise ValueError("UNKNOWN_UNDECLARED_FAMILY")
    return out

def run_child(source, sha, family, out):
    source=Path(source).resolve()
    p=subprocess.run(("git","rev-parse","HEAD"),cwd=source,capture_output=True,text=True)
    if p.returncode or p.stdout.strip()!=sha:
        raise ValueError("UNKNOWN_WRONG_NATIVE_GIT_SHA")
    sys.path.insert(0,str(source))
    import tomlkit
    package=Path(tomlkit.__file__).resolve()
    if not package.is_relative_to(source):
        raise ValueError("UNKNOWN_WRONG_TOMLKIT_PACKAGE")
    rows=[]
    for task in cases(family):
        a=tomlkit.array()
        for item in task["values"]:a.append(item)
        action="OK"
        try:
            if task["op"]=="append": a.append(7)
            elif task["op"]=="del":
                del a[slice(task["start"],task["stop"],task["step"])]
            elif task["op"]=="repeat": a *= task["mult"]
            elif task["op"]=="comment":
                a.add_line(task["text"],comment="note",newline=task["newline"])
        except Exception as e:
            action="ERROR_"+type(e).__name__
        try:
            native=a.unwrap()
            length=len(a)
            render=a.as_string()
            try:
                parsed=tomllib.loads("value = "+render)["value"]
                parse_status="OK"
            except Exception as e:
                parsed=None
                parse_status="ERROR_"+type(e).__name__
            coherence=(parse_status=="OK" and parsed==native)
            label=("UNKNOWN" if action!="OK" else
                   "PASS" if coherence else "FAIL")
            feat={
                "mut_status":action,"native":native,"length":length,
                "render":render,"parse_status":parse_status,
                "parsed":parsed if parse_status=="OK" else None,
                "coherence":coherence
            }
        except Exception as e:
            label="UNKNOWN"
            feat={k:"UNAVAILABLE_"+type(e).__name__ for k in OBS}
        rows.append({"id":task["id"],"task":task,"label":label,"features":feat})
    result={
        "repo":"python-poetry/tomlkit",
        "source_sha":sha,
        "source_package":str(package.relative_to(source)),
        "family":family,
        "python":sys.version.split()[0],
        "native_tests":len(rows),
        "case_grammar_sha256":hashbytes(dump(cases(family)).encode()),
        "rows":rows
    }
    Path(out).parent.mkdir(parents=True,exist_ok=True)
    Path(out).write_text(json.dumps(result,indent=2,sort_keys=True)+"\n")
    print(dump({"phase":"NATIVE","family":family,"sha":sha,
                "pass":sum(x["label"]=="PASS" for x in rows),
                "fail":sum(x["label"]=="FAIL" for x in rows),
                "unknown":sum(x["label"]=="UNKNOWN" for x in rows)}))

def key(features,selected):
    return dump([features[s] for s in selected])

def basis_solver():
    raw=SOURCE_SOLVER.read_bytes()
    if gitblob(raw)!=SOURCE_BLOB:
        raise ValueError("UNKNOWN_SOURCE_SOLVER_CHANGED:"+gitblob(raw))
    spec=importlib.util.spec_from_file_location("original_flash_v11_solver",SOURCE_SOLVER)
    obj=importlib.util.module_from_spec(spec)
    spec.loader.exec_module(obj)
    assert obj.POLICY=={"bound":True,"include_first":True,
                         "mode":"both_branches","prune":False}
    return obj

def admissible(mask,rows):
    selected=tuple(OBS[i] for i in range(N) if not (mask>>i&1))
    lookup={}
    for row in rows:
        if row["label"]=="UNKNOWN":continue
        signature=key(row["features"],selected)
        if signature in lookup and lookup[signature]!=row["label"]:
            return False
        lookup[signature]=row["label"]
    return True

def acquire(aold,ahead,out):
    old=json.loads(Path(aold).read_text());head=json.loads(Path(ahead).read_text())
    if old["family"]!="A" or head["family"]!="A":
        raise ValueError("UNKNOWN_SOURCE_A_SCOPE")
    assert [x["id"] for x in old["rows"]]==[x["id"] for x in head["rows"]]
    rows=old["rows"]+head["rows"]
    yes=[i for i in range(1<<N) if admissible(i,rows)]
    if not yes or 0 not in yes:
        raise ValueError("SOURCE_OBSERVATION_GRAMMAR_INADEQUATE")
    optimum=max(i.bit_count() for i in yes)
    solver=basis_solver()
    calls=[0]
    def feasible(mask):
        calls[0]+=1
        return admissible(mask,rows)
    wanted=solver.learned_exact_rank(N,feasible)
    if wanted!=optimum:
        raise ValueError("QUALIFIED_V11_MISSED_EXHAUSTIVE_REFERENCE")
    # Recursion-grammar-preserving source self-reduction, no target dispatch.
    kept=0
    need=optimum
    for i in range(N):
        if not need:break
        attempted=kept|(1<<i)
        if not admissible(attempted,rows):continue
        after=tuple(range(i+1,N))
        def extension(m):
            mask=attempted
            for j,b in enumerate(after):
                if m>>j&1:mask|=1<<b
            return admissible(mask,rows)
        if 1+solver.learned_exact_rank(len(after),extension)==need:
            kept=attempted;need-=1
    if kept.bit_count()!=optimum or not admissible(kept,rows):
        raise ValueError("SOURCE_SELF_REDUCTION_FAILURE")
    selected=[x for i,x in enumerate(OBS) if not (kept>>i&1)]
    lookup={}
    for row in rows:
        if row["label"]!="UNKNOWN":
            lookup[key(row["features"],selected)]=row["label"]
    oldfail={x["id"] for x in old["rows"] if x["label"]=="FAIL"}
    newpass={x["id"] for x in head["rows"] if x["label"]=="PASS"}
    corrected=sorted(oldfail&newpass)
    if not corrected:
        raise ValueError("SOURCE_NO_NATIVE_FAILURE_TO_PASS")
    if any(x["label"]=="FAIL" for x in head["rows"] if x["id"] in oldfail):
        raise ValueError("SOURCE_INCOMPLETE_CORRECTION")
    policy={
        "source_A":{"old":old["source_sha"],"head":head["source_sha"]},
        "original_v11_solver_blob":SOURCE_BLOB,
        "source_old_failed":len(oldfail),
        "source_old_fail_to_head_pass":len(corrected),
        "source_first_resolved_witness":corrected[0],
        "exact_A_observation_optimum":len(selected),
        "selected_channels":selected,
        "deleted_channel_count":optimum,
        "candidate_observation_masks_exhaustively_checked":1<<N,
        "source_v11_oracle_calls":calls[0],
        "source_compiled_lookup":lookup,
        "strong_fully_informed_exhaustive_baseline_ties":wanted==optimum,
        "limits":"human-frozen operation/observer grammar, source-A relative only"
    }
    Path(out).parent.mkdir(parents=True,exist_ok=True)
    Path(out).write_text(json.dumps(policy,indent=2,sort_keys=True)+"\n")
    print(dump({"phase":"ACQUIRE_A","basis":selected,"old_fail_to_head_pass":len(corrected),
                "solver_oracle_calls":calls[0],"exhaustive_ties":True}))

def transfer(policy_path,inputs,out):
    policy=json.loads(Path(policy_path).read_text())
    selected=policy["selected_channels"]
    lookup=policy["source_compiled_lookup"]
    report={"source_capability":policy,
            "future":{}, "status":"UNKNOWN_OR_NEGATIVE_FUTURE_TRANSFER",
            "source_qualified_unchanged":True,
            "model_baseline":"NOT_RUN",
            "full_informed_exhaustive_baseline":"TIE",
            "actual_utility_superiority":"UNKNOWN"}
    total_good=0
    for label,oldfile,headfile in inputs:
        before=json.loads(Path(oldfile).read_text());after=json.loads(Path(headfile).read_text())
        assert before["family"]==after["family"]==label
        assert [x["id"] for x in before["rows"]]==[x["id"] for x in after["rows"]]
        prediction=[]
        for source_name,source in (("old",before),("head",after)):
            entries=[]
            for row in source["rows"]:
                guess=lookup.get(key(row["features"],selected),"UNKNOWN_NEW_FEATURE_SIGNATURE")
                entries.append({"id":row["id"],"actual":row["label"],"predicted":guess})
            prediction.extend({"version":source_name,**x} for x in entries)
        oldfail={x["id"] for x in before["rows"] if x["label"]=="FAIL"}
        headpass={x["id"] for x in after["rows"] if x["label"]=="PASS"}
        repaired=sorted(oldfail&headpass)
        false_warrant=sum(1 for p in prediction if p["predicted"] in ("FAIL","PASS") and
                         p["actual"]!=p["predicted"])
        detected=sum(1 for p in prediction if p["version"]=="old" and
                     p["id"] in repaired and p["predicted"]=="FAIL")
        report["future"][label]={
            "original_old_sha":before["source_sha"],"original_head_sha":after["source_sha"],
            "old_native_violations":len(oldfail),
            "head_repaired_witness_count":len(repaired),
            "learned_method_recognized_repaired_witnesses":detected,
            "false_warrants":false_warrant,
            "new_unrecognized_signatures":sum(p["predicted"]=="UNKNOWN_NEW_FEATURE_SIGNATURE" for p in prediction),
            "first_repaired":repaired[0] if repaired else None,
            "prediction":prediction}
        if repaired and detected and not false_warrant:
            total_good+=1
    # Physical capability artifact withdrawal, not mutation of original source.
    import os
    before=Path(policy_path)
    held=before.with_suffix(".withdrawn")
    if held.exists():raise ValueError("REFUSE_ALREADY_WITHDRAWN")
    os.rename(before,held)
    try:
        missing=not before.exists()
        withheld_status="UNKNOWN_CAPABILITY_WITHDRAWN" if missing else "UNSAFE_PRESENT"
    finally:
        os.rename(held,before)
    report["physical_withdrawal"]=withheld_status
    if withheld_status!="UNKNOWN_CAPABILITY_WITHDRAWN":
        raise ValueError("REVOCATION_TEST_FAILED")
    report["distinct_future_operations_with_native_causal_gain"]=total_good
    report["status"]=("PASS_BOUNDED_NATIVE_SOURCE_A_TO_TWO_FUTURE_OPERATIONS"
                      if total_good==len(inputs) else
                      "REJECTED_OR_UNKNOWN_PROSPECTIVE_TRANSFER")
    Path(out).write_text(json.dumps(report,indent=2,sort_keys=True)+"\n")
    print(dump({"phase":"TRANSFER_FUTURES","status":report["status"],
                "future":{k:{f:v[f] for f in
                   ("old_native_violations","head_repaired_witness_count",
                    "learned_method_recognized_repaired_witnesses","false_warrants",
                    "new_unrecognized_signatures")} for k,v in report["future"].items()}}))
    if total_good!=len(inputs):
        raise SystemExit(23)

if __name__=="__main__":
    if sys.argv[1]=="child":
        run_child(*sys.argv[2:])
    elif sys.argv[1]=="acquire":
        acquire(*sys.argv[2:])
    elif sys.argv[1]=="transfer":
        transfer(sys.argv[2],[("B",sys.argv[3],sys.argv[4]),
                              ("C",sys.argv[5],sys.argv[6])],sys.argv[7])
    else:raise ValueError("UNKNOWN_MODE")
