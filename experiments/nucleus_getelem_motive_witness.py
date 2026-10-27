#!/usr/bin/env python3
"""Exact-source Eq.ndrec / GetElem motive witness and falsifying receiver mutant.

This only inspects the pinned Lean NDJSON graph and compares external checker
verdicts. It never installs conversion or infers authority from matching names.
"""
import hashlib, json, os, pathlib, subprocess, sys

ROOT=pathlib.Path("/tmp/getelem")
EVIDENCE=ROOT/"evidence"
ORIGINAL=ROOT/"exact-source-prefix.ndjson"
SHA="fa21f2a48d84f66aeffc252e988d370634db1ad0706ebc717efdd7d5d379b71a"
OFFICIAL="/tmp/arena-reference/checkers/official/.lake/build/bin/kernel"
NUCLEUS="metatron-kernel/target/release/metatron-kernel"

def digest(raw):return hashlib.sha256(raw).hexdigest()
def head(exprs, index):
    args=[];seen=set()
    while "app" in exprs[index]:
        if index in seen:raise ValueError("Cyclic AST")
        seen.add(index)
        app=exprs[index]["app"]
        args.insert(0,app["arg"])
        index=app["fn"]
    return index,args
def run(command,data):
    p=subprocess.run(command,input=data,capture_output=True,timeout=180)
    return {"exit":p.returncode,"stderr_tail":p.stderr.decode(errors="replace")[-1000:]}
