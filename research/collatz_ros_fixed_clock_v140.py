#!/usr/bin/env python3
"""V140: stateful, read-only, proof-scoped fixed-clock chart decider.

This is an *epistemic grammar controller*, not a Collatz termination
oracle. It treats exact original-source two-clock base joins as potential
chart seeds. V137 proves an iff for existence of positive integer matched
multipliers at those fixed clocks; V139 proves a failed weighted inequality
cannot change by extending BOTH actual clocks with the same suffix.

If the source/pair does not meet at the supplied clocks, we mark only
BASE_MISMATCH, not mathematical divergence.
If it meets but its weighted guard fails, retire multiplier sweeps and
synchronous waiting for THIS chart branch, not all possible clocks.
If it meets and guard passes, emit the unique primitive multiplier
pair and its exact all-offset affine consequence, under CONDITIONAL
formal soundness plus independently replayable arithmetic premises.

No V134 or earlier proof record is created, changed, promoted or
revoked by this decider. The parent typed controller remains intact.
Global Collatz UNKNOWN, no QED.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from copy import deepcopy
from pathlib import Path

SCHEMA="COLLATZ_ROS_V140_FIXED_CLOCK_DECISION"
PARENT_PATH=Path("research/collatz_ros_state_v134.json")
PARENT_EXPECTED_SHA="586c5a0bd52757b29abffdc5785c752fbf8faaf4962229a5cea065de3d95d3b0"
PARENT_GIT_BLOB_SHA="d035f4a639b3e026681d432b3e3ceebe173c9c09"
PARENT_SHA="af2a2f1f51b5946709288583b09407aef0352d6d"
PINS={
 "V131_GENERIC_SOUNDNESS":{
    "run":37986167263,
    "commit":"9bd21704ef5fe22cbd2e74b04de65969922b28d3",
    "module":"Collatz.RootChartOverlapCompiler",
    "claim":"conditional ALL-OFFSET source/earlier chart merger only"},
 "V136_REDUCED_COEFFICIENTS":{
    "run":37994631045,
    "commit":"fee73139553e25e39050be1821d8ffd9e9cd5845",
    "module":"Collatz.ReducedThreePowerCharts",
    "claim":"reduced 3-adic coefficient pair gives matched slope under weighted guard"},
 "V137_MULTIPLIER_IFF":{
    "run":37995061222,
    "commit":"3dfbcf3a637cf241f4f5194000155fffb180e7dc",
    "module":"Collatz.ChartMultiplierCompleteness",
    "claim":"every positive matching integer multiplier pair scales the primitive pair; admission iff weighted clock inequality"},
 "V139_SUFFIX_INVARIANCE":{
    "run":37995933736,
    "commit":"88d72a20bdd0d9a3959f5a5ddf1d1c799fd7d6c3",
    "module":"Collatz.SynchronousClockOrientation",
    "claim":"same-length synchronous suffix preserves weighted clock-admissibility iff"},
}
PAIRS=[
 (5,3,1,2),(5,3,3,8),(21,3,3,2),
 (9,3,9,1),(15,3,8,1),(23,3,7,1),
 (27,23,59,0),(27,3,66,1),(45,7,3,2),
 (5,3,1,0),(27,3,0,0),
]

def T(n:int)->int:
    if type(n) is not int or n<=0:
        raise ValueError("shortcut requires a positive exact natural")
    return n//2 if n%2==0 else (3*n+1)//2

def iterate_with_odds(n:int,k:int)->tuple[int,int]:
    if type(k) is not int or not 0<=k<=10000:
        raise ValueError("exact finite clock out of declared executable bounds")
    odds=0
    for _ in range(k):
        odds+=n%2
        n=T(n)
    return n,odds

def chart(base:int,k:int,u:int)->dict:
    b,s=base,(1<<k)*u
    for _ in range(k):
        if s%2!=0: raise ValueError("affine offset does not preserve parity")
        if b%2==0:
            b,s=b//2,s//2
        else:
            b,s=(3*b+1)//2,3*s//2
    return {"source_slope":(1<<k)*u,"endpoint_intercept":b,
            "endpoint_slope":s}

def classify(a:int,p:int,i:int,j:int)->dict:
    if any(type(k) is not int for k in (a,p,i,j)):
        raise ValueError("all four source/clock coordinates must be exact integers")
    if not (0<p<a and 0<=i<=10000 and 0<=j<=10000):
        raise ValueError("original source must be strictly larger, positive, with valid clocks")
    yn,alpha=iterate_with_odds(a,i)
    yp,beta=iterate_with_odds(p,j)
    result={
       "original_source":a,"earlier_source":p,
       "source_clock":i,"earlier_clock":j,
       "source_endpoint":yn,"earlier_endpoint":yp,
       "source_odd_count":alpha,"earlier_odd_count":beta,
       "global_collatz":"UNKNOWN",
       "not_a_Collatz_counterexample":True,
    }
    if yn!=yp:
        return {**result,
           "status":"BASE_ENDPOINT_MISMATCH_AT_SUPPLIED_CLOCKS",
           "scope":"no coalescence proved at THESE clocks only",
           "candidate_multiplier_exists":None,
           "synchronous_guard_invariance_applicable":False,
           "proof_authority":"BOUNDED_EXACT_ONLY"}

    u=3**max(beta-alpha,0)
    v=3**max(alpha-beta,0)
    assert 3**alpha*u==3**beta*v
    left=2**j*3**alpha
    right=2**i*3**beta
    weighted_guard=(left<=right)
    slopeA=(1<<i)*u
    slopeP=(1<<j)*v
    assert (slopeP<=slopeA)==weighted_guard
    if not weighted_guard:
        return {**result,
           "status":"FIXED_CLOCK_MATCHED_COEFFICIENT_GRAMMAR_IMPOSSIBLE",
           "scope":"no positive source-nonexpanding integer chart multipliers at THESE clock orientations; no equal future suffix can repair",
           "candidate_multiplier_exists":False,
           "all_positive_pairs_primitive_scalings":True,
           "primitive_source_multiplier":u,"primitive_earlier_multiplier":v,
           "original_source_slope":slopeA,"earlier_source_slope":slopeP,
           "weighted_left":left,"weighted_right":right,
           "synchronous_guard_invariance_applicable":True,
           "proof_authority":["V137_MULTIPLIER_IFF","V139_SUFFIX_INVARIANCE"],
        }

    sourcechart=chart(a,i,u)
    earlierchart=chart(p,j,v)
    assert sourcechart["endpoint_intercept"]==earlierchart["endpoint_intercept"]==yn
    assert sourcechart["endpoint_slope"]==earlierchart["endpoint_slope"]==3**(alpha+beta)
    assert 0<p<a and slopeP<=slopeA
    return {**result,
      "status":"ADMISSIBLE_PRIMITIVE_FULL_OFFSET_CHART",
      "scope":"ALL nonnegative integer offsets for these TWO independently replayed parity charts, not a universal event producer",
      "candidate_multiplier_exists":True,
      "all_positive_pairs_primitive_scalings":True,
      "primitive_source_multiplier":u,"primitive_earlier_multiplier":v,
      "original_source_slope":slopeA,"earlier_source_slope":slopeP,
      "weighted_left":left,"weighted_right":right,
      "common_endpoint_slope":3**(alpha+beta),
      "common_endpoint_intercept":yn,
      "synchronous_guard_invariance_applicable":True,
      "proof_authority":["V136_REDUCED_COEFFICIENTS",
                         "V131_GENERIC_SOUNDNESS","V137_MULTIPLIER_IFF"],
      "individual_chart_formally_reified":False,
      "source_all_offsets":"a+original_source_slope*t",
      "earlier_all_offsets":"p+earlier_source_slope*t",
    }

def canonical(s)->str:
    return json.dumps(s,sort_keys=True,separators=(",",":"),ensure_ascii=False)

def digest(s)->str:
    return hashlib.sha256(canonical(s).encode()).hexdigest()

def parent_bytes()->bytes:
    b=PARENT_PATH.read_bytes()
    j=json.loads(b)
    if digest(j)!=PARENT_EXPECTED_SHA:
        raise ValueError("parent canonical research content changed without qualification")
    blob_head=("blob "+str(len(b))+"\\0").encode().replace(b"\\\\0",b"\\0")
    if hashlib.sha1(blob_head+b).hexdigest()!=PARENT_GIT_BLOB_SHA:
        raise ValueError("parent Git source blob bytes changed without qualification")
    if j["admission_schema"]!="COLLATZ_ROS_V134_LATE_ROOT_REUSE_AUTHORITY":
        raise ValueError("not the active qualified V134 parent")
    if len(j["joins"])!=17 or j["global_collatz"]!="UNKNOWN" or j["qed"] is not False:
        raise ValueError("old source-relative future warrants or epistemic state changed")
    if j["negative_controls"][2]["changing_source"]!=2**80-1:
        raise ValueError("80-bit naturalness negative control is no longer exact")
    return b

def bootstrap()->dict:
    parent_bytes()
    cases=[classify(*p) for p in PAIRS]
    return {
        "schema":SCHEMA,
        "parent":{"repo":"heathsanchez/test",
                  "commit":PARENT_SHA,
                  "relative_path":str(PARENT_PATH),
                  "canonical_state_sha256":PARENT_EXPECTED_SHA,
                  "git_blob_sha1":PARENT_GIT_BLOB_SHA,
                  "raw_file_sha256":hashlib.sha256(PARENT_PATH.read_bytes()).hexdigest(),
                  "parent_claim_count":17,
                  "mutated":False},
        "proof_authorities":deepcopy(PINS),
        "algorithm":"primitive integer coefficient pair; one weighted orientation bit, no multiplier sweeps or common synchronous waiting",
        "tracked_cases":cases,
        "retired_redundant_search":["repeated_positive_multiplier_search_at_fixed_clocks",
           "identical_additional_shortcut_wait_on_both_meeting_clocks"],
        "not_retired_search":["new_asymmetric_clock_or_meeting_endpoint",
           "new_original_source_relative_earlier_predecessor",
           "universal_no-second-positive-future-class theorem"],
        "universal_event_producer_proved":False,
        "global_collatz":"UNKNOWN",
        "qed":False,
    }

def audit(s:dict)->None:
    parent_bytes()
    if s.get("schema")!=SCHEMA or s.get("parent")!=bootstrap()["parent"]:
        raise ValueError("wrong parent reference or altered protected source world")
    if s.get("proof_authorities")!=PINS:
        raise ValueError("theorem authority changed without an independent proof gate")
    expected=bootstrap()
    if s!=expected:
        raise ValueError("cached decisions differ from exact replay or broaden their scopes")

def write(s:dict,path:Path)->str:
    audit(s)
    path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps(s,indent=2,sort_keys=True)+"\n")
    return digest(s)

def main()->None:
    cli=argparse.ArgumentParser()
    cli.add_argument("--bootstrap",action="store_true")
    cli.add_argument("--input",type=Path)
    cli.add_argument("--output",type=Path)
    args=cli.parse_args()
    if args.bootstrap==bool(args.input):
        cli.error("choose exactly --bootstrap or --input")
    s=bootstrap() if args.bootstrap else json.loads(args.input.read_text())
    checksum=write(s,args.output) if args.output else (audit(s) or digest(s))
    statuses={}
    for x in s["tracked_cases"]:
        statuses[x["status"]]=statuses.get(x["status"],0)+1
    print(json.dumps({"schema":SCHEMA,
       "parent_state_sha256":PARENT_EXPECTED_SHA,
       "decision_state_sha256":checksum,
       "tracked_clock_cases":len(s["tracked_cases"]),
       "decision_types":statuses,
       "global_collatz":"UNKNOWN",
       "qed":False},sort_keys=True))

if __name__=="__main__":
    main()
