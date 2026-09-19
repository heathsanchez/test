#!/usr/bin/env python3
from __future__ import annotations
import argparse,hashlib,json
from pathlib import Path
RUN=35403074591
ARTIFACT=10570879149
ARTIFACT_DIGEST="sha256:0062e1df0f118b2c788a02082c8319b9359d79dc7eba11de702d3b2aab211a27"
AUTHORITY="collatz-reviewed-dominance@0bd6cc71a5fb4268109d5b404ecbf21c7aaaf4c1"
VERIFIER="manual-review+finite-replay-v1"
BANK_EVENT_COMMIT="7fe10392f2865a008ff8642f4da64d93378c780f"
def canonical(v): return json.dumps(v,sort_keys=True,separators=(",",":"))
def h(s): return hashlib.sha256(s.encode()).hexdigest()
def build_event(*,source_commit):
    if len(source_commit)!=40 or any(c not in "0123456789abcdef" for c in source_commit): raise ValueError("source commit must be full SHA")
    evidence={"schema":"collatz-flash-propagation-evidence-v1","run":RUN,"artifact":ARTIFACT,"artifact_digest":ARTIFACT_DIGEST,
      "arms":{"isolated":{"T_calls":1501097},"flash":{"T_calls":208613},"guarded":{"T_calls":17401},"ablation":{"T_calls":1501097}},
      "verdict":"PASS_BOUNDED_PROPAGATION_NO_ADVANTAGE_OVER_UPFRONT_GUARD",
      "claim_boundary":"retrospective fixed workload; manually reviewed dominance rule; no Collatz termination claim"}
    candidate={"family":"same-verified-bank","variation":"bank-order-policy","claim":"strict-baseline-advantage"}
    obs={"obstruction_id":"collatz:bank-order-redundancy:v1","input_type":"collatz-bank-order-policy","output_type":"strict-baseline-advantage",
      "contract":{"authority_snapshot":AUTHORITY,"verifier_id":VERIFIER},"candidate_fingerprint":h(canonical(candidate)),
      "separating_input":"eight deterministic bank-order policies","expected_output":"new-strict-advantage","actual_output":"redundant-policy-order",
      "provenance":f"manual-review:reviewed-dominance-v1/run:{RUN}/artifact:{ARTIFACT}"}
    payload={"obstruction":obs}; et=canonical(evidence)
    event={"schema":"qckn-flash-external-event-v1","event_id":obs["obstruction_id"],"event_kind":"obstruction_admission",
      "repository":"heathsanchez/test","commit":BANK_EVENT_COMMIT,"authority_snapshot":AUTHORITY,"verifier_id":VERIFIER,
      "source_evidence_sha256":h(et),"payload":payload,"payload_sha256":h(canonical(payload))}
    return evidence,event

SHARED_RUN=35063857334
SHARED_SOURCE_SHA="8d4ff807f59dd0bf41f06a67b15f25e1c0c8ffc5"
SHARED_EQ_JOB=104689752490
SHARED_SCOUT_JOB=104689796559
SHARED_EQ_ARTIFACT=10433007976
SHARED_EQ_DIGEST="sha256:6fbceab4dcb0da71b5f8a311bc2dc7126acd89b320047615e5b0dc8a8d6b241b"
SHARED_SCOUT_ARTIFACT=10432833694
SHARED_SCOUT_DIGEST="sha256:f2f499a07ca04a9bd85ac14a61b55eddf08c3c8d142b74d1bf59d6bc5a90e5f3"
SHARED_AUTHORITY=f"collatz-shared-normalized@{SHARED_SOURCE_SHA}"
SHARED_VERIFIER="differential-equivalence+bounded-scout-v1"
SHARED_EVENT_COMMIT="c444e21e15557126fae555ddbdfa1e04016e1573"

