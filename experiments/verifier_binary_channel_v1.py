#!/usr/bin/env python3
"""Verifier Binary Channel V1.

Decisive follow-up to High Value Missing Tests V1B.

Question: does verified comparative repair still help when the verifier feedback is
provably non-identifying as a channel -- i.e. it says only whether the model's
current top query is wrong, never names a better rival, score, outcome, target
value, or quotient cell?

Primary comparison (same frozen tasks/model/temperature):
  ONE_SHOT_COMPARATIVE
  RECHECK_CONTROL         -- one extra reasoning pass, no verifier information
  VERIFIED_BINARY         -- one extra pass with only TOP_WRONG / TOP_OK

The binary repair arm is limited to ONE repair round. This prevents repeated
membership queries from identifying the answer by elimination.

Channel non-identification is certified exactly on the frozen task corpus before
LLM responses are used: for every candidate action index i that can be wrong,
the event "proposal i is wrong" is compatible with at least two different optimal
action indices. Thus the binary message + proposed action does not uniquely name
the repair across the frozen task distribution.
"""
import json, math, os, random, time, urllib.request
from collections import Counter, defaultdict
from itertools import product
from pathlib import Path

ROOT=Path('artifacts/verifier_binary_channel_v1')
ROOT.mkdir(parents=True, exist_ok=True)
MODEL=os.environ.get('UVRM_MODEL','gpt-4.1-mini')
TOKEN=os.environ['OPENAI_API_KEY']
URL='https://api.openai.com/v1/chat/completions'
SEED=202608251433
RNG=random.Random(SEED)
PREFIXES='ABCD'; SUFFIXES='XYZ'; FAMILIES=[2,3,5]; TASKS_PER_FAMILY=16


def all_hypotheses(m):
    return [(dict(zip(PREFIXES,v[:4])),{'X':0,'Y':v[4],'Z':v[5]}) for v in product(range(m),repeat=6)]
def pred(h,p,m): return (h[0][p[0]]+h[1][p[1]])%m
def entropy(vals):
    c=Counter(vals); n=len(vals)
    return 0.0 if not vals else -sum((v/n)*math.log2(v/n) for v in c.values())
def target_entropy(H,t,m): return entropy([pred(h,t,m) for h in H])
def update(H,q,a,m): return [h for h in H if pred(h,q,m)==a]
def survivors(H,obs,m): return [h for h in H if all(pred(h,p,m)==a for p,a in obs.items())]
def expected_target_entropy(H,q,t,m):
    groups=defaultdict(list)
    for h in H: groups[pred(h,q,m)].append(h)
    return sum(len(g)/len(H)*target_entropy(g,t,m) for g in groups.values())
def majority(H,t,m):
    c=Counter(pred(h,t,m) for h in H); mx=max(c.values()); return min(k for k,v in c.items() if v==mx)


def call(prompt,max_tokens=320):
    body=json.dumps({'model':MODEL,'messages':[{'role':'user','content':prompt}],
                     'temperature':0,'max_tokens':max_tokens,
                     'response_format':{'type':'json_object'}}).encode()
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
            target=remaining[0]; queries=sorted(remaining[1:5])
            obs={p:pred(truth,p,m) for p in obs_pairs}; S=survivors(H,obs,m)
            if len(S)<4 or len(S)>5000: continue
            e0=target_entropy(S,target,m)
            if e0<0.75: continue
            ents={q:expected_target_entropy(S,q,target,m) for q in queries}
            best=min(ents.values()); worst=max(ents.values())
            if best>1e-12 or worst-best<0.25: continue
            optimal=min(queries,key=lambda q:(ents[q],q)); opt_index=queries.index(optimal)
            tasks.append({'id':f'm{m}_{made:02d}','m':m,'truth':truth,'obs':obs,'target':target,
                          'queries':queries,'optimal':optimal,'optimal_index':opt_index,
                          'entropy_before':e0,'expected_entropy':ents})
            made+=1
        assert made==TASKS_PER_FAMILY,(m,made)
    return tasks


def prompt(t,previous=None,feedback=None):
    obs='; '.join(f'{p}->{a}' for p,a in sorted(t['obs'].items())); qs=', '.join(t['queries'])
    p=(f'Hidden verified law family: value=(base[prefix]+offset[suffix]) mod {t["m"]}, gauge offset[X]=0. '
       f'Verified observations: {obs}. TARGET: {t["target"]}. Candidate extra queries: {qs}. '
       'Construct a compact comparative representation over ALL candidate queries. Rank them best-to-worst for reducing expected uncertainty of the TARGET. '
       'Return only JSON {"ranking":["Q1","Q2","Q3","Q4"]}.')
    if previous is not None:
        p+='\nYour previous ranking was: '+json.dumps(previous)
    if feedback=='RECHECK':
        p+='\nNo verifier information is available. Re-evaluate the ranking once from the original evidence.'
    elif feedback=='TOP_WRONG':
        p+='\nExternal verifier feedback: TOP_WRONG. This is the entire verifier message. It does not identify a better rival, score, outcome, target value, or representation cell. Repair the ranking from the original evidence.'
    elif feedback=='TOP_OK':
        p+='\nExternal verifier feedback: TOP_OK. Return your ranking.'
    return p


