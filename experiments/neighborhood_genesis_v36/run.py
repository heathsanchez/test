from __future__ import annotations
import hashlib, json, math, re
from pathlib import Path

HERE=Path(__file__).resolve().parent
from kernel import Kernel
from challenge_pack import LATENT,EXPECTED_EDGES,WORLDS,RELABELLED,INCOMPLETE

SCIENTIFIC_FREEZE_COMMIT="52ce8f19cff4521755e836ea180cda124a886915"

def git_blob_sha(path: Path)->str:
    data=path.read_bytes()
    return hashlib.sha1(f"blob {len(data)}\0".encode()+data).hexdigest()

def choose(result):
    if result.get("status")!="VERIFIED":
        return None
    classes=tuple(result.get("canonical_graph_classes",()))
    return (
        int(result.get("minimum_edge_count",-1)),
        classes,
        int(result.get("canonical_class_count",-1)),
    )

def main()->int:
    freeze=json.loads((HERE/"FREEZE.json").read_text())
    observed={name:git_blob_sha(HERE/name) for name in freeze["scientific_core_paths"]}
    freeze_ok=observed==freeze["git_blob_sha"]

    k=Kernel()
    expected_class={name:k.canonical_graph(5,mask) for name,mask in LATENT.items()}
    results={}
    for name in LATENT:
        results[name]={}
        for v in range(3):
            results[name][str(v)]=k.synthesize(WORLDS[(name,v)])

    relabelled={name:k.synthesize(RELABELLED[name]) for name in LATENT}
    zero_only={name:k.synthesize(WORLDS[(name,0)],maximum_edges=0) for name in LATENT if name!="empty"}
    incomplete=k.synthesize(INCOMPLETE)
    nover=k.synthesize(WORLDS[("cycle5",0)],verification_enabled=False)

    G={}
    G["T1_frozen_scientific_core_byte_identical"]=freeze_ok

    G["T2_correct_minimum_edge_count_all_worlds"]=all(
        results[name][str(v)].get("status")=="VERIFIED"
        and results[name][str(v)].get("minimum_edge_count")==EXPECTED_EDGES[name]
        for name in LATENT for v in range(3)
    )

    G["T3_every_minimum_frontier_has_one_isomorphism_class"]=all(
        results[name][str(v)].get("canonical_class_count")==1
        for name in LATENT for v in range(3)
    )

    G["T4_no_neighborhood_control_retains_zero_edges"]=(
        results["empty"]["0"].get("minimum_edge_count")==0
        and results["empty"]["0"].get("canonical_graph_classes")==[expected_class["empty"]]
    )

    single=results["single"]["0"]
    G["T5_zero_edge_inadequacy_precedes_single_edge_genesis"]=(
        single.get("minimum_edge_count")==1
        and single.get("tested_by_edge_count",{}).get("0")==1
        and "0" in single.get("obstruction_by_edge_count",{})
    )

    matching=results["matching"]["0"]
    path2=results["path2"]["0"]
    G["T6_disconnected_and_connected_two_edge_topologies_are_distinguished"]=(
        matching.get("minimum_edge_count")==path2.get("minimum_edge_count")==2
        and matching.get("canonical_graph_classes")==[expected_class["matching"]]
        and path2.get("canonical_graph_classes")==[expected_class["path2"]]
        and expected_class["matching"]!=expected_class["path2"]
    )

    path3=results["path3"]["0"]
    G["T7_three_edge_path_exhausts_all_cheaper_graphs_first"]=(
        path3.get("minimum_edge_count")==3
        and all(path3.get("tested_by_edge_count",{}).get(str(e))==math.comb(10,e) for e in range(4))
        and all(str(e) in path3.get("obstruction_by_edge_count",{}) for e in range(3))
    )

    star=results["star"]["0"]
    G["T8_four_edge_star_is_unique_minimum_isomorphism_class"]=(
        star.get("minimum_edge_count")==4
        and star.get("canonical_graph_classes")==[expected_class["star"]]
        and star.get("canonical_class_count")==1
    )

    cycle=results["cycle5"]["0"]
    G["T9_five_cycle_requires_exhaustion_through_five_edges"]=(
        cycle.get("minimum_edge_count")==5
        and all(cycle.get("tested_by_edge_count",{}).get(str(e))==math.comb(10,e) for e in range(6))
        and all(str(e) in cycle.get("obstruction_by_edge_count",{}) for e in range(5))
    )

    G["T10_site_permutation_preserves_recovered_canonical_class"]=all(
        results[name][str(v)].get("canonical_graph_classes")==[expected_class[name]]
        for name in LATENT for v in range(3)
    )

    G["T11_consequence_label_relabelling_preserves_topology"]=all(
        relabelled[name].get("minimum_edge_count")==EXPECTED_EDGES[name]
        and relabelled[name].get("canonical_graph_classes")==[expected_class[name]]
        for name in LATENT
    )

    G["T12_rejected_cheaper_graphs_carry_explicit_obstruction_witnesses"]=all(
        any(
            w.get("kind") in {"MERGE_OBSTRUCTION","EXCESS_DISTINCTION"}
            for w in results[name]["0"].get("obstruction_by_edge_count",{}).values()
        )
        for name in LATENT if name!="empty"
    )

    G["T13_zero_edge_ablation_blocks_all_nontrivial_neighborhoods"]=all(
        r.get("status")=="CERTIFIED_NEIGHBORHOOD_INADEQUACY"
        and r.get("maximum_edges")==0
        for r in zero_only.values()
    )

    G["T14_incomplete_authority_stays_unknown"]=incomplete.get("status")=="UNKNOWN_AUTHORITY"
    G["T15_verifier_ablation_authorizes_no_graph_search"]=(
        nover.get("status")=="UNKNOWN_NO_VERIFIER" and nover.get("tested_graphs")==0
    )

    source=((HERE/"basis.py").read_text()+"\n"+(HERE/"kernel.py").read_text()).lower()
    hidden_names=("matching","path2","path3","star","cycle5","latent")
    G["T16_hidden_topology_families_absent_from_frozen_kernel"]=all(
        re.search(r"\b"+re.escape(tok)+r"\b",source) is None for tok in hidden_names
    )

    evidence={
        "experiment":"neighborhood_genesis_v36",
        "scientific_freeze_commit":SCIENTIFIC_FREEZE_COMMIT,
        "freeze_manifest":freeze,
        "observed_git_blob_sha":observed,
        "expected_canonical_classes":expected_class,
        "results":results,
        "relabelled_results":relabelled,
        "zero_edge_ablation":zero_only,
        "incomplete":incomplete,
        "no_verifier":nover,
        "gates":G,
    }
    evidence["full_pass"]=all(G.values())
    evidence["verdict"]=(
        "VERIFIED_MINIMUM_NEIGHBORHOOD_GENESIS_FROM_CONSEQUENCE_QUOTIENT"
        if evidence["full_pass"] else
        "NEIGHBORHOOD_GENESIS_V36_GAPS_EXPOSED"
    )
    (HERE/"evidence.json").write_text(json.dumps(evidence,indent=2,sort_keys=True,default=str)+"\n")
    print(json.dumps(evidence,indent=2,sort_keys=True,default=str))
    return 0 if evidence["full_pass"] else 1

if __name__=="__main__":
    raise SystemExit(main())
