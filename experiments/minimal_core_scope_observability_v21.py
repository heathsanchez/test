import json, math, os, random

PARENT='artifacts/v20_parent/result.json'
EVAL_SEED=2026082721
EVAL_TRIALS=64

# Reuse the exact frozen V20 mechanics without executing its 64-trial main loop.
src=open('experiments/minimal_core_epistemic_policy_scope_v20.py',encoding='utf-8').read()
prefix=src.split('perms=list(itertools.permutations(states))',1)[0]
ns={}
exec(prefix,ns)
perms=list(ns['itertools'].permutations(ns['states']))

def features(x):
    R=float(x['cv_relational']); G=float(x['cv_global'])
    rf=list(map(float,x['cv_rel_folds'])); gf=list(map(float,x['cv_global_folds']))
    gaps=[(r-g)/(r+g+1.0) for r,g in zip(rf,gf)]
    mr=sum(rf)/len(rf); mg=sum(gf)/len(gf)
    sr=math.sqrt(sum((v-mr)**2 for v in rf)/len(rf)); sg=math.sqrt(sum((v-mg)**2 for v in gf)/len(gf))
    return [
        math.log1p(R), math.log1p(G), (R-G)/(R+G+1.0),
        sum(gaps)/len(gaps), min(gaps), max(gaps),
        sum(g<0 for g in gaps)/len(gaps), sr/(mr+1.0), sg/(mg+1.0),
    ]

def standardizer(X):
    p=len(X[0]); mu=[sum(r[j] for r in X)/len(X) for j in range(p)]
    sd=[]
    for j in range(p):
        s=math.sqrt(sum((r[j]-mu[j])**2 for r in X)/len(X)); sd.append(s if s>1e-9 else 1.0)
    return mu,sd

def zx(x,mu,sd): return [(v-m)/s for v,m,s in zip(x,mu,sd)]

def fit_logistic(X,y):
    mu,sd=standardizer(X); Z=[zx(x,mu,sd) for x in X]; p=len(Z[0]); w=[0.0]*p; b=0.0
    pos=sum(y); neg=len(y)-pos; pw=neg/max(1,pos)
    for ep in range(1600):
        eta=.08/(1+ep/400); gw=[0.0]*p; gb=0.0
        for z,t in zip(Z,y):
            a=max(-30,min(30,b+sum(q*r for q,r in zip(w,z)))); pr=1/(1+math.exp(-a)); g=(pw if t else 1.0)*(pr-t); gb+=g
            for j in range(p): gw[j]+=g*z[j]
        n=len(Z); b-=eta*gb/n
        for j in range(p): w[j]-=eta*(gw[j]/n+1e-3*w[j])
    def score(x):
        z=zx(x,mu,sd); a=max(-30,min(30,b+sum(q*r for q,r in zip(w,z)))); return 1/(1+math.exp(-a))
    return score

def auc(scores,labels):
    pos=[s for s,y in zip(scores,labels) if y]; neg=[s for s,y in zip(scores,labels) if not y]
    if not pos or not neg:return 0.5
    wins=0.0
    for a in pos:
        for b in neg:wins+=1.0 if a>b else .5 if a==b else 0.0
    return wins/(len(pos)*len(neg))

with open(PARENT) as f: parent=json.load(f)
train_rows=parent['trial_results']
X=[features(x) for x in train_rows]
y=[1 if x['relational_steps']>x['global_steps'] else 0 for x in train_rows]
model=fit_logistic(X,y)

# Threshold is frozen from parent only: among thresholds at observed parent scores, choose the
# lowest-cost rule subject to rescuing >= half parent losses and harming <= 8 parent wins.
ps=[model(x) for x in X]
candidates=sorted(set(ps+[0.0,1.0]))
best=None
for th in candidates:
    switch=[p>=th for p in ps]
    rescue=sum(s and yy for s,yy in zip(switch,y)); harm=sum(s and not yy for s,yy in zip(switch,y))
    if rescue>=math.ceil(sum(y)/2) and harm<=8:
        # Prefer fewer switches, then larger threshold.
        key=(sum(switch),-th)
        if best is None or key<best[0]:best=(key,th)
threshold=best[1] if best else 1.0

