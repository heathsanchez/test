#!/usr/bin/env python3
"""V81: prospective fresh-family qualification of the V80 contracted interface.

V80 froze the bounded one-step interface
  (affine law, nearest-centre id, extra owner bits, a mod 3^6)
on the V53 authority. This gate does not retune that interface.

Fresh sources are chosen before observing outcomes:
  * all 64 frozen depth-9 binary cells,
  * every ternary class a mod 3^6,
  * four deterministic primitive balanced length-10 motifs not present in V53.
The first two canonical motifs form fresh family A and the next two form B.

The gate checks:
  1. exact one-step functionality on A, on B, and on V53+A+B;
  2. transport on states already seen in V53;
  3. missing-centre/key or censoring separators;
  4. if the interface survives, three-switch zero-zero closure on the combined
     source-free graph through the frozen interface.

Bounded prospective qualification only. Global Collatz remains UNKNOWN.
"""
from __future__ import annotations

from collections import Counter, defaultdict
from contextlib import redirect_stdout
from fractions import Fraction
from itertools import product
import hashlib
import io
import json
import os
import sys

frozen = os.environ.get("V60_EXPERIMENTS_DIR")
if frozen:
    sys.path.insert(0, frozen)

# Import the complete frozen V53 authority unchanged.
with redirect_stdout(io.StringIO()):
    import collatz_crystal_nonpositive_budget_kernel_v53 as v53

PARENT_V80_QUAL = "f792cbf3e654b40066a8d9bd18aeceada78d958a5839a7497f1411decc0a11f9"

def rotations(s: str):
    return [s[i:] + s[:i] for i in range(len(s))]

def complement(s: str):
    return "".join("1" if c == "0" else "0" for c in s)

