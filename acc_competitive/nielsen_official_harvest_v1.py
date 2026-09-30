#!/usr/bin/env python3
"""ACC #1 Nielsen harvest: public rank-two Nielsen search -> exact official moves.

Search mechanism is frozen to Avi161/ACSolverX@5ae1bd8... hfcascade fast engine
with four Nielsen basis maps and signed-permutation canonicalization. Every solved
mixed certificate is independently replayed by the public verifier, decoded to
generator-level elementary AC operations by the public certificate decoder, then
compiled to SAIR's pinned ac-r2-v1 move ids and replayed by the official verifier.

Only strict live improvements are emitted.
"""
from __future__ import annotations
import argparse, json, sys, time
from pathlib import Path

LETTER={1:"x",-1:"X",2:"y",-2:"Y"}
# Public decoder conjugate(target, letter) means letter^-1 r letter.
# Official conjugation move uses g r g^-1, hence the inverse-letter mapping.
CONJ={
    (1,"x"):7,(1,"X"):6,(1,"y"):9,(1,"Y"):8,
    (2,"x"):11,(2,"X"):10,(2,"y"):13,(2,"Y"):12,
}
# Universal tuple swap using only frozen ordinary AC moves:
# (a,b)->(a^-1,b^-1)->((ba)^-1,b^-1)->(ba,b^-1)->(ba,a)->(b,a)
SWAP=(0,1,2,0,4,3)

def snapshot_map(path):
    o=json.loads(Path(path).read_text()); d=o.get("data",o); out={}
    for x in d["items"]:
        cid=x.get("problemId") or x.get("challengeId")
        if cid: out[str(cid)]=x
    return out

def to_pair(initial):
    return tuple("".join(LETTER[int(a)] for a in w) for w in initial)

def compile_elementary(moves):
    out=[]
    for m in moves:
        op=m.get("op")
        if op=="invert":
            t=int(m["target"]); out.append(0 if t==1 else 1)
        elif op=="multiply":
            t,s=int(m["target"]),int(m["source"])
            if (t,s)==(1,2): out.append(2)
            elif (t,s)==(2,1): out.append(4)
            else: raise ValueError(("bad multiply",m))
        elif op=="conjugate":
            out.append(CONJ[(int(m["target"]),str(m["by"]))])
        elif op=="swap":
            out.extend(SWAP)
        else:
            raise ValueError(("unknown elementary op",m))
    return out

