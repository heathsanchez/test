"""Throwaway full-live audit of the pinned V53 corpus; no global proof."""
from contextlib import redirect_stdout
from collections import defaultdict, Counter, deque
import io, json, hashlib, time, sys
from pathlib import Path

print('Replaying pinned V53 corpus', flush=True)
started=time.time()
with redirect_stdout(io.StringIO()):
    import collatz_crystal_nonpositive_budget_kernel_v53 as v

assert v.result['certificate_sha256']=='16bc1fafea228c441faa11cd5c19b14a82df7739dba89673fc18127dcfceaecc'
print('Pinned V53 certificate reproduced', flush=True)

def audit_graph(rows, chronological=False):
    grouped=defaultdict(list)
    for row in rows:
        group=row['t'] if chronological else (row['t'],row['anchor'])
        grouped[group].append(row)
    nodes={row['key'] for row in rows}
    succ={u:set() for u in nodes}
    witnessed={}
    for group,rs in grouped.items():
        rs.sort(key=lambda z:(z['k0'],z['k1']))
        for a,b in zip(rs,rs[1:]):
            succ[a['key']].add(b['key'])
            witnessed.setdefault((a['key'],b['key']),(a,b))
    pred=defaultdict(set)
    for u,vs in succ.items():
        for w in vs: pred[w].add(u)
    remaining={u:len(vs) for u,vs in succ.items()}
    queue=deque(u for u,d in remaining.items() if d==0)
    rank={}
    while queue:
        u=queue.popleft()
        rank[u]=max((rank[w]+1 for w in succ[u]),default=0)
        for p in pred[u]:
            remaining[p]-=1
            if remaining[p]==0: queue.append(p)
    leftover=nodes-rank.keys()
    if not leftover:
        assert all(rank[w]<rank[u] for u,vs in succ.items() for w in vs)
    kinds=Counter()
    for a,b in witnessed.values():
        kinds[('R' if a['residual'] else 'P')+'->'+('R' if b['residual'] else 'P')]+=1
    return {'nodes':len(nodes),'edges':sum(map(len,succ.values())),
            'leftover_after_sink_elimination':len(leftover),
            'max_rank':max(rank.values(),default=None),
            'rank_layers':dict(sorted(Counter(rank.values()).items())),
            'edge_kinds':dict(kinds)},succ,rank

full,succ,rank=audit_graph(v.rows)
chrono,_,_=audit_graph(v.rows,True)
mixed=defaultdict(set)
for row in v.rows: mixed[row['key']].add(row['residual'])

groups=defaultdict(list)
for row in v.rows: groups[row['t'],row['anchor']].append(row)
macro=Counter(); first_overshoot=None; max_wait=0
for rs in groups.values():
    rs.sort(key=lambda z:(z['k0'],z['k1']))
    for i,start in enumerate(rs):
        if not start['residual']:continue
        candidates=rs[i:]
        local=next((j for j,z in enumerate(candidates) if z['progress']),None)
        origin=next((j for j,z in enumerate(candidates) if z['m1']<start['m0']),None)
        if local is not None:
            macro['later_local_progress']+=1
            if origin is None or origin>local:
                macro['local_progress_does_not_yet_beat_macro_start']+=1
                if first_overshoot is None:
                    z=candidates[local]
                    first_overshoot={'source':str(start['source']),'t':str(start['t']),
                       'anchor':start['anchor'],'start_depth':start['k0'],
                       'start_owner':str(start['m0']),'local_depth':[z['k0'],z['k1']],
                       'local_start_owner':str(z['m0']),'local_end_owner':str(z['m1']),
                       'positive_local_budget':z['W']>0,'W':str(z['W']),
                       'first_origin_descent_event':origin}
        if origin is not None:
            macro['later_descent_below_macro_start']+=1
            max_wait=max(max_wait,origin+1)
        else:macro['needs_later_exit_or_other_anchor']+=1

result={'schema':'COLLATZ_V53_FULL_LIVE_AUDIT_LOCAL',
  'pinned_commit':'2b49ce24eb1593e045a7e1b7bcb8782f3f426d02',
  'parent_certificate':v.result['certificate_sha256'],
  'source_count':v.sources,'return_rows':len(v.rows),
  'full_same_anchor_graph':full,
  'chronological_observation_graph':chrono,
  'keys_with_both_progress_and_residual_occurrences':sum(len(x)>1 for x in mixed.values()),
  'macro_start_relative_audit':dict(macro),'max_observed_origin_wait_returns':max_wait,
  'first_local_overshoot':first_overshoot,
  'global_collatz':'UNKNOWN',
  'boundary':'Pinned finite corpus only. Full graph includes local-progress edges. Chronological graph is an observation-order diagnostic, not a proved macro transition. No universal grammar coverage, complete event normalization, or full-live rank theorem is established.'}
result['certificate_sha256']=hashlib.sha256(json.dumps(result,sort_keys=True,separators=(',',':')).encode()).hexdigest()
outdir=Path(sys.argv[1] if len(sys.argv)>1 else 'evidence/collatz-ros-full-live-audit-20260930')
outdir.mkdir(parents=True,exist_ok=True)
with open(outdir/'result.json','w') as f:json.dump(result,f,indent=2,sort_keys=True)
print(json.dumps(result,indent=2,sort_keys=True),flush=True)
print('Elapsed',round(time.time()-started,2),flush=True)
