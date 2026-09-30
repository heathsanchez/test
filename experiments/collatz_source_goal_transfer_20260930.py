"""Goal-bound certificate transfer on the exact repayment residual.

Synthesis holdout from an already-observed corpus; not a universal proof.
Each positive certificate is independently checked against the actual source.
"""
from contextlib import redirect_stdout
from collections import defaultdict, Counter
import io, json, hashlib, pickle

print('Reproducing pinned parent and repayment experiment',flush=True)
with redirect_stdout(io.StringIO()):
    import collatz_symbolic_repayment_guards_20260930 as p
assert p.result['certificate_sha256']=='49c67affb77a79518286d2e89e0c6b9a646807c8ce710ff86faff2550739158d'
with open('v53-rows-local-cache.pickle','wb') as f:
    pickle.dump((p.v.result['certificate_sha256'],p.v.rows),f)

def T(x): return (3*x+1)//2 if x&1 else x//2

def goal(n,y):
    if 0<y<n: return 'D'
    if y%8==5 and y<=4*n: return 'S'
    if y%3==2:
        lower=(2*y-1)//3
        if 0<lower<n and T(lower)==y: return 'M1'
    return None

def checked_certificate(n,x,D,law,kind):
    A,B,P=law; y=x
    for _ in range(D): y=T(y)
    assert P*y==A*x+B
    if kind=='D':
        assert 0<y<n
        return {'kind':kind,'endpoint':str(y),'extra_steps':0}
    if kind=='M1':
        lower=(2*y-1)//3
        assert y%3==2 and 0<lower<n and T(lower)==y
        return {'kind':kind,'endpoint':str(y),'lower_source':str(lower),'lower_steps':1,'extra_steps':0}
    assert kind=='S' and y%8==5 and y<=4*n
    lower=(y-1)//4
    z=T(T(T(y)))
    assert 0<lower<n and T(lower)==z
    return {'kind':kind,'splice_endpoint':str(y),'endpoint':str(z),'lower_source':str(lower),'lower_steps':1,'extra_steps':3}

train={'N00011101','N11100010','N01011001','N10100110'}
starts=[]; bysource=defaultdict(list)
for row in p.residual_starts:
    bysource[row['source']].append(row)
for n,rs in bysource.items():
    depths={z['k0']:z for z in rs}
    y=n
    for k in range(max(depths)+1):
        if k in depths:
            assert y==((1<<depths[k]['anchor'])*depths[k]['m0']-1)
        y=T(y)

bank={}; targets={}; stats=Counter()
for start in p.residual_starts:
    n=start['source']; x=(1<<start['anchor'])*start['m0']-1
    assert goal(n,x) is None
    y=x; A,B,P=1,0,1; word=[]
    found=None
    for D in range(1,p.v.CAP-start['k0']+1):
        bit=y&1; word.append(str(bit))
        if bit: A,B=3*A,3*B+P
        P*=2; y=T(y)
        assert P*y==A*x+B
        kind=goal(n,y)
        if kind is not None:
            rho=(-B*pow(A,-1,P))%P
            assert x%P==rho
            g={'A':A,'B':B,'P':P,'D':D,'rho':rho,'word':''.join(word)}
            cert=checked_certificate(n,x,D,(A,B,P),kind)
            key=(D,rho)
            if start['motif'] in train:
                if key in bank: assert all(bank[key][a]==g[a] for a in g)
                bank.setdefault(key,g)
            targets[start['t'],start['anchor'],start['k0']]={'kind':kind,'depth':D,'certificate':cert}
            stats['all_starts_actual_exit_'+kind]+=1
            starts.append((start,x,key))
            found=kind; break
    assert found is not None, 'The pinned no-censoring source must exit before CAP'

