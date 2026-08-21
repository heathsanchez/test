#!/usr/bin/env python3
"""Developmental controller pilot v1.

Purpose: isolate cycle policy before introducing an LLM.
A sealed world contains a hidden 6-bit "representation". Experiments return
verified parity constraints over microscopic facets. No single residual normally
identifies the representation; the accumulated history does.

We compare four controllers:
  serial_latest : chases only the latest residual (history discarded)
  no_join       : probes but never synthesizes the history
  join_every    : globally joins after every probe
  proposed      : two probes -> JOIN -> version-space update -> next separator

JOIN here is exact GF(2)-constraint integration, deliberately deterministic.
The point of v1 is controller cadence, not semantic invention. A later v2 can
replace JOIN / candidate proposal with an LLM while keeping the verifier fixed.
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


def best_separator(candidates, used_masks):
    """Choose a probe that most evenly splits the current version space."""
    best = None
    best_score = None
    for mask in ALL_MASKS:
        if mask in used_masks:
            continue
        ones = sum(parity(s, mask) for s in candidates)
        zeros = len(candidates) - ones
        if not ones or not zeros:
            continue
        score = abs(ones - zeros)
        key = (score, sum(mask), mask)
        if best_score is None or key < best_score:
            best_score = key
            best = mask
    if best is None:
        # Any unused probe is fine once the version space is singleton.
        best = next((m for m in ALL_MASKS if m not in used_masks), ALL_MASKS[0])
    return best


def deterministic_probe(index, used_masks):
    # Diverse fixed probe schedule for pre-JOIN / non-JOIN arms.
    ordered = sorted(ALL_MASKS, key=lambda m: (sum(m), m))
    for offset in range(len(ordered)):
        mask = ordered[(index + 7 * offset) % len(ordered)]
        if mask not in used_masks:
            return mask
    return ordered[0]


@dataclass
class EpisodeResult:
    controller: str
    solved: bool
    cycles: int
    probes: int
    join_calls: int
    false_promotions: int
    final_version_space: int
    trace: list


def run_episode(hidden, controller, max_cycles=4, probes_per_cycle=2):
    constraints = []
    used = set()
    current_vs = ALL_STATES
    join_calls = 0
    false_promotions = 0
    trace = []
    probe_index = 0

    # Start with deliberately uninformative old-regime representative.
    candidate = (0,) * N_BITS

    for cycle in range(1, max_cycles + 1):
        # Candidate promotion is always externally checked.
        verified = candidate == hidden
        trace.append({"cycle": cycle, "event": "candidate_check", "candidate": candidate, "verified": verified})
        if verified:
            return EpisodeResult(controller, True, cycle - 1, len(constraints), join_calls,
                                 false_promotions, len(current_vs), trace)
        false_promotions += 1

        for _ in range(probes_per_cycle):
            if controller in ("proposed", "join_every") and len(current_vs) > 1 and join_calls > 0:
                mask = best_separator(current_vs, used)
            else:
                mask = deterministic_probe(probe_index, used)
            probe_index += 1
            used.add(mask)
            value = parity(hidden, mask)
            observation = (mask, value)

            if controller == "serial_latest":
                # Deliberately discard all prior residual constraints.
                constraints = [observation]
                local_vs = version_space(constraints)
                candidate = local_vs[0]
                current_vs = local_vs
            else:
                constraints.append(observation)

            trace.append({"cycle": cycle, "event": "probe", "mask": mask, "value": value})

            if controller == "join_every":
                current_vs = version_space(constraints)
                join_calls += 1
                candidate = current_vs[0]
                trace.append({"cycle": cycle, "event": "join", "version_space": len(current_vs)})

        if controller == "proposed":
            # Global synthesis only after a small residual field has accumulated.
            current_vs = version_space(constraints)
            join_calls += 1
            candidate = current_vs[0]
            trace.append({"cycle": cycle, "event": "join", "version_space": len(current_vs)})
        elif controller == "no_join":
            # History exists but is never globally integrated.
            candidate = tuple((cycle + i) & 1 for i in range(N_BITS))
            current_vs = ALL_STATES

    verified = candidate == hidden
    if not verified:
        false_promotions += 1
    trace.append({"cycle": max_cycles + 1, "event": "final_candidate_check", "candidate": candidate, "verified": verified})
    return EpisodeResult(controller, verified, max_cycles, len(constraints), join_calls,
                         false_promotions, len(current_vs), trace)


def summarize(results):
    by = {}
    for controller in sorted({r.controller for r in results}):
        rs = [r for r in results if r.controller == controller]
        solved = [r for r in rs if r.solved]
        by[controller] = {
            "episodes": len(rs),
            "solve_rate": sum(r.solved for r in rs) / len(rs),
            "mean_probes": statistics.mean(r.probes for r in rs),
            "mean_join_calls": statistics.mean(r.join_calls for r in rs),
            "mean_false_promotions": statistics.mean(r.false_promotions for r in rs),
            "median_final_version_space": statistics.median(r.final_version_space for r in rs),
            "mean_cycles_when_solved": statistics.mean(r.cycles for r in solved) if solved else None,
        }
    return by


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--worlds", type=int, default=256)
    ap.add_argument("--seed", type=int, default=20260821)
    ap.add_argument("--out", default="developmental_controller_pilot_v1_result.json")
    args = ap.parse_args()

    rng = random.Random(args.seed)
    controllers = ("serial_latest", "no_join", "join_every", "proposed")
    results = []
    for _ in range(args.worlds):
        hidden = ALL_STATES[rng.randrange(len(ALL_STATES))]
        for c in controllers:
            results.append(run_episode(hidden, c))

    summary = summarize(results)
    verdict = {
        "proposed_beats_serial_solve_rate": summary["proposed"]["solve_rate"] > summary["serial_latest"]["solve_rate"],
        "proposed_beats_no_join_solve_rate": summary["proposed"]["solve_rate"] > summary["no_join"]["solve_rate"],
        "proposed_uses_fewer_join_calls_than_join_every": summary["proposed"]["mean_join_calls"] < summary["join_every"]["mean_join_calls"],
        "proposed_full_solve": summary["proposed"]["solve_rate"] == 1.0,
    }
    payload = {
        "protocol": "DEVELOPMENTAL_CONTROLLER_PILOT_V1",
        "seed": args.seed,
        "worlds": args.worlds,
        "hidden_state_bits": N_BITS,
        "max_cycles": 4,
        "probes_per_cycle": 2,
        "join_semantics": "exact accumulation of verified GF(2) constraints",
        "summary": summary,
        "verdict": verdict,
        "all_gates_pass": all(verdict.values()),
        "claim_boundary": (
            "This tests controller cadence and the value of joining multiple verified residual constraints. "
            "JOIN is exact symbolic integration, not an LLM, and the candidate meta-language is finite and supplied. "
            "It does not establish semantic coagulation or open-ended representation invention."
        ),
        "example_proposed_trace": next(asdict(r) for r in results if r.controller == "proposed"),
    }
    with open(args.out, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2, sort_keys=True)
    print(json.dumps(payload, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
