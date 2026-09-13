from __future__ import annotations
import hashlib, json, re
from collections import Counter
from pathlib import Path

HERE=Path(__file__).resolve().parent
from kernel import Kernel
from challenge_pack import (
    KINDS,EXPECTED_METRIC,WORLDS,RELABELLED,INCOMPLETE,
    S22,S4,IDENTITY2,SWAP2,FULL4,transform_candidate,
)

SCIENTIFIC_FREEZE_COMMIT="a4717eb21af5507e29e9d37ec406292b4d308d7a"

def git_blob_sha(path: Path)->str:
    data=path.read_bytes()
    return hashlib.sha1(f"blob {len(data)}\0".encode()+data).hexdigest()

def metric(result):
    row=result.get("minimum_metric")
    return None if row is None else tuple(int(x) for x in row)

def norm_candidate(row):
    kind=row["kind"]
    if kind in ("VOID","BAGS"):
        return (kind,)
    return (
        "SEGMENTS",
        tuple(tuple(int(v) for v in b) for b in row["before_segments"]),
        tuple(tuple(int(v) for v in b) for b in row["after_segments"]),
        tuple(tuple(int(v) for v in x) for x in row["matching"]),
    )

def frontier(result):
    return tuple(norm_candidate(x) for x in result.get("frontier",[]))

def expected_segment_candidate(sb,sa,m,variant):
    tsb,tsa,tm=transform_candidate(sb,sa,m,variant)
    return (
        "SEGMENTS",
        tuple(tuple(x) for x in tsb),
        tuple(tuple(x) for x in tsa),
        tuple(tuple(x) for x in tm),
    )

def expected_frontier(kind,variant):
    if kind=="constant":
        return (("VOID",),)
    if kind=="bags":
        return (("BAGS",),)
    if kind=="segmentation_only":
        return (expected_segment_candidate(S22,S22,(),variant),)
    if kind=="joint_passive":
        return tuple(sorted((
            expected_segment_candidate(S22,S22,IDENTITY2,variant),
            expected_segment_candidate(S22,S22,SWAP2,variant),
        ),key=repr))
    if kind=="joint_active":
        return (expected_segment_candidate(S22,S22,IDENTITY2,variant),)
    if kind=="full_persistence":
        return (expected_segment_candidate(S4,S4,FULL4,variant),)
    raise ValueError(kind)

def expected_test_counts(kernel,winning_metric):
    counts=Counter()
    for candidate in kernel.candidate_rows(4):
        m=kernel.metric(*candidate)
        if m<=winning_metric:
            counts[":".join(str(x) for x in m)]+=1
    return dict(counts)

