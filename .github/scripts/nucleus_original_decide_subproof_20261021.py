#!/usr/bin/env python3
"""Extract a minimal ORIGINAL-source closed decide=true proof from two Magma exports.

The genuine Lean 4.34.1 source has a countermodel proof containing:
  of_decide_eq_true(P, nativeDecidable, id(Eq Bool (decide P) true, Eq.refl ...))
The inner id application and its EXACT Eq type are reused byte-for-byte,
without constructing a synthetic proof term or hypothesizing any equivalence.

Build two new standalone export declarations from this original proof:
  positive: original Eq type, original id proof
  negative: replace only the final Bool.true in the expected Eq type with
            the original source Bool.false constant (wrong proposition).
We compare independent Nucleus against a distinct reference kernel, but
never use reference results to bypass Nucleus checking.

This is a diagnostic, not a checker implementation change.
"""
from __future__ import annotations
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys

if len(sys.argv)!=5:
    raise SystemExit("usage: extract.py EXACT_ARENA_CORPUS NUCLEUS_BINARY REFERENCE_BINARY OUTPUT")
corpus,nucleus,reference,out=map(Path,sys.argv[1:])
out.mkdir(parents=True,exist_ok=True)
manifest=Path("metatron-kernel/evidence/performance/owned-environment-2026-10-13/nucleus-owned-environment-frozen196.json")
base={r["case"]:r for r in json.loads(manifest.read_text())["modes"]["origin"]["rows"]}
cases=("good/perf/magma-list-pair-n7.ndjson","good/perf/magma-list-pair-n21.ndjson")

def locate_source(original:Path,case:str)->dict:
    raw=original.read_bytes()
    assert hashlib.sha256(raw).hexdigest()==base[case]["sha256"],("PINNED_SOURCE_CHANGED",case)
    lines=raw.splitlines()
    rows=[json.loads(line) for line in lines]
    expr={r["ie"]:r for r in rows if "ie" in r}
    names={r["in"]:r for r in rows if "in" in r}
    def name(i:int)->str:
        if i==0:return ""
        n=names.get(i)
        assert n is not None,("MISSING_SOURCE_NAME",i)
        d=n.get("str") or n.get("num")
        assert isinstance(d,dict)
        pre=d["pre"]
        return (name(pre)+"." if pre else "")+str(d.get("str",d.get("i","")))
    def head(i:int):
        args=[]
        seen=set()
        while i not in seen and i in expr and "app" in expr[i]:
            seen.add(i);node=expr[i]["app"]
            args.append(node["arg"]);i=node["fn"]
        e=expr.get(i,{})
        if "const" in e:return name(e["const"]["name"]),list(reversed(args))
        return None,list(reversed(args))
    owned=[(idx,r["def"]) for idx,r in enumerate(rows) if "def" in r
           and name(r["def"]["name"])=="countermodel"]
    assert len(owned)==1 and owned[0][0]==len(rows)-1,("EXPECTED_LAST_REAL_COUNTERMODEL_DEF",case)
    end,owner=owned[0]
    assert owner["levelParams"]==[] and owner["value"] in expr
    visited=set();pending=[owner["value"]];matches=[]
    while pending:
        cur=pending.pop()
        if cur in visited:continue
        visited.add(cur)
        e=expr.get(cur)
        if not e:continue
        h,args=head(cur)
        if h=="of_decide_eq_true" and len(args)==3:
            original_proof=args[-1]
            ph,pargs=head(original_proof)
            if ph=="id" and len(pargs)==2:
                th,ty_args=head(pargs[0])
                vh,val_args=head(pargs[1])
                if (th=="Eq" and len(ty_args)==3 and
                    head(ty_args[0])[0]=="Bool" and
                    head(ty_args[-1])[0]=="Bool.true" and
                    vh=="Eq.refl" and len(val_args)==2 and
                    val_args[-1]==ty_args[-1]):
                    matches.append({"source_node":cur,"proof":original_proof,
                                    "type":pargs[0],"eq_args":ty_args,
                                    "decidable":args[1]})
        for key,children in (
          ("app",("fn","arg")),("lam",("type","body")),
          ("forallE",("type","body")),("letE",("type","value","body")),
          ("proj",("expr",)),("mdata",("expr",)),
        ):
            if key in e:
                pending.extend(v for c in children if isinstance((v:=e[key].get(c)),int))
    assert len(matches)==1,("NOT_UNIQUE_SOURCE_DERIVATION",case,matches)
    proof=matches[0]
    false_candidates=[eid for eid,e in expr.items()
                      if "const" in e and name(e["const"]["name"])=="Bool.false"
                      and not e["const"].get("us")]
    assert false_candidates,("MISSING_EXACT_BOOL_FALSE",case)
    false_id=min(false_candidates)
    full=expr[proof["type"]]
    assert "app" in full
    assert full["app"]["arg"]==proof["eq_args"][-1]
    eq_partial=full["app"]["fn"]
    assert head(eq_partial)[0]=="Eq"
    level_params=owner["levelParams"];declaration_name=owner["name"]
    value_expr=proof["proof"]
    def declaration(type_expr):
        return {"thm":{"all":[declaration_name],"name":declaration_name,
                       "levelParams":level_params,"type":type_expr,"value":value_expr}}
    # Keep complete untouched original source prefix; only the final
    # declaration is substituted for the separately extracted subproof.
    pos=rows[:end]+[declaration(proof["type"])]
    new_expr=max(expr)+1
    neg=rows[:end]+[{"ie":new_expr,"app":{"fn":eq_partial,"arg":false_id}},
                    declaration(new_expr)]
    paths={}
    for title,records in (("positive",pos),("negative",neg)):
        path=out/(case.split("/")[-1]+"-"+title+".ndjson")
        path.write_text("\n".join(json.dumps(x,ensure_ascii=False,separators=(",",":"))
                              for x in records)+"\n")
        paths[title]={"path":str(path),"sha256":hashlib.sha256(path.read_bytes()).hexdigest(),
                      "bytes":path.stat().st_size,"records":len(records)}
    return {"case":case,"input_sha256":base[case]["sha256"],"source_owner":declaration_name,
            "exact_subproof_expr":proof["proof"],"exact_subproof_type":proof["type"],
            "original_source_decidable":proof["decidable"],
            "original_source_proof_id":proof["source_node"],
            "negative_changed_proposition_only":True,
            "paths":paths}

