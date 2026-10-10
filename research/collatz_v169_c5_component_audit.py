"""Independent bounded negative control: 3n+5 has multiple coprime sectors' BASINS.

Both seed cycle 1->4->2->1 and surviving 187 cycle contain sources
coprime to 5. No universal Collatz inference from modular mixing.
"""
from __future__ import annotations
from collections import Counter
from pathlib import Path
import json
import hashlib
import subprocess

CPP=Path("research/collatz_v169_c5_component_control.cpp")
BIN=Path("/tmp/collatz-v169-c5-negative")


def T(n: int) -> int:
    return n//2 if n%2==0 else (3*n+5)//2


def full_graph(k: int,H: int):
    """Independent all-source-clock graph, no early stopping."""
    N=(1<<k)-1
    p=list(range(N+1))
    size=[1]*(N+1)
    terminal=[False]*(N+1)
    def root(n):
        while p[n]!=n:
            p[n]=p[p[n]]
            n=p[n]
        return n
    def join(a,b):
        a=root(a);b=root(b)
        if a==b:return
        if size[a]<size[b]:a,b=b,a
        p[b]=a;size[a]+=size[b];terminal[a]|=terminal[b]
    join(1,4);join(1,2);terminal[root(1)]=True
    owners={}
    for n in range(1,N+1):
        x=n
        for j in range(H+1):
            if x in (1,2,4):
                join(n,x);terminal[root(n)]=True
            else:
                if x in owners:
                    join(n,owners[x])
                else:
                    owners[x]=n
            if j<H:x=T(x)
    cnt=Counter(root(n) for n in range(1,N+1) if not terminal[root(n)])
    return len(cnt),sum(cnt.values()),max(cnt.values(),default=0)


def run(k:int):
    H=8*k
    d=json.loads(subprocess.check_output([str(BIN),str(k),str(H)],text=True))
    assert d['schema']=='COLLATZ_V169_G5_NON_GCD_COMPONENT_CONTROL'
    assert d['H']==H and d['k']==k
    if k<=12:
        p=full_graph(k,H)
        assert (d['unseeded_components'],d['unseeded_sources'],
            d['max_unseeded_component'])==p,(k,d,p)
    assert d['global_collatz']=='UNKNOWN' and d['qed'] is False
    return d


def main():
    subprocess.run(['g++','-std=c++17','-O3',str(CPP),'-o',str(BIN)],check=True)
    assert [T(1),T(4),T(2)] == [4,2,1]
    x=187
    seen=[]
    for i in range(27):
        assert x not in seen
        seen.append(x)
        x=T(x)
    assert x==187 and min(seen)==187
    assert all(y not in (1,2,4) for y in seen)
    assert 187%5!=0 and 1%5!=0 and 6%5!=0
    results=[run(k) for k in (8,10,12,14,16,18,20)]
    byk={r['k']:r for r in results}
    assert byk[20]['unseeded_sources']==900605
    assert byk[20]['unseeded_components']==6
    assert byk[20]['max_unseeded_component']==520517
    assert [6,520517] in byk[20]['top_source_components']
    assert [187,33851] in byk[20]['top_source_components']
    print(json.dumps({
       'schema':'COLLATZ_V169_G5_POSITIVE_BASIN_ADVERSARIAL',
       'compiler_sha256':hashlib.sha256(CPP.read_bytes()).hexdigest(),
       'independently_full_graph_replayed_k':[8,10,12],
       'nonterminal_cycle_187_length':27,
       'nonterminal_cycle_187_minimum':187,
       'seed_cycle':[1,4,2],
       'seed_1_and_bad_187_both_coprime_to_5':True,
       'rows':results,
       'no_universal_convergence_inferred':True,
       'global_collatz':'UNKNOWN','qed':False
    },indent=2,sort_keys=True))


if __name__=='__main__':
    main()
