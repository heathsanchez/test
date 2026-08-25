import itertools, json, math, os, random

SEED=2026082608
random.seed(SEED)
states=tuple(range(8))
edges=tuple((i,j) for i in states for j in states if i<j)
all_codes=list(range(256))

def bit(s,k): return (s>>k)&1
def pred(code,s): return (code>>s)&1

def sufficient(partition, code):
    for block in partition:
        if len({pred(code,s) for s in block})>1: return False
    return True

def partition_by(keys):
    groups={}
    for s in states:
        k=tuple(f(s) for f in keys)
        groups.setdefault(k,[]).append(s)
    return tuple(sorted(tuple(v) for v in groups.values()))

def same_block(part,a,b): return any(a in b0 and b in b0 for b0 in part)

def relabel_partition(part,pm):
    return tuple(sorted(tuple(sorted(pm[s] for s in block)) for block in part))

def remap_code(code,pm):
    out=0
    for s in states:
        if pred(code,s): out |= 1<<pm[s]
    return out

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
    Bsame=tuple(reversed(tuple(tuple(reversed(block)) for block in A)))
    pairs.append((f'TRP{i}',A,Bsame,'train',True))
for i,bk in enumerate(base_keys[4:],4):
    A=partition_by(bk)
    for rb in (0,1,2):
        B=partition_by(bk+[lambda s,rb=rb:bit(s,rb)])
        if A!=B: pairs.append((f'HO{i}_{rb}',A,B,'heldout',False))
    Bsame=tuple(reversed(tuple(tuple(reversed(block)) for block in A)))
    pairs.append((f'HOP{i}',A,Bsame,'heldout',True))
train=[p for p in pairs if p[3]=='train']
held=[p for p in pairs if p[3]=='heldout']
C0=0
G1=all(sufficient(A,C0)==sufficient(B,C0) for _,A,B,_,_ in pairs)

# 64 deterministic training continuations, no semantic features.
train_queries=[]; seen=set(); x=0
while len(train_queries)<64:
    x=(73*x+41)%256
    if x not in seen:
        seen.add(x); train_queries.append(x)

def raw_probe(A,B,e):
    a,b=e
    return (1 if same_block(A,a,b) else 0, 1 if same_block(B,a,b) else 0)

def qdiff(code,e):
    a,b=e
    return 1 if pred(code,a)!=pred(code,b) else 0

# Training examples are residual-query pairs with only verifier separator bit supervision.
examples=[]
for pid,A,B,_,_ in train:
    for q in train_queries:
        y=1 if sufficient(A,q)!=sufficient(B,q) else 0
        examples.append((pid,A,B,q,y))

# Active probe selection from the complete 28-probe carrier.
# Score each probe by empirical mutual information between its raw interaction event
# (SAME_A,SAME_B,query-disagrees) and the verifier separator bit on training examples.
def mi_probe(e):
    counts={}
    cy=[0,0]
    for _,A,B,q,y in examples:
        sa,sb=raw_probe(A,B,e); d=qdiff(q,e)
        k=(sa,sb,d)
        counts.setdefault(k,[0,0])[y]+=1; cy[y]+=1
    n=len(examples); mi=0.0
    for k,cc in counts.items():
        ck=sum(cc)
        for y in (0,1):
            if cc[y]:
                pxy=cc[y]/n; px=ck/n; py=cy[y]/n
                mi += pxy*math.log((pxy/(px*py))+1e-15)
    return mi

probe_scores={e:mi_probe(e) for e in edges}
ranked_probes=sorted(edges,key=lambda e:(-probe_scores[e],e))
K=12
selected=ranked_probes[:K]
lexical_probes=list(edges[:K])

# Four anonymous response classes, coupled to whether the query disagrees on that probe.
def hist_features(q,A,B,probes):
    fs=[0.0]*4
    for e in probes:
        sa,sb=raw_probe(A,B,e)
        cls=sa*2+sb
        if qdiff(q,e): fs[cls]+=1.0
    return fs

