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
PREFIXES='ABCD'
SUFFIXES='XYZ'
FAMILIES=[2,3,5]
TASKS_PER_FAMILY=16
LLM_ARMS=['GENERIC_OBS_ONLY','TARGET_INFO_GAIN_OBS_ONLY']

def all_hypotheses(m):
    # gauge X=0; A-D and Y,Z vary
    hs=[]
    for vals in product(range(m), repeat=6):
        b=dict(zip(PREFIXES, vals[:4])); o={'X':0,'Y':vals[4],'Z':vals[5]}
        hs.append((b,o))
    return hs

def pred(h,p,m):
    return (h[0][p[0]]+h[1][p[1]])%m

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

def survivors(H,obs,m):
    return [h for h in H if all(pred(h,p,m)==a for p,a in obs.items())]

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
    tasks=[]
    pairs=[a+b for a in PREFIXES for b in SUFFIXES]
    for m in FAMILIES:
        H=all_hypotheses(m)
        made=0; attempts=0
        while made<TASKS_PER_FAMILY and attempts<100000:
            attempts+=1
            truth=RNG.choice(H)
            shuffled=pairs[:]; RNG.shuffle(shuffled)
            # partial observations 4-6, target and 4 queries disjoint
            k=RNG.choice([4,5,6])
            obs_pairs=shuffled[:k]
            remaining=[p for p in pairs if p not in obs_pairs]
            if len(remaining)<5: continue
            target=remaining[0]; queries=remaining[1:5]
            obs={p:pred(truth,p,m) for p in obs_pairs}
            S=survivors(H,obs,m)
            if len(S)<4 or len(S)>5000: continue
            e0=target_entropy(S,target,m)
            if e0<0.75: continue
            gains={q:e0-expected_target_entropy(S,q,target,m) for q in queries}
            best=max(gains.values()); worst=min(gains.values())
            if best<0.5 or best-worst<0.25: continue
            optimal=sorted(queries,key=lambda q:(-gains[q],q))[0]
            tasks.append({'id':f'm{m}_{made:02d}','m':m,'truth':truth,'obs':obs,'target':target,'queries':queries,'n_survivors':len(S),'entropy_before':e0,'gains':gains,'optimal':optimal})
            made+=1
        assert made==TASKS_PER_FAMILY, (m,made)
    return tasks

def prompt(t,arm):
    obs='; '.join(f'{p}->{a}' for p,a in sorted(t['obs'].items()))
    qs=', '.join(t['queries'])
    base=(f'Hidden verified law family: value=(base[prefix]+offset[suffix]) mod {t["m"]}, with gauge offset[X]=0. '
          f'Verified observations: {obs}. Target pair whose value ultimately matters: {t["target"]}. '
          f'You may make exactly one extra query from: {qs}. Return only JSON {{"query":"PAIR"}}.')
    if arm=='GENERIC_OBS_ONLY': return base+' Choose the most useful next query.'
    return base+' Choose the allowed query that minimizes expected uncertainty (entropy) of the TARGET value after its answer is observed. Do not optimize irrelevant latent details.'

def serialize_truth(h): return {'base':h[0],'offset':h[1]}

tasks=build_tasks(); rows=[]
for t in tasks:
    m=t['m']; H=all_hypotheses(m); S=survivors(H,t['obs'],m); truth=t['truth']; tv=pred(truth,t['target'],m)
    # deterministic random and optimal
    for arm,q in [('RANDOM_QUERY',RNG.choice(t['queries'])),('OPTIMAL_QUERY',t['optimal'])]:
        a=pred(truth,q,m); S2=update(S,q,a,m); tp=majority(S2,t['target'],m)
        rows.append({'task_id':t['id'],'m':m,'arm':arm,'query':q,'query_optimal':q==t['optimal'],'target_truth':tv,'target_pred':tp,'correct':tp==tv,'entropy_before':t['entropy_before'],'entropy_after':target_entropy(S2,t['target'],m),'optimal_info_gain':t['gains'][t['optimal']],'chosen_info_gain':t['gains'][q]})
    for arm in LLM_ARMS:
        raw=call(prompt(t,arm))
        try: q=json.loads(raw).get('query')
        except Exception: q=None
        valid=q in t['queries']
        if valid:
            a=pred(truth,q,m); S2=update(S,q,a,m); tp=majority(S2,t['target'],m); ea=target_entropy(S2,t['target'],m)
        else:
            tp=majority(S,t['target'],m); ea=t['entropy_before']
        rows.append({'task_id':t['id'],'m':m,'arm':arm,'raw':raw,'query':q,'query_valid':valid,'query_optimal':q==t['optimal'],'target_truth':tv,'target_pred':tp,'correct':tp==tv,'entropy_before':t['entropy_before'],'entropy_after':ea,'optimal_info_gain':t['gains'][t['optimal']],'chosen_info_gain':t['gains'].get(q,0.0)})

safe_tasks=[]
for t in tasks:
    x=dict(t); x['truth']=serialize_truth(x['truth']); safe_tasks.append(x)
(ROOT/'tasks.json').write_text(json.dumps(safe_tasks,indent=2))
(ROOT/'answers.json').write_text(json.dumps(rows,indent=2))
(ROOT/'run_metadata.json').write_text(json.dumps({'schema':'right.question.transfer.v1','model':MODEL,'temperature':0,'seed':SEED,'families':FAMILIES,'tasks_per_family':TASKS_PER_FAMILY,'n_tasks':len(tasks),'llm_arms':LLM_ARMS},indent=2))
print('RIGHT_QUESTION_TRANSFER_V1_RUN_PASS',len(tasks),len(rows),flush=True)
