from __future__ import annotations
import hashlib, json, re
from itertools import product
from pathlib import Path

HERE=Path(__file__).resolve().parent
from kernel import Kernel
from challenge_pack import (
    KINDS,WORLDS,RELABELLED,INCOMPLETE,
    STATE_PERMS,transformed_expected,
)

SCIENTIFIC_FREEZE_COMMIT="2028f974258daae395d095ac6a57e57185360ce3"

def git_blob_sha(path:Path)->str:
    data=path.read_bytes()
    return hashlib.sha1(f"blob {len(data)}\0".encode()+data).hexdigest()

def norm_partition(row):
    return tuple(tuple(int(x) for x in block) for block in row)

def witnesses(result):
    out=[]
    for cls in result.get("class_witnesses",[]):
        out.append({
            "action_class":tuple(int(x) for x in cls["action_class"]),
            "minimum_block_count":int(cls["minimum_block_count"]),
            "frontier":tuple(norm_partition(p) for p in cls["frontier"]),
            "obstruction_by_block_count":cls.get("obstruction_by_block_count",{}),
        })
    return tuple(out)

def transform_partition(partition,p):
    return tuple(sorted(
        tuple(sorted(int(p[s]) for s in block))
        for block in partition
    ))

def common_refinement(parts,state_count=8):
    groups={}
    for state in range(state_count):
        key=[]
        for p in parts:
            idx=next(i for i,b in enumerate(p) if state in b)
            key.append(idx)
        groups.setdefault(tuple(key),[]).append(state)
    return tuple(sorted(tuple(v) for v in groups.values()))

def classify(parts,state_count=8):
    meet=common_refinement(parts,state_count)
    block_product=1
    for p in parts:
        block_product*=len(p)
    discrete=(len(meet)==state_count and all(len(cell)==1 for cell in meet))
    if discrete and block_product==state_count:
        return "COMPLEMENTARY"
    if discrete and block_product>state_count:
        return "CONSTRAINED"
    return "UNDERRESOLVED"

def combination_classes(result):
    ws=witnesses(result)
    if not ws:
        return {}
    counts={}
    for combo in product(*(w["frontier"] for w in ws)):
        label=classify(combo)
        counts[label]=counts.get(label,0)+1
    return counts

def frontier_signature(result):
    return tuple(
        (
            w["action_class"],
            w["minimum_block_count"],
            tuple(sorted(w["frontier"])),
        )
        for w in witnesses(result)
    )

def transformed_signature(result,p):
    rows=[]
    for w in witnesses(result):
        rows.append((
            w["action_class"],
            w["minimum_block_count"],
            tuple(sorted(transform_partition(part,p) for part in w["frontier"])),
        ))
    return tuple(rows)

