#!/usr/bin/env python3
import argparse,json,sys,time
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"andrews_curtis"))
import solver_v2_gssub as S

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--acc-root",required=True)
    ap.add_argument("--acsolverx-root",required=True)
    ap.add_argument("--target",required=True)
    ap.add_argument("--out-dir",required=True)
    ap.add_argument("--beam",type=int,default=4)
    a=ap.parse_args()
    out=Path(a.out_dir);out.mkdir(parents=True,exist_ok=True)

    acc=Path(a.acc_root)
    sys.path.insert(0,str(acc/"competition/tools"))
    from verifier import core

    manifest=json.loads((acc/"competition/tools/verifier/data/manifest.json").read_text())
    limits=manifest["limits"]
    byid={c["challenge_id"]:c for c in manifest["challenges"]}
    c=byid[a.target]
    exact=tuple(tuple(w) for w in c["initial_relators"])

    ns=S.load_gssub(Path(a.acsolverx_root))
    solver=ns["ACRelatorSolver"](
        S.int_word_to_str(exact[0]),S.int_word_to_str(exact[1]),
        max_nodes=120000,max_len=min(80,max(S.total_len(exact)+36,48)),
        verbose=False,stop_early=False,
    )
    t=time.time()
    found=solver.solve()
    qpath,nodes=found[:2]
    if qpath is None:
        rep={"target":a.target,"quotient_found":False,"nodes":int(nodes),"seconds":time.time()-t}
        (out/"report.json").write_text(json.dumps(rep,indent=2,sort_keys=True)+"\n")
        print("COMPILER_AB",json.dumps(rep,sort_keys=True));return

    rev,_=S.build_reverse(core,7,250000)
    legacy,lmeta=S.compile_quotient_path(core,ns,exact,qpath,rev,limits["max_total_relator_length"])
    opt,ometa=S.compile_quotient_path_optimized(core,ns,exact,qpath,rev,limits["max_total_relator_length"],beam_width=a.beam)

    lv=core.verify(c,list(legacy),c["move_spec_version"],limits) if legacy is not None else {"ok":False}
    ov=core.verify(c,list(opt),c["move_spec_version"],limits) if opt is not None else {"ok":False}
    rep={
      "target":a.target,"quotient_found":True,"nodes":int(nodes),"quotient_steps":len(qpath)-1,
      "legacy_ok":bool(lv.get("ok")),"legacy_length":None if legacy is None else len(legacy),
      "optimized_ok":bool(ov.get("ok")),"optimized_length":None if opt is None else len(opt),
      "beam":a.beam,
      "moves_saved":None if legacy is None or opt is None else len(legacy)-len(opt),
      "ratio":None if legacy is None or opt is None else len(opt)/len(legacy),
      "optimized_meta":ometa,
      "seconds":round(time.time()-t,3),
    }
    (out/"report.json").write_text(json.dumps(rep,indent=2,sort_keys=True)+"\n")
    print("COMPILER_AB",json.dumps({k:v for k,v in rep.items() if k!="optimized_meta"},sort_keys=True))

if __name__=="__main__":main()
