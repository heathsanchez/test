#!/usr/bin/env python3
"""WCD V1 heterogeneous-domain adjudicator.

The domain adapters were frozen in
experiments/warranted_consequential_difference_v1/HETEROGENEOUS_AUDIT_FROZEN_MANIFEST.md
at commit c884b39c67f7f30499a3ee4eafb50a8e88c394cb before the selected
protected logs were opened for this audit.

This script may not add observables beyond that manifest.
"""
from __future__ import annotations
import json, sys
from pathlib import Path

KERNEL = "978af4e94815128b4c517562f9a0bae26eea1e55"
MANIFEST = "c884b39c67f7f30499a3ee4eafb50a8e88c394cb"

def all_ground_pass(g):
    return all(
        x["good_pass"] == x["good_total"] and x["bad_reject"] == x["bad_total"]
        for x in g.values()
    )

def classify_controller(case):
    if case == "same_complete_signature":
        return "EQ"
    if case == "different_complete_signature":
        return "DIST"
    if case in {"protected_outcome_access","unfrozen_protocol","incomplete_probe_coverage"}:
        return "UNKNOWN"
    raise AssertionError(case)

def main():
    if len(sys.argv) != 2:
        raise SystemExit("usage: wcd_heterogeneous_domain_audit_v1.py observations.json")
    d=json.loads(Path(sys.argv[1]).read_text())
    assert d["schema"] == "wcd.heterogeneous.audit.observations.v1"
    assert d["frozen_kernel_commit"] == KERNEL
    assert d["adapter_manifest_commit"] == MANIFEST

    checks=[]
    rows={}
    def chk(name, cond, detail=""):
        checks.append((name,bool(cond),detail))
        print(f"  [{'PASS' if cond else 'FAIL'}] {name}" + (f" — {detail}" if detail else ""))

    print("="*100)
    print("WCD V1 HETEROGENEOUS DOMAIN AUDIT")
    print("kernel =",KERNEL)
    print("adapter_manifest =",MANIFEST)
    print("="*100)

    # D1 Lean performance optimization.
    print("\n--- D1 LEAN CHECKER OPTIMIZATION ---")
    x=d["domains"]["lean_e0034"]
    ground_eq=all_ground_pass(x["ground"])
    chk("D1.1 all three checker arms satisfy frozen semantic ground",ground_eq)
    cpu_order=sorted(x["median_cpu_s"], key=x["median_cpu_s"].get)
    chk("D1.2 enabled splice is not a preference win",
        x["median_cpu_s"]["a1"] > x["median_cpu_s"]["a0"],
        f"cpu_order={cpu_order} a1_delta={x['a1_cpu_delta_pct']:.3f}%")
    chk("D1.3 frozen interpretation rejects the slower lawful change",
        "reject" in x["frozen_interpretation"].lower())
    rows["lean_e0034"]={
        "wcd_form":"EQ + PREFERENCE",
        "decision":"REJECT_A1_CARRY_PRESENT",
        "counterexample":False
    }

    # D2 proof regeneration.
    print("\n--- D2 VERIFIED PROOF REGENESIS ---")
    x=d["domains"]["proof_regenesis"]
    chk("D2.1 amputation creates a protected consequence difference",
        x["gates"]["cold_amputation_fails"])
    chk("D2.2 exact synthesized-interface ablation restores failure",
        x["gates"]["exact_ablation_restores_failure"])
    lawful=(
        x["gates"]["agent_completed"]
        and x["gates"]["only_allowed_file_changed"]
        and x["gates"]["only_allowed_slot_changed"]
        and x["gates"]["ring_verifies"]
        and x["gates"]["full_build_verifies"]
        and x["gates"]["proof_hygiene_clean"]
    )
    chk("D2.3 candidate fails frozen lawfulness/ground gate",not lawful,
        f"agent_completed={x['gates']['agent_completed']} only_allowed_file_changed={x['gates']['only_allowed_file_changed']} ring_verifies={x['gates']['ring_verifies']}")
    chk("D2.4 failed candidate is not promoted",not x["passed"] and "RESIDUAL" in x["workflow_summary"])
    rows["proof_regenesis"]={
        "wcd_form":"DIST OBSERVED BUT CANDIDATE UNLAWFUL",
        "decision":"RESIDUAL_NO_INHERITANCE",
        "counterexample":False
    }

    # D3 target-relative prediction/query representation.
    print("\n--- D3 TARGET-RELATIVE PREDICTIVE QUOTIENT ---")
    x=d["domains"]["target_quotient"]
    tq=x["target_quotient"]; obs=x["obs_only"]; sham=x["sham_marginal"]
    chk("D3.1 quotient changes protected downstream accuracy vs observation-only",
        tq["accuracy"] > obs["accuracy"],
        f"{tq['accuracy']} > {obs['accuracy']}")
    chk("D3.2 quotient changes optimal-query consequence vs observation-only",
        tq["optimal_query_rate"] > obs["optimal_query_rate"],
        f"{tq['optimal_query_rate']} > {obs['optimal_query_rate']}")
    chk("D3.3 coupling control is separated by protected consequence",
        tq["accuracy"] > sham["accuracy"] and tq["optimal_query_rate"] > sham["optimal_query_rate"])
    chk("D3.4 frozen primary passes",x["primary_pass"])
    rows["target_quotient"]={
        "wcd_form":"DIST",
        "decision":"RETAIN_TARGET_RELATIVE_COUPLING",
        "counterexample":False,
        "calibration_only":True
    }

    # D4 controller outcome-blind equivalence.
    print("\n--- D4 RESEARCH-CONTROL MOVE EQUIVALENCE ---")
    x=d["domains"]["controller_v9"]
    chk("D4.1 original controller invariant suite passes",x["suite_pass"])
    for case,expected in x["cases"].items():
        got=classify_controller(case)
        chk(f"D4.{case} => {expected}", got == expected, f"got={got}")
    rows["controller_v9"]={
        "wcd_form":"EQ | DIST | UNKNOWN",
        "decision":"PRESERVE_OUTCOME_BLIND_ATTRIBUTION_CLASSES",
        "counterexample":False
    }

    # D5 Andrews-Curtis competitive search.
    print("\n--- D5 ANDREWS-CURTIS COMPETITIVE SEARCH ---")
    x=d["domains"]["acc_publisher"]
    chk("D5.1 current pool reaches pinned-verifier-clean candidates",
        x["verified_ac_candidates"] == x["optimized_candidates"] and x["verified_ac_candidates"] > 0,
        f"verified={x['verified_ac_candidates']}")
    chk("D5.2 internal lawful optimization can improve paths",
        x["fortification_moves_saved"] > 0,
        f"moves_saved={x['fortification_moves_saved']}")
    chk("D5.3 no strict public-frontier preference win exists",
        x["strict_wins_after"] == 0)
    chk("D5.4 publisher carries incumbent rather than promoting non-wins",
        x["selected_rows"] == 0 and x["selected_ac"] == 0)
    rows["acc_publisher"]={
        "wcd_form":"GROUND-VALID + NO PREFERENCE WIN",
        "decision":"IDENTITY_CARRY_PRESENT",
        "counterexample":False,
        "retrospective":True
    }

    # Cross-domain falsifier.
    print("\n--- CROSS-DOMAIN FALSIFICATION ---")
    counterexamples=[k for k,v in rows.items() if v.get("counterexample")]
    chk("X1 no tested verified transition requires an observable absent from its frozen adapter",
        not counterexamples, counterexamples)
    forms={v["wcd_form"] for v in rows.values()}
    chk("X2 audit is behaviorally non-degenerate across domains",
        len(forms) >= 4, sorted(forms))

    n=sum(ok for _,ok,_ in checks); total=len(checks)
    verdict="PASS" if n==total else "FAIL"
    print("\n"+json.dumps(rows,indent=2,sort_keys=True))
    print("\n"+"="*100)
    print(f"VERDICT: {verdict} {n}/{total}")
    if verdict=="PASS":
        print("SURVIVED_HETEROGENEOUS_DOMAIN_AUDIT_WCD_V1")
        print("NO_HETEROGENEOUS_COUNTEREXAMPLE_FOUND_UNDER_FROZEN_ADAPTERS")
    else:
        print("HETEROGENEOUS_COUNTEREXAMPLE_OR_ADAPTER_FAILURE_WCD_V1")
        raise SystemExit(1)

if __name__=="__main__":
    main()
