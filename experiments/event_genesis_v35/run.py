from __future__ import annotations
import hashlib, json, re
from itertools import product
from pathlib import Path

HERE=Path(__file__).resolve().parent
from basis import View
from kernel import Kernel
from challenge_pack import AXES,VARIANTS,RELABELLED,INCOMPLETE

SCIENTIFIC_FREEZE_COMMIT="7545d4e5d5b5130f26bff8e6aa7e2f92d27f02b9"

def git_blob_sha(path: Path)->str:
    data=path.read_bytes()
    return hashlib.sha1(f"blob {len(data)}\0".encode()+data).hexdigest()

def safe(x):
    if hasattr(x,"data"): return safe(x.data())
    if isinstance(x,dict): return {str(k):safe(v) for k,v in x.items() if not str(k).startswith("_")}
    if isinstance(x,(list,tuple)): return [safe(v) for v in x]
    return x

def graph_shape(result):
    states=result["machine"]["states"]
    root=int(result["machine"]["root"])
    memo={}
    def rec(s):
        if s in memo: return memo[s]
        row=states[s]
        if row[0]=="OUT":
            ans=("OUT",)
        else:
            ans=("STEP",tuple((int(sym),rec(int(ch))) for sym,ch in row[1]))
        memo[s]=ans
        return ans
    return rec(root)

def view_set(result):
    return {
        (tuple(v["motif"]),int(v["width"]))
        for v in result.get("frontier_views",[])
    }

def best_restricted_width(world,width:int):
    k=Kernel()
    labels={int(r.consequence) for r in world.rows}
    n=len(world.rows[0].boundary)
    scored=[]
    for m in range(2,min(k.max_motif_len,n-1)+1):
        rem=n-m
        if rem%width: continue
        for motif in product((0,1),repeat=m):
            view=View(tuple(int(x) for x in motif),int(width))
            pairs=[]
            ok=True
            for r in world.rows:
                seq=k._parse(tuple(r.boundary),view)
                if seq is None:
                    ok=False
                    break
                pairs.append((seq,int(r.consequence)))
            if not ok: continue
            machine=k._build_machine(pairs)
            if machine is None: continue
            bits=k._description_bits(view,machine,len(labels))
            stats=k._machine_stats(machine)
            scored.append((bits,stats["state_count"],stats["transition_count"],view))
    if not scored: return None
    scored.sort(key=lambda x:(x[0],x[1],x[2],len(x[3].motif),x[3].motif))
    bits,states,trans,view=scored[0]
    return {
        "description_bits":int(bits),
        "state_count":int(states),
        "transition_count":int(trans),
        "view":{"motif":list(view.motif),"width":int(view.width)},
    }

