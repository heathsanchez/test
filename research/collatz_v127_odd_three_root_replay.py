"""V127 exact replay of two-clock quotient to odd positive multiples of three.

A class-representation transport is NOT a lower-source descent rule; the
odd three-root may be larger than the original target. No universal QED.
"""
import json,hashlib
from research.collatz_v126_three_root_normal_form import normalize,T,replay

def odd_root_view(n):
    p,k=normalize(n)
    r=p
    a=0
    while r%2==0:
        r=T(r)
        a+=1
    assert r%2==1 and r%3==0 and r>0
    assert replay(n,a)==replay(r,k), (n,p,r,a,k)
    return dict(source=n,odd_three_root=r,
        source_clock=a,root_clock=k,
        endpoint=replay(n,a),
        source_has_lower_root=r<n)

def main():
    cases=[odd_root_view(n) for n in range(1,15001)]
    examples=[odd_root_view(n) for n in (1,2,3,6,7,11,21,27,81,144,729,1000,4096)]
    assert odd_root_view(1)['odd_three_root']==21
    assert odd_root_view(7)['odd_three_root']==9
    assert odd_root_view(27)['source_clock']==0
    assert odd_root_view(27)['root_clock']==0
    # Canonical right inverse is source-identity at all odd three-roots.
    for t in range(2000):
        root=6*t+3
        target=T(root)
        assert target==9*t+5
        assert normalize(target)==(root,1)
    result=dict(
        schema="COLLATZ_V127_ODD_THREE_ROOT_TWO_CLOCK_CLASS_NORMALIZATION",
        status="BOUNDED_EXACT_PLUS_FORMAL_CANDIDATE",
        verified_finite_n=len(cases),
        positive_sources_with_larger_root=sum(r['odd_three_root']>r['source'] for r in cases),
        negative_control_root_of_one=odd_root_view(1),
        negative_control_root_of_seven=odd_root_view(7),
        actual_two_clock_examples=examples,
        canonical_odd_root_stutter_checks=2000,
        strict_lower_source_claim=False,
        universal_termination_of_odd_three_roots="UNKNOWN",
        global_collatz="UNKNOWN",qed=False)
    canon=json.dumps(result,sort_keys=True,separators=(",",":"))
    result["payload_sha256"]=hashlib.sha256(canon.encode()).hexdigest()
    print(json.dumps(result,sort_keys=True,indent=2))

if __name__=="__main__":
    main()
