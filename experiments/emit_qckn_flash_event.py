#!/usr/bin/env python3
from __future__ import annotations
import argparse,hashlib,json
from pathlib import Path
RUN=35403074591
ARTIFACT=10570879149
ARTIFACT_DIGEST="sha256:0062e1df0f118b2c788a02082c8319b9359d79dc7eba11de702d3b2aab211a27"
AUTHORITY="collatz-reviewed-dominance@0bd6cc71a5fb4268109d5b404ecbf21c7aaaf4c1"
VERIFIER="manual-review+finite-replay-v1"
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
      "repository":"heathsanchez/test","commit":source_commit,"authority_snapshot":AUTHORITY,"verifier_id":VERIFIER,
      "source_evidence_sha256":h(et),"payload":payload,"payload_sha256":h(canonical(payload))}
    return evidence,event
def main():
    p=argparse.ArgumentParser();p.add_argument("--commit",required=True);p.add_argument("--out",type=Path,required=True);a=p.parse_args()
    e,v=build_event(source_commit=a.commit);a.out.mkdir(parents=True,exist_ok=True)
    (a.out/"evidence.json").write_text(canonical(e));(a.out/"event.json").write_text(canonical(v));print("QCKN_FLASH_EVENT="+v["event_id"])
if __name__=="__main__":main()
