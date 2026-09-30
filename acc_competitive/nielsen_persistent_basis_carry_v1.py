#!/usr/bin/env python3
"""Persistent-basis-frame compiler for #1-directed ACC Nielsen trajectories.

Unlike the public elementary decoder, basis automorphisms are carried as a
symbolic frame at zero immediate physical cost. Substitution edges are compiled
directly in the physical official state into the frame-transformed quotient
class, retaining cheap exact representatives across steps. Proof Atlas exits are
tested at every compiled layer. Every emitted candidate is replayed by the pinned
official verifier; only strict live improvements are written.
"""
from __future__ import annotations
import argparse, json, sqlite3, sys, time
from pathlib import Path

LETTER={1:"x",-1:"X",2:"y",-2:"Y"}
CODE={"x":1,"X":-1,"y":2,"Y":-2}
CONJ={(1,"x"):7,(1,"X"):6,(1,"y"):9,(1,"Y"):8,(2,"x"):11,(2,"X"):10,(2,"y"):13,(2,"Y"):12}
SWAP=(0,1,2,0,4,3)
MAP={-2:1,-1:2,1:3,2:4}
TARGET=((1,),(2,))

def key_state(s):
    return bytes([MAP[x] for x in s[0]]+[0]+[MAP[x] for x in s[1]])

def snapshot_map(path):
    o=json.loads(Path(path).read_text()); d=o.get("data",o); out={}
    for x in d["items"]:
        cid=x.get("problemId") or x.get("challengeId")
        if cid: out[str(cid)]=x
    return out

def to_pair(initial):
    return tuple("".join(LETTER[int(a)] for a in w) for w in initial)

def str_state(pair):
    return tuple(tuple(CODE[c] for c in w) for w in pair)

def compile_op(m):
    op=m.get("op")
    if op=="invert": return [0 if int(m["target"])==1 else 1]
    if op=="multiply":
        t,s=int(m["target"]),int(m["source"])
        if (t,s)==(1,2): return [2]
        if (t,s)==(2,1): return [4]
        raise ValueError(("bad multiply",m))
    if op=="conjugate": return [CONJ[(int(m["target"]),str(m["by"]))]]
    if op=="swap": return list(SWAP)
    raise ValueError(("unknown op",m))

def frame_key(ns,qstate,inverse_image,apply_hom):
    a=apply_hom(str(qstate[0]),inverse_image)
    b=apply_hom(str(qstate[1]),inverse_image)
    return ns["canonical_pair_str"](a,b)

def atlas_suffix(core,db,state,limit):
    s=state; out=[]; seen={s}
    for _ in range(limit):
        if s==TARGET:return tuple(out)
        row=db.execute("SELECT next_move FROM atlas WHERE state=?",(key_state(s),)).fetchone()
        if row is None or row[0] is None:return None
        m=int(row[0]); out.append(m); s=core.apply_move(s,m)
        if s in seen:return None
        seen.add(s)
    return None

