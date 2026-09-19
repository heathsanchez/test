#!/usr/bin/env python3
"""
Developmental controller pilot v2: semantic coagulation test.

Protocol:
- Each sealed episode contains two residual statements from each of three source
  domains (kernel, SAIR, code). Exactly one latent causal role recurs once in
  every domain; distractors do not.
- A fourth, held-out domain (database) supplies three candidate residuals.
- The semantic JOIN prediction must choose the held-out residual with the same
  causal role.
- The frozen ChatGPT predictions below were produced from the evidence packets
  before the hidden labels were inspected in the creating session.
- Controls: TF-IDF lexical aggregation and chance (1/3).

This is a microbenchmark of heterogeneous semantic JOIN, not evidence of
open-ended scientific discovery. The ontology (three latent causal roles) and
surface statement families are supplied by the benchmark author.
"""
from __future__ import annotations
import json
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

PACKETS = [
  {
    "id": 0,
    "task": "Find the recurring causal pattern represented once in each source domain, then choose the database statement with the same causal pattern.",
    "evidence": [
      {"channel": "sair", "statement": "The learned route helps only under one family of source laws."},
      {"channel": "code", "statement": "The abstraction is reusable, but naive instantiation spends most effort rediscovering role bindings."},
      {"channel": "kernel", "statement": "The fast path succeeds only when the local frame has a bounded shape."},
      {"channel": "sair", "statement": "The useful constructor exists, yet enumerating its parameterization dominates solve time."},
      {"channel": "kernel", "statement": "Cache reuse exists, but identifying reusable objects dominates runtime."},
      {"channel": "code", "statement": "Literal repair identity collapses cases that tests distinguish structurally."}
    ],
    "database_candidates": [
      "The desired plan exists, yet enumerating equivalent normalized forms costs more than execution.",
      "Rows that share a coarse memoization signature later produce different query plans.",
      "The transformation works, but its activation predicate includes a counterexample."
    ]
  },
  {
    "id": 1,
    "task": "Find the recurring causal pattern represented once in each source domain, then choose the database statement with the same causal pattern.",
    "evidence": [
      {"channel": "kernel", "statement": "The optimization helps inside tiny closures but harms larger environments."},
      {"channel": "kernel", "statement": "Two states share the same cache key but later reduce to different normal forms."},
      {"channel": "code", "statement": "The correct AST transform is available, but reconstructing the full program state is more expensive than applying it."},
      {"channel": "sair", "statement": "A broader grammar can express the repair but explodes the candidate search."},
      {"channel": "code", "statement": "The same token pattern occurs in contexts with opposite executable consequences."},
      {"channel": "sair", "statement": "The current quotient identifies two implication cases that the finite model separates."}
    ],
    "database_candidates": [
      "A rewrite rule speeds one query family but becomes invalid under a different join context.",
      "Avoiding plan construction gives little benefit because discovering the reusable representative is itself expensive.",
      "Rows that share a coarse memoization signature later produce different query plans."
    ]
  },
  {
    "id": 2,
    "task": "Find the recurring causal pattern represented once in each source domain, then choose the database statement with the same causal pattern.",
    "evidence": [
      {"channel": "sair", "statement": "The grammar aliases witness configurations that require different constructors."},
      {"channel": "sair", "statement": "The useful constructor exists, yet enumerating its parameterization dominates solve time."},
      {"channel": "code", "statement": "The operation is valid, but the learned when-to-use rule is false."},
      {"channel": "kernel", "statement": "Source identity agrees while semantic equality disagrees downstream."},
      {"channel": "code", "statement": "The abstraction is reusable, but naive instantiation spends most effort rediscovering role bindings."},
      {"channel": "kernel", "statement": "Cache reuse exists, but identifying reusable objects dominates runtime."}
    ],
    "database_candidates": [
      "A rewrite rule speeds one query family but becomes invalid under a different join context.",
      "The desired plan exists, yet enumerating equivalent normalized forms costs more than execution.",
      "The index key aliases workloads with different downstream behavior."
    ]
  },
  {
    "id": 3,
    "task": "Find the recurring causal pattern represented once in each source domain, then choose the database statement with the same causal pattern.",
    "evidence": [
      {"channel": "kernel", "statement": "A pointer-level alias survives until a verifier-visible divergence."},
      {"channel": "sair", "statement": "A source class treated as uniform contains both reachable and unreachable targets."},
      {"channel": "code", "statement": "The correct AST transform is available, but reconstructing the full program state is more expensive than applying it."},
      {"channel": "kernel", "statement": "Computing the semantic key costs nearly as much as materializing the value."},
      {"channel": "code", "statement": "The same token pattern occurs in contexts with opposite executable consequences."},
      {"channel": "sair", "statement": "A constructor transfers on one residual basin but fails on a neighboring source class."}
    ],
    "database_candidates": [
      "The optimization is correct only for a restricted transaction shape and harms cases admitted by a broader trigger.",
      "Two requests collapse to one normalized cache class even though execution distinguishes them.",
      "The cached plan is reusable, but computing its canonical fingerprint dominates planning time."
    ]
  },
  {
    "id": 4,
    "task": "Find the recurring causal pattern represented once in each source domain, then choose the database statement with the same causal pattern.",
    "evidence": [
      {"channel": "kernel", "statement": "Source identity agrees while semantic equality disagrees downstream."},
      {"channel": "kernel", "statement": "Computing the semantic key costs nearly as much as materializing the value."},
      {"channel": "code", "statement": "The correct AST transform is available, but reconstructing the full program state is more expensive than applying it."},
      {"channel": "sair", "statement": "A constructor transfers on one residual basin but fails on a neighboring source class."},
      {"channel": "code", "statement": "Two repair sites look identical lexically but require different AST-role edits."},
      {"channel": "sair", "statement": "A source class treated as uniform contains both reachable and unreachable targets."}
    ],
    "database_candidates": [
      "The cached plan is reusable, but computing its canonical fingerprint dominates planning time.",
      "Rows that share a coarse memoization signature later produce different query plans.",
      "The transformation works, but its activation predicate includes a counterexample."
    ]
  },
  {
    "id": 5,
    "task": "Find the recurring causal pattern represented once in each source domain, then choose the database statement with the same causal pattern.",
    "evidence": [
      {"channel": "sair", "statement": "The learned route helps only under one family of source laws."},
      {"channel": "code", "statement": "The patch repairs Requests but breaks a Django case inside the learned activation region."},
      {"channel": "kernel", "statement": "The fast path succeeds only when the local frame has a bounded shape."},
      {"channel": "code", "statement": "A generic repair search finds the edit only after exploring many equivalent syntax variants."},
      {"channel": "sair", "statement": "A source class treated as uniform contains both reachable and unreachable targets."},
      {"channel": "kernel", "statement": "A pointer-level alias survives until a verifier-visible divergence."}
    ],
    "database_candidates": [
      "Two requests collapse to one normalized cache class even though execution distinguishes them.",
      "A rewrite rule speeds one query family but becomes invalid under a different join context.",
      "The cached plan is reusable, but computing its canonical fingerprint dominates planning time."
    ]
  },
  {
    "id": 6,
    "task": "Find the recurring causal pattern represented once in each source domain, then choose the database statement with the same causal pattern.",
    "evidence": [
      {"channel": "code", "statement": "The same token pattern occurs in contexts with opposite executable consequences."},
      {"channel": "kernel", "statement": "The rewrite is valid in one demand context and unsound when that context changes."},
      {"channel": "code", "statement": "The correct AST transform is available, but reconstructing the full program state is more expensive than applying it."},
      {"channel": "kernel", "statement": "Cache reuse exists, but identifying reusable objects dominates runtime."},
      {"channel": "sair", "statement": "The useful constructor exists, yet enumerating its parameterization dominates solve time."},
      {"channel": "sair", "statement": "A source class treated as uniform contains both reachable and unreachable targets."}
    ],
    "database_candidates": [
      "Rows that share a coarse memoization signature later produce different query plans.",
      "A rewrite rule speeds one query family but becomes invalid under a different join context.",
      "The desired plan exists, yet enumerating equivalent normalized forms costs more than execution."
    ]
  },
  {
    "id": 7,
    "task": "Find the recurring causal pattern represented once in each source domain, then choose the database statement with the same causal pattern.",
    "evidence": [
      {"channel": "sair", "statement": "A source class treated as uniform contains both reachable and unreachable targets."},
      {"channel": "kernel", "statement": "The optimization helps inside tiny closures but harms larger environments."},
      {"channel": "code", "statement": "Two repair sites look identical lexically but require different AST-role edits."},
      {"channel": "code", "statement": "A generic repair search finds the edit only after exploring many equivalent syntax variants."},
      {"channel": "sair", "statement": "The useful constructor exists, yet enumerating its parameterization dominates solve time."},
      {"channel": "kernel", "statement": "A pointer-level alias survives until a verifier-visible divergence."}
    ],
    "database_candidates": [
      "The optimization is correct only for a restricted transaction shape and harms cases admitted by a broader trigger.",
      "Rows that share a coarse memoization signature later produce different query plans.",
      "Avoiding plan construction gives little benefit because discovering the reusable representative is itself expensive."
    ]
  }
]

