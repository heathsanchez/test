#!/usr/bin/env python3
import argparse, json, math, statistics, sys
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"andrews_curtis"))
from solver_v2_gssub import api, data_obj, snapshot_map

def save(path,obj):
    Path(path).write_text(json.dumps(obj,indent=2,sort_keys=True)+"\n",encoding="utf-8")

def load_items(path):
    if not path: return None
    p=Path(path)
    if not p.exists(): return None
    d=json.loads(p.read_text())
    x=d.get("data",d) if isinstance(d,dict) else d
    if isinstance(x,dict): return x.get("items",[])
    return x if isinstance(x,list) else None

def leaderboard(problem):
    st,_,obj=api("GET",f"/competitions/acc/leaderboard?problem={problem}")
    if not 200<=st<300: raise RuntimeError((st,obj))
    return obj

def submissions_mine():
    st,_,obj=api("GET","/competitions/acc/submissions/mine")
    if not 200<=st<300: raise RuntimeError((st,obj))
    return obj

def invert(w): return tuple(-a for a in reversed(w))

def word_stats(w):
    w=tuple(w); n=len(w)
    ex=sum(1 if a==1 else -1 if a==-1 else 0 for a in w)
    ey=sum(1 if a==2 else -1 if a==-2 else 0 for a in w)
    switches=sum(1 for a,b in zip(w,w[1:]) if abs(a)!=abs(b))
    signs=sum(1 for a,b in zip(w,w[1:]) if (a>0)!=(b>0))
    runs=0 if not w else 1+switches
    big=set(zip(w,w[1:])) if n>=2 else set()
    return dict(n=n,ex=ex,ey=ey,switches=switches,signswitch=signs,runs=runs,big=big)

def features(c):
    r0=tuple(c["initial_relators"][0]); r1=tuple(c["initial_relators"][1])
    a=word_stats(r0); b=word_stats(r1)
    inter=len(a["big"]&b["big"]); union=len(a["big"]|b["big"])
    det=abs(a["ex"]*b["ey"]-a["ey"]*b["ex"])
    return {
      "total_len":a["n"]+b["n"],
      "max_len":max(a["n"],b["n"]),
      "min_len":min(a["n"],b["n"]),
      "len_diff":abs(a["n"]-b["n"]),
      "det_abs":det,
      "r0_ex_abs":abs(a["ex"]),"r0_ey_abs":abs(a["ey"]),
      "r1_ex_abs":abs(b["ex"]),"r1_ey_abs":abs(b["ey"]),
      "switches":a["switches"]+b["switches"],
      "sign_switches":a["signswitch"]+b["signswitch"],
      "runs":a["runs"]+b["runs"],
      "bigram_jaccard":inter/union if union else 0.0,
      "r0_inv_pal":1.0 if r0==invert(r0) else 0.0,
      "r1_inv_pal":1.0 if r1==invert(r1) else 0.0,
      "end_cancel_potential":float((bool(r0 and r1) and (r0[-1]==-r1[0] or r1[-1]==-r0[0]))),
    }

def means(ids, fmap, keys):
    ids=[i for i in ids if i in fmap]
    if not ids:return {k:0.0 for k in keys}
    return {k:sum(float(fmap[i][k]) for i in ids)/len(ids) for k in keys}

def zstats(fmap,keys):
    vals={k:[float(v[k]) for v in fmap.values()] for k in keys}
    mu={k:statistics.fmean(vals[k]) for k in keys}
    sd={k:statistics.pstdev(vals[k]) or 1.0 for k in keys}
    return mu,sd

def contrast_score(fid,fmap,keys,mu,sd,pos_mean,neg_mean):
    s=0.0
    for k in keys:
        z=(float(fmap[fid][k])-mu[k])/sd[k]
        d=(pos_mean[k]-neg_mean[k])/sd[k]
        s+=z*d
    return s/max(1,len(keys))

