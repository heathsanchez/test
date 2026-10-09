"""Exact bounded source-cylinder merger compiler at depth 12.

Only all-offset symbolic inequalities are promoted. UNKNOWN is not counterevidence.
The underlying all-offset affine and merger laws are formalized separately in Lean.
"""
import json
from collections import Counter

DEPTH = 12
MODULUS = 1 << DEPTH

def shortcut(n):
    return n // 2 if n % 2 == 0 else (3 * n + 1) // 2

def prefixes(r):
    x, odds = r, 0
    for j in range(1, DEPTH + 1):
        odds += x % 2
        x = shortcut(x)
        a = (1 << (DEPTH-j)) * 3**odds
        yield j, x, odds, a

def candidates(r):
    out = []
    for j, x, odds, a in prefixes(r):
        if a < MODULUS:
            q0 = max(0, (x-r)//(MODULUS-a) + 1)
            out.append(dict(kind="direct", steps=j, intercept=x,
                            odds=odds, coefficient=a, q_min=q0))
        if odds > 0 and x >= 2 and x % 3 == 2 and 2*a < 3*MODULUS:
            q0 = max(0, (2*x-1-3*r)//(3*MODULUS-2*a) + 1)
            out.append(dict(kind="inverse_odd", steps=j, intercept=x,
                            odds=odds, coefficient=a, q_min=q0))
    return out

def validate(r, w):
    kind, j, x, odd, a = (w[k] for k in
        ("kind", "steps", "intercept", "odds", "coefficient"))
    assert 1 <= j <= DEPTH and a == (1 << (DEPTH-j)) * 3**odd
    # Regression samples, not the universal proof. Universal affine shift is Lean.
    for q in (0, 1, 2, 7, 19):
        n = r + MODULUS*q
        y = n
        for _ in range(j):
            y = shortcut(y)
        assert y == x+a*q
    q = w["q_min"]
    n = r+MODULUS*q
    y = x+a*q
    if kind == "direct":
        assert a < MODULUS and y < n
    else:
        assert kind == "inverse_odd"
        assert odd > 0 and x >= 2 and x % 3 == 2
        assert a % 3 == 0 and 2*a < 3*MODULUS
        assert (2*y-1) % 3 == 0
        p = (2*y-1)//3
        assert 0 < p < n and p%2 == 1 and shortcut(p) == y

def main():
    records = []
    counts = Counter()
    for r in range(MODULUS):
        cs = candidates(r)
        cs.sort(key=lambda w:(w["q_min"],w["kind"]!="direct",w["steps"]))
        if not cs:
            counts["unknown_cylinders"] += 1
            records.append(dict(residue=r,status="UNKNOWN_NO_PREFIX_MERGER"))
            continue
        w = cs[0]
        validate(r,w)
        if w["q_min"] == 0:
            assert r>1
        else:
            # Uncertified offsets are only n=0 and the terminal n=1.
            assert (r,w["q_min"]) in ((0,1),(1,1))
            counts["zero_or_terminal_exception_cylinders"] += 1
        counts["certified_cylinders_n_gt_1"] += 1
        counts[w["kind"]+"_cylinders"] += 1
        records.append(dict(residue=r,status="GUARDED_SOURCE_COALESCENCE",**w))
    assert counts["certified_cylinders_n_gt_1"] == 3904
    assert counts["direct_cylinders"] == 3870
    assert counts["inverse_odd_cylinders"] == 34
    assert counts["unknown_cylinders"] == 192
    assert counts["zero_or_terminal_exception_cylinders"] == 2
    assert len(records) == MODULUS
    print(json.dumps(dict(schema="COLLATZ_V108_EXACT_BOUNDED_MERGERS",
        status="BOUNDED_EXACT_ONLY",global_collatz="UNKNOWN",qed=False,
        depth=DEPTH,modulus=MODULUS,counts=dict(counts),records=records),
        sort_keys=True,indent=2))

if __name__ == "__main__":
    main()