def swap_self_test(core):
    samples=[
        (((1,2,-1),(2,1)),((2,1),(1,2,-1))),
        (((1,1,2),(-2,1)),((-2,1),(1,1,2))),
        (((1,), (2,)), ((2,), (1,))),
    ]
    for st,want in samples:
        cur=st
        for m in SWAP: cur=core.apply_move(cur,m)
        if cur!=want: raise AssertionError(("swap adapter failed",st,cur,want))

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--acc-root",required=True)
    ap.add_argument("--acsolverx-root",required=True)
    ap.add_argument("--snapshot-ac",required=True)
    ap.add_argument("--snapshot-stable",required=True)
    ap.add_argument("--target-ids-file",required=True)
    ap.add_argument("--out-dir",required=True)
    ap.add_argument("--budget",type=int,default=1000)
    a=ap.parse_args()

    acc=Path(a.acc_root); axs=Path(a.acsolverx_root)
    sys.path.insert(0,str(acc/"competition/tools"))
    from verifier import core,stable_core
    swap_self_test(core)

    sys.path.insert(0,str(axs))
    from research.ac_hashfree_cascade_20260914 import hfcascade, verify as public_verify
    from research.supermoves_20260908 import certificate_decoder

    manifest=json.loads((acc/"competition/tools/verifier/data/manifest.json").read_text())
    limits=manifest["limits"]; byid={c["challenge_id"]:c for c in manifest["challenges"]}
    live_ac=snapshot_map(a.snapshot_ac); live_stable=snapshot_map(a.snapshot_stable)
    ids=json.loads(Path(a.target_ids_file).read_text())
    ids=[x["challenge_id"] if isinstance(x,dict) else str(x) for x in ids]

    out=Path(a.out_dir); out.mkdir(parents=True,exist_ok=True)
    rows=[]; strict={}
    t0=time.time()
    for idx,cid in enumerate(ids):
        c=byid.get(cid); lr=live_ac.get(cid,{})
        best=lr.get("currentBestLength")
        if c is None or not isinstance(best,int): continue
        pair=to_pair(c["initial_relators"])
        rec={"challenge_id":cid,"live_best":best,"live_kTeams":lr.get("kTeams")}
        try:
            res=hfcascade.solve(
                pair,budget=a.budget,score="s20",gates=True,pair_descent=True,
                engine="fast",closed_set="sorted",nielsen=True,perms=True,
                gate_when="pop"
            )
            rec.update({"solved":bool(res["solved"]),"units":res["units"],
                        "stage":res.get("stage"),"mixed_steps":res.get("path_length")})
            if res["solved"]:
                public_verify.replay(pair,res["steps"],res["states"])
                elem=certificate_decoder.decode_elementary(pair,res["states"],res["steps"])
                official=compile_elementary(elem)
                verdict=core.verify(c,official,c["move_spec_version"],limits)
                rec.update({
                    "elementary_ops":len(elem),"official_length":len(official),
                    "official_ok":bool(verdict.get("ok")),
                    "certificate_hash":verdict.get("certificate_hash"),
                    "peak":verdict.get("peak_total_relator_length"),
                    "work":verdict.get("work"),
                    "strict_ac":bool(verdict.get("ok")) and len(official)<best,
                })
                if verdict.get("ok") and len(official)<best:
                    strict[cid]=official

                sid="sac-"+cid[3:]
                sb=live_stable.get(sid,{}).get("currentBestLength")
                rec["stable_live_best"]=sb
                rec["strict_stable"]=False
                if isinstance(sb,int):
                    sc=byid.get(sid)
                    spath=official+[16,15]
                    sv=stable_core.verify(sc,spath,sc["move_spec_version"],limits)
                    rec.update({"stable_length":len(spath),"stable_ok":bool(sv.get("ok")),
                                "stable_certificate_hash":sv.get("certificate_hash")})
                    if sv.get("ok") and len(spath)<sb:
                        rec["strict_stable"]=True; strict[sid]=spath
            else:
                rec.update({"strict_ac":False,"strict_stable":False})
        except Exception as exc:
            rec.update({"error":f"{type(exc).__name__}: {exc}","strict_ac":False,"strict_stable":False})
        rows.append(rec)
        print("NIELSEN_CASE",json.dumps(rec,sort_keys=True),flush=True)

    (out/"results.json").write_text(json.dumps(rows,indent=2,sort_keys=True)+"\n")
    (out/"pending_submission.txt").write_text(
        "\n".join(f"{cid}: {json.dumps(m,separators=(',',':'))}" for cid,m in sorted(strict.items()))
        + ("\n" if strict else "")
    )
    report={
        "targets":len(rows),"budget":a.budget,
        "mixed_solved":sum(bool(r.get("solved")) for r in rows),
        "official_verified":sum(bool(r.get("official_ok")) for r in rows),
        "strict_ac":sum(bool(r.get("strict_ac")) for r in rows),
        "strict_stable":sum(bool(r.get("strict_stable")) for r in rows),
        "pending_rows":len(strict),
        "errors":sum("error" in r for r in rows),
        "seconds":round(time.time()-t0,3),
        "public_solver_commit":"5ae1bd8eda6d80dfbea51680636f825da19fb802",
        "official_commit":"99a65377c5c4f412cd9af7b8d31c41464a855736",
    }
    (out/"report.json").write_text(json.dumps(report,indent=2,sort_keys=True)+"\n")
    print("NIELSEN_SUMMARY",json.dumps(report,sort_keys=True),flush=True)

if __name__=="__main__":
    main()
