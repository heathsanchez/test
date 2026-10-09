"""V142 finite exact qualifications; no finite sample proves unbounded recurrence."""
import json

def T(n):
    assert n > 0
    return n//2 if n%2==0 else (3*n+1)//2

def first_even(n):
    x=n
    u=n+1
    m=0
    while u%2==0:
        u//=2
        m+=1
    assert u>0 and u%2==1
    assert n+1==2**m*u
    for _ in range(m):
        assert x%2==1
        x=T(x)
    assert x%2==0
    assert x==3**m*u-1 and x>=n
    return m,x

def prefixes(n,depth):
    x=n
    values=[x]
    for _ in range(depth):
        x=T(x)
        values.append(x)
    return values

def audit(n,depth=200):
    values=prefixes(n,depth)
    max_odd=max((v for v in values if v%2==1),default=0)
    max_even=max((v for v in values if v%2==0),default=0)
    assert max(values)<=n+3*max_odd+1
    for B in (0,1,2,3,5,7,max_odd,max_odd+1):
        if all(v<=B for v in values if v%2==1):
            assert max(values)<=n+3*B+1
    return {"source":n,"sample_peak":max(values),
            "sample_even_peak":max_even,"sample_odd_peak":max_odd}

def main():
    nmax=12000
    checks=[first_even(n) for n in range(1,nmax+1)]
    sampled=[audit(n) for n in range(1,251)]
    assert all(y%2==0 and y>=n for n,(_,y) in enumerate(checks,1))
    mersenne=[]
    for k in (1,2,4,8,16,32,64,128):
        n=2**k-1
        m,y=first_even(n)
        assert m==k and y==3**k-1
        mersenne.append({"finite_odd_run_length":k,"start_digits":len(str(n)),
                         "first_even_not_below_source":y>=n})
    return {
      "schema":"COLLATZ_V142_UNBOUNDED_BOTH_PARITY_HEIGHTS",
      "finite_first_even_cases":nmax,
      "bounded_odd_to_bounded_whole_prefix_cases":len(sampled),
      "first_even_never_below_on_samples":True,
      "odd_bounded_implies_whole_bounded_on_sample_prefixes":True,
      "arbitrarily_long_finite_source_changing_prefixes":mersenne,
      "uniform_first_even_clock_claimed":False,
      "actual_unbounded_positive_orbit_exhibited":False,
      "global_nonterminal_cycle_excluded":False,
      "global_unbounded_trajectory_excluded":False,
      "global_collatz":"UNKNOWN",
      "qed":False
    }

if __name__=="__main__":
    print(json.dumps(main(),sort_keys=True,indent=2))
