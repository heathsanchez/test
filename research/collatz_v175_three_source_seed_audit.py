"""V175 independent exact source/clock audit for one seed closing three old vertices.

This is true Collatz n/2 versus (3n+1)/2 arithmetic.
A HEIGHT-only expansion admits source 23311879 in 2^24<=p<2^25.
The same H=200 finite canonical future graph then connects:
  T^2(14297769)=10723327
  T(10723327)=16084991
  T^198(16084991)=T^2(23311879)=52451729
  T^68(23311879)=2.
Thus a SINGLE new terminal seed closes THREE old-original sources
with all graph edge and seed clocks <=200.

Direct terminal clocks of the OLD three are 267,265,264 >200.
The phenomenon is genuinely source-height-only, not increasing
any old original source's search-clock budget.

The +7 and one-arrow-at5 synthetic controls protect against
assuming this certificate under a different transition function.
GLOBAL COLLATZ UNKNOWN; this is bounded exact evidence only.
"""

from __future__ import annotations
import json

N1=10723327
N2=16084991
N3=14297769
P=23311879
H=200


def T(n):
    assert n>0
    return n//2 if n%2==0 else (3*n+1)//2


def G7(n):
    assert n>0
    return n//2 if n%2==0 else (3*n+7)//2


def S5(n):
    assert n>0
    return 5 if n==5 else T(n)


def advance(n,k,f=T):
    for _ in range(k):
        n=f(n)
        assert n>0
    return n


def first_terminal(n,f=T,roots=(1,2),maxH=1000):
    for t in range(maxH+1):
        if n in roots:
            return t
        n=f(n)
    return None


def main():
    assert all(0<n<(1<<24) for n in (N1,N2,N3))
    assert (1<<24)<=P<(1<<25)
    assert T(N1)==N2
    assert advance(N3,2)==N1
    meet=advance(N2,198)
    assert meet==advance(P,2)==52451729
    assert advance(P,68)==2
    clocks={N1:265,N2:264,N3:267}
    for n,c in clocks.items():
        assert advance(n,c)==2
        assert first_terminal(n)==c
        assert c>H
    assert first_terminal(P)==68
    assert all(c<=H for c in (1,2,198,2,68))
    assert P>max(N1,N2,N3)

    # Compositional clock arithmetic: the new seed is certified at68,
    # meeting of N2 at198 with P at2 => N2 terminal at 198+(68-2).
    assert 198+(68-2)==264
    assert 1+264==265
    assert 2+265==267

    # The T-specific source/clock evidence is not a generic
    # parity-only or affine-slope-only certificate.
    assert advance(P,68,S5)!=2
    assert advance(P,2,G7)!=meet
    return {
        'schema':'COLLATZ_V175_SINGLE_NEW_SEED_CLOSES_THREE_OLD_SOURCES',
        'true_collatz_map':'T(even)=n/2; T(odd)=(3*n+1)/2',
        'old_positive_sources':[N1,N2,N3],
        'old_cutoff_exclusive':2**24,
        'new_cutoff_exclusive':2**25,
        'fixed_graph_clock_H':H,
        'single_new_larger_seed_source':P,
        'single_new_seed_first_true_terminal_clock':68,
        'exact_meeting_endpoint':meet,
        'graph_exact_edges':[
            {'source':N3,'clock':2,'other':N1,'other_clock':0,
             'endpoint':N1},
            {'source':N1,'clock':1,'other':N2,'other_clock':0,
             'endpoint':N2},
            {'source':N2,'clock':198,'other':P,'other_clock':2,
             'endpoint':meet}
        ],
        'all_graph_receipt_clocks_at_most_H':True,
        'derived_true_terminal_clocks_by_source':{
            str(n):c for n,c in clocks.items()
        },
        'all_old_sources_direct_terminal_later_than_H':True,
        'single_new_seed_closes_three_sources_by_genuine_paths':True,
        'new_seed_is_STRICTLY_LARGER_not_source_smaller':True,
        'synthetic_one_arrow_at_5_breaks_seed_terminal_proof':True,
        'synthetic_3n_plus7_breaks_true_meeting_endpoint':True,
        'all_k_uniform_elimination_proved':False,
        'global_collatz':'UNKNOWN','qed':False
    }


if __name__=='__main__':
    print(json.dumps(main(),indent=2,sort_keys=True))
