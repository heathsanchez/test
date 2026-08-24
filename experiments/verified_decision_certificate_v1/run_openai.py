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


def call(prompt,max_tokens=500):
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
        while made<TASKS_PER_FAMILY and attempts<200000:
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
            zero=[q for q in queries if expected_target_entropy(S,q,target,m)<1e-12]
            if not zero: continue
            optimal=sorted(queries,key=lambda q:(-gains[q],q))[0]
            tasks.append({'id':f'm{m}_{made:02d}','m':m,'truth':truth,'obs':obs,'target':target,'queries':queries,
                          'n_survivors':len(S),'entropy_before':e0,'gains':gains,'optimal':optimal,'decision_complete_queries':zero})
            made+=1
        assert made==TASKS_PER_FAMILY,(m,made)
    return tasks


def exact_support(S,q,target,m):
    out={}
    for qa in range(m):
        out[str(qa)]=sorted(set(pred(h,target,m) for h in S if pred(h,q,m)==qa))
    return out

def normalize_cert(obj,t):
    if not isinstance(obj,dict): obj={}
    q=obj.get('query')
    if q not in t['queries']: q=t['queries'][0]
    raw=obj.get('support',{})
    supp={}
    for a in range(t['m']):
        vals=raw.get(str(a),raw.get(a,[])) if isinstance(raw,dict) else []
        if not isinstance(vals,list): vals=[]
        clean=[]
        for x in vals:
            try: v=int(x)
            except Exception: continue
            if 0<=v<t['m'] and v not in clean: clean.append(v)
        supp[str(a)]=sorted(clean)
    return {'query':q,'support':supp}
def cert_errors(cert,S,t):
    truth=exact_support(S,cert['query'],t['target'],t['m']); errs=[]
    for a in range(t['m']):
        k=str(a); c=set(cert['support'][k]); z=set(truth[k])
        if c!=z: errs.append({'outcome':a,'missing':sorted(z-c),'spurious':sorted(c-z)})
    return errs
def cert_exact(cert,S,t): return not cert_errors(cert,S,t)
def decision_complete_support(supp):
    return all(len(v)<=1 for v in supp.values()) and any(len(v)==1 for v in supp.values())
def cert_decision_complete(cert,S,t):
    return decision_complete_support(exact_support(S,cert['query'],t['target'],t['m']))
def downstream(t,S,q):
    a=pred(t['truth'],q,t['m']); S2=update(S,q,a,t['m']); tp=majority(S2,t['target'],t['m']); tv=pred(t['truth'],t['target'],t['m'])
    return {'correct':tp==tv,'target_truth':tv,'target_pred':tp,'entropy_after':target_entropy(S2,t['target'],t['m'])}


def raw_prompt(t):
    obs='; '.join(f'{p}->{a}' for p,a in sorted(t['obs'].items())); qs=', '.join(t['queries'])
    return (f'Hidden verified law: value=(base[prefix]+offset[suffix]) mod {t["m"]}, gauge offset[X]=0. '
            f'Verified observations: {obs}. TARGET: {t["target"]}. One allowed extra query from: {qs}. '
            'Choose the query most likely to determine the TARGET. Return only JSON {"query":"PAIR"}.')

def cert_prompt(t,feedback=None,previous=None):
    obs='; '.join(f'{p}->{a}' for p,a in sorted(t['obs'].items())); qs=', '.join(t['queries'])
    schema={str(a):[] for a in range(t['m'])}
    p=(f'Construct the SMALLEST decision certificate needed to choose one useful extra query. Hidden verified law: '
       f'value=(base[prefix]+offset[suffix]) mod {t["m"]}, gauge offset[X]=0. Verified observations: {obs}. TARGET: {t["target"]}. '
       f'Allowed queries: {qs}. Choose ONE query q. For each possible observed value a of q, list ALL TARGET values still possible after q=a '
       'across every hidden law consistent with the observations. Prefer a query whose every reachable outcome leaves exactly one TARGET value. '
       f'Return only JSON {{"query":"PAIR","support":{json.dumps(schema)}}}.')
    if previous is not None: p+='\nPrevious certificate: '+json.dumps(previous,sort_keys=True)
    if feedback: p+='\nExternal verifier counterexamples for the chosen certificate: '+json.dumps(feedback,sort_keys=True)+'. Repair the certificate; you may change the query.'
    return p


