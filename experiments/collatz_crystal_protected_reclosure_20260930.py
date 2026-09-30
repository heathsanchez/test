"""Protected-object Crystal reclosure; universal adequacy is an explicit gate.

The --cached-local option uses only a cache written by our pinned parent replay.
Hosted qualification always reproduces the complete pinned parent.
"""
from __future__ import annotations
from collections import defaultdict, Counter, deque
from contextlib import redirect_stdout
from dataclasses import replace
from pathlib import Path
import argparse, hashlib, io, json, os, pickle, sys, types

parser=argparse.ArgumentParser()
parser.add_argument('--cached-local',action='store_true')
args=parser.parse_args()
if args.cached_local:
    parent,rows=pickle.load(open('v53-rows-local-cache.pickle','rb'))
    source_goal=json.load(open('source-goal-result.json'))
else:
    print('Reproduce pinned protected-object parents',flush=True)
    with redirect_stdout(io.StringIO()):
        import collatz_source_goal_transfer_20260930 as goal_parent
    parent=goal_parent.p.v.result['certificate_sha256']
    rows=goal_parent.p.v.rows
    source_goal=goal_parent.result
assert parent=='16bc1fafea228c441faa11cd5c19b14a82df7739dba89673fc18127dcfceaecc'
assert source_goal['certificate_sha256']=='4edd72e3371700118074b58438efeaaf6c7612cf289da6e86dcd0e1ce704302d'

# Load the two unmodified qualified components without importing unrelated
# MathGraph subsystems through its package initializer.
foundation=Path(os.environ.get('CRYSTAL_FOUNDATION_ROOT','mathgraph'))
pkg=types.ModuleType('mathgraph'); pkg.__path__=[str(foundation.resolve())]
sys.modules['mathgraph']=pkg
from mathgraph.crystal import Hyperedge, greatest_viability_kernel, find_quotient_falsifiers
from mathgraph.research_controller import (
    CampaignState, CandidateExperiment, ActionMode, VerificationGrade,
    ResidualStatus, decide_campaign)

N0=38911100780481085467
NC=3782158995862761504768
TRAIN={'N00011101','N11100010','N01011001','N10100110'}
FIFTH='N001011101'; SIXTH='N110100010'

def T(x): return x//2 if x%2==0 else (3*x+1)//2

def source_exit(n,y):
    if 0<y<n:
        return {'kind':'D','endpoint':str(y),'extra_steps':0}
    if y%8==5 and y<=4*n:
        p=(y-1)//4; z=T(T(T(y)))
        assert 0<p<n and T(p)==z
        return {'kind':'S','endpoint':str(z),'splice_endpoint':str(y),
                'lower_source':str(p),'lower_steps':1,'extra_steps':3}
    if y%3==2:
        p=(2*y-1)//3
        if 0<p<n:
            assert T(p)==y
            return {'kind':'M1','endpoint':str(y),'lower_source':str(p),
                    'lower_steps':1,'extra_steps':0}
    return None

print('Validate source admission, normalized transitions, and terminal witnesses',flush=True)
by_source=defaultdict(list); by_return=defaultdict(list)
for i,r in enumerate(rows):
    assert r['source']==N0+NC*r['t'] and r['k0']>=r['source'].bit_length()
    assert r['k1']-r['k0']==r['D'] and r['P']==1<<r['D']
    by_source[r['source']].append(i)
    by_return[r['t'],r['anchor']].append(i)
source_exits={}; witness_digests=[]
for n,ids in by_source.items():
    endpoints={}
    for i in ids:
        r=rows[i]
        for k,m in ((r['k0'],r['m0']),(r['k1'],r['m1'])):
            wanted=(1<<r['anchor'])*m-1
            if k in endpoints: assert endpoints[k]==wanted
            endpoints[k]=wanted
    y=n; cert=None
    for k in range(1601):
        if k in endpoints: assert endpoints[k]==y
        cert=source_exit(n,y)
        if cert is not None:
            assert k>max(endpoints), 'An observed return was recorded after source exit'
            source_exits[n]=(k,cert)
            break
        y=T(y)
    assert cert is not None
    witness_digests.append((str(n),source_exits[n]))
