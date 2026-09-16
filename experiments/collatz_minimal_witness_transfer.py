#!/usr/bin/env python3
"""Compare endpoint suffix memorization with minimal first-descent cylinders.

The final input is holdout-only: no rule is acquired from its trajectories.
All transferred matches use frozen rules before any next-stage training.
"""
import argparse
import json
from pathlib import Path
from collatz_witness_compiler import (read_rows, first_descent, compile_rule,
    freeze_index, matches, validate_rule)


def main():
    p=argparse.ArgumentParser()
    p.add_argument('inputs',nargs='+')
    p.add_argument('--out',required=True)
    a=p.parse_args()
    rules=set(); seen=set(); results=[]
    for i,path in enumerate(a.inputs):
        rows=read_rows(path)
        # Serialization boundary. Applicability sees only integer inputs.
        restarted={tuple(r) for r in json.loads(json.dumps(sorted(rules)))}
        assert restarted==rules
        index=freeze_index(restarted)
        novel=[r['b'] for r in rows if r['b'] not in seen]
        covered=[n for n in novel if matches(index,n)]
        result={'K':rows[0]['K'],'families':len(rows),'frozen_rules':len(rules),
                'novel_sources':len(novel),'novel_covered':len(covered),
                'all_covered':sum(matches(index,r['b']) for r in rows),
                'serialized_restart_exact':True,'ablated_coverage':0,
                'first_novel_successes':covered[:10],
                'first_novel_residuals':[n for n in novel if not matches(index,n)][:10]}
        if i<len(a.inputs)-1:
            for row in rows:
                path=first_descent(row['b'],row['K']+4096)
                if path is None: raise ValueError('unresolved training witness')
                stack=[]
                for j in range(len(path)-1,-1,-1):
                    while stack and path[stack[-1]]>=path[j]: stack.pop()
                    if stack and path[j] not in seen:
                        rule=compile_rule(path[j],stack[-1]-j)
                        if not validate_rule(rule): raise ValueError('certificate rejected')
                        rules.add(rule); seen.add(path[j])
                    stack.append(j)
            result['rules_after_training']=len(rules)
        results.append(result)
        print(json.dumps(result,sort_keys=True),flush=True)
        Path(a.out).write_text(json.dumps({'status':'EXPERIMENTALLY EXACT ON FINITE DOMAIN',
            'results':results,'scope':'novel source integers, not disjoint hereditary families',
            'rules':sorted(rules)},indent=2)+'\n')


if __name__=='__main__': main()