tasks=build_tasks(); rows=[]
for i,t in enumerate(tasks,1):
    print(f'[{i}/{len(tasks)}] {t["id"]}',flush=True)
    H=all_hypotheses(t['m']); S=survivors(H,t['obs'],t['m'])
    raw=call(raw_prompt(t),120)
    try: rq=json.loads(raw).get('query')
    except Exception: rq=None
    if rq not in t['queries']: rq=t['queries'][0]
    d=downstream(t,S,rq)
    rows.append({'task_id':t['id'],'m':t['m'],'arm':'RAW_DIRECT','query':rq,'query_optimal':rq==t['optimal'],'decision_complete':rq in t['decision_complete_queries'],**d})

    oraw=call(cert_prompt(t),500)
    try: oobj=json.loads(oraw)
    except Exception: oobj={}
    cert=normalize_cert(oobj,t); d=downstream(t,S,cert['query'])
    rows.append({'task_id':t['id'],'m':t['m'],'arm':'ONE_SHOT_CERTIFICATE','query':cert['query'],'query_optimal':cert['query']==t['optimal'],
                 'certificate_exact':cert_exact(cert,S,t),'decision_complete':cert_decision_complete(cert,S,t),'n_errors':len(cert_errors(cert,S,t)),**d})

    vcert=cert; rounds=1; feedback=cert_errors(vcert,S,t)
    # If support is exact but chosen query still not decision-complete, verifier supplies the unresolved exact cells only.
    if not feedback and not cert_decision_complete(vcert,S,t):
        feedback=[{'query_level':'chosen query is not decision-complete','unresolved':{k:v for k,v in exact_support(S,vcert['query'],t['target'],t['m']).items() if len(v)>1}}]
    while (feedback or not cert_decision_complete(vcert,S,t)) and rounds<4:
        vraw=call(cert_prompt(t,feedback=feedback,previous=vcert),600)
        try: vobj=json.loads(vraw)
        except Exception: vobj={}
        vcert=normalize_cert(vobj,t); rounds+=1; feedback=cert_errors(vcert,S,t)
        if not feedback and not cert_decision_complete(vcert,S,t):
            feedback=[{'query_level':'chosen query is not decision-complete','unresolved':{k:v for k,v in exact_support(S,vcert['query'],t['target'],t['m']).items() if len(v)>1}}]
    d=downstream(t,S,vcert['query'])
    rows.append({'task_id':t['id'],'m':t['m'],'arm':'VERIFIED_CERTIFICATE','query':vcert['query'],'query_optimal':vcert['query']==t['optimal'],
                 'certificate_exact':cert_exact(vcert,S,t),'decision_complete':cert_decision_complete(vcert,S,t),'n_errors':len(cert_errors(vcert,S,t)),'rounds':rounds,**d})

    hq=sorted(t['decision_complete_queries'],key=lambda q:(-t['gains'][q],q))[0]
    hcert={'query':hq,'support':exact_support(S,hq,t['target'],t['m'])}; d=downstream(t,S,hq)
    rows.append({'task_id':t['id'],'m':t['m'],'arm':'HAND_CERTIFICATE','query':hq,'query_optimal':hq==t['optimal'],'certificate_exact':True,'decision_complete':True,'n_errors':0,**d})
    oq=t['optimal']; d=downstream(t,S,oq)
    rows.append({'task_id':t['id'],'m':t['m'],'arm':'OPTIMAL_QUERY','query':oq,'query_optimal':True,'decision_complete':oq in t['decision_complete_queries'],**d})

safe=[]
for t in tasks:
    x=dict(t); x['truth']={'base':t['truth'][0],'offset':t['truth'][1]}; safe.append(x)
(ROOT/'tasks.json').write_text(json.dumps(safe,indent=2)); (ROOT/'answers.json').write_text(json.dumps(rows,indent=2))
(ROOT/'run_metadata.json').write_text(json.dumps({'schema':'verified.decision.certificate.v1','model':MODEL,'temperature':0,'seed':SEED,
    'families':FAMILIES,'tasks_per_family':TASKS_PER_FAMILY,'n_tasks':len(tasks),'max_verified_proposals':4},indent=2))
print('VERIFIED_DECISION_CERTIFICATE_V1_RUN_PASS',len(tasks),len(rows),flush=True)
