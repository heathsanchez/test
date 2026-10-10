"""V172: independent exact-arithmetic replay of a SOURCE HEIGHT unlock.

Source 4053039 is <2^22; at H=176 its direct terminal clock is 335.
The new source IDs 5640039 and 5575759 are in [2^22,2^24),
and two genuine independent two-clock edges plus one 131-clock
terminal seed certify the original source WITHOUT any infinite
convergence assumption. This audit is exact bounded arithmetic only.
"""
import hashlib
import json
from pathlib import Path


def T(n: int) -> int:
    assert n > 0
    return n // 2 if n % 2 == 0 else (3*n+1)//2


def run(n:int,t:int)->int:
    for _ in range(t):
        n=T(n)
    return n


def direct_first_hit(n:int)->tuple[int,int]:
    source=n
    for t in range(1000):
        if n in (1,2):
            return t,n
        n=T(n)
    raise AssertionError(f"source {source} exceeded 1000-clock audit cap")


def main()->None:
    origin=4053039
    p=5640039
    q=5575759
    X0=2**22
    X1=2**24
    H=176
    assert 0<origin<X0<=p<X1 and X0<=q<X1
    y=run(origin,141)
    assert y == run(p,2) == 12690089
    z=run(p,65)
    assert z == run(q,0) == 5575759
    assert run(q,131)==2
    assert direct_first_hit(origin)==(335,2)
    assert direct_first_hit(p)==(196,2)
    assert direct_first_hit(q)==(131,2)
    assert 141<=H and 2<=H and 65<=H and 0<=H and 131<=H
    assert 141+(196-2)==335
    assert 65+131==196
    assert run(origin,335)==run(p,196)==run(q,131)==2
    def OneArrow(n: int)->int:
        return 5 if n==5 else T(n)
    def ROne(n:int,t:int)->int:
        for _ in range(t):
            n=OneArrow(n)
        return n
    assert OneArrow(5)==5 and T(5)==8
    assert ROne(origin,141)==ROne(p,2)==y
    assert ROne(p,65)==ROne(q,0)==z
    assert ROne(q,128)==ROne(q,131)==5
    assert ROne(q,131) not in (1,2)

    # Each equality is replayed from the ORIGINAL integer source and clock.
    # No relative/rational orbit or unverified source-state is admitted.
    out={
        'schema':'COLLATZ_V172_EXACT_SOURCE_HEIGHT_UNLOCK',
        'source_original':origin,
        'cutoff_old':X0,
        'cutoff_new':X1,
        'max_each_witness_clock':H,
        'bridge_one':{'source':origin,'clock':141,'other':p,'other_clock':2,'endpoint':y},
        'bridge_two':{'source':p,'clock':65,'other':q,'other_clock':0,'endpoint':z},
        'terminal_seed':{'source':q,'terminal_clock':131,'terminal_endpoint':2},
        'derived_original_terminal_clock':335,
        'direct_original_terminal_clock':335,
        'terminal_consequence_replayed_from_all_three_original_sources':True,
        'source_height_unlock_requires_new_sources_for_THIS_LEDGER':True,
        'one_arrow_countercontrol_joins_survive_but_terminal_fails':True,
        'global_source_height_elimination_proved':False,
        'all_scale_contraction_proved':False,
        'global_collatz':'UNKNOWN','qed':False,
    }
    print(json.dumps(out,sort_keys=True,indent=2))


if __name__=='__main__':
    main()
