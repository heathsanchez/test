"""V114 independent reverse-affine audit: 9 unbounded congruence laws.

Mathematical boundary: verify every forward and reverse affine arithmetic
step once; exact linear base+slope inequalities imply the result for ALL
q>=0. Exhaustively intersect those laws with the V110 unknown CRT
classes. No assertion of global Collatz or universal natural-source bar.
"""
import hashlib
import json
from collections import Counter
from research.collatz_v108_reclosure import MODULUS as DYADIC, candidates
from research.collatz_v109_reverse_reclosure import reverse_witness
from research.collatz_v110_q7_crt_reclosure import TERNARY, PRODUCT, ternary_reverse, crt_base
from research.collatz_v113_three_laws_audit import LAWS as V113

LAWS = (
    ("a",1845,1727,"EEOEOEOOOOOO"),
    ("b",2631,2463,"EEOEOOEOOOOO"),
    ("c",1623,1519,"EEOEOOOEOOOO"),
    ("d",111,103,"EEOEOOOOEOOO"),
    ("e",2217,2075,"EEOEOOOOOEOO"),
    ("f",2221,2079,"EEOOEOEOOOOO"),
    ("g",1213,1135,"EEOOEOOEOOOO"),
    ("h",4075,3815,"EEOOEOOOEOOO"),
    ("i",1807,1691,"EEOOEOOOOEOO"),
)

def check_law(tag,n,p,w):
    # Exact shortcut on n + 4374*q for ALL q, using linear parity.
    assert n % 2 == 1 and 0 < p < n and 4096 < 4374
    x=(3*n+1)//2
    a=3*4374//2
    assert a==6561 and len(w)==12 and w.count("O")==8
    for op in w:
        if op=="E":
            x,a=2*x,2*a
        else:
            assert op=="O" and x>=2 and x%3==2 and a%3==0
            x,a=(2*x-1)//3,2*a//3
    assert (x,a)==(p,4096),(tag,x,a)

def main():
    for l in LAWS: check_law(*l)

    residual_r=[r for r in range(DYADIC)
                if not candidates(r) and reverse_witness(r) is None]
    residual_a=[a for a in range(TERNARY) if ternary_reverse(a) is None]
    assert (len(residual_r),len(residual_a))==(144,1174)

    seen=Counter()
    rows=[]
    for r in residual_r:
        for a in residual_a:
            n=crt_base(r,a)
            if any(n%law["modulus"]==law["base"] for law in V113):
                continue
            matches=[(tag,n0,p,w) for tag,n0,p,w in LAWS if n%4374==n0]
            assert len(matches)<=1
            if not matches:continue
            tag,n0,p0,w=matches[0]
            q=(n-n0)//4374
            assert q>=0 and n==n0+4374*q
            earlier=p0+4096*q
            assert 0<earlier<n
            assert PRODUCT%4374==0
            slope=4096*(PRODUCT//4374)
            assert slope<PRODUCT
            seen[tag]+=1
            rows.append((n,earlier,slope,tag))
    assert seen==Counter({tag:144 for tag,*_ in LAWS})
    assert len(rows)==1296
    assert len({n for n,*_ in rows})==1296
    payload=json.dumps(sorted(rows),separators=(",",":")).encode()
    result=dict(
        schema="COLLATZ_V114_NINE_CONGRUENCE_AUDIT",
        status="BOUNDED_EXECUTABLE_EXACT_GENERIC_LAWS",
        global_collatz="UNKNOWN",qed=False,
        source_modulus=PRODUCT,
        new_congruence_laws=[dict(tag=tag,n0=n,p0=p,
            source_slope=4374,earlier_slope=4096,forward_steps=1,
            reverse_steps=12,reverse_word=w) for tag,n,p,w in LAWS],
        newly_covered_crt_classes=len(rows),
        recovered_by_word=dict(sorted(seen.items())),
        v112_v113_previous_new=1701,
        total_new_since_v111=2997,
        total_covered_crt=8791893,
        unresolved_crt=166059,
        witness_digest_sha256=hashlib.sha256(payload).hexdigest(),
        natural_source_global_bar=False,
        individual_instances_lean_reified=False)
    print(json.dumps(result,sort_keys=True,indent=2))

if __name__=="__main__":
    main()
