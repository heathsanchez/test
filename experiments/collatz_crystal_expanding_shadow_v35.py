#!/usr/bin/env python3
"""Crystal V35: exact expanding-return shadow family after V34.

Parent:
  collatz-crystal-k-return-separator-v34@87a6036487431d22c4d8744cf109e056d88f3b82

V34 found the first consequential owner/source-carry separator at chamber state
514835.  Its expanding K-containing return is valid precisely on

    t == 1260 (mod 2^11)

for m = 7935 + 2^13*t, and induces

    E(t) = 3^9 * ((t-1260)/2^11) + 12118.

This gate asks whether "inspect sufficiently many carry bits" could close the
remaining source-coherent residual.  It recursively constructs the unique
2-adic cylinder whose first r base returns are all E.

For every finite r the cylinder has a positive natural least representative.
Thus arbitrarily long finite expanding K-return shadows are algebraically
compatible with natural owners.  The infinite repeated-E path is still excluded
by V28/V34 (its 2-adic fixed point is negative); the residual is therefore
genuinely an aperiodic/infinite source-carry theorem, not a missing finite depth.

The workflow verifies a long exact prefix of the symbolic recurrence.  The
universal arbitrary-r statement is emitted as a theorem target, not promoted as
Lean authority.
"""
from __future__ import annotations

from contextlib import redirect_stdout
import io
import json
import hashlib

with redirect_stdout(io.StringIO()):
    import collatz_crystal_k_return_separator_v34 as v34

A = 3**9
B = 2**11
R_ONE = 1260
C = 12118
BASE_RESIDUE = 7935
BASE_SCALE = 2**13
N0 = 38_911_100_780_481_085_467
CHECK_R = 32

assert A == 19683 and B == 2048
assert v34.Ae == A / B
# Exact parent identity, avoiding float semantics.
assert v34.Ae.numerator == A and v34.Ae.denominator == B

def E(t: int) -> int:
    assert t >= 0
    assert t % B == R_ONE
    return A * ((t - R_ONE)//B) + C

def owner(t: int) -> int:
    return BASE_RESIDUE + BASE_SCALE*t

def next_shadow_residue(R: int, M: int) -> tuple[int,int]:
    """If R mod M realizes r expanding returns, produce the unique residue
    mod B*M realizing r+1 returns."""
    assert M > 0 and M & (M-1) == 0
    inv = pow(A, -1, M)
    u = ((R - C) * inv) % M
    Rn = R_ONE + B*u
    Mn = B*M
    assert 0 <= Rn < Mn
    # First return lands in the previous r-return cylinder.
    assert E(Rn) % M == R
    return Rn, Mn

R = R_ONE
M = B
rows = []
first_above = None

for r in range(1, CHECK_R+1):
    t = R
    m0 = owner(t)
    cur = t
    owners = [m0]
    for i in range(r):
        assert cur % B == R_ONE
        cur = E(cur)
        owners.append(owner(cur))
    assert all(b > a for a,b in zip(owners, owners[1:])), (r, owners[:4])
    above = m0 > N0
    if above and first_above is None:
        first_above = r

    rows.append({
        "repeats": r,
        "parameter_residue": str(R),
        "parameter_modulus": str(M),
        "owner_start": str(m0),
        "owner_start_above_v23_floor": above,
        "owner_after_repeats": str(owners[-1]),
        "strict_owner_expansion_every_return": True,
    })

    R, M = next_shadow_residue(R, M)

assert first_above == 5
assert rows[0]["parameter_residue"] == "1260"
assert rows[1]["parameter_residue"] == "3118316"
assert rows[2]["parameter_residue"] == "3639579884"
assert rows[3]["parameter_residue"] == "6463270393068"
assert rows[4]["parameter_residue"] == "28628949964657900"

# Parent expanding return on m is exactly equivalent to E on t.
for t in (1260, 3_118_316, 28_628_949_964_657_900):
    if t % B != R_ONE:
        continue
    m = owner(t)
    mp = v34.Ae*m + v34.Be
    assert mp.denominator == 1
    assert mp.numerator == owner(E(t))

result = {
    "schema":"COLLATZ_CRYSTAL_EXPANDING_SHADOW_V35",
    "parent":"collatz-crystal-k-return-separator-v34@87a6036487431d22c4d8744cf109e056d88f3b82",
    "expanding_return":{
        "base_state":514835,
        "owner_parameterization":"m=7935+2^13*t",
        "guard":"t == 1260 (mod 2^11)",
        "map":"E(t)=3^9*((t-1260)/2^11)+12118",
        "owner_map":"F(m)=(19683*m+18403)/2048",
        "owner_fixed_point":"-18403/17635",
    },
    "shadow_recurrence":{
        "definition":[
            "R_1=1260, M_1=2^11",
            "u_r == (R_r-12118)*(3^9)^(-1) (mod M_r)",
            "R_(r+1)=1260+2^11*u_r",
            "M_(r+1)=2^11*M_r"
        ],
        "identity":"E(R_(r+1)) == R_r (mod M_r)",
        "uniqueness_reason":"3^9 is odd, hence invertible modulo every power of two",
        "checked_repeats":CHECK_R,
        "first_least_representative_above_v23_source_floor":first_above,
        "first_rows":rows[:12],
        "last_row":rows[-1],
    },
    "scientific_verdict":(
        "FINITE_CARRY_DEPTH_CLOSEOUT_REJECTED: exact positive-natural least "
        "representatives shadow the strictly expanding K return for every tested "
        "depth, with the recursive congruence giving the arbitrary-r theorem target."
    ),
    "next_residual":{
        "name":"INFINITE_SOURCE_CARRY_COHERENCE",
        "statement":(
            "Prove that no single fixed positive natural no-OrdinaryExit source can "
            "realize an infinite aperiodic sequence of guarded K returns. Finite carry "
            "depth is provably the wrong proof interface; periodic repetition is already "
            "excluded by V28, and the remaining distinction is infinite source coherence."
        ),
        "formal_target":(
            "Lean-formalize the shadow recurrence and then a coinductive/source-product "
            "theorem excluding an infinite eventually-zero natural source realization, "
            "without assuming Collatz or a disputed parity-density equality."
        ),
        "forbidden_shortcuts":[
            "increase finite carry depth",
            "raw source/residue census",
            "state-only owner rank",
            "promote the arXiv density-equality claim without independent proof"
        ],
    },
    "universal_status":"UNKNOWN",
    "global_collatz":"UNKNOWN",
}
result["certificate_sha256"] = hashlib.sha256(
    json.dumps(result,sort_keys=True,separators=(",",":")).encode()
).hexdigest()
print(json.dumps(result,indent=2,sort_keys=True))
