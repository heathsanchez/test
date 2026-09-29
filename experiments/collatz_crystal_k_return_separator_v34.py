#!/usr/bin/env python3
"""Crystal V34: correct V33 owner algebra and expose the exact K-return separator.

Parent:
  collatz-crystal-k-boundary-v33@8ed63c9d6c1312e656c181a89d1073173c22dcec

V33 correctly classified the graph-side zero-slack boundary, but its odd-edge
owner-map intercept omitted division by 3^12.  This gate repairs that algebra
and independently verifies every non-B owner edge against the defining reverse
equations.

It then asks the next Crystal question at one exact chamber state: is local
chamber state sufficient to rank canonical owner returns?  No.  The same state
has one exact K-containing return cycle that expands every positive owner and
another exact K-containing return cycle that contracts every positive owner.
The first extra owner/source-carry bit separates them.

Therefore the earned next coordinate is not another residue/cost scalar; it is
the exact 2-adic owner/source-carry guard selecting the return.
"""
from __future__ import annotations

from collections import defaultdict
from contextlib import redirect_stdout
from fractions import Fraction
import hashlib
import io
import json

with redirect_stdout(io.StringIO()):
    import collatz_crystal_k_density_tradeoff_v32 as v32

best = v32.best
edges = v32.edges
MOD = v32.MOD
N0 = 38_911_100_780_481_085_467
BASE = 514_835

lookup = defaultdict(list)
for e in edges:
    lookup[(e[0], e[1])].append(e)

def owner_map(u: int, v: int, bit: int):
    """Exact canonical-owner map derived from
       y=(MOD*m+C)/2^S and y'=T_bit(y).

    V33's odd case used 2^(Sp-1), but the +1 contribution is divided by MOD.
    """
    S, C, _ = best[u]
    Sp, Cp, _ = best[v]
    if bit == 0:
        a = Fraction(2**Sp, 2**(S+1))
        b = a*Fraction(C, MOD) - Fraction(Cp, MOD)
    else:
        a = Fraction(3*2**Sp, 2**(S+1))
        b = Fraction(2**(Sp-1), MOD) + a*Fraction(C, MOD) - Fraction(Cp, MOD)
    return a, b

def old_v33_owner_map(u: int, v: int, bit: int):
    S, C, _ = best[u]
    Sp, Cp, _ = best[v]
    if bit == 0:
        a = Fraction(2**Sp, 2**(S+1))
        b = a*Fraction(C, MOD) - Fraction(Cp, MOD)
    else:
        a = Fraction(3*2**Sp, 2**(S+1))
        b = Fraction(2**(Sp-1), 1) + a*Fraction(C, MOD) - Fraction(Cp, MOD)
    return a, b

def audit_edge(e):
    u, v, bit, cls, drop = e
    S, C, _ = best[u]
    Sp, Cp, _ = best[v]

    # Choose an exact positive owner in the unique mod-2^(S+1) cylinder that
    # makes the current endpoint integral with the declared next parity.
    mod = 1 << (S + 1)
    r = ((bit << S) - C) * pow(MOD, -1, mod) % mod
    m = r + 4*mod
    num = MOD*m + C
    assert num % (1 << S) == 0
    y = num >> S
    assert y & 1 == bit
    yp = (3*y + 1)//2 if bit else y//2

    a, b = owner_map(u, v, bit)
    mp = a*m + b
    assert mp.denominator == 1
    mp = mp.numerator

    nump = (1 << Sp)*yp - Cp
    assert nump % MOD == 0
    direct = nump // MOD
    assert mp == direct
    return bit

# Independent algebra audit over the complete non-B graph.
audited = 0
odd_edges = 0
old_odd_intercept_disagreements = 0
for e in edges:
    bit = audit_edge(e)
    audited += 1
    if bit:
        odd_edges += 1
        a, b = owner_map(e[0], e[1], bit)
        ao, bo = old_v33_owner_map(e[0], e[1], bit)
        assert a == ao
        if b != bo:
            old_odd_intercept_disagreements += 1

assert audited == 38_991
assert odd_edges == 27_469
assert old_odd_intercept_disagreements == odd_edges

def compose(path):
    A = Fraction(1)
    B = Fraction(0)
    for u, v, bit, cls, drop in path:
        a, b = owner_map(u, v, bit)
        B = a*B + b
        A = a*A
    return A, B

