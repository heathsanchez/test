#!/usr/bin/env python3
"""Exact forward witness DAG and frozen residue-cylinder transfer.

No finite coverage result is a global theorem. Python integers are exact.
Input CSV headers: K,b,d,c,L. Export using collatz_export_boundaries.cpp.
"""
import argparse
import csv
import hashlib
import json
from collections import Counter
from pathlib import Path
from statistics import median


def step(n):
    return (3*n+1)//2 if n&1 else n//2


def first_descent(n, cap):
    if n <= 1:
        raise ValueError('descent target must exceed one')
    path = [n]
    for _ in range(cap):
        path.append(step(path[-1]))
        if path[-1] < n:
            return path
    return None


def compile_rule(n, t):
    """Return (length,residue,A,B,minimum) for a proved affine descent rule.

    On n == residue mod 2**t, T**t(n)=(A*n+B)/2**t.
    Requires n >= minimum = floor(B/(2**t-A))+1.
    """
    if n < 1 or t < 1:
        raise ValueError('positive seed and length required')
    A,B,x=1,0,n
    for j in range(t):
        if x&1:
            A,B=3*A,3*B+(1<<j)
        x=step(x)
    M=1<<t
    if A>=M or x>=n:
        raise ValueError('not a descent witness')
    assert A*n+B == M*x
    return t,n%M,A,B,B//(M-A)+1


def applies(rule,n):
    t,r,A,B,minimum=rule
    return n>1 and n>=minimum and n%(1<<t)==r