def main()->int:
    freeze=json.loads((HERE/"FREEZE.json").read_text())
    observed={name:git_blob_sha(HERE/name) for name in freeze["scientific_core_paths"]}
    freeze_ok=observed==freeze["git_blob_sha"]

    k=Kernel()
    results={
        kind:{str(v):k.synthesize(WORLDS[(kind,v)]) for v in range(3)}
        for kind in KINDS
    }
    relabelled={kind:k.synthesize(RELABELLED[kind]) for kind in KINDS}

    cut_ablation={
        kind:k.synthesize(WORLDS[(kind,0)],maximum_cuts=0)
        for kind in KINDS
    }
    link_ablation={
        kind:k.synthesize(WORLDS[(kind,0)],maximum_links=0)
        for kind in KINDS
    }

    incomplete=k.synthesize(INCOMPLETE)
    nover=k.synthesize(WORLDS[("joint_active",0)],verification_enabled=False)

    G={}
    G["J1_frozen_scientific_core_byte_identical"]=freeze_ok

    G["J2_correct_minimum_metric_all_postfreeze_worlds"]=all(
        r.get("status")=="VERIFIED"
        and metric(r)==EXPECTED_METRIC[kind]
        for kind in KINDS
        for r in results[kind].values()
    )

    G["J3_constant_consequence_stops_at_void"]=(
        metric(results["constant"]["0"])==(0,0,0)
        and frontier(results["constant"]["0"])==(("VOID",),)
    )

    G["J4_frame_multiset_consequence_stops_at_bags_without_cuts"]=(
        metric(results["bags"]["0"])==(0,1,0)
        and frontier(results["bags"]["0"])==(("BAGS",),)
    )

    seg=results["segmentation_only"]["0"]
    G["J5_segmentation_only_exhausts_every_cheaper_metric_before_two_cuts"]=(
        metric(seg)==(1,2,0)
        and seg.get("tested_by_metric")==expected_test_counts(k,(1,2,0))
        and all(
            w.get("kind") in {"MERGE_OBSTRUCTION","EXCESS_DISTINCTION","INTERVENTION_OBSTRUCTION"}
            for w in seg.get("obstruction_by_metric",{}).values()
        )
    )

    G["J6_segmentation_only_frontier_is_unique_hidden_2_by_2_cut_pair"]=(
        seg.get("frontier_size")==1
        and frontier(seg)==expected_frontier("segmentation_only",0)
    )

    passive=results["joint_passive"]["0"]
    G["J7_passive_joint_world_earns_two_cuts_and_two_links"]=(
        metric(passive)==(1,2,2)
        and all(
            len(x[1])==2 and len(x[2])==2 and len(x[3])==2
            for x in frontier(passive)
        )
    )

    G["J8_passive_joint_world_preserves_exact_two_member_correspondence_frontier"]=(
        passive.get("frontier_size")==2
        and tuple(sorted(frontier(passive),key=repr))==expected_frontier("joint_passive",0)
    )

    active=results["joint_active"]["0"]
    G["J9_intervention_collapses_correspondence_without_extra_cuts_or_links"]=(
        metric(active)==(1,2,2)
        and active.get("frontier_size")==1
        and frontier(active)==expected_frontier("joint_active",0)
    )

    full=results["full_persistence"]["0"]
    G["J10_full_world_earns_six_cuts_four_links_after_exhausting_every_cheaper_metric"]=(
        metric(full)==(1,6,4)
        and full.get("frontier_size")==1
        and frontier(full)==expected_frontier("full_persistence",0)
        and full.get("tested_by_metric")==expected_test_counts(k,(1,6,4))
    )

    G["J11_independent_boundary_reversal_transforms_cuts_and_links_equivariantly"]=all(
        tuple(sorted(frontier(results[kind][str(v)]),key=repr))
        == tuple(sorted(expected_frontier(kind,v),key=repr))
        for kind in KINDS
        for v in range(3)
    )

    G["J12_consequence_label_relabelling_preserves_metric_and_frontier"]=all(
        metric(relabelled[kind])==EXPECTED_METRIC[kind]
        and tuple(sorted(frontier(relabelled[kind]),key=repr))
        == tuple(sorted(expected_frontier(kind,0),key=repr))
        for kind in KINDS
    )

    segmented_worlds=("segmentation_only","joint_passive","joint_active","full_persistence")
    G["J13_cut_ablation_preserves_nonsegmented_controls_and_blocks_segmented_worlds"]=(
        cut_ablation["constant"].get("status")=="VERIFIED"
        and metric(cut_ablation["constant"])==(0,0,0)
        and cut_ablation["bags"].get("status")=="VERIFIED"
        and metric(cut_ablation["bags"])==(0,1,0)
        and all(
            cut_ablation[kind].get("status")=="CERTIFIED_SEGMENTATION_PERSISTENCE_INADEQUACY"
            for kind in segmented_worlds
        )
    )

    persistence_worlds=("joint_passive","joint_active","full_persistence")
    G["J14_link_ablation_preserves_segmentation_only_and_blocks_persistence_worlds"]=(
        link_ablation["segmentation_only"].get("status")=="VERIFIED"
        and metric(link_ablation["segmentation_only"])==(1,2,0)
        and frontier(link_ablation["segmentation_only"])==expected_frontier("segmentation_only",0)
        and all(
            link_ablation[kind].get("status")=="CERTIFIED_SEGMENTATION_PERSISTENCE_INADEQUACY"
            for kind in persistence_worlds
        )
    )

    G["J15_incomplete_authority_and_verifier_ablation_authorize_no_growth"]=(
        incomplete.get("status")=="UNKNOWN_AUTHORITY"
        and nover.get("status")=="UNKNOWN_NO_VERIFIER"
        and nover.get("tested_candidates")==0
    )

    source=((HERE/"basis.py").read_text()+"\n"+(HERE/"kernel.py").read_text()).lower()
    forbidden=(
        "object","site","channel","graph","edge","relation",
        "segmentation_only","joint_passive","joint_active","full_persistence",
        "identity2","swap2","full4","hidden"
    )
    G["J16_named_objects_old_topologies_and_hidden_maps_absent_from_frozen_kernel"]=all(
        re.search(r"\b"+re.escape(tok)+r"\b",source) is None
        for tok in forbidden
    )

    evidence={
        "experiment":"joint_segmentation_persistence_genesis_v40",
        "scientific_freeze_commit":SCIENTIFIC_FREEZE_COMMIT,
        "freeze_manifest":freeze,
        "observed_git_blob_sha":observed,
        "results":results,
        "relabelled_results":relabelled,
        "cut_ablation":cut_ablation,
        "link_ablation":link_ablation,
        "incomplete":incomplete,
        "no_verifier":nover,
        "gates":G,
    }
    evidence["full_pass"]=all(G.values())
    evidence["verdict"]=(
        "VERIFIED_JOINT_LOCAL_SEGMENTATION_AND_CROSS_TIME_PERSISTENCE_GENESIS"
        if evidence["full_pass"] else
        "JOINT_SEGMENTATION_PERSISTENCE_V40_GAPS_EXPOSED"
    )
    (HERE/"evidence.json").write_text(json.dumps(evidence,indent=2,sort_keys=True,default=str)+"\n")
    print(json.dumps(evidence,indent=2,sort_keys=True,default=str))
    return 0 if evidence["full_pass"] else 1

if __name__=="__main__":
    raise SystemExit(main())
