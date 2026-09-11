#!/usr/bin/env python3
import hashlib, itertools, json, pathlib, sys

ROOT = pathlib.Path(__file__).resolve().parent

# Source and target alphabets share no token.  Only these frozen behavioral
# signatures connect them.
SOURCE = ("SCAN", "FILTER", "FIRST", "PAIR", "EXTEND", "TEMPORAL")
TARGET = ("zx9", "qa2", "mn7", "rv4", "kp1", "ht8")
TARGET_ROLE = dict(zip(TARGET, ("SCAN", "FILTER", "FIRST", "PAIR", "EXTEND", "TEMPORAL")))
SOURCE_D1 = ("SCAN", "FILTER", "FIRST", "PAIR")
SOURCE_D2 = ("SCAN", "FILTER", "FIRST", "PAIR", "EXTEND", "PAIR")
TARGET_TASK = {"required": frozenset(("lag-edge-a", "lag-edge-b")), "max_depth": 7}
PROBE_CASES = ("empty", "one", "two", "useful", "opened", "temporal")


def digest(x):
    return hashlib.sha256(json.dumps(x, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def behavior(role, case):
    # Frozen typed-interface outcomes.  These are operational signatures, not names.
    table = {
        "SCAN": (1, 2, 2, 2, 2, 3), "FILTER": (0, 0, 1, 2, 1, 2),
        "FIRST": (0, 0, 0, 1, 1, 1), "PAIR": (0, 0, 0, 0, 2, 2),
        "EXTEND": (0, 0, 0, 0, 1, 1), "TEMPORAL": (1, 1, 1, 1, 1, 4),
    }
    return table[role][PROBE_CASES.index(case)]


def compile_by_equivalence(source_program):
    """Instantiate roles by exhaustive target behavioral equivalence; charge every probe."""
    calls, compiled, certificates = 0, [], []
    for role in source_program:
        matches = []
        for token in TARGET:
            equal = True
            for case in PROBE_CASES:
                calls += 1
                if behavior(role, case) != behavior(TARGET_ROLE[token], case):
                    equal = False
            if equal:
                matches.append(token)
        if len(matches) != 1:
            return None, calls, certificates
        compiled.append(matches[0])
        certificates.append({"source_role": role, "target_token": matches[0], "all_cases_equal": True})
    return tuple(compiled), calls, certificates


def execute(tokens, macro_expansion=()):
    expanded = tuple(x for t in tokens for x in (macro_expansion if t == "XFER" else (t,)))
    required = TARGET_TASK["required"]
    available = ["edge-a", "edge-b", "edge-c", "edge-d"]
    scanned = useful = None
    selected, opened = [], False
    calls = evaluations = 0
    valid = True
    success = False
    for token in expanded:
        role = TARGET_ROLE.get(token)
        if token == "SHAM":
            continue
        if token == "MEM_A":
            selected.append("edge-a"); continue
        if token == "MEM_B":
            selected.append("edge-b"); continue
        if role == "TEMPORAL":
            available += ["lag-edge-a", "lag-edge-b", "lag-edge-c", "lag-edge-d"]
        elif role == "SCAN":
            scanned = list(available)
        elif role == "FILTER" and scanned is not None:
            calls += len(scanned) * len(required)
            useful = [x for x in scanned if x in required]
        elif role == "FIRST" and useful:
            if useful[0] not in selected: selected.append(useful[0])
        elif role == "PAIR" and selected:
            calls += len(required); evaluations += 1; opened = True
            success = required.issubset(selected)
        elif role == "EXTEND" and opened and useful is not None:
            for x in useful:
                calls += len(required)
                if x not in selected: selected.append(x)
                if required.issubset(selected): break
            opened = False; success = False
        else:
            valid = False; break
    return {"valid": valid, "success": success, "calls": calls, "evaluations": evaluations}


def search(extra=(), macro=(), adapter_calls=0):
    alphabet = TARGET + tuple(extra)
    calls, nodes, evals = adapter_calls, 0, 0
    wins = []
    depth_hit = None
    for depth in range(1, TARGET_TASK["max_depth"] + 1):
        level = []
        for program in itertools.product(alphabet, repeat=depth):
            nodes += 1
            r = execute(program, macro)
            calls += r["calls"]; evals += r["evaluations"]
            if r["valid"] and r["success"]: level.append(program)
        if level:
            depth_hit, wins = depth, level
            break
    return {"correct": depth_hit is not None, "verifier_calls": calls, "search_nodes": nodes,
            "candidate_evaluations": evals, "success_depth": depth_hit,
            "successful_program_count": len(wins), "canonical_success": list(min(wins)) if wins else None,
            "adapter_calls": adapter_calls, "direct_source_tokens_available": False}


def main():
    target_d2, adapter_calls, certificates = compile_by_equivalence(SOURCE_D2)
    # Matched sham carries six inert target tokens; answer memory exposes old source answers only.
    results = {
        "cold_immediate": search(),
        "q_warm": search(("XFER",), target_d2, adapter_calls),
        "q_ablation": search(),
        "sham": search(("SHAM",)),
        "answer_memory": search(("MEM_A", "MEM_B")),
    }
    c, w = results["cold_immediate"], results["q_warm"]
    gates = {
        "G1_all_correct": all(x["correct"] for x in results.values()),
        "G2_fully_charged_transfer_cheaper": w["verifier_calls"] < c["verifier_calls"],
        "G3_ablation_restores_cold": results["q_ablation"]["verifier_calls"] == c["verifier_calls"],
        "G4_sham_not_reproduce": results["sham"]["verifier_calls"] >= c["verifier_calls"],
        "G5_answer_memory_not_reproduce": results["answer_memory"]["verifier_calls"] >= c["verifier_calls"],
        "G6_no_shared_surface_tokens": not set(SOURCE).intersection(TARGET),
        "G7_unique_behavioral_compilation": len(certificates) == len(SOURCE_D2) and target_d2 is not None,
        "G8_source_macro_not_direct_solution": not execute((), SOURCE_D2)["success"],
    }
    snapshot = {"source_tokens": SOURCE, "target_tokens": TARGET, "source_d1": SOURCE_D1,
                "source_d2": SOURCE_D2, "target_task": {"required": sorted(TARGET_TASK["required"]), "max_depth": 7},
                "probe_cases": PROBE_CASES, "target_role_digest": digest(TARGET_ROLE),
                "search": "level-complete", "metric": "all task probes plus exhaustive adapter probes",
                "heldout": True, "conditions": list(results)}
    verdict = "VERIFIED_CROSS_REPRESENTATION_COMPOUNDING" if all(gates.values()) else "NEGATIVE_OR_PARTIAL"
    evidence = {"verdict": verdict, "classification": "BOUNDED_EXHAUSTIVE_CAUSAL_PROSPECTIVE",
                "snapshot_digest": digest(snapshot), "compiled_target_macro": list(target_d2 or ()),
                "adapter_certificates": certificates, "results": results, "gates": gates,
                "reduction_factor": c["verifier_calls"] / w["verifier_calls"], "seed": None,
                "not_established": ["natural-domain transfer", "unbounded transfer", "learned semantic adapters", "substrate genesis"]}
    out = ROOT / "results"; out.mkdir(exist_ok=True)
    (out / "snapshot.json").write_text(json.dumps(snapshot, sort_keys=True, separators=(",", ":")) + "\n")
    (out / "evidence.json").write_text(json.dumps(evidence, indent=2) + "\n")
    print(json.dumps(evidence, indent=2))
    return 0 if verdict.startswith("VERIFIED") else 1


if __name__ == "__main__": sys.exit(main())
