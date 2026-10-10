"""V172 independent witness-exact dominance compression qualification.

The C++ earliest-owner algorithm uses at most one dominant arrival
clock per genuine actual endpoint and can discard a later source
suffix. Lean separately proves the exact same-endpoint future-clock
dominance rule, including safe transfer of terminal certificates.

At k<=14 for T, synthetic G7 and synthetic one-arrow S5, this audit:
  1. constructs the FULL finite graph by enumerating ALL original
     source clocks H=8k, without dominance pruning;
  2. independently replays every C++ emitted genuine source/clock
     meeting and terminal receipt;
  3. reconstructs the C++ union-find from receipts alone;
  4. compares its per-source SEEDED status and exact minimum-source
     UNSEEDED component representative to the exhaustive full graph.
This is an independently implemented finite check of the algorithm.

Large k=20..25 is bounded executable evidence and is NOT
individually reified as a Lean theorem. No all-scale no-giant
estimate, Collatz QED, or independently imported external
positive-density result is claimed.
"""
from __future__ import annotations

import csv
import hashlib
import json
from collections import Counter
from pathlib import Path
import subprocess


def T(n:int)->int:
    assert n>=0
    return n//2 if n%2==0 else (3*n+1)//2

def G(n:int)->int:
    assert n>=0
    return n//2 if n%2==0 else (3*n+7)//2

def S(n:int)->int:
    assert n>=0
    return 5 if n==5 else T(n)

steps={'T':T,'G':G,'S':S}
roots={'T':(1,2),'G':(7,14),'S':(1,2)}


class UF:
    def __init__(self,N:int):
        self.parent=list(range(N+1))
        self.size=[1]*(N+1)
        self.minimum=list(range(N+1))
        self.good=bytearray(N+1)
    def root(self,n):
        p=self.parent
        x=n
        while p[x]!=x:x=p[x]
        while p[n]!=n:
            j=p[n]
            p[n]=x
            n=j
        return x
    def join(self,a,b):
        a=self.root(a);b=self.root(b)
        if a==b:return
        if self.size[a]<self.size[b]:a,b=b,a
        self.parent[b]=a
        self.size[a]+=self.size[b]
        self.minimum[a]=min(self.minimum[a],self.minimum[b])
        self.good[a] |= self.good[b]
    def mark(self,n):
        self.good[self.root(n)]=1
    def status(self,n):
        r=self.root(n)
        return (int(self.good[r]),0 if self.good[r] else self.minimum[r])
    def summary(self,N):
        cnt=Counter(self.root(n) for n in range(1,N+1))
        unseeded=[(self.minimum[r],num) for r,num in cnt.items()
                  if not self.good[r]]
        return dict(
          unseeded_sources=sum(num for _,num in unseeded),
          unseeded_components=len(unseeded),
          largest_unseeded_component=max([num for _,num in unseeded],default=0),
          top_components=sorted(unseeded,key=lambda p:(-p[1],p[0]))[:10]
        )


def replay_receipt(receipt:Path,k:int,system:str):
    H=8*k
    N=(1<<k)-1
    uf=UF(N)
    counts=Counter()
    f=steps[system]
    for ln in receipt.read_text().splitlines():
        r=json.loads(ln)
        counts[r['type']]+=1
        n,i=r['source'],r['clock']
        assert 0<n<=N and 0<=i<=H
        x=n
        for _ in range(i):x=f(x)
        assert x==r['endpoint']
        if r['type']=='terminal':
            assert x in roots[system]
            uf.mark(n)
        elif r['type']=='meet':
            p,j=r['other'],r['other_clock']
            assert 0<p<=N and 0<=j<=H and n!=p
            y=p
            for _ in range(j):y=f(y)
            assert y==x
            uf.join(n,p)
        else:
            raise AssertionError(('untrusted receipt type',r))
    return uf,dict(counts)


def exhaustive_graph(k,system):
    X=1<<k
    H=8*k
    N=X-1
    f=steps[system]
    uf=UF(N)
    owner={}
    for n in range(1,X):
        y=n
        for i in range(H+1):
            if y in roots[system]:uf.mark(n)
            if y in owner:
                p,j=owner[y]
                assert 0<p<X and 0<=j<=H
                uf.join(n,p)
            else:
                owner[y]=(n,i)
            if i<H:y=f(y)
    return uf,len(owner)


def compile_runner():
    src=Path("research/collatz_v172_dominant_clock_graph.cpp")
    assert src.is_file()
    path=Path("evidence/v172_runner")
    path.parent.mkdir(exist_ok=True)
    subprocess.run(["g++","-O3","-std=c++17",str(src),"-o",str(path)],
                   check=True)
    return path,hashlib.sha256(src.read_bytes()).hexdigest()