HIDDEN = [
  {"target": "representation_cost", "correct_candidate": "The desired plan exists, yet enumerating equivalent normalized forms costs more than execution."},
  {"target": "missing_distinction", "correct_candidate": "Rows that share a coarse memoization signature later produce different query plans."},
  {"target": "representation_cost", "correct_candidate": "The desired plan exists, yet enumerating equivalent normalized forms costs more than execution."},
  {"target": "missing_distinction", "correct_candidate": "Two requests collapse to one normalized cache class even though execution distinguishes them."},
  {"target": "missing_distinction", "correct_candidate": "Rows that share a coarse memoization signature later produce different query plans."},
  {"target": "wrong_scope", "correct_candidate": "A rewrite rule speeds one query family but becomes invalid under a different join context."},
  {"target": "representation_cost", "correct_candidate": "The desired plan exists, yet enumerating equivalent normalized forms costs more than execution."},
  {"target": "missing_distinction", "correct_candidate": "Rows that share a coarse memoization signature later produce different query plans."}
]

FROZEN_SEMANTIC_JOIN = [
  "The desired plan exists, yet enumerating equivalent normalized forms costs more than execution.",
  "Rows that share a coarse memoization signature later produce different query plans.",
  "The desired plan exists, yet enumerating equivalent normalized forms costs more than execution.",
  "Two requests collapse to one normalized cache class even though execution distinguishes them.",
  "Rows that share a coarse memoization signature later produce different query plans.",
  "A rewrite rule speeds one query family but becomes invalid under a different join context.",
  "The desired plan exists, yet enumerating equivalent normalized forms costs more than execution.",
  "Rows that share a coarse memoization signature later produce different query plans."
]

