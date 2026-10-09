"""V112: lawful alternative reverse paths on V110's unresolved CRT source families.

No global Collatz proof. Every admitted witness satisfies exact all-offset
affine identities and the ORIGINAL source guard 0 < p(q) < n(q).
V111 tested only the preferred endpoint q7 reverse word, not all continuations.
"""
import json
from collections import Counter
from research.collatz_v108_reclosure import MODULUS as DYADIC, candidates, shortcut
from research.collatz_v109_reverse_reclosure import reverse_witness
from research.collatz_v110_q7_crt_reclosure import (
    TERNARY, PRODUCT, ternary_reverse, crt_base
)

MAX_REVERSE = 10

def prefixes(n):
    x, odd = n, 0
    for j in range(1, 13):
        odd += x % 2
        x = shortcut(x)
        a = (DYADIC >> j) * 3**odd * TERNARY
        yield j, x, odd, a

def search(n):
    for j, x, odd, a in prefixes(n):
        states = [(x, a, "")]
        seen = {(x, a)}
        for depth in range(1, MAX_REVERSE + 1):
            remain = MAX_REVERSE - depth
            nxt = []
            for b, c, word in states:
                bb, cc = 2*b, 2*c
                if bb > 0 and (bb,cc) not in seen and cc*2**remain <= PRODUCT*3**remain:
                    nxt.append((bb, cc, word+"E"))
                    seen.add((bb,cc))
                if b >= 2 and b%3 == 2 and c%3 == 0:
                    bb, cc = (2*b-1)//3, 2*c//3
                    assert 3*bb+1 == 2*b and 3*cc == 2*c
                    if bb > 0 and (bb,cc) not in seen and cc*2**remain <= PRODUCT*3**remain:
                        nxt.append((bb, cc, word+"O"))
                        seen.add((bb,cc))
            for b,c,word in nxt:
                if 0 < b < n and c <= PRODUCT:
                    return dict(original_source=n, forward_prefix=j,
                                endpoint=x, endpoint_slope=a,
                                earlier_source=b, predecessor_slope=c,
                                reverse_word=word)
            states = nxt
            if not states:
                break
    return None

def independently_verify(n,w):
    j, x, a = w["forward_prefix"],w["endpoint"],w["endpoint_slope"]
    p, c, word = w["earlier_source"],w["predecessor_slope"],w["reverse_word"]
    assert 1 <= j <= 12 and len(word) <= MAX_REVERSE
    assert 0 < p < n and 0 <= c <= PRODUCT
    y=n
    odd=0
    for _ in range(j):
        odd+=y%2
        y=shortcut(y)
    assert y == x and a == (DYADIC >> j)*3**odd*TERNARY
    v,z=x,a
    for op in word:
        if op=="E":
            v,z=2*v,2*z
        else:
            assert op=="O" and v>=2 and v%3==2 and z%3==0
            old_v,old_z=v,z
            v,z=(2*v-1)//3,2*z//3
            assert 3*v+1==2*old_v and 3*z==2*old_z
    assert (v,z) == (p,c)
    for q in (0,1,2,7):
        source=n+PRODUCT*q
        endpoint=source
        for _ in range(j): endpoint=shortcut(endpoint)
        assert endpoint==x+a*q
        precursor=p+c*q
        assert 0 < precursor < source
        target=precursor
        for _ in word: target=shortcut(target)
        assert target==endpoint

def main():
    old_unknown=[r for r in range(DYADIC)
                 if not candidates(r) and reverse_witness(r) is None]
    ternary_unknown=[a for a in range(TERNARY) if ternary_reverse(a) is None]
    assert len(old_unknown)==144 and len(ternary_unknown)==1174
    records=[]
    for r in old_unknown:
        for a in ternary_unknown:
            n=crt_base(r,a)
            w=search(n)
            if w:
                independently_verify(n,w)
                records.append(dict(dyadic_residue=r,ternary_residue=a,**w))
    assert len(records)==1701
    assert len({v["dyadic_residue"] for v in records})==144
    words=Counter(w["reverse_word"] for w in records)
    assert dict(words)=={
        "EEOEOOOOOO":432,
        "EEOOEOOOOO":432,
        "EEOOOEOOOO":837
    }
    result=dict(schema="COLLATZ_V112_ALT_REVERSE_SOURCE_MERGERS",
                status="BOUNDED_EXECUTABLE_EXACT",
                global_collatz="UNKNOWN",qed=False,
                source_modulus=PRODUCT,depth=12,reverse_budget=MAX_REVERSE,
                previously_unresolved_crt=169056,
                newly_merged_crt=len(records),
                still_unresolved_crt=169056-len(records),
                total_covered_crt=8788896+len(records),
                reverse_word_counts=dict(words),
                individual_witnesses_lean_reified=False,
                natural_source_global_bar=False,
                records=records)
    print(json.dumps(result,sort_keys=True,indent=2))

if __name__=="__main__":
    main()