results=[]
for t in range(EVAL_TRIALS):
    rng=random.Random(EVAL_SEED+t)
    pm=perms[rng.randrange(len(perms))]
    train=[(pid,f,ns['relabel_partition'](A,pm),ns['relabel_partition'](B,pm),scope,perm) for pid,f,A,B,scope,perm in ns['train0']]
    held=[(pid,f,ns['relabel_partition'](A,pm),ns['relabel_partition'](B,pm),scope,perm) for pid,f,A,B,scope,perm in ns['held0']]
    qs=[ns['remap_code'](c,pm) for c in rng.sample(ns['all_codes'],64)]
    _,cvR,cvG,foldR,foldG=ns['source_cv_choice'](train,qs)
    stub={'cv_relational':cvR,'cv_global':cvG,'cv_rel_folds':foldR,'cv_global_folds':foldG}
    risk=model(features(stub)); switch=risk>=threshold
    rs=ns['fit_relational'](train,qs); gs=ns['fit_global'](train,qs)
    r=ns['score_steps'](held,rs); g=ns['score_steps'](held,gs); m=g if switch else r
    results.append({'trial':t,'risk':risk,'switch_global':switch,'relational_steps':r,'global_steps':g,'meta_steps':m,'loss_label':r>g,'completecover_ok':ns['completecover_ok'](held)})

labels=[int(x['loss_label']) for x in results]; scores=[x['risk'] for x in results]
rel=[x['relational_steps'] for x in results]; glob=[x['global_steps'] for x in results]; meta=[x['meta_steps'] for x in results]
losses=sum(labels); rescues=sum(x['switch_global'] and x['loss_label'] for x in results); harms=sum(x['switch_global'] and not x['loss_label'] for x in results)
switches=sum(x['switch_global'] for x in results)
A=auc(scores,labels)
# Oracle establishes whether scope switching has useful headroom on this held-out family.
oracle=[min(r,g) for r,g in zip(rel,glob)]

def median(v):
    z=sorted(v); n=len(z); return z[n//2] if n%2 else (z[n//2-1]+z[n//2])/2

gates={
 'G1_completecover_all':all(x['completecover_ok'] for x in results),
 'G2_oracle_switching_has_headroom':sum(oracle)<sum(rel) and max(oracle)<max(rel),
 'G3_new_family_contains_at_least_four_relational_losses':losses>=4,
 'G4_source_visible_risk_auc_at_least_0p75':A>=0.75,
 'G5_rescue_at_least_half_relational_losses':rescues>=math.ceil(losses/2),
 'G6_harm_at_most_eight_relational_wins':harms<=8,
 'G7_meta_mean_no_worse_than_relational':sum(meta)<=sum(rel),
 'G8_meta_worst_case_strictly_better_than_relational':max(meta)<max(rel),
 'G9_threshold_frozen_from_parent_only':True,
}
result={'schema':'minimal.core.scope.observability.v21','parent_run':32897971374,'eval_seed':EVAL_SEED,'trials':EVAL_TRIALS,
        'parent_losses':sum(y),'threshold':threshold,'eval_losses':losses,'switches':switches,'rescues':rescues,'harms':harms,'auc':A,
        'relational_mean':sum(rel)/len(rel),'global_mean':sum(glob)/len(glob),'meta_mean':sum(meta)/len(meta),'oracle_mean':sum(oracle)/len(oracle),
        'relational_median':median(rel),'global_median':median(glob),'meta_median':median(meta),
        'relational_max':max(rel),'global_max':max(glob),'meta_max':max(meta),'oracle_max':max(oracle),
        'gates':gates,'trial_results':results,'pass':all(gates.values()),
        'interpretation_boundary':'PASS means V19 relational-policy failure has a transferable source-visible scope signal after calibration on prior verified trials. FAIL means this frozen source-visible feature family is insufficient; it does not prove scope is intrinsically unobservable.'}
os.makedirs('artifacts/minimal_core_scope_observability_v21',exist_ok=True)
with open('artifacts/minimal_core_scope_observability_v21/result.json','w') as f:json.dump(result,f,indent=2,sort_keys=True)
print(json.dumps(result,indent=2,sort_keys=True))
if not result['pass']:raise SystemExit('FAIL_MINIMAL_CORE_SCOPE_OBSERVABILITY_V21')
print('PASS_MINIMAL_CORE_SCOPE_OBSERVABILITY_V21')
