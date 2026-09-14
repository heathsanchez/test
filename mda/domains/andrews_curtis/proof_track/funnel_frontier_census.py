#!/usr/bin/env python3
from __future__ import annotations
import argparse, heapq, importlib.util, json, sys
from pathlib import Path

CHAR_TO_INT={"x":1,"X":-1,"y":2,"Y":-2}

def load_module(path,name):
    spec=importlib.util.spec_from_file_location(name,path)
    m=importlib.util.module_from_spec(spec); spec.loader.exec_module(m); return m

def str_to_intword(s):
    return tuple(CHAR_TO_INT[ch] for ch in s)

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--acc-root",required=True)
    ap.add_argument("--acsolverx-root",required=True)
    ap.add_argument("--projector-script",required=True)
    ap.add_argument("--challenge-id",required=True)
    ap.add_argument("--node-cap",type=int,default=100000)
    ap.add_argument("--out-dir",required=True)
    a=ap.parse_args()

    proj=load_module(Path(a.projector_script),"proj")
    root=Path(__file__).resolve().parents[4]
    sys.path.insert(0,str(root/"andrews_curtis"))
    from solver_v2_gssub import load_gssub,int_word_to_str

    acc=Path(a.acc_root)
    manifest=json.loads((acc/"competition/tools/verifier/data/manifest.json").read_text())
    by={c["challenge_id"]:c for c in manifest["challenges"]}
    c=by[a.challenge_id]
    exact=tuple(tuple(w) for w in c["initial_relators"])
    ns=load_gssub(Path(a.acsolverx_root))

    reduce_relator=ns["reduce_relator_nj"]
    canonical_pair=ns["canonical_pair_nj"]
    state_to_key=ns["state_to_key"]
    str_to_arr=ns["str_to_arr"]
    get_neighbors=ns["get_neighbors_nj"]

    initial=canonical_pair(
        reduce_relator(str_to_arr(int_word_to_str(exact[0]))),
        reduce_relator(str_to_arr(int_word_to_str(exact[1])),
    ))
    ikey=state_to_key(initial)
    initial_total=len(ikey[0])+len(ikey[1])
    qcap=min(100,max(initial_total+36,48))
    pq=[(initial_total,0,ikey)]
    best_depth={ikey:0}
    nodes=0
    opportunities=[]
    record_gain=0
    first_positive=None

    while pq and nodes<a.node_cap:
        _,depth,key=heapq.heappop(pq)
        if depth!=best_depth.get(key): continue
        nodes+=1
        aarr,barr=str_to_arr(key[0]),str_to_arr(key[1])
        state=(str_to_intword(key[0]),str_to_intword(key[1]))
        cur_total=len(key[0])+len(key[1])
        nd=depth+1

        raw_neighbors=[]
        ordinary_keys=set()
        ordinary_best=10**9
        for nr1,nr2 in get_neighbors(aarr,barr):
            nr1r,nr2r=reduce_relator(nr1),reduce_relator(nr2)
            if len(nr1r)+len(nr2r)>=qcap: continue
            c1,c2=canonical_pair(nr1r,nr2r)
            knew=state_to_key((c1,c2))
            ordinary_keys.add(knew)
            ordinary_best=min(ordinary_best,len(c1)+len(c2))
            raw_neighbors.append(knew)

        arms=[]
        for i in (0,1):
            end,best,_ties=proj.project_state(state,i)
            endstr=(int_word_to_str(end[0]),int_word_to_str(end[1]))
            er1=reduce_relator(str_to_arr(endstr[0]))
            er2=reduce_relator(str_to_arr(endstr[1]))
            ec1,ec2=canonical_pair(er1,er2)
            ekey=state_to_key((ec1,ec2))
            projected_total=len(ec1)+len(ec2)
            gain=cur_total-projected_total
            arms.append({
                "i":i,"gain":gain,"w":list(best["w"]),
                "projected_total":projected_total,
                "projected_key":[ekey[0],ekey[1]],
                "novel_vs_ordinary":ekey not in ordinary_keys,
                "beats_ordinary_one_step":ordinary_best<10**9 and projected_total<ordinary_best,
                "ordinary_best":None if ordinary_best==10**9 else ordinary_best,
            })
        arms.sort(key=lambda z:(-z["gain"],z["projected_total"],z["i"],z["w"]))
        fb=arms[0]

        if fb["gain"]>0:
            rec={"pop_index":nodes,"depth":depth,"state":[key[0],key[1]],
                 "state_total":cur_total,**fb}
            opportunities.append(rec)
            if first_positive is None: first_positive=rec
            if fb["gain"]>record_gain:
                record_gain=fb["gain"]
                print("FUNNEL_FRONTIER_RECORD",json.dumps({"challenge_id":a.challenge_id,**rec},sort_keys=True),flush=True)

        for knew in raw_neighbors:
            if nd>=best_depth.get(knew,10**18): continue
            best_depth[knew]=nd
            heapq.heappush(pq,(len(knew[0])+len(knew[1]),nd,knew))

    opportunities.sort(key=lambda z:(-z["gain"],z["pop_index"],z["depth"]))
    best=opportunities[0] if opportunities else None
    report={
        "experiment":"ACC_FUNNEL_FRONTIER_CENSUS_V1",
        "challenge_id":a.challenge_id,
        "node_cap":a.node_cap,
        "nodes_popped":nodes,
        "qcap":qcap,
        "opportunity_count":len(opportunities),
        "first_positive":first_positive,
        "best_opportunity":best,
        "max_gain":0 if best is None else best["gain"],
        "novel_positive_count":sum(bool(z["novel_vs_ordinary"]) for z in opportunities),
        "beats_ordinary_count":sum(bool(z["beats_ordinary_one_step"]) for z in opportunities),
        "status":"FUNNEL_OPPORTUNITY_FOUND" if opportunities else "NO_FUNNEL_OPPORTUNITY_IN_CENSUS",
        "claim_boundary":"Observation-only instrumentation of unchanged GS-Sub search; no funnel transition was admitted into search."
    }
    out=Path(a.out_dir); out.mkdir(parents=True,exist_ok=True)
    (out/"report.json").write_text(json.dumps(report,indent=2,sort_keys=True)+"\n")
    (out/"opportunities.json").write_text(json.dumps(opportunities[:500],indent=2,sort_keys=True)+"\n")
    print("FUNNEL_FRONTIER_SUMMARY",json.dumps({
        k:report[k] for k in ["challenge_id","nodes_popped","opportunity_count","max_gain","novel_positive_count","beats_ordinary_count","status"]
    },sort_keys=True))

if __name__=="__main__":
    main()
