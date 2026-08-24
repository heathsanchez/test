import json, math, os, random, time, urllib.request
from collections import Counter, defaultdict
from itertools import product
from pathlib import Path

ROOT=Path(__file__).parent
MODEL=os.environ.get('UVRM_MODEL','gpt-4.1-mini')
TOKEN=os.environ['OPENAI_API_KEY']
URL='https://api.openai.com/v1/chat/completions'
SEED=2026082509
RNG=random.Random(SEED)
PREFIXES='ABCD'; SUFFIXES='XYZ'; FAMILIES=[2,3,5]; TASKS_PER_FAMILY=12


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


def call(prompt,max_tokens=900):
    body=json.dumps({'model':MODEL,'messages':[{'role':'user','content':prompt}], 'temperature':0,
                     'max_tokens':max_tokens,'response_format':{'type':'json_object'}}).encode()
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
            k=RNG.choice([4,5,6]); obs_pairs=shuffled[:k]
            remaining=[p for p in pairs if p not in obs_pairs]
            if len(remaining)<5: continue
            target=remaining[0]; queries=remaining[1:5]
            obs={p:pred(truth,p,m) for p in obs_pairs}; S=survivors(H,obs,m)
            if len(S)<4 or len(S)>5000: continue
            e0=target_entropy(S,target,m)
            if e0<0.75: continue
            gains={q:e0-expected_target_entropy(S,q,target,m) for q in queries}
            best=max(gains.values()); worst=min(gains.values())
            if best<0.5 or best-worst<0.25: continue
            optimal=sorted(queries,key=lambda q:(-gains[q],q))[0]
            # Require at least one query that fully determines target under every possible answer.
            if expected_target_entropy(S,optimal,target,m)>1e-12: continue
            tasks.append({'id':f'm{m}_{made:02d}','m':m,'truth':truth,'obs':obs,'target':target,'queries':queries,
                          'n_survivors':len(S),'entropy_before':e0,'gains':gains,'optimal':optimal})
            made+=1
        assert made==TASKS_PER_FAMILY,(m,made)
    return tasks


def exact_support(S,q,target,m):
    out={}
    for qa in range(m):
        vals=sorted(set(pred(h,target,m) for h in S if pred(h,q,m)==qa))
        out[str(qa)]=vals
    return out

def exact_quotient(S,t): return {q:exact_support(S,q,t['target'],t['m']) for q in t['queries']}

def normalize_candidate(obj,t):
    qobj=obj.get('quotient',obj) if isinstance(obj,dict) else {}
    out={}
    for q in t['queries']:
        cell=qobj.get(q,{}) if isinstance(qobj,dict) else {}
        out[q]={}
        for a in range(t['m']):
            raw=cell.get(str(a),cell.get(a,[])) if isinstance(cell,dict) else []
            if not isinstance(raw,list): raw=[]
            vals=[]
            for x in raw:
                try: v=int(x)
                except Exception: continue
                if 0<=v<t['m'] and v not in vals: vals.append(v)
            out[q][str(a)]=sorted(vals)
    return out

def quotient_errors(cand,truth,t,limit=12):
    errs=[]
    for q in t['queries']:
        for a in range(t['m']):
            k=str(a); c=set(cand[q][k]); z=set(truth[q][k])
            if c!=z:
                errs.append({'query':q,'outcome':a,'missing':sorted(z-c),'spurious':sorted(c-z)})
    return errs[:limit]

def quotient_exact(cand,truth): return cand==truth

def choose_from_support(cand,t):
    # A query is decision-complete iff every reachable/nonempty answer cell is singleton.
    # Prefer fewer unresolved cells, then smaller total support, then lexical.
    scores=[]
    for q in t['queries']:
        cells=list(cand[q].values())
        unresolved=sum(1 for s in cells if len(s)>1)
        empties=sum(1 for s in cells if len(s)==0)
        total=sum(len(s) for s in cells)
        # empties are allowed (unreachable outcomes); unresolved is what matters.
        scores.append((unresolved,total,empties,q))
    return sorted(scores)[0][3]

def downstream(t,S,q):
    a=pred(t['truth'],q,t['m']); S2=update(S,q,a,t['m']); tp=majority(S2,t['target'],t['m']); tv=pred(t['truth'],t['target'],t['m'])
    return {'correct':tp==tv,'target_truth':tv,'target_pred':tp,'entropy_after':target_entropy(S2,t['target'],t['m'])}

def raw_prompt(t):
    obs='; '.join(f'{p}->{a}' for p,a in sorted(t['obs'].items())); qs=', '.join(t['queries'])
    return (f'Hidden verified law family: value=(base[prefix]+offset[suffix]) mod {t["m"]}, gauge offset[X]=0. '
            f'Verified observations: {obs}. TARGET whose value ultimately matters: {t["target"]}. '
            f'You may make exactly one extra query from: {qs}. Choose the query most likely to make the TARGET value determined. '
            'Return only JSON {"query":"PAIR"}.')

