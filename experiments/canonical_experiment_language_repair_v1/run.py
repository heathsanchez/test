#!/usr/bin/env python3
"""Canonical Experiment-Language Repair V1: complete 16-denotation boundary."""
import hashlib, itertools, json, pathlib

ROOT = pathlib.Path(__file__).parent
H = tuple(range(4))
CONTRAST = (1, -1, -1, 1)

def bits(mask): return tuple((mask >> (3-i)) & 1 for i in H)
def separates(obs): return sum(a*b for a,b in zip(obs, CONTRAST)) != 0

def partition(obs):
    """Output-label invariant partition of the four histories."""
    cells = [tuple(i for i,v in enumerate(obs) if v == z) for z in (0,1)]
    return tuple(sorted(c for c in cells if c))

def refines(p, q):
    """p adds at least every distinction of q."""
    return all(any(set(a) <= set(b) for b in q) for a in p)

def main():
    denotations = [bits(i) for i in range(16)]
    repairs = [d for d in denotations if separates(d)]
    classes = {}
    for d in repairs: classes.setdefault(partition(d), []).append(d)
    ps = sorted(classes)
    minimal = [p for p in ps if not any(refines(p,q) and p != q for q in ps)]
    least = [p for p in ps if all(refines(q,p) for q in ps)]

    # Witnesses prove that successful repair does not determine unique growth.
    xor = partition((0,1,1,0))
    singleton = partition((0,0,0,1))
    incomparable = not refines(xor,singleton) and not refines(singleton,xor)
    factor_matrix = [[refines(a,b) for b in ps] for a in ps]
    outcome = ("CANONICAL_REPAIR" if len(least)==1 else
               "MULTIPLE_MINIMAL_REPAIRS" if minimal else
               "NO_REPAIR_IN_META_SUBSTRATE")
    gates = {
      "meta_boundary_complete": len(denotations)==16 and len(set(denotations))==16,
      "every_denotation_classified": len(repairs) + len([d for d in denotations if not separates(d)]) == 16,
      "output_recoding_quotiented": all(partition(d)==partition(tuple(1-x for x in d)) for d in denotations),
      "resolving_set_nonempty": bool(repairs),
      "all_factorizations_computed": len(factor_matrix)==len(ps) and all(len(r)==len(ps) for r in factor_matrix),
      "multiple_minimal_classes": len(minimal)>1,
      "no_least_repair": len(least)==0,
      "explicit_incomparable_witnesses": incomparable,
      "xor_is_minimal_not_least": xor in minimal and xor not in least,
      "choice_not_authorized": outcome=="MULTIPLE_MINIMAL_REPAIRS",
    }
    snap = {
      "parent_authority":"fa07d7d1b916730932e2c6b2ea17049950e53615",
      "carrier_histories":4,"declared_complete_boundary":"all 2^4 Boolean denotations",
      "repair_order":"partition refinement; output-label invariant",
      "separation_authority":"nonzero dot product with frozen contrast (1,-1,-1,1)",
    }
    ev = {
      "verdict": outcome, "classification":"FINITE_EXHAUSTIVE_CANONICAL_REPAIR_BOUNDARY",
      "denotations_examined":len(denotations),"resolving_denotations":len(repairs),
      "resolving_observational_classes":len(ps),"minimal_repair_classes":len(minimal),
      "least_repair_classes":len(least),
      "minimal_partitions":[list(map(list,p)) for p in minimal],
      "xor_partition":list(map(list,xor)),"incomparable_partition":list(map(list,singleton)),
      "factorization_matrix":factor_matrix,"gates":gates,
      "snapshot_digest":hashlib.sha256(json.dumps(snap,sort_keys=True).encode()).hexdigest(),
      "interpretation":"extension required; residual does not authorize choice among incomparable minimal repairs",
      "not_established":["canonical repair","initial repair object","meta-substrate inadequacy","unbounded universal property"],
    }
    out=ROOT/"results"; out.mkdir(exist_ok=True)
    (out/"snapshot.json").write_text(json.dumps(snap,indent=2,sort_keys=True)+"\n")
    (out/"evidence.json").write_text(json.dumps(ev,indent=2,sort_keys=True)+"\n")
    print(json.dumps(ev,indent=2,sort_keys=True))

if __name__=="__main__": main()
