import json, math, os, random, time, urllib.request
from collections import Counter, defaultdict
from itertools import product
from pathlib import Path

ROOT=Path(__file__).parent
MODEL=os.environ.get('UVRM_MODEL','gpt-4.1-mini')
TOKEN=os.environ['OPENAI_API_KEY']
URL='https://api.openai.com/v1/chat/completions'
SEED=2026082510
RNG=random.Random(SEED)
PREFIXES='ABCD'; SUFFIXES='XYZ'; FAMILIES=[2,3,5]; TASKS_PER_FAMILY=16

def all_hypotheses(m):
    return [(dict(zip(PREFIXES,v[:4])),{'X':0,'Y':v[4],'Z':v[5]}) for v in product(range(m),repeat=6)]
def pred(h,p,m): return (h[0][p[0]]+h[1][p[1]])%m
def entropy(vals):
    if not vals: return 0.0
    c=Counter(vals); n=len(vals)
    return -sum((v/n)*math.log2(v/n) for v in c.values())
def target_entropy(H,t,m): return entropy([pred(h,t,m) for h in H])
def update(H,q,a,m): return [h for h in H if pred(h,q,m)==a]
def expected_target_entropy(H,q,t,m):
    groups=defaultdict(list)
    for h in H: groups[pred(h,q,m)].append(h)
    return sum(len(g)/len(H)*target_entropy(g,t,m) for g in groups.values())
def majority(H,t,m):
    c=Counter(pred(h,t,m) for h in H); mx=max(c.values()); return min(k for k,v in c.items() if v==mx)
def survivors(H,obs,m): return [h for h in H if all(pred(h,p,m)==a for p,a in obs.items())]
def call(prompt,max_tokens=260):
    body=json.dumps({'model':MODEL,'messages':[{'role':'user','content':prompt}], 'temperature':0,'max_tokens':max_tokens,'response_format':{'type':'json_object'}}).encode()
    req=urllib.request.Request(URL,data=body,headers={'Authorization':f'Bearer {TOKEN}','Content-Type':'application/json'})
    last=None
    for i in range(4):
        try:
            with urllib.request.urlopen(req,timeout=90) as r: obj=json.loads(r.read().decode())
            return obj['choices'][0]['message']['content']
        except Exception as e:
            last=e; time.sleep(2**i)
    raise last

def build_tasks():
    tasks=[]; pairs=[a+b for a in PREFIXES for b in SUFFIXES]
    for m in FAMILIES:
        H=all_hypotheses(m); made=0; attempts=0
        while made<TASKS_PER_FAMILY and attempts<150000:
            attempts+=1; truth=RNG.choice(H); shuffled=pairs[:]; RNG.shuffle(shuffled)
            k=RNG.choice([4,5,6]); obs_pairs=shuffled[:k]; remaining=[p for p in pairs if p not in obs_pairs]
            if len(remaining)<5: continue
            target=remaining[0]; queries=remaining[1:5]; obs={p:pred(truth,p,m) for p in obs_pairs}; S=survivors(H,obs,m)
            if len(S)<4 or len(S)>5000: continue
            e0=target_entropy(S,target,m)
            if e0<0.75: continue
            ents={q:expected_target_entropy(S,q,target,m) for q in queries}
            best=min(ents.values()); worst=max(ents.values())
            if best>1e-12 or worst-best<0.25: continue
            optimal=sorted(queries,key=lambda q:(ents[q],q))[0]
            tasks.append({'id':f'm{m}_{made:02d}','m':m,'truth':truth,'obs':obs,'target':target,'queries':queries,'entropy_before':e0,'expected_entropy':ents,'optimal':optimal})
            made+=1
        assert made==TASKS_PER_FAMILY,(m,made)
    return tasks

def raw_prompt(t):
    obs='; '.join(f'{p}->{a}' for p,a in sorted(t['obs'].items())); qs=', '.join(t['queries'])
    return (f'Hidden verified law family: value=(base[prefix]+offset[suffix]) mod {t["m"]}, gauge offset[X]=0. '
            f'Verified observations: {obs}. TARGET: {t["target"]}. One extra query allowed from: {qs}. '
            'Choose the query most likely to determine the TARGET. Return only JSON {"query":"PAIR"}.')

def comp_prompt(t,previous=None,feedback=None):
    obs='; '.join(f'{p}->{a}' for p,a in sorted(t['obs'].items())); qs=', '.join(t['queries'])
    p=(f'Hidden verified law family: value=(base[prefix]+offset[suffix]) mod {t["m"]}, gauge offset[X]=0. '
       f'Verified observations: {obs}. TARGET: {t["target"]}. Candidate extra queries: {qs}. '
       'Construct a compact comparative representation over ALL candidate queries. Rank them best-to-worst for reducing expected uncertainty of the TARGET. '
       'Also give each query a predicted expected_target_entropy number (0 is best). Do not reconstruct the full latent world set or full quotient. '
       'Return only JSON {"ranking":["Q1","Q2","Q3","Q4"],"scores":{"Q1":number,"Q2":number,"Q3":number,"Q4":number}}.')
    if previous is not None: p+='\nPrevious comparison: '+json.dumps(previous,sort_keys=True)
    if feedback is not None: p+='\nExternal verifier ranking counterexample: '+json.dumps(feedback,sort_keys=True)+' Repair the comparative representation.'
    return p

