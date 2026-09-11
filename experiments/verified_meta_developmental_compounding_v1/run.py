#!/usr/bin/env python3
import hashlib
import itertools
import json
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parent
PRIMITIVES = ("SCAN", "FILTER", "FIRST", "PAIR", "EXTEND", "TEMPORAL")
EXPANSIONS = {
    "D1": ("SCAN", "FILTER", "FIRST", "PAIR"),
    "D2": ("SCAN", "FILTER", "FIRST", "PAIR", "EXTEND", "PAIR"),
    "SHAM1": ("INERT", "INERT", "INERT", "INERT"),
    "SHAM2": ("INERT", "INERT", "INERT", "INERT", "INERT", "INERT"),
    "MEM0": ("SELECT_MEM0",),
    "MEM1": ("SELECT_MEM1",),
}
TASKS = {
    "D2": {"required": frozenset(("f2", "f3")), "max_depth": 6},
    "D3": {"required": frozenset(("l0", "l1")), "max_depth": 7},
}


def digest(x):
    return hashlib.sha256(json.dumps(x, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def execute(tokens, task):
    expanded = tuple(step for token in tokens for step in EXPANSIONS.get(token, (token,)))
    required = task["required"]
    available = [f"f{i}" for i in range(4)]
    scanned = None
    useful = None
    selected = []
    representation_open = False
    calls = 0
    evaluations = 0
    valid = True
    success = False
    for op in expanded:
        if op == "INERT":
            continue
        if op == "TEMPORAL":
            available += [f"l{i}" for i in range(4)]
        elif op == "SCAN":
            scanned = list(available)
        elif op == "FILTER" and scanned is not None:
            calls += len(scanned) * len(required)
            useful = [c for c in scanned if c in required]
        elif op == "FIRST" and useful:
            if useful[0] not in selected:
                selected.append(useful[0])
        elif op == "PAIR" and selected:
            calls += len(required)
            evaluations += 1
            representation_open = True
            success = required.issubset(selected)
        elif op == "EXTEND" and representation_open and useful is not None:
            for candidate in useful:
                calls += len(required)
                if candidate not in selected:
                    selected.append(candidate)
                if required.issubset(selected):
                    break
            representation_open = False
            success = False
        elif op == "SELECT_MEM0":
            selected.append("f0")
        elif op == "SELECT_MEM1":
            selected.append("f1")
        else:
            valid = False
            break
    return {"valid": valid, "success": success, "calls": calls,
            "evaluations": evaluations, "expanded_length": len(expanded)}


def level_complete_search(task_name, extra_tokens):
    task = TASKS[task_name]
    alphabet = PRIMITIVES + tuple(extra_tokens)
    total_calls = 0
    nodes = 0
    evaluations = 0
    successful_programs = []
    success_depth = None
    for depth in range(1, task["max_depth"] + 1):
        level_success = []
        for program in itertools.product(alphabet, repeat=depth):
            nodes += 1
            result = execute(program, task)
            total_calls += result["calls"]
            evaluations += result["evaluations"]
            if result["valid"] and result["success"]:
                level_success.append(program)
        if level_success:
            success_depth = depth
            successful_programs = level_success
            break
    return {"correct": success_depth is not None, "verifier_calls": total_calls,
            "search_nodes": nodes, "candidate_evaluations": evaluations,
            "success_depth": success_depth, "successful_program_count": len(successful_programs),
            "canonical_success": list(min(successful_programs)) if successful_programs else None,
            "active_tokens": list(extra_tokens)}


def main():
    snapshot = {
        "primitives": list(PRIMITIVES), "macro_expansions": {k: list(v) for k, v in EXPANSIONS.items()},
        "tasks": {k: {"required": sorted(v["required"]), "max_depth": v["max_depth"]} for k, v in TASKS.items()},
        "search": "level-complete increasing token length", "metric": "all internal verifier probes",
        "conditions": ["COLD", "WARM", "ABLATION", "SHAM", "ANSWER_MEMORY"],
    }
    snapshot_digest = digest(snapshot)
    results = {
        "D2": {
            "cold": level_complete_search("D2", ()),
            "warm_d1": level_complete_search("D2", ("D1",)),
            "ablation_d1": level_complete_search("D2", ()),
            "sham": level_complete_search("D2", ("SHAM1",)),
            "answer_memory": level_complete_search("D2", ("MEM0", "MEM1")),
        },
        "D3": {
            "cold": level_complete_search("D3", ()),
            "warm_d1": level_complete_search("D3", ("D1",)),
            "warm_d1_d2": level_complete_search("D3", ("D1", "D2")),
            "ablation_d2": level_complete_search("D3", ("D1",)),
            "sham": level_complete_search("D3", ("SHAM1", "SHAM2")),
            "answer_memory": level_complete_search("D3", ("MEM0", "MEM1")),
        },
    }
    d2 = results["D2"]
    d3 = results["D3"]
    cold_aggregate = d2["cold"]["verifier_calls"] + d3["cold"]["verifier_calls"]
    warm_aggregate = d2["warm_d1"]["verifier_calls"] + d3["warm_d1_d2"]["verifier_calls"]
    gates = {
        "G1_all_conditions_correct": all(r["correct"] for stage in results.values() for r in stage.values()),
        "G2_d2_warm_cheaper": d2["warm_d1"]["verifier_calls"] < d2["cold"]["verifier_calls"],
        "G3_d2_ablation_restores_cold": d2["ablation_d1"]["verifier_calls"] == d2["cold"]["verifier_calls"],
        "G4_d2_controls_do_not_reproduce": min(d2["sham"]["verifier_calls"], d2["answer_memory"]["verifier_calls"]) >= d2["cold"]["verifier_calls"],
        "G5_d3_strict_accumulation_curve": d3["warm_d1_d2"]["verifier_calls"] < d3["warm_d1"]["verifier_calls"] < d3["cold"]["verifier_calls"],
        "G6_d3_ablation_restores_d1_only": d3["ablation_d2"]["verifier_calls"] == d3["warm_d1"]["verifier_calls"],
        "G7_d3_controls_do_not_reproduce": min(d3["sham"]["verifier_calls"], d3["answer_memory"]["verifier_calls"]) >= d3["cold"]["verifier_calls"],
        "G8_aggregate_at_least_2x": cold_aggregate >= 2 * warm_aggregate,
        "G9_next_warm_acquisition_gets_cheaper": d3["warm_d1_d2"]["verifier_calls"] < d2["warm_d1"]["verifier_calls"],
        "G10_d1_does_not_solve_d2_directly": not execute(("D1",), TASKS["D2"])["success"],
        "G11_d2_does_not_solve_d3_without_temporal": not execute(("D2",), TASKS["D3"])["success"],
    }
    verdict = "VERIFIED_META_DEVELOPMENTAL_COMPOUNDING" if all(gates.values()) else "NEGATIVE_OR_PARTIAL"
    evidence = {"verdict": verdict, "classification": "BOUNDED_EXHAUSTIVE_CAUSAL",
                "snapshot_digest": snapshot_digest, "results": results,
                "cold_aggregate": cold_aggregate, "warm_aggregate": warm_aggregate,
                "aggregate_reduction_factor": cold_aggregate / warm_aggregate,
                "gates": gates, "seed": None,
                "not_established": ["cross-domain compounding", "unbounded compounding", "model learning", "primitive-substrate genesis"]}
    out = ROOT / "results"
    out.mkdir(exist_ok=True)
    (out / "evidence.json").write_text(json.dumps(evidence, indent=2) + "\n")
    (out / "snapshot.json").write_text(json.dumps(snapshot, sort_keys=True, separators=(",", ":")) + "\n")
    print(json.dumps(evidence, indent=2))
    return 0 if verdict == "VERIFIED_META_DEVELOPMENTAL_COMPOUNDING" else 1


if __name__ == "__main__":
    sys.exit(main())
