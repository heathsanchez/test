"""V126 exact all-offset source->3-root normal form.

Six uniformly admissible legal shortcut affine families jointly cover every
positive residue not divisible by three. Every p chosen by the map is a
positive MULTIPLE OF THREE, but it may exceed the target n. Therefore this
is a protected future-CLASS normalization, not a source-descent witness.

The universal statements are checked separately by pinned Lean.
"""
import hashlib
import json

RULES=(
    (1,6,21,192),
    (2,5,21,96),
    (4,4,21,48),
    (5,1,3,6),
    (7,2,9,12),
    (8,3,21,24),
)

def T(n):
    if n<=0: raise ValueError("must stay positive")
    return n//2 if n%2==0 else (3*n+1)//2

def affine_step(b,s):
    assert s%2==0, "source-affine parity not fixed for ALL offsets"
    return (b//2,s//2) if b%2==0 else ((3*b+1)//2,3*s//2)

def normalize(n):
    assert n>0
    if n%3==0: return n,0
    rem=n%9
    r,k,b,s=next(row for row in RULES if row[0]==rem)
    return b+s*(n//9),k

def replay(n,k):
    for _ in range(k):
        n=T(n)
    return n

def audit():
    rows=[]
    for r,k,b,s in RULES:
        x,a=b,s
        assert b>0 and b%3==0 and s%3==0
        for j in range(k):
            x,a=affine_step(x,a)
        assert (x,a)==(r,9),(r,k,b,s,x,a)
        # Five independent integer samples are NOT the certificate;
        # symbolic intercept+slope is the all-offset certificate.
        for t in (0,1,2,7,31):
            assert replay(b+s*t,k)==9*t+r
        rows.append(dict(residue_mod9=r,clock=k,source_intercept=b,
                        source_slope=s,endpoint_intercept=x,endpoint_slope=a))
    cases=0
    larger=0
    unchanged=0
    for n in range(1,20001):
        p,k=normalize(n)
        assert 0<p and p%3==0 and k<=6 and replay(p,k)==n
        cases+=1
        larger+=p>n
        unchanged+=p==n
    assert normalize(1)==(21,6)
    assert normalize(2)==(21,5)
    for t in range(1000):
        root=6*t+3
        succ=T(root)
        assert succ==9*t+5
        assert normalize(succ)==(root,1)
    result={
        "schema":"COLLATZ_V126_THREE_ROOT_CLASS_NORMALIZATION",
        "status":"EXACT_SYMBOLIC_ALL_OFFSET_RULES_FORMAL_CANDIDATE",
        "rule_count":len(RULES),"exact_family_rules":rows,
        "every_positive_n_has_p_divisible_by3_with_clock_at_most6":True,
        "positive_integer_replays":cases,
        "non_smaller_root_replays":larger,
        "root_identity_replays":unchanged,
        "negative_control_root_of_1":21,
        "odd_three_root_stutters_under_canonical_normalization":True,
        "ROOT_TRANSPORT_IS_NOT_A_LOWER_SOURCE_MERGER":True,
        "universal_Collatz_proof":False,
        "global_collatz":"UNKNOWN","qed":False
    }
    serialized=json.dumps(result,sort_keys=True,separators=(",",":"))
    result["payload_sha256"]=hashlib.sha256(serialized.encode()).hexdigest()
    print(json.dumps(result,sort_keys=True,indent=2))

if __name__=="__main__":
    audit()
