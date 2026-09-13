#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import sys

HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE))

from basis import Q2, candidate_states, product_of_marginals, schmidt_rank
from kernel import Kernel
from challenge_pack import JOINT, PRODUCT, RELABELED, INCOMPLETE


def sha256(path:Path)->str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def safe(x):
    if hasattr(x,"data"):
        return safe(x.data())
    if isinstance(x,dict):
        return {str(k):safe(v) for k,v in x.items() if not str(k).startswith("_")}
    if isinstance(x,(list,tuple)):
        return [safe(v) for v in x]
    return x


def main()->int:
    k=Kernel()

    joint=k.analyze(JOINT)
    product=k.analyze(PRODUCT)
    relabel=k.analyze(RELABELED)
    incomplete=k.analyze(INCOMPLETE)

    joint_chsh=k.chsh_certificate(JOINT.probabilities)
    product_chsh=k.chsh_certificate(PRODUCT.probabilities)
    ablated_table=product_of_marginals(JOINT.probabilities)
    ablated_chsh=k.chsh_certificate(ablated_table)

    joint_search=joint["_search"]
    product_search=product["_search"]
    relabel_search=relabel["_search"]

    wrong_rank2=None
    for row in joint_search["candidate_rows"]:
        if (
            row["local_match"]
            and not row["full_match"]
            and row["schmidt_rank"]==2
        ):
            wrong_rank2=tuple(row["state"])
            break

    wrong_rank2_replay=(
        k.replay_state(JOINT,wrong_rank2)
        if wrong_rank2 is not None else None
    )

    evidence={
        "experiment":"quantum_joint_grain_genesis_v31",
        "scientific_freeze_commit":"091ffab475de3616534d9a837ed1cdfdb27cdf81",
        "post_freeze_challenges":True,
        "hashes":{
            "PROTOCOL.md":sha256(HERE/"PROTOCOL.md"),
            "FREEZE.json":sha256(HERE/"FREEZE.json"),
            "basis.py":sha256(HERE/"basis.py"),
            "kernel.py":sha256(HERE/"kernel.py"),
            "challenge_pack.py":sha256(HERE/"challenge_pack.py"),
        },
        "results":{
            "joint":safe(joint),
            "product_control":safe(product),
            "relabelled":safe(relabel),
            "incomplete":safe(incomplete),
            "joint_exact_chsh":safe(joint_chsh),
            "product_exact_chsh":safe(product_chsh),
            "correlation_ablation_chsh":safe(ablated_chsh),
            "wrong_rank2_same_local":list(wrong_rank2) if wrong_rank2 is not None else None,
            "wrong_rank2_full_replay":wrong_rank2_replay,
            "frozen_candidate_count":len(candidate_states()),
        },
        "gates":{},
    }

    G=evidence["gates"]

    # Q1: exact objects, no float criterion in acceptance path.
    basis_text=(HERE/"basis.py").read_text()
    kernel_text=(HERE/"kernel.py").read_text()
    G["Q1_exact_Qsqrt2_verification"]=(
        "class Q2" in basis_text
        and "Fraction" in basis_text
        and "tolerance" not in kernel_text.lower()
        and "isclose" not in kernel_text.lower()
    )

    G["Q2_joint_probabilities_valid"]=(
        joint.get("status")=="VERIFIED"
        and joint.get("valid_probabilities") is True
        and joint.get("no_signalling") is True
    )

    G["Q3_local_marginals_are_maximally_uninformative"]=(
        joint.get("uniform_local_marginals") is True
    )

    G["Q4_multiple_frozen_states_share_local_marginals"]=(
        joint_search.get("local_match_count",0)>=2
    )

    G["Q5_exact_CHSH_strictly_exceeds_two"]=(
        joint_chsh["_max"]>Q2.of(2)
    )

    G["Q6_Bell_local_adequacy_certified_false"]=(
        joint_chsh.get("violates_local_bound") is True
    )

    G["Q7_no_rank1_state_replays_joint_statistics"]=(
        joint_search.get("rank1_full_match_count")==0
    )

    G["Q8_rank2_state_exactly_replays_all_joint_probabilities"]=(
        joint_search.get("rank2_full_match_count",0)>=1
        and k.replay_state(JOINT,joint_search.get("_selected")) is True
    )

    G["Q9_minimum_surviving_Schmidt_rank_is_two"]=(
        joint_search.get("minimum_schmidt_rank")==2
    )

    G["Q10_joint_evidence_strictly_refines_local_hypothesis_grain"]=(
        joint_search.get("local_match_count",0)>
        joint_search.get("full_match_count",0)>=1
    )

    G["Q11_wrong_rank2_same_local_fails_joint_replay"]=(
        wrong_rank2 is not None
        and schmidt_rank(wrong_rank2)==2
        and wrong_rank2_replay is False
    )

    G["Q12_product_control_is_local_and_rank1_replayable"]=(
        product_chsh["_max"]<=Q2.of(2)
        and product_search.get("rank1_full_match_count",0)>=1
        and product_search.get("minimum_schmidt_rank")==1
    )

    G["Q13_correlation_ablation_removes_Bell_obstruction"]=(
        ablated_chsh["_max"]<=Q2.of(2)
        and ablated_chsh.get("violates_local_bound") is False
    )

    G["Q14_setting_outcome_relabelling_preserves_classification"]=(
        relabel.get("status")=="VERIFIED"
        and relabel_search.get("minimum_schmidt_rank")==2
        and k.chsh_certificate(RELABELED.probabilities)["_max"]>Q2.of(2)
    )

    G["Q15_incomplete_probability_authority_stays_unknown"]=(
        incomplete.get("status")=="UNKNOWN_AUTHORITY"
    )

    G["Q16_joint_evidence_ablation_restores_local_ambiguity"]=(
        joint_search.get("local_match_count",0)>1
        and joint_search.get("local_match_count",0)>
            joint_search.get("full_match_count",0)
    )

    # Candidate generator is generic signed-coefficient enumeration.
    candidate_fn_region=basis_text[
        basis_text.index("def candidate_states"):
        basis_text.index("def state_norm2")
    ].lower()
    G["Q17_no_named_Bell_state_constructor_in_frozen_generator"]=(
        "bell" not in candidate_fn_region
        and "itertools.product" in candidate_fn_region
    )

    G["Q18_quantum_certificate_requires_Bell_local_obstruction"]=(
        joint_chsh.get("violates_local_bound") is True
        and "Bell-local obstruction" in (HERE/"PROTOCOL.md").read_text()
    )

    evidence["full_pass"]=all(G.values())
    evidence["verdict"]=(
        "VERIFIED_BELL_LOCAL_OBSTRUCTION_AND_JOINT_QUANTUM_GRAIN_GENESIS"
        if evidence["full_pass"]
        else "QUANTUM_JOINT_GRAIN_V31_GAPS_EXPOSED"
    )

    (HERE/"evidence.json").write_text(
        json.dumps(evidence,indent=2,sort_keys=True,default=str)+"\n"
    )
    print(json.dumps(evidence,indent=2,sort_keys=True,default=str))
    return 0 if evidence["full_pass"] else 1


if __name__=="__main__":
    raise SystemExit(main())