def verify_candidate(core,stable_core,db,atlas_dist,c,limits,byid,sid,state,path,ac_best,stable_best):
    ad=atlas_dist.get(key_state(state))
    if ad is None:return None
    bound=ac_best
    if isinstance(stable_best,int):bound=max(bound,stable_best-2)
    if len(path)+ad>=bound:return None
    suffix=atlas_suffix(core,db,state,bound-len(path)+8)
    if suffix is None:return None
    cand=tuple(path)+tuple(suffix)
    v=core.verify(c,list(cand),c["move_spec_version"],limits)
    if not v.get("ok"):raise RuntimeError("official Atlas candidate replay failed")
    ans={"source_length":len(cand),"atlas_distance":len(suffix),
         "certificate_hash":v.get("certificate_hash"),"path":cand,
         "ac_strict":len(cand)<ac_best,"stable_strict":False}
    if sid and isinstance(stable_best,int) and len(cand)+2<stable_best:
        sc=byid[sid]; spath=list(cand)+[16,15]
        sv=stable_core.verify(sc,spath,sc["move_spec_version"],limits)
        if not sv.get("ok"):raise RuntimeError("stable transport replay failed")
        ans["stable_strict"]=True; ans["stable_path"]=tuple(spath)
        ans["stable_certificate_hash"]=sv.get("certificate_hash")
    return ans

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--acc-root",required=True)
    ap.add_argument("--acsolverx-root",required=True)
    ap.add_argument("--atlas",required=True)
    ap.add_argument("--snapshot-ac",required=True)
    ap.add_argument("--snapshot-stable",required=True)
    ap.add_argument("--target-ids-file",required=True)
    ap.add_argument("--out-dir",required=True)
    ap.add_argument("--budget",type=int,default=1000)
    ap.add_argument("--beam",type=int,default=32)
    ap.add_argument("--extra-total",type=int,default=120)
    a=ap.parse_args()

    acc=Path(a.acc_root); axs=Path(a.acsolverx_root)
    sys.path.insert(0,str(acc/"competition/tools"))
    from verifier import core,stable_core
    sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"andrews_curtis"))
    import solver_v2_gssub as S
    sys.path.insert(0,str(axs))
    from research.ac_hashfree_cascade_20260914 import hfcascade,verify as public_verify
    from research.supermoves_20260908 import certificate_decoder as cd
    from experiments.equivalence_classes.lib.words import apply_hom

    ns=S.load_gssub(axs)
    manifest=json.loads((acc/"competition/tools/verifier/data/manifest.json").read_text())
    limits=manifest["limits"]; byid={c["challenge_id"]:c for c in manifest["challenges"]}
    live_ac=snapshot_map(a.snapshot_ac); live_stable=snapshot_map(a.snapshot_stable)
    raw=json.loads(Path(a.target_ids_file).read_text())
    ids=[x["challenge_id"] if isinstance(x,dict) else str(x) for x in raw]

    db=sqlite3.connect(a.atlas)
    atlas_dist={bytes(k):int(d) for k,d in db.execute("SELECT state,distance FROM atlas")}
    reverse_paths,_=S.build_reverse(core,7,250000)

    out=Path(a.out_dir);out.mkdir(parents=True,exist_ok=True)
    rows=[]; strict={}; t0=time.time()
    for cid in ids:
        c=byid.get(cid); lr=live_ac.get(cid,{})
        ac_best=lr.get("currentBestLength")
        if c is None or not isinstance(ac_best,int):continue
        sid="sac-"+cid[3:]; stable_best=live_stable.get(sid,{}).get("currentBestLength")
        source_bound=ac_best
        if isinstance(stable_best,int):source_bound=max(source_bound,stable_best-2)
        exact=tuple(tuple(w) for w in c["initial_relators"])
        pair=to_pair(c["initial_relators"])
        total_cap=min(limits["max_total_relator_length"],max(100,sum(map(len,exact))+a.extra_total))
        rec={"challenge_id":cid,"live_best":ac_best,"stable_live_best":stable_best,
             "source_bound":source_bound,"beam_width":a.beam,"total_cap":total_cap}
        try:
            res=hfcascade.solve(pair,budget=a.budget,score="s20",gates=True,pair_descent=True,
                                engine="fast",closed_set="sorted",nielsen=True,perms=True,gate_when="pop")
            rec.update({"solved":bool(res["solved"]),"units":res["units"],
                        "mixed_steps":res.get("path_length"),"stage":res.get("stage")})
            if not res["solved"]:
                rec.update({"strict_ac":False,"strict_stable":False})
                rows.append(rec);print("BASIS_CARRY_CASE",json.dumps(rec,sort_keys=True),flush=True);continue
            public_verify.replay(pair,res["steps"],res["states"])
            if res.get("path_length") is not None and res["path_length"]>=source_bound:
                # Safe cheap admission: each accepted mixed step is state-changing or
                # an automorphism that must eventually be discharged.
                rec["mixed_depth_gate"]="FAIL"
            else:rec["mixed_depth_gate"]="PASS"

            inv_image=dict(cd.IDENTITY); applied=[]
            beam={exact:(0,())}
            if S.gssub_key(ns,exact)!=frame_key(ns,res["states"][0],inv_image,apply_hom):
                raise RuntimeError("initial frame invariant mismatch")

            subs_suffix=[0]*(len(res["steps"])+1)
            for i in range(len(res["steps"])-1,-1,-1):
                subs_suffix[i]=subs_suffix[i+1]+(1 if res["steps"][i].get("kind")=="substitution" else 0)

            best_join=None; atlas_contacts=0; layer_meta=[]; rejected=False
            for i,step in enumerate(res["steps"]):
                target_state=res["states"][i+1]
                if step.get("kind")=="automorphism":
                    image=step["images"]
                    inv_image=cd._compose(cd.elementary_inverse(image),inv_image)
                    applied.append(image)
                    desired=frame_key(ns,target_state,inv_image,apply_hom)
                    bad=sum(1 for st in beam if S.gssub_key(ns,st)!=desired)
                    if bad:
                        raise RuntimeError(f"frame invariant mismatch after automorphism: {bad}/{len(beam)}")
                    continue
                if step.get("kind")!="substitution":
                    raise RuntimeError(f"unsupported mixed step {step.get('kind')}")
                desired=frame_key(ns,target_state,inv_image,apply_hom)
                next_by={}
                raw_cands=0
                remaining=subs_suffix[i+1]
                for st,(cost,path) in beam.items():
                    cands=S.compiled_superneighbor_candidates(core,ns,st,desired,total_cap)
                    raw_cands+=len(cands)
                    for nxt,edge in cands:
                        nc=cost+len(edge)
                        # optimistic lower bound; basis discharge ignored deliberately.
                        if nc+remaining>=source_bound:continue
                        prev=next_by.get(nxt)
                        if prev is None or nc<prev[0]:
                            next_by[nxt]=(nc,path+tuple(edge))
                if not next_by:
                    rejected=True
                    layer_meta.append({"mixed_step":i+1,"kind":"substitution","raw_candidates":raw_cands,
                                       "distinct":0,"reason":"strict_bound_or_no_compilation"})
                    break
                ranked=sorted(((v[0],st,v[1]) for st,v in next_by.items()),
                              key=lambda x:(x[0],sum(map(len,x[1])),x[1]))[:max(1,a.beam)]
                beam={st:(cost,path) for cost,st,path in ranked}
                layer_meta.append({"mixed_step":i+1,"kind":"substitution","raw_candidates":raw_cands,
                                   "distinct":len(next_by),"beam":len(beam),"best_cost":ranked[0][0],
                                   "remaining_substitutions":remaining})
                for st,(cost,path) in beam.items():
                    if key_state(st) in atlas_dist:
                        atlas_contacts+=1
                        j=verify_candidate(core,stable_core,db,atlas_dist,c,limits,byid,sid,st,path,
                                           ac_best,stable_best)
                        if j and (best_join is None or j["source_length"]<best_join["source_length"]):
                            best_join=j
                if best_join is not None:break

            terminal_best=None
            if best_join is None and not rejected and beam:
                for st,(cost,path) in beam.items():
                    # Discharge the accumulated basis frame only once, at the end.
                    tr=cd._ElementaryTrace(tuple(S.int_word_to_str(w) for w in st))
                    for image in reversed(applied):cd._emit_tuple_image(tr,image)
                    tail=[]
                    for m in tr.moves:tail.extend(compile_op(m))
                    if cost+len(tail)>=source_bound:continue
                    cur=st
                    for m in tail:cur=core.apply_move(cur,m)
                    p2=path+tuple(tail)
                    # Prefer the existing Atlas; then tiny exact terminal reverse bank.
                    j=verify_candidate(core,stable_core,db,atlas_dist,c,limits,byid,sid,cur,p2,
                                       ac_best,stable_best)
                    if j and (terminal_best is None or j["source_length"]<terminal_best["source_length"]):
                        terminal_best=j
                    if j is None:
                        suffix=S.exact_terminal_suffix(core,cur,reverse_paths)
                        if suffix is not None and len(p2)+len(suffix)<source_bound:
                            cand=p2+tuple(suffix)
                            v=core.verify(c,list(cand),c["move_spec_version"],limits)
                            if v.get("ok"):
                                jj={"source_length":len(cand),"atlas_distance":None,
                                    "certificate_hash":v.get("certificate_hash"),"path":cand,
                                    "ac_strict":len(cand)<ac_best,"stable_strict":False}
                                if isinstance(stable_best,int) and len(cand)+2<stable_best:
                                    sc=byid[sid]; sp=list(cand)+[16,15]
                                    sv=stable_core.verify(sc,sp,sc["move_spec_version"],limits)
                                    if sv.get("ok"):
                                        jj["stable_strict"]=True;jj["stable_path"]=tuple(sp)
                                        jj["stable_certificate_hash"]=sv.get("certificate_hash")
                                if terminal_best is None or jj["source_length"]<terminal_best["source_length"]:
                                    terminal_best=jj

            win=best_join or terminal_best
            rec.update({"frame_automorphisms":len(applied),"atlas_contacts":atlas_contacts,
                        "compiled_layers":len(layer_meta),"rejected":rejected,
                        "best_prefix_cost":min((v[0] for v in beam.values()),default=None),
                        "strict_ac":False,"strict_stable":False,"layer_tail":layer_meta[-8:]})
            if win:
                rec.update({"source_length":win["source_length"],"certificate_hash":win.get("certificate_hash"),
                            "strict_ac":bool(win.get("ac_strict")),"strict_stable":bool(win.get("stable_strict"))})
                if rec["strict_ac"]:strict[cid]=win["path"]
                if rec["strict_stable"]:strict[sid]=win["stable_path"]
        except Exception as exc:
            rec.update({"error":f"{type(exc).__name__}: {exc}","strict_ac":False,"strict_stable":False})
        rows.append(rec);print("BASIS_CARRY_CASE",json.dumps(rec,sort_keys=True),flush=True)

    (out/"results.json").write_text(json.dumps(rows,indent=2,sort_keys=True)+"\n")
    (out/"pending_submission.txt").write_text("\n".join(
        f"{cid}: {json.dumps(list(m),separators=(',',':'))}" for cid,m in sorted(strict.items())
    )+("\n" if strict else ""))
    rep={"targets":len(rows),"mixed_solved":sum(bool(r.get("solved")) for r in rows),
         "strict_ac":sum(bool(r.get("strict_ac")) for r in rows),
         "strict_stable":sum(bool(r.get("strict_stable")) for r in rows),
         "pending_rows":len(strict),"errors":sum("error" in r for r in rows),
         "contacts":sum(r.get("atlas_contacts") or 0 for r in rows),
         "rejected":sum(bool(r.get("rejected")) for r in rows),
         "seconds":round(time.time()-t0,3)}
    (out/"report.json").write_text(json.dumps(rep,indent=2,sort_keys=True)+"\n")
    print("BASIS_CARRY_SUMMARY",json.dumps(rep,sort_keys=True),flush=True)
    db.close()

if __name__=="__main__":main()
