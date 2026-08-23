#!/usr/bin/env python3
import json, re, sys
from collections import defaultdict
from pathlib import Path

TOKENS = (
    'eval','infer','apply','force','unfold','whnf','conv','defeq','unify',
    'key_env','prune_env','intern_frame','thunk','proj','iota','recursor'
)

def interesting(name: str) -> bool:
    n = name.lower()
    return any(t in n for t in TOKENS)

def clean_name(s: str) -> str:
    s = s.strip()
    if s.startswith('(') and ')' in s:
        s = s.split(')',1)[1].strip()
    return s

def parse(path: Path):
    cur_fn = '<unknown>'
    pending_callee = None
    pending_calls = 0
    total = 0
    edges = defaultdict(lambda: [0,0])
    funcs = defaultdict(int)
    # Callgrind positions normally contain one or more numeric costs; V1 uses
    # the first event (Ir) and keeps the parser deliberately format-tolerant.
    for raw in path.read_text(errors='replace').splitlines():
        line = raw.strip()
        if not line or line.startswith('#'):
            continue
        if line.startswith('fn='):
            cur_fn = clean_name(line[3:])
            pending_callee = None
            pending_calls = 0
        elif line.startswith('cfn='):
            pending_callee = clean_name(line[4:])
        elif line.startswith('calls='):
            parts = line[6:].split()
            try: pending_calls = int(parts[0])
            except Exception: pending_calls = 0
        elif line[0].isdigit() or line[0] in '+-*':
            nums = re.findall(r'(?<![A-Za-z])\d+(?![A-Za-z])', line)
            if not nums:
                continue
            try: cost = int(nums[-1])
            except Exception: continue
            total += cost
            if pending_callee is not None:
                if interesting(cur_fn) or interesting(pending_callee):
                    k=(cur_fn,pending_callee)
                    edges[k][0] += pending_calls
                    edges[k][1] += cost
                pending_callee = None
                pending_calls = 0
            elif interesting(cur_fn):
                funcs[cur_fn] += cost
    rows=[]
    for (src,dst),(calls,cost) in edges.items():
        rows.append({
            'caller':src,'callee':dst,'calls':calls,'instructions':cost,
            'fraction_of_profile': (cost/total if total else 0.0),
        })
    rows.sort(key=lambda r:r['instructions'], reverse=True)
    frows=[{'function':k,'self_instructions':v,'fraction_of_profile':(v/total if total else 0.0)} for k,v in funcs.items()]
    frows.sort(key=lambda r:r['self_instructions'], reverse=True)
    return {'source':str(path),'profile_cost_units':total,'edges':rows,'functions':frows}

def main():
    if len(sys.argv)<3:
        raise SystemExit('usage: parse_callgrind_handoffs.py OUT.json callgrind.out...')
    out=Path(sys.argv[1])
    profiles=[parse(Path(p)) for p in sys.argv[2:]]
    agg=defaultdict(lambda:[0,0,set()])
    for p in profiles:
        label=Path(p['source']).name
        for e in p['edges']:
            a=agg[(e['caller'],e['callee'])]
            a[0]+=e['calls']; a[1]+=e['instructions']; a[2].add(label)
    total=sum(p['profile_cost_units'] for p in profiles)
    aggregated=[]
    for (src,dst),(calls,cost,workloads) in agg.items():
        aggregated.append({
            'caller':src,'callee':dst,'calls':calls,'instructions':cost,
            'fraction_of_all_profiles':cost/total if total else 0.0,
            'workload_count':len(workloads),'workloads':sorted(workloads),
        })
    aggregated.sort(key=lambda r:r['instructions'],reverse=True)
    data={'tokens':TOKENS,'profiles':profiles,'aggregated_edges':aggregated,'total_profile_cost_units':total}
    out.parent.mkdir(parents=True,exist_ok=True)
    out.write_text(json.dumps(data,indent=2,sort_keys=True))
    print(json.dumps({'top_edges':aggregated[:20],'total_profile_cost_units':total},indent=2))

if __name__=='__main__': main()
