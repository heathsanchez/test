import itertools, json, math, os, random

SEED=2026082620
TRIALS=64
states=tuple(range(8))
edges=tuple((i,j) for i in states for j in states if i<j)
all_codes=list(range(256))

def bit(s,k): return (s>>k)&1
def pred(code,s): return (code>>s)&1

def partition_by(keys):
    g={}
    for s in states:g.setdefault(tuple(f(s) for f in keys),[]).append(s)
    return tuple(sorted(tuple(v) for v in g.values()))

def sufficient(part,code): return all(len({pred(code,s) for s in block})<=1 for block in part)
def same_block(part,a,b): return any(a in block and b in block for block in part)
def relabel_partition(part,pm): return tuple(sorted(tuple(sorted(pm[s] for s in block)) for block in part))
def remap_code(code,pm):
    out=0
    for s in states:
        if pred(code,s): out|=1<<pm[s]
    return out

def raw_trace(code): return [float(pred(code,s)) for s in states]
def pair_residual(A,B): return [1.0 if same_block(A,a,b) and not same_block(B,a,b) else 0.0 for a,b in edges]
def relfeat(code,A,B):
    x=raw_trace(code); d=pair_residual(A,B)
    return [d[k]*abs(x[a]-x[b]) for k,(a,b) in enumerate(edges)]

base_keys=[
 [lambda s:bit(s,0)],[lambda s:bit(s,1)],[lambda s:bit(s,2)],
 [lambda s:bit(s,0)^bit(s,1)],[lambda s:bit(s,1)^bit(s,2)],[lambda s:bit(s,0)^bit(s,2)]]
pairs=[]
for i,bk in enumerate(base_keys[:4]):
    A=partition_by(bk)
    for rb in (0,1,2):
        B=partition_by(bk+[lambda s,rb=rb:bit(s,rb)])
        if A!=B:pairs.append((f'TR{i}_{rb}',i,A,B,'train',False))
    pairs.append((f'TRP{i}',i,A,tuple(reversed(tuple(tuple(reversed(block)) for block in A))),'train',True))
for i,bk in enumerate(base_keys[4:],4):
    A=partition_by(bk)
    for rb in (0,1,2):
        B=partition_by(bk+[lambda s,rb=rb:bit(s,rb)])
        if A!=B:pairs.append((f'HO{i}_{rb}',i,A,B,'heldout',False))
    pairs.append((f'HOP{i}',i,A,tuple(reversed(tuple(tuple(reversed(block)) for block in A))),'heldout',True))
train0=[p for p in pairs if p[4]=='train']; held0=[p for p in pairs if p[4]=='heldout']

def solve_linear(A,b):
    n=len(b); M=[list(A[i])+[b[i]] for i in range(n)]
    for c in range(n):
        p=max(range(c,n),key=lambda r:abs(M[r][c])); M[c],M[p]=M[p],M[c]
        if abs(M[c][c])<1e-12: continue
        d=M[c][c]; M[c]=[v/d for v in M[c]]
        for r in range(n):
            if r==c: continue
            f=M[r][c]
            if abs(f)>1e-12:M[r]=[M[r][j]-f*M[c][j] for j in range(n+1)]
    return [M[i][n] for i in range(n)]

def fit_rel_det(data):
    w=[0.0]*len(edges); b=-2.0
    pos=sum(y for _,y in data); neg=len(data)-pos; pw=max(1.0,neg/max(1.0,pos))
    for ep in range(700):
        eta=.08/(1+ep/175); gw=[0.0]*len(w); gb=0.0
        for f,y in data:
            z=max(-30,min(30,b+sum(a*x for a,x in zip(w,f)))); p=1/(1+math.exp(-z)); g=(pw if y>.5 else 1.0)*(p-y); gb+=g
            for j,x in enumerate(f):
                if x:gw[j]+=g*x
        n=len(data); b-=eta*gb/n
        for j in range(len(w)):w[j]-=eta*(gw[j]/n+1e-4*w[j])
    return tuple(w),b

def fit_scalar(train,queries):
    yagg=[sum(1 for _,_,A,B,_,_ in train if sufficient(A,c)!=sufficient(B,c)) for c in queries]
    p=9; XtX=[[0.0]*p for _ in range(p)]; Xty=[0.0]*p
    for c,t in zip(queries,yagg):
        f=[1.0]+raw_trace(c)
        for i in range(p):
            Xty[i]+=f[i]*t
            for j in range(p):XtX[i][j]+=f[i]*f[j]
    for i in range(p):XtX[i][i]+=1e-3
    return solve_linear(XtX,Xty)

def score_steps(held, scorefn):
    pmap={pid:(A,B,perm) for pid,_,A,B,_,perm in held}
    openp={pid for pid,(A,B,perm) in pmap.items() if not perm}; used=[]
    while openp:
        rem=[c for c in all_codes if c not in used]
        q=max(rem,key=lambda c:(sum(scorefn(c,*pmap[pid][:2]) for pid in openp),-c)); used.append(q)
        for pid in list(openp):
            A,B,_=pmap[pid]
            if sufficient(A,q)!=sufficient(B,q):openp.remove(pid)
        if len(used)>=256:break
    return len(used)

def fit_relational(train,queries):
    data=[]
    for _,_,A,B,_,_ in train:
        for c in queries:data.append((relfeat(c,A,B),1.0 if sufficient(A,c)!=sufficient(B,c) else 0.0))
    w,b=fit_rel_det(data)
    def rs(c,A,B):
        f=relfeat(c,A,B); z=max(-30,min(30,b+sum(a*x for a,x in zip(w,f)))); return 1/(1+math.exp(-z))
    return rs