for r in rows:
    x=(1<<r['anchor'])*r['m0']-1
    for _ in range(r['D']): x=T(x)
    assert x==(1<<r['anchor'])*r['m1']-1
    assert r['P']*r['m1']==r['A']*r['m0']+r['B']

nextrow={}; terminal_witnesses=[]
for ids in by_return.values():
    ids.sort(key=lambda i:rows[i]['k0'])
    for a,b in zip(ids,ids[1:]):
        assert rows[a]['k1']==rows[b]['k0']
        assert rows[a]['m1']==rows[b]['m0']
        nextrow[a]=b
    r=rows[ids[-1]]
    k,cert=source_exits[r['source']]
    assert k>r['k0']
    terminal_witnesses.append((str(r['source']),r['anchor'],r['k0'],k-r['k0'],cert))

def graph(motifs):
    ids=[i for i,r in enumerate(rows) if r['motif'] in motifs]
    succ={rows[i]['key']:set() for i in ids}
    outputs=defaultdict(set)
    for i in ids:
        key=rows[i]['key']
        if i in nextrow:
            target=rows[nextrow[i]]['key']
            succ[key].add(target); outputs[key].add(('NEXT',repr(target)))
        else: outputs[key].add(('EXIT',))
    pred=defaultdict(set)
    for a,bs in succ.items():
        for b in bs: pred[b].add(a)
    rem={a:len(bs) for a,bs in succ.items()}
    q=deque(a for a,k in rem.items() if k==0); rank={}
    while q:
        a=q.popleft()
        rank[a]=max((rank[b]+1 for b in succ[a]),default=0)
        for b in pred[a]:
            rem[b]-=1
            if not rem[b]:q.append(b)
    kernel=set(succ)-rank.keys()
    assert all(rank[b]<rank[a] for a,bs in succ.items() for b in bs if a in rank and b in rank)
    report={'rows':len(ids),'cells':len(succ),'nonexit_edges':sum(map(len,succ.values())),
            'observed_recurrent_kernel':len(kernel),'max_rank':max(rank.values(),default=-1),
            'nonfunctional_successor_cells':sum(len(o)>1 for o in outputs.values())}
    return report,succ,rank,ids

def freeze_check(rank,motifs):
    counts=Counter(); violations=[]
    for i,r in enumerate(rows):
        if r['motif'] not in motifs:continue
        counts['rows']+=1
        if r['key'] not in rank: counts['unseen_current_cell']+=1;continue
        counts['recognized_current_cell']+=1
        if i not in nextrow:counts['actual_source_exit']+=1;continue
        nxt=rows[nextrow[i]]
        if nxt['key'] not in rank:counts['unseen_successor_cell']+=1;continue
        if rank[nxt['key']]>=rank[r['key']]:
            counts['frozen_rank_failure']+=1
            violations.append((i,nextrow[i]))
        else:counts['strict_rank_progress']+=1
    return dict(counts),violations

train,s0,r0,_=graph(TRAIN)
fifth_fail,v5=freeze_check(r0,{FIFTH})
fifth,s1,r1,_=graph(TRAIN|{FIFTH})
sixth_fail,v6=freeze_check(r1,{SIXTH})
full,s2,r2,allids=graph(TRAIN|{FIFTH,SIXTH})
assert not full['observed_recurrent_kernel']
assert not freeze_check(r2,TRAIN|{FIFTH,SIXTH})[1]

