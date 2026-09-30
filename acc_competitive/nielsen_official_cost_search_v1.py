#!/usr/bin/env python3
"""Official-cost-native Nielsen search for ACC singleton stealing.

Search state = (virtual canonical presentation, persistent inverse basis frame,
physical exact official state). Nielsen basis edges change only the virtual
presentation/frame; substitution edges must compile immediately into exact
pinned official moves. Thus route selection is charged by physical official
cost while it is made, not after a presentation-score solve is found.

This is deliberately bounded: finite frame-size/streak, top-K quotient
substitution proposals, exact official-cost pruning, and a node cap. Every
candidate exits through the verified Proof Atlas or an exact terminal bridge and
is replayed by the pinned official verifier.
"""
from __future__ import annotations
import argparse, heapq, itertools, json, sqlite3, sys, time
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
        if cid:out[str(cid)]=x
    return out

def to_pair(initial):
    return tuple("".join(LETTER[int(a)] for a in w) for w in initial)

def compile_op(m):
    op=m.get("op")
    if op=="invert":return [0 if int(m["target"])==1 else 1]
    if op=="multiply":
        t,s=int(m["target"]),int(m["source"])
        if (t,s)==(1,2):return [2]
        if (t,s)==(2,1):return [4]
        raise ValueError(("bad multiply",m))
    if op=="conjugate":return [CONJ[(int(m["target"]),str(m["by"]))]]
    if op=="swap":return list(SWAP)
    raise ValueError(("unknown op",m))

def frame_key(ns,qstate,inverse_image,apply_hom):
    return ns["canonical_pair_str"](
        apply_hom(str(qstate[0]),inverse_image),
        apply_hom(str(qstate[1]),inverse_image),
    )

def frame_tuple(inv):
    return (str(inv["x"]),str(inv["y"]))

def frame_dict(ft):
    return {"x":ft[0],"y":ft[1]}

def frame_size(ft):
    return len(ft[0])+len(ft[1])

def atlas_suffix(core,db,state,limit):
    s=state; out=[]; seen={s}
    for _ in range(limit):
        if s==TARGET:return tuple(out)
        row=db.execute("SELECT next_move FROM atlas WHERE state=?",(key_state(s),)).fetchone()
        if row is None or row[0] is None:return None
        m=int(row[0]);out.append(m);s=core.apply_move(s,m)
        if s in seen:return None
        seen.add(s)
    return None

def reconstruct(nodes,idx):
    official=[]; images=[]
    chain=[]
    while idx is not None:
        chain.append(idx);idx=nodes[idx]["parent"]
    for i in reversed(chain):
        e=nodes[i]["edge"]
        if e is None:continue
        if e[0]=="basis":images.append(e[1])
        else:official.extend(e[1])
    return tuple(official),images

