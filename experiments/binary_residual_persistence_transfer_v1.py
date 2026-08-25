import json, math, os, random, time, urllib.request
from collections import Counter, defaultdict
from itertools import product
from pathlib import Path

MODEL=os.environ.get('UVRM_MODEL','gpt-4.1-mini')
TOKEN=os.environ['OPENAI_API_KEY']
URL='https://api.openai.com/v1/chat/completions'
SEED=2026082515
RNG=random.Random(SEED)
PREFIXES='ABCD'; SUFFIXES='XYZ'
ACQ_FAMILIES=[2,3]; HELDOUT_FAMILIES=[5]
ACQ_PER_FAMILY=12; HELDOUT_PER_FAMILY=16
ROOT=Path('artifacts/binary_residual_persistence_transfer_v1'); ROOT.mkdir(parents=True,exist_ok=True)

def all_hypotheses(m):
    return [(dict(zip(PREFIXES,v[:4])),{'X':0,'Y':v[4],'Z':v[5]}) for v in product(range(m),repeat=6)]
def pred(h,p,m): return (h[0][p[0]]+h[1][p[1]])%m
def entropy(vals):
    c=Counter(vals); n=len(vals)
    return -sum((v/n)*math.log2(v/n) for v in c.values()) if n else 0.0
def target_entropy(H,t,m): return entropy([pred(h,t,m) for h in H])
def survivors(H,obs,m): return [h for h in H if all(pred(h,p,m)==a for p,a in obs.items())]
def expected_target_entropy(H,q,t,m):
    groups=defaultdict(list)
    for h in H: groups[pred(h,q,m)].append(h)
    return sum(len(g)/len(H)*target_entropy(g,t,m) for g in groups.values())
def update(H,q,a,m): return [h for h in H if pred(h,q,m)==a]
def majority(H,t,m):
    c=Counter(pred(h,t,m) for h in H); mx=max(c.values()); return min(k for k,v in c.items() if v==mx)
def call(prompt,max_tokens=320):
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

def build_tasks(families,n_each,label):
    tasks=[]; pairs=[a+b for a in PREFIXES for b in SUFFIXES]
    for m in families:
        H=all_hypotheses(m); made=0; attempts=0
        while made<n_each and attempts<150000:
            attempts+=1; truth=RNG.choice(H); sh=pairs[:]; RNG.shuffle(sh)
            k=RNG.choice([4,5,6]); obs_pairs=sh[:k]; rem=[p for p in pairs if p not in obs_pairs]
            if len(rem)<5: continue
            target=rem[0]; queries=rem[1:5]; obs={p:pred(truth,p,m) for p in obs_pairs}; S=survivors(H,obs,m)
            if len(S)<4 or len(S)>5000: continue
            ents={q:expected_target_entropy(S,q,target,m) for q in queries}; best=min(ents.values()); worst=max(ents.values())
            if best>1e-12 or worst-best<0.25: continue
            optimal=sorted(queries,key=lambda q:(ents[q],q))[0]
            tasks.append({'id':f'{label}_m{m}_{made:02d}','m':m,'truth':truth,'obs':obs,'target':target,'queries':queries,'expected_entropy':ents,'optimal':optimal}); made+=1
        assert made==n_each,(m,made)
    return tasks

def base_prompt(t,extra=''):
    obs='; '.join(f'{p}->{a}' for p,a in sorted(t['obs'].items())); qs=', '.join(t['queries'])
    return (f'Hidden verified law family: value=(base[prefix]+offset[suffix]) mod {t["m"]}, gauge offset[X]=0. Verified observations: {obs}. '
            f'TARGET: {t["target"]}. Candidate extra queries: {qs}. Rank all four queries best-to-worst for reducing expected uncertainty of TARGET. '
            f'{extra} Return only JSON {{"ranking":["Q1","Q2","Q3","Q4"]}}.')

def norm(raw,t):
    try: obj=json.loads(raw)
    except Exception: obj={}
    r=[q for q in obj.get('ranking',[]) if q in t['queries']]
    for q in t['queries']:
        if q not in r: r.append(q)
    return r[:4]

def downstream(t,q):
    H=all_hypotheses(t['m']); S=survivors(H,t['obs'],t['m']); a=pred(t['truth'],q,t['m']); S2=update(S,q,a,t['m']); tv=pred(t['truth'],t['target'],t['m']); tp=majority(S2,t['target'],t['m'])
    return {'correct':tp==tv,'zero_entropy':target_entropy(S2,t['target'],t['m'])<1e-12}

acq=build_tasks(ACQ_FAMILIES,ACQ_PER_FAMILY,'acq')
held=build_tasks(HELDOUT_FAMILIES,HELDOUT_PER_FAMILY,'held')

# Acquisition: one-shot -> one non-identifying binary residual -> one repair.
lessons=[]; acq_rows=[]
for i,t in enumerate(acq,1):
    print(f'[ACQ {i}/{len(acq)}] {t["id"]}',flush=True)
    r1=norm(call(base_prompt(t),220),t); q1=r1[0]; fb='TOP_OK' if q1==t['optimal'] else 'TOP_WRONG'
    r2=norm(call(base_prompt(t,extra=f'Previous ranking: {r1}. External verifier says only: {fb}. It gives no rival, score, outcome, target value, or hidden state. Reconsider once.'),260),t); q2=r2[0]
    lessons.append({'m':t['m'],'initial_position':t['queries'].index(q1),'feedback':fb,'repaired_position':t['queries'].index(q2),'changed':q1!=q2,'repair_optimal':q2==t['optimal']})
    acq_rows.append({'task':t['id'],'initial_optimal':q1==t['optimal'],'feedback':fb,'repair_optimal':q2==t['optimal']})

