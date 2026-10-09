"""V136 exact chart reduction: cancel common 3-adic factors in V135.

For actual shortcut prefixes with odd counts alpha and beta, choose
  u=3**max(beta-alpha,0), v=3**max(alpha-beta,0).
These exact coefficients satisfy 3**alpha*u=3**beta*v.
Previous V135 canonical coefficients are (3**beta,3**alpha);
they multiply both reduced coordinates by 3**min(alpha,beta).

This is a strict *representation refinement* on every tested positive
source family where min(alpha,beta)>0. It does not imply the existence
of a base coalescence or favourable clock for all natural sources.
"""
import hashlib
import json

FAMILIES=[
    (21,3,3,2),
    (9,3,9,1),
    (15,3,8,1),
    (23,3,7,1),
    (5,3,1,2),
    (27,23,59,0),
]
def T(n):
    assert n>0
    return n//2 if n%2==0 else (3*n+1)//2

def step(b,s):
    if s%2:
        raise ValueError("parity cylinder coefficient not even at this step")
    return (b//2,s//2) if b%2==0 else ((3*b+1)//2,3*s//2)

def count(base,k):
    n=base;odds=0
    for _ in range(k):
        odds+=n%2
        n=T(n)
    return n,odds

def chart(a,i,u):
    b,s=a,(1<<i)*u
    o=0;path=[(b,s)]
    for _ in range(i):
        o+=b%2
        b,s=step(b,s)
        path.append((b,s))
    assert s==3**o*u
    return dict(base=a,clock=i,odd_count=o,
        source_slope=(1<<i)*u,
        endpoint_intercept=b,endpoint_slope=s,
        affine_prefix=path)

def audit(a,p,i,j):
    ya,alpha=count(a,i)
    yp,beta=count(p,j)
    assert 0<p<a and ya==yp
    u=3**max(beta-alpha,0)
    v=3**max(alpha-beta,0)
    U=3**beta
    V=3**alpha
    m=3**min(alpha,beta)
    assert U==u*m and V==v*m
    assert 3**alpha*u==3**beta*v
    source=chart(a,i,u)
    pred=chart(p,j,v)
    assert source["endpoint_intercept"]==pred["endpoint_intercept"]
    assert source["endpoint_slope"]==pred["endpoint_slope"]
    assert source["source_slope"]>=pred["source_slope"]
    assert 0<p<a
    old_source_slope=(1<<i)*U
    old_pred_slope=(1<<j)*V
    assert old_source_slope==m*source["source_slope"]
    assert old_pred_slope==m*pred["source_slope"]
    samples=[]
    for t in (0,1,2,3,7,31):
        n=a+source["source_slope"]*t
        q=p+pred["source_slope"]*t
        assert 0<q<n
        nx,px=n,q
        for _ in range(i):nx=T(nx)
        for _ in range(j):px=T(px)
        assert nx==px==source["endpoint_intercept"]+source["endpoint_slope"]*t
        samples.append(dict(t=t,original_source=n,earlier=q,
                            source_clock=i,earlier_clock=j,
                            common_endpoint=nx))
    return dict(base_source=a,base_earlier=p,
        source_clock=i,earlier_clock=j,odds_source=alpha,odds_earlier=beta,
        reduced_multiplier_u=u,reduced_multiplier_v=v,
        old_multiplier_u=U,old_multiplier_v=V,
        old_to_reduced_parameter_dilation=m,
        source_chart=source,earlier_chart=pred,samples=samples)

def main():
    all_cases=[audit(*x) for x in FAMILIES]
    expect=[(24,4),(512,162),(256,54),(128,18),(6,4),(2**59,3**37)]
    assert [(w["source_chart"]["source_slope"],w["earlier_chart"]["source_slope"])
            for w in all_cases]==expect
    assert [w["old_to_reduced_parameter_dilation"] for w in all_cases]==[3,3,3,3,3,1]
    assert all_cases[0]["samples"][1]["original_source"]==45
    assert all_cases[0]["samples"][1]["earlier"]==7
    assert all_cases[0]["samples"][1]["common_endpoint"]==17
    assert 45%6==3 and 7%3==1  # source root type preserved, earlier not root
    assert all_cases[1]["samples"][1]["original_source"]==521
    assert all_cases[1]["samples"][1]["earlier"]==165
    assert all_cases[1]["samples"][1]["common_endpoint"]==248
    assert all_cases[5]["old_to_reduced_parameter_dilation"]==1
    result=dict(
        schema="COLLATZ_V136_REDUCED_THREE_POWER_SOURCE_CHARTS",
        status="EXACT_AFFINE_REPRESENTATION_REDUCTION_FORMAL_CANDIDATE",
        canonical_coefficients="u=3^max(beta-alpha,0), v=3^max(alpha-beta,0)",
        old_chart_is_reduced_subfamily="old t equals reduced parameter 3^min(alpha,beta)*t",
        checked_all_offset_chart_count=len(all_cases),
        strictly_broader_charts=5,
        unaffected_zero_min_chart=1,
        new_source45_earlier7_meeting_at_3_2=True,
        source45_is_odd_three_root=True,
        predecessor7_is_not_three_root=True,
        results=all_cases,
        universal_base_meeting_existence=False,
        universal_weighted_clock_orientation=False,
        global_collatz="UNKNOWN",qed=False)
    canonical=json.dumps(result,sort_keys=True,separators=(",",":"))
    result["payload_sha256"]=hashlib.sha256(canonical.encode()).hexdigest()
    print(json.dumps(result,sort_keys=True,indent=2))

if __name__=="__main__":
    main()