def validate_rule(rule):
    """Independent scalar replay: do not reuse affine coefficient recurrence."""
    if len(rule)!=5 or not all(type(v) is int for v in rule): return False
    t,r,A,B,minimum=rule
    if t<1 or not 0<=r<(1<<t): return False
    x=r; odd=0
    for _ in range(t):
        odd+=x&1
        x=(3*x+1)//2 if x&1 else x//2
    expected_A=3**odd; M=1<<t
    expected_B=M*x-expected_A*r
    return (A==expected_A and B==expected_B and A<M and
            minimum==B//(M-A)+1)


def read_rows(path):
    with open(path,newline='') as f:
        reader=csv.DictReader(f)
        if reader.fieldnames!=['K','b','d','c','L']:
            raise ValueError('unexpected CSV headers: '+repr(reader.fieldnames))
        rows=[{k:int(v) for k,v in row.items()} for row in reader]
    if not rows or len({r['K'] for r in rows})!=1:
        raise ValueError('one nonempty depth required')
    if len({r['b'] for r in rows})!=len(rows):
        raise ValueError('duplicate boundary')
    return rows


def freeze_index(rules):
    index={}
    for rule in rules:
        t,r,_,_,minimum=rule
        old=index.setdefault(t,{}).get(r)
        if old is not None and old!=minimum:
            raise ValueError('inconsistent same-cylinder rule')
        index[t][r]=minimum
    return index


def matches(index,n):
    return any(n>=by_r.get(n% (1<<t), n+1) for t,by_r in index.items())


def analyze(rows, cap, frozen_rules):
    K=rows[0]['K']
    edges={}; visits=Counter(); suffix_ids={}; lengths=[]
    rules=set(); sources=set(); hardest=None; raw_edges=0; pending=[]
    # Freeze before inspecting any holdout trajectories.
    frozen=freeze_index(frozen_rules)
    covered=[r['b'] for r in rows if matches(frozen,r['b'])]
    for row in rows:
        b,d,c,L=(row[k] for k in ('b','d','c','L'))
        if L!=0 or b<=1: raise ValueError('expected positive q=0 boundary')
        x=b; odd=0
        for _ in range(K):
            odd+=x&1; x=step(x)
        if (x,odd)!=(d,c): raise ValueError('invalid exported prefix')
        path=first_descent(b,K+cap)
        if path is None:
            pending.append(b); continue
        if len(path)-1<=K: raise ValueError('baseline retained direct descent')
        tail=path[K:]; extra=len(tail)-1
        lengths.append(extra)
        if hardest is None or extra>hardest['extra_steps']:
            hardest={'b':b,'d':d,'extra_steps':extra,'path':tail}
        raw_edges+=extra
        for x,y in zip(tail,tail[1:]):
            if x in edges and edges[x]!=y: raise ValueError('nondeterminism')
            edges[x]=y; visits[x]+=1
        # Endpoint-sensitive suffix interning does not erase stopping thresholds.
        sid=0
        for x in reversed(tail):
            key=(x,sid)
            if key not in suffix_ids: suffix_ids[key]=len(suffix_ids)+1
            sid=suffix_ids[key]
        # Compile all suffixes ending at this certified lower endpoint.
        # A shorter internal suffix may be useful to an unseen starting integer.
        for j,x in enumerate(path[:-1]):
            sources.add(x)
            rules.add(compile_rule(x,len(path)-1-j))
    # Different endpoints for the same x are reusable edges but not identical
    # stopping consequences. Record both compression measures separately.
    unique_nodes=set(edges)|set(edges.values())
    result={
        'K':K,'status':'EXPERIMENTALLY EXACT ON FINITE DOMAIN',
        'families':len(rows),'closed':len(rows)-len(pending),'unresolved':pending,
        'raw_tail_edges':raw_edges,'unique_edges':len(edges),
        'unique_nodes':len(unique_nodes),'endpoint_sensitive_suffix_nodes':len(suffix_ids),
        'max_reuse':max(visits.values(),default=0),'median_reuse':median(visits.values()) if visits else 0,
        'reused_edges':sum(v>1 for v in visits.values()),
        'median_extra_steps':median(lengths) if lengths else None,
        'max_extra_steps':max(lengths,default=0),'hardest':hardest,
        'extra_steps_histogram':dict(sorted(Counter(lengths).items())),
        'frozen_rule_count':len(frozen_rules),'frozen_covered':len(covered),
        'frozen_unexplained':len(rows)-len(covered),'acquired_rules':len(rules),
        'scope':'representatives q=0; rule cylinders extend soundly but are not exhaustive',
    }
    digest=hashlib.sha256()
    for x,y in sorted(edges.items()): digest.update(f'{x},{y}\n'.encode())
    result['edge_sha256']=digest.hexdigest()
    return result,rules,sources


def main():
    p=argparse.ArgumentParser()
    p.add_argument('inputs',nargs='+')
    p.add_argument('--cap',type=int,default=4096)
    p.add_argument('--out',required=True)
    p.add_argument('--rules-out',help='Optional potentially large exact rule artifact')
    a=p.parse_args()
    all_results=[]; accumulated=set(); seen_boundaries=set(); seen_sources=set()
    for path in a.inputs:
        rows=read_rows(path)
        result,rules,sources=analyze(rows,a.cap,accumulated)
        unseen=[r['b'] for r in rows if r['b'] not in seen_boundaries]
        frozen=freeze_index(accumulated)
        result['unseen_boundaries']=len(unseen)
        result['frozen_unseen_covered']=sum(matches(frozen,b) for b in unseen)
        novel=[r['b'] for r in rows if r['b'] not in seen_sources]
        result['novel_source_boundaries']=len(novel)
        result['frozen_novel_source_covered']=sum(matches(frozen,b) for b in novel)
        result['input_sha256']=hashlib.sha256(Path(path).read_bytes()).hexdigest()
        all_results.append(result)
        print(json.dumps({k:v for k,v in result.items() if k not in ('hardest','extra_steps_histogram')},sort_keys=True),flush=True)
        accumulated.update(rules)
        seen_boundaries.update(r['b'] for r in rows)
        seen_sources.update(sources)
        Path(a.out).write_text(json.dumps({'results':all_results,'total_rules':len(accumulated)},indent=2)+'\n')
    if a.rules_out:
        Path(a.rules_out).write_text(json.dumps(sorted(accumulated))+'\n')


if __name__=='__main__': main()
