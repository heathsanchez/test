import json, os, random, time, urllib.request
from pathlib import Path

ROOT=Path(__file__).parent
DATA=json.loads((ROOT.parent/'law_induction_v1b'/'cases.json').read_text())
MODEL=os.environ.get('UVRM_MODEL','gpt-4.1-mini')
TOKEN=os.environ['OPENAI_API_KEY']
URL='https://api.openai.com/v1/chat/completions'
ARMS=['RAW_RECONSTRUCT','JOIN_DOTS','RIVAL_SEPARATOR','VERIFIED_RESIDUAL']
SEED=2026082503
CODES={'J':0,'K':1,'L':2,'M':3}; INV={v:k for k,v in CODES.items()}

def predict(law,pair):
    if not isinstance(law,dict): return None
    kind=law.get('kind')
    if kind=='lookup':
        m=law.get('map',{})
        x=m.get(pair)
        return x if x in CODES else None
    if kind=='add_mod4':
        b=law.get('base',{}); o=law.get('offset',{})
        if len(pair)!=2 or pair[0] not in b or pair[1] not in o: return None
        try:
            z=(int(b[pair[0]])+int(o[pair[1]]))%4
        except Exception:
            return None
        return INV.get(z)
    return None

def oracle_law(c):
    # Parse the frozen oracle text into executable parameters.
    import re
    bs={k:int(v) for k,v in re.findall(r'([ABCD])=(\d)',c['oracle'])}
    os_={k:int(v) for k,v in re.findall(r'([XY])=(\d)',c['oracle'])}
    return {'kind':'add_mod4','base':bs,'offset':os_}

def truth_obs(c):
    out=[]
    for s in c['observations']:
        pair,act=s.split('->')
        out.append((pair,act))
    return out

def call(prompt):
    body=json.dumps({'model':MODEL,'messages':[{'role':'user','content':prompt}],'temperature':0,'max_tokens':220,'response_format':{'type':'json_object'}}).encode()
    req=urllib.request.Request(URL,data=body,headers={'Authorization':f'Bearer {TOKEN}','Content-Type':'application/json'})
    last=None
    for i in range(4):
        try:
            with urllib.request.urlopen(req,timeout=90) as r: obj=json.loads(r.read().decode())
            return obj['choices'][0]['message']['content']
        except Exception as e:
            last=e; time.sleep(2**i)
    raise last

def prompt(c,arm):
    obs='; '.join(c['observations'])
    schema='Return ONLY JSON using exactly one executable kind. Either {"kind":"lookup","map":{"AX":"J",...}} or {"kind":"add_mod4","base":{"A":0,"B":1,"C":2,"D":3},"offset":{"X":0,"Y":1}}. Action codes are J=0,K=1,L=2,M=3. Values may differ from the example. No prose.'
    base=f'You are given verified observations from one arbitrary symbolic world. Infer the smallest reusable law that explains them and can predict an unseen pair. OBSERVATIONS: {obs}\n{schema}\n'
    if arm=='RAW_RECONSTRUCT': tail='Infer the best reusable law.'
    elif arm=='JOIN_DOTS': tail='Join the dispersed observations into their latent common structure before choosing the law.'
    elif arm=='RIVAL_SEPARATOR': tail='Compare the strongest simple rival explanations, especially memorization versus a compositional rule, and retain the law whose predictions best account for all observations and support the unseen pair.'
    else: tail='Use the verified residual process: keep live rivals, inspect the residual each leaves, prefer closure/composition before memorization, and retain the smallest law forced by all verified observations that supports lawful future prediction.'
    return base+tail

# Deterministic oracle gate: validates evaluator and frozen cases without an LLM.
for c in DATA['cases']:
    law=oracle_law(c)
    for p,a in truth_obs(c):
        assert predict(law,p)==a, (c['id'],p,predict(law,p),a)
    assert predict(law,c['query'])==c['correct'], (c['id'],'heldout')
print('ORACLE_DETERMINISTIC_GATE_PASS_8_OF_8',flush=True)

jobs=[(c,a) for c in DATA['cases'] for a in ARMS]
random.Random(SEED).shuffle(jobs)
out=[]
for i,(c,a) in enumerate(jobs,1):
    print(f'[{i}/{len(jobs)}] {c["id"]} {a}',flush=True)
    raw=call(prompt(c,a))
    try: law=json.loads(raw)
    except Exception: law=None
    train=sum(predict(law,p)==act for p,act in truth_obs(c)) if law is not None else 0
    held=predict(law,c['query']) if law is not None else None
    out.append({'case_id':c['id'],'arm':a,'raw':raw,'law':law,'train_correct':train,'heldout_pred':held,'heldout_truth':c['correct']})
for c in DATA['cases']:
    law=oracle_law(c)
    out.append({'case_id':c['id'],'arm':'ORACLE_LAW','raw':json.dumps(law),'law':law,'train_correct':7,'heldout_pred':predict(law,c['query']),'heldout_truth':c['correct']})
(ROOT/'answers.json').write_text(json.dumps(out,indent=2))
(ROOT/'run_metadata.json').write_text(json.dumps({'schema':'law.induction.v1d.run','model':MODEL,'temperature':0,'max_tokens':220,'seed':SEED,'arms':ARMS+['ORACLE_LAW'],'application':'deterministic_python'},indent=2))
