#!/usr/bin/env python3
"""Transfer solved n-1 Miller-Schupp checkpoint procedures into live-unsolved n residuals."""

from __future__ import annotations
import argparse, ast, json, sys, time
from pathlib import Path

from solver_v2_gssub import (
    load_gssub, compile_quotient_path, total_len, snapshot_map,
    current_competitive, build_reverse, int_word_to_str,
)
from solver_v2_checkpoint import (
    canon_pair, parse_padded_presentation, restore_solve_data,
    checkpoint_s_move, compile_checkpoint_transition, decode_action,
)

def parse_args():
    p=argparse.ArgumentParser()
    p.add_argument("--acc-root",required=True)
    p.add_argument("--acsolverx-root",required=True)
    p.add_argument("--residual-json",required=True)
    p.add_argument("--out-dir",default="andrews_curtis/out_v2_family")
    p.add_argument("--prefix-candidates",type=int,default=3)
    p.add_argument("--nodes-per-prefix",type=int,default=30000)
    p.add_argument("--max-len",type=int,default=80)
    p.add_argument("--search-seconds",type=int,default=1200)
    return p.parse_args()

def save(path,obj):
    Path(path).write_text(json.dumps(obj,indent=2,sort_keys=True)+"\n")

def load_prefix(path,n=634):
    out=[]
    with Path(path).open() as f:
        for i,line in enumerate(f):
            if i>=n: break
            out.append(parse_padded_presentation(ast.literal_eval(line.strip())))
    return out

def challenge_maps(manifest):
    ac={}; sac={}
    for c in manifest["challenges"]:
        cid=c["challenge_id"]
        if cid.startswith("ac-"): ac[cid]=c
        elif cid.startswith("sac-"): sac[cid]=c
    return ac,sac

def infer_ms(state):
    for i,w in enumerate(state):
        w=tuple(w)
        # canonical MS long relator: Y^(n+1) X y^n x
        a=0
        while a<len(w) and w[a]==-2: a+=1
        if a>=2 and len(w)==2*a+1 and w[a]==-1 and tuple(w[a+1:-1])==(2,)*(a-1) and w[-1]==1:
            return {"n":a-1,"long_index":i,"small":tuple(state[1-i]),"long":w}
    return None