def leaderboard_map(obj):
    d=data_obj(obj); return {x["team"]["teamId"]:x for x in d.get("items",[])}

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--acc-root",required=True)
    p.add_argument("--out-dir",required=True)
    p.add_argument("--prev-ac")
    p.add_argument("--prev-stable")
    p.add_argument("--prev-leaderboard-ac")
    p.add_argument("--prev-leaderboard-stable")
    p.add_argument("--known-failures")
    p.add_argument("--known-successes")
    p.add_argument("--attack-count",type=int,default=64)
    p.add_argument("--defend-fraction",type=float,default=0.20)
    p.add_argument("--shards",type=int,default=8)
    a=p.parse_args()
    out=Path(a.out_dir);out.mkdir(parents=True,exist_ok=True)

    manifest=json.loads((Path(a.acc_root)/"competition/tools/verifier/data/manifest.json").read_text())
    byid={c["challenge_id"]:c for c in manifest["challenges"] if c["challenge_id"].startswith("ac-")}

    acsnap,ac=snapshot_map("ac"); ssnap,sac=snapshot_map("stable_ac")
    lba=leaderboard("ac"); lbs=leaderboard("stable_ac"); mine=submissions_mine()
    save(out/"snapshot_ac.json",acsnap); save(out/"snapshot_stable.json",ssnap)
    save(out/"leaderboard_ac.json",lba); save(out/"leaderboard_stable.json",lbs); save(out/"submissions_mine.json",mine)

    prev_ac_items=load_items(a.prev_ac) or []
    prev_ac={x["challengeId"]:x for x in prev_ac_items}
    prev_s_items=load_items(a.prev_stable) or []
    prev_s={x["challengeId"]:x for x in prev_s_items}

    events=[]
    for cid,row in ac.items():
        pr=prev_ac.get(cid)
        if not pr: continue
        pb=pr.get("currentBestLength"); cb=row.get("currentBestLength")
        if pr.get("status")=="unsolved" and row.get("status")=="solved":
            events.append({"challenge_id":cid,"kind":"new_solve","before":None,"after":cb,"kTeams":row.get("kTeams")})
        elif isinstance(pb,int) and isinstance(cb,int) and cb<pb:
            events.append({"challenge_id":cid,"kind":"shortened","before":pb,"after":cb,"delta":pb-cb,
                           "ratio":cb/pb if pb else None,"kTeams":row.get("kTeams")})
        elif row.get("kTeams")!=pr.get("kTeams") and cb==pb:
            events.append({"challenge_id":cid,"kind":"tie_change","before_k":pr.get("kTeams"),"after_k":row.get("kTeams"),"best":cb})
    save(out/"record_events.json",events)

    # Our exact best submitted lengths.
    our={}
    md=data_obj(mine)
    for sub in md.get("items",[]):
        for r in sub.get("results",[]):
            if not r.get("ok"): continue
            cid=r.get("challenge_id"); n=r.get("length")
            if cid and isinstance(n,int):
                our[cid]=min(n,our.get(cid,n))
    ours_status=[]
    for cid,n in sorted(our.items()):
        live=(ac if cid.startswith("ac-") else sac).get(cid,{})
        best=live.get("currentBestLength"); k=live.get("kTeams")
        if isinstance(best,int):
            status="unique_hold" if n==best and k==1 else "tied_hold" if n==best else "lost" if n>best else "ahead_unpublished"
        else: status="unknown"
        ours_status.append({"challenge_id":cid,"our_best":n,"live_best":best,"kTeams":k,"status":status})
    save(out/"mathgraph_status.json",ours_status)

    # Aggregate contestant movements. This is exact at team-total level, not challenge attribution.
    prev_lba=json.loads(Path(a.prev_leaderboard_ac).read_text()) if a.prev_leaderboard_ac and Path(a.prev_leaderboard_ac).exists() else None
    prev_lbs=json.loads(Path(a.prev_leaderboard_stable).read_text()) if a.prev_leaderboard_stable and Path(a.prev_leaderboard_stable).exists() else None
    deltas=[]
    for problem,cur,prev in (("ac",lba,prev_lba),("stable_ac",lbs,prev_lbs)):
        cm=leaderboard_map(cur); pm=leaderboard_map(prev) if prev else {}
        for tid,x in cm.items():
            y=pm.get(tid)
            deltas.append({
              "problem":problem,"teamId":tid,"teamName":x["team"].get("teamName"),"rank":x.get("rank"),
              "score":float(x.get("score") or 0),"record_count":x.get("currentBestCount"),
              "delta_score":None if not y else float(x.get("score") or 0)-float(y.get("score") or 0),
              "delta_record_count":None if not y else (x.get("currentBestCount") or 0)-(y.get("currentBestCount") or 0),
            })
    save(out/"contestant_deltas.json",deltas)

    fmap={cid:features(c) for cid,c in byid.items()}
    keys=list(next(iter(fmap.values())).keys())
    mu,sd=zstats(fmap,keys)

    known_success=[]
    kp=ROOT/"andrews_curtis/checkpoint_residual_v2.json"
    if kp.exists():
        raw=json.loads(kp.read_text())
        known_success=[x["challenge_id"] if isinstance(x,dict) else str(x) for x in raw]
    if a.known_successes and Path(a.known_successes).exists():
        raw=json.loads(Path(a.known_successes).read_text())
        known_success += [x["challenge_id"] if isinstance(x,dict) else str(x) for x in raw]
    static_success=ROOT/"acc_competitive/recovered_cycle2_successes.json"
    if static_success.exists():
        raw=json.loads(static_success.read_text())
        known_success += [x["challenge_id"] if isinstance(x,dict) else str(x) for x in raw]
    known_success=list(dict.fromkeys(known_success))
    known_fail=[]
    if a.known_failures and Path(a.known_failures).exists():
        raw=json.loads(Path(a.known_failures).read_text())
        known_fail=[x["challenge_id"] if isinstance(x,dict) else str(x) for x in raw]
    static_fail=ROOT/"acc_competitive/recovered_cycle2_failures.json"
    if static_fail.exists():
        raw=json.loads(static_fail.read_text())
        known_fail += [x["challenge_id"] if isinstance(x,dict) else str(x) for x in raw]
    known_fail=list(dict.fromkeys(known_fail))
    ss=set(known_success)
    known_fail=[x for x in known_fail if x not in ss]

    save(out/"known_successes_input.json",known_success)
    save(out/"known_failures_input.json",known_fail)
    success_mean=means(known_success,fmap,keys); fail_mean=means(known_fail,fmap,keys)
    positive_events=[e["challenge_id"] for e in events if e["kind"] in ("new_solve","shortened")]
    # Unchanged controls are evidence of no public movement in this interval, not certified failures.
    unchanged=[cid for cid,row in ac.items() if cid in prev_ac and row.get("currentBestLength")==prev_ac[cid].get("currentBestLength") and row.get("status")=="solved"]
    event_mean=means(positive_events,fmap,keys); unchanged_mean=means(unchanged,fmap,keys)

    sep=[]
    for k in keys:
        sep.append({
          "feature":k,
          "mathgraph_success_minus_failure_sd":(success_mean[k]-fail_mean[k])/sd[k] if known_success and known_fail else None,
          "public_moved_minus_unchanged_sd":(event_mean[k]-unchanged_mean[k])/sd[k] if positive_events and unchanged else None,
        })
    sep.sort(key=lambda x:max(abs(x["mathgraph_success_minus_failure_sd"] or 0),abs(x["public_moved_minus_unchanged_sd"] or 0)),reverse=True)
    save(out/"separators.json",sep)

    our_ac={x["challenge_id"]:x for x in ours_status if x["challenge_id"].startswith("ac-")}
    event_set=set(positive_events)
    acquire=[]
    defend=[]
    for cid,row in ac.items():
        if cid not in fmap or row.get("status")!="solved": continue
        best=row.get("currentBestLength"); k=row.get("kTeams")
        if not isinstance(best,int) or best<100: continue
        os=our_ac.get(cid)
        status=None if not os else os["status"]
        # A just-submitted path can be ahead of a lagging public snapshot.
        # Do not waste a second acquisition search until the board catches up.
        if status=="ahead_unpublished": continue
        cap=contrast_score(cid,fmap,keys,mu,sd,success_mean,fail_mean) if known_success and known_fail else 0.0
        mov=contrast_score(cid,fmap,keys,mu,sd,event_mean,unchanged_mean) if positive_events and unchanged else 0.0
        value=(2.0 if k==1 else 1.0/(2**max(0,(k or 1)-1)))
        length_score=math.log1p(best)
        lost_bonus=1.5 if status=="lost" else 0.0
        recent_bonus=0.8 if cid in event_set else 0.0
        if status=="unique_hold":
            # Defense does not add a point immediately, but a shorter owned
            # record increases survival probability. Prefer large/slack-looking
            # records in regions where our shortening mechanism has worked.
            score=0.90*length_score + 1.50*cap + 0.50*mov + recent_bonus
            defend.append({
              "challenge_id":cid,"priority":score,"mode":"defend","live_best":best,"kTeams":k,
              "record_value":1.0,"capability_score":cap,"public_movement_score":mov,
              "mathgraph_status":status,"recent_public_move":cid in event_set,**fmap[cid],
            })
            continue
        # Tied holds belong here too: beating our own tie converts a tiny
        # shared score into a unique full point.
        tie_break_bonus=1.5 if status=="tied_hold" else 0.0
        score=2.0*value + 0.75*length_score + 1.25*cap + 0.75*mov + lost_bonus + recent_bonus + tie_break_bonus
        acquire.append({
          "challenge_id":cid,"priority":score,"mode":"acquire","live_best":best,"kTeams":k,
          "record_value":value,"capability_score":cap,"public_movement_score":mov,
          "mathgraph_status":status,"recent_public_move":cid in event_set,**fmap[cid],
        })
    acquire.sort(key=lambda x:(-x["priority"],-x["live_best"],x["challenge_id"]))
    defend.sort(key=lambda x:(-x["priority"],-x["live_best"],x["challenge_id"]))
    defend_n=min(len(defend),max(0,round(a.attack_count*max(0.0,min(0.5,a.defend_fraction)))))
    acquire_n=min(len(acquire),a.attack_count-defend_n)
    selected=acquire[:acquire_n]+defend[:defend_n]
    if len(selected)<a.attack_count:
        used={x["challenge_id"] for x in selected}
        extras=[x for x in acquire[acquire_n:]+defend[defend_n:] if x["challenge_id"] not in used]
        selected+=extras[:a.attack_count-len(selected)]
    selected.sort(key=lambda x:(x["mode"]!="acquire",-x["priority"],x["challenge_id"]))
    candidates=acquire+defend
    candidates.sort(key=lambda x:(-x["priority"],x["mode"],-x["live_best"],x["challenge_id"]))
    save(out/"attack_ranking.json",candidates[:500])
    save(out/"selected_targets.json",[x["challenge_id"] for x in selected])
    save(out/"selected_modes.json",[{k:x[k] for k in ("challenge_id","mode","priority","live_best","kTeams","mathgraph_status")} for x in selected])

    shards=[[] for _ in range(a.shards)]
    for i,x in enumerate(selected): shards[i%a.shards].append(x["challenge_id"])
    for i,s in enumerate(shards): save(out/f"shard_{i}.json",s)

    report={
      "experiment":"acc-competitive-residual-v1",
      "public_record_events":len(events),
      "public_shortening_or_new_solve_events":len(positive_events),
      "contestants":len(data_obj(lba).get("items",[])),
      "mathgraph_submitted_challenges":len(our),
      "mathgraph_current_unique":sum(x["status"]=="unique_hold" for x in ours_status),
      "mathgraph_current_tied":sum(x["status"]=="tied_hold" for x in ours_status),
      "mathgraph_lost":sum(x["status"]=="lost" for x in ours_status),
      "known_success_cases":len(known_success),
      "known_failure_cases":len(known_fail),
      "attack_candidates":len(candidates),
      "selected_targets":len(selected),
      "selected_acquire":sum(x.get("mode")=="acquire" for x in selected),
      "selected_defend":sum(x.get("mode")=="defend" for x in selected),
      "shards":[len(x) for x in shards],
      "exact_per_challenge_opponent_holder_available":False,
      "holder_note":"Public API exposes challenge best length/kTeams and aggregate team records, but no per-challenge holder endpoint was found; do not treat absent team/challenge cells as failures.",
    }
    save(out/"report.json",report)
    print("COMPETITIVE_SCOUT",json.dumps(report,sort_keys=True))

if __name__=="__main__": main()
