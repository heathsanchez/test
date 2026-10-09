"""V112: source-guarded mixed reverse words on the V110 unresolved CRT product.

Searches only previously unresolved exact source residue classes modulo 2^12*3^7.
Each accepted witness p(t)=p0+c*t has 0<p0<n0 and 0<c<=PRODUCT;
the reverse word is an actual shortcut predecessor path and agrees
symbolically with a forward prefix of n(t)=n0+PRODUCT*t for ALL t>=0.
This is bounded exact arithmetic, NOT a universal Collatz proof and
NOT a set of Lean-reified individual witnesses.
"""
from collections import Counter
import hashlib
import json
from research.collatz_v108_reclosure import candidates, prefixes, shortcut
from research.collatz_v109_reverse_reclosure import reverse_witness
from research.collatz_v110_q7_crt_reclosure import (
    DYADIC, TERNARY, PRODUCT, crt_base, ternary_reverse,
)

MAX_FORWARD = 12
MAX_REVERSE = 12
MAX_COEFFICIENT = 50 * PRODUCT

def source_guarded_mixed(n0):
    for j, x, odd, dyadic_slope in prefixes(n0):
        slope = dyadic_slope * TERNARY
        states = [(x, slope, "")]
        seen = {(x, slope)}
        for length in range(1, MAX_REVERSE + 1):
            next_states = []
            for b, c, word in states:
                even_b, even_c = 2 * b, 2 * c
                if (even_b > 0 and even_c < MAX_COEFFICIENT
                        and (even_b, even_c) not in seen):
                    next_states.append((even_b, even_c, word + "E"))
                    seen.add((even_b, even_c))
                if b >= 2 and b % 3 == 2 and c % 3 == 0:
                    odd_b, odd_c = (2 * b - 1) // 3, (2 * c) // 3
                    assert 3 * odd_b + 1 == 2 * b
                    assert 3 * odd_c == 2 * c
                    if odd_b > 0 and (odd_b, odd_c) not in seen:
                        next_states.append((odd_b, odd_c, word + "O"))
                        seen.add((odd_b, odd_c))
            for b, c, word in next_states:
                if 0 < b < n0 and 0 < c <= PRODUCT:
                    return dict(forward_prefix=j, reverse_steps=length,
                                reverse_word=word, forward_intercept=x,
                                forward_slope=slope,
                                predecessor_intercept=b,
                                predecessor_slope=c)
            states = next_states
            if not states:
                break
    return None

def validate(n0, r, a, witness):
    assert 0 <= n0 < PRODUCT
    assert n0 % DYADIC == r and n0 % TERNARY == a
    j = witness["forward_prefix"]
    word = witness["reverse_word"]
    b = witness["predecessor_intercept"]
    c = witness["predecessor_slope"]
    assert 1 <= j <= MAX_FORWARD and len(word) == witness["reverse_steps"]
    assert 0 < b < n0 and 0 < c <= PRODUCT
    x = n0
    odd = 0
    for _ in range(j):
        odd += x % 2
        x = shortcut(x)
    # All offsets n(t)=n0+2^12*3^7*t preserve this actual parity prefix.
    slope = (DYADIC >> j) * (3 ** odd) * TERNARY
    assert (x, slope) == (
        witness["forward_intercept"], witness["forward_slope"])
    y, z = x, slope
    for op in word:
        if op == "E":
            y, z = 2 * y, 2 * z
        else:
            assert op == "O" and y >= 2 and y % 3 == 2 and z % 3 == 0
            old_y, old_z = y, z
            y, z = (2 * y - 1) // 3, (2 * z) // 3
            assert 3 * y + 1 == 2 * old_y and 3 * z == 2 * old_z
    assert (y, z) == (b, c)
    # The identities above certify every offset; these are regressions only.
    for t in (0, 1, 2, 7, 13):
        n, p = n0 + PRODUCT * t, b + c * t
        assert 0 < p < n
        future_n = n
        for _ in range(j):
            future_n = shortcut(future_n)
        future_p = p
        for _ in word:
            future_p = shortcut(future_p)
        assert future_n == future_p

def main():
    dyadic_unknown = [
        r for r in range(DYADIC)
        if not candidates(r) and reverse_witness(r) is None
    ]
    ternary_unknown = [
        a for a in range(TERNARY) if ternary_reverse(a) is None
    ]
    assert len(dyadic_unknown) == 144
    assert len(ternary_unknown) == 1174
    records = []
    word_types = Counter()
    checked = 0
    for r in dyadic_unknown:
        for a in ternary_unknown:
            n0 = crt_base(r, a)
            checked += 1
            witness = source_guarded_mixed(n0)
            if witness is not None:
                validate(n0, r, a, witness)
                word_types[(witness["forward_prefix"],
                            witness["reverse_word"])] += 1
                records.append(dict(crt_source=n0, dyadic_residue=r,
                                    ternary_residue=a, **witness))
    records.sort(key=lambda record: record["crt_source"])
    assert checked == 169056
    assert len(records) == 4617
    assert len(word_types) == 14
    result = dict(
        schema="COLLATZ_V112_CRT_GUARDED_MIXED_REVERSE",
        status="BOUNDED_EXACT_ONLY",
        global_collatz="UNKNOWN", qed=False,
        individually_lean_reified=False,
        source_modulus=PRODUCT, max_forward=MAX_FORWARD,
        max_reverse=MAX_REVERSE, original_v110_covered=8788896,
        examined_original_unknown=checked,
        new_source_relative_mergers=len(records),
        covered_after_v112=8788896+len(records),
        remaining_unknown=checked-len(records),
        qualified_word_templates=[
            dict(forward_prefix=j, word=word, count=count)
            for (j, word), count in sorted(word_types.items())
        ],
        new_witness_records=records,
    )
    canonical = json.dumps(result, sort_keys=True, separators=(",", ":"))
    result["certificate_payload_sha256"] = hashlib.sha256(
        canonical.encode()).hexdigest()
    print(json.dumps(result, indent=2, sort_keys=True))

if __name__ == "__main__":
    main()
