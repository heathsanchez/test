#!/usr/bin/env python3
import itertools, json
from pathlib import Path

ROOT = Path(__file__).resolve().parent
E = json.loads((ROOT / "results/evidence.json").read_text())

def idx(bits):
    x = 0
    for b in bits:
        x = (x << 1) | b
    return x

def ev(mask, bits):
    return (mask >> idx(bits)) & 1

def target(m, i):
    return int(i == 1)

def old(m, i):
    return (int(i == 0), int(i == m - 1))

def atom(kind, m, i):
    cls = [j for j in range(m) if old(m, j) == (0, 0)]
    if kind == "LEFT_EDGE_OF_CONFLICT_CLASS":
        return int(bool(cls) and i == min(cls))
    if kind == "RIGHT_EDGE_OF_CONFLICT_CLASS":
        return int(bool(cls) and i == max(cls))
    raise AssertionError(kind)

def errors(mask, m, kind=None):
    n = 0
    for i in range(m):
        bits = old(m, i) if kind is None else old(m, i) + (atom(kind, m, i),)
        n += ev(mask, bits) != target(m, i)
    return n

assert all(errors(mask, 4) > 0 for mask in range(16))
assert old(4, 1) == old(4, 2) == (0, 0)
assert target(4, 1) != target(4, 2)

q4 = {}
q5 = {}
for kind in ("LEFT_EDGE_OF_CONFLICT_CLASS", "RIGHT_EDGE_OF_CONFLICT_CLASS"):
    q4[kind] = [mask for mask in range(256) if errors(mask, 4, kind) == 0]
    q5[kind] = [mask for mask in range(256) if errors(mask, 5, kind) == 0]
    assert q4[kind]

assert set(q4["LEFT_EDGE_OF_CONFLICT_CLASS"]) & set(q5["LEFT_EDGE_OF_CONFLICT_CLASS"])
assert not (
    set(q4["RIGHT_EDGE_OF_CONFLICT_CLASS"])
    & set(q5["RIGHT_EDGE_OF_CONFLICT_CLASS"])
)

kind = E["selected_refinement"]
mask = E["selected_program"]["operator_id"]
assert kind == "LEFT_EDGE_OF_CONFLICT_CLASS"

for m in (4, 5, 6, 7):
    assert errors(mask, m, kind) == 0

for F, L, X in itertools.product((0, 1), repeat=3):
    assert ev(mask, (F, L, X)) == X

assert E["selected_program"]["dependency_indices"] == [2]

for sham in ("duplicate", "constant"):
    best = 999
    for cand in range(256):
        er = 0
        for i in range(4):
            F, L = old(4, i)
            X = F if sham == "duplicate" else 0
            er += ev(cand, (F, L, X)) != target(4, i)
        best = min(best, er)
    assert best > 0

assert E["incomplete_search_control"]["growth_authorized"] is False
assert E["incomplete_search_control"]["required_outcome"] == "UNKNOWN"
assert all(E["gates"].values())
assert E["verdict"] == "QUALIFIED_RECURSIVE_ACTION_LANGUAGE_GENESIS"

print("INDEPENDENT_VERIFIER_PASS")