def synth_prompt(t,feedback=None,previous=None):
    obs='; '.join(f'{p}->{a}' for p,a in sorted(t['obs'].items())); qs=', '.join(t['queries'])
    schema={q:{str(a):[] for a in range(t['m'])} for q in t['queries']}
    p=(f'Construct a target-relative quotient from raw verified evidence. Hidden law family: value=(base[prefix]+offset[suffix]) mod {t["m"]}, gauge offset[X]=0. '
       f'Verified observations: {obs}. TARGET: {t["target"]}. Allowed future queries: {qs}. '
       'For each allowed query q and each possible observed value a, list ALL target values that remain possible if q=a, considering every hidden law consistent with the verified observations. '
       'Do not choose or rank a query. Preserve only target-relevant possibility sets. '
       f'Return only JSON exactly shaped as {{"quotient":{json.dumps(schema)}}}.')
    if previous is not None:
        p += '\nPrevious candidate: '+json.dumps(previous,sort_keys=True)
    if feedback:
        p += '\nExternal verifier counterexamples. Repair every reported cell and re-check the whole quotient: '+json.dumps(feedback,sort_keys=True)
    return p

tasks=build_tasks(); rows=[]
for i,t in enumerate(tasks,1):
    print(f'[{i}/{len(tasks)}] {t["id"]}',flush=True)
    m=t['m']; H=all_hypotheses(m); S=survivors(H,t['obs'],m); tq=exact_quotient(S,t)
    # raw direct
    raw=call(raw_prompt(t),120)
    try: rq=json.loads(raw).get('query')
    except Exception: rq=None
    if rq not in t['queries']: rq=t['queries'][0]
    d=downstream(t,S,rq)
    rows.append({'task_id':t['id'],'m':m,'arm':'RAW_DIRECT','query':rq,'query_optimal':rq==t['optimal'],**d})
    # one-shot synthesis
    sraw=call(synth_prompt(t),900)
    try: sobj=json.loads(sraw)
    except Exception: sobj={}
    cand=normalize_candidate(sobj,t); q=choose_from_support(cand,t); d=downstream(t,S,q)
    rows.append({'task_id':t['id'],'m':m,'arm':'ONE_SHOT_SYNTHESIS','query':q,'query_optimal':q==t['optimal'],
                 'quotient_exact':quotient_exact(cand,tq),'n_errors':len(quotient_errors(cand,tq,t,999)),**d})
    # verified iterative synthesis: same first candidate, then up to 3 repairs (4 proposals total)
    vcand=cand; rounds=1; feedback=quotient_errors(vcand,tq,t)
    while feedback and rounds<4:
        vraw=call(synth_prompt(t,feedback=feedback,previous=vcand),1100)
        try: vobj=json.loads(vraw)
        except Exception: vobj={}
        vcand=normalize_candidate(vobj,t); rounds+=1; feedback=quotient_errors(vcand,tq,t)
    vq=choose_from_support(vcand,t); d=downstream(t,S,vq)
    rows.append({'task_id':t['id'],'m':m,'arm':'VERIFIED_SYNTHESIS','query':vq,'query_optimal':vq==t['optimal'],
                 'quotient_exact':quotient_exact(vcand,tq),'n_errors':len(quotient_errors(vcand,tq,t,999)),'rounds':rounds,**d})
    # hand quotient and exact optimum
    hq=choose_from_support(tq,t); d=downstream(t,S,hq)
    rows.append({'task_id':t['id'],'m':m,'arm':'HAND_QUOTIENT','query':hq,'query_optimal':hq==t['optimal'],'quotient_exact':True,'n_errors':0,**d})
    oq=t['optimal']; d=downstream(t,S,oq)
    rows.append({'task_id':t['id'],'m':m,'arm':'OPTIMAL_QUERY','query':oq,'query_optimal':True,**d})

safe=[]
for t in tasks:
    x=dict(t); x['truth']={'base':t['truth'][0],'offset':t['truth'][1]}; safe.append(x)
(ROOT/'tasks.json').write_text(json.dumps(safe,indent=2)); (ROOT/'answers.json').write_text(json.dumps(rows,indent=2))
(ROOT/'run_metadata.json').write_text(json.dumps({'schema':'verified.quotient.synthesis.v1','model':MODEL,'temperature':0,'seed':SEED,
    'families':FAMILIES,'tasks_per_family':TASKS_PER_FAMILY,'n_tasks':len(tasks),'max_verified_proposals':4},indent=2))
print('VERIFIED_QUOTIENT_SYNTHESIS_V1_RUN_PASS',len(tasks),len(rows),flush=True)