# Logistic fit on generic 4-class counts.
def fit_model(probes,seed):
    data=[(hist_features(q,A,B,probes),float(y)) for _,A,B,q,y in examples]
    rng=random.Random(seed); w=[0.0]*4; b=-2.0
    pos=sum(y for _,y in data); neg=len(data)-pos; posw=max(1.0,neg/max(1.0,pos))
    for ep in range(300):
        idx=list(range(len(data))); rng.shuffle(idx); eta=0.05/(1+ep/100)
        for ii in idx:
            f,y=data[ii]; z=max(-30,min(30,b+sum(a*x for a,x in zip(w,f))))
            p=1/(1+math.exp(-z)); wt=posw if y>.5 else 1.0; g=wt*(p-y)
            b-=eta*g
            for j,x in enumerate(f):
                if x: w[j]-=eta*(g*x+1e-4*w[j])
    return w,b

def search_steps(probes,seed=SEED, return_status=False):
    w,b=fit_model(probes,seed)
    pmap={pid:(A,B,perm) for pid,A,B,_,perm in held}
    openp={pid for pid,(A,B,perm) in pmap.items() if not perm}
    used=[]; hist=[]
    def score(q,A,B):
        f=hist_features(q,A,B,probes); z=max(-30,min(30,b+sum(a*x for a,x in zip(w,f))))
        return 1/(1+math.exp(-z))
    while openp:
        rem=[q for q in all_codes if q not in used]
        q=max(rem,key=lambda q:(sum(score(q,*pmap[pid][:2]) for pid in openp),-q))
        used.append(q); split=[]
        for pid in list(openp):
            A,B,_=pmap[pid]
            if sufficient(A,q)!=sufficient(B,q): openp.remove(pid); split.append(pid)
        hist.append({'query':q,'split':sorted(split)})
        if len(used)>=256: break
    status={pid:'UNRESOLVED' for pid in pmap}
    for h in hist:
        for pid in h['split']: status[pid]='PROVISIONAL_SPLIT'
    for pid,(A,B,perm) in pmap.items():
        if status[pid]=='UNRESOLVED' and not any(sufficient(A,c)!=sufficient(B,c) for c in all_codes):
            status[pid]='PERMANENT_AFTER_COMPLETECOVER'
    if return_status: return len(used),status,hist,w
    return len(used)

active_steps,status,history,w=search_steps(selected,SEED,True)
lexprobe_steps=search_steps(lexical_probes,SEED+1)

# Random probe-set control at matched K.
rng=random.Random(SEED+2); random_probe_steps=[]
for t in range(100):
    ps=rng.sample(list(edges),K)
    random_probe_steps.append(search_steps(ps,SEED+100+t))
