"""V163 exact backward coverage ceiling and terminal-clock negative control.

This audit enumerates all REAL shortcut reverse sources of terminal
{1,2} at exact time t. Because that 1<->2 target is closed, the
sources reaching terminal AT OR BEFORE t equal the exact-depth set.
This removes V152's avoidable overcount of every earlier clock.

Lean proves, for EVERY natural t:
  3^t * exact_depth_list_length <= 3 * 5^t.
Thus for X=2^k the direct terminal-by-k coverage share is at most
  3*(5/6)^k -> 0.
The limit is elementary but the proof of it is NOT a separately
compiled Lean theorem in V163; the scaled integer inequality IS.

These negative results do NOT rule out longer or source-dependent
terminal clocks or verified earlier-source future merges.
GLOBAL COLLATZ UNKNOWN. No QED.
"""
from functools import lru_cache
import json


def T(n:int)->int:
    assert n>=0
    return n//2 if n%2==0 else (3*n+1)//2


def predecessors(y:int):
    yield 2*y
    if y%3==2:
        p=(2*y-1)//3
        assert p>0 and T(p)==y
        yield p


@lru_cache(maxsize=None)
def words(t:int,y:int)->int:
    if not t:
        return 1
    return sum(words(t-1,p) for p in predecessors(y))


def main():
    A=B=1
    path_budget=0
    level={1,2}
    all_before=set()
    rows=[]
    full_source_replays=0
    for t in range(0,25):
        if t:
            level={p for y in level for p in predecessors(y)}
        all_before |= level
        assert all_before==level,("terminal forward invariance",t)
        # exact-depth path count includes duplicates, hence is an
        # upper bound on the number of distinct sources.
        path_words=words(t,1)+words(t,2)
        assert len(level)<=path_words<=2*B,(t,len(level),path_words,2*B)
        path_budget+=2*B
        assert 3**t*path_budget<=6*5**t
        assert 3**t*(2*B)<=3*5**t
        assert 6**(4*t)>=2**t*5**(4*t)

        cutoff=1<<t
        valid={n for n in level if 0<n<cutoff}
        for n in valid:
            x=n
            for _ in range(t):
                x=T(x)
            assert x in (1,2),(n,t,x)
            full_source_replays+=1
        if t in (0,1,2,4,6,8,10,12,16,20,24):
            rows.append({
                't':t,'dyadic_cutoff':cutoff,
                'terminal_by_t_positive_sources_below_cutoff':len(valid),
                'terminal_by_t_fraction':round(len(valid)/cutoff,10),
                'exact_reverse_distinct_sources_total':len(level),
                'exact_reverse_path_multiplicity':path_words,
                'fib_pair_A':A,'fib_pair_B':B,
                'exact_depth_path_ceiling':2*B,
                'sum_of_all_depths_ceiling':path_budget,
                'rational_bound_numerator':3*5**t,
                'rational_bound_denominator':3**t,
                'one_depth_ceiling_proved':3**t*(2*B)<=3*5**t
            })
        A,B=B,A+B

    assert rows[-1]['terminal_by_t_fraction']<rows[-2]['terminal_by_t_fraction']
    assert rows[-1]['terminal_by_t_positive_sources_below_cutoff']==3571
    assert rows[-1]['dyadic_cutoff']==1<<24
    assert words(24,1)+words(24,2)>=len(level)

    return {
      'schema':'COLLATZ_V163_REVERSE_HORIZON_MASS_CEILING',
      't_max_checked':24,
      'tested_actual_source_terminal_paths':full_source_replays,
      'exact_terminal_by_horizon_equals_terminal_at_exact_depth':True,
      'terminal_targets':[1,2],
      'all_sources_true_collatz_shortcut':True,
      'true_odd_inverse_condition':'y%3==2',
      'fibonacci_scaled_sum_bound_all_tested':True,
      'fibonacci_scaled_exact_depth_bound_all_tested':True,
      'four_step_six_over_five_exponential_separation_all_tested':True,
      'terminal_by_bitlength_coverage_upper_bound':'3*(5/6)^k',
      'direct_terminal_by_bitlength_fraction_tends_to_zero_elementary':True,
      'global_density_one_of_all_eventual_terminal_sources_proved':False,
      'all_source_time_unbounded_coverage_proved':False,
      'source_relative_merger_clock_excluded':False,
      'rows':rows,
      'global_collatz':'UNKNOWN','qed':False
    }


if __name__=='__main__':
    print(json.dumps(main(),sort_keys=True,indent=2))
