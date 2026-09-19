#!/usr/bin/env python3
import argparse,json,os,re,sys
from datetime import datetime, timezone
from urllib import request
from pathlib import Path

INV=(0,1,3,2,5,4,7,6,9,8,11,10,13,12)
PUBLIC_BASE="https://server-9527.sair.foundation"
API_BASE="https://api.sair.foundation/api/public/v1"


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
    states=[state];out=[];pos={state:0}
    for m in moves:
        nxt=core.apply_move(states[-1],m)
        if nxt in pos:
            j=pos[nxt]
            for st in states[j+1:]:pos.pop(st,None)
            states=states[:j+1];out=out[:j]
        else:
            out.append(m);states.append(nxt);pos[nxt]=len(out)
    return out


def compress(core,initial,moves):
    cur=list(moves)
    while True:
        nxt=inverse_reduce(cur)
        nxt=loop_erase(core,initial,nxt)
        nxt=inverse_reduce(nxt)
        if len(nxt)==len(cur):return nxt
        cur=nxt


def strict_record_steal(row,candidate_len):
    if row.get("status") == "unsolved":return True,"currently_unsolved"
    best=row.get("currentBestLength")
    if isinstance(best,int) and candidate_len < best:return True,"strict_improvement"
    if isinstance(best,int) and candidate_len == best:return False,"tie_not_a_strict_steal"
    return False,"longer_than_live_best"


def get_json(url,auth=False):
    h={"Accept":"application/json","User-Agent":"Mozilla/5.0"}
    if auth:
        key=os.environ.get("SAIR_API_KEY","").strip()
        if not key:raise RuntimeError("SAIR_API_KEY missing; publication is fail-closed")
        h["Authorization"]=f"Bearer {key}"
    req=request.Request(url,headers=h)
    with request.urlopen(req,timeout=60) as r:return json.loads(r.read().decode("utf-8"))


def public_snapshot_map(problem):
    obj=get_json(f"{PUBLIC_BASE}/api/acc/discoveries/snapshot?problem={problem}")
    d=obj.get("data",obj)
    out={}
    for x in d["items"]:
        if not isinstance(x,dict):continue
        cid=x.get("problemId") or x.get("challengeId")
        if cid:out[str(cid)]=x
    return obj,out


def submission_stamp(rec):
    if not isinstance(rec,dict):return None
    for k in ("receivedAt","updatedAt","createdAt","submittedAt","created","timestamp","submitted"):
        s=rec.get(k)
        if not isinstance(s,str) or not s.strip():continue
        try:
            dt=datetime.fromisoformat(s.strip().replace("Z","+00:00"))
            if dt.tzinfo is None:dt=dt.replace(tzinfo=timezone.utc)
            return dt.astimezone(timezone.utc)
        except Exception:pass
    return None


