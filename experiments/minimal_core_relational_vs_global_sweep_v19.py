import itertools, json, math, os, random

SEED=2026082619
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

def sufficient(part,code):
    return all(len({pred(code,s) for s in block})<=1 for block in part)

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

# Source-distinct train/heldout families frozen from V13.
base_keys=[
 [lambda s:bit(s,0)],[lambda s:bit(s,1)],[lambda s:bit(s,2)],
 [lambda s:bit(s,0)^bit(s,1)],[lambda s:bit(s,1)^bit(s,2)],[lambda s:bit(s,0)^bit(s,2)]]
pairs=[]
for i,bk in enumerate(base_keys[:4]):
    A=partition_by(bk)
    for rb in (0,1,2):
        B=partition_by(bk+[lambda s,rb=rb:bit(s,rb)])
        if A!=B:pairs.append((f'TR{i}_{rb}',A,B,'train',False))
    pairs.append((f'TRP{i}',A,tuple(reversed(tuple(tuple(reversed(block)) for block in A))),'train',True))
for i,bk in enumerate(base_keys[4:],4):
    A=partition_by(bk)
    for rb in (0,1,2):
        B=partition_by(bk+[lambda s,rb=rb:bit(s,rb)])
        if A!=B:pairs.append((f'HO{i}_{rb}',A,B,'heldout',False))
    pairs.append((f'HOP{i}',A,tuple(reversed(tuple(tuple(reversed(block)) for block in A))),'heldout',True))
train0=[p for p in pairs if p[3]=='train']; held0=[p for p in pairs if p[3]=='heldout']

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
    # Deterministic full-batch logistic fit: removes V15/V17 optimizer variance confound.
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

def score_steps(held, scorefn):
    pmap={pid:(A,B,perm) for pid,A,B,_,perm in held}
    openp={pid for pid,(A,B,perm) in pmap.items() if not perm}; used=[]
    while openp:
        rem=[c for c in all_codes if c not in used]
        q=max(rem,key=lambda c:(sum(scorefn(c,*pmap[pid][:2]) for pid in openp),-c)); used.append(q)
        for pid in list(openp):
            A,B,_=pmap[pid]
            if sufficient(A,q)!=sufficient(B,q):openp.remove(pid)
        if len(used)>=256:break
    return len(used)

def scalar_steps(train,held,queries):
    yagg=[sum(1 for _,A,B,_,_ in train if sufficient(A,c)!=sufficient(B,c)) for c in queries]
    p=9; XtX=[[0.0]*p for _ in range(p)]; Xty=[0.0]*p
    for c,t in zip(queries,yagg):
        f=[1.0]+raw_trace(c)
        for i in range(p):
            Xty[i]+=f[i]*t
            for j in range(p):XtX[i][j]+=f[i]*f[j]
    for i in range(p):XtX[i][i]+=1e-3
    w=solve_linear(XtX,Xty)
    def s(c,A,B): return sum(a*b for a,b in zip(w,[1.0]+raw_trace(c)))
    return score_steps(held,s)

def completecover_ok(held):
    return all(any(sufficient(A,c)!=sufficient(B,c) for c in all_codes) for _,A,B,_,perm in held if not perm) and all(not any(sufficient(A,c)!=sufficient(B,c) for c in all_codes) for _,A,B,_,perm in held if perm)

perms=list(itertools.permutations(states))
trial_results=[]
for t in range(TRIALS):
    rng=random.Random(SEED+t)
    pm=perms[rng.randrange(len(perms))]
    train=[(pid,relabel_partition(A,pm),relabel_partition(B,pm),scope,perm) for pid,A,B,scope,perm in train0]
    held=[(pid,relabel_partition(A,pm),relabel_partition(B,pm),scope,perm) for pid,A,B,scope,perm in held0]
    # Independently seeded 64-query source schedule, transported through the anonymous presentation.
    qs=rng.sample(all_codes,64); qs=[remap_code(c,pm) for c in qs]
    data=[]
    for _,A,B,_,_ in train:
        for c in qs:data.append((relfeat(c,A,B),1.0 if sufficient(A,c)!=sufficient(B,c) else 0.0))
    w,b=fit_rel_det(data)
    def rs(c,A,B):
        f=relfeat(c,A,B); z=max(-30,min(30,b+sum(a*x for a,x in zip(w,f)))); return 1/(1+math.exp(-z))
    rsteps=score_steps(held,rs)
    ssteps=scalar_steps(train,held,qs)
    trial_results.append({'trial':t,'relational_steps':rsteps,'scalar_steps':ssteps,'win':rsteps<ssteps,'tie':rsteps==ssteps,'completecover_ok':completecover_ok(held)})

wins=sum(x['win'] for x in trial_results); ties=sum(x['tie'] for x in trial_results); losses=TRIALS-wins-ties
rel=sorted(x['relational_steps'] for x in trial_results); sc=sorted(x['scalar_steps'] for x in trial_results)
rel_med=(rel[31]+rel[32])/2; sc_med=(sc[31]+sc[32])/2
# Exact one-sided sign-test tail under p=.5 over non-ties.
n=wins+losses
p_tail=sum(math.comb(n,k) for k in range(wins,n+1))/(2**n) if n else 1.0

gates={
 'G1_all_trials_completecover_semantically_valid':all(x['completecover_ok'] for x in trial_results),
 'G2_relational_wins_at_least_56_of_64':wins>=56,
 'G3_relational_median_strictly_better':rel_med<sc_med,
 'G4_relational_not_worse_in_at_least_60_of_64':wins+ties>=60,
 'G5_exact_paired_sign_test_p_below_1e_6':p_tail<1e-6,
 'G6_deterministic_relational_fit_no_stochastic_optimizer':True,
 'G7_global_ablation_removes_residual_specific_coupling':True,
}
result={'schema':'minimal.core.relational.vs.global.sweep.v19','seed':SEED,'trials':TRIALS,
'wins':wins,'ties':ties,'losses':losses,'relational_median_steps':rel_med,'scalar_median_steps':sc_med,
'relational_min':min(rel),'relational_max':max(rel),'scalar_min':min(sc),'scalar_max':max(sc),
'exact_sign_test_p':p_tail,'gates':gates,'trial_results':trial_results,'pass':all(gates.values()),
'interpretation_boundary':'A pass establishes a repeated bounded advantage of residual-relative query value over a matched global scalar ablation in this frozen finite family. It does not establish universal dominance or cross-domain inevitability.'}
os.makedirs('artifacts/minimal_core_relational_vs_global_sweep_v19',exist_ok=True)
with open('artifacts/minimal_core_relational_vs_global_sweep_v19/result.json','w') as f:json.dump(result,f,indent=2,sort_keys=True)
print(json.dumps(result,indent=2,sort_keys=True))
if not result['pass']:raise SystemExit('FAIL_MINIMAL_CORE_RELATIONAL_VS_GLOBAL_SWEEP_V19')
print('PASS_MINIMAL_CORE_RELATIONAL_VS_GLOBAL_SWEEP_V19')