index=defaultdict(dict)
for (D,rho),g in bank.items(): index[D][rho]=g
heldstats=Counter(); first_failure=None; first_bad_binding=None; successes=[]
origin_descent_starts={(s['t'],s['anchor'],s['k0']) for s,_,_ in p.observed}
for start,x,actualkey in starts:
    if start['motif'] in train: continue
    n=start['source']; sk=(start['t'],start['anchor'],start['k0'])
    heldstats['starts']+=1
    matched=[]; bound=[]; ablated=[]
    for D,rhos in index.items():
        g=rhos.get(x%(1<<D))
        if g is None: continue
        numerator=g['A']*x+g['B']
        assert numerator%g['P']==0
        y=numerator//g['P']; matched.append((g,y))
        kind=goal(n,y)
        if kind is not None: bound.append((g,y,kind))
        # Deliberately wrong binding for a negative semantic control.
        wrong=goal(x,y)
        if wrong is not None: ablated.append((g,y,wrong))
    has_repayment=sk in origin_descent_starts
    if not matched: heldstats['no_frozen_word_admitted']+=1
    elif not bound: heldstats['admitted_word_but_original_source_guard_fails']+=1
    if bound:
        g,y,kind=min(bound,key=lambda z:(z[0]['D'],z[2]))
        cert=checked_certificate(n,x,g['D'],(g['A'],g['B'],g['P']),kind)
        heldstats['source_bound_frozen_certificate']+=1
        heldstats['certificate_'+kind]+=1
        successes.append((str(n),start['k0'],g['D'],cert))
    else:
        heldstats['uncovered']+=1
        if first_failure is None:
            first_failure={'source':str(n),'t':str(start['t']),'root_depth':start['k0'],
              'root_endpoint':str(x),'anchor':start['anchor'],
              'has_observed_same_anchor_repayment':has_repayment,
              'actual_eventual_exit':targets[sk],
              'frozen_words_admitted':len(matched)}
    if ablated:
        heldstats['wrong_current_endpoint_binding_accepts']+=1
        g,y,kind=min(ablated,key=lambda z:(z[0]['D'],z[2]))
        if goal(n,y) is None:
            heldstats['wrong_binding_selected_certificate_invalid_for_source']+=1
            if first_bad_binding is None:
                first_bad_binding={'source':str(n),'root_depth':start['k0'],'root_endpoint':str(x),
                    'candidate_steps':g['D'],'candidate_endpoint':str(y),'wrong_kind':kind,
                    'law':{k:str(g[k]) for k in ('A','B','P','rho')},
                    'actual_eventual_exit':targets[sk]}
    # Partition the previous 1,349 failures rather than treating them as one
    # missing-law class. This changes no baseline result.
    prior_match=False
    for D,rhos in p.guardindex[start['anchor']].items():
        g=rhos.get(start['m0']%(1<<(D+1)))
        if g is not None and start['m0']>=int(g['floor']): prior_match=True; break
    if not prior_match:
        heldstats['prior_1349_has_observed_repayment' if has_repayment else 'prior_1349_exits_without_observed_repayment']+=1
        heldstats['prior_1349_source_bound_certificate' if bound else 'prior_1349_still_uncovered']+=1

result={'schema':'COLLATZ_SOURCE_GOAL_CERTIFICATE_TRANSFER_20260930',
    'parent_certificate':p.result['certificate_sha256'],'stats':dict(stats),
    'training_word_certificates':len(bank),'synthesis_holdout':dict(heldstats),
    'first_uncovered':first_failure,'first_bad_origin_binding':first_bad_binding,
    'source_binding_ablation':'Replace original n by current endpoint x; not a valid OrdinaryExit certificate for n.',
    'successes_sha256':hashlib.sha256(json.dumps(successes,sort_keys=True).encode()).hexdigest(),
    'global_collatz':'UNKNOWN',
    'boundary':'Previously observed V53 corpus, fixed four/two motif synthesis split. All 5487 residual starts have actual finite source-bound exit certificates, but frozen-word transfer is not universal coverage. No all-depth availability, completeness, or new global Collatz theorem.'}
result['certificate_sha256']=hashlib.sha256(json.dumps(result,sort_keys=True,separators=(',',':')).encode()).hexdigest()
with open('source-goal-result.json','w') as f: json.dump(result,f,indent=2,sort_keys=True)
print(json.dumps(result,indent=2,sort_keys=True),flush=True)
