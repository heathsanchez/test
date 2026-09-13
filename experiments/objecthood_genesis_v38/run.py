from __future__ import annotations
import hashlib, json, re
from pathlib import Path

HERE=Path(__file__).resolve().parent
from kernel import Kernel
from challenge_pack import HIDDEN,EXPECTED_METRIC,WORLDS,RELABELLED,INCOMPLETE,N

SCIENTIFIC_FREEZE_COMMIT="5a25b0a385b63eccae0fe6761d46e8edce722269"

def git_blob_sha(path: Path)->str:
    data=path.read_bytes()
    return hashlib.sha1(f"blob {len(data)}\0".encode()+data).hexdigest()

def metric(result):
    row=result.get("minimum_metric")
    return None if row is None else tuple(int(x) for x in row)

def render_expected(kernel,name):
    kind,partition,structure=HIDDEN[name]
    if kind in ("VOID","BAG"):
        return {"kind":kind}
    cp,cs=kernel.canonical_object_structure(N,partition,structure)
    return {
        "kind":"OBJECTS",
        "partition":[list(b) for b in cp],
        "incidence":[[[int(v) for v in word] for word in unit] for unit in cs],
    }

def metric_key_parts(key):
    return tuple(int(x) for x in key.split(":"))

def main()->int:
    freeze=json.loads((HERE/"FREEZE.json").read_text())
    observed={name:git_blob_sha(HERE/name) for name in freeze["scientific_core_paths"]}
    freeze_ok=observed==freeze["git_blob_sha"]

    k=Kernel(max_arity=3,max_units=2)
    expected_class={name:render_expected(k,name) for name in HIDDEN}

    results={}
    for name in HIDDEN:
        results[name]={}
        for v in range(3):
            results[name][str(v)]=k.synthesize(WORLDS[(name,v)])

    relabelled={name:k.synthesize(RELABELLED[name]) for name in HIDDEN}

    zero_object={
        name:k.synthesize(WORLDS[(name,0)],max_objects=0)
        for name in HIDDEN
    }
    no_incidence={
        name:k.synthesize(WORLDS[(name,0)],max_units=0)
        for name in HIDDEN
    }

    incomplete=k.synthesize(INCOMPLETE)
    nover=k.synthesize(WORLDS[("four_cyclic_triple",0)],verification_enabled=False)

    G={}
    G["O1_frozen_scientific_core_byte_identical"]=freeze_ok

    G["O2_correct_minimum_metric_all_postfreeze_worlds"]=all(
        r.get("status")=="VERIFIED" and metric(r)==EXPECTED_METRIC[name]
        for name in HIDDEN
        for r in results[name].values()
    )

    G["O3_unique_minimum_canonical_object_incidence_class"]=all(
        r.get("canonical_class_count")==1
        and r.get("canonical_classes")==[expected_class[name]]
        for name in HIDDEN
        for r in results[name].values()
    )

    G["O4_constant_consequence_retains_void"]=(
        metric(results["constant"]["0"])==(0,0,0,0,0)
        and results["constant"]["0"].get("canonical_classes")==[{"kind":"VOID"}]
    )

    G["O5_global_multiset_stops_at_bag_without_inventing_object"]=(
        metric(results["bag"]["0"])==(0,1,0,0,0)
        and results["bag"]["0"].get("canonical_classes")==[{"kind":"BAG"}]
    )

    bal=results["balanced_objects"]["0"]
    unbal=results["unbalanced_objects"]["0"]
    G["O6_distinct_two_object_partition_shapes_are_recovered"]=(
        metric(bal)==metric(unbal)==(2,0,0,0,0)
        and bal.get("canonical_classes")==[expected_class["balanced_objects"]]
        and unbal.get("canonical_classes")==[expected_class["unbalanced_objects"]]
        and expected_class["balanced_objects"]!=expected_class["unbalanced_objects"]
    )

    three=results["three_objects"]["0"]
    expected_lower=2
    for partition in k.set_partitions(N):
        if len(partition)<3:
            expected_lower += len(k.candidate_incidence(len(partition),3,2))
    actual_lower=sum(
        int(count)
        for key,count in three.get("tested_by_metric",{}).items()
        if metric_key_parts(key)[0] < 3
    )
    G["O7_three_object_persistence_follows_exhaustion_of_all_lower_object_counts"]=(
        metric(three)==(3,0,1,1,1)
        and actual_lower==expected_lower
        and all(
            any(metric_key_parts(key)[0]==count for key in three.get("tested_by_metric",{}))
            for count in (0,1,2,3)
        )
    )

    ordered=results["four_ordered_triple"]["0"]
    G["O8_ordered_ternary_consequence_requires_four_objects_plus_ternary_incidence"]=(
        metric(ordered)==(4,0,1,3,1)
        and ordered.get("canonical_classes")==[expected_class["four_ordered_triple"]]
    )

    cyclic=results["four_cyclic_triple"]["0"]
    G["O9_cyclic_ternary_consequence_requires_three_word_coordinate_orbit"]=(
        metric(cyclic)==(4,0,1,3,3)
        and cyclic.get("canonical_classes")==[expected_class["four_cyclic_triple"]]
    )

    multi=results["four_two_pairs"]["0"]
    expected_one_unit=len(k.incidence_units(4,3))
    actual_one_unit=sum(
        int(count)
        for key,count in multi.get("tested_by_metric",{}).items()
        if metric_key_parts(key)[0]==4 and metric_key_parts(key)[2]==1
    )
    G["O10_two_incidence_world_rejects_entire_one_incidence_language"]=(
        metric(multi)==(4,0,2,4,2)
        and actual_one_unit==expected_one_unit
        and multi.get("canonical_classes")==[expected_class["four_two_pairs"]]
    )

    G["O11_recurrence_mark_relabelling_preserves_canonical_class"]=all(
        results[name][str(v)].get("canonical_classes")==[expected_class[name]]
        for name in HIDDEN for v in range(3)
    )

    G["O12_consequence_label_relabelling_preserves_metric_and_class"]=all(
        metric(relabelled[name])==EXPECTED_METRIC[name]
        and relabelled[name].get("canonical_classes")==[expected_class[name]]
        for name in HIDDEN
    )

    object_worlds=(
        "balanced_objects","unbalanced_objects","three_objects",
        "four_ordered_triple","four_cyclic_triple","four_two_pairs",
    )
    G["O13_zero_object_ablation_preserves_nonobject_controls_and_blocks_object_worlds"]=(
        zero_object["constant"].get("status")=="VERIFIED"
        and metric(zero_object["constant"])==(0,0,0,0,0)
        and zero_object["bag"].get("status")=="VERIFIED"
        and metric(zero_object["bag"])==(0,1,0,0,0)
        and all(
            zero_object[name].get("status")=="CERTIFIED_OBJECT_LANGUAGE_INADEQUACY"
            for name in object_worlds
        )
    )

    incidence_worlds=("three_objects","four_ordered_triple","four_cyclic_triple","four_two_pairs")
    G["O14_incidence_ablation_preserves_partition_only_worlds_and_blocks_incidence_worlds"]=(
        no_incidence["balanced_objects"].get("status")=="VERIFIED"
        and metric(no_incidence["balanced_objects"])==(2,0,0,0,0)
        and no_incidence["unbalanced_objects"].get("status")=="VERIFIED"
        and metric(no_incidence["unbalanced_objects"])==(2,0,0,0,0)
        and all(
            no_incidence[name].get("status")=="CERTIFIED_OBJECT_LANGUAGE_INADEQUACY"
            for name in incidence_worlds
        )
    )

    G["O15_incomplete_authority_and_verifier_ablation_authorize_no_object_growth"]=(
        incomplete.get("status")=="UNKNOWN_AUTHORITY"
        and nover.get("status")=="UNKNOWN_NO_VERIFIER"
        and nover.get("tested_candidates")==0
    )

    source=((HERE/"basis.py").read_text()+"\n"+(HERE/"kernel.py").read_text()).lower()
    forbidden=(
        "site","channel","graph","edge","hyperedge",
        "balanced_objects","unbalanced_objects","three_objects",
        "four_ordered_triple","four_cyclic_triple","four_two_pairs",
    )
    G["O16_named_roles_old_topologies_and_hidden_families_absent_from_frozen_kernel"]=all(
        re.search(r"\b"+re.escape(tok)+r"\b",source) is None
        for tok in forbidden
    )

    evidence={
        "experiment":"objecthood_genesis_v38",
        "scientific_freeze_commit":SCIENTIFIC_FREEZE_COMMIT,
        "freeze_manifest":freeze,
        "observed_git_blob_sha":observed,
        "expected_canonical_classes":expected_class,
        "results":results,
        "relabelled_results":relabelled,
        "zero_object_ablation":zero_object,
        "no_incidence_ablation":no_incidence,
        "incomplete":incomplete,
        "no_verifier":nover,
        "gates":G,
    }
    evidence["full_pass"]=all(G.values())
    evidence["verdict"]=(
        "VERIFIED_PERSISTENT_OBJECT_PARTITION_AND_ROLE_GENESIS_FROM_RECURRING_CONSEQUENCE"
        if evidence["full_pass"] else
        "OBJECTHOOD_GENESIS_V38_GAPS_EXPOSED"
    )

    (HERE/"evidence.json").write_text(json.dumps(evidence,indent=2,sort_keys=True,default=str)+"\n")
    print(json.dumps(evidence,indent=2,sort_keys=True,default=str))
    return 0 if evidence["full_pass"] else 1

if __name__=="__main__":
    raise SystemExit(main())
