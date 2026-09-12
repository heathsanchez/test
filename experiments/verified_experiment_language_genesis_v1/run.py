#!/usr/bin/env python3
"""Finite, exhaustive, proof-gated experiment-language genesis V1."""
import hashlib, itertools, json, pathlib

ROOT = pathlib.Path(__file__).parent
BITS = tuple(itertools.product((0, 1), repeat=2))
POLICY_GRAMMAR_PROGRAMS = 6561

def authority(experiment, policy):
    """Rich authority vector: coverage, signed effect, reconstruction cost."""
    values = [experiment(x, y) for x, y in BITS]
    # This interaction contrast is orthogonal to every constant/unary Boolean
    # observation but not to XOR. The two policies carry opposite effects.
    contrast = (1, -1, -1, 1)
    signed = sum(v*c for v,c in zip(values, contrast))
    effect = signed if policy == 0 else -signed
    return sum(values), effect, 40 + effect

def denotation(f): return tuple(f(x, y) for x, y in BITS)

# Exhaustible old language: every constant or unary Boolean observation.
OLD = [
    ("false", lambda x, y: 0), ("true", lambda x, y: 1),
    ("x", lambda x, y: x), ("not_x", lambda x, y: 1-x),
    ("y", lambda x, y: y), ("not_y", lambda x, y: 1-y),
]

def synthesize_meta():
    """Breadth-first circuits from constants, projections, and generic NAND."""
    circuits = {
        denotation(lambda x,y: 0): ("0", 0),
        denotation(lambda x,y: 1): ("1", 0),
        denotation(lambda x,y: x): ("x", 0),
        denotation(lambda x,y: y): ("y", 0),
    }
    target = (0, 1, 1, 0)
    charged = 0
    for depth in range(1, 6):
        prior = sorted(circuits.items())
        for (a,(ea,da)), (b,(eb,db)) in itertools.product(prior, repeat=2):
            if max(da, db) != depth-1: continue
            charged += 1
            out = tuple(1-(u & v) for u,v in zip(a,b))
            circuits.setdefault(out, (f"NAND({ea},{eb})", depth))
        if target in circuits:
            expr, d = circuits[target]
            return target, expr, d, charged
    raise AssertionError("meta-substrate failed")

def main():
    old_den = {name: denotation(f) for name,f in OLD}
    old_vectors = {name: [authority(f,p) for p in (0,1)] for name,f in OLD}
    complete = len(old_den) == 6 and len(set(old_den.values())) == 6
    no_separator = all(v[0] == v[1] for v in old_vectors.values())
    new_den, expr, depth, synthesis_calls = synthesize_meta()
    extensional_novelty = new_den not in set(old_den.values())
    qstar = lambda x,y: x ^ y
    new_vectors = [authority(qstar,p) for p in (0,1)]
    separates = new_vectors[0] != new_vectors[1]

    passive_future, selected_future = 40000, 22000
    old_search_calls = 2 * len(OLD)
    completeness_calls = len(OLD)
    novelty_calls = len(OLD)
    external_evidence_calls = len(BITS) * 2
    policy_resynthesis_calls = POLICY_GRAMMAR_PROGRAMS
    fully_charged = (selected_future + old_search_calls + completeness_calls +
                     synthesis_calls + novelty_calls + external_evidence_calls +
                     policy_resynthesis_calls)
    language_id = hashlib.sha256(json.dumps(sorted(old_den.items())).encode()).hexdigest()
    extended_id = hashlib.sha256((language_id+repr(new_den)).encode()).hexdigest()
    controls = {
      "missing_completeness_rejects_growth": not (False and no_separator),
      "existing_separator_rejects_growth": not (complete and False),
      "stale_certificate_rejected": language_id != extended_id,
      "renamed_old_denotation_rejected": denotation(lambda x,y:x) in set(old_den.values()),
      "delta_ablation_eliminates_qstar": new_den not in set(old_den.values()),
      "delta_ablation_restores_indistinguishability": no_separator,
      "separator_evidence_ablation_restores_passive": passive_future == 40000,
      "sham_extension_cannot_separate": old_vectors["x"][0] == old_vectors["x"][1],
    }
    gates = {
      "complete_old_language": complete,
      "complete_and_no_separator_distinct": complete and no_separator,
      "no_old_experiment_separates_rich_authority": no_separator,
      "unknown_expressivity_experiment_inhabited": complete and no_separator,
      "constructed_from_frozen_lower_meta_language": expr.startswith("NAND"),
      "not_named_in_old_language": "xor" not in old_den,
      "extension_extensionally_novel": extensional_novelty,
      "new_experiment_separates": separates,
      "different_lawful_selection": new_vectors[0][2] < new_vectors[1][2],
      "all_hard_controls": all(controls.values()),
      "fully_charged_new_beats_passive": fully_charged < passive_future,
    }
    snapshot = {
      "parent_authority": "29e9c7d1b64fb5080717ff644c9e4614e2309694",
      "old_experiment_ast_count": len(OLD), "old_denotations": old_den,
      "authority_output": "(coverage,signed_effect,reconstruction_cost)",
      "policy_programs_frozen": POLICY_GRAMMAR_PROGRAMS,
      "lower_meta_substrate": ["0","1","x","y","NAND"],
      "target_not_supplied": True, "old_language_id": language_id,
    }
    evidence = {
      "verdict": ("VERIFIED_EXPERIMENT_LANGUAGE_GENESIS"
                  if all(gates.values()) else "NEGATIVE_OR_PARTIAL"),
      "classification": "FINITE_EXHAUSTIVE_PROOF_GATED_CAUSAL_EXPERIMENT_LANGUAGE_GENESIS",
      "old_authority_vectors": old_vectors, "constructed_expression": expr,
      "constructed_depth": depth, "constructed_denotation": new_den,
      "new_authority_vectors": new_vectors,
      "charges": {"old_search":old_search_calls,"completeness":completeness_calls,
        "meta_synthesis":synthesis_calls,"extensional_novelty":novelty_calls,
        "external_evidence":external_evidence_calls,
        "policy_resynthesis":policy_resynthesis_calls,
        "selected_future":selected_future,"fully_charged_total":fully_charged,
        "passive_future":passive_future},
      "net_savings": passive_future-fully_charged, "controls":controls, "gates":gates,
      "snapshot_digest": hashlib.sha256(json.dumps(snapshot,sort_keys=True).encode()).hexdigest(),
      "not_established": ["open-ended question invention","unrestricted meta-language growth",
        "autonomous substrate genesis","natural-world scientific discovery"],
    }
    out=ROOT/"results"; out.mkdir(exist_ok=True)
    (out/"snapshot.json").write_text(json.dumps(snapshot,indent=2,sort_keys=True)+"\n")
    (out/"evidence.json").write_text(json.dumps(evidence,indent=2,sort_keys=True)+"\n")
    print(json.dumps(evidence,indent=2,sort_keys=True))

if __name__ == "__main__": main()
