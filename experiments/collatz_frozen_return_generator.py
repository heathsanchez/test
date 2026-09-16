#!/usr/bin/env python3
"""Frozen B12 first-return operators with exact variable-repeat compilation.

Tracks fallback explicitly; the audit replays every macro independently.
Zero new rule acquisition is not zero residual trajectory computation.
"""
import argparse
import hashlib
import json
from collections import defaultdict,Counter
from pathlib import Path
from collatz_return_interface import trace,certificate,admissible,jump_repetitions,episode,valuation
from collatz_witness_compiler import read_rows,compile_rule,freeze_index,matches


def train(rows):
    words=set();sources=set();baseline_rules=set()
    for row in rows:
        states,branches=trace(row['b']);last={states[0][0]:0}
        # Exclude every training shortcut state, including internal odd steps,
        # not merely episode boundaries or roots.
        x=row['b'];sources.add(x);scalar_path=[x]
        for _ in range(sum(r+s for r,s,_ in branches)):
            x=(3*x+1)//2 if x&1 else x//2
            sources.add(x);scalar_path.append(x)
        stack=[]
        for j in range(len(scalar_path)-1,-1,-1):
            while stack and scalar_path[stack[-1]]>=scalar_path[j]: stack.pop()
            if stack:
                baseline_rules.add(compile_rule(scalar_path[j],stack[-1]-j))
            stack.append(j)
        for j in range(1,len(states)):
            r=states[j][0]
            if r in last:
                word=tuple(branches[last[r]:j])
                assert not any(z[0]==r for z in word[1:])
                words.add(word)
            last[r]=j
    wire=json.dumps(sorted(words),separators=(',',':'))
    restored={tuple(tuple(z) for z in w) for w in json.loads(wire)}
    assert restored==words
    index=defaultdict(list)
    for word in sorted(restored): index[word[0][0]].append(certificate(word))
    return index,sources,hashlib.sha256(wire.encode()).hexdigest(),len(words),baseline_rules


def close(n,index):
    x=n;counts=Counter();used=set()
    for _ in range(4096):
        if x<n: return counts,used
        r=valuation(x+1);m=(x+1)>>r
        candidates=[c for c in index.get(r,()) if admissible(c,m)]
        assert len(candidates)<=1 # Exact first-return cylinders are disjoint.
        if not candidates:
            *_,x=episode(x)
            counts['fallback_episodes']+=1
            continue
        c=candidates[0];jump=jump_repetitions(c,m)
        assert jump['repeats']>=1
        used.add(c['word'])
        counts['macro_invocations']+=1
        counts['compiled_episode_transitions']+=len(c['word'])*jump['repeats']
        counts['prefix_formula_evaluations']+=jump['prefix_evaluations']
        counts['extra_repetitions_compiled']+=jump['repeats']-1
        # Independent verifier. Its work is not counted as zero-search reuse.
        checked=x;smallest=x
        for _ in range(jump['repeats']*sum(a+b for a,b,_ in c['word'])):
            checked=(3*checked+1)//2 if checked&1 else checked//2
            smallest=min(smallest,checked)
        assert checked==(1<<r)*jump['out']-1
        assert smallest==jump['minimum_n']
        counts['independent_macro_replays']+=1
        if jump['minimum_n']<n: return counts,used
        x=(1<<r)*jump['out']-1
    raise ValueError('UNKNOWN: execution budget exhausted')


def main():
    p=argparse.ArgumentParser();p.add_argument('training');p.add_argument('futures',nargs='+')
    p.add_argument('--lineage-holdout',action='store_true',
                   help='Train on B12 roots not divisible by 3; hold out all descendants of other roots')
    p.add_argument('--out',required=True);a=p.parse_args()
    training=read_rows(a.training)
    K=training[0]['K'];all_roots={r['b'] for r in training}
    held={r['b'] for r in training if r['b']%3==0} if a.lineage_holdout else set()
    if a.lineage_holdout:
        training=[r for r in training if r['b'] not in held]
        assert not ({r['b'] for r in training}&held)
    index,sources,digest,size,baseline_rules=train(training)
    baseline=freeze_index(baseline_rules)
    results=[]
    for file in a.futures:
        rows=read_rows(file)
        assert all(r['b']%(1<<K) in all_roots for r in rows)
        if a.lineage_holdout: rows=[r for r in rows if r['b']%(1<<K) in held]
        totals=Counter();used=set();examples=[]
        for row in rows:
            counts,local=close(row['b'],index)
            totals.update(counts);used.update(local);totals['closed']+=1
            novel=row['b'] not in sources
            if novel:
                totals['novel_sources']+=1
                if matches(baseline,row['b']):totals['novel_baseline_direct_closure']+=1
                if counts['macro_invocations']: totals['novel_sources_using_frozen_rule']+=1
                if counts['extra_repetitions_compiled']: totals['novel_sources_using_repeat_generator']+=1
            if counts['fallback_episodes']==0:
                totals['closed_without_fallback']+=1
                if novel:
                    totals['novel_closed_without_fallback']+=1
                    if counts['macro_invocations']>1: totals['novel_zero_fallback_multiple_macros']+=1
                    if len(examples)<10: examples.append(row['b'])
        for key in ('novel_baseline_direct_closure','novel_closed_without_fallback',
                    'novel_zero_fallback_multiple_macros'):
            totals.setdefault(key,0)
        result={'K':rows[0]['K'],'families':len(rows),'counts':dict(totals),
                'frozen_operators_used':len(used),'new_operators_acquired':0,
                'novel_zero_fallback_examples':examples}
        results.append(result);print(json.dumps(result,sort_keys=True),flush=True)
        Path(a.out).write_text(json.dumps({'status':'EXPERIMENTALLY EXACT ON FINITE DOMAIN',
            'training_K':training[0]['K'],'frozen_operator_count':size,
            'training_roots':len(training),'held_out_root_count':len(held),
            'held_out_roots':sorted(held),
            'same_training_baseline_rules':len(baseline_rules),'operator_serialization_sha256':digest,
            'results':results,'scope':'macro reuse with explicit residual fallback; no global closure'},indent=2)+'\n')


if __name__=='__main__':main()