def edge_exists(e):
    return e in lookup[(e[0], e[1])]

# Re-audit V33's sharp c=18 witness under the corrected owner algebra.
sharp_nodes = [
169775,254663,381995,41552,328049,492074,246037,369056,184528,
92264,46132,23066,300320,184760,92380,46190,335006,236789,384115,
44732,332819,499229,217403,374422,187211,359326,179663,269495,
404243,74924,378107,35720,17860,8930,279116,139558,475058,237529,
356294,178147,267221,399331,67556,33778,316388,158194,503012,
488798,467477,169775
]
sharp = []
for u, v in zip(sharp_nodes[:-1], sharp_nodes[1:]):
    opts = lookup[(u, v)]
    assert opts
    sharp.append(min(opts, key=lambda z: 19*z[2] - 12 + 18*z[4]))
assert len(sharp) == 49
assert sum(e[2] for e in sharp) == 29
assert sum(e[4] for e in sharp) == 2
A33, B33 = compose(sharp)
fp33 = B33/(1-A33)
assert A33 == Fraction(3**29, 2**49)
assert B33 == Fraction(1596699704000581, 562949953421312)
assert fp33 == Fraction(1596699704000581, 494319576056429)
assert fp33 < N0
assert A33*N0 + B33 < N0

# Same-state expanding K-return.
expanding = [
(514835,240812,1,"I",0),
(240812,95498,1,"I",0),
(95498,408968,1,"I",0),
(408968,347732,1,"I",0),
(347732,255878,1,"I",0),
(255878,118097,1,"I",0),
(118097,324769,0,"I",0),
(324769,428105,0,"I",0),
(428105,110717,1,"I",0),
(110717,166076,1,"K",1),
(166076,514835,1,"I",0),
]

# Same-state contracting K-return, found by exact minimum-q dynamic search.
contracting = [
(514835,523138,0,"I",0),
(523138,261569,0,"I",0),
(261569,396505,0,"I",0),
(396505,463973,0,"I",0),
(463973,497707,0,"I",0),
(497707,514574,0,"I",0),
(514574,506141,1,"I",0),
(506141,227771,1,"I",0),
(227771,341657,1,"I",0),
(341657,512486,1,"K",0),
(512486,503009,1,"I",0),
(503009,223073,1,"I",0),
(223073,377257,0,"I",0),
(377257,34445,1,"K",1),
(34445,51668,1,"K",1),
(51668,343223,1,"I",0),
(343223,514835,1,"K",1),
]

assert all(edge_exists(e) for e in expanding)
assert all(edge_exists(e) for e in contracting)
assert expanding[0][0] == expanding[-1][1] == BASE
assert contracting[0][0] == contracting[-1][1] == BASE
assert any(e[3] == "K" for e in expanding)
assert any(e[3] == "K" for e in contracting)

Ae, Be = compose(expanding)
Ac, Bc = compose(contracting)
assert Ae == Fraction(19683, 2048)
assert Be == Fraction(18403, 2048)
assert Ac == Fraction(59049, 131072)
assert Bc == Fraction(-12375, 131072)
assert Ae > 1 and Be > 0
assert Ac < 1 and Bc < 0
assert Ae*N0 + Be > N0
assert Ac*N0 + Bc < N0

def parity_residue(bits):
    r = 0
    mod = 1
    for i, bit in enumerate(bits):
        found = None
        for cand in (r, r + mod):
            x = cand
            for _ in range(i):
                x = (3*x + 1)//2 if x & 1 else x//2
            if (x & 1) == bit:
                found = cand
                break
        assert found is not None
        r = found
        mod <<= 1
    return r, mod

def owner_guard(path):
    S, C, _ = best[path[0][0]]
    bits = [e[2] for e in path]
    yres, ymod = parity_residue(bits)
    modulus = 1 << (S + len(bits))
    rhs = ((1 << S)*yres - C) % modulus
    mres = rhs * pow(MOD, -1, modulus) % modulus
    return mres, modulus

Sbase, Cbase, _ = best[BASE]
base_mod = 1 << Sbase
base_res = (-Cbase * pow(MOD, -1, base_mod)) % base_mod
eg, emod = owner_guard(expanding)
cg, cmod = owner_guard(contracting)