def run(k,system,exe,full=False):
    stem=f"v172_{system}_k{k}"
    receipt=Path("evidence")/f"{stem}_receipts.jsonl"
    labels=Path("evidence")/f"{stem}_labels.csv"
    args=[str(exe),str(k),system]
    if full:
        args.extend([str(labels),str(receipt)])
    result=subprocess.run(args,check=True,capture_output=True,text=True)
    data=json.loads(result.stdout)
    assert data['schema']=='COLLATZ_V172_DOMINANT_CLOCK_QUOTIENT'
    assert data['finite_only']
    assert data['H']==8*k
    assert data['positive_sources']==(1<<k)-1
    assert data['actual_endpoint_examinations']<=data['naive_full_source_clock_slots']
    assert data['global_collatz']=='UNKNOWN' and data['qed'] is False
    if not full:
        return data,None

    receiptsUF, receiptCounts=replay_receipt(receipt,k,system)
    exhaustiveUF, distinct=exhaustive_graph(k,system)
    assert distinct>=data['distinct_endpoints']
    N=(1<<k)-1
    with labels.open(newline='') as f:
        reader=csv.DictReader(f)
        encountered=0
        for row in reader:
            n=int(row['n'])
            encountered+=1
            assert n==encountered
            label=(int(row['seeded']),int(row['unseeded_min_source']))
            independent=receiptsUF.status(n)
            exhaustive=exhaustiveUF.status(n)
            assert label==independent==exhaustive,(
                'label mismatch',k,system,n,label,independent,exhaustive)
        assert encountered==N
    v=exhaustiveUF.summary(N)
    assert data['unseeded_sources']==v['unseeded_sources']
    assert data['unseeded_components']==v['unseeded_components']
    assert data['largest_unseeded_component']==v['largest_unseeded_component']
    assert data['top_unseeded_min_source_and_size'] == [
        list(p) for p in v['top_components']
    ]
    assert data['effective_real_two_clock_joins']==receiptCounts['meet']
    assert data['direct_terminal_source_receipts']==receiptCounts['terminal']

    return data,{
      'system':system,'k':k,'positive_sources_checked':N,
      'genuine_receipt_count':sum(receiptCounts.values()),
      'independent_labels_compared':N,
      'all_actual_two_clock_receipts_replayed':True,
      'receipt_DSUs_equivalent_to_exhaustive':True,
      'no_false_terminal_propagation':True,
      'unseeded_summary':v,
    }


def main():
    runner,digest=compile_runner()
    independently_qualified=[]
    small_rows=[]
    for k in (8,10,12,14):
        for system in ('T','G','S'):
            row,cert=run(k,system,runner,full=True)
            independently_qualified.append(cert)
            small_rows.append(row)

    large_true=[]
    for k in (16,18,20,22,24,25):
        row,_=run(k,'T',runner)
        large_true.append(row)
    large_controls=[]
    for system in ('G','S'):
        row,_=run(20,system,runner)
        large_controls.append(row)

    expected={16:(0,0,0),18:(0,0,0),
              20:(2,2,1),22:(5,3,2),24:(40,10,13),25:(40,10,10)}
    assert {
      x['k']:(x['unseeded_sources'],
              x['unseeded_components'],
              x['largest_unseeded_component'])
      for x in large_true
    }==expected
    assert all(x['system']=='TRUE_COLLATZ' for x in large_true)
    assert all(x['unseeded_sources']>100000 for x in large_controls)
    assert large_controls[-1]['system']=='SYNTHETIC_ONE_ARROW'
    assert large_controls[-1]['largest_unseeded_component']==983307
    assert len(independently_qualified)==12
    assert sum(x['independent_labels_compared'] for x in independently_qualified)==(
        3*sum((1<<k)-1 for k in (8,10,12,14))
    )
    k24=next(r for r in large_true if r['k']==24)
    assert k24['actual_endpoint_examinations']==68881607
    assert k24['largest_unseeded_component']==13

    out={
      'schema':'COLLATZ_V172_DOMINANT_CLOCK_END_TO_END_AUDIT',
      'source_cpp_sha256':digest,
      'all_12_exhaustive_source_clock_graphs_matched':True,
      'actual_all_source_meeting_clocks_replayed_on_small_cutoffs':True,
      'all_finite_ledger_termination_sound':True,
      'max_bounded_real_source_checked':(1<<25)-1,
      'k24_endpoints_examined':k24['actual_endpoint_examinations'],
      'k24_naive_positions':k24['naive_full_source_clock_slots'],
      'k24_clock_examinations_reduction_factor':(
          k24['naive_full_source_clock_slots']/
          k24['actual_endpoint_examinations']),
      'large_true_rows':large_true,
      'synthetic_big_controls':large_controls,
      'small_rows':small_rows,
      'independent_source_receipt_replays':independently_qualified,
      'single_bounded_horizon_only':True,
      'all_k_no_giant_theorem_proved':False,
      'external_timed_density_locally_imported':False,
      'universal_collatz':'UNKNOWN','qed':False,
    }
    Path("evidence/v172-summary.json").write_text(
      json.dumps(out,sort_keys=True,indent=2)+'\n')
    print(json.dumps({
      'schema':out['schema'],
      'largest_checked_source':out['max_bounded_real_source_checked'],
      'k24_meeting_examinations':out['k24_endpoints_examined'],
      'k25_unseeded':large_true[-1]['unseeded_sources'],
      'all_small_exhaustive_graphs_matched':
        out['all_12_exhaustive_source_clock_graphs_matched'],
      'global_collatz':out['universal_collatz']
    },sort_keys=True))


if __name__=="__main__":
    main()
