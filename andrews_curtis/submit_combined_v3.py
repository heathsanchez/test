#!/usr/bin/env python3
import argparse, json, re, sys
from pathlib import Path

def parse_line(line):
    m=re.match(r"^([A-Za-z0-9_-]+)\s*:\s*(\[.*\])\s*$",line.strip())
    if not m: return None
    moves=json.loads(m.group(2))
    return m.group(1),moves

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--glob",required=True)
    p.add_argument("--out-dir",required=True)
    p.add_argument("--description",default="MathGraph ACC V3 full MS residual sweep")
    a=p.parse_args()

    root=Path(__file__).resolve().parent
    sys.path.insert(0,str(root))
    from solver_v2_gssub import snapshot_map, current_competitive, submit_batch

    out=Path(a.out_dir); out.mkdir(parents=True,exist_ok=True)
    files=sorted(Path(".").glob(a.glob))
    candidates={}
    source_files=[]
    for fp in files:
        source_files.append(str(fp))
        for line in fp.read_text().splitlines():
            if not line.strip() or line.lstrip().startswith("#"): continue
            parsed=parse_line(line)
            if not parsed: continue
            cid,moves=parsed
            prev=candidates.get(cid)
            if prev is None or len(moves)<len(prev):
                candidates[cid]=moves

    ac_snap,ac=snapshot_map("ac")
    sac_snap,sac=snapshot_map("stable_ac")
    (out/"snapshot_ac_pre_submit.json").write_text(json.dumps(ac_snap,indent=2,sort_keys=True)+"\n")
    (out/"snapshot_stable_ac_pre_submit.json").write_text(json.dumps(sac_snap,indent=2,sort_keys=True)+"\n")

    selected=[]
    selection=[]
    for cid,moves in sorted(candidates.items(), key=lambda kv:(len(kv[1]),kv[0])):
        live=ac if cid.startswith("ac-") else sac
        row=live.get(cid)
        if row is None:
            selection.append({"challenge_id":cid,"length":len(moves),"selected":False,"reason":"missing_live_row"})
            continue
        ok,reason=current_competitive(row,len(moves))
        selection.append({
            "challenge_id":cid,
            "length":len(moves),
            "live_status":row.get("status"),
            "live_best":row.get("currentBestLength"),
            "selected":ok,
            "reason":reason,
        })
        if ok:
            selected.append((cid,moves))

    text="\n".join(f"{cid}: {json.dumps(m,separators=(',',':'))}" for cid,m in selected)
    if text: text+="\n"
    (out/"selection.json").write_text(json.dumps(selection,indent=2,sort_keys=True)+"\n")
    (out/"submission_v3.txt").write_text(text)

    report={
        "source_files":source_files,
        "candidate_rows":len(candidates),
        "selected_rows":len(selected),
        "selected_ac":sum(cid.startswith("ac-") for cid,_ in selected),
        "selected_stable":sum(cid.startswith("sac-") for cid,_ in selected),
        "submission_id":None,
    }

    if selected:
        if len(selected)>500:
            raise RuntimeError(f"refusing {len(selected)} rows > 500")
        sid,response,polls,final=submit_batch(text)
        report["submission_id"]=sid
        (out/"submission_response.json").write_text(json.dumps(response,indent=2,sort_keys=True)+"\n")
        (out/"submission_polls.json").write_text(json.dumps(polls,indent=2,sort_keys=True)+"\n")
        (out/"submission_final.json").write_text(json.dumps(final,indent=2,sort_keys=True)+"\n")
        data=final.get("data",final)
        status=str(data.get("status","")).lower() if isinstance(data,dict) else ""
        results=data.get("results",[]) if isinstance(data,dict) else []
        report["terminal_status"]=status
        report["result_rows"]=len(results) if isinstance(results,list) else None
        report["failed_rows"]=sum(1 for x in results if x.get("ok") is False) if isinstance(results,list) else None
        if status not in ("complete","completed"):
            raise RuntimeError(f"submission terminal status {status}")
        if isinstance(results,list) and any(x.get("ok") is False for x in results):
            raise RuntimeError("one or more platform verifications failed")

        ac_after,_=snapshot_map("ac")
        sac_after,_=snapshot_map("stable_ac")
        (out/"snapshot_ac_after.json").write_text(json.dumps(ac_after,indent=2,sort_keys=True)+"\n")
        (out/"snapshot_stable_ac_after.json").write_text(json.dumps(sac_after,indent=2,sort_keys=True)+"\n")

    (out/"report.json").write_text(json.dumps(report,indent=2,sort_keys=True)+"\n")
    print("V3_AGGREGATE",json.dumps(report,sort_keys=True))

if __name__=="__main__":
    main()
