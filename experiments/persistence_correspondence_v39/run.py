from __future__ import annotations
import hashlib, json, re
from pathlib import Path

HERE=Path(__file__).resolve().parent
from kernel import Kernel
from challenge_pack import BASE,PASSIVE,ACTIVE_TWO,RELABELLED,INCOMPLETE,mapped

SCIENTIFIC_FREEZE_COMMIT="1d939fe83a7351ec04ec8f96971f1bcc30a89155"

def git_blob_sha(path: Path)->str:
    data=path.read_bytes()
    return hashlib.sha1(f"blob {len(data)}\0".encode()+data).hexdigest()

def frontier(result):
    return tuple(
        tuple(tuple(int(v) for v in pair) for pair in matching)
        for matching in result.get("frontier",[])
    )

def canon(result):
    return tuple(
        tuple(tuple(int(v) for v in pair) for pair in matching)
        for matching in result.get("canonical_classes",[])
    )

def main()->int:
    freeze=json.loads((HERE/"FREEZE.json").read_text())
    observed={name:git_blob_sha(HERE/name) for name in freeze["scientific_core_paths"]}
    freeze_ok=observed==freeze["git_blob_sha"]

    k=Kernel()
    passive={
        name:{str(v):k.synthesize(PASSIVE[(name,v)]) for v in range(3)}
        for name in BASE
    }
    active={str(v):k.synthesize(ACTIVE_TWO[v]) for v in range(3)}
    relabelled={
        name:k.synthesize(world)
        for name,world in RELABELLED.items()
    }
    zero_ablation={
        name:k.synthesize(PASSIVE[(name,0)],maximum_links=0)
        for name in BASE
    }
    active_zero=k.synthesize(ACTIVE_TWO[0],maximum_links=0)
    incomplete=k.synthesize(INCOMPLETE)
    nover=k.synthesize(ACTIVE_TWO[0],verification_enabled=False)

    G={}
    G["P1_frozen_scientific_core_byte_identical"]=freeze_ok

    no0=passive["no_persistence"]["0"]
    G["P2_zero_persistence_stops_at_zero_links"]=(
        no0.get("status")=="VERIFIED"
        and no0.get("minimum_link_count")==0
        and frontier(no0)==((),)
    )

    one0=passive["one_link"]["0"]
    G["P3_one_link_exhausts_bag_baseline_before_correspondence"]=(
        one0.get("status")=="VERIFIED"
        and one0.get("minimum_link_count")==1
        and one0.get("tested_by_link_count",{}).get("0")==1
        and frontier(one0)==(BASE["one_link"],)
    )

    two0=passive["two_link"]["0"]
    two_front=frontier(two0)
    G["P4_passive_two_link_world_preserves_two_member_minimum_frontier"]=(
        two0.get("status")=="VERIFIED"
        and two0.get("minimum_link_count")==2
        and two0.get("frontier_size")==2
        and BASE["two_link"] in two_front
    )

    G["P5_passive_two_witnesses_are_distinct_labelled_maps_but_one_abstract_class"]=(
        len(set(two_front))==2
        and two0.get("canonical_class_count")==1
        and len(canon(two0))==1
    )

    act0=active["0"]
    G["P6_intervention_response_evidence_collapses_to_hidden_correspondence"]=(
        act0.get("status")=="VERIFIED"
        and act0.get("frontier_size")==1
        and frontier(act0)==(BASE["two_link"],)
    )

    G["P7_active_two_link_world_does_not_invent_third_identity"]=(
        act0.get("minimum_link_count")==2
    )

    full0=passive["full_link"]["0"]
    G["P8_full_persistence_requires_three_links"]=(
        full0.get("status")=="VERIFIED"
        and full0.get("minimum_link_count")==3
        and frontier(full0)==(BASE["full_link"],)
    )

    G["P9_full_persistence_exhausts_every_cheaper_matching_count"]=(
        full0.get("tested_by_link_count",{}).get("0")==1
        and full0.get("tested_by_link_count",{}).get("1")==9
        and full0.get("tested_by_link_count",{}).get("2")==18
        and full0.get("tested_by_link_count",{}).get("3")==6
        and all(str(i) in full0.get("obstruction_by_link_count",{}) for i in (0,1,2))
    )

    equivariant=True
    for v in range(3):
        if frontier(passive["one_link"][str(v)])!=(mapped("one_link",v),):
            equivariant=False
        if frontier(active[str(v)])!=(mapped("two_link",v),):
            equivariant=False
        if frontier(passive["full_link"][str(v)])!=(mapped("full_link",v),):
            equivariant=False
        expected_passive={
            Kernel.map_matching(m, 
                __import__("challenge_pack").BEFORE_PERMS[v],
                __import__("challenge_pack").AFTER_PERMS[v])
            for m in two_front
        }
        if set(frontier(passive["two_link"][str(v)]))!=expected_passive:
            equivariant=False
    G["P10_independent_frame_permutations_transform_recovered_maps_equivariantly"]=equivariant

    G["P11_consequence_label_relabelling_preserves_link_count_and_frontier"]=(
        relabelled["no_persistence"].get("minimum_link_count")==0
        and frontier(relabelled["no_persistence"])==frontier(passive["no_persistence"]["0"])
        and relabelled["one_link"].get("minimum_link_count")==1
        and frontier(relabelled["one_link"])==frontier(passive["one_link"]["0"])
        and relabelled["two_link_passive"].get("minimum_link_count")==2
        and set(frontier(relabelled["two_link_passive"]))==set(two_front)
        and relabelled["two_link_active"].get("minimum_link_count")==2
        and frontier(relabelled["two_link_active"])==(BASE["two_link"],)
        and relabelled["full_link"].get("minimum_link_count")==3
        and frontier(relabelled["full_link"])==(BASE["full_link"],)
    )

    persistence_worlds=("one_link","two_link","full_link")
    G["P12_zero_link_ablation_preserves_no_persistence_and_blocks_persistence_worlds"]=(
        zero_ablation["no_persistence"].get("status")=="VERIFIED"
        and zero_ablation["no_persistence"].get("minimum_link_count")==0
        and all(
            zero_ablation[name].get("status")=="CERTIFIED_CORRESPONDENCE_INADEQUACY"
            for name in persistence_worlds
        )
        and active_zero.get("status")=="CERTIFIED_CORRESPONDENCE_INADEQUACY"
    )

    G["P13_removing_intervention_restores_passive_nonidentifiability"]=(
        passive["two_link"]["0"].get("frontier_size")==2
        and active["0"].get("frontier_size")==1
        and active["0"].get("minimum_link_count")==passive["two_link"]["0"].get("minimum_link_count")==2
    )

    G["P14_rejected_cheaper_matchings_carry_explicit_obstruction_witnesses"]=all(
        any(
            w.get("kind") in {"MERGE_OBSTRUCTION","EXCESS_DISTINCTION"}
            for w in result.get("obstruction_by_link_count",{}).values()
        )
        for result in (one0,two0,act0,full0)
    )

    G["P15_incomplete_authority_and_verifier_ablation_authorize_no_correspondence_growth"]=(
        incomplete.get("status")=="UNKNOWN_AUTHORITY"
        and nover.get("status")=="UNKNOWN_NO_VERIFIER"
        and nover.get("tested_matchings")==0
    )

    source=((HERE/"basis.py").read_text()+"\n"+(HERE/"kernel.py").read_text()).lower()
    forbidden=(
        "object","site","graph","edge","relation",
        "no_persistence","one_link","two_link","full_link",
        "hidden_map","identity_map"
    )
    G["P16_named_objects_old_topologies_and_hidden_maps_absent_from_frozen_kernel"]=all(
        re.search(r"\b"+re.escape(tok)+r"\b",source) is None
        for tok in forbidden
    )

    evidence={
        "experiment":"persistence_correspondence_genesis_v39",
        "scientific_freeze_commit":SCIENTIFIC_FREEZE_COMMIT,
        "freeze_manifest":freeze,
        "observed_git_blob_sha":observed,
        "passive_results":passive,
        "active_two_link_results":active,
        "relabelled_results":relabelled,
        "zero_link_ablation":zero_ablation,
        "active_zero_link_ablation":active_zero,
        "incomplete":incomplete,
        "no_verifier":nover,
        "gates":G,
    }
    evidence["full_pass"]=all(G.values())
    evidence["verdict"]=(
        "VERIFIED_PERSISTENCE_CORRESPONDENCE_GENESIS_AND_INTERVENTIONAL_DISAMBIGUATION"
        if evidence["full_pass"] else
        "PERSISTENCE_CORRESPONDENCE_V39_GAPS_EXPOSED"
    )
    (HERE/"evidence.json").write_text(json.dumps(evidence,indent=2,sort_keys=True,default=str)+"\n")
    print(json.dumps(evidence,indent=2,sort_keys=True,default=str))
    return 0 if evidence["full_pass"] else 1

if __name__=="__main__":
    raise SystemExit(main())
