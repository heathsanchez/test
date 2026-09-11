#!/usr/bin/env python3
import argparse, ast, json, sys
from pathlib import Path

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--acc-root",required=True)
    p.add_argument("--acsolverx-root",required=True)
    p.add_argument("--out-dir",required=True)
    p.add_argument("--shards",type=int,default=4)
    p.add_argument("--max-targets",type=int,default=120)
    p.add_argument("--exclude-json",default=None)
    a=p.parse_args()

    root=Path(__file__).resolve().parent
    sys.path.insert(0,str(root))
    from solver_v2_checkpoint import canon_pair, parse_padded_presentation
    from solver_v2_gssub import snapshot_map, total_len

    acc=Path(a.acc_root)
    acx=Path(a.acsolverx_root)
    out=Path(a.out_dir); out.mkdir(parents=True,exist_ok=True)
    manifest=json.loads((acc/"competition/tools/verifier/data/manifest.json").read_text())

    by_key={}
    by_id={}
    for c in manifest["challenges"]:
        cid=c["challenge_id"]
        if not cid.startswith("ac-"): continue
        st=tuple(tuple(w) for w in c["initial_relators"])
        k=canon_pair(st)
        if k in by_key and by_key[k]!=cid:
            raise RuntimeError(f"quotient collision {cid} {by_key[k]}")
        by_key[k]=cid
        by_id[cid]=c

    _,live=snapshot_map("ac")
    excluded=set()
    if a.exclude_json and Path(a.exclude_json).exists():
        raw=json.loads(Path(a.exclude_json).read_text())
        for x in raw:
            excluded.add(x.get("challenge_id") if isinstance(x,dict) else str(x))

    rows=[]
    dataset=acx/"data/AC19_extended.txt"
    with dataset.open() as f:
        for idx,line in enumerate(f):
            s=line.strip()
            if not s: continue
            state=parse_padded_presentation(ast.literal_eval(s))
            cid=by_key.get(canon_pair(state))
            if not cid or cid in excluded: continue
            lr=live.get(cid,{})
            if lr.get("status")!="unsolved": continue
            rows.append({
                "dataset_index":idx,
                "challenge_id":cid,
                "initial_total":total_len(state),
                "live_status":"unsolved",
            })

    # Deduplicate by scored challenge, keeping earliest dataset representative.
    uniq={}
    for r in rows:
        uniq.setdefault(r["challenge_id"],r)
    rows=list(uniq.values())
    rows.sort(key=lambda r:(r["initial_total"],r["dataset_index"],r["challenge_id"]))
    selected=rows[:a.max_targets]

    shards=[[] for _ in range(a.shards)]
    for i,r in enumerate(selected):
        shards[i%a.shards].append(r["challenge_id"])
    for i,items in enumerate(shards):
        (out/f"shard_{i}.json").write_text(json.dumps(items,indent=2)+"\n")

    report={
        "experiment":"acc-ms-full-family-residual-v3",
        "dataset_rows_scanned":sum(1 for _ in dataset.open()),
        "mapped_live_unsolved_excluding_checkpoint_residual":len(rows),
        "selected":len(selected),
        "excluded_checkpoint_residual":len(excluded),
        "shards":[len(x) for x in shards],
        "selected_rows":selected,
    }
    (out/"report.json").write_text(json.dumps(report,indent=2,sort_keys=True)+"\n")
    print("MS_FULL_RESIDUAL",json.dumps({
        "mapped_live_unsolved_excluding_checkpoint_residual":len(rows),
        "selected":len(selected),
        "shards":[len(x) for x in shards],
    },sort_keys=True))

if __name__=="__main__":
    main()
