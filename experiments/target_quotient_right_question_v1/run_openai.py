import json, math, os, random, time, urllib.request
from collections import Counter, defaultdict
from itertools import product
from pathlib import Path

ROOT=Path(__file__).parent
MODEL=os.environ.get('UVRM_MODEL','gpt-4.1-mini')
TOKEN=os.environ['OPENAI_API_KEY']
URL='https://api.openai.com/v1/chat/completions'
SEED=2026082507
RNG=random.Random(SEED)
PREFIXES='ABCD'; SUFFIXES='XYZ'; FAMILIES=[2,3,5]; TASKS_PER_FAMILY=16
LLM_ARMS=['OBS_ONLY','TARGET_QUOTIENT','SHAM_MARGINAL']

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

def call(prompt):
    body=json.dumps({'model':MODEL,'messages':[{'role':'user','content':prompt}], 'temperature':0,'max_tokens':40,'response_format':{'type':'json_object'}}).encode()
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
        while made<TASKS_PER_FAMILY and attempts<100000:
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
            tasks.append({'id':f'm{m}_{made:02d}','m':m,'truth':truth,'obs':obs,'target':target,'queries':queries,'n_survivors':len(S),'entropy_before':e0,'gains':gains,'optimal':optimal})
            made+=1
        assert made==TASKS_PER_FAMILY,(m,made)
    return tasks

def quotient_table(S,q,target,m):
    # Sufficient target-relative partition: for each possible query outcome,
    # count the surviving hypotheses by TARGET value.
    out={}
    for qa in range(m):
        grp=[h for h in S if pred(h,q,m)==qa]
        tc=Counter(pred(h,target,m) for h in grp)
        out[str(qa)]={str(tv):tc.get(tv,0) for tv in range(m)}
    return out

def sham_table(S,q,target,m):
    qc=Counter(pred(h,q,m) for h in S); tc=Counter(pred(h,target,m) for h in S)
    return {'query_outcome_counts':{str(v):qc.get(v,0) for v in range(m)},
            'target_marginal_counts':{str(v):tc.get(v,0) for v in range(m)}}

def prompt(t,S,arm):
    obs='; '.join(f'{p}->{a}' for p,a in sorted(t['obs'].items())); qs=', '.join(t['queries'])
    base=(f'Hidden verified law family: value=(base[prefix]+offset[suffix]) mod {t["m"]}, gauge offset[X]=0. '
          f'Verified observations: {obs}. TARGET whose value ultimately matters: {t["target"]}. '
          f'You may make exactly one extra query from: {qs}. Return only JSON {{"query":"PAIR"}}.')
    if arm=='TARGET_QUOTIENT':
        tables={q:quotient_table(S,q,t['target'],t['m']) for q in t['queries']}
        base+='\nTARGET-RELATIVE QUOTIENT TABLES. For each query, each possible observed query value maps to counts of remaining TARGET values:\n'+json.dumps(tables,sort_keys=True)
    elif arm=='SHAM_MARGINAL':
        tables={q:sham_table(S,q,t['target'],t['m']) for q in t['queries']}
        base+='\nMARGINAL TABLES (query-outcome counts and current target counts; no query-outcome/target coupling):\n'+json.dumps(tables,sort_keys=True)
    return base+'\nChoose the query that minimizes expected uncertainty of the TARGET after the query answer is observed. Ignore uncertainty about latent details that cannot change the target.'

tasks=build_tasks(); rows=[]
for t in tasks:
    m=t['m']; H=all_hypotheses(m); S=survivors(H,t['obs'],m); truth=t['truth']; tv=pred(truth,t['target'],m)
    for arm,q in [('RANDOM_QUERY',RNG.choice(t['queries'])),('OPTIMAL_QUERY',t['optimal'])]:
        a=pred(truth,q,m); S2=update(S,q,a,m); tp=majority(S2,t['target'],m)
        rows.append({'task_id':t['id'],'m':m,'arm':arm,'query':q,'query_optimal':q==t['optimal'],'target_truth':tv,'target_pred':tp,'correct':tp==tv,'entropy_before':t['entropy_before'],'entropy_after':target_entropy(S2,t['target'],m),'optimal_info_gain':t['gains'][t['optimal']],'chosen_info_gain':t['gains'][q]})
    for arm in LLM_ARMS:
        raw=call(prompt(t,S,arm))
        try: q=json.loads(raw).get('query')
        except Exception: q=None
        valid=q in t['queries']
        if valid:
            a=pred(truth,q,m); S2=update(S,q,a,m); tp=majority(S2,t['target'],m); ea=target_entropy(S2,t['target'],m)
        else:
            tp=majority(S,t['target'],m); ea=t['entropy_before']
        rows.append({'task_id':t['id'],'m':m,'arm':arm,'raw':raw,'query':q,'query_valid':valid,'query_optimal':q==t['optimal'],'target_truth':tv,'target_pred':tp,'correct':tp==tv,'entropy_before':t['entropy_before'],'entropy_after':ea,'optimal_info_gain':t['gains'][t['optimal']],'chosen_info_gain':t['gains'].get(q,0.0)})

safe=[]
for t in tasks:
    x=dict(t); x['truth']={'base':t['truth'][0],'offset':t['truth'][1]}; safe.append(x)
(ROOT/'tasks.json').write_text(json.dumps(safe,indent=2)); (ROOT/'answers.json').write_text(json.dumps(rows,indent=2))
(ROOT/'run_metadata.json').write_text(json.dumps({'schema':'target.quotient.right.question.v1','model':MODEL,'temperature':0,'seed':SEED,'families':FAMILIES,'tasks_per_family':TASKS_PER_FAMILY,'n_tasks':len(tasks),'llm_arms':LLM_ARMS},indent=2))
print('TARGET_QUOTIENT_RIGHT_QUESTION_V1_RUN_PASS',len(tasks),len(rows),flush=True)
