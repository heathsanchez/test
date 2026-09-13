#!/usr/bin/env python3
import argparse,glob,json
from pathlib import Path

def save(p,o): Path(p).write_text(json.dumps(o,indent=2,sort_keys=True)+"\n")

def ids_from(path):
    if not path or not Path(path).exists(): return []
    raw=json.loads(Path(path).read_text())
    out=[]
    for x in raw:
        out.append(x.get("challenge_id") if isinstance(x,dict) else str(x))
    return [x for x in out if x]

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--selected",required=True)
    ap.add_argument("--glob",required=True)
    ap.add_argument("--out-dir",required=True)
    ap.add_argument("--prior-wins")
    ap.add_argument("--prior-attempted")
    ap.add_argument("--mechanism-id",default="gssub-v2-current")
    a=ap.parse_args()
    out=Path(a.out_dir); out.mkdir(parents=True,exist_ok=True)

    selected=json.loads(Path(a.selected).read_text())
    rows={}
    for fp in [Path(x) for x in sorted(glob.glob(a.glob,recursive=True))]:
        try: data=json.loads(fp.read_text())
        except Exception: continue
        if not isinstance(data,list): continue
        for r in data:
            cid=r.get("challenge_id")
            if cid: rows[cid]=r

    outcomes=[]
    scoring_successes=[]
    strict=[]
    ties=[]
    near=[]
    for cid in selected:
        r=rows.get(cid)
        if r is None:
            outcomes.append({"challenge_id":cid,"outcome":"not_processed","mechanism_id":a.mechanism_id})
            continue
        live=r.get("live_best")
        live_status=r.get("live_status")
        alen=r.get("atomic_length")
        verdict=(r.get("ac_verdict") or {}).get("ok") is True
        q=r.get("quotient_found")
        gap=None
        rel=None
        if verdict and isinstance(alen,int):
            if live_status=="unsolved" or live is None:
                outcome="new_solve"; scoring_successes.append(cid); strict.append(cid)
            elif isinstance(live,int):
                gap=alen-live
                rel=gap/live if live else None
                if gap<0:
                    outcome="strict_improvement"; scoring_successes.append(cid); strict.append(cid)
                elif gap==0:
                    outcome="scoring_tie"; scoring_successes.append(cid); ties.append(cid)
                else:
                    outcome="noncompetitive_verified"
                    if rel is not None and rel <= 0.10: near.append(cid)
            else:
                outcome="verified_unknown_frontier"
        elif not q:
            outcome="search_failure"
        elif q and not verdict:
            outcome="compile_or_verify_failure"
        else:
            outcome="other_failure"
        outcomes.append({
          "challenge_id":cid,"outcome":outcome,"live_status":live_status,
          "live_best":live,"atomic_length":alen,"gap_moves":gap,
          "relative_gap":rel,"nodes":r.get("nodes"),"quotient_found":q,
          "mechanism_id":a.mechanism_id,
        })

    prior_w=ids_from(a.prior_wins)
    prior_a=ids_from(a.prior_attempted)
    processed=[x["challenge_id"] for x in outcomes if x["outcome"]!="not_processed"]
    all_wins=list(dict.fromkeys(prior_w+scoring_successes))
    all_attempted=list(dict.fromkeys(prior_a+processed))
    winset=set(all_wins)
    all_nonwins=[x for x in all_attempted if x not in winset]

    save(out/"attack_outcomes.json",outcomes)
    save(out/"gap_memory.json",outcomes)
    save(out/"competitive_wins.json",all_wins)
    save(out/"competitive_attempted.json",all_attempted)
    save(out/"competitive_nonwins.json",all_nonwins)
    rep={
      "selected":len(selected),"processed":len(rows),
      "new_solves":sum(x["outcome"]=="new_solve" for x in outcomes),
      "strict_improvements":sum(x["outcome"]=="strict_improvement" for x in outcomes),
      "scoring_ties":sum(x["outcome"]=="scoring_tie" for x in outcomes),
      "scoring_successes":len(scoring_successes),
      "near_misses_within_10pct":len(near),
      "verified_noncompetitive":sum(x["outcome"]=="noncompetitive_verified" for x in outcomes),
      "search_failures":sum(x["outcome"]=="search_failure" for x in outcomes),
      "compile_or_verify_failures":sum(x["outcome"]=="compile_or_verify_failure" for x in outcomes),
      "not_processed":sum(x["outcome"]=="not_processed" for x in outcomes),
      "mechanism_id":a.mechanism_id,
      "cumulative_competitive_wins":len(all_wins),
      "cumulative_competitive_attempted":len(all_attempted),
    }
    save(out/"outcome_report.json",rep)
    print("COMPETITIVE_OUTCOME_V2",json.dumps(rep,sort_keys=True))

if __name__=="__main__": main()