def main():
    a=parse_args()
    out=Path(a.out_dir); out.mkdir(parents=True,exist_ok=True)
    acc=Path(a.acc_root).resolve(); ax=Path(a.acsolverx_root).resolve()
    sys.path.insert(0,str(acc/"competition"/"tools"))
    from verifier import core, stable_core

    manifest=json.loads((acc/"competition"/"tools"/"verifier"/"data"/"manifest.json").read_text())
    limits=manifest["limits"]; ac_by_id,sac_by_id=challenge_maps(manifest)
    residual=json.loads(Path(a.residual_json).read_text())

    states=load_prefix(ax/"data"/"AC19_extended.txt",634)
    dataset_map={canon_pair(s):i for i,s in enumerate(states)}
    sd=restore_solve_data(ax,"610model",1000)
    solved=set(int(i) for i,x in enumerate(sd["solved_idx"][:634]) if bool(x))
    ns=load_gssub(ax)
    reverse_paths,_=build_reverse(core,7,250000)

    ac_snap,ac_live=snapshot_map("ac"); sac_snap,sac_live=snapshot_map("stable_ac")
    save(out/"snapshot_ac_before.json",ac_snap); save(out/"snapshot_stable_ac_before.json",sac_snap)

    verified={}; attempts=[]
    t0=time.time()

    for rr in residual:
        if time.time()-t0>a.search_seconds: break
        cid=rr["challenge_id"]
        if ac_live[cid]["status"]!="unsolved": continue
        c=ac_by_id[cid]
        original=tuple(tuple(w) for w in c["initial_relators"])
        fam=infer_ms(original)
        rec={"challenge_id":cid,"target_index":rr["dataset_index"],"family":fam}
        if not fam or fam["n"]<1:
            rec["failure"]="not_recognized_ms_family"; attempts.append(rec); continue

        n=fam["n"]
        pred_long=(-2,)*n+(-1,)+(2,)*(n-1)+(1,)
        pred_key=canon_pair((fam["small"],pred_long))
        pred_idx=dataset_map.get(pred_key)
        rec["predecessor_n"]=n-1; rec["predecessor_index"]=pred_idx
        if pred_idx is None or pred_idx not in solved:
            rec["failure"]="predecessor_not_checkpoint_solved"; attempts.append(rec); continue

        plen=int(sd["path_lengths"][pred_idx])
        packed=[int(x) for x in sd["best_paths"][pred_idx][:plen]]
        rec["predecessor_checkpoint_steps"]=plen

        cur=original
        model_state=states[rr["dataset_index"]]
        prefix=()
        prefixes=[{"step":0,"state":cur,"path":prefix,"total":total_len(cur)}]
        transfer_fail=None
        for step_i,p in enumerate(packed,1):
            action=decode_action(p,24)
            model_state=checkpoint_s_move(model_state,action,24)
            desired=canon_pair(model_state)
            if canon_pair(cur)==desired:
                continue
            hit=compile_checkpoint_transition(core,cur,action[0],desired,limits["max_total_relator_length"])
            if hit is None:
                transfer_fail={"step":step_i,"action":action}
                break
            cur,edge=hit
            prefix+=tuple(edge)
            prefixes.append({"step":step_i,"state":cur,"path":prefix,"total":total_len(cur)})

        rec["transfer_fail"]=transfer_fail
        rec["transferred_steps"]=prefixes[-1]["step"]
        rec["transferred_atomic_length"]=len(prefix)
        rec["best_transferred_total"]=min(x["total"] for x in prefixes)

        # Search from the smallest distinct transferred states, excluding cold.
        uniq=[]; seen=set()
        for pfx in sorted(prefixes[1:],key=lambda x:(x["total"],x["step"])):
            k=canon_pair(pfx["state"])
            if k in seen: continue
            seen.add(k); uniq.append(pfx)
            if len(uniq)>=a.prefix_candidates: break

        searches=[]
        for pfx in uniq:
            # First check whether exact reverse census can close immediately.
            suffix=reverse_paths.get(pfx["state"])
            if suffix is not None:
                full=tuple(pfx["path"])+tuple(suffix)
                v=core.verify(c,list(full),c["move_spec_version"],limits)
                searches.append({"prefix_step":pfx["step"],"prefix_total":pfx["total"],
                                 "nodes":0,"found":bool(v["ok"]),"mode":"reverse","atomic_length":len(full)})
                if v["ok"]:
                    sid="sac-"+cid[3:]; sc=sac_by_id[sid]; sp=full+(16,15)
                    sv=stable_core.verify(sc,list(sp),sc["move_spec_version"],limits)
                    if sv["ok"]:
                        verified[cid]={"path":full,"verdict":v,"stable_id":sid,"stable_path":sp,
                                       "stable_verdict":sv,"predecessor_index":pred_idx,
                                       "prefix_step":pfx["step"],"nodes":0}
                        break

            r0=int_word_to_str(pfx["state"][0]); r1=int_word_to_str(pfx["state"][1])
            solver=ns["ACRelatorSolver"](r0,r1,max_nodes=a.nodes_per_prefix,max_len=a.max_len,
                                          verbose=False,stop_early=False)
            qp,nodes,_seen=solver.solve()
            sr={"prefix_step":pfx["step"],"prefix_total":pfx["total"],
                "nodes":int(nodes),"found":qp is not None,"mode":"gssub"}
            if qp is not None:
                cont,meta=compile_quotient_path(core,ns,pfx["state"],qp,reverse_paths,
                                                 limits["max_total_relator_length"])
                sr["compile"]=meta
                if cont is not None:
                    full=tuple(pfx["path"])+tuple(cont)
                    v=core.verify(c,list(full),c["move_spec_version"],limits)
                    sr["official_ok"]=bool(v["ok"]); sr["atomic_length"]=len(full)
                    if v["ok"]:
                        sid="sac-"+cid[3:]; sc=sac_by_id[sid]; sp=full+(16,15)
                        sv=stable_core.verify(sc,list(sp),sc["move_spec_version"],limits)
                        if sv["ok"]:
                            verified[cid]={"path":full,"verdict":v,"stable_id":sid,"stable_path":sp,
                                           "stable_verdict":sv,"predecessor_index":pred_idx,
                                           "prefix_step":pfx["step"],"nodes":int(nodes)}
                            searches.append(sr)
                            break
            searches.append(sr)
        rec["searches"]=searches
        attempts.append(rec)
        print("FAMILY",json.dumps({
            "challenge":cid,"n":n,"pred_idx":pred_idx,
            "pred_steps":plen,"best_transfer_total":rec["best_transferred_total"],
            "searched_prefixes":len(searches),"verified":cid in verified
        },sort_keys=True),flush=True)

    save(out/"attempts.json",attempts)

    # Live-filter only; this experiment does not auto-submit to avoid racing the beam job.
    ac_pre,ac_now=snapshot_map("ac"); sac_pre,sac_now=snapshot_map("stable_ac")
    save(out/"snapshot_ac_pre_submit.json",ac_pre); save(out/"snapshot_stable_ac_pre_submit.json",sac_pre)
    lines=[]; selection=[]
    for cid,v in sorted(verified.items(),key=lambda kv:(len(kv[1]["path"]),kv[0])):
        ok,reason=current_competitive(ac_now[cid],len(v["path"]))
        selection.append({"challenge_id":cid,"length":len(v["path"]),"selected":ok,"reason":reason,
                          "live_status":ac_now[cid]["status"],"live_best":ac_now[cid].get("currentBestLength")})
        if ok: lines.append(f"{cid}: {json.dumps(list(v['path']),separators=(',',':'))}")
        sid=v["stable_id"]; sok,sreason=current_competitive(sac_now[sid],len(v["stable_path"]))
        selection.append({"challenge_id":sid,"length":len(v["stable_path"]),"selected":sok,"reason":sreason,
                          "live_status":sac_now[sid]["status"],"live_best":sac_now[sid].get("currentBestLength")})
        if sok: lines.append(f"{sid}: {json.dumps(list(v['stable_path']),separators=(',',':'))}")
    save(out/"selection.json",selection)
    (out/"submission_family_v2.txt").write_text("\n".join(lines)+("\n" if lines else ""))

    report={
        "experiment":"n-minus-1-family-procedure-transfer",
        "targets_attempted":len(attempts),
        "verified_ac":len(verified),
        "competitive_rows":len(lines),
        "elapsed_seconds":round(time.time()-t0,3),
        "solutions":[{
            "ac_id":cid,"ac_length":len(v["path"]),"ac_hash":v["verdict"]["certificate_hash"],
            "stable_id":v["stable_id"],"stable_length":len(v["stable_path"]),
            "stable_hash":v["stable_verdict"]["certificate_hash"],
            "predecessor_index":v["predecessor_index"],"prefix_step":v["prefix_step"],"nodes":v["nodes"]
        } for cid,v in sorted(verified.items())]
    }
    save(out/"report_family_v2.json",report)
    print("FINAL",json.dumps(report,sort_keys=True),flush=True)

if __name__=="__main__":
    main()