def normalize(raw,t):
    try: obj=json.loads(raw)
    except Exception: obj={}
    ranking=obj.get('ranking',[]) if isinstance(obj,dict) else []
    ranking=[q for q in ranking if q in t['queries']]
    for q in t['queries']:
        if q not in ranking: ranking.append(q)
    return ranking[:4]


def downstream(t,S,q):
    a=pred(t['truth'],q,t['m']); S2=update(S,q,a,t['m'])
    return {'correct':majority(S2,t['target'],t['m'])==pred(t['truth'],t['target'],t['m']),
            'entropy_after':target_entropy(S2,t['target'],t['m'])}


tasks=build_tasks()

# Exact pre-LLM channel audit. Candidate actions are canonical query indices 0..3.
# For each proposed index i, ask which optimal indices remain possible among frozen tasks
# on which i would receive TOP_WRONG.
channel_audit={}
for proposed_i in range(4):
    opts=sorted(set(t['optimal_index'] for t in tasks if t['optimal_index']!=proposed_i))
    channel_audit[str(proposed_i)]={'compatible_optimal_indices_after_TOP_WRONG':opts,
                                    'count':len(opts),'non_identifying':len(opts)>=2}
assert all(v['non_identifying'] for v in channel_audit.values()), channel_audit

rows=[]
for i,t in enumerate(tasks,1):
    print(f'[{i}/{len(tasks)}] {t["id"]}',flush=True)
    H=all_hypotheses(t['m']); S=survivors(H,t['obs'],t['m'])

    one=normalize(call(prompt(t),220),t); q1=one[0]
    rows.append({'task_id':t['id'],'m':t['m'],'arm':'ONE_SHOT_COMPARATIVE','query':q1,
                 'query_optimal':q1==t['optimal'],'ranking':one,**downstream(t,S,q1)})

    recheck=normalize(call(prompt(t,previous=one,feedback='RECHECK'),240),t); qr=recheck[0]
    rows.append({'task_id':t['id'],'m':t['m'],'arm':'RECHECK_CONTROL','query':qr,
                 'query_optimal':qr==t['optimal'],'ranking':recheck,**downstream(t,S,qr)})

    verdict='TOP_OK' if q1==t['optimal'] else 'TOP_WRONG'
    verified=normalize(call(prompt(t,previous=one,feedback=verdict),240),t); qv=verified[0]
    rows.append({'task_id':t['id'],'m':t['m'],'arm':'VERIFIED_BINARY','query':qv,
                 'query_optimal':qv==t['optimal'],'ranking':verified,'verifier_message':verdict,
                 **downstream(t,S,qv)})

# Score.
def summarize(arm):
    rr=[r for r in rows if r['arm']==arm]; n=len(rr)
    return {'n':n,'optimal':sum(r['query_optimal'] for r in rr),'optimal_rate':sum(r['query_optimal'] for r in rr)/n,
            'correct':sum(r['correct'] for r in rr),'accuracy':sum(r['correct'] for r in rr)/n,
            'zero_entropy':sum(r['entropy_after']<1e-12 for r in rr),
            'zero_entropy_rate':sum(r['entropy_after']<1e-12 for r in rr)/n}
summary={a:summarize(a) for a in ('ONE_SHOT_COMPARATIVE','RECHECK_CONTROL','VERIFIED_BINARY')}
wrong_initial=[t for t,r in zip(tasks,[r for r in rows if r['arm']=='ONE_SHOT_COMPARATIVE']) if not r['query_optimal']]
metadata={'schema':'verifier.binary.channel.v1','seed':SEED,'model':MODEL,'temperature':0,'n_tasks':len(tasks),
          'max_binary_repair_rounds':1,'feedback_payloads':['TOP_OK','TOP_WRONG'],
          'channel_audit':channel_audit,'initial_wrong_tasks':len(wrong_initial)}
(ROOT/'tasks.json').write_text(json.dumps([{k:v for k,v in t.items() if k!='truth'} for t in tasks],indent=2))
(ROOT/'answers.json').write_text(json.dumps(rows,indent=2))
(ROOT/'summary.json').write_text(json.dumps(summary,indent=2))
(ROOT/'metadata.json').write_text(json.dumps(metadata,indent=2))
print(json.dumps({'channel_audit':channel_audit,'summary':summary},indent=2))

# Frozen primary: binary verifier feedback must improve exact selection over both
# one-shot and equal-compute no-information recheck. Secondary: downstream accuracy
# must not be worse than recheck.
assert len(tasks)==48
assert summary['VERIFIED_BINARY']['optimal_rate'] > summary['ONE_SHOT_COMPARATIVE']['optimal_rate']
assert summary['VERIFIED_BINARY']['optimal_rate'] > summary['RECHECK_CONTROL']['optimal_rate']
assert summary['VERIFIED_BINARY']['accuracy'] >= summary['RECHECK_CONTROL']['accuracy']
print('PASS_VERIFIER_BINARY_CHANNEL_V1')
