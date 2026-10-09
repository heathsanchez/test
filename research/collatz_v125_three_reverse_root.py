"""V125 independent exact regression: 3-divisible endpoint has ONLY the doubling-ray inverse.

The general statement is proved in Lean, not inferred from these samples.
This executable verifies the parity/divisibility constraints and provides
the protected source-27 dyadic-lift separator. Global Collatz UNKNOWN.
"""
import hashlib
import json

POW2_59 = 2**59
SOURCE_27_FIRST_CLOCK = 59

def shortcut(n):
    return n//2 if n%2==0 else (3*n+1)//2

def iterate(n, k):
    for _ in range(k):
        n = shortcut(n)
    return n

def run():
    samples=0
    for y in range(3,3001,3):
        for k in (0,1,2,3,5,8,12,30,50):
            p=(1<<k)*y
            assert iterate(p,k)==y
            samples+=1
    # Inspect all actual one-step predecessors of multiples of 3 in
    # a concrete interval. The unrestricted result is the Lean theorem.
    for x in range(1,30001):
        y=shortcut(x)
        if y%3==0:
            assert x==2*y and x%2==0

    # Exact 34-state smaller-source forward envelope (V121/122).
    envelope=set(range(1,27))|{29,32,35,38,40,44,53,80}
    assert len(envelope)==34 and 83 not in envelope
    assert all(shortcut(x) in envelope for x in envelope)
    x=27
    for k in range(59):
        assert x not in envelope, (k,x)
        x=shortcut(x)
    assert x==23 and x in envelope

    lifted=[]
    for t in (0,1,2,7,13,37):
        q=3*t+1
        n=27+POW2_59*q
        p=(2*n-1)//3
        assert n%3==2
        assert (2*n-1)%3==0 and 0<p<n
        assert shortcut(p)==n
        assert n==576460752303423515+1729382256910270464*t
        assert p==384307168202282343+1152921504606846976*t
        assert n%POW2_59==27
        lifted.append(dict(t=t,dyadic_offset=q,source=n,earlier=p,
                           source_clock=0,earlier_clock=1))

    result=dict(
        schema="COLLATZ_V125_THREE_REVERSE_ROOT_AND_DYADIC_SOURCE_SEPARATION",
        status="BOUNDED_EXACT_REGRESSION_PLUS_GENERIC_LEAN_CANDIDATE",
        reverse_ray_replay_cases=samples,
        source27_first_lower_clock=SOURCE_27_FIRST_CLOCK,
        generic_three_root="all reverse k sources from n%3=0 equal 2**k*n",
        source27_lift_family=dict(modulus=POW2_59,parity_residue=27,
            zero_clock_if_offset_mod3_eq1=True,
            infinite_affine_family=True),
        samples=lifted,
        universal_termination_claim=False,
        global_collatz="UNKNOWN",qed=False)
    canonical=json.dumps(result,sort_keys=True,separators=(",",":"))
    result["payload_sha256"]=hashlib.sha256(canonical.encode()).hexdigest()
    print(json.dumps(result,sort_keys=True,indent=2))

if __name__=="__main__":
    run()