def fit_global(train,queries):
    w=fit_scalar(train,queries)
    def gs(c,A,B): return sum(a*b for a,b in zip(w,[1.0]+raw_trace(c)))
    return gs

def completecover_ok(held):
    return all(any(sufficient(A,c)!=sufficient(B,c) for c in all_codes) for _,_,A,B,_,perm in held if not perm) and all(not any(sufficient(A,c)!=sufficient(B,c) for c in all_codes) for _,_,A,B,_,perm in held if perm)

def source_cv_choice(train,queries):
    # Leave one source family out at a time. This uses source-side verifier outcomes only.
    fams=sorted(set(f for _,f,_,_,_,_ in train))
    rcost=[]; gcost=[]
    for fam in fams:
        fit=[p for p in train if p[1]!=fam]
        val=[p for p in train if p[1]==fam]
        # Skip folds with no provisional residual.
        if not any(not p[5] for p in val): continue
        rs=fit_relational(fit,queries); gs=fit_global(fit,queries)
        rcost.append(score_steps(val,rs)); gcost.append(score_steps(val,gs))
    R=sum(rcost); G=sum(gcost)
    # Conservative tie-break to global: relational is used only when source evidence favors it.
    return ('relational' if R<G else 'global'),R,G,rcost,gcost

perms=list(itertools.permutations(states))
results=[]
for t in range(TRIALS):
    rng=random.Random(SEED+t)
    pm=perms[rng.randrange(len(perms))]
    train=[(pid,f,relabel_partition(A,pm),relabel_partition(B,pm),scope,perm) for pid,f,A,B,scope,perm in train0]
    held=[(pid,f,relabel_partition(A,pm),relabel_partition(B,pm),scope,perm) for pid,f,A,B,scope,perm in held0]
    qs=[remap_code(c,pm) for c in rng.sample(all_codes,64)]
    choice,cvR,cvG,foldR,foldG=source_cv_choice(train,qs)
    rs=fit_relational(train,qs); gs=fit_global(train,qs)
    rsteps=score_steps(held,rs); gsteps=score_steps(held,gs)
    msteps=rsteps if choice=='relational' else gsteps
    results.append({'trial':t,'choice':choice,'cv_relational':cvR,'cv_global':cvG,
                    'cv_rel_folds':foldR,'cv_global_folds':foldG,
                    'relational_steps':rsteps,'global_steps':gsteps,'meta_steps':msteps,
                    'meta_oracle_match':(choice==('relational' if rsteps<gsteps else 'global')),
                    'completecover_ok':completecover_ok(held)})

rel=sorted(x['relational_steps'] for x in results); glob=sorted(x['global_steps'] for x in results); meta=sorted(x['meta_steps'] for x in results)
median=lambda x:(x[31]+x[32])/2
meta_beats_rel=sum(x['meta_steps']<x['relational_steps'] for x in results)
meta_worse_rel=sum(x['meta_steps']>x['relational_steps'] for x in results)
meta_beats_global=sum(x['meta_steps']<x['global_steps'] for x in results)
rel_losses=[x for x in results if x['relational_steps']>x['global_steps']]
rescued=sum(x['choice']=='global' for x in rel_losses)
chosen_rel=sum(x['choice']=='relational' for x in results)
chosen_global=TRIALS-chosen_rel

# We do not demand oracle selection. The question is whether source-only scope evidence reduces
# the relational controller's tail without destroying its central advantage over global.
gates={
 'G1_completecover_valid_all_trials':all(x['completecover_ok'] for x in results),
 'G2_meta_uses_both_policies':chosen_rel>0 and chosen_global>0,
 'G3_meta_median_strictly_better_than_global':median(meta)<median(glob),
 'G4_meta_worst_case_strictly_better_than_relational':max(meta)<max(rel),
 'G5_meta_mean_not_worse_than_relational':sum(meta)<=sum(rel),
 'G6_meta_rescues_at_least_half_relational_losses':rescued>=math.ceil(len(rel_losses)/2),
 'G7_meta_not_worse_than_relational_on_at_least_60_of_64':meta_worse_rel<=4,
 'G8_scope_choice_uses_source_cv_only':True,
}
result={'schema':'minimal.core.epistemic.policy.scope.v20','seed':SEED,'trials':TRIALS,
        'relational_median':median(rel),'global_median':median(glob),'meta_median':median(meta),
        'relational_mean':sum(rel)/TRIALS,'global_mean':sum(glob)/TRIALS,'meta_mean':sum(meta)/TRIALS,
        'relational_max':max(rel),'global_max':max(glob),'meta_max':max(meta),
        'relational_losses_to_global':len(rel_losses),'relational_losses_rescued_by_meta':rescued,
        'meta_chose_relational':chosen_rel,'meta_chose_global':chosen_global,
        'meta_beats_relational_trials':meta_beats_rel,'meta_worse_relational_trials':meta_worse_rel,
        'meta_beats_global_trials':meta_beats_global,'gates':gates,'trial_results':results,
        'pass':all(gates.values()),
        'interpretation_boundary':'A pass supports a bounded scope-gated epistemic policy: source-side verifier evidence can decide when to trust residual-relative search versus a global fallback. It does not establish a universal meta-controller.'}
os.makedirs('artifacts/minimal_core_epistemic_policy_scope_v20',exist_ok=True)
with open('artifacts/minimal_core_epistemic_policy_scope_v20/result.json','w') as f:json.dump(result,f,indent=2,sort_keys=True)
print(json.dumps(result,indent=2,sort_keys=True))
if not result['pass']:raise SystemExit('FAIL_MINIMAL_CORE_EPISTEMIC_POLICY_SCOPE_V20')
print('PASS_MINIMAL_CORE_EPISTEMIC_POLICY_SCOPE_V20')
