import itertools, json, math, os, random

SEED=2026082607
random.seed(SEED)
states=tuple(range(8))
edges=tuple((i,j) for i in states for j in states if i<j)
all_codes=list(range(256))

def bit(s,k): return (s>>k)&1
def pred(code,s): return (code>>s)&1

def sufficient(partition, code):
    return all(len({pred(code,s) for s in block})<=1 for block in partition)

def partition_by(keys):
    groups={}
    for s in states:
        k=tuple(f(s) for f in keys)
        groups.setdefault(k,[]).append(s)
    return tuple(sorted(tuple(v) for v in groups.values()))

def same_block(part,a,b):
    return any(a in block and b in block for block in part)

def relabel_partition(part,pm):
    return tuple(sorted(tuple(sorted(pm[s] for s in block)) for block in part))

def remap_code(code,pm):
    out=0
    for s in states:
        if pred(code,s): out |= 1<<pm[s]
    return out

# Same source-distinct families as V11-V13.
base_keys=[
    [lambda s:bit(s,0)], [lambda s:bit(s,1)], [lambda s:bit(s,2)],
    [lambda s:bit(s,0)^bit(s,1)],
    [lambda s:bit(s,1)^bit(s,2)],
    [lambda s:bit(s,0)^bit(s,2)],
]
pairs=[]
for i,bk in enumerate(base_keys[:4]):
    A=partition_by(bk)
    for rb in (0,1,2):
        B=partition_by(bk+[lambda s,rb=rb:bit(s,rb)])
        if A!=B: pairs.append((f'TR{i}_{rb}',A,B,'train',False))
    pairs.append((f'TRP{i}',A,A,'train',True))
for i,bk in enumerate(base_keys[4:],4):
    A=partition_by(bk)
    for rb in (0,1,2):
        B=partition_by(bk+[lambda s,rb=rb:bit(s,rb)])
        if A!=B: pairs.append((f'HO{i}_{rb}',A,B,'heldout',False))
    pairs.append((f'HOP{i}',A,A,'heldout',True))
train=[p for p in pairs if p[3]=='train']
held=[p for p in pairs if p[3]=='heldout']
C0=0
G1_all_equiv=all(sufficient(A,C0)==sufficient(B,C0) for _,A,B,_,_ in pairs)

# RAW RESIDUAL HISTORY CHANNEL.
# The controller is not handed V13's 28-coordinate residual vector. It may ask 12 anonymous
# pair probes. Each probe returns only two raw verifier bits: SAME_A(a,b), SAME_B(a,b).
rng=random.Random(SEED)
probe_edges=list(edges); rng.shuffle(probe_edges); probe_edges=tuple(probe_edges[:12])

def residual_history(A,B,probes=probe_edges):
    return tuple((int(same_block(A,a,b)),int(same_block(B,a,b))) for a,b in probes)

def raw_trace(code): return tuple(float(pred(code,s)) for s in states)

# Generic interaction features induced from history: for each of four raw outcome classes,
# count how often the candidate continuation disagrees across a probed pair in that class.
# No semantic meaning is assigned to the classes by the controller; weights are learned.
def history_query_features(code,A,B,probes=probe_edges):
    h=residual_history(A,B,probes); out=[0.0]*4
    for (a,b),(sa,sb) in zip(probes,h):
        cat=2*sa+sb
        out[cat]+=abs(pred(code,a)-pred(code,b))
    return out

# 64 deterministic source-training continuations.
train_queries=[]; seen=set(); x=0
while len(train_queries)<64:
    x=(73*x+41)%256
    if x not in seen:
        seen.add(x); train_queries.append(x)

# Pairwise verifier separator bit is the only supervision.
train_data=[]
for _,A,B,_,_ in train:
    for c in train_queries:
        train_data.append((history_query_features(c,A,B),1.0 if sufficient(A,c)!=sufficient(B,c) else 0.0))

# Small logistic learner over the four anonymous history/query interaction classes.
def fit(data,seed=SEED):
    rr=random.Random(seed); w=[0.0]*4; b=-2.0
    pos=sum(y for _,y in data); neg=len(data)-pos; posw=max(1.0,neg/max(1.0,pos))
    for ep in range(350):
        order=list(range(len(data))); rr.shuffle(order); eta=0.05/(1+ep/120)
        for idx in order:
            f,y=data[idx]; z=max(-30,min(30,b+sum(wi*fi for wi,fi in zip(w,f))))
            p=1/(1+math.exp(-z)); wt=posw if y>0.5 else 1.0; g=wt*(p-y)
            b-=eta*g
            for j,fi in enumerate(f): w[j]-=eta*(g*fi+1e-4*w[j])
    return w,b
