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
    ap.add_argument("--expansion-cap",type=int,default=60000)
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
    target=canonical_key_pair(str_to_arr("x"),str_to_arr("y"))

    norm_cache={}
    def normalize(key):
        if key in norm_cache: return norm_cache[key]
        s=(intword(key[0]),intword(key[1]))
        start_total=sum(map(len,s)); steps=0; atomic=0
        while True:
            arms=[]
            for i in (0,1):
                end,best,_=proj.project_state(s,i)
                gain=sum(map(len,s))-sum(map(len,end))
                if gain<=0: continue
                macro,chk,peak=proj.compile_projection(core,s,i,best["w"])
                if chk!=end: raise RuntimeError("macro mismatch")
                if peak>official_cap: continue
                arms.append((-gain,len(macro),i,tuple(best["w"]),end,tuple(macro)))
            if not arms: break
            arms.sort()
            ng,cost,i,w,end,macro=arms[0]
            s=end; steps+=1; atomic+=len(macro)
        nk=canonical_key_pair(str_to_arr(wordstr(s[0])),str_to_arr(wordstr(s[1])))
        meta={"changed":nk!=key,"drop":(len(key[0])+len(key[1]))-(len(nk[0])+len(nk[1])),
              "steps":steps,"atomic_cost":atomic}
        norm_cache[key]=(nk,meta)
        return nk,meta

    def run(use_quotient):
        pq=[(initial_total,0,initial)]
        best_depth={initial:0}
        expanded=set()
        expansions=0; raw_pops=0; generated=0
        quotient_skips=0; changed_pops=0; total_drop=0
        best_total=initial_total; best_key=initial; first_target=None
        while pq and expansions<a.expansion_cap:
            _,depth,key=heapq.heappop(pq)
            if depth!=best_depth.get(key): continue
            raw_pops+=1
            ek=key
            if use_quotient:
                ek,meta=normalize(key)
                if meta["changed"]:
                    changed_pops+=1; total_drop+=meta["drop"]
            if ek in expanded:
                if use_quotient: quotient_skips+=1
                continue
            expanded.add(ek); expansions+=1
            et=len(ek[0])+len(ek[1])
            if et<best_total:
                best_total=et;best_key=ek
                print("LAZY_QUOTIENT_RECORD",json.dumps({
                  "arm":"quotient" if use_quotient else "baseline",
                  "expansions":expansions,"raw_pops":raw_pops,
                  "depth":depth,"best_total":best_total,"key":[ek[0],ek[1]]
                },sort_keys=True),flush=True)
            if ek==target:
                first_target={"expansions":expansions,"raw_pops":raw_pops,"depth":depth}
                break

            e0,e1=str_to_arr(ek[0]),str_to_arr(ek[1])
            nd=depth+1
            for nr0,nr1 in get_neighbors(e0,e1):
                r0,r1=reduce_relator(nr0),reduce_relator(nr1)
                if len(r0)+len(r1)>=qcap: continue
                nk=canonical_key_pair(r0,r1)
                generated+=1
                if nd>=best_depth.get(nk,10**18): continue
                best_depth[nk]=nd
                heapq.heappush(pq,(len(nk[0])+len(nk[1]),nd,nk))
        return {
          "expansions":expansions,"raw_pops":raw_pops,"generated":generated,
          "discovered_raw_keys":len(best_depth),"expanded_keys":len(expanded),
          "best_total":best_total,"best_key":[best_key[0],best_key[1]],
          "target_found":first_target is not None,"target":first_target,
          "queue_remaining":len(pq),
          "quotient_skips":quotient_skips,"changed_pops":changed_pops,
          "total_strict_drop_on_changed_pops":total_drop
        }

    baseline=run(False)
    quotient=run(True)
    report={
      "experiment":"ACC_LAZY_FUNNEL_QUOTIENT_SEARCH_V2",
      "challenge_id":a.challenge_id,
      "expansion_cap":a.expansion_cap,"qcap":qcap,
      "baseline":baseline,"quotient":quotient,
      "best_total_gain":baseline["best_total"]-quotient["best_total"],
      "expansion_gain_to_target":(
        baseline["target"]["expansions"]-quotient["target"]["expansions"]
        if baseline["target_found"] and quotient["target_found"] else None
      ),
      "normalizer_cache_size":len(norm_cache),
      "status":(
        "LAZY_FUNNEL_QUOTIENT_SEARCH_GAIN"
        if (quotient["target_found"] and not baseline["target_found"])
        or quotient["best_total"]<baseline["best_total"]
        or (baseline["target_found"] and quotient["target_found"]
            and quotient["target"]["expansions"]<baseline["target"]["expansions"])
        else "NO_LAZY_FUNNEL_QUOTIENT_SEARCH_GAIN"
      ),
      "claim_boundary":"Existence-search comparison only. Same GS-Sub neighbor generator, qcap and expansion cap. Quotient arm applies only strict theorem-sound funnel contractions at pop time and treats them as zero-cost equivalences; certificate length is not claimed."
    }
    out=Path(a.out_dir);out.mkdir(parents=True,exist_ok=True)
    (out/"report.json").write_text(json.dumps(report,indent=2,sort_keys=True)+"\n")
    print("LAZY_FUNNEL_QUOTIENT_SEARCH",json.dumps(report,sort_keys=True))

if __name__=="__main__": main()
