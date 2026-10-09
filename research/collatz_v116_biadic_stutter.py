"""V116 exact natural-source finite-biadic stutter obstruction.

For d,q,L>=1, set K=d+q+L+1 and n=2**K-1. The actual shortcut
orbit has L+1 consecutive endpoints congruent to -1 mod 2**d*3**q,
from time q to q+L, and none of its first q+L iterates passes the
source-capped ternary return bar. All claims are integer-exact.

This rejects residue-only ranks with bounded-delay strict progress.
It does NOT reject source-dependent, unbounded-precision macro ranks.
It is not a Collatz proof.
"""
import hashlib
import json
from math import gcd

def shortcut(n):
    return n // 2 if n % 2 == 0 else (3*n + 1)//2

def v2(n):
    assert n > 0
    return (n & -n).bit_length() - 1

def witness(d, q, L):
    assert min(d, q, L) >= 1
    K = d + q + L + 1
    n = (1 << K) - 1
    M = (1 << d) * 3**q
    assert gcd(1 << d, 3**q) == 1
    x = n
    states = []
    for j in range(q + L + 1):
        y = 3**j * (1 << (K-j)) - 1
        assert x == y  # actual shortcut trace, not a free 2-adic path
        assert not (x % 3 == 2 and 2*x - 1 < 3*n)
        if q <= j <= q+L:
            assert y % M == M-1, (d,q,L,j)
            assert (y+1) % (1 << d) == 0
            assert (y+1) % (3**q) == 0
            assert v2(y+1) == K-j
            states.append((j, y % M, v2(y+1)))
        x = shortcut(x)
    assert len(states) == L+1
    assert len({residue for j,residue,valuation in states}) == 1
    return dict(d=d, q=q, stutter_transitions=L,
                K=K, source=n, source_residue=n%M,
                endpoint_residue=M-1, modulus=M,
                j_first=q, j_last=q+L,
                first_v2=K-q, last_v2=K-q-L,
                source_capped_returns_in_full_prefix=0,
                all_stutter_states_equal=True)

def main():
    cases = [(1,1,1),(1,1,15),(2,3,20),
             (6,6,50),(12,7,100),(16,9,130)]
    result = dict(
        schema="COLLATZ_V116_BIADIC_STUTTER_NO_GO",
        status="EXACT_SYMBOLIC_CONSTRUCTION_WITH_EXECUTABLE_REGRESSIONS",
        global_collatz="UNKNOWN", qed=False,
        theorem="For all d,q,L>=1, the positive source n=2^(d+q+L+1)-1 has L+1 consecutive actual iterates congruent to -1 modulo 2^d*3^q and no source-capped ternary return in that interval, starting at index q.",
        limitation="Only rejects ranks depending solely on fixed finite source/endpoint residues with bounded-delay strict-drop obligations; does not reject source-precision ranks with unbounded counters.",
        cases=[witness(*c) for c in cases])
    canonical = json.dumps(result, sort_keys=True, separators=(",",":"))
    result["payload_sha256"] = hashlib.sha256(canonical.encode()).hexdigest()
    print(json.dumps(result, sort_keys=True, indent=2))

if __name__ == "__main__":
    main()
