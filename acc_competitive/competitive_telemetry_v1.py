#!/usr/bin/env python3
import argparse,json,sys
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"andrews_curtis"))
from solver_v2_gssub import api,data_obj,snapshot_map

def save(p,o): Path(p).write_text(json.dumps(o,indent=2,sort_keys=True)+"\n")

def get_lb(problem):
    st,_,obj=api("GET",f"/competitions/acc/leaderboard?problem={problem}")
    if not 200<=st<300: raise RuntimeError((st,obj))
    return obj

def items(obj):
    d=data_obj(obj); return d.get("items",[]) if isinstance(d,dict) else []

def cmap(obj): return {x["challengeId"]:x for x in items(obj)}
def tmap(obj): return {x["team"]["teamId"]:x for x in items(obj)}

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--out-dir",required=True)
    ap.add_argument("--prev-ac")
    ap.add_argument("--prev-stable")
    ap.add_argument("--prev-lba")
    ap.add_argument("--prev-lbs")
    ap.add_argument("--prev-history")
    a=ap.parse_args()
    out=Path(a.out_dir);out.mkdir(parents=True,exist_ok=True)

    acs,ac=snapshot_map("ac"); ss,sac=snapshot_map("stable_ac")
    lba=get_lb("ac"); lbs=get_lb("stable_ac")
    save(out/"snapshot_ac.json",acs);save(out/"snapshot_stable.json",ss)
    save(out/"leaderboard_ac.json",lba);save(out/"leaderboard_stable.json",lbs)

    history=[]
    if a.prev_history and Path(a.prev_history).exists():
        history=json.loads(Path(a.prev_history).read_text())

    all_intervals=[]
    exact=[]
    for problem,cur_snap,cur_lb,p_snap,p_lb in (
      ("ac",acs,lba,a.prev_ac,a.prev_lba),
      ("stable_ac",ss,lbs,a.prev_stable,a.prev_lbs),
    ):
        if not p_snap or not Path(p_snap).exists() or not p_lb or not Path(p_lb).exists():
            continue
        prev_snap=json.loads(Path(p_snap).read_text());prev_lb=json.loads(Path(p_lb).read_text())
        cm=cmap(cur_snap);pm=cmap(prev_snap)
        events=[]
        for cid,c in cm.items():
            p=pm.get(cid)
            if not p:continue
            pb=p.get("currentBestLength");cb=c.get("currentBestLength")
            if p.get("status")=="unsolved" and c.get("status")=="solved":
                events.append({"challenge_id":cid,"kind":"new_solve","before":None,"after":cb,
                               "before_k":p.get("kTeams"),"after_k":c.get("kTeams")})
            elif isinstance(pb,int) and isinstance(cb,int) and cb<pb:
                events.append({"challenge_id":cid,"kind":"shortened","before":pb,"after":cb,
                               "before_k":p.get("kTeams"),"after_k":c.get("kTeams")})
            elif pb==cb and p.get("kTeams")!=c.get("kTeams"):
                events.append({"challenge_id":cid,"kind":"tie_change","before":pb,"after":cb,
                               "before_k":p.get("kTeams"),"after_k":c.get("kTeams")})
        ct=tmap(cur_lb);pt=tmap(prev_lb)
        deltas=[]
        for tid,x in ct.items():
            y=pt.get(tid)
            if not y:continue
            dc=(x.get("currentBestCount") or 0)-(y.get("currentBestCount") or 0)
            ds=float(x.get("score") or 0)-float(y.get("score") or 0)
            if dc or abs(ds)>1e-12:
                deltas.append({"teamId":tid,"teamName":x["team"].get("teamName"),
                               "delta_record_count":dc,"delta_score":ds})
        interval={
          "problem":problem,
          "from_generatedAt":data_obj(prev_snap).get("generatedAt"),
          "to_generatedAt":data_obj(cur_snap).get("generatedAt"),
          "events":events,"team_deltas":deltas,
        }
        all_intervals.append(interval)

        # Conservative exact attribution only in sparse intervals with a unique accounting solution.
        substantive=[e for e in events if e["kind"] in ("new_solve","shortened")]
        plus=[d for d in deltas if d["delta_record_count"]==1]
        minus=[d for d in deltas if d["delta_record_count"]==-1]
        nonunit=[d for d in deltas if d["delta_record_count"] not in (-1,0,1)]
        if len(substantive)==1 and not nonunit:
            e=substantive[0]
            if e["kind"]=="new_solve" and e.get("after_k")==1 and len(plus)==1 and len(minus)==0:
                exact.append({**e,"problem":problem,"winner":plus[0],"loser":None,"basis":"single sparse new-solve interval"})
            elif e["kind"]=="shortened" and e.get("before_k")==1 and e.get("after_k")==1 and len(plus)==1 and len(minus)==1:
                exact.append({**e,"problem":problem,"winner":plus[0],"loser":minus[0],"basis":"single sparse unique-record transfer"})

    history.extend(exact)
    save(out/"intervals.json",all_intervals)
    save(out/"exact_attributions.json",exact)
    save(out/"attribution_history.json",history)
    rep={"intervals":len(all_intervals),"exact_attributions_this_run":len(exact),"cumulative_exact_attributions":len(history),
         "note":"Only sparse intervals with uniquely determined team-count accounting are attributed exactly; all other public events remain ambiguous."}
    save(out/"report.json",rep)
    print("COMPETITIVE_TELEMETRY",json.dumps(rep,sort_keys=True))

if __name__=="__main__":main()
