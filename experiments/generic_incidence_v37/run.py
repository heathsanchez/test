from __future__ import annotations
import hashlib, json, re
from pathlib import Path

HERE=Path(__file__).resolve().parent
from kernel import Kernel
from challenge_pack import HIDDEN,EXPECTED_METRIC,WORLDS,RELABELLED,INCOMPLETE

SCIENTIFIC_FREEZE_COMMIT="eb8957a873858544ccc78bf1b33b2948444364c2"

def git_blob_sha(path: Path)->str:
    data=path.read_bytes()
    return hashlib.sha1(f"blob {len(data)}\0".encode()+data).hexdigest()

def normalize_structure(x):
    return tuple(tuple(tuple(int(v) for v in word) for word in unit) for unit in x)

def expected_class(kernel,name):
    return kernel.canonical_structure(4,HIDDEN[name])

def selected_class(result):
    rows=result.get("canonical_classes",[])
    if len(rows)!=1:
        return None
    return normalize_structure(rows[0])

def metric(result):
    m=result.get("minimum_metric")
    return None if m is None else tuple(int(x) for x in m)

def main()->int:
    freeze=json.loads((HERE/"FREEZE.json").read_text())
    observed={name:git_blob_sha(HERE/name) for name in freeze["scientific_core_paths"]}
    freeze_ok=observed==freeze["git_blob_sha"]

    k=Kernel(max_arity=3,max_units=2)
    results={}
    for name in HIDDEN:
        results[name]={}
        for v in range(3):
            results[name][str(v)]=k.synthesize(WORLDS[(name,v)])

    relabelled={name:k.synthesize(RELABELLED[name]) for name in HIDDEN}

    arity_ablation={
        name:k.synthesize(WORLDS[(name,0)],max_arity=2,max_units=2)
        for name in ("ordered_triple","cyclic_triple","symmetric_triple")
    }
    symmetry_ablation={
        name:k.synthesize(
            WORLDS[(name,0)],
            allow_nontrivial_coordinate_symmetry=False,
            max_units=2,
        )
        for name in ("symmetric_pair","cyclic_triple","symmetric_triple")
    }

    incomplete=k.synthesize(INCOMPLETE)
    nover=k.synthesize(WORLDS[("cyclic_triple",0)],verification_enabled=False)

    G={}
    G["I1_frozen_scientific_core_byte_identical"]=freeze_ok

    G["I2_correct_minimum_metric_all_postfreeze_worlds"]=all(
        r.get("status")=="VERIFIED" and metric(r)==EXPECTED_METRIC[name]
        for name in HIDDEN
        for r in results[name].values()
    )

    G["I3_unique_minimum_canonical_incidence_class_all_worlds"]=all(
        r.get("canonical_class_count")==1
        and selected_class(r)==expected_class(k,name)
        for name in HIDDEN
        for r in results[name].values()
    )

    z=results["zero"]["0"]
    G["I4_zero_unit_control_retains_no_incidence"]=(
        metric(z)==(0,0,0)
        and selected_class(z)==()
    )

    one=results["one_place"]["0"]
    G["I5_minimum_arity_one_is_earned_before_larger_arity"]=(
        metric(one)==(1,1,1)
        and one.get("tested_by_metric",{}).get("0:0:0")==1
        and set(one.get("tested_by_metric",{}))=={"0:0:0","1:1:1"}
    )

    p1=results["oriented_pair"]["0"]
    p2=results["symmetric_pair"]["0"]
    G["I6_distinct_arity_two_coordinate_orbits_compete_without_named_types"]=(
        metric(p1)==(1,2,1)
        and metric(p2)==(1,2,2)
        and selected_class(p1)!=selected_class(p2)
        and p2.get("tested_by_metric",{}).get("1:2:1")==12
    )

    t1=results["ordered_triple"]["0"]
    G["I7_minimum_arity_three_one_word_orbit_exhausts_all_lower_arity_first"]=(
        metric(t1)==(1,3,1)
        and t1.get("tested_by_metric",{}).get("1:1:1")==4
        and t1.get("tested_by_metric",{}).get("1:2:1")==12
        and t1.get("tested_by_metric",{}).get("1:2:2")==6
        and t1.get("tested_by_metric",{}).get("1:3:1")==24
    )

    tc=results["cyclic_triple"]["0"]
    G["I8_three_word_coordinate_orbit_is_selected_after_cheaper_triple_orbits_fail"]=(
        metric(tc)==(1,3,3)
        and tc.get("tested_by_metric",{}).get("1:3:1")==24
        and tc.get("tested_by_metric",{}).get("1:3:2")==36
        and tc.get("tested_by_metric",{}).get("1:3:3")==8
        and "1:3:2" in tc.get("obstruction_by_metric",{})
    )

    ts=results["symmetric_triple"]["0"]
    G["I9_full_coordinate_orbit_requires_exhaustion_of_all_smaller_orbits"]=(
        metric(ts)==(1,3,6)
        and ts.get("tested_by_metric",{}).get("1:3:1")==24
        and ts.get("tested_by_metric",{}).get("1:3:2")==36
        and ts.get("tested_by_metric",{}).get("1:3:3")==8
        and ts.get("tested_by_metric",{}).get("1:3:6")==4
    )

    multi=results["two_symmetric_pairs"]["0"]
    one_unit_tested=sum(
        int(v) for key,v in multi.get("tested_by_metric",{}).items()
        if key.startswith("1:")
    )
    G["I10_two_unit_world_rejects_entire_one_unit_language"]=(
        metric(multi)==(2,4,4)
        and one_unit_tested==94
        and selected_class(multi)==expected_class(k,"two_symmetric_pairs")
    )

    G["I11_site_relabelling_preserves_canonical_incidence_class"]=all(
        selected_class(results[name][str(v)])==expected_class(k,name)
        for name in HIDDEN for v in range(3)
    )

    G["I12_consequence_label_relabelling_preserves_metric_and_class"]=all(
        metric(relabelled[name])==EXPECTED_METRIC[name]
        and selected_class(relabelled[name])==expected_class(k,name)
        for name in HIDDEN
    )

    ao=arity_ablation["ordered_triple"]
    ac=arity_ablation["cyclic_triple"]
    ass=arity_ablation["symmetric_triple"]
    G["I13_arity_ablation_reveals_decomposition_cost_and_irreducible_residuals"]=(
        ao.get("status")=="VERIFIED"
        and metric(ao)==(2,3,2)
        and EXPECTED_METRIC["ordered_triple"] < metric(ao)
        and ac.get("status")=="CERTIFIED_INCIDENCE_LANGUAGE_INADEQUACY"
        and ass.get("status")=="CERTIFIED_INCIDENCE_LANGUAGE_INADEQUACY"
    )

    sp=symmetry_ablation["symmetric_pair"]
    cc=symmetry_ablation["cyclic_triple"]
    ss=symmetry_ablation["symmetric_triple"]
    G["I14_coordinate_symmetry_ablation_increases_cost_or_restores_inadequacy"]=(
        sp.get("status")=="VERIFIED"
        and metric(sp)==(2,2,2)
        and EXPECTED_METRIC["symmetric_pair"] < metric(sp)
        and cc.get("status")=="CERTIFIED_INCIDENCE_LANGUAGE_INADEQUACY"
        and ss.get("status")=="CERTIFIED_INCIDENCE_LANGUAGE_INADEQUACY"
    )

    G["I15_incomplete_authority_and_verifier_ablation_authorize_no_growth"]=(
        incomplete.get("status")=="UNKNOWN_AUTHORITY"
        and nover.get("status")=="UNKNOWN_NO_VERIFIER"
        and nover.get("tested_structures")==0
    )

    source=((HERE/"basis.py").read_text()+"\n"+(HERE/"kernel.py").read_text()).lower()
    forbidden=(
        "unary","directed","undirected","one_place","oriented_pair","symmetric_pair",
        "ordered_triple","cyclic_triple","symmetric_triple","two_symmetric_pairs",
        "graph","edge","hyperedge"
    )
    G["I16_named_relation_types_and_hidden_families_absent_from_frozen_kernel"]=all(
        re.search(r"\b"+re.escape(tok)+r"\b",source) is None
        for tok in forbidden
    )

    evidence={
        "experiment":"generic_incidence_genesis_v37",
        "scientific_freeze_commit":SCIENTIFIC_FREEZE_COMMIT,
        "freeze_manifest":freeze,
        "observed_git_blob_sha":observed,
        "results":results,
        "relabelled_results":relabelled,
        "arity_ablation":arity_ablation,
        "coordinate_symmetry_ablation":symmetry_ablation,
        "incomplete":incomplete,
        "no_verifier":nover,
        "gates":G,
    }
    evidence["full_pass"]=all(G.values())
    evidence["verdict"]=(
        "VERIFIED_GENERIC_INCIDENCE_ARITY_AND_COORDINATE_SYMMETRY_GENESIS"
        if evidence["full_pass"] else
        "GENERIC_INCIDENCE_V37_GAPS_EXPOSED"
    )
    (HERE/"evidence.json").write_text(json.dumps(evidence,indent=2,sort_keys=True,default=str)+"\n")
    print(json.dumps(evidence,indent=2,sort_keys=True,default=str))
    return 0 if evidence["full_pass"] else 1

if __name__=="__main__":
    raise SystemExit(main())