def main()->int:
    freeze=json.loads((HERE/"FREEZE.json").read_text())
    observed={name:git_blob_sha(HERE/name) for name in freeze["scientific_core_paths"]}
    freeze_ok=observed==freeze["git_blob_sha"]

    k=Kernel()
    census=len(k.set_partitions(8))

    results={
        kind:{str(v):k.synthesize(WORLDS[(kind,v)]) for v in range(3)}
        for kind in KINDS
    }
    relabelled={kind:k.synthesize(RELABELLED[kind]) for kind in KINDS}

    one_block_ablation={
        kind:k.synthesize(WORLDS[(kind,0)],maximum_blocks_per_quotient=1)
        for kind in KINDS
    }
    two_block_ablation={
        kind:k.synthesize(WORLDS[(kind,0)],maximum_blocks_per_quotient=2)
        for kind in KINDS
    }

    incomplete=k.synthesize(INCOMPLETE)
    nover=k.synthesize(WORLDS[("three_class",0)],verification_enabled=False)

    one=results["one_class"]["0"]
    two=results["two_class"]["0"]
    three=results["three_class"]["0"]
    two4=results["two_by_four"]["0"]

    G={}
    G["Q1_frozen_scientific_core_byte_identical"]=freeze_ok
    G["Q2_exhaustive_equivalence_relation_census_is_bell8_4140"]=(census==4140)

    G["Q3_one_class_evidence_remains_undecomposed"]=(
        one.get("status")=="VERIFIED"
        and one.get("undecomposed") is True
        and one.get("quotient_class_count")==0
        and one.get("tested_partitions")==0
    )

    w2=witnesses(two)
    G["Q4_two_class_evidence_earns_one_minimum_quotient_family_per_class"]=(
        two.get("status")=="VERIFIED"
        and two.get("quotient_class_count")==2
        and len(w2)==2
        and all(w["minimum_block_count"]==2 for w in w2)
    )

    G["Q5_two_class_minimum_witness_frontiers_preserve_residual_ambiguity"]=(
        [len(w["frontier"]) for w in w2]==[2,2]
    )

    G["Q6_all_two_class_minimum_combinations_remain_underresolved"]=(
        combination_classes(two)=={"UNDERRESOLVED":4}
    )

    w3=witnesses(three)
    G["Q7_third_transformation_class_forces_three_unique_minimum_quotients"]=(
        three.get("status")=="VERIFIED"
        and three.get("quotient_class_count")==3
        and len(w3)==3
        and all(w["minimum_block_count"]==2 and len(w["frontier"])==1 for w in w3)
    )

    expected_three=set(transformed_expected("three_class",0))
    recovered_three={w["frontier"][0] for w in w3}
    G["Q8_three_unique_quotients_are_hidden_binary_quotients_and_complementary_posthoc"]=(
        recovered_three==expected_three
        and combination_classes(three)=={"COMPLEMENTARY":1}
        and sorted(w["minimum_block_count"] for w in w3)==[2,2,2]
    )

    w24=witnesses(two4)
    expected_two4=set(transformed_expected("two_by_four",0))
    recovered_two4={w["frontier"][0] for w in w24 if len(w["frontier"])==1}
    G["Q9_independent_two_by_four_world_recovers_unique_2_and_4_block_complementary_quotients"]=(
        two4.get("status")=="VERIFIED"
        and len(w24)==2
        and sorted(w["minimum_block_count"] for w in w24)==[2,4]
        and all(len(w["frontier"])==1 for w in w24)
        and recovered_two4==expected_two4
        and combination_classes(two4)=={"COMPLEMENTARY":1}
    )

    equivariant=True
    for kind in KINDS:
        base=results[kind]["0"]
        for v,p in enumerate(STATE_PERMS):
            current=results[kind][str(v)]
            if kind=="one_class":
                if frontier_signature(current)!=frontier_signature(base):
                    equivariant=False
            else:
                if frontier_signature(current)!=transformed_signature(base,p):
                    equivariant=False
    G["Q10_opaque_state_relabelling_transforms_quotient_frontiers_equivariantly"]=equivariant

    G["Q11_consequence_label_relabelling_preserves_quotient_frontiers"]=all(
        frontier_signature(relabelled[kind])==frontier_signature(results[kind]["0"])
        and relabelled[kind].get("quotient_class_count")==results[kind]["0"].get("quotient_class_count")
        and relabelled[kind].get("undecomposed")==results[kind]["0"].get("undecomposed")
        for kind in KINDS
    )

    G["Q12_one_block_ablation_preserves_undecomposed_control_and_blocks_all_multi_class_worlds"]=(
        one_block_ablation["one_class"].get("status")=="VERIFIED"
        and one_block_ablation["one_class"].get("undecomposed") is True
        and all(
            one_block_ablation[kind].get("status")=="CERTIFIED_QUOTIENT_LANGUAGE_INADEQUACY"
            for kind in ("two_class","three_class","two_by_four")
        )
    )

    G["Q13_two_block_ablation_preserves_binary_three_class_world_but_blocks_four_valued_quotient"]=(
        two_block_ablation["two_class"].get("status")=="VERIFIED"
        and two_block_ablation["three_class"].get("status")=="VERIFIED"
        and two_block_ablation["two_by_four"].get("status")=="CERTIFIED_QUOTIENT_LANGUAGE_INADEQUACY"
    )

    two_rows={(r.state,r.action,r.after,r.consequence) for r in WORLDS[("two_class",0)].rows}
    three_prefix={
        (r.state,r.action,r.after,r.consequence)
        for r in WORLDS[("three_class",0)].rows
        if r.action<4
    }
    G["Q14_removing_third_transformation_class_restores_broader_underresolved_frontier"]=(
        two_rows==three_prefix
        and combination_classes(two)=={"UNDERRESOLVED":4}
        and combination_classes(three)=={"COMPLEMENTARY":1}
        and sum(len(w["frontier"]) for w in w2)>sum(len(w["frontier"]) for w in w3[:2])
    )

    obstruction_ok=True
    for result in (two,three,two4):
        for w in witnesses(result):
            if not any(
                x.get("kind") in {"NOT_AN_INVARIANT_QUOTIENT","MOVE_SET_MISMATCH"}
                for x in w["obstruction_by_block_count"].values()
            ):
                obstruction_ok=False

    G["Q15_explicit_obstructions_unknown_authority_and_verifier_ablation_are_preserved"]=(
        obstruction_ok
        and incomplete.get("status")=="UNKNOWN_AUTHORITY"
        and nover.get("status")=="UNKNOWN_NO_VERIFIER"
        and nover.get("tested_partitions")==0
    )

    source=((HERE/"basis.py").read_text()+"\n"+(HERE/"kernel.py").read_text()).lower()
    forbidden=(
        "cartesian","product","factor","coordinate","bit",
        "graph","edge","site","channel",
        "one_class","two_class","three_class","two_by_four",
        "hidden"
    )
    G["Q16_cartesian_factor_and_hidden_challenge_language_absent_from_frozen_kernel"]=all(
        re.search(r"\b"+re.escape(tok)+r"\b",source) is None
        for tok in forbidden
    )

    evidence={
        "experiment":"transformation_quotient_genesis_v42",
        "scientific_freeze_commit":SCIENTIFIC_FREEZE_COMMIT,
        "freeze_manifest":freeze,
        "observed_git_blob_sha":observed,
        "partition_census":census,
        "results":results,
        "posthoc_combination_classes":{
            kind:combination_classes(results[kind]["0"]) for kind in KINDS
        },
        "relabelled_results":relabelled,
        "one_block_ablation":one_block_ablation,
        "two_block_ablation":two_block_ablation,
        "incomplete":incomplete,
        "no_verifier":nover,
        "gates":G,
    }
    evidence["full_pass"]=all(G.values())
    evidence["verdict"]=(
        "VERIFIED_TRANSFORMATION_QUOTIENT_GENESIS_WITH_DERIVED_COMPLEMENTARITY"
        if evidence["full_pass"] else
        "TRANSFORMATION_QUOTIENT_V42_GAPS_EXPOSED"
    )
    (HERE/"evidence.json").write_text(json.dumps(evidence,indent=2,sort_keys=True,default=str)+"\n")
    print(json.dumps(evidence,indent=2,sort_keys=True,default=str))
    return 0 if evidence["full_pass"] else 1

if __name__=="__main__":
    raise SystemExit(main())
