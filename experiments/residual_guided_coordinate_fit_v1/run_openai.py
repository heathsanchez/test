import json, os, random, time, urllib.request
from itertools import product
from pathlib import Path

ROOT=Path(__file__).parent
DATA=json.loads((ROOT.parent/'law_induction_v1b'/'cases.json').read_text())
MODEL=os.environ.get('UVRM_MODEL','gpt-4.1-mini')
TOKEN=os.environ['OPENAI_API_KEY']
URL='https://api.openai.com/v1/chat/completions'
CODES={'J':0,'K':1,'L':2,'M':3}; INV={v:k for k,v in CODES.items()}
SEED=2026082504
ROUNDS=4


def predict(law,pair):
    if not isinstance(law,dict) or law.get('kind')!='add_mod4': return None
    b=law.get('base',{}); o=law.get('offset',{})
    if len(pair)!=2 or pair[0] not in b or pair[1] not in o: return None
    try: return INV[(int(b[pair[0]])+int(o[pair[1]]))%4]
    except Exception: return None


def obs(c):
    out=[]
    for s in c['observations']:
        p,a=s.split('->'); out.append((p,a))
    return out


def fit(c,law):
    rows=[]
    for p,a in obs(c):
        pr=predict(law,p); rows.append({'pair':p,'pred':pr,'truth':a,'ok':pr==a})
    return sum(r['ok'] for r in rows), rows


def call(prompt):
    body=json.dumps({'model':MODEL,'messages':[{'role':'user','content':prompt}], 'temperature':0, 'max_tokens':180, 'response_format':{'type':'json_object'}}).encode()
    req=urllib.request.Request(URL,data=body,headers={'Authorization':f'Bearer {TOKEN}','Content-Type':'application/json'})
    last=None
    for i in range(4):
        try:
            with urllib.request.urlopen(req,timeout=90) as r: obj=json.loads(r.read().decode())
            return obj['choices'][0]['message']['content']
        except Exception as e:
            last=e; time.sleep(2**i)
    raise last


def schema_prompt(c):
    return (
        'The verified law family is fixed: action=(base[prefix]+offset[suffix]) mod 4, '
        'with J=0,K=1,L=2,M=3. Infer only the latent coordinates. '
        'Return ONLY JSON exactly like {"kind":"add_mod4","base":{"A":0,"B":1,"C":2,"D":3},"offset":{"X":0,"Y":1}}. '
        'All coordinate values must be integers 0..3.\nOBSERVATIONS: ' + '; '.join(c['observations'])
    )


def parse(raw):
    try: return json.loads(raw)
    except Exception: return None


def csp(c):
    # Gauge-fix X=0; exhaustive 4^5 search over A-D and Y.
    best=None
    for vals in product(range(4), repeat=5):
        law={'kind':'add_mod4','base':dict(zip('ABCD',vals[:4])),'offset':{'X':0,'Y':vals[4]}}
        k,_=fit(c,law)
        if k==7: return law
        if best is None or k>best[0]: best=(k,law)
    return best[1]

# External evaluator sanity gate.
for c in DATA['cases']:
    law=csp(c)
    k,_=fit(c,law)
    assert k==7
    assert predict(law,c['query'])==c['correct']
print('CSP_ORACLE_GATE_PASS_8_OF_8',flush=True)

jobs=[]
for c in DATA['cases']:
    jobs.extend([(c,'ONE_SHOT'),(c,'RANDOM_RESTART'),(c,'RESIDUAL_GUIDED')])
random.Random(SEED).shuffle(jobs)
out=[]

for ji,(c,arm) in enumerate(jobs,1):
    print(f'[{ji}/{len(jobs)}] {c["id"]} {arm}',flush=True)
    history=[]
    best=(-1,None,None)
    rounds=1 if arm=='ONE_SHOT' else ROUNDS
    for r in range(1,rounds+1):
        p=schema_prompt(c)
        if arm=='RANDOM_RESTART':
            p += f'\nThis is independent proposal {r} of {ROUNDS}. Produce your best coordinates from the observations only; you receive no verifier feedback.'
        elif arm=='RESIDUAL_GUIDED' and history:
            prev=history[-1]
            mism=[x for x in prev['rows'] if not x['ok']]
            p += '\nPrevious candidate: '+json.dumps(prev['law'],sort_keys=True)
            p += '\nVERIFIED RESIDUAL MISMATCHES: '+json.dumps(mism,sort_keys=True)
            p += '\nRevise the smallest set of coordinates needed to eliminate these verified mismatches. Preserve coordinates not implicated unless required by consistency.'
        elif arm=='RESIDUAL_GUIDED':
            p += '\nThis is round 1. Propose coordinates; later rounds will receive exact verifier mismatches.'
        raw=call(p); law=parse(raw); k,rows=fit(c,law)
        rec={'round':r,'raw':raw,'law':law,'train_correct':k,'rows':rows}
        history.append(rec)
        if k>best[0]: best=(k,law,r)
        if arm=='RESIDUAL_GUIDED' and k==7: break
    retained=best[1]
    out.append({'case_id':c['id'],'arm':arm,'history':history,'best_train':best[0],'best_round':best[2],
                'retained_law':retained,'heldout_pred':predict(retained,c['query']),'heldout_truth':c['correct']})

for c in DATA['cases']:
    law=csp(c); k,_=fit(c,law)
    out.append({'case_id':c['id'],'arm':'CSP_ORACLE','history':[],'best_train':k,'best_round':0,
                'retained_law':law,'heldout_pred':predict(law,c['query']),'heldout_truth':c['correct']})

(ROOT/'answers.json').write_text(json.dumps(out,indent=2))
(ROOT/'run_metadata.json').write_text(json.dumps({'schema':'residual.guided.coordinate.fit.v1','model':MODEL,'temperature':0,'rounds':ROUNDS,'seed':SEED,'application':'deterministic_python'},indent=2))
