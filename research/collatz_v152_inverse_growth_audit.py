"""V152: exact reverse-word geometry and fixed-horizon density separator.

This test is NOT a Collatz proof. It independently enumerates all actual
predecessor choices, compares dynamic word counts against explicit paths,
and tests the Fibonacci ceiling. It keeps a toy countermodel showing that
almost-everywhere immediate descent is not terminal convergence.
"""
from __future__ import annotations
import functools
import json

def shortcut(n: int)->int:
    assert n>=0
    return n//2 if n%2==0 else (3*n+1)//2

def preimages(y: int)->tuple[int,...]:
    assert y>=0
    out=[2*y]
    if y%3==2:
        x=(2*y-1)//3
        assert x%2==1 and shortcut(x)==y
        out.append(x)
    return tuple(out)

@functools.lru_cache(maxsize=None)
def words(t:int,y:int)->int:
    assert t>=0 and y>=0
    if t==0:
        return 1
    return sum(words(t-1,p) for p in preimages(y))

def inverse_list(t:int,y:int)->list[int]:
    if t==0:
        return [y]
    out=[]
    for p in preimages(y):
        out.extend(inverse_list(t-1,p))
    return out

def fib_bounds(t:int)->tuple[int,int]:
    a=b=1
    for _ in range(t):
        a,b=b,a+b
    return a,b

def toy_descent_is_not_terminal():
    # Countermodel intentionally NOT the Collatz map:
    # toy T(1)=1, T(2)=2, T(n)=n-1 for n>=3.
    # Every n>=3 immediately drops below itself, yet ALL n>=2
    # are permanently trapped in the basin of the bad fixed point 2.
    def toy(n):
        return 1 if n==1 else (2 if n==2 else n-1)
    for n in range(3,1001):
        assert toy(n)<n
        x=n
        for _ in range(n):
            if x<=2: break
            x=toy(x)
        assert x==2
    assert sum(1 for n in range(1,1001) if n!=1)==999
    return dict(synthetic_not_collatz=True,
                all_tested_n_ge_3_immediately_descend=True,
                all_tested_n_ge_2_are_bad=True,
                bad_fixed_point=2,
                counterexample_to_descent_to_terminal_promotion=True)

def main():
    for y in range(0,151):
        for p in preimages(y):
            assert shortcut(p)==y
        for p in range(0,1201):
            assert (shortcut(p)==y)==(p in preimages(y))
        if y%3==0:
            assert len(preimages(y))==1

    for t in range(0,13):
        for y in range(1,22):
            found=inverse_list(t,y)
            assert len(found)==words(t,y)
            assert all(__iter_shortcut(t,n)==y for n in found)
            a,b=fib_bounds(t)
            assert len(found)<=(b if y%3==2 else a)

    audit=[]
    for t in range(0,31):
        a,b=fib_bounds(t)
        row={"depth":t,"nonbranching_class_ceiling":a,
             "class_two_fibonacci_ceiling":b,
             "root_one_paths":words(t,1),
             "root_two_paths":words(t,2)}
        assert row["root_one_paths"]<=a
        assert row["root_two_paths"]<=b
        audit.append(row)

    front={1,2}; all_seen=set(front)
    for t in range(0,31):
        if t==0: continue
        new=set()
        for y in front:
            new.update(preimages(y))
        front=new-all_seen
        all_seen.update(front)
        terminal_paths_by_t=sum(words(j,y) for j in range(t+1) for y in (1,2))
        assert len(all_seen)<=terminal_paths_by_t
    counts={str(k):sum(1 for n in all_seen if 1<=n<(1<<k))
            for k in (8,12,16,20,24,30)}
    assert counts['30']<2**30
    # The known terminal basin is finite under fixed budget 30.
    # Hence its population has zero dyadic density as k tends to infinity.
    result={
      "schema":"COLLATZ_V152_EXACT_INVERSE_FIBONACCI_SEPARATION",
      "reverse_ancestor_arithmetic_checks":151*1201,
      "independent_list_checks":13*21,
      "fibonacci_depth_max":30,
      "fibonacci_ceiling_asserted_all_sampled_sources":True,
      "terminal_paths_depth_30":sum(words(j,y) for j in range(31) for y in (1,2)),
      "distinct_terminal_sources_depth_at_most_30":len(all_seen),
      "finite_terminal_source_count_by_dyadic_cutoff":counts,
      "fixed_horizon_not_sufficient_for_sparse_exceptional_mass":True,
      "toy_diagnostic":toy_descent_is_not_terminal(),
      "not_an_all_depth_density_bound":True,
      "external_predecessor_theorem_imported":False,
      "full_collatz":"UNKNOWN","qed":False,
      "selected_path_counts": [audit[j] for j in (0,5,10,15,20,25,30)]
    }
    return result

def __iter_shortcut(t:int,n:int)->int:
    for _ in range(t):
        n=shortcut(n)
    return n

if __name__=='__main__':
    print(json.dumps(main(),indent=2,sort_keys=True))