def maybe_atlas(core,stable_core,db,atlas_dist,c,limits,byid,sid,state,path,ac_best,stable_best):
    ad=atlas_dist.get(key_state(state))
    if ad is None:return None
    bound=ac_best
    if isinstance(stable_best,int):bound=max(bound,stable_best-2)
    if len(path)+ad>=bound:return None
    suffix=atlas_suffix(core,db,state,bound-len(path)+8)
    if suffix is None:return None
    cand=tuple(path)+suffix
    v=core.verify(c,list(cand),c["move_spec_version"],limits)
    if not v.get("ok"):raise RuntimeError("official Atlas replay failed")
    out={"source_length":len(cand),"path":cand,"certificate_hash":v.get("certificate_hash"),
         "ac_strict":len(cand)<ac_best,"stable_strict":False,"atlas_distance":len(suffix)}
    if sid and isinstance(stable_best,int) and len(cand)+2<stable_best:
        sc=byid[sid];sp=list(cand)+[16,15]
        sv=stable_core.verify(sc,sp,sc["move_spec_version"],limits)
        if not sv.get("ok"):raise RuntimeError("Stable +2 replay failed")
        out["stable_strict"]=True;out["stable_path"]=tuple(sp)
        out["stable_certificate_hash"]=sv.get("certificate_hash")
    return out

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--acc-root",required=True)
    ap.add_argument("--acsolverx-root",required=True)
    ap.add_argument("--atlas",required=True)
    ap.add_argument("--snapshot-ac",required=True)
    ap.add_argument("--snapshot-stable",required=True)
    ap.add_argument("--target-id",required=True)
    ap.add_argument("--out-dir",required=True)
    ap.add_argument("--node-cap",type=int,default=25000)
    ap.add_argument("--frame-cap",type=int,default=9)
    ap.add_argument("--basis-streak",type=int,default=3)
    ap.add_argument("--topk-sub",type=int,default=8)
    ap.add_argument("--virtual-cap",type=int,default=90)
    ap.add_argument("--extra-total",type=int,default=120)
    ap.add_argument("--score-weight",type=float,default=0.5)
    ap.add_argument("--frame-weight",type=float,default=0.5)
    a=ap.parse_args()

    acc=Path(a.acc_root);axs=Path(a.acsolverx_root)
    sys.path.insert(0,str(acc/"competition/tools"))
    from verifier import core,stable_core
    sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"andrews_curtis"))
    import solver_v2_gssub as S
    sys.path.insert(0,str(axs))
    from research.ac_hashfree_cascade_20260914 import hfcascade
    from research.supermoves_20260908 import certificate_decoder as cd
    from experiments.equivalence_classes.lib.words import apply_hom

    ns=S.load_gssub(axs)
    scorer=hfcascade.SCORES["s20"]
    manifest=json.loads((acc/"competition/tools/verifier/data/manifest.json").read_text())
    limits=manifest["limits"];byid={c["challenge_id"]:c for c in manifest["challenges"]}
    c=byid[a.target_id]
    live_ac=snapshot_map(a.snapshot_ac);live_stable=snapshot_map(a.snapshot_stable)
    ac_best=live_ac[a.target_id].get("currentBestLength")
    if not isinstance(ac_best,int):raise SystemExit("target lacks live AC record")
    sid="sac-"+a.target_id[3:];stable_best=live_stable.get(sid,{}).get("currentBestLength")
    bound=ac_best
    if isinstance(stable_best,int):bound=max(bound,stable_best-2)

    exact=tuple(tuple(w) for w in c["initial_relators"])
    q0=hfcascade.canon_pair(*to_pair(c["initial_relators"]))
    identity=frame_tuple(cd.IDENTITY)
    if S.gssub_key(ns,exact)!=frame_key(ns,q0,cd.IDENTITY,apply_hom):
        raise RuntimeError("root invariant mismatch")

    total_cap=min(limits["max_total_relator_length"],max(100,sum(map(len,exact))+a.extra_total))
    db=sqlite3.connect(a.atlas)
    atlas_dist={bytes(k):int(d) for k,d in db.execute("SELECT state,distance FROM atlas")}
    reverse_paths,_=S.build_reverse(core,7,250000)

    out=Path(a.out_dir);out.mkdir(parents=True,exist_ok=True)
    t0=time.time();counter=itertools.count()
    nodes=[]
    def add_node(q,ft,physical,g,parent,edge,streak,depth):
        idx=len(nodes)
        nodes.append({"q":q,"ft":ft,"physical":physical,"g":g,"parent":parent,
                      "edge":edge,"streak":streak,"depth":depth})
        pri=g+a.score_weight*float(scorer(q))+a.frame_weight*max(0,frame_size(ft)-2)
        heapq.heappush(heap,(pri,g,next(counter),idx))
        return idx

    heap=[];seen={}
    root=add_node(q0,identity,exact,0,None,None,0,0)
    seen[(q0,identity,exact,0)]=0
    popped=0;generated=1;basis_generated=0;sub_generated=0;atlas_contacts=0
    best=None;best_terminal=None;min_terminal_lb=None

    while heap and popped<a.node_cap:
        _,g,_,idx=heapq.heappop(heap);n=nodes[idx]
        sk=(n["q"],n["ft"],n["physical"],n["streak"])
        if seen.get(sk)!=g:continue
        popped+=1

        # Exact Atlas exit from the physical official state.
        ad=atlas_dist.get(key_state(n["physical"]))
        if ad is not None:
            atlas_contacts+=1
            path,_=reconstruct(nodes,idx)
            j=maybe_atlas(core,stable_core,db,atlas_dist,c,limits,byid,sid,n["physical"],path,
                          ac_best,stable_best)
            if j is not None:
                best=j;break

        # If the virtual presentation is terminal, discharge the accumulated
        # basis sequence only once, then bridge exactly.
        if hfcascade.is_terminal(n["q"]):
            path,images=reconstruct(nodes,idx)
            tr=cd._ElementaryTrace(tuple(S.int_word_to_str(w) for w in n["physical"]))
            for image in reversed(images):cd._emit_tuple_image(tr,image)
            tail=[]
            for m in tr.moves:tail.extend(compile_op(m))
            lb=len(path)+len(tail)
            min_terminal_lb=lb if min_terminal_lb is None else min(min_terminal_lb,lb)
            if lb<bound:
                cur=n["physical"]
                for m in tail:cur=core.apply_move(cur,m)
                p2=path+tuple(tail)
                j=maybe_atlas(core,stable_core,db,atlas_dist,c,limits,byid,sid,cur,p2,
                              ac_best,stable_best)
                if j is None:
                    suffix=S.exact_terminal_suffix(core,cur,reverse_paths)
                    if suffix is not None and len(p2)+len(suffix)<bound:
                        cand=p2+tuple(suffix)
                        v=core.verify(c,list(cand),c["move_spec_version"],limits)
                        if v.get("ok"):
                            j={"source_length":len(cand),"path":cand,
                               "certificate_hash":v.get("certificate_hash"),
                               "ac_strict":len(cand)<ac_best,"stable_strict":False,
                               "atlas_distance":None}
                            if isinstance(stable_best,int) and len(cand)+2<stable_best:
                                sc=byid[sid];sp=list(cand)+[16,15]
                                sv=stable_core.verify(sc,sp,sc["move_spec_version"],limits)
                                if sv.get("ok"):
                                    j["stable_strict"]=True;j["stable_path"]=tuple(sp)
                                    j["stable_certificate_hash"]=sv.get("certificate_hash")
                if j is not None:
                    best=j;best_terminal=True;break

        # Zero-immediate-cost Nielsen basis edges, with bounded persistent frame.
        if n["streak"]<a.basis_streak:
            inv=frame_dict(n["ft"])
            for qchild,img in hfcascade.nielsen_children(n["q"]):
                inv2=cd._compose(cd.elementary_inverse(img),inv);ft2=frame_tuple(inv2)
                if frame_size(ft2)>a.frame_cap:continue
                desired=frame_key(ns,qchild,inv2,apply_hom)
                if S.gssub_key(ns,n["physical"])!=desired:
                    raise RuntimeError("basis-edge invariant mismatch")
                nk=(qchild,ft2,n["physical"],n["streak"]+1)
                if g>=seen.get(nk,10**18):continue
                seen[nk]=g
                add_node(qchild,ft2,n["physical"],g,idx,("basis",img),n["streak"]+1,n["depth"]+1)
                generated+=1;basis_generated+=1

        # Official-costed substitution proposals. Limit virtual branching by the
        # public structural score, but retain all exact physical representatives
        # of each admitted quotient child.
        raw=hfcascade.children(n["q"])
        ded={}
        for qchild,mv in raw:
            if sum(map(len,qchild))>a.virtual_cap:continue
            sc=float(scorer(qchild))
            old=ded.get(qchild)
            if old is None or sc<old[0]:ded[qchild]=(sc,mv)
        qchildren=sorted(((sc,q,mv) for q,(sc,mv) in ded.items()),key=lambda x:(x[0],x[1]))[:a.topk_sub]
        inv=frame_dict(n["ft"])
        for _,qchild,mv in qchildren:
            desired=frame_key(ns,qchild,inv,apply_hom)
            cands=S.compiled_superneighbor_candidates(core,ns,n["physical"],desired,total_cap)
            for physical2,edge in cands:
                g2=g+len(edge)
                if g2>=bound:continue
                # one future official move is necessary unless already at a known exit
                nk=(qchild,n["ft"],physical2,0)
                if g2>=seen.get(nk,10**18):continue
                seen[nk]=g2
                add_node(qchild,n["ft"],physical2,g2,idx,("official",tuple(edge)),0,n["depth"]+1)
                generated+=1;sub_generated+=1

    strict={}
    if best is not None:
        if best.get("ac_strict"):strict[a.target_id]=list(best["path"])
        if best.get("stable_strict"):strict[sid]=list(best["stable_path"])
    report={
        "challenge_id":a.target_id,"live_best":ac_best,"stable_live_best":stable_best,
        "strict_bound":bound,"found":best is not None,
        "source_length":None if best is None else best.get("source_length"),
        "strict_ac":False if best is None else bool(best.get("ac_strict")),
        "strict_stable":False if best is None else bool(best.get("stable_strict")),
        "certificate_hash":None if best is None else best.get("certificate_hash"),
        "atlas_distance":None if best is None else best.get("atlas_distance"),
        "node_cap":a.node_cap,"popped":popped,"generated":generated,
        "basis_generated":basis_generated,"sub_generated":sub_generated,
        "open_remaining":len(heap),"closed_states":len(seen),"atlas_contacts":atlas_contacts,
        "min_terminal_lower_bound":min_terminal_lb,
        "frame_cap":a.frame_cap,"basis_streak":a.basis_streak,"topk_sub":a.topk_sub,
        "score_weight":a.score_weight,"frame_weight":a.frame_weight,
        "seconds":round(time.time()-t0,3),
    }
    (out/"report.json").write_text(json.dumps(report,indent=2,sort_keys=True)+"\n")
    (out/"pending_submission.txt").write_text("\n".join(
        f"{cid}: {json.dumps(m,separators=(',',':'))}" for cid,m in sorted(strict.items())
    )+("\n" if strict else ""))
    print("OFFICIAL_COST_CASE",json.dumps(report,sort_keys=True),flush=True)
    db.close()

if __name__=="__main__":main()
