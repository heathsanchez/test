#!/usr/bin/env python3
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parent
PRIOR=ROOT/"prior"
OUT=ROOT/"results"

EXPECTED={
    "v26":"VERIFIED_DOC_UPGRADE_AUDIT_V26",
    "v27":"VERIFIED_PROSPECTIVE_RETAINED_RELATIONAL_CAPABILITY_TRANSFER",
    "v28":"VERIFIED_CAUSAL_COMPOUNDING_OF_RETAINED_RELATIONAL_CAPABILITY",
    "v29":"VERIFIED_BOUNDED_CHANGE_LANGUAGE_GROWTH_CHAIN",
    "v30":"VERIFIED_OUTER_EDIT_OPERATION_GENESIS_FROM_ANONYMOUS_TRANSDUCER_SUBSTRATE",
}

def jsons(name):
    files=list((PRIOR/name).rglob("*.json"))
    out=[]
    for p in files:
        try:
            out.append((p,json.loads(p.read_text())))
        except Exception:
            pass
    return out

def verdict_of(x):
    return x.get("final_verdict") or x.get("verdict")

def find_verdict(name, expected):
    matches=[]
    for p,x in jsons(name):
        if verdict_of(x)==expected:
            matches.append((p,x))
    if len(matches)!=1:
        raise RuntimeError(f"{name}: expected exactly one {expected}, found {len(matches)}")
    return matches[0]

def all_bool_gates(x):
    g=x.get("gates")
    if not isinstance(g,dict) or not g:
        return None
    vals=[]
    for v in g.values():
        if isinstance(v,bool): vals.append(v)
        elif isinstance(v,str) and v=="PASS": vals.append(True)
        else: vals.append(bool(v))
    return all(vals)

def main():
    OUT.mkdir(exist_ok=True)
    rows={}
    gates={}

    found={}
    for name,expected in EXPECTED.items():
        p,x=find_verdict(name,expected)
        found[name]=x
        rows[name]={
            "path":str(p.relative_to(ROOT)),
            "verdict":expected,
            "claim_boundary":x.get("claim_boundary"),
        }
        gates[f"{name}_verdict_exact"]=True

    # V26: exact theorem/controller authority.
    v26=found["v26"]
    gates["v26_claim_boundary_preserved"] = "unrestricted action-language invention remains open" in json.dumps(v26).lower()

    # V27 prospective no-search/no-development kernel transfer.
    v27=found["v27"]
    g27=v27.get("gates",{})
    gates["v27_all_source_positive"]=g27.get("all_source_positive") is True
    gates["v27_all_source_negative"]=g27.get("all_source_negative") is True
    gates["v27_zero_representation_search"]=g27.get("zero_representation_search") is True
    gates["v27_zero_development_transitions"]=g27.get("zero_development_transitions") is True
    gates["v27_hex_kernel_pass"]=g27.get("hex_kernel_check")=="PASS"
    files27=v27.get("generated_lean_sha256",{})
    gates["v27_six_sealed_lean_obligations"]=len(files27)==6

    # V28 causal compounding.
    v28=found["v28"]
    gates["v28_all_scientific_gates"]=all_bool_gates(v28) is True
    econ=v28.get("economics",{})
    gates["v28_128x_ratio"]=econ.get("cold_to_warm_qualification_ratio")==128.0
    gates["v28_warm_zero_search"]=econ.get("warm_representation_search_candidates")==0
    ctl=v28.get("controller_ablation",{})
    gates["v28_retention_ablation_restores_development"]=ctl.get("retained_ablated_development_enabled",{}).get("route")=="DEVELOP_THEN_PROMOTE"
    gates["v28_no_retention_no_development_unknown"]=ctl.get("retained_ablated_development_disabled",{}).get("route")=="UNKNOWN"

    # V29 bounded change-language chain.
    v29=found["v29"]
    gates["v29_all_audit_gates"]=all_bool_gates(v29) is True
    gates["v29_frontier_is_outer_edit_substrate"]= "outer edit operations" in v29.get("remaining_frontier","")

    # V30 outer edit construction and independent replay.
    v30=found["v30"]
    gates["v30_all_primary_gates"]=all_bool_gates(v30) is True
    sel=v30.get("selected_operator",{})
    gates["v30_unique_operator_id_4"]=sel.get("operator_id")==4 and sel.get("truth_table")==[0,0,1,0]
    indep=[]
    for p,x in jsons("v30"):
        if verdict_of(x)=="INDEPENDENT_V30_REPLAY_PASS":
            indep.append((p,x))
    gates["v30_independent_replay_unique"]=len(indep)==1
    if indep:
        gates["v30_independent_replay_all_gates"]=all_bool_gates(indep[0][1]) is True
        rows["v30_independent"]={
            "path":str(indep[0][0].relative_to(ROOT)),
            "verdict":"INDEPENDENT_V30_REPLAY_PASS"
        }
    else:
        gates["v30_independent_replay_all_gates"]=False

    authorized_claims=[
        "Execute until certified inadequate; develop only under obstruction; promote verified transferable development into retained execution; contract proven redundancy; return UNKNOWN when evidence does not license change.",
        "V20-V25 compile a developmentally discovered relational representation into a formally verified source-level decision capability.",
        "Prospective retained-capability reuse is demonstrated on a frozen unseen relational challenge pack with zero representation search and zero developmental transitions, with six positive/negative obligations kernel-checked through pinned Hex.",
        "Causal compounding is demonstrated in the finite V28 setting: cold exhaustive re-derivation versus retained reuse yields a 128x qualification reduction; retention ablation restores development; removing both retention and development yields UNKNOWN.",
        "The developmental/change language itself has undergone bounded consequence-governed development in finite supplied meta-substrates.",
        "A previously supplied named outer edit operation can itself be constructed from consequence inside a supplied anonymous finite transducer substrate, with independent replay."
    ]
    required_boundaries=[
        "unrestricted action-language invention",
        "genesis from no prior primitives",
        "universal completeness",
        "autonomous/designerless subject selection or teleology",
        "optimal promotion/retention policies",
        "natural-world generality",
        "unbounded recursive self-development"
    ]
    remaining_frontier=(
        "generation, extension, contraction, or replacement of the lowest-level generic "
        "transducer/edit substrate without presupposing a richer supplied encompassing language; "
        "plus open-ended, non-finite, and natural-domain transfer"
    )

    gates["all_authority_gates"]=all(gates.values())
    verdict="VERIFIED_MINIMAL_DEVELOPMENTAL_ALGORITHM_UPGRADE_AUTHORITY_V31" if gates["all_authority_gates"] else "NEGATIVE_OR_PARTIAL"

    result={
        "verdict":verdict,
        "classification":"SEALED_DOCUMENT_UPGRADE_CAPSTONE",
        "authorities":rows,
        "gates":gates,
        "authorized_claims":authorized_claims,
        "required_boundaries":required_boundaries,
        "remaining_frontier":remaining_frontier,
        "canonical_compression":"Execute until inadequacy is proved. Develop only what the obstruction earns. Verify. Promote what transfers. Contract what no longer matters. Recurse on the language only when its own boundary is proved.",
        "interpretation":"Intelligence is the verified conversion of expensive discovery into cheaper future reachability."
    }
    (OUT/"final_evidence.json").write_text(json.dumps(result,indent=2,sort_keys=True)+"\n")
    print(json.dumps(result,indent=2,sort_keys=True))
    if verdict!="VERIFIED_MINIMAL_DEVELOPMENTAL_ALGORITHM_UPGRADE_AUTHORITY_V31":
        raise SystemExit(1)

if __name__=="__main__":
    main()
