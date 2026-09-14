#!/usr/bin/env python3
import json
from pathlib import Path

OBS=Path("experiments/warranted_consequential_difference_v1/HETEROGENEOUS_OBSERVATIONS_V1.json")

def run():
    d=json.loads(OBS.read_text())["domains"]
    checks=[]
    def chk(n,c,detail=""):
        checks.append(bool(c))
        print(f"  [{'PASS' if c else 'FAIL'}] {n}" + (f" — {detail}" if detail else ""))

    print("STATE–TEST KERNEL COMPLETENESS BOUNDARY")

    lean=d["lean_e0034"]
    ground_rows={
        a:(x["good_pass"],x["good_total"],x["bad_reject"],x["bad_total"])
        for a,x in lean["ground"].items()
    }
    chk("K1 Lean arms are identical under frozen correctness ground",
        len(set(ground_rows.values()))==1,ground_rows)
    chk("K2 Lean arms differ under developmental resource measurement",
        len(set(lean["median_cpu_s"].values()))>1,lean["median_cpu_s"])
    chk("K3 frozen developmental decision uses preference despite semantic EQ",
        lean["median_cpu_s"]["a1"]>lean["median_cpu_s"]["a0"] and
        "reject" in lean["frozen_interpretation"].lower())

    proof=d["proof_regenesis"]
    chk("K4 proof domain contains a real consequential distinction",
        proof["gates"]["cold_amputation_fails"] and proof["gates"]["exact_ablation_restores_failure"])
    lawful=(proof["gates"]["agent_completed"] and proof["gates"]["only_allowed_file_changed"] and proof["gates"]["ring_verifies"])
    chk("K5 consequential distinction alone does not make a candidate lawful/retainable",
        not lawful and not proof["passed"])

    acc=d["acc_publisher"]
    chk("K6 ACC candidates can be semantically valid without winning developmental preference",
        acc["verified_ac_candidates"]>0 and acc["strict_wins_after"]==0 and acc["selected_rows"]==0,
        f"verified={acc['verified_ac_candidates']} selected={acc['selected_rows']}")

    tq=d["target_quotient"]
    chk("K7 when protected consequence itself differs, kernel-level distinction is sufficient to justify non-equivalence",
        tq["target_quotient"]["accuracy"]>tq["obs_only"]["accuracy"] and tq["primary_pass"])

    passed=sum(checks); total=len(checks)
    print(f"VERDICT: {'PASS' if passed==total else 'FAIL'} {passed}/{total}")
    if passed!=total: raise SystemExit(1)
    print("VERIFIED_STATE_TEST_KERNEL_IS_CONSEQUENTIAL_EQUIVALENCE_CORE")
    print("FALSIFIED_KERNEL_ALONE_AS_COMPLETE_DEVELOPMENTAL_SELECTOR")
    print("REQUIRES_WARRANT_LAWFULNESS_AND_PREORDER_OUTSIDE_OR_TYPED_ABOVE_KERNEL")

if __name__=="__main__":run()
