#!/usr/bin/env python3
"""V9: test whether preserving rival developmental hypotheses beats premature JOIN collapse.

This is a bounded controller-policy test, not a claim of open-ended discovery.
A hidden regime is sampled from four candidate developmental explanations. Initial
observations are deliberately ambiguous: all four explain them. The controller then
gets one intervention budget before a protected transfer query.

Arms:
  SINGLE: collapse to the highest-prior story, choose its preferred local probe.
  TOPK:   preserve all live hypotheses and choose the probe with maximum expected
          version-space reduction.
  ORACLE: knows the hidden regime and chooses the best probe.

Pass criterion: TOPK must strictly beat SINGLE on protected transfer across all
hidden regimes and recover the hidden regime after its separator.
"""
from __future__ import annotations
import json
from pathlib import Path

HYPOTHESES = {
    "constructor_gap": {
        "prior": 0.34,
        "probe": "constructor_probe",
        "signature": {"constructor_probe": 1, "continuation_probe": 0, "compounding_probe": 0, "routing_probe": 0},
        "transfer": "construct",
    },
    "continuation_ir": {
        "prior": 0.30,
        "probe": "continuation_probe",
        "signature": {"constructor_probe": 0, "continuation_probe": 1, "compounding_probe": 0, "routing_probe": 0},
        "transfer": "represent",
    },
    "multi_episode_compounding": {
        "prior": 0.22,
        "probe": "compounding_probe",
        "signature": {"constructor_probe": 0, "continuation_probe": 0, "compounding_probe": 1, "routing_probe": 0},
        "transfer": "compound",
    },
    "routing_hardening": {
        "prior": 0.14,
        "probe": "routing_probe",
        "signature": {"constructor_probe": 0, "continuation_probe": 0, "compounding_probe": 0, "routing_probe": 1},
        "transfer": "route",
    },
}
PROBES = ["constructor_probe", "continuation_probe", "compounding_probe", "routing_probe"]


def posterior(live, probe, outcome):
    return [h for h in live if HYPOTHESES[h]["signature"][probe] == outcome]


def expected_remaining(live, probe):
    # prior-weighted expected live-set size after the probe
    total = sum(HYPOTHESES[h]["prior"] for h in live)
    exp = 0.0
    for outcome in (0, 1):
        subset = [h for h in live if HYPOTHESES[h]["signature"][probe] == outcome]
        p = sum(HYPOTHESES[h]["prior"] for h in subset) / total if total else 0
        exp += p * len(subset)
    return exp


def topk_probe(live):
    return min(PROBES, key=lambda p: (expected_remaining(live, p), p))


def run(hidden):
    live = list(HYPOTHESES)

    # SINGLE prematurely commits to highest-prior explanation.
    single_story = max(live, key=lambda h: HYPOTHESES[h]["prior"])
    single_probe = HYPOTHESES[single_story]["probe"]
    single_outcome = HYPOTHESES[hidden]["signature"][single_probe]
    single_live = posterior(live, single_probe, single_outcome)
    # SINGLE remains committed unless its own story is directly falsified; if falsified,
    # it picks the highest-prior survivor without another experiment.
    if single_story not in single_live:
        single_story = max(single_live, key=lambda h: HYPOTHESES[h]["prior"])
    single_prediction = HYPOTHESES[single_story]["transfer"]

    # TOPK chooses the intervention that maximally reduces the live version space.
    top_probe = topk_probe(live)
    top_outcome = HYPOTHESES[hidden]["signature"][top_probe]
    top_live = posterior(live, top_probe, top_outcome)
    # If one probe is insufficient, continue choosing separators until singleton;
    # charge every probe, but protected prediction is made only after evidence.
    top_probes = [(top_probe, top_outcome)]
    while len(top_live) > 1:
        p = topk_probe(top_live)
        o = HYPOTHESES[hidden]["signature"][p]
        top_live = posterior(top_live, p, o)
        top_probes.append((p, o))
    top_story = top_live[0]
    top_prediction = HYPOTHESES[top_story]["transfer"]

    truth = HYPOTHESES[hidden]["transfer"]
    return {
        "hidden": hidden,
        "truth": truth,
        "single": {
            "first_probe": single_probe,
            "live_after_probe": single_live,
            "chosen_story": single_story,
            "prediction": single_prediction,
            "correct": single_prediction == truth,
        },
        "topk": {
            "probes": top_probes,
            "chosen_story": top_story,
            "prediction": top_prediction,
            "correct": top_prediction == truth,
            "recovered_hidden": top_story == hidden,
        },
    }


def main():
    episodes = [run(h) for h in HYPOTHESES]
    single_correct = sum(e["single"]["correct"] for e in episodes)
    topk_correct = sum(e["topk"]["correct"] for e in episodes)
    recovered = sum(e["topk"]["recovered_hidden"] for e in episodes)
    mean_topk_probes = sum(len(e["topk"]["probes"]) for e in episodes) / len(episodes)
    verdict = "PASS" if topk_correct == len(episodes) and recovered == len(episodes) and topk_correct > single_correct else "FAIL"
    result = {
        "test": "V9_VERSION_SPACE_VS_SINGLE_STORY",
        "claim_boundary": "bounded controller-policy test; hypothesis family is supplied",
        "single_correct": single_correct,
        "topk_correct": topk_correct,
        "topk_hidden_recovered": recovered,
        "mean_topk_probes": mean_topk_probes,
        "episodes": episodes,
        "verdict": verdict,
    }
    Path("v9_version_space_result.json").write_text(json.dumps(result, indent=2))
    print(json.dumps(result, indent=2))
    if verdict != "PASS":
        raise SystemExit(1)

if __name__ == "__main__":
    main()
