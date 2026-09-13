#!/usr/bin/env python3
import argparse,ast,json,re,sys,time
from datetime import datetime, timezone
from urllib.parse import quote
from urllib import request
from pathlib import Path

INV=(0,1,3,2,5,4,7,6,9,8,11,10,13,12)

def parse_line(line):
    m=re.match(r"^([A-Za-z0-9_-]+)\s*:\s*(\[.*\])\s*$",line.strip())
    if not m:return None
    return m.group(1),list(json.loads(m.group(2)))

def inverse_reduce(xs):
    st=[]
    for a in xs:
        if st and st[-1] < 14 and a < 14 and INV[st[-1]]==a:
            st.pop()
        else:
            st.append(a)
    return st

def loop_erase(core,initial,moves):
    state=tuple(tuple(w) for w in initial)
    states=[state]
    out=[]
    pos={state:0}
    for m in moves:
        nxt=core.apply_move(states[-1],m)
        if nxt in pos:
            j=pos[nxt]
            for st in states[j+1:]:
                pos.pop(st,None)
            states=states[:j+1]
            out=out[:j]
        else:
            out.append(m)
            states.append(nxt)
            pos[nxt]=len(out)
    return out

def compress(core,initial,moves):
    cur=list(moves)
    while True:
        nxt=inverse_reduce(cur)
        nxt=loop_erase(core,initial,nxt)
        nxt=inverse_reduce(nxt)
        if len(nxt)==len(cur):
            return nxt
        cur=nxt

def strict_record_steal(row,candidate_len):
    if row.get("status") == "unsolved":
        return True, "currently_unsolved"
    best=row.get("currentBestLength")
    if isinstance(best,int) and candidate_len < best:
        return True, "strict_improvement"
    if isinstance(best,int) and candidate_len == best:
        return False, "tie_not_a_strict_steal"
    return False, "longer_than_live_best"


PUBLIC_BASE="https://server-9527.sair.foundation"

