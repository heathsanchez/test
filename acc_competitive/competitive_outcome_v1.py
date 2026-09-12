#!/usr/bin/env python3
import argparse,json
from pathlib import Path

def save(p,o): Path(p).write_text(json.dumps(o,indent=2,sort_keys=True)+"\n")

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--selected",required=True)
    ap.add_argument("--glob",required=True)
    ap.add_argument("--out-dir",required=True)
    ap.add_argument("--prior-successes")
    ap.add_argument("--prior-failures")
    a=ap.parse_args()
    out=Path(a.out_dir);out.mkdir(parents=True,exist_ok=True)
    selected=json.loads(Path(a.selected).read_text())
    rows={}
    files=sorted(Path(".").glob(a.glob))
    for fp in files:
        try:data=json.loads(fp.read_text())
        except Exception:continue
        if not isinstance(data,list):continue
        for r in data:
            cid=r.get("challenge_id")
            if cid: rows[cid]=r
    outcomes=[]
    successes=[]
    failures=[]
    for cid in selected:
        r=rows.get(cid)
        if r is None:
            outcomes.append({"challenge_id":cid,"outcome":"not_processed"})
            continue
        live=r.get("live_best")
        alen=r.get("atomic_length")
        verdict=(r.get("ac_verdict") or {}).get("ok") is True
        q=r.get("quotient_found")
        comp=r.get("compile")
        if verdict and isinstance(alen,int) and isinstance(live,int):
            if alen<live:
                outcome="strict_improvement"; successes.append(cid)
            elif alen==live:
                outcome="tie"; successes.append(cid)
            else:
                outcome="noncompetitive_verified"; failures.append(cid)
        elif not q:
            outcome="search_failure"; failures.append(cid)
        elif q and not verdict:
            outcome="compile_or_verify_failure"; failures.append(cid)
        else:
            outcome="other_failure"; failures.append(cid)
        outcomes.append({
          "challenge_id":cid,"outcome":outcome,"live_best":live,"atomic_length":alen,
          "nodes":r.get("nodes"),"quotient_found":q,
        })

    prior_s=[]
    if a.prior_successes and Path(a.prior_successes).exists():
        prior_s=json.loads(Path(a.prior_successes).read_text())
    prior_f=[]
    if a.prior_failures and Path(a.prior_failures).exists():
        prior_f=json.loads(Path(a.prior_failures).read_text())
    ps=[x["challenge_id"] if isinstance(x,dict) else str(x) for x in prior_s]
    pf=[x["challenge_id"] if isinstance(x,dict) else str(x) for x in prior_f]
    all_s=list(dict.fromkeys(ps+successes))
    all_f=list(dict.fromkeys(pf+failures))
    # Success takes precedence if a challenge was previously failed then later improved.
    ss=set(all_s); all_f=[x for x in all_f if x not in ss]
    save(out/"attack_outcomes.json",outcomes)
    save(out/"known_successes.json",all_s)
    save(out/"known_failures.json",all_f)
    rep={
      "selected":len(selected),"processed":len(rows),
      "strict_improvements":sum(x["outcome"]=="strict_improvement" for x in outcomes),
      "ties":sum(x["outcome"]=="tie" for x in outcomes),
      "verified_noncompetitive":sum(x["outcome"]=="noncompetitive_verified" for x in outcomes),
      "search_failures":sum(x["outcome"]=="search_failure" for x in outcomes),
      "compile_or_verify_failures":sum(x["outcome"]=="compile_or_verify_failure" for x in outcomes),
      "not_processed":sum(x["outcome"]=="not_processed" for x in outcomes),
      "cumulative_known_successes":len(all_s),"cumulative_known_failures":len(all_f),
    }
    save(out/"outcome_report.json",rep)
    print("COMPETITIVE_OUTCOME",json.dumps(rep,sort_keys=True))

if __name__=="__main__":main()
