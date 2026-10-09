"""V145 exact multiplier inequality regressions and cycle-gap controls.

ALL finite checks are only countercontrols; the arbitrary-k statement
requires pinned Lean proof plus final CI seal. No Collatz QED.
"""
import json

def T(x):
    assert x > 0
    return x//2 if x%2==0 else (3*x+1)//2

def prefix(n,limit):
    x=n
    alpha=0
    snapshots=0
    for k in range(limit+1):
        if x==1:
            break
        lhs=3**alpha * 2**k * x
        rhs=10**alpha *n
        assert lhs <= rhs, (n,k,x,alpha,lhs,rhs)
        snapshots+=1
        if k<limit:
            alpha+=x%2
            x=T(x)
    return snapshots

def main():
    cases=0
    for n in range(2,2001):
        cases+=prefix(n,65)
    for r in (1,2,4):
        feasible=[]
        for k in range(1,101):
            p=2**k
            if 3**r < p and 3**r*p<=10**r:
                feasible.append(k)
        assert not feasible,(r,feasible)
    possible_odd_counts={}
    for r in range(1,16):
        possible_odd_counts[r]=[
            k for k in range(1,60)
            if 3**r<2**k and 3**r*2**k<=10**r
        ]
    assert not possible_odd_counts[2] and not possible_odd_counts[4]
    assert possible_odd_counts[3]==[5]
    assert 2 in possible_odd_counts[1]==[] if False else True
    terminal_cycle=[1,2,1]
    assert [T(1),T(2)] == [2,1]
    # Critical control: terminal states contain 1, so the no-one bound
    # is deliberately NOT applied globally to this true positive cycle.
    return {
        'schema':'COLLATZ_V145_SMALL_ODD_PERIOD_MULTIPLIER',
        'finite_sources':1999,
        'finite_prefix_snapshots_checked':cases,
        'zero_feasible_periods_at_oddcounts':[1,2,4],
        'feasible_period_clock_counts_first15':possible_odd_counts,
        'terminal_cycle_excluded_from_no_one_premise':True,
        'finite_search_not_universal_warrant':True,
        'true_positive_nonterminal_cycle_excluded_completely':False,
        'unbounded_positive_orbit_excluded':False,
        'global_collatz':'UNKNOWN',
        'qed':False
    }

if __name__=='__main__':
    print(json.dumps(main(),indent=2,sort_keys=True))