# Compress acquisition episodes into a reusable, task-agnostic rule. No concrete pair names, moduli, answers, or task IDs are permitted.
lesson_prompt=('You are given acquisition summaries from a verifier-guided query-selection process. Derive ONE compact reusable decision rule for future tasks of the same structural kind. '
               'The rule must describe how to compare candidate queries from observations and target relevance; it must not mention concrete task IDs, pair names, specific moduli, answer values, or memorized positions. '
               'Return JSON {"rule":"..."} with <=90 words. Summaries: '+json.dumps(lessons))
try: retained_rule=json.loads(call(lesson_prompt,180)).get('rule','')
except Exception: retained_rule=''
assert retained_rule and len(retained_rule.split())<=110

# Sham retention: same length/style instruction, but based only on initial rankings and without verifier residuals.
sham_prompt=('Create ONE compact generic query-selection rule from these acquisition summaries, but you are not given verifier feedback. '
             'Do not mention concrete task IDs, pair names, specific moduli, answer values, or memorized positions. Return JSON {"rule":"..."} with <=90 words. Summaries: '+json.dumps([{k:v for k,v in x.items() if k not in ('feedback','repair_optimal')} for x in lessons]))
try: sham_rule=json.loads(call(sham_prompt,180)).get('rule','')
except Exception: sham_rule=''
assert sham_rule

rows=[]
for i,t in enumerate(held,1):
    print(f'[HELD {i}/{len(held)}] {t["id"]}',flush=True)
    # Cold one shot
    cold=norm(call(base_prompt(t),220),t); qc=cold[0]; rows.append({'task':t['id'],'arm':'COLD','optimal':qc==t['optimal'],**downstream(t,qc)})
    # Equal-compute recheck, no retained state
    re=norm(call(base_prompt(t,extra=f'Previous ranking: {cold}. Recheck carefully once, with no external verifier feedback.'),260),t); qr=re[0]; rows.append({'task':t['id'],'arm':'RECHECK','optimal':qr==t['optimal'],**downstream(t,qr)})
    # Retained verified rule, no verifier feedback on heldout
    rr=norm(call(base_prompt(t,extra='Reusable rule learned earlier from separate acquisition tasks: '+retained_rule+' Apply it. No verifier feedback is available on this task.'),260),t); qv=rr[0]; rows.append({'task':t['id'],'arm':'RETAINED_VERIFIED_RULE','optimal':qv==t['optimal'],**downstream(t,qv)})
    # Sham retained rule
    sr=norm(call(base_prompt(t,extra='Reusable rule learned earlier from separate acquisition tasks: '+sham_rule+' Apply it. No verifier feedback is available on this task.'),260),t); qs=sr[0]; rows.append({'task':t['id'],'arm':'SHAM_RULE','optimal':qs==t['optimal'],**downstream(t,qs)})
    # Targeted ablation: explicit removal of retained rule, same wrapper language
    ab=norm(call(base_prompt(t,extra='The previously retained acquisition rule has been ablated. Solve without using any retained rule and with no verifier feedback.'),260),t); qa=ab[0]; rows.append({'task':t['id'],'arm':'ABLATION','optimal':qa==t['optimal'],**downstream(t,qa)})

summary={}
for arm in sorted(set(r['arm'] for r in rows)):
    z=[r for r in rows if r['arm']==arm]; summary[arm]={'n':len(z),'optimal':sum(r['optimal'] for r in z),'optimal_rate':sum(r['optimal'] for r in z)/len(z),'correct':sum(r['correct'] for r in z),'accuracy':sum(r['correct'] for r in z)/len(z),'zero_entropy':sum(r['zero_entropy'] for r in z),'zero_entropy_rate':sum(r['zero_entropy'] for r in z)/len(z)}
out={'seed':SEED,'model':MODEL,'acquisition_n':len(acq),'heldout_n':len(held),'acquisition_families':ACQ_FAMILIES,'heldout_families':HELDOUT_FAMILIES,'retained_rule':retained_rule,'sham_rule':sham_rule,'acquisition_rows':acq_rows,'summary':summary,'rows':rows}
(ROOT/'results.json').write_text(json.dumps(out,indent=2)); print(json.dumps({'retained_rule':retained_rule,'sham_rule':sham_rule,'summary':summary},indent=2),flush=True)

# Frozen primary: source-distinct heldout mod-5, no verifier feedback.
v=summary['RETAINED_VERIFIED_RULE']['optimal_rate']; c=summary['COLD']['optimal_rate']; r=summary['RECHECK']['optimal_rate']; s=summary['SHAM_RULE']['optimal_rate']; a=summary['ABLATION']['optimal_rate']
assert v>c and v>r and v>s
assert v>a
assert summary['RETAINED_VERIFIED_RULE']['accuracy']>=summary['RECHECK']['accuracy']
print('PASS_BINARY_RESIDUAL_PERSISTENCE_TRANSFER_V1')
