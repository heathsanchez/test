#!/usr/bin/env python3
"""Compile ACSolverX beam paths on the frozen checkpoint residual into official SAIR moves."""

from __future__ import annotations
import argparse, ast, csv, json, sys
from pathlib import Path

from solver_v2_gssub import snapshot_map, current_competitive, submit_batch
from solver_v2_checkpoint import (
    canon_pair, parse_padded_presentation, checkpoint_s_move,
    compile_checkpoint_transition, bridge_to_target, build_reverse,
)

def args():
    p=argparse.ArgumentParser()
    p.add_argument("--acc-root", required=True)
    p.add_argument("--acsolverx-root", required=True)
    p.add_argument("--beam-csv", required=True)
    p.add_argument("--residual-json", required=True)
    p.add_argument("--out-dir", default="andrews_curtis/out_v2_beam")
    p.add_argument("--submit", action="store_true")
    return p.parse_args()

def save(p,obj):
    Path(p).write_text(json.dumps(obj,indent=2,sort_keys=True)+"\n",encoding="utf-8")

def load_orig_state(path, idx):
    with Path(path).open() as f:
        for i,line in enumerate(f):
            if i==idx:
                vals=ast.literal_eval(line.strip())
                return parse_padded_presentation(vals)
    raise IndexError(idx)

def challenge_maps(manifest):
    ac={}; sac={}
    for c in manifest["challenges"]:
        cid=c["challenge_id"]
        if cid.startswith("ac-"): ac[cid]=c
        elif cid.startswith("sac-"): sac[cid]=c
    return ac,sac