def build_shared_normalized_event(*,source_commit):
    if len(source_commit)!=40 or any(ch not in "0123456789abcdef" for ch in source_commit):
        raise ValueError("source commit must be full SHA")
    evidence={
      "schema":"collatz-shared-normalized-evidence-v1",
      "run":SHARED_RUN,
      "source_sha":SHARED_SOURCE_SHA,
      "equivalence":{
        "job":SHARED_EQ_JOB,
        "artifact":SHARED_EQ_ARTIFACT,
        "artifact_digest":SHARED_EQ_DIGEST,
        "K":8,
        "R":4,
        "residual":16,
        "comparisons":80,
        "reference_nodes":1467,
        "reference_memo_hits":665,
        "shared_calls":2607,
        "shared_unique_states":1139,
        "shared_memo_hits":1468,
        "shared_peak_memo":367,
        "shared_e_cases":2141,
        "shared_o_run_cases":2527,
        "shared_prunes":1100,
        "max_u":14,
        "max_v":12,
        "marker":"VERIFIED_SHARED_EQUIVALENCE",
      },
      "scout":{
        "job":SHARED_SCOUT_JOB,
        "artifact":SHARED_SCOUT_ARTIFACT,
        "artifact_digest":SHARED_SCOUT_DIGEST,
        "K":12,
        "R":8,
        "residual":144,
        "closed":75,
        "unresolved":69,
        "max_required_r":7,
        "max_witness_b":111,
        "calls":52798,
        "unique_states":27464,
        "memo_hits":25334,
        "prunes":27245,
        "marker":"VERIFIED_SHARED_NORMALIZED_SCOUT",
        "residual_marker":"SHARED_NORMALIZED_ZERO_TERNARY_RESIDUAL_REMAINS",
      },
      "claim_boundary":"bounded shared-normalized equivalence and scout evidence only; no Collatz termination claim",
    }
    capability={
      "capability_id":"collatz:shared-normalized-equivalence:k8-r4:v1",
      "input_type":"collatz-shared-normalized-contract",
      "output_type":"verification-status",
      "semantics":[["K8-R4","equivalent-to-reference"]],
      "guard_inputs":["K8-R4"],
      "certificate_id":f"run:{SHARED_RUN}/jobs:{SHARED_EQ_JOB},{SHARED_SCOUT_JOB}",
      "dependencies":[],
      "authority_snapshot":SHARED_AUTHORITY,
      "verifier_id":SHARED_VERIFIER,
      "provenance_ids":[
        f"source-commit:{SHARED_SOURCE_SHA}",
        f"run:{SHARED_RUN}",
        f"artifact:{SHARED_EQ_ARTIFACT}",
        f"artifact:{SHARED_SCOUT_ARTIFACT}",
      ],
      "cost":0,
    }
    payload={
      "capability":capability,
      "oracle":[["K8-R4","equivalent-to-reference"]],
      "support_ids":[],
      "origin":"collatz-shared-normalized",
    }
    evidence_text=canonical(evidence)
    event={
      "schema":"qckn-flash-external-event-v1",
      "event_id":capability["capability_id"],
      "event_kind":"capability_admission",
      "repository":"heathsanchez/test",
      "commit":SHARED_EVENT_COMMIT,
      "authority_snapshot":SHARED_AUTHORITY,
      "verifier_id":SHARED_VERIFIER,
      "source_evidence_sha256":h(evidence_text),
      "payload":payload,
      "payload_sha256":h(canonical(payload)),
    }
    return evidence,event

def main():
    p=argparse.ArgumentParser();p.add_argument("--commit",required=True);p.add_argument("--out",type=Path,required=True);a=p.parse_args()
    e,v=build_event(source_commit=a.commit)
    a.out.mkdir(parents=True,exist_ok=True)
    (a.out/"evidence.json").write_text(canonical(e))
    (a.out/"event.json").write_text(canonical(v))
    print("QCKN_FLASH_EVENT="+v["event_id"])

    se,sv=build_shared_normalized_event(source_commit=a.commit)
    shared_out=a.out/"shared-normalized"
    shared_out.mkdir(parents=True,exist_ok=True)
    (shared_out/"evidence.json").write_text(canonical(se))
    (shared_out/"event.json").write_text(canonical(sv))
    print("QCKN_FLASH_EVENT="+sv["event_id"])
if __name__=="__main__":main()