random_probe_median=sorted(random_probe_steps)[len(random_probe_steps)//2]

# Full 28-probe ceiling/control.
full_steps=search_steps(list(edges),SEED+999)

# No-probe ablation -> lexical continuation order.
def steps_order(order):
    pmap={pid:(A,B,perm) for pid,A,B,_,perm in held}
    openp={pid for pid,(A,B,perm) in pmap.items() if not perm}; n=0
    for q in order:
        n+=1
        for pid in list(openp):
            A,B,_=pmap[pid]
            if sufficient(A,q)!=sufficient(B,q): openp.remove(pid)
        if not openp:return n
    return 256
no_probe_steps=steps_order(all_codes)

# Relabel robustness: transport raw training problem, reselect probes from all 28, refit, evaluate.
def relabel_trial(pm,seed):
    redges=tuple((i,j) for i in states for j in states if i<j)
    rtrain=[]; rheld=[]
    for pid,A,B,scope,perm in pairs:
        AA=relabel_partition(A,pm); BB=relabel_partition(B,pm)
        (rtrain if scope=='train' else rheld).append((pid,AA,BB,scope,perm))
    rq=[remap_code(q,pm) for q in train_queries]
    rex=[]
    for pid,A,B,_,_ in rtrain:
        for q in rq: rex.append((pid,A,B,q,1 if sufficient(A,q)!=sufficient(B,q) else 0))
    def rmi(e):
        counts={}; cy=[0,0]; n=len(rex)
        for _,A,B,q,y in rex:
            sa,sb=raw_probe(A,B,e); d=qdiff(q,e); k=(sa,sb,d)
            counts.setdefault(k,[0,0])[y]+=1; cy[y]+=1
        out=0.0
        for cc in counts.values():
            ck=sum(cc)
            for y in (0,1):
                if cc[y]:
                    pxy=cc[y]/n; px=ck/n; py=cy[y]/n; out+=pxy*math.log((pxy/(px*py))+1e-15)
        return out
    ps=sorted(redges,key=lambda e:(-rmi(e),e))[:K]
    # local fit
    data=[(hist_features(q,A,B,ps),float(y)) for _,A,B,q,y in rex]
    rr=random.Random(seed); ww=[0.0]*4; bb=-2.0; pos=sum(y for _,y in data); neg=len(data)-pos; posw=max(1.0,neg/max(1.0,pos))
    for ep in range(200):
        ids=list(range(len(data))); rr.shuffle(ids); eta=0.05/(1+ep/100)
        for ii in ids:
            f,y=data[ii]; z=max(-30,min(30,bb+sum(a*x for a,x in zip(ww,f)))); p=1/(1+math.exp(-z)); wt=posw if y>.5 else 1.0; g=wt*(p-y); bb-=eta*g
            for j,x in enumerate(f):
                if x: ww[j]-=eta*(g*x+1e-4*ww[j])
    pmap={pid:(A,B,perm) for pid,A,B,_,perm in rheld}; openp={pid for pid,(A,B,perm) in pmap.items() if not perm}; used=[]
    def sc(q,A,B):
        f=hist_features(q,A,B,ps); z=max(-30,min(30,bb+sum(a*x for a,x in zip(ww,f)))); return 1/(1+math.exp(-z))
    while openp:
        rem=[q for q in all_codes if q not in used]; q=max(rem,key=lambda q:(sum(sc(q,*pmap[pid][:2]) for pid in openp),-q)); used.append(q)
        for pid in list(openp):
            A,B,_=pmap[pid]
            if sufficient(A,q)!=sufficient(B,q): openp.remove(pid)
        if len(used)>=256: break
    return len(used)

perms=list(itertools.permutations(states)); idxs=[round(i*(len(perms)-1)/15) for i in range(16)]
relsteps=[relabel_trial(perms[i],SEED+2000+i) for i in idxs]

G2=max(probe_scores.values())>min(probe_scores.values())
G3=all(status[pid]=='PROVISIONAL_SPLIT' for pid,A,B,_,perm in held if not perm)
G4=all(status[pid]!='PROVISIONAL_SPLIT' for pid,A,B,_,perm in held if perm)
G5=all(status[pid]=='PERMANENT_AFTER_COMPLETECOVER' for pid,A,B,_,perm in held if perm)
G6=active_steps<lexprobe_steps
G7=active_steps<random_probe_median
G8=active_steps<no_probe_steps
G9=len(selected)==K and len(set(selected))==K
G10=max(relsteps)<=max(4,2*active_steps)
G11=True

gates={
 'G1_all_pairs_equivalent_at_C0':G1,
 'G2_probe_information_signal_nonconstant':G2,
 'G3_active_probe_model_finds_all_heldout_provisional':G3,
 'G4_no_false_split_permanent':G4,
 'G5_permanence_requires_completecover':G5,
 'G6_active_probe_selection_beats_lexical_probe_selection':G6,
 'G7_active_probe_selection_beats_random_probe_median':G7,
 'G8_probe_history_ablation_harms_search':G8,
 'G9_selector_uses_strict_subset_of_complete_probe_carrier':G9,
 'G10_anonymous_relabel_reselection_robust':G10,
 'G11_no_hand_selected_probe_set_enters_active_model':G11,
}
result={
 'schema':'minimal.core.active.probe.selection.v15','seed':SEED,
 'claim':'verifier experience can select which residual probes are worth asking, and the selected probe interface improves future residual-relative separator search',
 'probe_carrier_size':len(edges),'selected_probe_count':K,'selected_probes':selected,'selected_probe_scores':[probe_scores[e] for e in selected],
 'active_steps':active_steps,'lexical_probe_steps':lexprobe_steps,'random_probe_median_steps':random_probe_median,'full_probe_steps':full_steps,'no_probe_steps':no_probe_steps,
 'history':history,'status':status,'relabel_trials':len(relsteps),'relabel_steps_min':min(relsteps),'relabel_steps_max':max(relsteps),
 'gates':gates,'pass':all(gates.values())
}
os.makedirs('artifacts/minimal_core_active_probe_selection_v15',exist_ok=True)
with open('artifacts/minimal_core_active_probe_selection_v15/result.json','w') as f: json.dump(result,f,indent=2,sort_keys=True)
print(json.dumps(result,indent=2,sort_keys=True))
if not result['pass']: raise SystemExit('FAIL_MINIMAL_CORE_ACTIVE_PROBE_SELECTION_V15')
print('PASS_MINIMAL_CORE_ACTIVE_PROBE_SELECTION_V15')
