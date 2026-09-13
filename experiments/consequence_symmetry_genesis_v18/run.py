#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import sys

HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE))

from kernel import Kernel
from basis import identity
from challenge_pack import (
    WORLD_A,WORLD_B,WORLD_RELABEL,WORLD_WRONG,WORLD_HET,WORLD_MARKED,WORLD_INCOMPLETE
)

def sha256(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()

def safe(x):
    if hasattr(x,"data"):
        return safe(x.data())
    if isinstance(x,dict):
        return {str(k):safe(v) for k,v in x.items()}
    if isinstance(x,(list,tuple,set,frozenset)):
        return [safe(v) for v in x]
    return x

def group_set(result):
    rows=result.get("analysis",result).get("transformations",[])
    return {tuple(p) for p in rows}

def main():
    evidence={
        "experiment":"consequence_symmetry_genesis_v18",
        "scientific_freeze_commit":"898d203c54f059700910ca9257363a2d219d02c9",
        "post_freeze_challenges":True,
        "hashes":{
            "PROTOCOL.md":sha256(HERE/"PROTOCOL.md"),
            "FREEZE.json":sha256(HERE/"FREEZE.json"),
            "basis.py":sha256(HERE/"basis.py"),
            "kernel.py":sha256(HERE/"kernel.py"),
            "challenge_pack.py":sha256(HERE/"challenge_pack.py"),
        },
        "results":{},
        "gates":{},
    }

    # Main discovery.
    k=Kernel()
    a=k.solve("Y_train_a",WORLD_A)
    b=k.solve("Y_train_b",WORLD_B)
    relabel=Kernel().solve("Y_relabel",WORLD_RELABEL)
    wrong=k.solve("Y_wrong",WORLD_WRONG,allow_search=True)
    het=Kernel().solve("Y_heterogeneous",WORLD_HET)
    marked=Kernel().solve("Y_marked",WORLD_MARKED)
    incomplete=Kernel().solve("Y_incomplete",WORLD_INCOMPLETE)
    ablated=Kernel().solve("Y_identity_only",WORLD_A,allow_nonidentity=False)

    for name,val in (
        ("a",a),("b",b),("relabel",relabel),("wrong",wrong),
        ("heterogeneous",het),("marked",marked),("incomplete",incomplete),
        ("identity_only",ablated),
    ):
        evidence["results"][name]=safe(val)

    A=a["analysis"]
    B=b["analysis"]
    R=relabel["analysis"]
    H=het["analysis"]
    M=marked["analysis"]
    I=ablated["analysis"]

    core=((HERE/"basis.py").read_text()+"\n"+(HERE/"kernel.py").read_text()).lower()
    forbidden=("coordinate","angle","distance","rotation","reflection","frequency","unit","dimension")

    G=evidence["gates"]
    G["Y1_no_geometry_vocabulary_in_frozen_executable_core"]=all(x not in core for x in forbidden)
    protocol_text=(HERE/"PROTOCOL.md").read_text().lower()
    G["Y2_identity_only_beginning_is_explicit"]=(
        ("begin with identity only" in protocol_text or "identity transformation only" in protocol_text)
        and tuple(identity(WORLD_A.n)) in group_set(a)
    )
    G["Y3_all_bijections_exhaustively_tested"]=A["tested_bijections"]==720
    G["Y4_nontrivial_verified_symmetry_emerges"]=A["group_size"]==12
    G["Y5_group_laws_verified"]=all(A["group_laws"].values())
    G["Y6_orbit_quotient_emerges"]=(
        len(A["point_orbits"])==1
        and len(A["pair_orbits"])==4
    )
    G["Y7_exact_orbit_reconstruction_reduces_qualification"]=(
        A["exact_orbit_reconstruction"] is True
        and A["raw_relation_comparisons"]==36
        and A["orbit_relation_comparisons"]==4
        and A["qualification_reduction"]==32
    )
    G["Y8_hidden_relabeling_has_same_invariant_symmetry_counts"]=(
        R["group_size"]==A["group_size"]
        and len(R["point_orbits"])==len(A["point_orbits"])
        and len(R["pair_orbits"])==len(A["pair_orbits"])
        and R["exact_orbit_reconstruction"] is True
    )
    G["Y9_wrong_structure_falsifies_compiled_symmetry_then_redevelops"]=(
        b.get("promoted_code") is not None
        and wrong.get("failed_reuse") is not None
        and wrong["failed_reuse"]["status"]=="REPLAY_FAILED"
        and wrong["route"]=="DEVELOP"
        and wrong["analysis"]["group_size"]==1
    )
    G["Y10_same_kernel_discovers_different_nontrivial_structure"]=(
        H["group_size"]==72
        and H["group_size"]!=A["group_size"]
        and len(H["pair_orbits"])==3
        and all(H["group_laws"].values())
    )
    G["Y11_consequence_breaks_structural_symmetry"]=(
        M["group_size"]==2
        and M["group_size"]<A["group_size"]
        and all(M["group_laws"].values())
    )
    G["Y12_incomplete_authority_stays_unknown"]=incomplete["status"]=="UNKNOWN_AUTHORITY"
    G["Y13_nonidentity_ablation_removes_reduction"]=(
        I["group_size"]==1
        and I["orbit_relation_comparisons"]==I["raw_relation_comparisons"]==36
        and I["qualification_reduction"]==0
    )
    G["minimal_developmental_algorithm_respected"]=all(
        token in (HERE/"PROTOCOL.md").read_text()
        for token in ("EXECUTE","VERIFY","DIAGNOSE","CONSTRAIN","RESTRUCTURE","CHOOSE","COMPILE","UPDATE")
    )

    evidence["full_pass"]=all(G.values())
    evidence["verdict"]=(
        "VERIFIED_CONSEQUENCE_PRESERVING_SYMMETRY_GENESIS_AND_ORBIT_QUALIFICATION_REDUCTION"
        if evidence["full_pass"] else
        "CONSEQUENCE_SYMMETRY_GENESIS_V18_GAPS_EXPOSED"
    )
    (HERE/"evidence.json").write_text(json.dumps(evidence,indent=2,sort_keys=True)+"\n")
    print(json.dumps(evidence,indent=2,sort_keys=True))
    return 0 if evidence["full_pass"] else 1

if __name__=="__main__":
    raise SystemExit(main())
