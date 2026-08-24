#!/usr/bin/env python3
"""Adversarial audit of Developmental Controller Pilot v1.

Question: does v1 establish a special causal value for JOIN, or mainly the value of
retaining and integrating multiple verified constraints?

The audit adds fair history-retaining controls that were absent from v1.
All controllers see the same sealed 6-bit worlds and parity observations.
"""
from __future__ import annotations

import argparse
import json
import random
import statistics
from dataclasses import dataclass, asdict
from itertools import product

N_BITS = 6
ALL_STATES = tuple(tuple(bits) for bits in product((0, 1), repeat=N_BITS))
ALL_MASKS = tuple(tuple(bits) for bits in product((0, 1), repeat=N_BITS) if any(bits))


def parity(state, mask):
    return sum(a * b for a, b in zip(state, mask)) & 1


def satisfies(state, constraints):
    return all(parity(state, mask) == value for mask, value in constraints)


def version_space(constraints):
    return tuple(s for s in ALL_STATES if satisfies(s, constraints))


def deterministic_probe(index, used_masks):
    ordered = sorted(ALL_MASKS, key=lambda m: (sum(m), m))
    for offset in range(len(ordered)):
        mask = ordered[(index + 7 * offset) % len(ordered)]
        if mask not in used_masks:
            return mask
    return ordered[0]


def best_separator(candidates, used_masks):
    best = None
    best_key = None
    for mask in ALL_MASKS:
        if mask in used_masks:
            continue
        ones = sum(parity(s, mask) for s in candidates)
        zeros = len(candidates) - ones
        if not ones or not zeros:
            continue
        key = (abs(ones - zeros), sum(mask), mask)
        if best_key is None or key < best_key:
            best_key = key
            best = mask
    return best or next((m for m in ALL_MASKS if m not in used_masks), ALL_MASKS[0])


@dataclass
class Result:
    controller: str
    solved: bool
    probes: int
    integration_calls: int
    false_promotions: int
    final_version_space: int
    trace: list


def run(hidden, controller, max_probes=8, batch_size=2):
    constraints = []
    used = set()
    current_vs = ALL_STATES
    candidate = (0,) * N_BITS
    integration_calls = 0
    false_promotions = 0
    trace = []

    for i in range(max_probes + 1):
        if candidate == hidden:
            return Result(controller, True, len(constraints), integration_calls,
                          false_promotions, len(current_vs), trace)
        false_promotions += 1
        if i == max_probes:
            break

        if controller in {"adaptive_incremental", "batch_join_2"} and len(current_vs) > 1 and constraints:
            mask = best_separator(current_vs, used)
        else:
            mask = deterministic_probe(i, used)
        used.add(mask)
        obs = (mask, parity(hidden, mask))
        constraints.append(obs)
        trace.append({"event": "probe", "i": i + 1, "mask": mask, "value": obs[1]})

        if controller == "serial_latest":
            current_vs = version_space([obs])
            candidate = current_vs[0]
            integration_calls += 1
        elif controller == "fixed_history_incremental":
            # Fair control: retain ALL evidence, fixed probe schedule, update exactly.
            current_vs = version_space(constraints)
            candidate = current_vs[0]
            integration_calls += 1
        elif controller == "adaptive_incremental":
            # Fair control: retain ALL evidence and choose separators adaptively.
            current_vs = version_space(constraints)
            candidate = current_vs[0]
            integration_calls += 1
        elif controller == "batch_join_2":
            # v1-style batching: only recompute after a small residual field accumulates.
            if len(constraints) % batch_size == 0:
                current_vs = version_space(constraints)
                candidate = current_vs[0]
                integration_calls += 1
                trace.append({"event": "join", "after_probes": len(constraints),
                              "version_space": len(current_vs)})
        else:
            raise ValueError(controller)

    return Result(controller, candidate == hidden, len(constraints), integration_calls,
                  false_promotions, len(current_vs), trace)