def run(exe:Path,source:Path,is_reference:bool):
    base_env={k:v for k,v in os.environ.items() if not k.startswith("NUCLEUS_")}
    if is_reference:
        command=[str(exe.resolve()),"--stdin","--nat-extension","--string-extension",
                 "--axiom-allow-all","--threads","1"]
    else:
        for flag in ("RELEVANCE","CONTEXT_BINDER","TYPED_LINEAGE",
                     "SUBSTITUTION_RECLOSURE","TYPED_VALUE_NORMALIZATION",
                     "PROJECTION_CONTEXT","PROJECTION_CROSSFRAME_512",
                     "TYPED_RECEIVER","SOURCE_PAIR_DEPTH8",
                     "POLYMORPHIC_PROP_IRREL","PROP_SINGLETON_2P1F",
                     "EXPECTED_LAMBDA"):
            base_env["NUCLEUS_EXPERIMENTAL_"+flag]="1"
        base_env["NUCLEUS_TRACE_DOWNSTREAM"]="1"
        command=[str(exe.resolve())]
    with source.open("rb") as src:
        p=subprocess.run(command,stdin=src,stdout=subprocess.PIPE,
                         stderr=subprocess.PIPE,timeout=160,env=base_env)
    lines=p.stderr.decode(errors="replace").splitlines()
    return {"exit":p.returncode,
            "terminal":[s for s in lines if s.startswith("NUCLEUS_DOWNSTREAM:")][-1:],
            "stderr_tail":p.stderr.decode(errors="replace")[-900:]}

results=[]
for case in cases:
    row=locate_source(corpus/case,case)
    for scenario,data in row["paths"].items():
        path=Path(data["path"])
        gold=run(reference,path,True)
        actual=run(nucleus,path,False)
        row["paths"][scenario]["reference"]=gold
        row["paths"][scenario]["nucleus"]=actual
        print("NUCLEUS_ORIGINAL_DECIDE_SUBPROOF="+json.dumps({
            "case":case,"scenario":scenario,
            "reference_rc":gold["exit"],"nucleus_rc":actual["exit"],
            "nucleus_terminal":actual["terminal"],
        },ensure_ascii=False),flush=True)
        assert gold["exit"]==(0 if scenario=="positive" else 1),("REFERENCE_DISAGREES_SOURCE",case,scenario,gold)
        assert actual["exit"] in (0,2) if scenario=="positive" else actual["exit"] in (1,2),\
          ("INDEPENDENT_KERNEL_WRONG_VERDICT",case,scenario,actual)
    results.append(row)
report={
  "pinned_independent_checker":"ff003e7fad888d39a40cfd2375885fe20e3209fa",
  "pinned_reference":"intgrah/sokonanoda@7645b1e1fcacfe410c99141f1234381d995b325d",
  "source":"exact positive source subterms; negative changes only final expected Eq Bool value",
  "meta":{"original_checker_sha256":hashlib.sha256(nucleus.read_bytes()).hexdigest(),
          "independent_reference_sha256":hashlib.sha256(reference.read_bytes()).hexdigest()},
  "cases":results,
  "source_derived":True,"no_kernel_semantic_changes":True,
  "decision":"BOUNDARY_LOCALIZATION_ONLY_NO_PROMOTION"}
(out/"decide-subproof-gate.json").write_text(json.dumps(report,indent=2,ensure_ascii=False)+"\n")
print("NUCLEUS_DECIDE_SUBPROOF_DECISION="+json.dumps({
 "cases":len(results),"positive_nucleus":[r["paths"]["positive"]["nucleus"]["exit"] for r in results],
 "negative_nucleus":[r["paths"]["negative"]["nucleus"]["exit"] for r in results],
 "decision":report["decision"]
},ensure_ascii=False),flush=True)
