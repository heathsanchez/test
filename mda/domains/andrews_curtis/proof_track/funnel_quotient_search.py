#!/usr/bin/env python3
from __future__ import annotations
import argparse, heapq, importlib.util, json, sys
from pathlib import Path

CHARS={1:"x",-1:"X",2:"y",-2:"Y"}
BACK={"x":1,"X":-1,"y":2,"Y":-2}

def load_module(path,name):
    spec=importlib.util.spec_from_file_location(name,path)
    m=importlib.util.module_from_spec(spec); spec.loader.exec_module(m); return m

def intword(s): return tuple(BACK[c] for c in s)
def wordstr(w): return "".join(CHARS[x] for x in w)

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--acc-root",required=True)
    ap.add_argument("--acsolverx-root",required=True)
    ap.add_argument("--projector-script",required=True)
    ap.add_argument("--challenge-id",default="ac-01684")
    ap.add_argument("--node-cap",type=int,default=60000)
    ap.add_argument("--out-dir",required=True)
    a=ap.parse_args()

    proj=load_module(Path(a.projector_script),"proj")
    root=Path(__file__).resolve().parents[4]
    sys.path.insert(0,str(root/"andrews_curtis"))
    from solver_v2_gssub import load_gssub,int_word_to_str

    acc=Path(a.acc_root); sys.path.insert(0,str(acc/"competition"/"tools"))
    from verifier import core

    manifest=json.loads((acc/"competition/tools/verifier/data/manifest.json").read_text())
    by={c["challenge_id"]:c for c in manifest["challenges"]}
    c=by[a.challenge_id]
    official_cap=manifest["limits"]["max_total_relator_length"]
    exact=tuple(tuple(w) for w in c["initial_relators"])
    ns=load_gssub(Path(a.acsolverx_root))

    reduce_relator=ns["reduce_relator_nj"]
    canonical_pair=ns["canonical_pair_nj"]
    state_to_key=ns["state_to_key"]
    str_to_arr=ns["str_to_arr"]
    get_neighbors=ns["get_neighbors_nj"]

    def canonical_key_pair(r0,r1):
        a0=reduce_relator(r0); a1=reduce_relator(r1)
        c0,c1=canonical_pair(a0,a1)
        return state_to_key((c0,c1))

    initial=canonical_key_pair(
        str_to_arr(int_word_to_str(exact[0])),
        str_to_arr(int_word_to_str(exact[1]))
    )
    initial_total=len(initial[0])+len(initial[1])
    qcap=min(100,max(initial_total+36,48))
    target_key=canonical_key_pair(str_to_arr("x"),str_to_arr("y"))

    norm_cache={}
    norm_stats={"changed_keys":0,"macro_steps":0,"macro_atomic_cost":0,"max_drop":0}

    def funnel_normalize_key(key):
        if key in norm_cache: return norm_cache[key]
        s=(intword(key[0]),intword(key[1]))
        start=s; steps=0; atomic=0
        while True:
            arms=[]
            for i in (0,1):
                end,best,_=proj.project_state(s,i)
                gain=sum(map(len,s))-sum(map(len,end))
                if gain<=0: continue
                macro,chk,peak=proj.compile_projection(core,s,i,best["w"])
                if chk!=end: raise RuntimeError("projection compile mismatch")
                if peak>official_cap: continue
                arms.append((-gain,len(macro),i,tuple(best["w"]),end,tuple(macro)))
            if not arms: break
            arms.sort()
            ng,cost,i,w,end,macro=arms[0]
            s=end; steps+=1; atomic+=len(macro)
        nk=canonical_key_pair(str_to_arr(wordstr(s[0])),str_to_arr(wordstr(s[1])))
        drop=(len(key[0])+len(key[1]))-(len(nk[0])+len(nk[1]))
        if nk!=key:
            norm_stats["changed_keys"]+=1
            norm_stats["macro_steps"]+=steps
            norm_stats["macro_atomic_cost"]+=atomic
            norm_stats["max_drop"]=max(norm_stats["max_drop"],drop)
        norm_cache[key]=(nk,{"steps":steps,"atomic_cost":atomic,"drop":drop})
        return norm_cache[key]

    def search(use_funnel):
        pq=[(initial_total,0,initial)]
        best_depth={initial:0}
        nodes=0; generated=0; raw_to_norm_changes=0; quotient_hits=0
        best_total=initial_total; best_key=initial; first_target=None
        seen_raw=set([initial])
        seen_norm=set([initial])
        while pq and nodes<a.node_cap:
            _,depth,key=heapq.heappop(pq)
            if depth!=best_depth.get(key): continue
            nodes+=1
            kt=len(key[0])+len(key[1])
            if kt<best_total:
                best_total=kt;best_key=key
                print("QUOTIENT_SEARCH_RECORD",json.dumps({
                  "arm":"funnel" if use_funnel else "baseline",
                  "nodes":nodes,"depth":depth,"best_total":best_total,
                  "key":[key[0],key[1]]
                },sort_keys=True),flush=True)
            if key==target_key:
                first_target={"nodes":nodes,"depth":depth}; break
            a0,b0=str_to_arr(key[0]),str_to_arr(key[1])
            nd=depth+1
            for nr0,nr1 in get_neighbors(a0,b0):
                r0,r1=reduce_relator(nr0),reduce_relator(nr1)
                if len(r0)+len(r1)>=qcap: continue
                raw=canonical_key_pair(r0,r1)
                generated+=1; seen_raw.add(raw)
                nk=raw
                if use_funnel:
                    nk,_meta=funnel_normalize_key(raw)
                    if nk!=raw: raw_to_norm_changes+=1
                    if nk in seen_norm and raw not in seen_norm:
                        quotient_hits+=1
                seen_norm.add(nk)
                if nd>=best_depth.get(nk,10**18): continue
                best_depth[nk]=nd
                heapq.heappush(pq,(len(nk[0])+len(nk[1]),nd,nk))
        return {
          "nodes_popped":nodes,"generated":generated,
          "unique_raw_seen":len(seen_raw),"unique_search_keys":len(best_depth),
          "best_total":best_total,"best_key":[best_key[0],best_key[1]],
          "target_found":first_target is not None,"target":first_target,
          "queue_remaining":len(pq),
          "raw_to_norm_changes":raw_to_norm_changes,
          "quotient_duplicate_hits":quotient_hits
        }

    baseline=search(False)
    funnel=search(True)
    report={
      "experiment":"ACC_FUNNEL_QUOTIENT_SEARCH_V1",
      "challenge_id":a.challenge_id,
      "node_cap":a.node_cap,"qcap":qcap,
      "baseline":baseline,"funnel":funnel,
      "best_total_gain":baseline["best_total"]-funnel["best_total"],
      "node_gain_to_target":(
        baseline["target"]["nodes"]-funnel["target"]["nodes"]
        if baseline["target_found"] and funnel["target_found"] else None
      ),
      "normalizer_cache_size":len(norm_cache),
      "normalizer_stats":norm_stats,
      "status":(
        "FUNNEL_QUOTIENT_SEARCH_GAIN"
        if funnel["target_found"] and not baseline["target_found"]
        or funnel["best_total"]<baseline["best_total"]
        or (baseline["target_found"] and funnel["target_found"] and funnel["target"]["nodes"]<baseline["target"]["nodes"])
        else "NO_FUNNEL_QUOTIENT_SEARCH_GAIN"
      ),
      "claim_boundary":"Same ACSolverX GS-Sub neighbor generator and node/length caps. Funnel arm only applies a deterministic, strict length-decreasing, officially replayed normalization before deduplication; it adds no exploratory move."
    }
    out=Path(a.out_dir);out.mkdir(parents=True,exist_ok=True)
    (out/"report.json").write_text(json.dumps(report,indent=2,sort_keys=True)+"\n")
    print("FUNNEL_QUOTIENT_SEARCH",json.dumps(report,sort_keys=True))

if __name__=="__main__": main()