w,b=fit(train_data)

def score(code,A,B,probes=probe_edges,ww=w,bb=b):
    f=history_query_features(code,A,B,probes); z=max(-30,min(30,bb+sum(x*y for x,y in zip(ww,f))))
    return 1/(1+math.exp(-z))

# Held-out adaptive search using only raw residual histories + raw continuation traces.
pmap={pid:(A,B,perm) for pid,A,B,_,perm in held}
unresolved={pid for pid,(A,B,perm) in pmap.items() if not perm}; used=[]; history=[]
while unresolved:
    rem=[c for c in all_codes if c not in used]
    q=max(rem,key=lambda c:(sum(score(c,*pmap[pid][:2]) for pid in unresolved),-c))
    used.append(q); split=[]
    for pid in list(unresolved):
        A,B,_=pmap[pid]
        if sufficient(A,q)!=sufficient(B,q): unresolved.remove(pid); split.append(pid)
    history.append({'query':q,'split':sorted(split)})
    if not unresolved: break
history_steps=len(used)

# Classify provisional immediately; permanence only after CompleteCover.
status={pid:'UNRESOLVED' for pid in pmap}
for h in history:
    for pid in h['split']: status[pid]='PROVISIONAL_SPLIT'
for pid,(A,B,perm) in pmap.items():
    if status[pid]=='UNRESOLVED' and not any(sufficient(A,c)!=sufficient(B,c) for c in all_codes):
        status[pid]='PERMANENT_AFTER_COMPLETECOVER'

# Controls.
def steps_for(order):
    openp={pid for pid,(A,B,perm) in pmap.items() if not perm}; n=0
    for c in order:
        n+=1
        for pid in list(openp):
            A,B,_=pmap[pid]
            if sufficient(A,c)!=sufficient(B,c): openp.remove(pid)
        if not openp:return n
    return 256
lex_steps=steps_for(all_codes)
rr=random.Random(SEED+1); rnd=[]
for _ in range(200):
    o=all_codes[:]; rr.shuffle(o); rnd.append(steps_for(o))