def authenticated_quota():
    mine=get_json(f"{API_BASE}/competitions/acc/submissions/mine?limit=100",auth=True)
    comp=get_json(f"{API_BASE}/competitions/acc",auth=True)
    md=mine.get("data",mine) if isinstance(mine,dict) else mine
    cd=comp.get("data",comp) if isinstance(comp,dict) else comp
    items=md.get("items",[]) if isinstance(md,dict) else []
    limit=None
    if isinstance(cd,dict):
        for k in ("dailySubmissions","dailySubmissionLimit","submissionsPerDay"):
            v=cd.get(k)
            if isinstance(v,int):limit=v;break
    if limit is None:limit=40
    today=datetime.now(timezone.utc).date()
    used=sum((submission_stamp(x) is not None and submission_stamp(x).date()==today) for x in items)
    return {"used":used,"remaining":max(0,limit-used),"limit":limit}


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
    limits=manifest["limits"];by_id={c["challenge_id"]:c for c in manifest["challenges"]}
    out=Path(a.out_dir);out.mkdir(parents=True,exist_ok=True)

    files=sorted(Path(".").glob(a.glob));raw_candidates={}
    for fp in files:
        for line in fp.read_text().splitlines():
            parsed=parse_line(line)
            if not parsed:continue
            cid,moves=parsed
            if not cid.startswith("ac-"):continue
            prev=raw_candidates.get(cid)
            if prev is None or len(moves)<len(prev):raw_candidates[cid]=moves

    verified={};compression=[]
    for cid,moves in sorted(raw_candidates.items()):
        c=by_id[cid];short=compress(core,c["initial_relators"],moves)
        verdict=core.verify(c,short,c["move_spec_version"],limits)
        sid="sac-"+cid[3:];sc=by_id[sid];stable=short+[16,15]
        sv=stable_core.verify(sc,stable,sc["move_spec_version"],limits)
        rec={"challenge_id":cid,"raw_length":len(moves),"compressed_length":len(short),"saved":len(moves)-len(short),"ac_ok":bool(verdict.get("ok")),"stable_id":sid,"stable_length":len(stable),"stable_ok":bool(sv.get("ok"))}
        compression.append(rec)
        if not verdict.get("ok") or not sv.get("ok"):raise RuntimeError(f"compressed candidate failed official verifier: {rec}")
        verified[cid]=(short,sid,stable)

    # Fail closed on authenticated quota. One packed call consumes one daily submission.
    quota=authenticated_quota()
    (out/"submission_spec.json").write_text(json.dumps({"source":"authenticated-live","limits":{"dailySubmissions":quota["limit"]},"quota":quota},indent=2,sort_keys=True)+"\n")

    acsnap,ac=public_snapshot_map("ac");ssnap,sac=public_snapshot_map("stable_ac")
    (out/"snapshot_ac_pre.json").write_text(json.dumps(acsnap,indent=2,sort_keys=True)+"\n")
    (out/"snapshot_stable_pre.json").write_text(json.dumps(ssnap,indent=2,sort_keys=True)+"\n")

    selected=[];selection=[]
    for cid,(moves,sid,stable) in sorted(verified.items()):
        for qid,path,live in ((cid,moves,ac),(sid,stable,sac)):
            row=live.get(qid)
            if row is None:
                selection.append({"challenge_id":qid,"length":len(path),"selected":False,"reason":"missing_live_row"});continue
            ok,reason=strict_record_steal(row,len(path))
            selection.append({"challenge_id":qid,"length":len(path),"live_status":row.get("status"),"live_best":row.get("currentBestLength"),"selected":ok,"reason":reason})
            if ok:selected.append((qid,path))

    dropped_for_batch_limit=0
    if len(selected)>500:
        dropped_for_batch_limit=len(selected)-500;selected=selected[:500]

    # Immediately-before-publication authority recheck: both live record and authenticated quota.
    if selected:
        _,ac_now=public_snapshot_map("ac");_,sac_now=public_snapshot_map("stable_ac")
        kept=[]
        for qid,path in selected:
            row=(ac_now if qid.startswith("ac-") else sac_now).get(qid)
            ok,reason=(strict_record_steal(row,len(path)) if row is not None else (False,"missing_live_row_at_publish"))
            selection.append({"challenge_id":qid,"length":len(path),"selected_at_publish":ok,"publish_reason":reason,"publish_live_best":row.get("currentBestLength") if row else None})
            if ok:kept.append((qid,path))
        selected=kept
        quota=authenticated_quota()

    quota_blocked=bool(selected) and quota["remaining"]<1
    text="\n".join(f"{cid}: {json.dumps(m,separators=(',',':'))}" for cid,m in selected)
    if text:text+="\n"
    (out/"submission.txt").write_text(text)
    (out/"selection.json").write_text(json.dumps(selection,indent=2,sort_keys=True)+"\n")
    (out/"compression.json").write_text(json.dumps(compression,indent=2,sort_keys=True)+"\n")

    submission_id=None;terminal=None;failures=None
    if selected and not quota_blocked:
        submission_id,response,polls,final=submit_batch(text)
        (out/"submission_response.json").write_text(json.dumps(response,indent=2,sort_keys=True)+"\n")
        (out/"submission_polls.json").write_text(json.dumps(polls,indent=2,sort_keys=True)+"\n")
        (out/"submission_final.json").write_text(json.dumps(final,indent=2,sort_keys=True)+"\n")
        d=final.get("data",final);terminal=str(d.get("status","")).lower() if isinstance(d,dict) else ""
        results=d.get("results",[]) if isinstance(d,dict) else []
        failures=sum(1 for x in results if x.get("ok") is False) if isinstance(results,list) else None
        if terminal not in ("complete","completed"):raise RuntimeError(f"submission terminal state {terminal}")
        if failures:raise RuntimeError(f"{failures} platform verification failures")

    report={"experiment":"acc-continuous-residual-loop-v4","cycle":a.cycle,"source_files":[str(x) for x in files],"raw_ac_candidates":len(raw_candidates),"verified_ac_candidates":len(verified),"compression_moves_saved":sum(x["saved"] for x in compression),"selected_rows":len(selected),"selected_ac":sum(cid.startswith("ac-") for cid,_ in selected),"selected_stable":sum(cid.startswith("sac-") for cid,_ in selected),"dropped_for_batch_limit":dropped_for_batch_limit,"daily_submission_limit":quota["limit"],"daily_submissions_used_pre":quota["used"],"daily_submissions_remaining_pre":quota["remaining"],"quota_blocked":quota_blocked,"submission_id":submission_id,"terminal_status":terminal,"failed_rows":failures}
    (out/"report.json").write_text(json.dumps(report,indent=2,sort_keys=True)+"\n")
    print("CONTINUOUS_AGGREGATE",json.dumps(report,sort_keys=True))


if __name__=="__main__":main()
