"""FLASH V15 source-distinct sealed prospective protected task generator.

This was committed BEFORE the compiler or consumer. All generated positive
families have typed source semantics, not arbitrary uninspectable callbacks.
No protected data should be used to choose or specialize the source learner.
"""
from dataclasses import dataclass
from itertools import combinations
from random import Random

SEED=20261012
POSITIVE_COUNT=1024
FORMAT="forbidden_hypergraph.v1"
CONTRACT="typed-source-constructor-v1"

@dataclass(frozen=True)
class Task:
    name: str
    spec: dict
    expected_admission: bool

def positive_tasks():
    rng=Random(SEED)
    all_choices={n:[sum(1<<v for v in subset)
               for sz in (2,3,4) for subset in combinations(range(n),sz)] for n in (8,9)}
    for index in range(POSITIVE_COUNT):
        n=8 if index%5==0 else 9
        number=rng.randrange(3,12)
        chosen=rng.sample(all_choices[n],number)
        if index%7==0:chosen.extend([chosen[0],chosen[0]])  # canonical duplicates
        weights=[rng.randrange(1,16) for _ in range(n)]
        yield Task("protected_%04d"%index,dict(
            format=FORMAT,source_contract=CONTRACT,n=n,
            forbidden=chosen,weights=weights),True)

def negative_tasks():
    base=dict(format=FORMAT,source_contract=CONTRACT,n=9,
              forbidden=[0b0011,0b1100],weights=[1,2,3,4,5,6,7,8,9])
    def variant(name,**updates):
        item=base.copy();item.update(updates)
        return Task("invalid_"+name,item,False)
    yield variant("unknown_format",format="arbitrary_python_callback.v9")
    yield variant("counterfeit_origin",source_contract="untrusted-source-claim")
    yield variant("pattern_outside_width",forbidden=[1<<12])
    yield variant("empty_forbidden_pattern",forbidden=[0])
    yield variant("negative_weights",weights=[1,2,3,-4,5,6,7,8,9])
    yield variant("missing_weight",weights=[1,2,3,4,5])
    yield variant("unsigned_callback",callback="lambda mask: not bool(mask&3)")
    yield variant("noninteger_pattern",forbidden=["bad"])
    yield variant("invalid_n",n=17)
    yield variant("zero_weight",weights=[1,2,3,0,5,6,7,8,9])
    yield variant("falsified_source_bytes",source_sha256="0"*64)
    yield variant("nonmodular_callback",score_override="score plus bonus for pair")

def all_tasks():
    yield from positive_tasks()
    yield from negative_tasks()

def reference_feasible(mask,spec):
    return all((mask&p)!=p for p in spec["forbidden"])

def reference_score(mask,spec):
    return sum(w for i,w in enumerate(spec["weights"]) if (mask>>i)&1)
