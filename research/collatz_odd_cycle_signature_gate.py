"""Exact symbolic exclusion of nonterminal shortcut cycles with few odd entries.

Proof boundary: In an actual positive periodic shortcut orbit avoiding 1,
each odd visit x_i >= 3 and 2^a_i*x_(i+1) = 3*x_i+1, a_i>=1.
Multiplication gives 3^c < 2^k <= (10/3)^c, where k=sum a_i.
For each admissible c,k, exhaust every positive composition of k into
c parts; its affine fixed point has at most one positive integer solution.
Replay any integral candidate against the ACTUAL shortcut dynamics.
This finite audit does not exclude cycles with arbitrarily many odd visits,
or unbounded nonperiodic trajectories.
"""
import itertools
import json
import hashlib
import sys
from math import comb


def k_window(c):
    assert c >= 1
    lo = 0
    while (1 << lo) <= 3**c:
        lo += 1
    hi = 0
    while (1 << (hi+1))*3**c <= 10**c:
        hi += 1
    return lo, hi


def cycle_candidate(parts):
    c, k = len(parts), sum(parts)
    denom = (1 << k) - 3**c
    assert denom > 0
    B, s = 0, 0
    for a in parts:
        B = 3*B + (1 << s)
        s += a
    assert s == k
    if B % denom:
        return None
    x0 = B // denom
    if x0 <= 0 or x0 % 2 == 0:
        return None
    x = x0
    for a in parts:
        assert x % 2 == 1
        z = 3*x+1
        if z % (1 << a):
            return None
        nxt = z >> a
        if nxt % 2 != 1:
            return None
        # Test all actual steps: one odd shortcut, then a-1 even steps.
        w = x
        for _ in range(a):
            w = w//2 if w%2 == 0 else (3*w+1)//2
        if w != nxt:
            return None
        x = nxt
    return x0 if x == x0 else None


def audit(max_c=14):
    rows, total = [], 0
    for c in range(1, max_c+1):
        lo, hi = k_window(c)
        num, terminal, bad = 0, 0, []
        for k in range(max(c,lo), hi+1):
            for cuts in itertools.combinations(range(1,k), c-1):
                parts = tuple(b-a for a,b in zip((0,)+cuts, cuts+(k,)))
                num += 1
                n = cycle_candidate(parts)
                if n is not None:
                    if n == 1:
                        terminal += 1
                    else:
                        bad.append((n, parts))
        expected = sum(comb(k-1,c-1) for k in range(max(c,lo),hi+1))
        assert num == expected
        assert not bad, (c, bad[:3])
        rows.append(dict(odd_visits=c,k_min=lo,k_max=hi,
                         signature_count=num,terminal_signature_count=terminal,
                         nonterminal_cycles=0))
        total += num
        print(f"cycle-odd-visits={c} k={lo}..{hi} signatures={num} nonterminal=0",
              file=sys.stderr, flush=True)
    result = dict(
        schema="COLLATZ_ODD_VISIT_CYCLE_SIGNATURE_EXCLUSION",
        status="BOUNDED_EXACT_EXECUTABLE",
        max_odd_visits=max_c, total_signatures=total,
        nonterminal_cycles_in_declared_envelope=0,
        global_collatz="UNKNOWN", qed=False, rows=rows)
    canonical = json.dumps(result, sort_keys=True, separators=(",",":"))
    result["payload_sha256"] = hashlib.sha256(canonical.encode()).hexdigest()
    print(json.dumps(result, sort_keys=True, indent=2))


if __name__ == "__main__":
    audit(int(sys.argv[1]) if len(sys.argv)>1 else 14)
