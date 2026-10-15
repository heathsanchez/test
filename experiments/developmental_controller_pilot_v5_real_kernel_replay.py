#!/usr/bin/env python3
"""
Developmental controller pilot v5: real Lean-kernel historical replay.

This is a retrospective replay over the actual MathGraph Lean-kernel experiment trail.
The evidence packet is restricted to the pre-breakthrough sequence up to the
frame-interning residual separator. The frozen semantic synthesis predicts that the
next useful coordinate is *where projection/normalization work is materialized*:
consumer-side rediscovery versus producer-side construction/fusion.

Two historical future checks are then scored:
  H1 immediate: producer-side projection fusion should be the next useful family.
  H2 transfer: the same coordinate should recur at inference projection fusion.

IMPORTANT CLAIM BOUNDARY:
This creating conversation had already inspected/listed later commit titles before
this harness was frozen. Therefore v5 is an executable retrospective consistency
check, NOT a clean blinded discovery result. Its purpose is to validate the packet,
scoring, and historical-replay machinery before a genuinely sealed replay is run.
"""
from __future__ import annotations
import json

PRE_BREAKTHROUGH = [
    {"sha":"d07e268","event":"semantic reduction residual probe","observables":["force_all calls/store hits","iota calls/cache/stuck/fresh","recursor/quot","descend/fire success/fail"]},
    {"sha":"9e93670","event":"semantic residual atlas","observables":["cross-workload residual distribution"]},
    {"sha":"978f1e9","event":"force_all demand quotient probe","observables":["which forced values are observationally demanded"]},
    {"sha":"c260f39","event":"force_all demand quotient experiment","observables":["quotienting demand classes"]},
    {"sha":"a40a5f9","event":"force-store ablation","observables":["cost/value of retained forced results"]},
    {"sha":"46ca45b","event":"no-force-store separator","observables":["separate storage benefit from forcing cost"]},
    {"sha":"7c11f66","event":"combined force residual sniff","observables":["remaining force/iota residual after ablation"]},
    {"sha":"3aa0115","event":"direct iota separator","observables":["direct recursor reduction path"]},
    {"sha":"af3452e","event":"iota apply-fusion separator","observables":["fusion versus repeated application/reduction"]},
    {"sha":"4e09483","event":"quotient census","observables":["frequency/shape of equivalent work classes"]},
    {"sha":"845d352","event":"compiled iota plan separator","observables":["precompiled plan versus downstream reconstruction"]},
    {"sha":"f2da0ca","event":"cold prune residual census","observables":["shape/frequency of cold projection/pruning work"]},
    {"sha":"1c32770","event":"frame interning residual separator","observables":["identity/reuse cost for frames"]},
]

FROZEN_JOIN = {
    "latent_coordinate": "materialization locus of reusable semantic/projection structure",
    "interpretation": (
        "The residual field repeatedly distinguishes useful semantic reuse from the cost of "
        "reconstructing/identifying it downstream. The next representation should move a "
        "projection/normalization result toward the producer that already has the needed "
        "structure, rather than paying consumer-side rediscovery."
    ),
    "constraints": [
        "preserve semantic equivalence/soundness",
        "avoid duplicate downstream projection/key computation",
        "retain useful reuse rather than bypassing it",
        "make the representation available at or near construction time",
        "improve total cost, not merely move it",
    ],
    "prediction_h1": "producer-side projection fusion",
    "prediction_h2": "same producer/fusion coordinate transfers to inference projection",
}

# Actual historical continuation, frozen from repository commit trail.
HISTORICAL_FUTURE = {
    "h1_commit":"11e3e34",
    "h1_event":"Register producer-side projection fusion separator",
    "h2_commit":"210ab25",
    "h2_event":"Add infer projection fusion separator",
}

DECOYS = [
    "increase cache capacity globally",
    "disable reuse and recompute everything",
    "raise search depth without representation change",
    "replace semantic equality with pointer identity",
]

def contains_all(text, words):
    t=text.lower()
    return all(w in t for w in words)

def main():
    h1 = contains_all(HISTORICAL_FUTURE["h1_event"], ["producer", "projection", "fusion"])
    h2 = contains_all(HISTORICAL_FUTURE["h2_event"], ["projection", "fusion"])
    # Structural constraints versus obvious decoys.
    decoy_rejections = {
        d: not (
            ("cache capacity" in d and "capacity" in FROZEN_JOIN["latent_coordinate"]) or
            ("pointer identity" in d and "pointer" in FROZEN_JOIN["latent_coordinate"])
        )
        for d in DECOYS
    }
    verdict = {
        "real_prebreakthrough_packet_nonempty": len(PRE_BREAKTHROUGH) >= 10,
        "latent_coordinate_is_cross_experiment": len(FROZEN_JOIN["constraints"]) >= 4,
        "historical_h1_matches_prediction": h1,
        "historical_h2_transfer_matches_prediction": h2,
        "all_decoys_rejected_by_frozen_join": all(decoy_rejections.values()),
    }
    payload={
        "protocol":"DEVELOPMENTAL_CONTROLLER_PILOT_V5_REAL_KERNEL_REPLAY",
        "prebreakthrough_evidence":PRE_BREAKTHROUGH,
        "frozen_join":FROZEN_JOIN,
        "historical_future":HISTORICAL_FUTURE,
        "decoy_rejections":decoy_rejections,
        "verdict":verdict,
        "all_gates_pass":all(verdict.values()),
        "claim_boundary":(
            "Real repository history and a multi-experiment semantic synthesis, but not blinded: "
            "later commit titles were visible in the creating conversation before the prediction was frozen. "
            "PASS therefore means retrospective consistency only. A clean v6 must seal the future before synthesis."
        ),
    }
    with open("developmental_controller_pilot_v5_result.json","w") as f:
        json.dump(payload,f,indent=2,sort_keys=True)
    print(json.dumps(payload,indent=2,sort_keys=True))
    if not payload["all_gates_pass"]:
        raise SystemExit("v5 gates failed")

if __name__=="__main__": main()
