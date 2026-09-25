#!/usr/bin/env python3
"""Stateful future-kernel probe for the exact q=0 Collatz RIGID return language.

Scientific question
-------------------
The existing return-switch algebra proves that every fixed return macro consumes
an exact 2-adic defect resource, while switches can recharge that resource.
This probe asks whether the recurrent classes seen after quotienting by return
control alone disappear when the consequential resource state is retained.

This is a bounded theorem-discovery experiment, NOT a Collatz proof.

For every completed source in the declared finite corpus:
  * build exact same-anchor first-return events inside the hereditary q=0 RIGID
    segment using the existing independently checked episode/certificate code;
  * compile each return word to its semantic affine map, not its syntax;
  * build observed transition graphs at four representation levels:
      CONTROL   = affine return-map identity only;
      OWN_FUEL  = CONTROL + exact active defect excess;
      OWN_V23    = CONTROL + active defect (v2 excess, v3);
      V2_VECTOR = CONTROL + exact v2 defect valuation against every observed
                  return map at the same anchor;
      V3_VECTOR = CONTROL + exact v3 defect valuation against every observed
                  return map at the same anchor;
      V23_VECTOR = CONTROL + exact (v2,v3) defect valuations against every
                   observed return map at the same anchor;
  * minimize each graph by the coarsest stable protected-future signature
    (exit flag + successor-class set);
  * compute the greatest post-fixed nonterminal kernel.  A nonempty kernel is
    only an abstraction-level recurrent possibility, never a Collatz orbit.

Exact resource law
------------------
For c=(A,B,D), C=2^D-A and Delta_c(m)=C*m-B.  Executing c gives

    2^D Delta_c(m') = A Delta_c(m),

so every nonzero active defect loses exactly D factors of 2.  For a switch
c -> d, the existing pairwise injection/separation law is rechecked on every
observed distinct transition.

A positive bounded separator is:
    CONTROL future-kernel nonempty, but a resource-aware future-kernel empty.

That would warrant the representation claim only on this frozen corpus.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from collections import defaultdict, Counter
from pathlib import Path

import collatz_q0_coalescence_component_audit as base
import collatz_q0_rigid_recharge_audit as ra


def v2z(x: int):
    x = abs(int(x))
    if x == 0:
        return None
    return (x & -x).bit_length() - 1


def vpz(x: int, p: int):
    x = abs(int(x))
    if x == 0:
        return None
    v = 0
    while x % p == 0:
        x //= p
        v += 1
    return v


def semantic_tuple(c):
    return (int(c["r"]), int(c["A"]), int(c["B"]), int(c["D"]))


def semantic_id(c):
    payload = ",".join(map(str, semantic_tuple(c))).encode()
    return hashlib.sha256(payload).hexdigest()[:20]


def defect(c, m: int) -> int:
    return int(c["C"]) * int(m) - int(c["B"])


def return_sequences(n: int, K: int):
    """Exact consecutive same-anchor returns inside the q0 RIGID segment."""
    starts, branches = ra.rigid_episode_segment(n, K)
    cache = {}
    last = {}
    out = defaultdict(list)
    for end in range(1, len(starts)):
        r = starts[end][1]
        if r in last:
            start = last[r]
            word = tuple(branches[start:end])
            c = cache.setdefault(word, ra.certificate(word))
            m0 = starts[start][2]
            m1 = starts[end][2]
            assert ra.admissible(c, m0)
            assert ra.replay(c, m0) == m1
            out[r].append({
                "source": n,
                "anchor": r,
                "k0": starts[start][0],
                "k1": starts[end][0],
                "m0": m0,
                "m1": m1,
                "cert": c,
            })
        last[r] = end

    for r, seq in out.items():
        for a, b in zip(seq, seq[1:]):
            assert a["m1"] == b["m0"], (n, r, a["m1"], b["m0"])
    return out


def completed_rigid_source(n: int, K: int) -> bool:
    survives, _ = base.survives_to_q0(n)
    if not survives or base.birth_status(n)[0] != "RIGID":
        return False
    k0 = n.bit_length()
    if k0 > K:
        return False
    # Exact completion criterion for this bounded corpus: the q0 symbolic
    # classifier must leave RIGID at some depth no later than K.
    for k in range(k0, K + 1):
        if ra.q0_status(k, n) != "RIGID":
            return True
    return False


def canonical(x):
    if isinstance(x, tuple):
        return [canonical(z) for z in x]
    if isinstance(x, list):
        return [canonical(z) for z in x]
    if isinstance(x, dict):
        return {str(k): canonical(v) for k, v in sorted(x.items(), key=lambda kv: str(kv[0]))}
    return x


def graph_from_occurrences(occurrences, patterns_by_anchor, mode: str):
    """Build observed quotient graph and exact exit set for one representation."""
    order = {
        r: sorted(patterns, key=lambda c: semantic_tuple(c))
        for r, patterns in patterns_by_anchor.items()
    }

    def state_key(event):
        c = event["cert"]
        pid = semantic_id(c)
        m = event["m0"]
        active = defect(c, m)
        av2 = v2z(active)
        assert av2 is None or av2 >= c["D"] + 1, (event["source"], semantic_tuple(c), m, av2)
        if mode == "CONTROL":
            return (pid,)
        excess = None if av2 is None else av2 - (c["D"] + 1)
        if mode == "OWN_FUEL":
            return (pid, excess)
        if mode == "OWN_V23":
            return (pid, excess, vpz(active, 3))
        if mode == "V2_VECTOR":
            vals = tuple(v2z(defect(d, m)) for d in order[event["anchor"]])
            return (pid, vals)
        if mode == "V3_VECTOR":
            vals = tuple(vpz(defect(d, m), 3) for d in order[event["anchor"]])
            return (pid, vals)
        if mode == "V23_VECTOR":
            vals = tuple((v2z(defect(d, m)), vpz(defect(d, m), 3))
                         for d in order[event["anchor"]])
            return (pid, vals)
        raise ValueError(mode)

    nodes = set()
    exits = set()
    succ = defaultdict(set)
    edge_occurrences = 0

    for seq in occurrences:
        keys = [state_key(e) for e in seq]
        nodes.update(keys)
        for a, b in zip(keys, keys[1:]):
            succ[a].add(b)
            edge_occurrences += 1
        if keys:
            exits.add(keys[-1])

    for n in nodes:
        succ.setdefault(n, set())
    return nodes, succ, exits, edge_occurrences


def refine_future_quotient(nodes, succ, exits):
    """Coarsest stable quotient by exit flag + successor-class set."""
    nodes = sorted(nodes, key=repr)
    classes = {n: int(n in exits) for n in nodes}
    rounds = 0
    while True:
        sigs = {}
        for n in nodes:
            sigs[n] = (n in exits, tuple(sorted({classes[s] for s in succ[n]})))
        uniq = {sig: i for i, sig in enumerate(sorted(set(sigs.values()), key=repr))}
        new = {n: uniq[sigs[n]] for n in nodes}
        rounds += 1
        if all(new[n] == classes[n] for n in nodes):
            classes = new
            break
        # Class numbers are arbitrary; stability is partition equality, not id equality.
        old_groups = {}
        new_groups = {}
        for n in nodes:
            old_groups.setdefault(classes[n], set()).add(n)
            new_groups.setdefault(new[n], set()).add(n)
        old_partition = {frozenset(v) for v in old_groups.values()}
        new_partition = {frozenset(v) for v in new_groups.values()}
        classes = new
        if old_partition == new_partition:
            break

    qnodes = set(classes.values())
    qsucc = {q: set() for q in qnodes}
    qexits = set()
    for n in nodes:
        q = classes[n]
        if n in exits:
            qexits.add(q)
        for s in succ[n]:
            qsucc[q].add(classes[s])
    return classes, qnodes, qsucc, qexits, rounds


def greatest_kernel(nodes, succ):
    live = set(nodes)
    rounds = []
    while True:
        dead = {n for n in live if not (succ[n] & live)}
        rounds.append(len(dead))
        if not dead:
            break
        live -= dead
    return live, rounds


def cycle_witness(kernel, succ):
    if not kernel:
        return None
    start = min(kernel, key=repr)
    seen = {}
    path = []
    cur = start
    while True:
        if cur in seen:
            return path[seen[cur]:] + [cur]
        seen[cur] = len(path)
        path.append(cur)
        nxt = sorted(succ[cur] & kernel, key=repr)
        if not nxt:
            return None
        cur = nxt[0]


def analyze(lo: int, hi: int, K: int, output: Path):
    patterns = defaultdict(dict)
    source_sequences = []
    counts = Counter()
    transport = Counter()
    incomplete = []

    start = max(3, lo)
    if start % 2 == 0:
        start += 1

    # First pass: freeze complete bounded source sequences and semantic pattern bank.
    for n in range(start, hi + 1, 2):
        survives, _ = base.survives_to_q0(n)
        if not survives or base.birth_status(n)[0] != "RIGID":
            continue
        counts["hereditary_birth_rigid"] += 1
        if not completed_rigid_source(n, K):
            incomplete.append(n)
            continue
        counts["completed_sources"] += 1
        seqs = return_sequences(n, K)
        for r, seq in seqs.items():
            if not seq:
                continue
            counts["anchor_sequences"] += 1
            counts["return_occurrences"] += len(seq)
            source_sequences.append(seq)
            for e in seq:
                c = e["cert"]
                patterns[r][semantic_id(c)] = c

    patterns_by_anchor = {
        r: tuple(patterns[r][k] for k in sorted(patterns[r]))
        for r in sorted(patterns)
    }
    counts["anchors"] = len(patterns_by_anchor)
    counts["semantic_patterns"] = sum(len(v) for v in patterns_by_anchor.values())

    # Exact local resource law and switch law audit across every retained edge.
    for seq in source_sequences:
        for e in seq:
            c, m0, m1 = e["cert"], e["m0"], e["m1"]
            d0 = defect(c, m0)
            d1 = defect(c, m1)
            assert (1 << c["D"]) * d1 == c["A"] * d0
            if d0 != 0:
                assert d1 != 0
                assert v2z(d1) == v2z(d0) - c["D"]
                transport["active_fuel_consumption_checks"] += 1
            else:
                transport["zero_active_defect"] += 1

        for a, b in zip(seq, seq[1:]):
            ca, cb = a["cert"], b["cert"]
            assert a["m1"] == b["m0"]
            if ca["q"] == cb["q"]:
                transport["same_pattern_transitions"] += 1
                continue
            same, disjoint, h, J = ra.separation(ca, cb)
            assert not same and disjoint and h is not None and J != 0
            da = defect(ca, b["m0"])
            assert v2z(da) == h
            db = defect(cb, b["m0"])
            vb = v2z(db)
            assert vb is None or vb >= cb["D"] + 1
            transport["distinct_switch_checks"] += 1

    results = {}
    for mode in ("CONTROL", "OWN_FUEL", "OWN_V23", "V2_VECTOR", "V3_VECTOR", "V23_VECTOR"):
        nodes, succ, exits, edge_occ = graph_from_occurrences(
            source_sequences, patterns_by_anchor, mode)
        kernel, prune = greatest_kernel(nodes, succ)
        classes, qnodes, qsucc, qexits, qrounds = refine_future_quotient(nodes, succ, exits)
        qkernel, qprune = greatest_kernel(qnodes, qsucc)
        results[mode] = {
            "raw_nodes": len(nodes),
            "raw_unique_edges": sum(len(v) for v in succ.values()),
            "edge_occurrences": edge_occ,
            "exit_nodes": len(exits),
            "raw_kernel_nodes": len(kernel),
            "raw_prune_rounds": prune,
            "raw_cycle_witness": canonical(cycle_witness(kernel, succ)),
            "future_classes": len(qnodes),
            "future_refinement_rounds": qrounds,
            "future_unique_edges": sum(len(v) for v in qsucc.values()),
            "future_exit_classes": len(qexits),
            "future_kernel_classes": len(qkernel),
            "future_prune_rounds": qprune,
            "future_cycle_witness": canonical(cycle_witness(qkernel, qsucc)),
        }

    control = results["CONTROL"]["future_kernel_classes"]
    own = results["OWN_FUEL"]["future_kernel_classes"]
    own_v23 = results["OWN_V23"]["future_kernel_classes"]
    v2 = results["V2_VECTOR"]["future_kernel_classes"]
    v3 = results["V3_VECTOR"]["future_kernel_classes"]
    v23 = results["V23_VECTOR"]["future_kernel_classes"]

    if incomplete:
        verdict = "RESIDUAL_INCOMPLETE_BOUNDED_CORPUS"
    elif control > 0 and own_v23 == 0:
        verdict = "PASS_BOUNDED_LOCAL_V23_RESOURCE_KILLS_CONTROL_FUTURE_KERNEL"
    elif control > 0 and v2 == 0:
        verdict = "PASS_BOUNDED_V2_RESOURCE_KILLS_CONTROL_FUTURE_KERNEL"
    elif control > 0 and v3 == 0:
        verdict = "PASS_BOUNDED_V3_VECTOR_KILLS_CONTROL_FUTURE_KERNEL"
    elif control > 0 and v23 == 0:
        verdict = "PASS_BOUNDED_V23_RESOURCE_KILLS_CONTROL_FUTURE_KERNEL"
    elif control > 0 and own < control:
        verdict = "PARTIAL_BOUNDED_RESOURCE_REFINEMENT"
    elif control == 0:
        verdict = "CONTROL_FUTURE_KERNEL_ALREADY_EMPTY"
    else:
        verdict = "RESIDUAL_RESOURCE_AWARE_FUTURE_KERNEL_SURVIVES"

    evidence = {
        "schema": "COLLATZ_STATEFUL_FUTURE_KERNEL_V0",
        "claim_boundary": (
            "Exact bounded comparison of return-control versus defect-resource "
            "future quotients on completed hereditary q0 RIGID sources only; "
            "not a Collatz proof, not universal quotient completeness."
        ),
        "source_range": [start, hi],
        "depth_cap": K,
        "counts": dict(sorted(counts.items())),
        "incomplete_sources": incomplete,
        "transport_audit": dict(sorted(transport.items())),
        "pattern_counts_by_anchor": {
            str(r): len(patterns_by_anchor[r]) for r in sorted(patterns_by_anchor)
        },
        "representations": results,
        "verdict": verdict,
    }
    body = json.dumps(evidence, sort_keys=True, separators=(",", ":"))
    evidence["closure_certificate"] = hashlib.sha256(body.encode()).hexdigest()
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(evidence, indent=2, sort_keys=True) + "\n")

    print("COUNTS", json.dumps(dict(sorted(counts.items())), sort_keys=True))
    print("INCOMPLETE_SOURCES", len(incomplete), incomplete[:40])
    print("TRANSPORT_AUDIT", json.dumps(dict(sorted(transport.items())), sort_keys=True))
    for mode in ("CONTROL", "OWN_FUEL", "OWN_V23", "V2_VECTOR", "V3_VECTOR", "V23_VECTOR"):
        print("KERNEL", mode, json.dumps(results[mode], sort_keys=True))
    print("VERDICT", verdict)
    print("CLOSURE_CERTIFICATE", evidence["closure_certificate"])
    return evidence


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--lo", type=int, default=3)
    ap.add_argument("--hi", type=int, default=8191)
    ap.add_argument("--K", type=int, default=128)
    ap.add_argument("--output", type=Path, default=Path("/tmp/collatz-stateful-future-kernel-v0.json"))
    a = ap.parse_args()
    analyze(a.lo, a.hi, a.K, a.output)


if __name__ == "__main__":
    main()