def main():
    a=args()
    out=Path(a.out_dir); out.mkdir(parents=True,exist_ok=True)
    acc=Path(a.acc_root).resolve(); ax=Path(a.acsolverx_root).resolve()
    sys.path.insert(0,str(acc/"competition"/"tools"))
    from verifier import core, stable_core

    manifest=json.loads((acc/"competition"/"tools"/"verifier"/"data"/"manifest.json").read_text())
    limits=manifest["limits"]
    ac_by_id,sac_by_id=challenge_maps(manifest)
    residual=json.loads(Path(a.residual_json).read_text())
    by_idx={int(r["dataset_index"]):r["challenge_id"] for r in residual}

    # Beam CSV from a filtered subset carries orig_presentation_idx.
    beam=[]
    with Path(a.beam_csv).open(newline="") as f:
        for row in csv.DictReader(f):
            solved=str(row["solved"]).lower() in ("true","1")
            if not solved: continue
            orig=int(row["orig_presentation_idx"])
            packed=ast.literal_eval(row["path"])
            beam.append({"orig_index":orig,"packed":packed,"beam_length":int(row["path_length"])})

    reverse_paths,_=build_reverse(core,7,250000)
    attempts=[]; verified={}

    for b in beam:
        idx=b["orig_index"]
        cid=by_idx.get(idx)
        if not cid:
            continue
        c=ac_by_id[cid]
        exact=tuple(tuple(w) for w in c["initial_relators"])
        model_state=load_orig_state(ax/"data"/"AC19_extended.txt",idx)
        if canon_pair(exact)!=canon_pair(model_state):
            raise RuntimeError(f"mapping mismatch {idx} {cid}")

        cur=exact
        atomics=()
        fail=None
        for step_i,packed in enumerate(b["packed"]):
            # decode exact packed action used by public policy
            L=24; x=int(packed)
            k1=(x//(4*L))+1
            rem=x%(4*L); k2_tmp=rem//4; ij=rem%4
            i=ij//2; j=ij%2
            k2=k2_tmp*((-1)**j)-j
            action=[int(i),int(j),int(k1),int(k2)]

            model_state=checkpoint_s_move(model_state,action,max_length=24)
            desired=canon_pair(model_state)
            if canon_pair(cur)==desired:
                continue
            hit=compile_checkpoint_transition(
                core,cur,action[0],desired,total_cap=limits["max_total_relator_length"]
            )
            if hit is None:
                fail={"code":"uncompiled_beam_transition","step":step_i,"action":action}
                break
            cur,edge=hit
            atomics+=tuple(edge)

        if fail is None:
            bridge=bridge_to_target(core,cur,reverse_paths)
            if bridge is None:
                fail={"code":"no_terminal_bridge"}
            else:
                atomics+=tuple(bridge)

        rec={"challenge_id":cid,"dataset_index":idx,"beam_length":b["beam_length"],
             "compile_ok":fail is None,"failure":fail}
        if fail is None:
            v=core.verify(c,list(atomics),c["move_spec_version"],limits)
            rec["atomic_length"]=len(atomics); rec["ac_verdict"]=v
            if v["ok"]:
                sid="sac-"+cid[3:]
                sc=sac_by_id[sid]
                sp=tuple(atomics)+(16,15)
                sv=stable_core.verify(sc,list(sp),sc["move_spec_version"],limits)
                rec["stable_verdict"]=sv
                if sv["ok"]:
                    verified[cid]={"path":tuple(atomics),"verdict":v,"stable_id":sid,
                                   "stable_path":sp,"stable_verdict":sv,
                                   "dataset_index":idx,"beam_length":b["beam_length"]}
        attempts.append(rec)

    save(out/"compile_attempts.json",attempts)

    ac_snap,ac_live=snapshot_map("ac")
    sac_snap,sac_live=snapshot_map("stable_ac")
    save(out/"snapshot_ac_pre_submit.json",ac_snap)
    save(out/"snapshot_stable_ac_pre_submit.json",sac_snap)

    lines=[]; selection=[]
    for cid,v in sorted(verified.items(),key=lambda kv:(len(kv[1]["path"]),kv[0])):
        ok,reason=current_competitive(ac_live[cid],len(v["path"]))
        selection.append({"challenge_id":cid,"problem":"ac","length":len(v["path"]),
                          "live_status":ac_live[cid]["status"],
                          "live_best":ac_live[cid].get("currentBestLength"),
                          "selected":ok,"reason":reason})
        if ok:
            lines.append(f"{cid}: {json.dumps(list(v['path']),separators=(',',':'))}")
        sid=v["stable_id"]
        sok,sreason=current_competitive(sac_live[sid],len(v["stable_path"]))
        selection.append({"challenge_id":sid,"problem":"stable_ac","length":len(v["stable_path"]),
                          "live_status":sac_live[sid]["status"],
                          "live_best":sac_live[sid].get("currentBestLength"),
                          "selected":sok,"reason":sreason})
        if sok:
            lines.append(f"{sid}: {json.dumps(list(v['stable_path']),separators=(',',':'))}")
    save(out/"selection.json",selection)
    text="\n".join(lines)+("\n" if lines else "")
    (out/"submission_beam_v2.txt").write_text(text)

    submission_id=None; final=None
    if a.submit and lines:
        submission_id,response,polls,final=submit_batch(text)
        save(out/"submission_receipt.json",{
            "submission_id":submission_id,"response":response,"polls":polls,"final":final
        })

    report={
        "experiment":"andrews-curtis-v2-beam-residual",
        "beam_solved_rows":len(beam),
        "compile_attempts":len(attempts),
        "verified_ac":len(verified),
        "competitive_rows":len(lines),
        "submission_id":submission_id,
        "solutions":[{
            "ac_id":cid,"dataset_index":v["dataset_index"],"beam_steps":v["beam_length"],
            "ac_length":len(v["path"]),"ac_hash":v["verdict"]["certificate_hash"],
            "stable_id":v["stable_id"],"stable_length":len(v["stable_path"]),
            "stable_hash":v["stable_verdict"]["certificate_hash"]
        } for cid,v in sorted(verified.items())]
    }
    save(out/"report_beam_v2.json",report)
    print("FINAL",json.dumps(report,sort_keys=True),flush=True)

if __name__=="__main__":
    main()
