#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import sys

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

from basis import JointSwap, is_joint_swap_symmetry
from kernel import Kernel
from challenge_pack import BASE, RELABELED, BROKEN, NO_GROWTH, HETEROGENEOUS_GROWTH, INCOMPLETE


def sha256(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def safe(x):
    if hasattr(x, "data"):
        return safe(x.data())
    if isinstance(x, dict):
        return {str(k): safe(v) for k, v in x.items() if not str(k).startswith("_")}
    if isinstance(x, (list, tuple)):
        return [safe(v) for v in x]
    return x


def main() -> int:
    k = Kernel()
    base = k.develop(BASE, enumerate_full_frontier=True)
    compiled = k.compile(BASE, base, provenance=("V21_BASE",))
    relabelled = k.develop(RELABELED, enumerate_full_frontier=True)
    no_growth = k.develop(NO_GROWTH, enumerate_full_frontier=True)
    ablated = k.develop(BASE, growth_enabled=False)
    wrong_swap = JointSwap((0,0),(0,1))
    wrong_swap_ok = is_joint_swap_symmetry(BASE, wrong_swap)
    broken_replay = k.replay_compiled(BROKEN, compiled)
    broken = k.develop(BROKEN, enumerate_full_frontier=False)
    hetero = k.develop(HETEROGENEOUS_GROWTH, enumerate_full_frontier=True)
    incomplete = k.develop(INCOMPLETE)
    no_consequence = k.develop(BASE, consequence_enabled=False)

    evidence = {
        "experiment":"residual_generated_transformation_language_v21",
        "scientific_freeze_commit":"d918d4ff6d3756058e391ce80884c57d9a3a56e8",
        "hashes":{
            "PROTOCOL.md":sha256(HERE/"PROTOCOL.md"),
            "FREEZE.json":sha256(HERE/"FREEZE.json"),
            "basis.py":sha256(HERE/"basis.py"),
            "kernel.py":sha256(HERE/"kernel.py"),
            "challenge_pack.py":sha256(HERE/"challenge_pack.py"),
        },
        "results":{
            "base":safe(base),
            "compiled":safe(compiled),
            "relabelled":safe(relabelled),
            "no_growth":safe(no_growth),
            "growth_ablation":safe(ablated),
            "wrong_swap":{"swap":wrong_swap.data(),"replay_ok":wrong_swap_ok},
            "broken_replay":safe(broken_replay),
            "broken":safe(broken),
            "heterogeneous":safe(hetero),
            "incomplete":safe(incomplete),
            "no_consequence":safe(no_consequence),
        },
        "gates":{},
    }
    G=evidence["gates"]

    G["L1_l0_exhausted_before_growth"] = (
        base.get("status")=="VERIFIED"
        and base.get("l0",{}).get("candidate_count")==14400
        and base.get("l0",{}).get("symmetry_count")==10
        and base.get("growth_authorized") is True
    )
    G["L2_certified_same_consequence_distinct_orbit_residual"] = (
        bool(base.get("residuals"))
        and base.get("initial_orbit_count",0)>base.get("final_orbit_count",0)
    )
    checks=base.get("generated_swap_checks",[])
    G["L3_generated_primitives_are_residual_earned"] = (
        bool(checks) and all(r.get("residual_earned") and r.get("replay_ok") for r in checks)
    )
    G["L4_generated_primitive_is_outside_l0"] = (
        bool(checks) and all(not r.get("representable_in_l0") for r in checks)
    )
    repair=base.get("repair_search",{})
    G["L5_exact_minimum_language_growth_and_frontier"] = (
        base.get("minimum_growth_count")==1
        and repair.get("lower_bound")==1
        and repair.get("frontier_enumeration")=="complete"
        and len(repair.get("frontier",[]))>1
        and len(base.get("generated_swaps",[]))==1
    )
    G["L6_final_orbits_equal_consequence_classes"] = (
        base.get("final_orbit_count")==2
        and sorted(len(o) for o in base.get("_final_orbits",()))==[10,15]
    )
    G["L7_exact_reconstruction"] = base.get("final_reconstruction",{}).get("exact") is True
    G["L8_language_growth_contracts_representation"] = (
        base.get("initial_orbit_count")==3 and base.get("final_orbit_count")==2
    )
    G["L9_relabelling_preserves_growth_signature"] = (
        relabelled.get("status")=="VERIFIED"
        and k.structural_signature(BASE,base)==k.structural_signature(RELABELED,relabelled)
    )
    G["L10_no_growth_when_l0_already_maximal"] = (
        no_growth.get("status")=="VERIFIED"
        and no_growth.get("growth_authorized") is False
        and no_growth.get("minimum_growth_count")==0
    )
    G["L11_growth_rule_ablation_stops_at_typed_residual"] = (
        ablated.get("status")=="CERTIFIED_TRANSFORMATION_LANGUAGE_RESIDUAL"
        and ablated.get("minimum_growth_count")==1
        and ablated.get("generated_swaps")==[]
    )
    G["L12_wrong_generated_primitive_rejected"] = (wrong_swap_ok is False)
    G["L13_consequence_perturbation_revokes_generated_transform"] = (
        broken_replay.get("status")=="REPLAY_FAILED"
        and broken_replay.get("failed_generated_swap_count",0)>0
        and broken.get("status")=="VERIFIED"
        and broken.get("final_reconstruction",{}).get("exact") is True
    )
    G["L14_heterogeneous_transfer"] = (
        hetero.get("status")=="VERIFIED"
        and hetero.get("growth_authorized") is True
        and hetero.get("minimum_growth_count",0)>=1
        and hetero.get("final_reconstruction",{}).get("exact") is True
        and k.structural_signature(HETEROGENEOUS_GROWTH,hetero)!=k.structural_signature(BASE,base)
    )
    G["L15_incomplete_authority_unknown"] = incomplete.get("status")=="UNKNOWN_AUTHORITY"
    G["L16_no_consequence_no_generated_transform"] = (
        no_consequence.get("status")=="UNKNOWN_NO_CONSEQUENCE_AUTHORITY"
        and no_consequence.get("generated_swaps")==[]
    )
    G["minimal_developmental_algorithm_respected"] = all(
        tok in (HERE/"PROTOCOL.md").read_text()
        for tok in ("EXECUTE","VERIFY","DIAGNOSE","CONSTRAIN","RESTRUCTURE","CHOOSE","COMPILE","UPDATE")
    )

    evidence["full_pass"]=all(G.values())
    evidence["verdict"]=(
        "VERIFIED_RESIDUAL_GENERATED_TRANSFORMATION_LANGUAGE_GROWTH_AND_QUOTIENT_CONTRACTION"
        if evidence["full_pass"]
        else "RESIDUAL_GENERATED_TRANSFORMATION_LANGUAGE_V21_GAPS_EXPOSED"
    )
    (HERE/"evidence.json").write_text(json.dumps(evidence,indent=2,sort_keys=True,default=str)+"\n")
    print(json.dumps(evidence,indent=2,sort_keys=True,default=str))
    return 0 if evidence["full_pass"] else 1

if __name__=="__main__":
    raise SystemExit(main())
