#!/usr/bin/env python3
import argparse,json,sys
from pathlib import Path

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--acc-root",required=True)
    p.add_argument("--out-dir",required=True)
    p.add_argument("--shards",type=int,default=8)
    p.add_argument("--max-targets",type=int,default=160)
    p.add_argument("--exclude-json",default=None)
    a=p.parse_args()
    root=Path(__file__).resolve().parent
    sys.path.insert(0,str(root))
    from solver_v2_gssub import snapshot_map,total_len

    acc=Path(a.acc_root)
    out=Path(a.out_dir); out.mkdir(parents=True,exist_ok=True)
    manifest=json.loads((acc/"competition/tools/verifier/data/manifest.json").read_text())
    by_id={c["challenge_id"]:c for c in manifest["challenges"] if c["challenge_id"].startswith("ac-")}
    _,live=snapshot_map("ac")

    excluded=set()
    if a.exclude_json and Path(a.exclude_json).exists():
        raw=json.loads(Path(a.exclude_json).read_text())
        for x in raw:
            excluded.add(x.get("challenge_id") if isinstance(x,dict) else str(x))

    rows=[]
    for cid,c in by_id.items():
        if cid in excluded: continue
        lr=live.get(cid,{})
        if lr.get("status")!="unsolved": continue
        state=tuple(tuple(w) for w in c["initial_relators"])
        lens=[len(w) for w in state]
        rows.append({
            "challenge_id":cid,
            "initial_total":total_len(state),
            "max_relator":max(lens),
            "min_relator":min(lens),
        })
    rows.sort(key=lambda r:(r["initial_total"],r["max_relator"],r["challenge_id"]))
    selected=rows[:a.max_targets]
    shards=[[] for _ in range(a.shards)]
    for i,r in enumerate(selected):
        shards[i%a.shards].append(r["challenge_id"])
    for i,items in enumerate(shards):
        (out/f"shard_{i}.json").write_text(json.dumps(items,indent=2)+"\n")
    report={
        "experiment":"acc-deep-live-frontier-v3",
        "live_unsolved_excluding_known_residual":len(rows),
        "selected":len(selected),
        "excluded":len(excluded),
        "shards":[len(x) for x in shards],
        "selected_rows":selected,
    }
    (out/"report.json").write_text(json.dumps(report,indent=2,sort_keys=True)+"\n")
    print("DEEP_FRONTIER",json.dumps({
        "live_unsolved_excluding_known_residual":len(rows),
        "selected":len(selected),
        "shards":[len(x) for x in shards],
        "min_initial_total":selected[0]["initial_total"] if selected else None,
        "max_initial_total":selected[-1]["initial_total"] if selected else None,
    },sort_keys=True))
if __name__=="__main__":
    main()