assert Sbase == 13
assert base_res == 7935
assert (eg, emod) == (10_329_855, 1 << 24)
assert (cg, cmod) == (504_348_415, 1 << 30)
# The very next newly exposed owner bit already separates opposite drift.
assert ((eg >> Sbase) & 1) == 0
assert ((cg >> Sbase) & 1) == 1
assert expanding[0][2] == 1
assert contracting[0][2] == 0

result = {
    "schema": "COLLATZ_CRYSTAL_K_RETURN_SEPARATOR_V34",
    "parent": "collatz-crystal-k-boundary-v33@8ed63c9d6c1312e656c181a89d1073173c22dcec",
    "owner_map_audit": {
        "non_B_edges_checked": audited,
        "odd_edges_checked": odd_edges,
        "v33_odd_intercept_disagreements": old_odd_intercept_disagreements,
        "correct_odd_constant": "2^(S'-1)/3^12",
        "disposition": (
            "V33 graph/cycle classification is retained, but its printed odd-edge "
            "owner intercept/fixed-point arithmetic is superseded by this corrected audit."
        ),
    },
    "v33_sharp_cycle_corrected": {
        "length": len(sharp),
        "odd_steps": sum(e[2] for e in sharp),
        "K_drop": sum(e[4] for e in sharp),
        "slope": [A33.numerator, A33.denominator],
        "intercept": [B33.numerator, B33.denominator],
        "fixed_point": [fp33.numerator, fp33.denominator],
        "fixed_point_lt_v23_source_floor": fp33 < N0,
        "contracts_at_v23_floor": A33*N0 + B33 < N0,
    },
    "same_state_opposite_return_drift": {
        "base_state": BASE,
        "base_owner_modulus": base_mod,
        "base_owner_residue": base_res,
        "expanding": {
            "length": len(expanding),
            "odd_steps": sum(e[2] for e in expanding),
            "K_drop": sum(e[4] for e in expanding),
            "K_edges": sum(e[3] == "K" for e in expanding),
            "slope": [Ae.numerator, Ae.denominator],
            "intercept": [Be.numerator, Be.denominator],
            "fixed_point": [
                (Be/(1-Ae)).numerator,
                (Be/(1-Ae)).denominator,
            ],
            "owner_guard_residue": eg,
            "owner_guard_modulus": emod,
            "first_new_owner_bit": (eg >> Sbase) & 1,
            "first_orbit_bit": expanding[0][2],
            "drift_for_positive_owner": "STRICT_EXPANSION",
        },
        "contracting": {
            "length": len(contracting),
            "odd_steps": sum(e[2] for e in contracting),
            "K_drop": sum(e[4] for e in contracting),
            "K_edges": sum(e[3] == "K" for e in contracting),
            "slope": [Ac.numerator, Ac.denominator],
            "intercept": [Bc.numerator, Bc.denominator],
            "fixed_point": [
                (Bc/(1-Ac)).numerator,
                (Bc/(1-Ac)).denominator,
            ],
            "owner_guard_residue": cg,
            "owner_guard_modulus": cmod,
            "first_new_owner_bit": (cg >> Sbase) & 1,
            "first_orbit_bit": contracting[0][2],
            "drift_for_positive_owner": "STRICT_CONTRACTION",
        },
    },
    "scientific_verdict": (
        "V33_OWNER_INTERCEPT_CORRECTED; SAME_CHAMBER_STATE_HAS_OPPOSITE "
        "K_RETURN_OWNER_DRIFT; CHAMBER_STATE_ONLY_OWNER_RANK_REJECTED"
    ),
    "next_residual": {
        "name": "SOURCE_CARRY_GUARDED_K_RETURN",
        "statement": (
            "Carry the exact 2-adic owner/source guard through K returns. "
            "A proof must show that an eventually-zero fixed natural source cannot "
            "select expanding guarded returns indefinitely without a B contraction "
            "or an OrdinaryExit p<n. The newly exposed owner bit is consequential."
        ),
        "forbidden_shortcuts": [
            "state-only owner scalar rank",
            "treat local K rewind as original-source descent",
            "raw deeper chamber or parameter census",
        ],
    },
    "universal_status": "UNKNOWN",
    "global_collatz": "UNKNOWN",
}
result["certificate_sha256"] = hashlib.sha256(
    json.dumps(result, sort_keys=True, separators=(",", ":")).encode()
).hexdigest()
print(json.dumps(result, indent=2, sort_keys=True))
