"""V137: exact exhaustive regression for complete multiplier admission at fixed clocks.

For alpha,beta,i,j>=0 a positive integer coefficient pair (u,v)
is suitable for the V131 source-affine chart iff
    3^alpha*u = 3^beta*v,
    2^j*v <= 2^i*u.
This is equivalent to the fixed-clock guard
    2^j*3^alpha <= 2^i*3^beta.

Furthermore EVERY positive matched pair has form
    u = 3^max(beta-alpha,0)*t
    v = 3^max(alpha-beta,0)*t  for some t>=1.

Unlike numerical trial coverage, the universal proof is in Lean.
This exhaustive finite integer check is an independent negative control
against changes to exponent order, ratio or orientation.
"""
import hashlib,json

def coefficients(alpha,beta,t):
    assert alpha>=0 and beta>=0 and t>=1
    return 3**max(beta-alpha,0)*t,3**max(alpha-beta,0)*t

def guard(alpha,beta,i,j):
    return 2**j*3**alpha <= 2**i*3**beta

def audit():
    pairs=0
    witnesses=0
    for alpha in range(7):
        for beta in range(7):
            for u in range(1,151):
                for v in range(1,151):
                    if 3**alpha*u != 3**beta*v:
                        continue
                    pairs+=1
                    p,q=coefficients(alpha,beta,1)
                    assert u%p==0 and v%q==0
                    assert u//p==v//q>0
            for i in range(7):
                for j in range(7):
                    g=guard(alpha,beta,i,j)
                    p,q=coefficients(alpha,beta,1)
                    admitted=2**j*q <= 2**i*p
                    assert g==admitted,(alpha,beta,i,j)
                    witnesses+=1
                    for t in (1,2,7,100):
                        u,v=coefficients(alpha,beta,t)
                        assert 3**alpha*u==3**beta*v
                        assert (2**j*v<=2**i*u)==g
    # Real actual clock pairs of same sources, with opposite orientation.
    def T(n):
        return n//2 if n%2==0 else (3*n+1)//2
    def prefix(n,k):
        x=n;odd=0
        for _ in range(k):
            odd+=x%2
            x=T(x)
        return x,odd
    y1,alpha_good=prefix(5,1)
    z1,beta_good=prefix(3,2)
    y2,alpha_bad=prefix(5,3)
    z2,beta_bad=prefix(3,8)
    assert y1==z1==8 and y2==z2==2
    assert (alpha_good,beta_good)==(1,2)
    assert (alpha_bad,beta_bad)==(1,4)
    assert guard(alpha_good,beta_good,1,2)
    assert not guard(alpha_bad,beta_bad,3,8)
    goodu,goodv=coefficients(alpha_good,beta_good,1)
    badu,badv=coefficients(alpha_bad,beta_bad,1)
    assert (goodu,goodv)==(3,1)
    assert (badu,badv)==(27,1)
    assert 2**2*goodv==4<=6==2**1*goodu
    assert 2**8*badv==256>216==2**3*badu

    result=dict(
        schema="COLLATZ_V137_EXHAUSTIVE_PRIMITIVE_MULTIPLIER_BOUNDARY",
        status="BOUNDED_EXACT_REGRESSION_AND_FORMAL_CANDIDATE",
        exponents_tested=[0,6],
        coefficient_upper_bound=150,
        exactly_matched_positive_pairs_tested=pairs,
        fixed_clock_guard_cases_tested=witnesses,
        primitive_positive_pair_shape="u=3^max(beta-alpha,0)*t;v=3^max(alpha-beta,0)*t",
        all_matched_pairs_are_primitive_scalings=True,
        positive_multiplier_existence_iff_weighted_clock=True,
        favourable_source5_to3=dict(clocks=[1,2],odds=[1,2],
            minimum_coefficients=[3,1],original_source_slope=6,
            earlier_source_slope=4,meeting_endpoint=8),
        rejected_source5_to3=dict(clocks=[3,8],odds=[1,4],
            minimum_coefficients=[27,1],original_source_slope=216,
            earlier_source_slope=256,meeting_endpoint=2),
        failure_means_ONLY_fixed_clock_coefficient_grammar_impossible=True,
        universal_source_coalescence="UNKNOWN",
        global_collatz="UNKNOWN",qed=False,
    )
    canon=json.dumps(result,sort_keys=True,separators=(",",":"))
    result["payload_sha256"]=hashlib.sha256(canon.encode()).hexdigest()
    print(json.dumps(result,indent=2,sort_keys=True))

if __name__=="__main__":
    audit()