def lexical_baseline(packet):
    evidence = [e["statement"] for e in packet["evidence"]]
    candidates = packet["database_candidates"]
    X = TfidfVectorizer(ngram_range=(1, 2), stop_words="english").fit_transform(evidence + candidates)
    sims = cosine_similarity(X[len(evidence):], X[:len(evidence)])
    scores = sims.sum(axis=1)
    return candidates[int(scores.argmax())]

def main():
    semantic = []
    lexical = []
    rows = []
    for p, h, pred in zip(PACKETS, HIDDEN, FROZEN_SEMANTIC_JOIN):
        lp = lexical_baseline(p)
        sc = pred == h["correct_candidate"]
        lc = lp == h["correct_candidate"]
        semantic.append(sc)
        lexical.append(lc)
        rows.append({
            "id": p["id"],
            "target_latent": h["target"],
            "semantic_prediction": pred,
            "lexical_prediction": lp,
            "correct_candidate": h["correct_candidate"],
            "semantic_correct": sc,
            "lexical_correct": lc,
        })
    out = {
        "protocol": "DEVELOPMENTAL_CONTROLLER_PILOT_V2_SEMANTIC_JOIN",
        "episodes": len(PACKETS),
        "semantic_join_correct": sum(semantic),
        "semantic_join_rate": sum(semantic) / len(semantic),
        "lexical_full_history_correct": sum(lexical),
        "lexical_full_history_rate": sum(lexical) / len(lexical),
        "chance_rate": 1 / 3,
        "semantic_beats_lexical": sum(semantic) > sum(lexical),
        "semantic_full_solve": all(semantic),
        "per_episode": rows,
        "claim_boundary": (
            "This establishes only that an LLM semantic join can outperform a lexical "
            "full-history baseline on a small sealed heterogeneous-language microbenchmark. "
            "The latent ontology and statement families are supplied, episodes are synthetic, "
            "and this does not establish autonomous history-to-specification, meta-language "
            "escape, or scientific discovery."
        ),
    }
    print(json.dumps(out, indent=2))
    with open("developmental_controller_pilot_v2_result.json", "w") as f:
        json.dump(out, f, indent=2)
    if not (out["semantic_beats_lexical"] and out["semantic_full_solve"]):
        raise SystemExit("v2 gates failed")

if __name__ == "__main__":
    main()
