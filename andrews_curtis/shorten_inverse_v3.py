#!/usr/bin/env python3
import argparse,ast,json,re,sys
from pathlib import Path

INV=(0,1,3,2,5,4,7,6,9,8,11,10,13,12)

def reduce_moves(xs):
    st=[]
    for a in xs:
        if st and st[-1] < 14 and a < 14 and INV[st[-1]]==a:
            st.pop()
        else:
            st.append(a)
    return st

def parse(path):
    out={}
    for line in Path(path).read_text().splitlines():
        if not line.startswith("ac-"): continue
        cid,s=line.split(":",1)
        out[cid]=list(ast.literal_eval(s.strip()))
    return out

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
    limits=manifest["limits"]
    by_id={c["challenge_id"]:c for c in manifest["challenges"]}

    out=Path(a.out_dir);out.mkdir(parents=True,exist_ok=True)
    originals=parse(a.input)
    verified={}
    rows=[]
    total_saved=0

    for cid,moves in sorted(originals.items()):
        red=reduce_moves(moves)
        saved=len(moves)-len(red)
        c=by_id[cid]
        v=core.verify(c,red,c["move_spec_version"],limits)
        sid="sac-"+cid[3:]
        sm=red+[16,15]
        sc=by_id[sid]
        sv=stable_core.verify(sc,sm,sc["move_spec_version"],limits)
        row={"ac_id":cid,"old_length":len(moves),"new_length":len(red),"saved":saved,
             "ac_ok":v["ok"],"stable_id":sid,"stable_length":len(sm),"stable_ok":sv["ok"]}
        rows.append(row)
        if not v["ok"] or not sv["ok"]:
            raise RuntimeError(f"verifier failure after inverse reduction: {row}")
        if saved>0:
            verified[cid]=(red,v,sid,sm,sv)
            total_saved+=saved

    ac_snap,ac=snapshot_map("ac")
    sac_snap,sac=snapshot_map("stable_ac")
    (out/"snapshot_ac_pre.json").write_text(json.dumps(ac_snap,indent=2,sort_keys=True)+"\n")
    (out/"snapshot_stable_pre.json").write_text(json.dumps(sac_snap,indent=2,sort_keys=True)+"\n")

    selected=[]
    selection=[]
    for cid,(m,v,sid,sm,sv) in sorted(verified.items()):
        for qid,path,live in ((cid,m,ac),(sid,sm,sac)):
            lr=live[qid]
            best=lr.get("currentBestLength")
            ok=lr.get("status")=="unsolved" or (isinstance(best,int) and len(path)<best)
            selection.append({"challenge_id":qid,"length":len(path),"live_status":lr.get("status"),
                              "live_best":best,"selected":ok})
            if ok:selected.append((qid,path))

    text="\n".join(f"{cid}: {json.dumps(m,separators=(',',':'))}" for cid,m in selected)
    if text:text+="\n"
    (out/"submission.txt").write_text(text)
    (out/"rows.json").write_text(json.dumps(rows,indent=2,sort_keys=True)+"\n")
    (out/"selection.json").write_text(json.dumps(selection,indent=2,sort_keys=True)+"\n")

    sid=None; final=None
    if a.submit and selected:
        sid,response,polls,final=submit_batch(text)
        (out/"submission_response.json").write_text(json.dumps(response,indent=2,sort_keys=True)+"\n")
        (out/"submission_polls.json").write_text(json.dumps(polls,indent=2,sort_keys=True)+"\n")
        (out/"submission_final.json").write_text(json.dumps(final,indent=2,sort_keys=True)+"\n")
        d=final.get("data",final)
        rs=d.get("results",[]) if isinstance(d,dict) else []
        if str(d.get("status","")).lower() not in ("complete","completed") or any(x.get("ok") is False for x in rs):
            raise RuntimeError("platform rejected inverse-reduced batch")

    report={"experiment":"acc-inverse-pair-shortening-v3","ac_paths":len(originals),
            "improved_ac_paths":len(verified),"total_ac_moves_saved":total_saved,
            "selected_rows":len(selected),"submission_id":sid}
    (out/"report.json").write_text(json.dumps(report,indent=2,sort_keys=True)+"\n")
    print("SHORTEN_FINAL",json.dumps(report,sort_keys=True))

if __name__=="__main__":main()
