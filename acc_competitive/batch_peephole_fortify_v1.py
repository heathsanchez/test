#!/usr/bin/env python3
import argparse,json,math,sys,urllib.request
from pathlib import Path

def parse_line(line):
    line=line.strip()
    if not line or ":" not in line:return None
    cid,raw=line.split(":",1)
    try:return cid.strip(),list(json.loads(raw.strip()))
    except Exception:return None

def public_snapshot(problem):
    url=f"https://server-9527.sair.foundation/api/acc/discoveries/snapshot?problem={problem}"
    req=urllib.request.Request(url,headers={"User-Agent":"Mozilla/5.0","Accept":"application/json"})
    with urllib.request.urlopen(req,timeout=60) as r:
        obj=json.loads(r.read().decode())
    d=obj.get("data",obj)
    return obj,{x["challengeId"]:x for x in d["items"]}

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--acc-root",required=True)
    ap.add_argument("--input",required=True)
    ap.add_argument("--out-dir",required=True)
    ap.add_argument("--thin-win-frac",type=float,default=0.25)
    ap.add_argument("--near-miss-frac",type=float,default=0.10)
    ap.add_argument("--max-window",type=int,default=5)
    ap.add_argument("--max-path",type=int,default=6000)
    a=ap.parse_args()

    root=Path(__file__).resolve().parents[1]
    sys.path.insert(0,str(root/"acc_competitive"))
    from peephole_superopt_v1 import optimize

    acc=Path(a.acc_root)
    sys.path.insert(0,str(acc/"competition/tools"))
    from verifier import core
    manifest=json.loads((acc/"competition/tools/verifier/data/manifest.json").read_text())
    byid={c["challenge_id"]:c for c in manifest["challenges"]}
    limits=manifest["limits"]

    out=Path(a.out_dir);out.mkdir(parents=True,exist_ok=True)
    raw={}
    for line in Path(a.input).read_text().splitlines():
        p=parse_line(line)
        if p and p[0].startswith("ac-"):
            cid,moves=p
            if cid not in raw or len(moves)<len(raw[cid]):raw[cid]=moves

    snap,live=public_snapshot("ac")
    (out/"public_snapshot_ac.json").write_text(json.dumps(snap,indent=2,sort_keys=True)+"\n")

    final={}
    reports=[]
    for cid,moves in sorted(raw.items()):
        c=byid[cid]
        v=core.verify(c,moves,c["move_spec_version"],limits)
        if not v.get("ok"):raise RuntimeError(f"input fails verifier {cid}")
        row=live.get(cid,{})
        best=row.get("currentBestLength")
        status=row.get("status")
        reason="skip"
        do_opt=False
        if isinstance(best,int) and best>0 and len(moves)<=a.max_path:
            frac=(best-len(moves))/best
            if 0 <= frac < a.thin_win_frac:
                do_opt=True;reason="thin_win"
            elif frac < 0 and (-frac) <= a.near_miss_frac:
                do_opt=True;reason="near_miss"
        elif status=="unsolved" and len(moves)<=a.max_path:
            do_opt=True;reason="unsolved"

        new=list(moves);changes=[]
        if do_opt:
            if isinstance(best,int):
                # For an existing thin win, push toward a 25% moat; for a
                # near miss, crossing best is the first objective.
                target=max(0,int(math.floor(best*(1-a.thin_win_frac)))) if len(moves)<best else best
            else:
                target=max(0,len(moves)-1)
            new,changes=optimize(core,tuple(tuple(w) for w in c["initial_relators"]),
                                 list(moves),limits["max_total_relator_length"],
                                 target,a.max_window,max_passes=4)
            nv=core.verify(c,new,c["move_spec_version"],limits)
            if not nv.get("ok"):raise RuntimeError(f"peephole output fails {cid}")

        final[cid]=new
        reports.append({
          "challenge_id":cid,"live_best":best,"live_status":status,
          "before":len(moves),"after":len(new),"saved":len(moves)-len(new),
          "optimized":do_opt,"reason":reason,"rewrite_count":len(changes),
          "strict_win_after":status=="unsolved" or (isinstance(best,int) and len(new)<best),
          "margin_after":None if not isinstance(best,int) else best-len(new),
          "margin_fraction_after":None if not isinstance(best,int) or best==0 else (best-len(new))/best,
        })

    text="\n".join(f"{cid}: {json.dumps(m,separators=(',',':'))}" for cid,m in sorted(final.items()))
    if text:text+="\n"
    (out/"fortified_ac.txt").write_text(text)
    (out/"peephole_report.json").write_text(json.dumps(reports,indent=2,sort_keys=True)+"\n")
    summary={
      "candidates":len(final),"optimized":sum(r["optimized"] for r in reports),
      "moves_saved":sum(r["saved"] for r in reports),
      "strict_wins_after":sum(r["strict_win_after"] for r in reports),
      "thin_or_near_processed":[r["challenge_id"] for r in reports if r["optimized"]],
    }
    (out/"report.json").write_text(json.dumps(summary,indent=2,sort_keys=True)+"\n")
    print("BATCH_PEEPHOLE",json.dumps(summary,sort_keys=True))

if __name__=="__main__":main()
