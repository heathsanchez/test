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


def call(prompt,max_tokens=220,json_mode=False):
    body={'model':MODEL,'messages':[{'role':'user','content':prompt}], 'temperature':0,'max_tokens':max_tokens}
    if json_mode: body['response_format']={'type':'json_object'}
    req=urllib.request.Request(URL,data=json.dumps(body).encode(),headers={'Authorization':f'Bearer {TOKEN}','Content-Type':'application/json'})
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
    out={}
    for qa in range(m):
        grp=[h for h in S if pred(h,q,m)==qa]
        tc=Counter(pred(h,target,m) for h in grp)
        out[str(qa)]={str(tv):tc.get(tv,0) for tv in range(m)}
    return out

def sham_table(S,q,target,m):
    qc=Counter(pred(h,q,m) for h in S); tc=Counter(pred(h,target,m) for h in S)
    return {'query_outcome_counts':{str(v):qc.get(v,0) for v in range(m)},'target_marginal_counts':{str(v):tc.get(v,0) for v in range(m)}}

def raw_prompt(t):
    obs='; '.join(f'{p}->{a}' for p,a in sorted(t['obs'].items())); qs=', '.join(t['queries'])
    return (f'Hidden verified law family: value=(base[prefix]+offset[suffix]) mod {t["m"]}, gauge offset[X]=0. '
            f'Verified observations: {obs}. TARGET whose value ultimately matters: {t["target"]}. '
            f'You may make exactly one extra query from: {qs}. Choose the query that minimizes expected uncertainty of the TARGET after its answer is observed. '
            'Return only JSON {"query":"PAIR"}.')

def induce_prompt(t):
    obs='; '.join(f'{p}->{a}' for p,a in sorted(t['obs'].items())); qs=', '.join(t['queries'])
    return (f'Hidden verified law family: value=(base[prefix]+offset[suffix]) mod {t["m"]}, gauge offset[X]=0. '
            f'Verified observations: {obs}. TARGET whose value ultimately matters: {t["target"]}. Allowed future queries: {qs}. '
            'Before choosing any query, construct the smallest useful decision representation of the remaining uncertainty. Preserve distinctions only when different possible answers to an allowed query can change what values remain possible for the TARGET; discard latent details that cannot change that future decision. '
            'Do NOT recommend, rank, or select a query. Output only the compact representation, in whatever notation is most useful for a fresh solver.')
def choose_from_rep_prompt(t,rep):
    return (f'TARGET: {t["target"]}. Allowed queries: {", ".join(t["queries"])}. You are given a compact representation produced by another solver from the verified evidence:\n{rep}\n'
            'Using only this representation, choose the allowed query that minimizes expected uncertainty of the TARGET after its answer is observed. Return only JSON {"query":"PAIR"}.')
def hand_prompt(t,S,kind):
    base=(f'TARGET: {t["target"]}. Allowed queries: {", ".join(t["queries"])}. ')
    if kind=='HAND_QUOTIENT':
        tables={q:quotient_table(S,q,t['target'],t['m']) for q in t['queries']}
        base+='For each query, each possible query outcome maps to counts of surviving TARGET outcomes: '+json.dumps(tables,sort_keys=True)
    else:
        tables={q:sham_table(S,q,t['target'],t['m']) for q in t['queries']}
        base+='Marginal summaries without query-target coupling: '+json.dumps(tables,sort_keys=True)
    return base+' Choose the query that minimizes expected uncertainty of the TARGET after its answer is observed. Return only JSON {"query":"PAIR"}.'

def parse_q(raw,queries):
    try: q=json.loads(raw).get('query')
    except Exception: q=None
    return q if q in queries else None

tasks=build_tasks(); rows=[]
for ti,t in enumerate(tasks,1):
    print(f'[{ti}/{len(tasks)}] {t["id"]}',flush=True)
    m=t['m']; H=all_hypotheses(m); S=survivors(H,t['obs'],m); truth=t['truth']; tv=pred(truth,t['target'],m)
    # deterministic ceiling
    q=t['optimal']; a=pred(truth,q,m); S2=update(S,q,a,m); tp=majority(S2,t['target'],m)
    rows.append({'task_id':t['id'],'m':m,'arm':'OPTIMAL_QUERY','query':q,'query_optimal':True,'target_truth':tv,'target_pred':tp,'correct':tp==tv,'entropy_after':target_entropy(S2,t['target'],m),'optimal_info_gain':t['gains'][q],'chosen_info_gain':t['gains'][q]})
    # raw direct
    raw=call(raw_prompt(t),40,True); q=parse_q(raw,t['queries'])
    if q is None: tp=majority(S,t['target'],m); ea=t['entropy_before']; cig=0.0
    else:
        a=pred(truth,q,m); S2=update(S,q,a,m); tp=majority(S2,t['target'],m); ea=target_entropy(S2,t['target'],m); cig=t['gains'][q]
    rows.append({'task_id':t['id'],'m':m,'arm':'RAW_DIRECT','raw':raw,'query':q,'query_optimal':q==t['optimal'],'target_truth':tv,'target_pred':tp,'correct':tp==tv,'entropy_after':ea,'optimal_info_gain':t['gains'][t['optimal']],'chosen_info_gain':cig})
    # self-induced two stage
    rep=call(induce_prompt(t),260,False)
    raw2=call(choose_from_rep_prompt(t,rep),40,True); q=parse_q(raw2,t['queries'])
    if q is None: tp=majority(S,t['target'],m); ea=t['entropy_before']; cig=0.0
    else:
        a=pred(truth,q,m); S2=update(S,q,a,m); tp=majority(S2,t['target'],m); ea=target_entropy(S2,t['target'],m); cig=t['gains'][q]
    rows.append({'task_id':t['id'],'m':m,'arm':'SELF_INDUCED','representation':rep,'raw':raw2,'query':q,'query_optimal':q==t['optimal'],'target_truth':tv,'target_pred':tp,'correct':tp==tv,'entropy_after':ea,'optimal_info_gain':t['gains'][t['optimal']],'chosen_info_gain':cig})
    # hand and sham
    for arm in ['HAND_QUOTIENT','SHAM_MARGINAL']:
        raw=call(hand_prompt(t,S,arm),40,True); q=parse_q(raw,t['queries'])
        if q is None: tp=majority(S,t['target'],m); ea=t['entropy_before']; cig=0.0
        else:
            a=pred(truth,q,m); S2=update(S,q,a,m); tp=majority(S2,t['target'],m); ea=target_entropy(S2,t['target'],m); cig=t['gains'][q]
        rows.append({'task_id':t['id'],'m':m,'arm':arm,'raw':raw,'query':q,'query_optimal':q==t['optimal'],'target_truth':tv,'target_pred':tp,'correct':tp==tv,'entropy_after':ea,'optimal_info_gain':t['gains'][t['optimal']],'chosen_info_gain':cig})

safe=[]
for t in tasks:
    x=dict(t); x['truth']={'base':t['truth'][0],'offset':t['truth'][1]}; safe.append(x)
(ROOT/'tasks.json').write_text(json.dumps(safe,indent=2)); (ROOT/'answers.json').write_text(json.dumps(rows,indent=2))
(ROOT/'run_metadata.json').write_text(json.dumps({'schema':'self.induced.future.quotient.v1','model':MODEL,'temperature':0,'seed':SEED,'families':FAMILIES,'tasks_per_family':TASKS_PER_FAMILY,'n_tasks':len(tasks)},indent=2))
print('SELF_INDUCED_FUTURE_QUOTIENT_V1_RUN_PASS',len(tasks),len(rows),flush=True)
