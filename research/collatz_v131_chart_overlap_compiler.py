"""V131 exact compiler for overlapping two-clock source-affine parity charts.

Each lawful chart is the semantic map
    (a,i,u) -> T^i(a + 2^i*u*t)
             = T^i(a) + 3^oddCount(a,i)*u*t.

To merge source chart (a,i,u) into p-chart (p,j,v), verify:
    0<p<a,
    2^j*v <= 2^i*u,
    T^i(a)=T^j(p),
    3^oddCount(a,i)*u=3^oddCount(p,j)*v.
Then all offsets t>=0 admit T^i(n(t))=T^j(p(t)) and p(t)<n(t).

The generic rule is kernel checked in Lean; here every affine arithmetic
premise and true shortcut parity step is independently replayed.
"""
import json
import hashlib

def T(n):
    assert n>0
    return n//2 if n%2==0 else (3*n+1)//2

def step(b,s):
    assert s%2==0, "affine slope cannot change parity across offsets"
    return (b//2,s//2) if b%2==0 else ((3*b+1)//2,3*s//2)

def chart(a,i,u):
    assert min(a,i,u)>0
    n_slope=(2**i)*u
    current=(a,n_slope)
    odds=0
    prefix=[current]
    for k in range(i):
        odds+=current[0]%2
        current=step(*current)
        prefix.append(current)
    assert current[1]==3**odds*u
    return dict(base=a,clock=i,u=u,
        original_source_slope=n_slope,
        odd_count=odds,
        endpoint_intercept=current[0],
        endpoint_slope=current[1],
        actual_affine_prefix=prefix)

def qualify(a,p,i,j,u,v):
    assert 0<p<a
    source=chart(a,i,u)
    earlier=chart(p,j,v)
    assert earlier['original_source_slope']<=source['original_source_slope']
    assert source['endpoint_intercept']==earlier['endpoint_intercept']
    assert source['endpoint_slope']==earlier['endpoint_slope']
    assert a%6==p%6==3
    assert source['original_source_slope']%6==earlier['original_source_slope']%6==0
    samples=[]
    for t in (0,1,2,7,31,1000):
        n=a+source['original_source_slope']*t
        q=p+earlier['original_source_slope']*t
        assert 0<q<n and n%6==q%6==3
        x,y=n,q
        for _ in range(i):x=T(x)
        for _ in range(j):y=T(y)
        assert x==y==source['endpoint_intercept']+source['endpoint_slope']*t
        samples.append(dict(t=t,source=n,earlier=q,
            source_clock=i,earlier_clock=j,common_endpoint=x))
    return dict(source=source,earlier=earlier,samples=samples)

def main():
    old=qualify(21,3,3,2,9,3)
    new=qualify(9,3,9,1,3,243)
    assert old['source']['original_source_slope']==72
    assert old['earlier']['original_source_slope']==12
    assert old['source']['endpoint_intercept']==8
    assert old['source']['endpoint_slope']==27
    assert new['source']['original_source_slope']==1536
    assert new['earlier']['original_source_slope']==486
    assert new['source']['endpoint_intercept']==5
    assert new['source']['endpoint_slope']==729
    assert new['source']['odd_count']==5
    assert new['earlier']['odd_count']==1
    result=dict(schema="COLLATZ_V131_TWO_CLOCK_AFFINE_CHART_OVERLAP",
        status="EXACT_GENERIC_CHART_PREMISES_FORMAL_CANDIDATE",
        compiler_signature="source (a,i,u), earlier (p,j,v), t in Nat",
        prior_v129_root21_family=old,
        new_root9_family=new,
        source9_claim="T^9(9+1536*t)=5+729*t=T(3+486*t); 0<earlier<source",
        chart_count=2,
        strict_smaller_source_required=True,
        two_independent_clocks_protected=True,
        lower_source_guard_false_at_equal_origins=True,
        no_universal_root_coverage_claim=True,
        global_collatz="UNKNOWN",qed=False)
    canonical=json.dumps(result,sort_keys=True,separators=(",",":"))
    result['payload_sha256']=hashlib.sha256(canonical.encode()).hexdigest()
    print(json.dumps(result,sort_keys=True,indent=2))

if __name__=="__main__":
    main()