def summarize(rows):
    out = {}
    for c in sorted({r.controller for r in rows}):
        rs = [r for r in rows if r.controller == c]
        out[c] = {
            "episodes": len(rs),
            "solve_rate": sum(r.solved for r in rs) / len(rs),
            "mean_probes": statistics.mean(r.probes for r in rs),
            "mean_integration_calls": statistics.mean(r.integration_calls for r in rs),
            "mean_false_promotions": statistics.mean(r.false_promotions for r in rs),
            "median_final_version_space": statistics.median(r.final_version_space for r in rs),
        }
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--worlds", type=int, default=256)
    ap.add_argument("--seed", type=int, default=20260821)
    ap.add_argument("--out", default="developmental_controller_pilot_v1_adversarial_result.json")
    args = ap.parse_args()

    rng = random.Random(args.seed)
    controllers = (
        "serial_latest",
        "fixed_history_incremental",
        "adaptive_incremental",
        "batch_join_2",
    )
    rows = []
    for _ in range(args.worlds):
        hidden = ALL_STATES[rng.randrange(len(ALL_STATES))]
        for c in controllers:
            rows.append(run(hidden, c))

    s = summarize(rows)
    tests = {
        "history_retention_beats_latest_only":
            s["fixed_history_incremental"]["solve_rate"] > s["serial_latest"]["solve_rate"],
        "fair_incremental_history_full_solve":
            s["fixed_history_incremental"]["solve_rate"] == 1.0,
        "adaptive_incremental_full_solve":
            s["adaptive_incremental"]["solve_rate"] == 1.0,
        "batched_join_full_solve":
            s["batch_join_2"]["solve_rate"] == 1.0,
        "batching_reduces_integration_calls":
            s["batch_join_2"]["mean_integration_calls"] < s["adaptive_incremental"]["mean_integration_calls"],
    }

    # The key adversarial question. If a fair non-JOIN history control also solves
    # perfectly, v1 cannot identify a JOIN-specific causal effect; it identifies
    # history integration + useful batching.
    join_specific_effect_established = (
        s["batch_join_2"]["solve_rate"] > s["fixed_history_incremental"]["solve_rate"]
        or s["batch_join_2"]["mean_probes"] < s["adaptive_incremental"]["mean_probes"]
    )

    if all(tests.values()) and not join_specific_effect_established:
        verdict = "PARTIAL_V1_CADENCE_SURVIVES_JOIN_SPECIFIC_CLAIM_NOT_IDENTIFIED"
    elif all(tests.values()) and join_specific_effect_established:
        verdict = "PASS_JOIN_SPECIFIC_ADVANTAGE_SURVIVES_FAIR_HISTORY_CONTROLS"
    else:
        verdict = "FAIL_OR_INCONCLUSIVE"

    payload = {
        "protocol": "DEVELOPMENTAL_CONTROLLER_PILOT_V1_ADVERSARIAL_AUDIT",
        "seed": args.seed,
        "worlds": args.worlds,
        "summary": s,
        "tests": tests,
        "join_specific_effect_established": join_specific_effect_established,
        "verdict": verdict,
        "interpretation": (
            "This audit separates three effects conflated in v1: retaining history, exact integration of history, "
            "and batching expensive global synthesis. If fair incremental history controls solve as well as batched JOIN, "
            "the v1 result supports accumulated evidence and synthesis cadence, not a special semantic JOIN mechanism."
        ),
        "next_test": (
            "Use heterogeneous residuals whose shared latent explanation is not recoverable by direct accumulation in the "
            "original coordinate system. Compare (a) exact/local history retention, (b) LLM semantic JOIN, and (c) wrong/shuffled JOIN."
        ),
        "example_traces": {
            c: asdict(next(r for r in rows if r.controller == c)) for c in controllers
        },
    }
    with open(args.out, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2, sort_keys=True)
    print(json.dumps(payload, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
