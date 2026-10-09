"""V138 exact two-clock affine source27→odd-three-root lift.

Prior formally verified:
  T^59(27)=23,
  T^7(23)=T(3)=5,
  hence T^66(27)=T(3)=5.
The V136/V137 reduced all-offset chart rule then yields:
  n(t)=27+2^66*t,
  p(t)=3+2*3^39*t,  0<p(t)<n(t),
  T^66(n(t))=T(p(t))=5+3^40*t.

Important: n(t) is inside the ALREADY formally certified V120
source cylinder 27+2^59*q at q=128*t. No new CRT coverage.
The new capability is an explicit earlier ODD 3-root with its real
asynchronous clocks and a checked source-relative strong induction
predecessor. Global Collatz remains UNKNOWN.
"""
import hashlib,json

def T(n):
    if n<=0:raise ValueError("positive shortcut domain only")
    return n//2 if n%2==0 else (3*n+1)//2

def step(b,s):
    assert s%2==0
    return (b//2,s//2) if b%2==0 else ((3*b+1)//2,3*s//2)

def symbolic(base,slope,steps):
    b,s=base,slope
    records=[(b,s)]
    for _ in range(steps):
        b,s=step(b,s)
        records.append((b,s))
    return records

def main():
    two66=2**66
    three39=3**39
    three40=3**40
    source=symbolic(27,two66,66)
    earlier=symbolic(3,2*three39,1)
    direct=symbolic(27,two66,59)
    assert source[-1]==earlier[-1]==(5,three40)
    assert direct[-1]==(23,128*3**37)
    assert source[59]==direct[-1]
    assert 2*three39<two66
    assert two66==128*2**59
    cases=[]
    for t in (0,1,2,7,33,128):
        n=27+two66*t
        p=3+2*three39*t
        assert 0<p<n and p%6==3
        x=n
        for _ in range(66):
            x=T(x)
        y=T(p)
        assert x==y==5+three40*t
        z=n
        for _ in range(59):
            z=T(z)
        assert z==23+128*(3**37)*t<n
        assert n==27+(2**59)*(128*t)
        cases.append(dict(t=t,source=n,earlier=p,
            source_clock=66,earlier_clock=1,common=x,
            existing_direct_clock=59,direct_endpoint=z))
    result=dict(
        schema="COLLATZ_V138_PRIMITIVE_SOURCE27_ROOT3_LIFT",
        status="EXACT_SYMBOLIC_AND_FORMAL_CANDIDATE",
        source_base=27,source_slope=two66,
        earlier_base=3,earlier_slope=2*three39,
        source_clock=66,earlier_clock=1,
        source_odd_count_66=40,earlier_odd_count_1=1,
        common_endpoint_intercept=5,common_endpoint_slope=three40,
        v120_original_source_subfamily_factor=128,
        old_v120_direct_descent_clock=59,
        original_root3_join_authority="V133 run 37988274186",
        qualifier="NEW root-normalized earlier source; NOT new convergence coverage",
        exact_affine_prefix_source=source,
        exact_affine_prefix_earlier=earlier,
        exact_affine_prefix_direct=direct,
        independent_samples=cases,
        root3_future_source_guaranteed_positive=True,
        entire_original_V120_CRT_family_closed=False,
        universal_odd_root_event_production=False,
        global_collatz="UNKNOWN",qed=False
    )
    serial=json.dumps(result,sort_keys=True,separators=(",",":"))
    result['payload_sha256']=hashlib.sha256(serial.encode()).hexdigest()
    print(json.dumps(result,sort_keys=True,indent=2))

if __name__=="__main__":main()