# Locate real same-cell/different-validity witnesses for the frozen training
# rank. Unknown ports are omitted from this falsifier test, not called valid.
representation={}; protected_target={}
for i in allids:
    key=rows[i]['key']
    if key not in r0: continue
    if i not in nextrow:
        valid=True
    else:
        target=rows[nextrow[i]]['key']
        if target not in r0:continue
        valid=r0[target]<r0[key]
    representation[str(i)]=(repr(key),)
    protected_target[str(i)]=('VALID_SOURCE_EXIT_OR_FROZEN_RANK_PROGRESS' if valid else 'FROZEN_RANK_NONDECREASE',)
frozen_falsifiers=find_quotient_falsifiers(representation,protected_target)
assert frozen_falsifiers
rank_violations_after_reclosure=len(freeze_check(r2,TRAIN|{FIFTH,SIXTH})[1])
assert rank_violations_after_reclosure==0
layers=sorted(set(r2.values()))
layer_edges=sorted({(r2[a],r2[b]) for a,bs in s2.items() for b in bs})
assert all(b<a for a,b in layer_edges)
live={'RAW_SOURCE_ADMISSION','ORIGINAL_SOURCE_BINDING','FINITE_BOUNDARY'}
edges=[Hyperedge(str(a),str(b),'continue',frozenset(live),
                evidence_refs=('independently-replayed-normalized-macro',))
       for a,b in layer_edges]
native_kernel=greatest_viability_kernel(map(str,layers),('continue',),edges,live)
assert not native_kernel

# The qualified controller selects reclosure before any new coordinate.
invariants=('original_source_binding','actual_transition_admission','zero_tail_phase','all_progress_edges_retained')
state=CampaignState('collatz-protected-future-loop','source-relative progress or lower-source exit',
    'V53-full-live-frozen-four-motif-model','frozen_rank_transport_failure',ResidualStatus.OPEN,
    ('exact-held-motif-rank-counterexamples',),invariants,
    ('crystal-greatest-viability-kernel@2c6a845','V48-progress-or-exit-socket'),
    ('finite_bank_completeness','bounded_horizon_as_universality'))
reclose=CandidateExperiment('reclose_warranted_transitions',state.campaign_id,
    'Propagate exact admitted transitions and certified exits, then reclose before refining',
    state.residual_id,ActionMode.REUSE,1.0,1.0,VerificationGrade.KERNEL,
    'raw-source-replay-plus-independent-DAG-and-native-Crystal-plus-Lean-layer-check',
    ('acyclic-observed-full-graph','exact-frozen-rank-failures'),invariants,
    ('crystal-greatest-viability-kernel@2c6a845',))
grow=CandidateExperiment('grow_constructor_bank',state.campaign_id,'Grow the finite bank',
    state.residual_id,ActionMode.SEARCH,1.0,1.0,VerificationGrade.INDEPENDENT,
    'bounded-replay',('prior-bank-transfer',),invariants,
    mechanism_tags=('finite_bank_completeness',))
split=CandidateExperiment('split_all_successor_aliases',state.campaign_id,
    'Add coordinates merely to force successor determinism',state.residual_id,
    ActionMode.REFINE,1.0,1.0,VerificationGrade.INDEPENDENT,'held-motif-replay',
    ('successor-alias-count',),invariants,separator_refs=())
decision=decide_campaign(state,[reclose,grow,split])
assert decision.selected_candidate_id=='reclose_warranted_transitions'
ablation=decide_campaign(state,[replace(reclose,preserves_invariants=invariants[1:]),grow,split])
assert ablation.status=='HOLD'

global_state=replace(state,residual_id='universal_admission_and_progress_transport',
    residual_evidence_refs=('finite_reclosure_is_not_universal_coverage',))
global_decision=decide_campaign(global_state,[
    replace(grow,targets_residual=global_state.residual_id),
    replace(split,targets_residual=global_state.residual_id)])