def normalize(obj,t):
    ranking=obj.get('ranking',[]) if isinstance(obj,dict) else []
    ranking=[q for q in ranking if q in t['queries']]
    for q in t['queries']:
        if q not in ranking: ranking.append(q)
    scores=obj.get('scores',{}) if isinstance(obj,dict) else {}
    out={}
    for q in t['queries']:
        try: out[q]=float(scores.get(q,99.0))
        except Exception: out[q]=99.0
    return {'ranking':ranking[:4],'scores':out}

def better_feedback(c,t):
    top=c['ranking'][0]; ents=t['expected_entropy']; best=t['optimal']
    if top==best: return None
    # choose a strictly better rival, preferring exact optimum
    rivals=sorted([q for q in t['queries'] if ents[q] < ents[top]-1e-12], key=lambda q:(ents[q],q))
    if not rivals: return None
    r=rivals[0]
    return {'current_top':top,'current_top_true_expected_target_entropy':ents[top],
            'strictly_better_rival':r,'rival_true_expected_target_entropy':ents[r],
            'claim':'current ranking is invalid because the rival leaves less expected TARGET uncertainty'}

def downstream(t,S,q):
    a=pred(t['truth'],q,t['m']); S2=update(S,q,a,t['m']); tp=majority(S2,t['target'],t['m']); tv=pred(t['truth'],t['target'],t['m'])
    return {'correct':tp==tv,'entropy_after':target_entropy(S2,t['target'],t['m'])}

tasks=build_tasks(); rows=[]
for i,t in enumerate(tasks,1):
    print(f'[{i}/{len(tasks)}] {t["id"]}',flush=True)
    H=all_hypotheses(t['m']); S=survivors(H,t['obs'],t['m'])
    raw=call(raw_prompt(t),100)
    try: rq=json.loads(raw).get('query')
    except Exception: rq=None
    if rq not in t['queries']: rq=t['queries'][0]
    rows.append({'task_id':t['id'],'m':t['m'],'arm':'RAW_DIRECT','query':rq,'query_optimal':rq==t['optimal'],**downstream(t,S,rq)})
    sraw=call(comp_prompt(t),300)
    try: sobj=json.loads(sraw)
    except Exception: sobj={}
    one=normalize(sobj,t); oq=one['ranking'][0]
    rows.append({'task_id':t['id'],'m':t['m'],'arm':'ONE_SHOT_COMPARATIVE','query':oq,'query_optimal':oq==t['optimal'],'ranking':one['ranking'],**downstream(t,S,oq)})
    cur=one; rounds=1; fb=better_feedback(cur,t)
    while fb is not None and rounds<4:
        vraw=call(comp_prompt(t,previous=cur,feedback=fb),360)
        try: vobj=json.loads(vraw)
        except Exception: vobj={}
        cur=normalize(vobj,t); rounds+=1; fb=better_feedback(cur,t)
    vq=cur['ranking'][0]
    rows.append({'task_id':t['id'],'m':t['m'],'arm':'VERIFIED_COMPARATIVE','query':vq,'query_optimal':vq==t['optimal'],'ranking':cur['ranking'],'rounds':rounds,'ranking_verified':fb is None,**downstream(t,S,vq)})
    hand=sorted(t['queries'],key=lambda q:(t['expected_entropy'][q],q)); hq=hand[0]
    rows.append({'task_id':t['id'],'m':t['m'],'arm':'HAND_COMPARATIVE','query':hq,'query_optimal':True,'ranking':hand,'ranking_verified':True,**downstream(t,S,hq)})
    q=t['optimal']; rows.append({'task_id':t['id'],'m':t['m'],'arm':'OPTIMAL_QUERY','query':q,'query_optimal':True,**downstream(t,S,q)})

safe=[]
for t in tasks:
    x=dict(t); x['truth']={'base':t['truth'][0],'offset':t['truth'][1]}; safe.append(x)
(ROOT/'tasks.json').write_text(json.dumps(safe,indent=2)); (ROOT/'answers.json').write_text(json.dumps(rows,indent=2))
(ROOT/'run_metadata.json').write_text(json.dumps({'schema':'verified.comparative.quotient.v1','model':MODEL,'temperature':0,'seed':SEED,'families':FAMILIES,'tasks_per_family':TASKS_PER_FAMILY,'n_tasks':len(tasks),'max_verified_proposals':4},indent=2))
print('VERIFIED_COMPARATIVE_QUOTIENT_V1_RUN_PASS',len(tasks),len(rows),flush=True)
