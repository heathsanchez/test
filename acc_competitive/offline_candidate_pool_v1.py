#!/usr/bin/env python3
import argparse,json,re,sys
from pathlib import Path

def parse_line(line):
    m=re.match(r"^([A-Za-z0-9_-]+)\s*:\s*(\[.*\])\s*$",line.strip())
    if not m:return None
    return m.group(1),list(json.loads(m.group(2)))

def data_obj(obj):
    return obj.get("data",obj) if isinstance(obj,dict) else obj

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--acc-root",required=True)
    ap.add_argument("--glob",required=True)
    ap.add_argument("--snapshot-ac",required=True)
    ap.add_argument("--snapshot-stable",required=True)
    ap.add_argument("--out-dir",required=True)
    a=ap.parse_args()
    out=Path(a.out_dir);out.mkdir(parents=True,exist_ok=True)

    acc=Path(a.acc_root)
    sys.path.insert(0,str(acc/"competition/tools"))
    from verifier import core,stable_core
    manifest=json.loads((acc/"competition/tools/verifier/data/manifest.json").read_text())
    limits=manifest["limits"]
    byid={c["challenge_id"]:c for c in manifest["challenges"]}

    acs=json.loads(Path(a.snapshot_ac).read_text()); sas=json.loads(Path(a.snapshot_stable).read_text())
    ac={x["challengeId"]:x for x in data_obj(acs)["items"]}
    sac={x["challengeId"]:x for x in data_obj(sas)["items"]}

    best={}
    sources={}
    for fp in sorted(Path(".").glob(a.glob)):
        for line in fp.read_text().splitlines():
            p=parse_line(line)
            if not p:continue
            cid,moves=p
            old=best.get(cid)
            if old is None or len(moves)<len(old):
                best[cid]=moves;sources[cid]=str(fp)

    verified={}
    failures=[]
    for cid,moves in sorted(best.items()):
        c=byid.get(cid)
        if not c:continue
        verifier=stable_core if cid.startswith("sac-") else core
        v=verifier.verify(c,moves,c["move_spec_version"],limits)
        if not v.get("ok"):
            failures.append({"challenge_id":cid,"source":sources[cid],"verdict":v})
            continue
        verified[cid]=moves

    competitive=[]
    comparisons=[]
    for cid,moves in sorted(verified.items()):
        row=(sac if cid.startswith("sac-") else ac).get(cid,{})
        live=row.get("currentBestLength")
        ok=(row.get("status")=="unsolved") or (isinstance(live,int) and len(moves)<live)
        comparisons.append({"challenge_id":cid,"length":len(moves),"frozen_best":live,
                            "frozen_kTeams":row.get("kTeams"),"strictly_better_frozen":ok,
                            "source":sources[cid]})
        if ok:competitive.append((cid,moves))

    text="\n".join(f"{cid}: {json.dumps(m,separators=(',',':'))}" for cid,m in competitive)
    if text:text+="\n"
    (out/"pending_submission.txt").write_text(text)
    (out/"comparisons.json").write_text(json.dumps(comparisons,indent=2,sort_keys=True)+"\n")
    (out/"verification_failures.json").write_text(json.dumps(failures,indent=2,sort_keys=True)+"\n")
    rep={"candidate_rows":len(best),"verified_rows":len(verified),
         "strictly_better_than_frozen":len(competitive),
         "unique_challenges":len({cid.replace("sac-","ac-") for cid,_ in competitive}),
         "verification_failures":len(failures)}
    (out/"report.json").write_text(json.dumps(rep,indent=2,sort_keys=True)+"\n")
    print("OFFLINE_POOL",json.dumps(rep,sort_keys=True))

if __name__=="__main__":main()