def main()->int:
    freeze=json.loads((HERE/"FREEZE.json").read_text())
    observed={name:git_blob_sha(HERE/name) for name in freeze["scientific_core_paths"]}
    frozen_ok=observed==freeze["git_blob_sha"]

    raw={}
    results={}
    for variant,cases in VARIANTS.items():
        k=Kernel()
        rr={}
        for case in cases:
            r=k.solve(case.world)
            raw[(variant,case.axis)]=r
            rr[case.axis]=safe(r)
        results[str(variant)]=rr

    rel={}
    for case in RELABELLED:
        r=Kernel().solve(case.world)
        raw[("rel",case.axis)]=r
        rel[case.axis]=safe(r)

    incomplete=Kernel().solve(INCOMPLETE)
    no_verifier=Kernel().solve(VARIANTS[0][3].world,verification_enabled=False)

    width1={}
    for axis in ("xor","pair4","triple8","conditional"):
        case=next(c for c in VARIANTS[0] if c.axis==axis)
        width1[axis]=best_restricted_width(case.world,1)

    evidence={
        "experiment":"consequence_selected_eventization_v35",
        "scientific_freeze_commit":SCIENTIFIC_FREEZE_COMMIT,
        "freeze_manifest":freeze,
        "observed_git_blob_sha":observed,
        "results":results,
        "relabelled_results":rel,
        "width1_ablations":width1,
        "incomplete":safe(incomplete),
        "no_verifier":safe(no_verifier),
        "gates":{},
    }
    G=evidence["gates"]
    G["E1_frozen_scientific_core_byte_identical"]=frozen_ok
    G["E2_all_hidden_worlds_replay_exactly"]=all(
        r.get("status")=="VERIFIED" and r.get("exact_replay") is True
        for key,r in raw.items() if key[0]!="rel"
    )

    const=raw[(0,"constant")]
    G["E3_constant_consequence_requires_no_eventization"]=(
        const.get("status")=="VERIFIED"
        and const.get("selected_view") is None
        and const.get("description_bits")==1
    )

    first=raw[(0,"first")]
    G["E4_asymmetric_consequence_earns_unique_orientation"]=(
        first.get("frontier_size")==1
        and first.get("selected_view") is not None
        and len(first["selected_view"]["motif"])>=2
    )

    parity=raw[(0,"parity")]
    pviews=view_set(parity)
    G["E5_symmetric_consequence_preserves_opposite_orientations"]=(
        parity.get("frontier_size",0)>=2
        and any((tuple(reversed(m)),w) in pviews and tuple(reversed(m))!=m for m,w in pviews)
    )

    widths={
        int(r["selected_view"]["width"])
        for key,r in raw.items()
        if key[0]!="rel" and r.get("selected_view") is not None
    }
    G["E6_consequence_selects_at_least_three_distinct_event_widths"]=len(widths)>=3

    relational=("xor","pair4","triple8")
    G["E7_relational_eventization_beats_raw_bit_segmentation"]=any(
        raw[(0,a)]["selected_view"]["width"]>1
        and width1[a] is not None
        and raw[(0,a)]["description_bits"] < width1[a]["description_bits"]
        for a in relational
    )

    pair=raw[(0,"pair4")]
    G["E8_four_class_relation_has_four_consequence_terminals"]=(
        pair.get("terminal_count")==4 and pair.get("exact_replay") is True
    )

    triple=raw[(0,"triple8")]
    G["E9_eight_class_relation_has_eight_consequence_terminals"]=(
        triple.get("terminal_count")==8 and triple.get("exact_replay") is True
    )

    cond=raw[(0,"conditional")]
    G["E10_conditional_world_has_nontrivial_selected_eventization"]=(
        cond.get("status")=="VERIFIED"
        and cond.get("selected_view") is not None
        and cond.get("step_count",0)>0
        and cond.get("state_count",0)>2
    )

    changed=0
    for axis in AXES:
        a=raw[(0,axis)].get("selected_view")
        b=raw[(1,axis)].get("selected_view")
        c=raw[(2,axis)].get("selected_view")
        sig=lambda v: None if v is None else (tuple(v["motif"]),int(v["width"]))
        if len({sig(a),sig(b),sig(c)})>1:
            changed+=1
    G["E11_latent_source_permutation_changes_multiple_selected_eventizations"]=changed>=3

    G["E12_complete_dihedral_presentation_authority_is_enforced"]=all(
        Kernel().authority(case.world) is None
        for cases in VARIANTS.values() for case in cases
    )

    G["E13_label_relabelling_preserves_view_frontier_and_machine_shape"]=all(
        view_set(raw[(0,axis)])==view_set(raw[("rel",axis)])
        and graph_shape(raw[(0,axis)])==graph_shape(raw[("rel",axis)])
        for axis in AXES
    )

    G["E14_incomplete_dihedral_authority_stays_unknown"]=(
        incomplete.get("status") in {"UNKNOWN_AUTHORITY","UNKNOWN_DIHEDRAL_AUTHORITY"}
    )

    G["E15_verifier_ablation_authorizes_no_eventization_search"]=(
        no_verifier.get("status")=="UNKNOWN_NO_VERIFIER"
        and no_verifier.get("candidate_views_tested")==0
    )

    source=((HERE/"basis.py").read_text()+"\n"+(HERE/"kernel.py").read_text()).lower()
    forbidden=(
        "constant","parity","xor","pair4","triple8","conditional","distant",
        "x0","x1","x2","x3","x4","x5",
        "(1,1,1,0,0,0)"
    )
    G["E16_hidden_axes_sources_and_anchor_are_absent_from_frozen_kernel"]=all(
        tok not in source for tok in forbidden
    )

    evidence["selected_widths"]=sorted(widths)
    evidence["permutation_changed_task_count"]=changed
    evidence["full_pass"]=all(G.values())
    evidence["verdict"]=(
        "VERIFIED_CONSEQUENCE_SELECTED_EVENTIZATION_ORIGIN_DIRECTION_AND_GRAIN_GENESIS"
        if evidence["full_pass"] else
        "EVENT_GENESIS_V35_GAPS_EXPOSED"
    )
    (HERE/"evidence.json").write_text(json.dumps(evidence,indent=2,sort_keys=True,default=str)+"\n")
    print(json.dumps(evidence,indent=2,sort_keys=True,default=str))
    return 0 if evidence["full_pass"] else 1

if __name__=="__main__":
    raise SystemExit(main())
