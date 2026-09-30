#!/usr/bin/env python3
from __future__ import annotations
import argparse, json, sqlite3, sys, time
from pathlib import Path

LETTER={1:"x",-1:"X",2:"y",-2:"Y"}
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

def compile_op(m):
    op=m.get("op")
    if op=="invert":
        return [0 if int(m["target"])==1 else 1]
    if op=="multiply":
        t,s=int(m["target"]),int(m["source"])
        if (t,s)==(1,2): return [2]
        if (t,s)==(2,1): return [4]
        raise ValueError(("bad multiply",m))
    if op=="conjugate":
        return [CONJ[(int(m["target"]),str(m["by"]))]]
    if op=="swap":
        return list(SWAP)
    raise ValueError(("unknown elementary op",m))

def atlas_suffix(core,db,state,limit):
    out=[]; s=state; seen={s}
    for _ in range(limit):
        if s==TARGET: return out
        row=db.execute("SELECT next_move FROM atlas WHERE state=?",(key_state(s),)).fetchone()
        if row is None or row[0] is None: return None
        m=int(row[0]); out.append(m); s=core.apply_move(s,m)
        if s in seen: return None
        seen.add(s)
    return None

def maybe_join(core,db,atlas_dist,c,limits,physical,prefix,ac_best,stable_best,byid,sid):
    ad=atlas_dist.get(key_state(physical))
    if ad is None: return None
    source_bound=ac_best
    if isinstance(stable_best,int): source_bound=max(source_bound,stable_best-2)
    if len(prefix)+ad>=source_bound: return {"contact":True,"competitive":False,"atlas_distance":ad}
    suffix=atlas_suffix(core,db,physical,source_bound-len(prefix)+8)
    if suffix is None: return {"contact":True,"competitive":False,"atlas_distance":ad,"suffix_missing":True}
    path=prefix+suffix
    v=core.verify(c,path,c["move_spec_version"],limits)
    if not v.get("ok"): raise RuntimeError("atlas candidate failed official verifier")
    out={"contact":True,"competitive":True,"atlas_distance":ad,"source_length":len(path),
         "certificate_hash":v.get("certificate_hash"),"path":path,
         "ac_strict":len(path)<ac_best,"stable_strict":False}
    if sid and isinstance(stable_best,int) and len(path)+2<stable_best:
        sc=byid[sid]
        from verifier import stable_core
        spath=path+[16,15]
        sv=stable_core.verify(sc,spath,sc["move_spec_version"],limits)
        if not sv.get("ok"): raise RuntimeError("stable lift failed official verifier")
        out["stable_strict"]=True; out["stable_path"]=spath
        out["stable_certificate_hash"]=sv.get("certificate_hash")
    return out

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
    a=ap.parse_args()

    acc=Path(a.acc_root); axs=Path(a.acsolverx_root)
    sys.path.insert(0,str(acc/"competition/tools"))
    from verifier import core
    sys.path.insert(0,str(axs))
    from research.ac_hashfree_cascade_20260914 import hfcascade, verify as public_verify
    from research.supermoves_20260908 import certificate_decoder as cd
    from experiments.equivalence_classes.lib.words import apply_hom, free_reduce, inv

    manifest=json.loads((acc/"competition/tools/verifier/data/manifest.json").read_text())
    limits=manifest["limits"]; byid={c["challenge_id"]:c for c in manifest["challenges"]}
    live_ac=snapshot_map(a.snapshot_ac); live_stable=snapshot_map(a.snapshot_stable)
    ids=json.loads(Path(a.target_ids_file).read_text())
    ids=[x["challenge_id"] if isinstance(x,dict) else str(x) for x in ids]

    db=sqlite3.connect(a.atlas)
    atlas_dist={bytes(k):int(d) for k,d in db.execute("SELECT state,distance FROM atlas")}
    out=Path(a.out_dir); out.mkdir(parents=True,exist_ok=True)
    rows=[]; strict={}; t0=time.time()

    for cid in ids:
        c=byid.get(cid); lr=live_ac.get(cid,{})
        best=lr.get("currentBestLength")
        if c is None or not isinstance(best,int): continue
        sid="sac-"+cid[3:]; sb=live_stable.get(sid,{}).get("currentBestLength")
        pair=to_pair(c["initial_relators"])
        rec={"challenge_id":cid,"live_best":best,"stable_live_best":sb}
        try:
            res=hfcascade.solve(pair,budget=a.budget,score="s20",gates=True,pair_descent=True,
                                engine="fast",closed_set="sorted",nielsen=True,perms=True,gate_when="pop")
            rec.update({"solved":bool(res["solved"]),"units":res["units"],"mixed_steps":res.get("path_length")})
            if not res["solved"]:
                rows.append(rec); print("PHYSICAL_ATLAS_CASE",json.dumps(rec,sort_keys=True),flush=True); continue
            public_verify.replay(pair,res["steps"],res["states"])

            trace=cd._ElementaryTrace(pair)
            inverse_image=dict(cd.IDENTITY)
            cd._emit_canonicalization(trace,pair,res["states"][0],inverse_image)
            physical=tuple(tuple(w) for w in c["initial_relators"])
            prefix=[]; emitted=0; contacts=0; best_join=None

            def flush_new():
                nonlocal physical,emitted,contacts,best_join
                while emitted < len(trace.moves):
                    for m in compile_op(trace.moves[emitted]):
                        prefix.append(m); physical=core.apply_move(physical,m)
                        ad=atlas_dist.get(key_state(physical))
                        if ad is not None:
                            contacts+=1
                            j=maybe_join(core,db,atlas_dist,c,limits,physical,list(prefix),best,sb,byid,sid)
                            if j and j.get("competitive"):
                                if best_join is None or j["source_length"]<best_join["source_length"]:
                                    best_join=j
                    emitted+=1

            flush_new()
            for i,step in enumerate(res["steps"]):
                current=tuple(res["states"][i]); target_state=tuple(res["states"][i+1])
                if step.get("kind")=="automorphism":
                    image=step["images"]
                    inverse_image=cd._compose(cd.elementary_inverse(image),inverse_image)
                    raw=tuple(apply_hom(word,image) for word in current)
                elif step.get("kind")=="substitution":
                    move=tuple(map(int,step["move"].split("_")))
                    target,source_sign,conjugator=cd.to_conjugator(current,move)
                    transported=apply_hom(conjugator,inverse_image)
                    trace.conjugated_multiply(target,source_sign,transported)
                    source=current[2-target]; oriented=source if source_sign==1 else inv(source)
                    rr=list(current)
                    rr[target-1]=free_reduce(current[target-1]+inv(conjugator)+oriented+conjugator)
                    raw=tuple(rr)
                elif step.get("kind")=="elementary":
                    raw=tuple(cd.replay_elementary(current,step["moves"]))
                    for move in step["moves"]:
                        op=move["op"]
                        if op=="conjugate": trace.conjugate_word(move["target"],apply_hom(move["by"],inverse_image))
                        elif op=="invert": trace.invert(move["target"])
                        elif op=="multiply": trace.multiply(move["target"],move["source"])
                        elif op=="swap": trace.swap()
                        else: raise ValueError(op)
                else:
                    raise ValueError(step)
                cd._emit_canonicalization(trace,raw,target_state,inverse_image)
                flush_new()
                if best_join is not None:
                    break

            rec.update({"physical_official_prefix":len(prefix),"atlas_contacts":contacts,
                        "strict_ac":False,"strict_stable":False})
            if best_join is not None:
                rec.update({k:v for k,v in best_join.items() if k not in ("path","stable_path")})
                rec["strict_ac"]=bool(best_join.get("ac_strict"))
                rec["strict_stable"]=bool(best_join.get("stable_strict"))
                if rec["strict_ac"]: strict[cid]=best_join["path"]
                if rec["strict_stable"]: strict[sid]=best_join["stable_path"]
        except Exception as exc:
            rec["error"]=f"{type(exc).__name__}: {exc}"
            rec["strict_ac"]=False; rec["strict_stable"]=False
        rows.append(rec); print("PHYSICAL_ATLAS_CASE",json.dumps(rec,sort_keys=True),flush=True)

    (out/"results.json").write_text(json.dumps(rows,indent=2,sort_keys=True)+"\n")
    (out/"pending_submission.txt").write_text("\n".join(
        f"{cid}: {json.dumps(m,separators=(',',':'))}" for cid,m in sorted(strict.items())
    )+("\n" if strict else ""))
    report={"targets":len(rows),"mixed_solved":sum(bool(r.get("solved")) for r in rows),
            "targets_with_contacts":sum((r.get("atlas_contacts") or 0)>0 for r in rows),
            "contacts":sum(r.get("atlas_contacts") or 0 for r in rows),
            "strict_ac":sum(bool(r.get("strict_ac")) for r in rows),
            "strict_stable":sum(bool(r.get("strict_stable")) for r in rows),
            "pending_rows":len(strict),"errors":sum("error" in r for r in rows),
            "seconds":round(time.time()-t0,3)}
    (out/"report.json").write_text(json.dumps(report,indent=2,sort_keys=True)+"\n")
    print("PHYSICAL_ATLAS_SUMMARY",json.dumps(report,sort_keys=True),flush=True)
    db.close()

if __name__=="__main__": main()
