#!/usr/bin/env python3
from __future__ import annotations
import argparse, importlib.util, json, sys, zipfile
from collections import defaultdict
from pathlib import Path

CHAR_TO_INT={"x":1,"X":-1,"y":2,"Y":-2}

def load_module(path,name):
    spec=importlib.util.spec_from_file_location(name,path)
    m=importlib.util.module_from_spec(spec); spec.loader.exec_module(m); return m

def word(s): return tuple(CHAR_TO_INT[c] for c in s)

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--acc-root",required=True)
    ap.add_argument("--acsolverx-root",required=True)
    ap.add_argument("--projector-script",required=True)
    ap.add_argument("--artifacts-root",required=True)
    ap.add_argument("--out-dir",required=True)
    a=ap.parse_args()

    proj=load_module(Path(a.projector_script),"proj")
    root=Path(__file__).resolve().parents[4]
    sys.path.insert(0,str(root/"andrews_curtis"))
    from solver_v2_gssub import load_gssub,int_word_to_str

    acc=Path(a.acc_root); sys.path.insert(0,str(acc/"competition"/"tools"))
    from verifier import core
    manifest=json.loads((acc/"competition/tools/verifier/data/manifest.json").read_text())
    limit=manifest["limits"]["max_total_relator_length"]
    ns=load_gssub(Path(a.acsolverx_root))
    reduce_relator=ns["reduce_relator_nj"]; canonical_pair=ns["canonical_pair_nj"]
    state_to_key=ns["state_to_key"]; str_to_arr=ns["str_to_arr"]

    def canonical_exact(s):
        a0=reduce_relator(str_to_arr(int_word_to_str(s[0])))
        a1=reduce_relator(str_to_arr(int_word_to_str(s[1])))
        return state_to_key(canonical_pair(a0,a1))

    all_reports=[]
    global_rows=[]
    for p in sorted(Path(a.artifacts_root).rglob("opportunities.json")):
        rows=json.loads(p.read_text())
        if not rows: continue
        cid=p.parent.name if p.parent.name.startswith("ac-") else "unknown"
        verified=[]
        classes=defaultdict(set)
        for r in rows:
            s=(word(r["state"][0]),word(r["state"][1]))
            i=int(r["i"])
            end,best,_=proj.project_state(s,i)
            macro,chk,peak=proj.compile_projection(core,s,i,best["w"])
            if chk!=end: raise RuntimeError(("macro mismatch",cid,r))
            if peak>limit: raise RuntimeError(("limit breach",cid,peak))
            key=canonical_exact(end)
            if list(key)!=r["projected_key"]:
                raise RuntimeError(("canonical mismatch",cid,key,r["projected_key"]))
            if total:=sum(map(len,s))-sum(map(len,end)):
                if total!=r["gain"]: raise RuntimeError(("gain mismatch",cid,total,r["gain"]))
            classes[key].add(s)
            verified.append({
                "state":[list(s[0]),list(s[1])],
                "projected_key":[key[0],key[1]],
                "gain":r["gain"],"i":i,
                "w":list(best["w"]),"macro_cost":len(macro),"peak":peak
            })
        exact_states={tuple(map(tuple,x["state"])) for x in verified}
        multi=[v for v in classes.values() if len(v)>1]
        rep={
            "challenge_id":cid,
            "rows":len(verified),
            "distinct_exact_positive_states":len(exact_states),
            "distinct_projected_keys":len(classes),
            "multi_classes":len(multi),
            "induced_collisions":sum(len(v)-1 for v in multi),
            "largest_class":max([len(v) for v in multi] or [1]),
            "all_macros_officially_replayed":True,
            "max_gain":max(x["gain"] for x in verified),
            "max_macro_cost":max(x["macro_cost"] for x in verified),
        }
        all_reports.append(rep)
        global_rows.extend((cid,x) for x in verified)
        print("FUNNEL_COLLISION_CASE",json.dumps(rep,sort_keys=True))

    summary={
      "experiment":"ACC_FUNNEL_QUOTIENT_COLLISION_SYNTHESIS_V1",
      "completed_shards":len(all_reports),
      "verified_rows":sum(x["rows"] for x in all_reports),
      "distinct_positive_states":sum(x["distinct_exact_positive_states"] for x in all_reports),
      "projected_keys":sum(x["distinct_projected_keys"] for x in all_reports),
      "induced_collisions":sum(x["induced_collisions"] for x in all_reports),
      "largest_class":max([x["largest_class"] for x in all_reports] or [1]),
      "status":"VERIFIED_MANY_TO_ONE_FUNNEL_QUOTIENT" if sum(x["induced_collisions"] for x in all_reports)>0 else "NO_FUNNEL_COLLISIONS",
      "claim_boundary":"Synthesis over the four completed observation-only 100k-node frontier shards. Each selected funnel macro is replayed through the pinned official transition semantics; projected keys additionally use the already-proved orientation/permutation quotient."
    }
    out=Path(a.out_dir);out.mkdir(parents=True,exist_ok=True)
    (out/"report.json").write_text(json.dumps(summary,indent=2,sort_keys=True)+"\n")
    (out/"cases.json").write_text(json.dumps(all_reports,indent=2,sort_keys=True)+"\n")
    print("FUNNEL_COLLISION_SUMMARY",json.dumps(summary,sort_keys=True))

if __name__=="__main__": main()
