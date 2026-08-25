import itertools, json, math, os

SEED=2026082609
states=tuple(range(8))
edges=tuple((i,j) for i in states for j in states if i<j)
all_codes=list(range(256))
K=12

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

def same_block(part,a,b): return any(a in block and b in block for block in part)

def relabel_partition(part,pm):
    return tuple(sorted(tuple(sorted(pm[s] for s in block)) for block in part))

def remap_code(code,pm):
    out=0
    for s in states:
        if pred(code,s): out |= 1<<pm[s]
    return out

def remap_edge(e,pm):
    a,b=pm[e[0]],pm[e[1]]
    return (a,b) if a<b else (b,a)

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

train_queries=[]; seen=set(); x=0
while len(train_queries)<64:
    x=(73*x+41)%256
    if x not in seen:
        seen.add(x); train_queries.append(x)

def raw_probe(A,B,e):
    a,b=e
    return (1 if same_block(A,a,b) else 0,1 if same_block(B,a,b) else 0)

def qdiff(code,e):
    a,b=e
    return 1 if pred(code,a)!=pred(code,b) else 0

def make_examples(tpairs,queries):
    out=[]
    for pid,A,B,_,_ in tpairs:
        for q in queries:
            out.append((pid,A,B,q,1 if sufficient(A,q)!=sufficient(B,q) else 0))
    return out

def mi_probe(e,examples):
    counts={}; cy=[0,0]; n=len(examples)
    for _,A,B,q,y in examples:
        sa,sb=raw_probe(A,B,e); d=qdiff(q,e); k=(sa,sb,d)
        counts.setdefault(k,[0,0])[y]+=1; cy[y]+=1
    mi=0.0
    for cc in counts.values():
        ck=sum(cc)
        for y in (0,1):
            if cc[y]:
                pxy=cc[y]/n; px=ck/n; py=cy[y]/n
                mi += pxy*math.log((pxy/(px*py))+1e-15)
    return mi

def select_probes(examples):
    scores={e:mi_probe(e,examples) for e in edges}
    return tuple(sorted(edges,key=lambda e:(-scores[e],e))[:K]),scores

def hist_features(q,A,B,probes):
    fs=[0.0]*4
    for e in probes:
        sa,sb=raw_probe(A,B,e); cls=sa*2+sb
        if qdiff(q,e): fs[cls]+=1.0
    return fs

# Deterministic full-batch logistic gradient descent, used only to isolate equivariance.
def fit_model(probes,examples):
    data=[(hist_features(q,A,B,probes),float(y)) for _,A,B,q,y in examples]
    w=[0.0]*4; b=-2.0
    pos=sum(y for _,y in data); neg=len(data)-pos; posw=max(1.0,neg/max(1.0,pos))
    for ep in range(600):
        eta=0.08/(1.0+ep/150.0); gb=0.0; gw=[0.0]*4
        for f,y in data:
            z=max(-30,min(30,b+sum(a*x for a,x in zip(w,f))))
            p=1/(1+math.exp(-z)); wt=posw if y>.5 else 1.0; g=wt*(p-y)
            gb+=g
            for j,x in enumerate(f): gw[j]+=g*x
        n=len(data); b-=eta*gb/n
        for j in range(4): w[j]-=eta*(gw[j]/n+1e-4*w[j])
    return tuple(w),b

def score(q,A,B,probes,w,b):
    f=hist_features(q,A,B,probes); z=max(-30,min(30,b+sum(a*x for a,x in zip(w,f))))
    return 1/(1+math.exp(-z))

def max_score_transport_error(orig_probes,orig_w,orig_b,rprobes,rw,rb,pm,rheld):
    omap={pid:(A,B) for pid,A,B,_,_ in held}
    rmap={pid:(A,B) for pid,A,B,_,_ in rheld}
    err=0.0
    for pid in omap:
        A,B=omap[pid]; AA,BB=rmap[pid]
        for q in all_codes:
            qq=remap_code(q,pm)
            err=max(err,abs(score(q,A,B,orig_probes,orig_w,orig_b)-score(qq,AA,BB,rprobes,rw,rb)))
    return err

def canonical_graph(probes):
    S=set(probes); best=None
    for pm in itertools.permutations(states):
        bits=0
        for idx,e in enumerate(edges):
            # inverse-free canonicalization by mapping selected original edges forward.
            if e in S:
                ee=remap_edge(e,pm); bits |= 1<<edges.index(ee)
        if best is None or bits<best: best=bits
    return best

orig_examples=make_examples(train,train_queries)
orig_selected,orig_scores=select_probes(orig_examples)
orig_w,orig_b=fit_model(orig_selected,orig_examples)
orig_orbit=canonical_graph(orig_selected)

