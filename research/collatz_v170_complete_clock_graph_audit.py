"""V170 exact ideal all-clock/height graph versus incomplete worklist audit.

The full graph is defined WITHOUT an assumed external completeness
criterion: all positive sources n<X, all actual shortcut clocks
0<=i<=H, joined by identical actual endpoints. This is the direct
executable counterpart of the inductive Lean V170FullClockPath.

Terminal seeds close their entire graph components. In the true
Collatz map every finitely tested original source may reach a seed;
in G7 a genuine nonterminal cycle stays separate. No finite result
is promoted to a universal all-H or all-k theorem.

For b≡2(mod3) and C^t(n)=b with t<=H, true endpoint
T^i(n)=b for some i<=t. We independently replay this
conversion and demand the finite full graph directly join n,b.
"""
from __future__ import annotations
from collections import Counter
from pathlib import Path
from hashlib import sha256
import json


def T(n:int)->int:
    assert n>=0
    return n//2 if n%2==0 else (3*n+1)//2

def G7(n:int)->int:
    assert n>=0
    return n//2 if n%2==0 else (3*n+7)//2

def C(n:int,intercept:int)->int:
    assert n>=0
    return n//2 if n%2==0 else 3*n+intercept


class UF:
    def __init__(self,N:int):
        self.parent=list(range(N+1))
        self.size=[1]*(N+1)
        self.seed=bytearray(N+1)
    def root(self,x:int)->int:
        p=self.parent
        z=x
        while p[z]!=z:z=p[z]
        while p[x]!=x:
            y=p[x];p[x]=z;x=y
        return z
    def join(self,x:int,y:int)->bool:
        x=self.root(x);y=self.root(y)
        if x==y:return False
        if self.size[x]<self.size[y]:x,y=y,x
        self.parent[y]=x
        self.size[x]+=self.size[y]
        self.seed[x] |= self.seed[y]
        return True
    def mark(self,x:int):
        self.seed[self.root(x)]=1
    def snapshot(self,X:int):
        components=Counter()
        for n in range(1,X):
            components[self.root(n)]+=1
        unknown=[(r,count) for r,count in components.items()
                 if not self.seed[r]]
        return {
          "unseeded_sources":sum(cnt for _,cnt in unknown),
          "unseeded_components":len(unknown),
          "largest_unseeded_component":max([cnt for _,cnt in unknown],default=0),
          "all_positive_sources_covered_once":sum(components.values())==X-1,
          "seeded_components":sum(1 for r in components if self.seed[r])
        }


def test_full(k:int,system:str):
    X=1<<k;N=X-1;H=8*k
    S=T if system=="T" else G7
    c=1 if system=="T" else 7
    terminals=(1,2) if system=="T" else (7,14)
    uf=UF(N)
    endpoint_owner={}
    meet_edges=0
    collision_events=0
    total_clocks=0
    direct_terminal_source_hits=0
    ledger_example=[]
    for n in range(1,X):
        x=n
        for i in range(H+1):
            total_clocks+=1
            if x in terminals:
                uf.mark(n)
                direct_terminal_source_hits+=1
            old=endpoint_owner.get(x)
            if old is None:
                endpoint_owner[x]=(n,i)
            else:
                p,j=old
                if n!=p:
                    collision_events+=1
                    if uf.join(n,p):
                        meet_edges+=1
                        if len(ledger_example)<8:
                            y=n
                            for _ in range(i): y=S(y)
                            z=p
                            for _ in range(j): z=S(z)
                            assert y==z==x
                            ledger_example.append([n,i,p,j,x])
            if i<H:x=S(x)
    # Terminal reachability is detected by a terminal seed
    # in the same full graph component, including root vertices.
    for root in terminals:
        assert 0<root<X
        uf.mark(root)
    stat=uf.snapshot(X)
    assert stat['all_positive_sources_covered_once']
    samples=(1,2,3,5,7,11,21,27,31,63,127,187)
    witnessed_true=0;ordinary_hits=0
    for n in range(1,min(X,4096)):
        y=n
        for t in range(H+1):
            if y%3==2 and y<X:
                ordinary_hits+=1
                assert uf.root(y)==uf.root(n),("phase-bridge",system,k,n,t,y)
                witnessed_true+=1
            if t<H:y=C(y,c)
    # Synthetic negative source5 must not reach terminal 7/14.
    if system=="G":
        assert uf.root(5)!=uf.root(7)
        assert not uf.seed[uf.root(5)]
        assert uf.root(10)==uf.root(5)
        assert stat['largest_unseeded_component']>0

    return {
      'source_prefix_bits':k,'system':system,
      'positive_sources':N,'clock_budget':H,
      'complete_source_clock_instances':total_clocks,
      'observed_two_clock_collision_events':collision_events,
      'effective_source_component_mergers':meet_edges,
      'distinct_reached_endpoints':len(endpoint_owner),
      'direct_terminal_source_clock_hits':direct_terminal_source_hits,
      'ordinary_residue2_hits_checked':ordinary_hits,
      'all_ordinary_unit_hits_in_the_same_full_graph_component':True,
      'checked_replayed_meeting_witnesses':ledger_example,
      'finite':stat
    }


def main():
    rows=[]
    for k in (8,10,12,14):
        rows.append(test_full(k,"T"))
    controls=[]
    for k in (8,10,12,14):
        controls.append(test_full(k,"G"))
    assert all(x['finite']['unseeded_sources']==0 for x in rows)
    assert all(x['finite']['unseeded_components']==0 for x in rows)
    assert controls[-1]['finite']['largest_unseeded_component']>1<<10
    assert controls[-1]['finite']['unseeded_sources']>1<<10
    all_clocks=sum(x['complete_source_clock_instances'] for x in rows+controls)
    return {
      'schema':'COLLATZ_V170_CANONICAL_FULL_CLOCK_GRAPH_EXACT',
      'all_source_clock_pairs_checked':all_clocks,
      'same_shortcut_odd_and_even_arithmetic_tested':True,
      'all_full_graph_edges_are_actual_two_clock_meetings':True,
      'full_graph_completeness_is_by_construction':True,
      'true_shortcut_rows':rows,
      'synthetic_G7_rows':controls,
      'synthetic_negative_retains_unseeded_cycle':True,
      'one_missing_universal_arithmetic_no_giant_theorem':True,
      'external_timed_density_locally_imported':False,
      'global_all_scale_bound_proved':False,
      'global_collatz':'UNKNOWN','qed':False
    }


if __name__=="__main__":
    d=main()
    Path("evidence").mkdir(exist_ok=True)
    Path("evidence/v170-full-graph.json").write_text(
      json.dumps(d,sort_keys=True,indent=2)+"\n")
    print(json.dumps({
      'schema':d['schema'],
      'tested_true_max_positive_source':d['true_shortcut_rows'][-1]['positive_sources'],
      'true_largest_unseeded':d['true_shortcut_rows'][-1]['finite']['largest_unseeded_component'],
      'g7_largest_unseeded':d['synthetic_G7_rows'][-1]['finite']['largest_unseeded_component'],
      'global_collatz':d['global_collatz']
    },sort_keys=True))
