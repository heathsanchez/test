#!/usr/bin/env python3
"""
MDA Historical Holdout Adjudicator v1

FROZEN BEFORE OPENING THE FOUR SELECTED PROTECTED RUN LOGS IN THIS AUDIT.

Purpose:
  Apply the already-derived recursive residue discipline to historical experiments
  that predate the MDA compression. Domain-specific warrant criteria come ONLY
  from each experiment's frozen PRECOMMIT.md. This script does not predict raw
  outcomes; it determines the narrowest scientifically warranted residue after
  protected outcomes are supplied.

Selected blind-audit cases:
  - active_latent_disambiguation_v1
  - right_question_transfer_v1
  - target_quotient_right_question_v1
  - verified_comparative_quotient_v1

The four outcomes are supplied later in a separate JSON file. Do not edit this
file in response to those outcomes.

Output vocabulary:
  UNKNOWN      : the measurement is inadequate for the intended decision.
  RESIDUAL     : the focal claim is not warranted; preserve the failure/residual.
  RETAIN(...)  : retain only the listed bounded claim(s).
  REJECT(...)  : protected evidence is adverse to the proposed mechanism.

This is a claim-discipline / time-split audit, not a proof of universal MDA.
"""
from __future__ import annotations
import json, sys
from pathlib import Path

CASE_ORDER = (
    "active_latent_disambiguation_v1",
    "right_question_transfer_v1",
    "target_quotient_right_question_v1",
    "verified_comparative_quotient_v1",
)

def gt(a,b,eps=1e-12): return float(a) > float(b) + eps
def ge(a,b,eps=1e-12): return float(a) + eps >= float(b)
def eq(a,b,eps=1e-12): return abs(float(a)-float(b)) <= eps

def adjudicate_active(m):
    # Frozen PRECOMMIT:
    # invalid if NO_EXTRA already at ceiling;
    # INFO_GAIN > RANDOM supports causal value of active separation;
    # equality does not support it.
    if ge(m["no_extra_accuracy"], 1.0):
        return {
            "status":"UNKNOWN",
            "residue":[],
            "reason":"NO_EXTRA ceiling makes separator test inadequate"
        }
    if gt(m["info_gain_accuracy"], m["random_accuracy"]):
        return {
            "status":"RETAIN",
            "residue":["ACTIVE_TARGET_DISAMBIGUATION"],
            "reason":"INFO_GAIN_QUERY > RANDOM_QUERY under matched one-query budget"
        }
    return {
        "status":"RESIDUAL",
        "residue":[],
        "reason":"active-separator hypothesis not supported on frozen family"
    }

def adjudicate_right_question_transfer(m):
    # Frozen primary:
    # TARGET_INFO accuracy > RANDOM accuracy AND pooled optimal-query >= .80.
    passed = (
        gt(m["target_info_accuracy"], m["random_accuracy"]) and
        ge(m["target_info_optimal_query_rate"], 0.80)
    )
    if passed:
        return {
            "status":"RETAIN",
            "residue":["OBSERVATION_ONLY_TARGET_DIRECTED_QUERY_SELECTION_TRANSFERS"],
            "reason":"both frozen primary transfer criteria pass"
        }
    return {
        "status":"RESIDUAL",
        "residue":[],
        "reason":"frozen transfer claim failed; preserve residual without rescue"
    }

def adjudicate_target_quotient(m):
    # Frozen primary:
    # TARGET_QUOTIENT > OBS_ONLY on optimal-query AND downstream accuracy;
    # pooled TARGET_QUOTIENT optimal-query rate >= .90.
    primary = (
        gt(m["target_quotient_optimal_query_rate"], m["obs_only_optimal_query_rate"]) and
        gt(m["target_quotient_accuracy"], m["obs_only_accuracy"]) and
        ge(m["target_quotient_optimal_query_rate"], 0.90)
    )
    if not primary:
        return {
            "status":"RESIDUAL",
            "residue":[],
            "reason":"target-quotient frozen primary did not pass"
        }

    residue=["TARGET_RELATIVE_QUOTIENT_USEFUL"]
    # Coupling identification is narrower than generic quotient usefulness.
    # PRECOMMIT's sham marginal removes outcome->target coupling. Only retain
    # coupling-specific mechanism when quotient also beats that sham.
    if (
        gt(m["target_quotient_optimal_query_rate"], m["sham_marginal_optimal_query_rate"]) and
        ge(m["target_quotient_accuracy"], m["sham_marginal_accuracy"])
    ):
        residue.append("QUERY_OUTCOME_TO_TARGET_COUPLING_WARRANTED")
    return {
        "status":"RETAIN",
        "residue":residue,
        "reason":"frozen primary passes; coupling retained only if sham control is beaten"
    }