def main():
    EVIDENCE.mkdir(parents=True,exist_ok=True)
    report={"status":"UNKNOWN","source_sha256":SHA}
    try:
        data=ORIGINAL.read_bytes()
        assert digest(data)==SHA
        lines=data.splitlines(keepends=True)
        rows=[json.loads(x) for x in lines]
        assert rows[0]["meta"]["format"]["version"]=="3.1.0"
        exprs={o["ie"]:o for o in rows if "ie" in o}
        names={0:""}
        for o in rows:
            if "in" in o:
                node=o.get("str") or o.get("num")
                if node:
                    par=node["pre"]
                    assert par in names
                    names[o["in"]]=names[par]+("." if par else "")+str(node.get("str",node.get("i")))
        def shape(index,required):
            h,args=head(exprs,index)
            obj=exprs[h]
            const=obj.get("const")
            name=names.get(const["name"]) if const else None
            assert name==required,(index,name,required)
            return {"expr":index,"head":name,"head_expr":h,"args":args}
        witness={
            "ndrec":shape(84287,"Eq.ndrec"),
            "left_eq":shape(84154,"Eq"),
            "right_eq":shape(84272,"Eq"),
            "left_some":shape(84153,"Option.some"),
            "right_some":shape(84271,"Option.some"),
            "left_getElem":shape(84152,"GetElem.getElem"),
            "right_getElem":shape(84270,"GetElem.getElem"),
            "right_cons":shape(84257,"List.cons"),
        }
        assert len(witness["ndrec"]["args"])==5
        assert witness["ndrec"]["args"][2]==84274
        assert witness["ndrec"]["args"][3]==84285
        assert witness["ndrec"]["args"][4]==16
        assert witness["left_eq"]["args"][-1]==84153
        assert witness["right_eq"]["args"][-1]==84271
        assert witness["left_some"]["args"][-1]==84152
        assert witness["right_some"]["args"][-1]==84270
        assert witness["right_getElem"]["args"][-3]==84257
        report["witness"]=witness
        # The mutant changes just the dependent motive's final receiver.
        # This is a valid NDJSON source edit, not a claim that old and new
        # receivers were ever proven convertible.
        lines2=lines.copy()
        pos=next(i for i,o in enumerate(rows) if o.get("ie")==84272)
        changed=json.loads(lines2[pos])
        assert changed["app"]=={"arg":84271,"fn":84260}
        changed["app"]["arg"]=84153
        lines2[pos]=(json.dumps(changed,separators=(",",":"),ensure_ascii=False)+"\n").encode()
        altered=b"".join(lines2)
        assert altered!=data
        path=EVIDENCE/"forged-dependent-motive.ndjson"
        path.write_bytes(altered)
        assert json.loads(altered.split(b"\n",1)[0])==rows[0]
        report["mutant"]={"changed_expr":84272,"field":"app.arg",
            "old_receiver":84271,"new_receiver":84153,
            "sha256":digest(altered),"proof_term_unchanged_except_motive_receiver":True}
        orig=run([OFFICIAL,str(ORIGINAL)],None)
        forged=run([OFFICIAL,str(path)],None)
        assert orig["exit"]==0,("official original not accepted",orig)
        assert forged["exit"]==1,("mutant did not independently falsify premise",forged)
        # Second, narrower falsification: keep the SAME List element type and
        # receiver, but replace only the Nat index of GetElem.getElem.
        # Its dependent bounds proof stays untouched. This cannot be
        # dismissed as changing the Option carrier from List to an element.
        lines3=lines.copy()
        index_pos=next(i for i,o in enumerate(rows) if o.get("ie")==84269)
        index_node=json.loads(lines3[index_pos])
        assert index_node["app"]=={"arg":2,"fn":84268}
        assert names[exprs[137]["const"]["name"]]=="Nat.zero"
        index_node["app"]["arg"]=137
        lines3[index_pos]=(json.dumps(index_node,separators=(",",":"),ensure_ascii=False)+"\\n").encode()
        index_mutant=b"".join(lines3)
        index_path=EVIDENCE/"forged-dependent-index.ndjson"
        index_path.write_bytes(index_mutant)
        typed_forged=run([OFFICIAL,str(index_path)],None)
        report["index_mutant"]={"changed_expr":84269,"old_index":2,
            "new_index":137,"new_index_type":"Nat",
            "dependent_proof_left_unchanged":True,
            "sha256":digest(index_mutant),"official":typed_forged}
        assert typed_forged["exit"]==1,(
            "incorrect-index mutant was not rejected by Lean",typed_forged)
        report["official"]={"authentic":orig,"mutated":forged}
        modes={}
        for mode in ("default","origin"):
            e=os.environ.copy()
            if mode=="origin":
                ledger=json.loads(pathlib.Path("metatron-kernel/evidence/performance/owned-environment-2026-10-13/nucleus-owned-environment-frozen196.json").read_text())
                e.update({"NUCLEUS_EXPERIMENTAL_"+n:"1" for n in ledger["origin_flags"]})
            e["NUCLEUS_EXPERIMENTAL_CERTIFIED_QUOT_IOTA"]="1"
            e["NUCLEUS_EXPERIMENTAL_SOURCE_PROOF_IRREL"]="1"
            e["NUCLEUS_EXPERIMENTAL_NEUTRAL_PAIR_PROOF_IRREL"]="1"
            def check(raw):
                p=subprocess.run([NUCLEUS],input=raw,capture_output=True,timeout=180,env=e)
                return {"exit":p.returncode,"stderr_tail":p.stderr.decode(errors="replace")[-700:]}
            a=check(data);b=check(altered);c=check(index_mutant)
            assert a["exit"] in (0,2),(mode,"original incorrectly rejected",a)
            assert b["exit"] in (1,2),(mode,"receiver forgery accepted",b)
            assert c["exit"] in (1,2),(mode,"index forgery accepted",c)
            modes[mode]={"authentic":a,"mutated":b,"wrong_index":c}
        report["nucleus"]=modes
        report["status"]="SOURCE_WITNESS_MUTANT_REJECTED_BOUNDED"
        result=0
    except Exception as exc:
        report["error"]=repr(exc)
        result=1
    finally:
        (EVIDENCE/"eq-motive-witness.json").write_text(json.dumps(report,indent=2,ensure_ascii=False)+"\n")
        print(json.dumps({k:v for k,v in report.items() if k!="witness"},ensure_ascii=False),flush=True)
    return result
if __name__=="__main__":sys.exit(main())
