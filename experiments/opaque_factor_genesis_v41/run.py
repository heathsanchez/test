from __future__ import annotations
import hashlib, json, re
from pathlib import Path

HERE=Path(__file__).resolve().parent
from kernel import Kernel
from challenge_pack import (
    KINDS,WORLDS,RELABELLED,INCOMPLETE,
    STATE_PERMS,HIDDEN_THREE,HIDDEN_TWO_BY_FOUR,
)

SCIENTIFIC_FREEZE_COMMIT="2ced9a3317583e433c5da08afa6a6df089c113f8"

def git_blob_sha(path:Path)->str:
    data=path.read_bytes()
    return hashlib.sha1(f"blob {len(data)}\0".encode()+data).hexdigest()

def norm_factorization(row):
    return tuple(
        tuple(tuple(int(x) for x in block) for block in part)
        for part in row
    )

def frontier(result):
    return tuple(norm_factorization(x) for x in result.get("frontier",[]))

def frontier_set(result):
    return set(frontier(result))

def transformed_set(kernel,rows,p):
    return {
        kernel.transform_factorization(f,tuple(int(x) for x in p))
        for f in rows
    }

def main()->int:
    freeze=json.loads((HERE/"FREEZE.json").read_text())
    observed={name:git_blob_sha(HERE/name) for name in freeze["scientific_core_paths"]}
    freeze_ok=observed==freeze["git_blob_sha"]

    k=Kernel()
    census={i:0 for i in (1,2,3)}
    for f in k.candidates():
        census[len(f)]+=1

    results={
        kind:{str(v):k.synthesize(WORLDS[(kind,v)]) for v in range(3)}
        for kind in KINDS
    }
    relabelled={kind:k.synthesize(RELABELLED[kind]) for kind in KINDS}

    one_factor_ablation={
        kind:k.synthesize(WORLDS[(kind,0)],maximum_factors=1)
        for kind in KINDS
    }
    two_factor_ablation={
        kind:k.synthesize(WORLDS[(kind,0)],maximum_factors=2)
        for kind in KINDS
    }

    incomplete=k.synthesize(INCOMPLETE)
    nover=k.synthesize(WORLDS[("three_target",0)],verification_enabled=False)

    G={}
    G["F1_frozen_scientific_core_byte_identical"]=freeze_ok

    G["F2_exhaustive_factorization_census_matches_frozen_bound"]=(
        census=={1:1,2:840,3:840}
    )

    one=results["one_target"]["0"]
    G["F3_one_target_evidence_stops_at_single_opaque_factor"]=(
        one.get("status")=="VERIFIED"
        and one.get("minimum_factor_count")==1
        and one.get("frontier_size")==1
        and one.get("tested_by_factor_count")=={"1":1}
    )

    two=results["two_target"]["0"]
    G["F4_two_target_evidence_rejects_atomic_state_and_earns_two_factors"]=(
        two.get("status")=="VERIFIED"
        and two.get("minimum_factor_count")==2
        and two.get("tested_by_factor_count")=={"1":1,"2":840}
    )

    G["F5_two_target_frontier_preserves_unresolved_factorizations"]=(
        two.get("frontier_size",0)>1
    )

    three=results["three_target"]["0"]
    G["F6_third_target_class_forces_three_factors"]=(
        three.get("status")=="VERIFIED"
        and three.get("minimum_factor_count")==3
        and three.get("tested_by_factor_count")=={"1":1,"2":840,"3":840}
    )

    G["F7_full_three_target_world_contracts_to_hidden_factor_partition"]=(
        three.get("frontier_size")==1
        and frontier_set(three)=={HIDDEN_THREE}
    )

    two4=results["two_by_four"]["0"]
    G["F8_independent_two_by_four_world_earns_two_factors_and_contains_hidden_factorization"]=(
        two4.get("status")=="VERIFIED"
        and two4.get("minimum_factor_count")==2
        and HIDDEN_TWO_BY_FOUR in frontier_set(two4)
    )

    equivariant=True
    for kind in KINDS:
        base=frontier_set(results[kind]["0"])
        for v,p in enumerate(STATE_PERMS):
            expected=transformed_set(k,base,p)
            if frontier_set(results[kind][str(v)])!=expected:
                equivariant=False
    G["F9_opaque_state_relabelling_transforms_frontier_equivariantly"]=equivariant

    G["F10_consequence_label_relabelling_preserves_minimum_and_frontier"]=all(
        relabelled[kind].get("minimum_factor_count")==results[kind]["0"].get("minimum_factor_count")
        and frontier_set(relabelled[kind])==frontier_set(results[kind]["0"])
        for kind in KINDS
    )

    G["F11_one_factor_ablation_preserves_one_target_and_blocks_multi_target_worlds"]=(
        one_factor_ablation["one_target"].get("status")=="VERIFIED"
        and one_factor_ablation["one_target"].get("minimum_factor_count")==1
        and all(
            one_factor_ablation[kind].get("status")=="CERTIFIED_FACTOR_LANGUAGE_INADEQUACY"
            for kind in ("two_target","three_target","two_by_four")
        )
    )

    G["F12_two_factor_ablation_preserves_two_target_worlds_and_blocks_three_target_world"]=(
        two_factor_ablation["two_target"].get("status")=="VERIFIED"
        and two_factor_ablation["two_target"].get("minimum_factor_count")==2
        and two_factor_ablation["two_by_four"].get("status")=="VERIFIED"
        and two_factor_ablation["two_by_four"].get("minimum_factor_count")==2
        and two_factor_ablation["three_target"].get("status")=="CERTIFIED_FACTOR_LANGUAGE_INADEQUACY"
    )

    two_rows={(r.state,r.action,r.after,r.consequence) for r in WORLDS[("two_target",0)].rows}
    three_prefix={
        (r.state,r.action,r.after,r.consequence)
        for r in WORLDS[("three_target",0)].rows
        if r.action<4
    }
    G["F13_removing_third_target_class_restores_broader_two_factor_frontier"]=(
        two_rows==three_prefix
        and two.get("minimum_factor_count")==2
        and three.get("minimum_factor_count")==3
        and two.get("frontier_size",0)>three.get("frontier_size",0)
    )

    G["F14_rejected_cheaper_factorizations_carry_explicit_obstructions"]=all(
        any(
            witness.get("kind") in {
                "INTERVENTION_NOT_FACTOR_LOCAL",
                "TARGET_CLASS_OBSTRUCTION",
            }
            for witness in result.get("obstruction_by_factor_count",{}).values()
        )
        for result in (two,three,two4)
    )

    G["F15_incomplete_authority_and_verifier_ablation_authorize_no_factor_growth"]=(
        incomplete.get("status")=="UNKNOWN_AUTHORITY"
        and nover.get("status")=="UNKNOWN_NO_VERIFIER"
        and nover.get("tested_factorizations")==0
    )

    source=((HERE/"basis.py").read_text()+"\n"+(HERE/"kernel.py").read_text()).lower()
    forbidden=(
        "bit","raw_position","site","channel","graph","edge",
        "one_target","two_target","three_target","two_by_four",
        "hidden_three","hidden_two_by_four"
    )
    G["F16_hidden_semantic_coordinates_and_old_topologies_absent_from_frozen_kernel"]=all(
        re.search(r"\b"+re.escape(tok)+r"\b",source) is None
        for tok in forbidden
    )

    evidence={
        "experiment":"opaque_factor_genesis_v41",
        "scientific_freeze_commit":SCIENTIFIC_FREEZE_COMMIT,
        "freeze_manifest":freeze,
        "observed_git_blob_sha":observed,
        "candidate_census":census,
        "results":results,
        "relabelled_results":relabelled,
        "one_factor_ablation":one_factor_ablation,
        "two_factor_ablation":two_factor_ablation,
        "incomplete":incomplete,
        "no_verifier":nover,
        "gates":G,
    }
    evidence["full_pass"]=all(G.values())
    evidence["verdict"]=(
        "VERIFIED_OPAQUE_STATE_SPACE_FACTOR_GENESIS_FROM_INTERVENTION_CONSEQUENCE"
        if evidence["full_pass"] else
        "OPAQUE_FACTOR_GENESIS_V41_GAPS_EXPOSED"
    )
    (HERE/"evidence.json").write_text(json.dumps(evidence,indent=2,sort_keys=True,default=str)+"\n")
    print(json.dumps(evidence,indent=2,sort_keys=True,default=str))
    return 0 if evidence["full_pass"] else 1

if __name__=="__main__":
    raise SystemExit(main())