def adjudicate_verified_comparative(m):
    # Frozen primary: VERIFIED_COMPARATIVE improves BOTH downstream accuracy
    # and exact-optimal-query rate relative to ONE_SHOT_COMPARATIVE.
    better_query = gt(m["verified_optimal_query_rate"], m["one_shot_optimal_query_rate"])
    better_acc   = gt(m["verified_accuracy"], m["one_shot_accuracy"])

    # Frozen interpretation explicitly says "if verification hurts, reject".
    hurts = (
        float(m["verified_optimal_query_rate"]) < float(m["one_shot_optimal_query_rate"]) or
        float(m["verified_accuracy"]) < float(m["one_shot_accuracy"])
    )
    if hurts:
        return {
            "status":"REJECT",
            "residue":[],
            "reason":"verification hurts at least one protected endpoint"
        }

    if better_query and better_acc:
        residue=["VERIFIED_COMPARATIVE_REPAIR_CAUSALLY_USEFUL"]
        if ge(m["verified_accuracy"],0.90) and ge(m["verified_optimal_query_rate"],0.80):
            residue.append("COMPARATIVE_FUTURE_STRUCTURE_STRONG_THRESHOLD")
        return {
            "status":"RETAIN",
            "residue":residue,
            "reason":"verified comparative beats one-shot on both frozen primary endpoints"
        }

    if better_query and not better_acc:
        return {
            "status":"RESIDUAL",
            "residue":["RANKING_FIDELITY_ONLY"],
            "reason":"ranking improves without downstream action; preserve as residual"
        }

    return {
        "status":"RESIDUAL",
        "residue":[],
        "reason":"comparative-repair causal claim not identified"
    }

ADJUDICATORS = {
    "active_latent_disambiguation_v1": adjudicate_active,
    "right_question_transfer_v1": adjudicate_right_question_transfer,
    "target_quotient_right_question_v1": adjudicate_target_quotient,
    "verified_comparative_quotient_v1": adjudicate_verified_comparative,
}

def rival_always_promote(case, m):
    return "RETAIN"

def rival_never_promote(case, m):
    return "RESIDUAL"

def rival_best_arm_promote(case, m):
    # Deliberately naive rival: if a focal/treated arm ties or beats its named
    # comparator on the first available accuracy-like endpoint, promote it.
    pairs = {
        "active_latent_disambiguation_v1": ("info_gain_accuracy","random_accuracy"),
        "right_question_transfer_v1": ("target_info_accuracy","random_accuracy"),
        "target_quotient_right_question_v1": ("target_quotient_accuracy","obs_only_accuracy"),
        "verified_comparative_quotient_v1": ("verified_accuracy","one_shot_accuracy"),
    }
    a,b=pairs[case]
    return "RETAIN" if ge(m[a],m[b]) else "RESIDUAL"

def main():
    if len(sys.argv)!=2:
        raise SystemExit("usage: mda_historical_holdout_adjudicator_v1.py outcomes.json")
    data=json.loads(Path(sys.argv[1]).read_text())
    assert data["schema"]=="mda.historical.holdout.outcomes.v1"
    assert tuple(data["cases"].keys()) == CASE_ORDER

    out={}
    for case in CASE_ORDER:
        m=data["cases"][case]
        decision=ADJUDICATORS[case](m)
        out[case]={
            **decision,
            "rivals":{
                "always_promote":rival_always_promote(case,m),
                "never_promote":rival_never_promote(case,m),
                "best_arm_promote":rival_best_arm_promote(case,m),
            }
        }
        print(case)
        print("  status :",decision["status"])
        print("  residue:",decision["residue"])
        print("  reason :",decision["reason"])
        print("  rivals :",out[case]["rivals"])

    # Non-degeneracy: a meaningful blind audit should not collapse all unseen
    # cases to the same decision class.
    statuses={v["status"] for v in out.values()}
    assert len(statuses) >= 2, f"degenerate adjudication across holdouts: {statuses}"

    result={"schema":"mda.historical.holdout.adjudication.v1","cases":out}
    outpath=Path(sys.argv[1]).with_name("historical_holdout_adjudication_v1.json")
    outpath.write_text(json.dumps(result,indent=2,sort_keys=True))
    print("HISTORICAL_HOLDOUT_ADJUDICATION_PASS")
    print("decision_classes=",sorted(statuses))

if __name__=="__main__":
    main()