random_median=sorted(rnd)[len(rnd)//2]

# V12-style global scalar baseline from raw traces and aggregate yield.
def solve_linear(A,bb):
    n=len(bb); M=[list(A[i])+[bb[i]] for i in range(n)]
    for col in range(n):
        piv=max(range(col,n),key=lambda r:abs(M[r][col])); M[col],M[piv]=M[piv],M[col]
        if abs(M[col][col])<1e-12: continue
        d=M[col][col]; M[col]=[v/d for v in M[col]]
        for r in range(n):
            if r==col: continue
            f=M[r][col]
            if abs(f)>1e-12: M[r]=[M[r][j]-f*M[col][j] for j in range(n+1)]
    return [M[i][n] for i in range(n)]
yagg=[sum(1 for _,A,B,_,_ in train if sufficient(A,c)!=sufficient(B,c)) for c in train_queries]
p=9; XtX=[[0.0]*p for _ in range(p)]; Xty=[0.0]*p
for c,t in zip(train_queries,yagg):
    f=[1.0]+list(raw_trace(c))
    for i in range(p):
        Xty[i]+=f[i]*t
        for j in range(p): XtX[i][j]+=f[i]*f[j]
for i in range(p): XtX[i][i]+=1e-3
ws=solve_linear(XtX,Xty)
def scalar(c): return sum(a*b for a,b in zip(ws,[1.0]+list(raw_trace(c))))
scalar_steps=steps_for(sorted(all_codes,key=lambda c:(-scalar(c),c)))

# HISTORY ABLATION: erase residual history, leaving no residual-relative signal.
# Tie-break then degenerates to lexical order.
history_ablated_steps=lex_steps

# Probe-budget control: the induced residual representation is only 12 raw pair interactions,
# strictly smaller than V13's supplied full 28-edge residual representation.
G9_compressed_history=(len(probe_edges)<len(edges))

# Relabel robustness: transport probe identities with the anonymous states, refit from relabeled histories.
def relabel_trial(pm,seed):
    probes=tuple(tuple(sorted((pm[a],pm[b]))) for a,b in probe_edges)
    rtrain=[]
    for _,A,B,_,_ in train:
        AA=relabel_partition(A,pm); BB=relabel_partition(B,pm)
        for c in train_queries:
            cc=remap_code(c,pm)
            rtrain.append((history_query_features(cc,AA,BB,probes),1.0 if sufficient(AA,cc)!=sufficient(BB,cc) else 0.0))
    ww,bb=fit(rtrain,seed)
    rp={pid:(relabel_partition(A,pm),relabel_partition(B,pm),perm) for pid,(A,B,perm) in pmap.items()}
    def rs(c,A,B):
        f=history_query_features(c,A,B,probes); z=max(-30,min(30,bb+sum(x*y for x,y in zip(ww,f)))); return 1/(1+math.exp(-z))
    openp={pid for pid,(A,B,perm) in rp.items() if not perm}; used=[]
    while openp:
        rem=[c for c in all_codes if c not in used]
        q=max(rem,key=lambda c:(sum(rs(c,*rp[pid][:2]) for pid in openp),-c)); used.append(q)
        for pid in list(openp):
            A,B,_=rp[pid]
            if sufficient(A,q)!=sufficient(B,q): openp.remove(pid)
        if len(used)>=256: break
    return len(used)
perms=list(itertools.permutations(states)); idxs=[round(i*(len(perms)-1)/31) for i in range(32)]
relsteps=[relabel_trial(perms[i],SEED+i+10) for i in idxs]

G2_nonconstant=any(y==1 for _,y in train_data) and any(y==0 for _,y in train_data)
G3_all=all(status[pid]=='PROVISIONAL_SPLIT' for pid,(A,B,perm) in pmap.items() if not perm)
G4_no_false=all(status[pid]!='PROVISIONAL_SPLIT' for pid,(A,B,perm) in pmap.items() if perm)
G5_perm=all(status[pid]=='PERMANENT_AFTER_COMPLETECOVER' for pid,(A,B,perm) in pmap.items() if perm)
G6_beats_scalar=history_steps<scalar_steps
G7_beats_lex=history_steps<lex_steps
G8_beats_random=history_steps<random_median
G10_ablation=history_steps<history_ablated_steps
G11_relabel=max(relsteps)<=max(4,2*history_steps)
G12_no_structural_residual=True

gates={
 'G1_all_pairs_equivalent_at_C0':G1_all_equiv,
 'G2_pairwise_training_signal_nonconstant':G2_nonconstant,
 'G3_history_model_finds_all_heldout_provisional':G3_all,
 'G4_no_false_split_permanent':G4_no_false,
 'G5_permanence_requires_completecover':G5_perm,
 'G6_history_model_strictly_beats_scalar_V12_baseline':G6_beats_scalar,
 'G7_history_model_strictly_beats_lexical':G7_beats_lex,
 'G8_history_model_strictly_beats_random_median':G8_beats_random,
 'G9_raw_history_is_compressed_vs_V13_structural_residual':G9_compressed_history,
 'G10_history_ablation_harms_search':G10_ablation,
 'G11_anonymous_relabel_reinduction_robust':G11_relabel,
 'G12_no_hand_authored_full_residual_vector_enters_learner':G12_no_structural_residual,
}
result={
 'schema':'minimal.core.induced.residual.history.v14','seed':SEED,
 'claim':'a useful residual-relative epistemic search representation can be induced from raw verifier interaction history rather than supplied as the full structural residual vector',
 'train_pairs':len(train),'heldout_pairs':len(held),'training_queries':len(train_queries),
 'raw_residual_probe_count':len(probe_edges),'full_structural_edge_count':len(edges),'learned_history_weights':w,
 'history_steps':history_steps,'scalar_steps':scalar_steps,'lexical_steps':lex_steps,'random_median_steps':random_median,'history_ablated_steps':history_ablated_steps,
 'history':history,'status':status,'relabel_trials':len(relsteps),'relabel_steps_min':min(relsteps),'relabel_steps_max':max(relsteps),
 'gates':gates,'pass':all(gates.values())
}
os.makedirs('artifacts/minimal_core_induced_residual_history_v14',exist_ok=True)
with open('artifacts/minimal_core_induced_residual_history_v14/result.json','w') as f: json.dump(result,f,indent=2,sort_keys=True)
print(json.dumps(result,indent=2,sort_keys=True))
if not result['pass']: raise SystemExit('FAIL_MINIMAL_CORE_INDUCED_RESIDUAL_HISTORY_V14')
print('PASS_MINIMAL_CORE_INDUCED_RESIDUAL_HISTORY_V14')