def primitive(s: str):
    n = len(s)
    return all(s != s[:d] * (n // d) for d in range(1, n) if n % d == 0)

def canonical_orbit_rep(s: str):
    orb = rotations(s) + rotations(complement(s))
    return s == min(orb)

def select_fresh_motifs():
    old = set(v53.MOTIFS.values())
    out = []
    for bits in product("01", repeat=10):
        s = "".join(bits)
        if s.count("1") != 5:
            continue
        if not primitive(s) or not canonical_orbit_rep(s):
            continue
        if s in old:
            continue
        out.append(s)
    assert len(out) >= 4
    return out[:4]

FRESH = select_fresh_motifs()
FRESH_A = tuple(FRESH[:2])
FRESH_B = tuple(FRESH[2:4])
assert set(FRESH).isdisjoint(v53.MOTIFS.values())

def law(row):
    return (int(row["A"]), int(row["B"]), int(row["P"]), int(row["D"]))

def interface(row, t: int):
    key = row["key"]
    # V80: affine law + canonical nearest-centre id + extra owner bits
    #      + exact ternary source class mod 3^6.
    return (law(row), key[3], key[5], int(t) % v53.MOD3)

def outcome(tr):
    if tr["kind"] == "EXIT":
        return ("EXIT",)
    d = tr["dst"]
    assert d is not None
    return (tr["kind"], interface(d, tr["t"]))

def build_source_transitions(motifs, tag):
    transitions = []
    stats = Counter()
    first_missing = None
    first_censored = None
    sources = 0

    for r in v53.v43.LIVE:
        for a in range(v53.MOD3):
            for idx, pattern in enumerate(motifs):
                t = v53.crt_parameter(r, a, pattern)
                n = v53.v25.N0 + v53.v25.NC * t
                name = f"{tag}-r{r}-a{a}-m{idx}-{pattern}"
                rr = v53.v40.actual_episode_returns(name, n, v53.CAP)
                sources += 1

                if rr["note"] == "ordinary exit before zero-tail":
                    stats["EXIT_PRE_ZERO"] += 1
                    continue

                stats["POST_ZERO_SOURCE"] += 1
                if rr["first_exit"] is None:
                    stats["SOURCE_CENSORED"] += 1
                    if first_censored is None:
                        first_censored = {
                            "name": name, "r": r, "a": a, "pattern": pattern,
                            "t": str(t), "source": str(n),
                        }

                by = defaultdict(list)
                for e in rr["events"]:
                    k = v53.reduced_key(e)
                    if k is None:
                        stats["MISSING_V80_KEY"] += 1
                        if first_missing is None:
                            first_missing = {
                                "name": name, "r": r, "a": a, "pattern": pattern,
                                "t": str(t), "source": str(n),
                                "anchor": e["anchor"], "depth": [e["k0"], e["k1"]],
                            }
                        continue
                    cl = v53.classify_event(e)
                    row = {
                        "source": n, "t": t, "pattern": pattern,
                        "anchor": e["anchor"], "k0": e["k0"], "k1": e["k1"],
                        "key": k, "m0": e["m0"], "m1": e["m1"], **cl,
                    }
                    by[e["anchor"]].append(row)
                    stats["RETURN_ROWS"] += 1

                for anchor, es in by.items():
                    es.sort(key=lambda z: (z["k0"], z["k1"]))
                    for i, cur in enumerate(es):
                        if not cur["residual"]:
                            continue
                        if i + 1 < len(es):
                            nxt = es[i + 1]
                            transitions.append({
                                "t": t, "source": n, "pattern": pattern,
                                "anchor": anchor, "src": cur, "dst": nxt,
                                "kind": "RESIDUAL" if nxt["residual"] else "PROGRESS",
                            })
                            stats["TRANSITIONS"] += 1
                        else:
                            ex = rr["first_exit"]
                            if ex is not None and ex["depth"] >= cur["k1"]:
                                transitions.append({
                                    "t": t, "source": n, "pattern": pattern,
                                    "anchor": anchor, "src": cur, "dst": None,
                                    "kind": "EXIT",
                                })
                                stats["TRANSITIONS"] += 1
                            else:
                                stats["CENSORED_RESIDUAL_TAIL"] += 1
                                if first_censored is None:
                                    first_censored = {
                                        "name": name, "r": r, "a": a,
                                        "pattern": pattern, "t": str(t),
                                        "source": str(n), "anchor": anchor,
                                        "depth": [cur["k0"], cur["k1"]],
                                    }

    return {
        "motifs": list(motifs),
        "sources": sources,
        "transitions": transitions,
        "stats": dict(sorted(stats.items())),
        "first_missing_key": first_missing,
        "first_censored": first_censored,
    }

def functional(transitions):
    outs = defaultdict(set)
    first = {}
    for tr in transitions:
        s = interface(tr["src"], tr["t"])
        o = outcome(tr)
        outs[s].add(o)
        first.setdefault((s, o), tr)
    bad = [(s, os) for s, os in outs.items() if len(os) > 1]
    bad.sort(key=lambda z: repr(z[0]))
    witness = None
    if bad:
        s, os = bad[0]
        witness = {
            "state": repr(s),
            "outcomes": sorted(map(repr, os)),
            "rows": [
                {
                    "pattern": first[(s,o)].get("pattern"),
                    "t": str(first[(s,o)]["t"]),
                    "source": str(first[(s,o)]["source"]),
                    "kind": first[(s,o)]["kind"],
                    "src_depth": [
                        first[(s,o)]["src"]["k0"], first[(s,o)]["src"]["k1"]
                    ],
                    "outcome": repr(o),
                }
                for o in sorted(os, key=repr)[:6]
            ],
        }
    return {
        "states": len(outs),
        "collision_states": len(bad),
        "max_outcomes": max(map(len, outs.values()), default=0),
        "first_collision": witness,
    }

def frozen_map():
    outs = defaultdict(set)
    for tr in v53.transitions:
        if not tr["src"]["residual"]:
            continue
        outs[interface(tr["src"], tr["t"])].add(outcome(tr))
    assert all(len(x) == 1 for x in outs.values())
    return {k: next(iter(v)) for k,v in outs.items()}

def transport(fresh, oldmap):
    seen = matched = conflicted = unseen = 0
    first_conflict = None
    for tr in fresh:
        s = interface(tr["src"], tr["t"])
        o = outcome(tr)
        if s not in oldmap:
            unseen += 1
            continue
        seen += 1
        if oldmap[s] == o:
            matched += 1
        else:
            conflicted += 1
            if first_conflict is None:
                first_conflict = {
                    "state": repr(s),
                    "expected": repr(oldmap[s]),
                    "observed": repr(o),
                    "pattern": tr.get("pattern"),
                    "t": str(tr["t"]),
                    "source": str(tr["source"]),
                }
    return {
        "seen": seen, "matched": matched, "conflicted": conflicted,
        "unseen": unseen, "first_conflict": first_conflict,
    }

def centre(L):
    A,B,P,D = L
    assert A % 2 == 1 and P == 1 << D and P != A
    return Fraction(B, P-A)

def v2z(x):
    x = abs(x)
    assert x
    return (x & -x).bit_length()-1

def rat_v2(q):
    assert q
    return v2z(q.numerator)-v2z(q.denominator)

def residue(q, bits):
    if bits == 0:
        return 0
    mod = 1 << bits
    den = q.denominator % mod
    assert den & 1
    return (q.numerator * pow(den, -1, mod)) % mod

def zero_interval(q, lo, hi):
    rr = residue(q, hi)
    return ((rr >> lo) & ((1 << (hi-lo))-1)) == 0

def advance(comp, L):
    Abar,Bbar,Pbar = comp
    A,B,P,D = L
    return A*Abar, A*Bbar + B*Pbar, P*Pbar

def pull(comp, c):
    Abar,Bbar,Pbar = comp
    return (Pbar*c-Bbar)/Abar

def zerozero(transitions):
    # Exact source-free graph through the frozen V80 interface.
    edges = {}
    for tr in transitions:
        if tr["kind"] != "RESIDUAL":
            continue
        sl = law(tr["src"])
        dl = law(tr["dst"])
        if centre(sl) == centre(dl):
            continue
        s = interface(tr["src"], tr["t"])
        d = interface(tr["dst"], tr["t"])
        edges[(s,d)] = (s,d)

    outgoing = defaultdict(list)
    for s,d in edges.values():
        outgoing[s].append(d)

    raw = strict = first_zero = second_zero = 0
    witnesses = []
    for s0,s1 in edges.values():
        for s2 in outgoing.get(s1, ()):
            for s3 in outgoing.get(s2, ()):
                raw += 1
                laws = [s0[0], s1[0], s2[0], s3[0]]
                c0,c1,c2,c3 = map(centre, laws)
                comp1 = advance((1,0,1), laws[0])
                C0 = c0
                C1 = pull(comp1, c1)
                comp2 = advance(comp1, laws[1])
                C2 = pull(comp2, c2)
                comp3 = advance(comp2, laws[2])
                C3 = pull(comp3, c3)
                p0 = rat_v2(C0-C1)
                p1 = rat_v2(C1-C2)
                p2 = rat_v2(C2-C3)
                if not (0 <= p0 < p1 < p2):
                    continue
                strict += 1
                z1 = zero_interval(C1,p0,p1)
                z2 = zero_interval(C2,p1,p2)
                first_zero += int(z1)
                second_zero += int(z2)
                if z1 and z2 and len(witnesses) < 20:
                    witnesses.append({
                        "states": list(map(repr, (s0,s1,s2,s3))),
                        "laws": [list(L) for L in laws],
                        "precisions": [p0,p1,p2],
                        "interval_widths": [p1-p0,p2-p1],
                        "natural_congruence_witness": residue(C2,p2+1) ^ (1<<p2),
                    })
    return {
        "deduplicated_switch_edges": len(edges),
        "raw_three_switch_paths": raw,
        "strict_precision_paths": strict,
        "paths_with_first_zero": first_zero,
        "paths_with_second_zero": second_zero,
        "zero_zero_paths": len(witnesses),
        "sample_zero_zero": witnesses,
    }

A = build_source_transitions(FRESH_A, "freshA")
B = build_source_transitions(FRESH_B, "freshB")
old = [tr for tr in v53.transitions if tr["src"]["residual"]]
oldmap = frozen_map()

checks = {
    "fresh_A": functional(A["transitions"]),
    "fresh_B": functional(B["transitions"]),
    "old_plus_A": functional(old + A["transitions"]),
    "old_plus_A_plus_B": functional(old + A["transitions"] + B["transitions"]),
}
transport_checks = {
    "A": transport(A["transitions"], oldmap),
    "B": transport(B["transitions"], oldmap),
}
hard_separator = (
    A["stats"].get("MISSING_V80_KEY",0)
    + B["stats"].get("MISSING_V80_KEY",0)
    + A["stats"].get("SOURCE_CENSORED",0)
    + B["stats"].get("SOURCE_CENSORED",0)
    + A["stats"].get("CENSORED_RESIDUAL_TAIL",0)
    + B["stats"].get("CENSORED_RESIDUAL_TAIL",0)
)
interface_survives = (
    hard_separator == 0
    and checks["fresh_A"]["collision_states"] == 0
    and checks["fresh_B"]["collision_states"] == 0
    and checks["old_plus_A"]["collision_states"] == 0
    and checks["old_plus_A_plus_B"]["collision_states"] == 0
    and transport_checks["A"]["conflicted"] == 0
    and transport_checks["B"]["conflicted"] == 0
)

zz = None
if interface_survives:
    zz = zerozero(old + A["transitions"] + B["transitions"])

result = {
    "schema": "COLLATZ_V80_FRESH_INTERFACE_V81",
    "parent_v80_qualification_sha256": PARENT_V80_QUAL,
    "selection_rule": (
        "first four lexicographically canonical primitive length-10 binary "
        "necklace/complement representatives with Hamming weight 5"
    ),
    "fresh_motifs": FRESH,
    "fresh_A": {k:v for k,v in A.items() if k != "transitions"},
    "fresh_B": {k:v for k,v in B.items() if k != "transitions"},
    "old_transition_rows": len(old),
    "fresh_A_transition_rows": len(A["transitions"]),
    "fresh_B_transition_rows": len(B["transitions"]),
    "functionality": checks,
    "transport": transport_checks,
    "hard_separator_count": hard_separator,
    "interface_survives": interface_survives,
    "zerozero_reclosure": zz,
    "status": (
        "FRESH_INTERFACE_AND_ZEROZERO_SURVIVE"
        if interface_survives and zz is not None and zz["zero_zero_paths"] == 0
        else "FRESH_INTERFACE_SURVIVES_ZEROZERO_RESIDUAL"
        if interface_survives
        else "FRESH_INTERFACE_REJECTED"
    ),
    "global_collatz": "UNKNOWN",
    "qed": False,
}
result["certificate_sha256"] = hashlib.sha256(
    json.dumps(result, sort_keys=True, separators=(",", ":")).encode()
).hexdigest()
print(json.dumps(result, indent=2, sort_keys=True))
