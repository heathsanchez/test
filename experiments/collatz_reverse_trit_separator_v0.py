#!/usr/bin/env python3
"""Exact first-difference reverse-trit separator audit at the live Farey resonance.

This is a theorem-discovery audit, not a Collatz proof.

It freezes the first dangerous Farey resonance and independently reconstructs
the final 20 reverse Complete-O exponents of the extremal latest-odd word.
For every first differing 3-adic digit relative to that extremal reverse
centre, it asks whether an already-known coefficient-contracting reverse
predecessor certificate of at most that depth applies to the entire cylinder.

A contracting reverse certificate p(y)=(2^S y-C)/3^o is additionally checked
against the certified live interval and near-return gap G, so p < y-G <= n.
Thus a closed class gives an honest lower merge for any hypothetical live seed
in that class. Any class not closed is emitted as an explicit symbolic
separator; it is never silently promoted.
"""
from __future__ import annotations
import argparse, json
from functools import lru_cache
from pathlib import Path

import collatz_transfer_farey as farey

G = 4_142_380_787
L = farey.L
Q, T = farey.q1, farey.t1
DEPTH = 20


def floor_frac(x):
    return x.numerator // x.denominator


def extremal_reverse_actions(depth=DEPTH):
    """Certify last depth reverse exponents of the latest-odd extremal word."""
    beta_lo = farey.ln3_lo / farey.ln2_hi
    beta_hi = farey.ln3_hi / farey.ln2_lo
    cumulative = [0]
    positions = []
    for k in range(1, depth + 1):
        jminus1 = Q - k
        lo = jminus1 * beta_lo
        hi = jminus1 * beta_hi
        flo = floor_frac(lo)
        fhi = floor_frac(hi)
        assert flo == fhi, ("uncertified mechanical position", k, flo, fhi)
        positions.append(flo)
        cumulative.append(T - flo)
    acts = [cumulative[k] - cumulative[k-1] for k in range(1, depth+1)]
    for k,S in enumerate(cumulative[1:],1):
        assert (1 << (S-1)) < 3**k < (1 << S), (k,S)
    return acts, cumulative[1:], positions


def terminal_residue(actions):
    """Unique endpoint residue mod 3^j on which all reverse O-blocks are legal."""
    S = 0
    C = 0
    for idx,a in enumerate(actions):
        S += a
        C = (1 << a) * C + 3**idx
    M = 3**len(actions)
    return (C * pow(1 << S, -1, M)) % M


def cocycle(actions):
    S=0
    C=0
    for idx,a in enumerate(actions):
        S += a
        C = (1 << a) * C + 3**idx
    return S,C


@lru_cache(None)
def contracting_word(j, r, budget):
    """Return one exact reverse action tuple of length j and cost <= budget."""
    if j == 0:
        return ()
    if budget < j:
        return None
    mod = 3**j
    r %= mod
    if r % 3 == 0:
        return None
    tailmod = 3**(j-1)
    start = 2 if r % 3 == 1 else 1
    for a in range(start, budget-(j-1)+1, 2):
        z = (pow(2,a,mod) * r - 1) % mod
        if z % 3:
            continue
        rp = (z // 3) % tailmod if j > 1 else 0
        tail = contracting_word(j-1, rp, budget-a)
        if tail is not None:
            return (a,) + tail
    return None


def best_contracting_prefix(r, depth):
    """Find a coefficient-contracting reverse certificate at some o<=depth."""
    for o in range(1, depth+1):
        ro = r % (3**o)
        budget = (3**o).bit_length() - 1
        w = contracting_word(o, ro, budget)
        if w is None:
            continue
        S,C = cocycle(w)
        assert S <= budget and (1 << S) < 3**o
        assert terminal_residue(w) == ro
        assert (1 << S) * L - C > 0
        assert ((3**o - (1 << S))*L + C) > (3**o)*G
        M=3**o
        y = ro + ((L-ro + M-1)//M)*M
        p = ((1 << S)*y - C)//M
        assert 0 < p < y-G
        x=p
        for a in reversed(w):
            assert x & 1
            x=(3*x+1)//2
            for _ in range(a-1):
                assert x % 2 == 0
                x//=2
        assert x == y, (w,ro,p,y,x)
        return dict(odd_inverse_steps=o, actions=list(w), S=S, C=C,
                    residue=ro, modulus=M, sample_y=y, sample_p=p)
    return None


def run(output: Path):
    acts,cums,positions=extremal_reverse_actions()
    expected=[2,2,1,2,1,2,2,1,2,1,2,2,1,2,1,2,1,2,2,1]
    assert acts == expected, acts
    rows=[]
    closed=0
    first_survivor=None
    centre_prefix=[]
    for j in range(1,DEPTH+1):
        qj = terminal_residue(tuple(acts[:j]))
        if j>1:
            assert qj % (3**(j-1)) == centre_prefix[-1]
        centre_prefix.append(qj)
        base = qj % (3**(j-1)) if j>1 else 0
        qdigit = (qj // (3**(j-1))) % 3
        for digit in range(3):
            if digit == qdigit:
                continue
            r = base + digit*3**(j-1)
            cert = best_contracting_prefix(r,j)
            status = "LOWER_MERGE" if cert is not None else "RESIDUAL"
            closed += cert is not None
            row=dict(first_difference_depth=j-1, depth=j,
                     centre_residue=qj, centre_digit=qdigit,
                     alternate_digit=digit, alternate_residue=r,
                     modulus=3**j, status=status, certificate=cert)
            rows.append(row)
            if cert is None and first_survivor is None:
                first_survivor=row

    result=dict(
        schema="COLLATZ_REVERSE_TRIT_SEPARATOR_V0",
        resonance=dict(q=Q,t=T,live_lower=L,near_return_gap=G),
        extremal_reverse_actions=acts,
        extremal_cumulative_costs=cums,
        classes=len(rows), closed=closed, residual=len(rows)-closed,
        first_survivor=first_survivor,
        rows=rows,
        verdict=("PASS_ALL_EXTREMAL_FIRST_DIFFERENCES_CLOSE"
                 if closed==len(rows)
                 else "EXACT_SYMBOLIC_SEPARATOR_REMAINS"),
        scope=("extremal latest-odd first-resonance suffix only; coefficient-contracting "
               "reverse predecessor certificates; no universal Collatz claim")
    )
    output.parent.mkdir(parents=True,exist_ok=True)
    output.write_text(json.dumps(result,indent=2,sort_keys=True)+"\n")
    print("EXTREMAL_REVERSE_ACTIONS",acts)
    print("CLASSES",len(rows),"CLOSED",closed,"RESIDUAL",len(rows)-closed)
    print("FIRST_SURVIVOR",json.dumps(first_survivor,sort_keys=True))
    for row in rows:
        print("CLASS",json.dumps({k:row[k] for k in
              ("first_difference_depth","centre_digit","alternate_digit",
               "alternate_residue","modulus","status")},sort_keys=True))
    print("VERDICT",result["verdict"])


if __name__=="__main__":
    ap=argparse.ArgumentParser()
    ap.add_argument("--output",type=Path,required=True)
    a=ap.parse_args()
    run(a.output)