assert global_decision.status=='HOLD'
admission={'finite_source_replay':'WARRANTED_BOUNDED',
    'source_bound_exit_certificates':'WARRANTED_BOUNDED',
    'finite_normalized_macro_transitions':'WARRANTED_BOUNDED',
    'finite_ranked_kernel_empty':'WARRANTED_BOUNDED',
    'universal_source_coverage':'UNKNOWN','universal_macro_admission_totality':'UNKNOWN',
    'universal_progress_or_exit_transport':'UNKNOWN'}
qed=all(admission[k]=='WARRANTED' for k in ('universal_source_coverage',
    'universal_macro_admission_totality','universal_progress_or_exit_transport'))
assert not qed

first=None
if v5:
    a,b=v5[0];r=rows[a]
    first={'source':str(r['source']),'t':str(r['t']),'current_key':list(r['key']),
       'depth':[r['k0'],r['k1']],'old_rank':r0[r['key']],
       'old_successor_rank':r0[rows[b]['key']],
       'reclosed_rank':r1[r['key']],'reclosed_successor_rank':r1[rows[b]['key']]}

result={'schema':'COLLATZ_CRYSTAL_PROTECTED_OBJECT_RECLOSURE_20260930',
    'foundation_commit':'metalogiclabs/mathgraph@2c6a845f113ea902734b242b1a3c9795574e30ff',
    'foundation_source_hashes':{f:hashlib.sha256((foundation.joinpath(f).read_text().rstrip('\n')+'\n').encode()).hexdigest()
                               for f in ('crystal.py','research_controller.py')},
    'protected_object':{'objective':'eventual descent below fixed original n, or warranted smaller-source merge',
      'source_family':{'N0':str(N0),'NC':str(NC),'parameter':'t >= 0'},
      'normalization':'post-zero-tail same-anchor owner x=2^r*m-1, every observed return retained',
      'quotient':'frozen V53 source-free key interpreted as a nondeterministic abstract relation',
      'coverage':'finite observed boundary only; no universal adequacy claim'},
    'sources_independently_replayed':len(by_source),'return_rows_independently_replayed':len(rows),
    'terminal_macro_certificates':len(terminal_witnesses),
    'terminal_certificate_sha256':hashlib.sha256(json.dumps(terminal_witnesses,sort_keys=True).encode()).hexdigest(),
    'training_reclosure':train,'fifth_motif_frozen_check':fifth_fail,
    'after_fifth_reclosure':fifth,'sixth_motif_frozen_check':sixth_fail,
    'full_observed_reclosure':full,'first_frozen_rank_counterexample':first,
    'progress_sufficient_rank_layers':len(layers),'rank_layer_edges':len(layer_edges),
    'native_Crystal_recurrent_kernel_size':len(native_kernel),
    'frozen_protected_rank_falsifier_pairs':len(frozen_falsifiers),
    'protected_rank_violations_after_reclosure':rank_violations_after_reclosure,
    'source_binding_control':source_goal['synthesis_holdout'],
    'local_controller':decision.to_dict(),'source_binding_policy_ablation':ablation.to_dict(),
    'global_controller':global_decision.to_dict(),'proof_admission':admission,
    'qed_admitted':qed,'global_collatz':'UNKNOWN',
    'boundary':'All terminal and macro witnesses are exact for this finite source set. Successor aliases are allowed when every admitted observation exits or strictly decreases the common rank. Reclosure earns no universal coverage. Rank layers are finite-boundary certificates, not an all-depth rank bound.'}
result['certificate_sha256']=hashlib.sha256(json.dumps(result,sort_keys=True,separators=(',',':')).encode()).hexdigest()
with open('controlled-reclosure-result.json','w') as f:json.dump(result,f,indent=2,sort_keys=True)
with open('controlled-reclosure-layer-edges.json','w') as f:json.dump(layer_edges,f)
print(json.dumps({k:v for k,v in result.items() if k not in
    ('local_controller','source_binding_policy_ablation','global_controller')},indent=2,sort_keys=True),flush=True)
