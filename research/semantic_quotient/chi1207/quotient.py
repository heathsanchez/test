#!/usr/bin/env python3
"""Exhaustive *declared* parameter-name admission quotient; independent of chi."""
from itertools import product
import json

ALPHABET = ("a", "b", "c")
MAX_HISTORY, MAX_FUTURE = 4, 3
histories = [tuple(w) for n in range(MAX_HISTORY + 1) for w in product(ALPHABET, repeat=n)]
futures = [tuple(w) for n in range(MAX_FUTURE + 1) for w in product(ALPHABET, repeat=n)]

def state(word):
    seen = frozenset()
    for name in word:
        if name in seen:
            return ("INVALID",)
        seen = seen | {name}
    return ("VALID", tuple(sorted(seen)))

def observation(history, continuation):
    # All observable admission results (including empty continuation).
    return tuple(state(history + continuation[:n])[0] == "VALID"
                 for n in range(len(continuation) + 1))

classes = sorted({state(h) for h in histories}, key=str)
assert len(classes) == 2 ** len(ALPHABET) + 1, classes
same_count = distinct_count = 0
separators = {}
for i, a in enumerate(histories):
    for b in histories[i:]:
        qa, qb = state(a), state(b)
        same = qa == qb
        distinct = next((tail for tail in futures
                         if observation(a, tail) != observation(b, tail)), None)
        if same:
            assert distinct is None, ("FALSE_QUOTIENT", a, b, distinct)
            same_count += 1
        else:
            assert distinct is not None, ("INSUFFICIENT_DISTINCTIONS", a, b)
            distinct_count += 1
            separators.setdefault((str(qa), str(qb)), distinct)
# Show two *syntactically different* but semantically equivalent states.
assert state(("a", "b")) == state(("b", "a"))
assert observation(("a", "b"), ("c", "a")) == observation(("b", "a"), ("c", "a"))
report = {
    "schema": "metalogic.semantic-quotient.key-admission.v1",
    "alphabet": ALPHABET,
    "histories": len(histories),
    "future_sequences": len(futures),
    "equivalence_classes": len(classes),
    "equivalent_pairs": same_count,
    "distinct_pairs": distinct_count,
    "separated_pairs": distinct_count,
    "minimality_scope": "all key-admission continuations of length <= 3 in the frozen alphabet",
    "non_claims": [
        "Does not model all route-tree state or complete pattern grammar",
        "Does not prove automatic discovery of the semantic projection"
    ]
}
print("MATHGRAPH_QUOTIENT_MODEL " + json.dumps(report, sort_keys=True))