def public_snapshot_map(problem):
    url=f"{PUBLIC_BASE}/api/acc/discoveries/snapshot?problem={problem}"
    req=request.Request(url,headers={"User-Agent":"Mozilla/5.0","Accept":"application/json"})
    with request.urlopen(req,timeout=60) as r:
        obj=json.loads(r.read().decode("utf-8"))
    d=obj.get("data",obj)
    return obj,{x["challengeId"]:x for x in d["items"]}

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--acc-root",required=True)
    p.add_argument("--glob",required=True)
    p.add_argument("--out-dir",required=True)
    p.add_argument("--cycle",type=int,default=0)
    a=p.parse_args()

    root=Path(__file__).resolve().parent
    sys.path.insert(0,str(root))
    from solver_v2_gssub import submit_batch

    acc=Path(a.acc_root)
    sys.path.insert(0,str(acc/"competition/tools"))
    from verifier import core,stable_core

    manifest=json.loads((acc/"competition/tools/verifier/data/manifest.json").read_text())
    limits=manifest["limits"]
    by_id={c["challenge_id"]:c for c in manifest["challenges"]}

    out=Path(a.out_dir);out.mkdir(parents=True,exist_ok=True)

    files=sorted(Path(".").glob(a.glob))
    raw_candidates={}
    for fp in files:
        for line in fp.read_text().splitlines():
            parsed=parse_line(line)
            if not parsed:continue
            cid,moves=parsed
            if not cid.startswith("ac-"):continue
            prev=raw_candidates.get(cid)
            if prev is None or len(moves)<len(prev):
                raw_candidates[cid]=moves

    verified={}
    compression=[]
    for cid,moves in sorted(raw_candidates.items()):
        c=by_id[cid]
        short=compress(core,c["initial_relators"],moves)
        verdict=core.verify(c,short,c["move_spec_version"],limits)
        sid="sac-"+cid[3:]
        sc=by_id[sid]
        stable=short+[16,15]
        sv=stable_core.verify(sc,stable,sc["move_spec_version"],limits)
        rec={
            "challenge_id":cid,"raw_length":len(moves),"compressed_length":len(short),
            "saved":len(moves)-len(short),"ac_ok":bool(verdict.get("ok")),
            "stable_id":sid,"stable_length":len(stable),"stable_ok":bool(sv.get("ok"))
        }
        compression.append(rec)
        if not verdict.get("ok") or not sv.get("ok"):
            raise RuntimeError(f"compressed candidate failed official verifier: {rec}")
        verified[cid]=(short,sid,stable)

    # Publication economics: routine scheduler is capped below 40 batches/day,
    # so do not spend authenticated API calls reading history or static policy.
    # All live frontier reads use SAIR's public frontend backend.
    daily_limit=40
    used_today=None
    quota_remaining=None
    quota_blocked=False
    local_spec={"source":"pinned-current-spec","limits":{"dailySubmissions":daily_limit}}
    (out/"submission_spec.json").write_text(json.dumps(local_spec,indent=2,sort_keys=True)+"\n")

    acsnap,ac=public_snapshot_map("ac")
    ssnap,sac=public_snapshot_map("stable_ac")
    (out/"snapshot_ac_pre.json").write_text(json.dumps(acsnap,indent=2,sort_keys=True)+"\n")
    (out/"snapshot_stable_pre.json").write_text(json.dumps(ssnap,indent=2,sort_keys=True)+"\n")

    selected=[]
    selection=[]
    for cid,(moves,sid,stable) in sorted(verified.items()):
        for qid,path,live in ((cid,moves,ac),(sid,stable,sac)):
            row=live.get(qid)
            if row is None:
                selection.append({"challenge_id":qid,"length":len(path),"selected":False,"reason":"missing_live_row"})
                continue
            ok,reason=strict_record_steal(row,len(path))
            selection.append({
                "challenge_id":qid,"length":len(path),"live_status":row.get("status"),
                "live_best":row.get("currentBestLength"),"selected":ok,"reason":reason
            })
            if ok:selected.append((qid,path))

    dropped_for_batch_limit=0
    if len(selected)>500:
        dropped_for_batch_limit=len(selected)-500
        selected=selected[:500]
    text="\n".join(f"{cid}: {json.dumps(m,separators=(',',':'))}" for cid,m in selected)
    if text:text+="\n"
    (out/"submission.txt").write_text(text)
    (out/"selection.json").write_text(json.dumps(selection,indent=2,sort_keys=True)+"\n")
    (out/"compression.json").write_text(json.dumps(compression,indent=2,sort_keys=True)+"\n")

    submission_id=None
    terminal=None
    failures=None
    if selected and not quota_blocked:
        submission_id,response,polls,final=submit_batch(text)
        (out/"submission_response.json").write_text(json.dumps(response,indent=2,sort_keys=True)+"\n")
        (out/"submission_polls.json").write_text(json.dumps(polls,indent=2,sort_keys=True)+"\n")
        (out/"submission_final.json").write_text(json.dumps(final,indent=2,sort_keys=True)+"\n")
        d=final.get("data",final)
        terminal=str(d.get("status","")).lower() if isinstance(d,dict) else ""
        results=d.get("results",[]) if isinstance(d,dict) else []
        failures=sum(1 for x in results if x.get("ok") is False) if isinstance(results,list) else None
        if terminal not in ("complete","completed"):
            raise RuntimeError(f"submission terminal state {terminal}")
        if failures:
            raise RuntimeError(f"{failures} platform verification failures")

    report={
        "experiment":"acc-continuous-residual-loop-v4",
        "cycle":a.cycle,
        "source_files":[str(x) for x in files],
        "raw_ac_candidates":len(raw_candidates),
        "verified_ac_candidates":len(verified),
        "compression_moves_saved":sum(x["saved"] for x in compression),
        "selected_rows":len(selected),
        "selected_ac":sum(cid.startswith("ac-") for cid,_ in selected),
        "selected_stable":sum(cid.startswith("sac-") for cid,_ in selected),
        "dropped_for_batch_limit":dropped_for_batch_limit,
        "daily_submission_limit":daily_limit,
        "daily_submissions_used_pre":used_today,
        "daily_submissions_remaining_pre":quota_remaining,
        "quota_blocked":quota_blocked,
        "submission_id":submission_id,
        "terminal_status":terminal,
        "failed_rows":failures,
    }
    (out/"report.json").write_text(json.dumps(report,indent=2,sort_keys=True)+"\n")
    print("CONTINUOUS_AGGREGATE",json.dumps(report,sort_keys=True))

if __name__=="__main__":
    main()
