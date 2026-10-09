"""V113: independently audit V112's 1701 certificates using only 3
source-congruence laws, not V112's reverse-path search or witness table.

Proof boundary:
- exact affine parity steps and reverse steps are checked once as integer
  identities; inequalities on base and slope prove ALL nonnegative offsets.
- finite CRT residual intersection is exhaustively enumerated.
- universal Lean promotion requires an actual pinned Lean kernel gate.
"""
import hashlib
import json
from collections import Counter

from research.collatz_v108_reclosure import MODULUS as DYADIC, candidates
from research.collatz_v109_reverse_reclosure import reverse_witness
from research.collatz_v110_q7_crt_reclosure import TERNARY, PRODUCT, ternary_reverse, crt_base

LAWS = (
  dict(tag="a", base=273, modulus=1458, prefix=1,
       endpoint=410, earlier=191, earlier_slope=1024,
       reverse_word="EEOEOOOOOO"),
  dict(tag="b", base=1321, modulus=1458, prefix=1,
       endpoint=1982, earlier=927, earlier_slope=1024,
       reverse_word="EEOOEOOOOO"),
  dict(tag="c", base=1275, modulus=1296, prefix=4,
       endpoint=2153, earlier=1007, earlier_slope=1024,
       reverse_word="EEOOOEOOOO"),
)

def verify_law(law):
    n, slope = law["base"], law["modulus"]
    assert n > law["earlier"] > 0
    assert 0 < law["earlier_slope"] <= slope

    # Derive the exact shortcut affine action on n+slope*q for EVERY q.
    for _ in range(law["prefix"]):
        assert slope % 2 == 0
        if n % 2 == 0:
            n, slope = n//2, slope//2
        else:
            n, slope = (3*n+1)//2, (3*slope)//2
    assert (n, slope) == (law["endpoint"], TERNARY)

    # Verify EVERY inverse affine operation; modular premises are explicit.
    for op in law["reverse_word"]:
        if op == "E":
            n, slope = 2*n, 2*slope
        else:
            assert op == "O" and n >= 2 and n % 3 == 2 and slope % 3 == 0
            n, slope = (2*n-1)//3, 2*slope//3
    assert (n, slope) == (law["earlier"], law["earlier_slope"])

def main():
    for law in LAWS:
        verify_law(law)

    dyadic_residual = [r for r in range(DYADIC)
                       if not candidates(r) and reverse_witness(r) is None]
    ternary_residual = [a for a in range(TERNARY) if ternary_reverse(a) is None]
    assert len(dyadic_residual) == 144
    assert len(ternary_residual) == 1174

    counts = Counter()
    source_bases = []
    witness_rows = []
    for r in dyadic_residual:
        for a in ternary_residual:
            n0 = crt_base(r,a)
            matches = [law for law in LAWS
                       if n0 % law["modulus"] == law["base"]]
            assert len(matches) <= 1  # three disjoint classes
            if matches:
                law = matches[0]
                q = (n0 - law["base"])//law["modulus"]
                assert q >= 0 and n0 == law["base"] + law["modulus"]*q
                p0 = law["earlier"] + law["earlier_slope"]*q
                assert 0 < p0 < n0
                # Rebase to CRT offset t: q -> q + (PRODUCT / mod)*t.
                assert PRODUCT % law["modulus"] == 0
                c = law["earlier_slope"]*(PRODUCT//law["modulus"])
                assert 0 < c < PRODUCT
                source_bases.append(n0)
                witness_rows.append((n0,p0,c,law["tag"]))
                counts[law["tag"]] += 1
    assert counts == Counter({"a":432,"b":432,"c":837})
    assert len(source_bases) == 1701
    assert len(set(source_bases)) == 1701
    assert (6991899,5524463,7077888,"c") in witness_rows

    canonical=json.dumps(sorted(witness_rows),separators=(",",":")).encode()
    output=dict(
        schema="COLLATZ_V113_THREE_CONGRUENCE_AUDIT",
        status="BOUNDED_EXECUTABLE_EXACT_GENERIC_LAWS",
        global_collatz="UNKNOWN", qed=False,
        generic_laws=LAWS,
        source_modulus=PRODUCT,
        v110_unknown_crt=169056,
        v112_recovered_crt=1701,
        recovered_by_law=dict(sorted(counts.items())),
        total_covered_crt=8790597,
        remaining_unknown_crt=167355,
        witness_digest_sha256=hashlib.sha256(canonical).hexdigest(),
        universal_natural_source_bar=False,
        individual_witnesses_lean_reified=False,
        example=dict(original=6991899, earlier=5524463, earlier_slope=7077888))
    print(json.dumps(output,sort_keys=True,indent=2))

if __name__=="__main__":
    main()