# Fixed 16 frozen relabelings, same coverage style as V15.
perms=list(itertools.permutations(states)); idxs=[round(i*(len(perms)-1)/15) for i in range(16)]
trials=[]
for ti,i in enumerate(idxs):
    pm=perms[i]
    rtrain=[]; rheld=[]
    for pid,A,B,scope,perm in pairs:
        AA=relabel_partition(A,pm); BB=relabel_partition(B,pm)
        (rtrain if scope=='train' else rheld).append((pid,AA,BB,scope,perm))
    rq=[remap_code(q,pm) for q in train_queries]
    rex=make_examples(rtrain,rq)

    transported=tuple(sorted(remap_edge(e,pm) for e in orig_selected))
    tw,tb=fit_model(transported,rex)
    terr=max_score_transport_error(orig_selected,orig_w,orig_b,transported,tw,tb,pm,rheld)

    reselected,rscores=select_probes(rex)
    rw,rb=fit_model(reselected,rex)
    rerr=max_score_transport_error(orig_selected,orig_w,orig_b,reselected,rw,rb,pm,rheld)

    inter=len(set(transported)&set(reselected)); union=len(set(transported)|set(reselected))
    trials.append({
        'trial':ti,
        'transport_error':terr,
        'reselection_error':rerr,
        'reselection_jaccard_to_transport':inter/union,
        'reselected_same_graph_orbit':canonical_graph(reselected)==orig_orbit,
        'transported_same_graph_orbit':canonical_graph(transported)==orig_orbit,
    })

transport_max=max(t['transport_error'] for t in trials)
reselect_max=max(t['reselection_error'] for t in trials)
reselect_min_jaccard=min(t['reselection_jaccard_to_transport'] for t in trials)
same_orbit_count=sum(t['reselected_same_graph_orbit'] for t in trials)

# Decision is preregistered as a separator among causes, not as a forced positive.
if transport_max<1e-10 and reselect_max>=1e-8:
    diagnosis='RESELECTION_BREAKS_EQUIVARIANCE'
elif transport_max>=1e-8:
    diagnosis='REPRESENTATION_OR_MODEL_BREAKS_EQUIVARIANCE'
elif transport_max<1e-10 and reselect_max<1e-10:
    diagnosis='NO_EQUIVARIANCE_DEFECT_AT_SCORE_LEVEL'
else:
    diagnosis='MIXED_OR_NUMERICAL'

G1_transport_exact=transport_max<1e-10
G2_decisive=diagnosis!='MIXED_OR_NUMERICAL'
G3_orbit_audited=all(t['transported_same_graph_orbit'] for t in trials)
G4_nontrivial_reselection=(reselect_min_jaccard<1.0) or (reselect_max>=1e-8)

gates={
 'G1_transported_probe_interface_is_score_equivariant':G1_transport_exact,
 'G2_failure_source_is_decisively_classified':G2_decisive,
 'G3_transport_preserves_probe_graph_orbit':G3_orbit_audited,
 'G4_reselection_control_is_nontrivial':G4_nontrivial_reselection,
}
result={
 'schema':'minimal.core.probe.interface.equivariance.v16',
 'seed':SEED,
 'parent':'V15 run 32883964654',
 'question':'does V15 relabel sensitivity come from the probe-selection rule choosing presentation-dependent representatives, or from the downstream residual/query model itself?',
 'original_selected_probes':orig_selected,
 'original_probe_graph_orbit':orig_orbit,
 'trial_count':len(trials),
 'transport_score_error_max':transport_max,
 'reselection_score_error_max':reselect_max,
 'reselection_jaccard_min':reselect_min_jaccard,
 'reselected_same_graph_orbit_count':same_orbit_count,
 'diagnosis':diagnosis,
 'trials':trials,
 'gates':gates,
 'pass':all(gates.values()),
 'interpretation_boundary':'This diagnoses the source of V15 presentation sensitivity in the frozen finite family. It does not yet prove an invariant learned probe-class selector or autonomous observation-language invention.'
}
os.makedirs('artifacts/minimal_core_probe_interface_equivariance_v16',exist_ok=True)
with open('artifacts/minimal_core_probe_interface_equivariance_v16/result.json','w') as f: json.dump(result,f,indent=2,sort_keys=True)
print(json.dumps(result,indent=2,sort_keys=True))
if not result['pass']: raise SystemExit('FAIL_MINIMAL_CORE_PROBE_INTERFACE_EQUIVARIANCE_V16')
print('PASS_MINIMAL_CORE_PROBE_INTERFACE_EQUIVARIANCE_V16')
