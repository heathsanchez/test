#!/usr/bin/env python3
import argparse,ast,json,sys
from pathlib import Path

def parse_ac(path):
    out={}
    for line in Path(path).read_text().splitlines():
        if not line.startswith("ac-"): continue
        cid,s=line.split(":",1)
        out[cid]=list(ast.literal_eval(s.strip()))
    return out

def loop_erase(core,initial,moves):
    state=tuple(tuple(w) for w in initial)
    states=[state]
    out=[]
    pos={state:0}
    removed=0
    for m in moves:
        nxt=core.apply_move(states[-1],m)
        if nxt in pos:
            j=pos[nxt]
            # Remove the detour from state j back to itself.
            removed += len(out)-j+1
            for st in states[j+1:]:
                pos.pop(st,None)
            states=states[:j+1]
            out=out[:j]
        else:
            out.append(m)
            states.append(nxt)
            pos[nxt]=len(out)
    return out,removed

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--acc-root",required=True)
    p.add_argument("--input",required=True)
    p.add_argument("--out-dir",required=True)
    p.add_argument("--submit",action="store_true")
    a=p.parse_args()
    root=Path(__file__).resolve().parent
    sys.path.insert(0,str(root))
    from solver_v2_gssub import snapshot_map,submit_batch

    acc=Path(a.acc_root)
    sys.path.insert(0,str(acc/"competition/tools"))
    from verifier import core,stable_core
    manifest=json.loads((acc/"competition/tools/verifier/data/manifest.json").read_text())
    limits=manifest["limits"]; by_id={c["challenge_id"]:c for c in manifest["challenges"]}
    outdir=Path(a.out_dir);outdir.mkdir(parents=True,exist_ok=True)

    originals=parse_ac(a.input)
    improved={}
    rows=[]
    total=0
    for cid,moves in sorted(originals.items()):
        c=by_id[cid]
        red,removed=loop_erase(core,c["initial_relators"],moves)
        v=core.verify(c,red,c["move_spec_version"],limits)
        sid="sac-"+cid[3:]; sc=by_id[sid]; sm=red+[16,15]
        sv=stable_core.verify(sc,sm,sc["move_spec_version"],limits)
        row={"ac_id":cid,"old_length":len(moves),"new_length":len(red),"removed":len(moves)-len(red),
             "loop_events_removed_moves":removed,"ac_ok":v["ok"],"stable_ok":sv["ok"]}
        rows.append(row)
        if not v["ok"] or not sv["ok"]: raise RuntimeError(f"loop erase invalid {row}")
        if len(red)<len(moves):
            improved[cid]=(red,sid,sm); total+=len(moves)-len(red)

    acsnap,ac=snapshot_map("ac"); ssnap,sac=snapshot_map("stable_ac")
    (outdir/"snapshot_ac_pre.json").write_text(json.dumps(acsnap,indent=2,sort_keys=True)+"\n")
    (outdir/"snapshot_stable_pre.json").write_text(json.dumps(ssnap,indent=2,sort_keys=True)+"\n")
    selected=[]; selection=[]
    for cid,(m,sid,sm) in sorted(improved.items()):
        for qid,path,live in ((cid,m,ac),(sid,sm,sac)):
            lr=live[qid]; best=lr.get("currentBestLength")
            ok=lr.get("status")=="unsolved" or (isinstance(best,int) and len(path)<best)
            selection.append({"challenge_id":qid,"length":len(path),"live_best":best,"live_status":lr.get("status"),"selected":ok})
            if ok:selected.append((qid,path))
    text="\n".join(f"{cid}: {json.dumps(m,separators=(',',':'))}" for cid,m in selected)
    if text:text+="\n"
    (outdir/"submission.txt").write_text(text)
    (outdir/"rows.json").write_text(json.dumps(rows,indent=2,sort_keys=True)+"\n")
    (outdir/"selection.json").write_text(json.dumps(selection,indent=2,sort_keys=True)+"\n")
    subid=None
    if a.submit and selected:
        subid,response,polls,final=submit_batch(text)
        (outdir/"submission_response.json").write_text(json.dumps(response,indent=2,sort_keys=True)+"\n")
        (outdir/"submission_polls.json").write_text(json.dumps(polls,indent=2,sort_keys=True)+"\n")
        (outdir/"submission_final.json").write_text(json.dumps(final,indent=2,sort_keys=True)+"\n")
        d=final.get("data",final); rs=d.get("results",[]) if isinstance(d,dict) else []
        if str(d.get("status","")).lower() not in ("complete","completed") or any(x.get("ok") is False for x in rs):
            raise RuntimeError("platform rejected loop-erased batch")
    report={"experiment":"acc-exact-loop-erasure-v3","ac_paths":len(originals),"improved_ac_paths":len(improved),
            "total_ac_moves_saved":total,"selected_rows":len(selected),"submission_id":subid}
    (outdir/"report.json").write_text(json.dumps(report,indent=2,sort_keys=True)+"\n")
    print("LOOP_FINAL",json.dumps(report,sort_keys=True))

if __name__=="__main__":main()
