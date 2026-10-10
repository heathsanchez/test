"""V156 exact source-3 terminal-exit separator.

This is not a proof of the Collatz conjecture. It independently
replays the real shortcut trajectory and shows why the older V82/V85
*universal later-LIVE rank* premise is false on a genuine terminal
trajectory. The Lean theorem proves this for every future clock,
not merely the finite exact replay.
"""
from __future__ import annotations
import json

def shortcut(n:int)->int:
    assert n>0
    return n//2 if n%2==0 else (3*n+1)//2

def main():
    n=3
    states=[n]
    for _ in range(48):
        states.append(shortcut(states[-1]))
    assert states[:7]==[3,5,8,4,2,1,2]
    assert n//(2**3)==0
    source3_at_clock3=states[3]
    assert source3_at_clock3==4

    # Only positive sources smaller than 3 are 1 and 2.
    # Their futures stay in {1,2} by closure, confirmed by exact replay.
    earlier={1,2}
    for p in earlier:
        v=p
        for _ in range(80):
            assert v in (1,2)
            v=shortcut(v)
    assert source3_at_clock3 not in earlier

    # Every positive clock after the clock-3 state hits a terminal
    # endpoint {1,2}. Consequently there is no later LIVE state.
    v=source3_at_clock3
    all_later_terminal=True
    for j in range(1,101):
        v=shortcut(v)
        all_later_terminal &= (v in (1,2))
    assert all_later_terminal
    # Choosing j=0 returns exactly the same state and hence
    # cannot lower ANY well-founded function of the state.
    return {
      'schema':'COLLATZ_V156_REAL_LAST_LIVE_STATE_SEPARATOR',
      'source':3,'initial_clock':3,'real_endpoint':4,'original_source_tail':0,
      'earlier_positive_sources':[1,2],
      'earlier_sources_cannot_reach_endpoint4':True,
      'actual_step_to_terminal':[4,2],
      'all_later_shortcut_states_terminal':True,
      'zero_clock_rank_decrease_impossible_by_reflexivity':True,
      'old_V82_later_live_progress_premise_universally_realizable':False,
      'correct_replacement':'eventual exact EXIT or later certified LIVE lex decrease',
      'new_universal_exit_or_rank_condition_proved':False,
      'global_collatz':'UNKNOWN','qed':False
    }

if __name__=='__main__':
    print(json.dumps(main(),indent=2,sort_keys=True))
