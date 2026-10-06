#!/usr/bin/env python3
"""V83: residual-kernel test on the prospectively qualified V80 interface.

Parent V81 freezes the interface
  (affine law, nearest-centre id, extra owner bits, a mod 3^6)
and qualifies it on old V53 plus 186,624 fresh sources with zero one-step
collisions and zero zero-zero paths.

V83 asks the decisive rank question on that exact combined authority:
is the directed graph of RESIDUAL -> RESIDUAL interface transitions acyclic?
If yes, reverse sink elimination produces an explicit finite macro rank whose
every observed residual edge strictly decreases. If not, emit the first exact
recurrent SCC/cycle as the next protected obstruction.

This is finite qualified evidence, not an all-depth completeness theorem.
"""
from __future__ import annotations

from collections import defaultdict, deque
from contextlib import redirect_stdout
import hashlib
import io
import json

with redirect_stdout(io.StringIO()):
    import collatz_v80_fresh_interface_v81 as v81

PARENT_V81_QUAL = "cf152e580fce5a4a46ba8c98a2b83a16aacf91ee794a521bdf8eb6a20968c4cf"

assert v81.result["interface_survives"]
assert v81.result["zerozero_reclosure"]["zero_zero_paths"] == 0

trs = v81.old + v81.A["transitions"] + v81.B["transitions"]

nodes = set()
succ = defaultdict(set)
pred = defaultdict(set)
edge_rows = 0
terminal_rows = 0
for tr in trs:
    if not tr["src"]["residual"]:
        continue
    u = v81.interface(tr["src"], tr["t"])
    nodes.add(u)
    succ.setdefault(u, set())
    pred.setdefault(u, set())
    if tr["kind"] == "RESIDUAL":
        v = v81.interface(tr["dst"], tr["t"])
        nodes.add(v)
        succ[u].add(v)
        pred[v].add(u)
        succ.setdefault(v, set())
        pred.setdefault(v, set())
        edge_rows += 1
    else:
        terminal_rows += 1

def tarjan(nodes, succ):
    idx = 0
    ind = {}
    low = {}
    stack = []
    on = set()
    comps = []

    def visit(v):
        nonlocal idx
        ind[v] = low[v] = idx
        idx += 1
        stack.append(v)
        on.add(v)
        for w in succ[v]:
            if w not in ind:
                visit(w)
                low[v] = min(low[v], low[w])
            elif w in on:
                low[v] = min(low[v], ind[w]
                )
        if low[v] == ind[v]:
            cc = []
            while True:
                w = stack.pop()
                on.remove(w)
                cc.append(w)
                if w == v:
                    break
            comps.append(cc)

    for v in sorted(nodes, key=repr):
        if v not in ind:
            visit(v)

    recurrent = []
    for cc in comps:
        cyc = len(cc) > 1 or any(v in succ[v] for v in cc)
        if cyc:
            recurrent.append(cc)
    recurrent.sort(key=lambda c: (-len(c), repr(sorted(c, key=repr)[0])))
    return comps, recurrent

def elimination_rank(nodes, succ, pred):
    outdeg = {x: len(succ[x]) for x in nodes}
    q = deque(sorted((x for x in nodes if outdeg[x] == 0), key=repr))
    rank = {}
    layers = []
    layer = 0
    current = list(q)
    q.clear()

    while current:
        layers.append(len(current))
        nextset = set()
        for x in current:
            rank[x] = layer
            for p in pred[x]:
                if p in rank:
                    continue
                outdeg[p] -= 1
                if outdeg[p] == 0:
                    nextset.add(p)
        current = sorted(nextset, key=repr)
        layer += 1

    residual = nodes - rank.keys()
    return rank, residual, layers

def find_cycle(component, succ):
    C = set(component)
    seen = set()
    stack = []
    pos = {}

    def dfs(v):
        seen.add(v)
        pos[v] = len(stack)
        stack.append(v)
        for w in sorted(succ[v] & C, key=repr):
            if w in pos:
                i = pos[w]
                return stack[i:] + [w]
            if w not in seen:
                z = dfs(w)
                if z is not None:
                    return z
        stack.pop()
        pos.pop(v, None)
        return None

    for v in sorted(C, key=repr):
        if v not in seen:
            z = dfs(v)
            if z is not None:
                return z
    return None

comps, recurrent = tarjan(nodes, succ)
rank, leftover, layers = elimination_rank(nodes, succ, pred)

edge_rank_violations = []
if not recurrent:
    for u in nodes:
        for v in succ[u]:
            if not rank[v] < rank[u]:
                edge_rank_violations.append((u, v, rank[u], rank[v]))
                if len(edge_rank_violations) >= 20:
                    break
        if edge_rank_violations:
            break

first_scc = None
first_cycle = None
if recurrent:
    cc = recurrent[0]
    first_scc = [repr(x) for x in sorted(cc, key=repr)[:50]]
    cyc = find_cycle(cc, succ)
    if cyc is not None:
        first_cycle = [repr(x) for x in cyc[:100]]

rank_payload = sorted((repr(k), v) for k, v in rank.items())
rank_sha = hashlib.sha256(
    json.dumps(rank_payload, separators=(",", ":")).encode()
).hexdigest()

result = {
    "schema": "COLLATZ_V82_INTERFACE_KERNEL_V83",
    "parent_v81_qualification_sha256": PARENT_V81_QUAL,
    "combined_transition_rows": len(trs),
    "interface_nodes": len(nodes),
    "residual_edge_rows": edge_rows,
    "deduplicated_residual_edges": sum(len(v) for v in succ.values()),
    "terminal_transition_rows": terminal_rows,
    "scc_count": len(comps),
    "recurrent_sccs": len(recurrent),
    "largest_recurrent_scc": max((len(c) for c in recurrent), default=0),
    "eliminated_nodes": len(rank),
    "leftover_nodes": len(leftover),
    "elimination_layers": layers,
    "max_rank": max(rank.values(), default=None),
    "rank_sha256": rank_sha,
    "edge_rank_violations": [
        [repr(u), repr(v), ru, rv]
        for u, v, ru, rv in edge_rank_violations
    ],
    "first_recurrent_scc": first_scc,
    "first_cycle": first_cycle,
    "status": (
        "FINITE_INTERFACE_KERNEL_ACYCLIC"
        if not recurrent and not edge_rank_violations
        else "RECURRENT_INTERFACE_CELL_EMITTED"
    ),
    "interpretation": (
        "If acyclic, the prospectively qualified interface carries an explicit "
        "finite macro rank on the combined old+fresh authority. Universal Collatz "
        "still requires proving every lawful ZeroTailLive macro transition factors "
        "through this interface and obeys the same transition/rank law."
    ),
    "global_collatz": "UNKNOWN",
    "qed": False,
}
result["certificate_sha256"] = hashlib.sha256(
    json.dumps(result, sort_keys=True, separators=(",", ":")).encode()
).hexdigest()
print(json.dumps(result, indent=2, sort_keys=True))
