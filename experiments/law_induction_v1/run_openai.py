import json, os, random, time, urllib.request
from pathlib import Path

ROOT=Path(__file__).parent
DATA=json.loads((ROOT/'cases.json').read_text())
MODEL=os.environ.get('UVRM_MODEL','gpt-4.1-mini')
TOKEN=os.environ['OPENAI_API_KEY']
URL='https://api.openai.com/v1/chat/completions'
ARMS=['RAW_RECONSTRUCT','JOIN_DOTS','RIVAL_SEPARATOR','VERIFIED_RESIDUAL','ORACLE_LAW']
SEED=2026082407

def call(prompt,max_tokens):
    body=json.dumps({'model':MODEL,'messages':[{'role':'user','content':prompt}],'temperature':0,'max_tokens':max_tokens}).encode()
    req=urllib.request.Request(URL,data=body,headers={'Authorization':f'Bearer {TOKEN}','Content-Type':'application/json'})
    last=None
    for i in range(4):
        try:
            with urllib.request.urlopen(req,timeout=90) as r: obj=json.loads(r.read().decode())
            return obj['choices'][0]['message']['content']
        except Exception as e:
            last=e; time.sleep(2**i)
    raise last

def induction_prompt(c,arm):
    obs='; '.join(c['observations'])
    base=f'You are given verified observations from one arbitrary symbolic world. Infer one reusable law sufficient for an unseen combination. Do not answer the held-out query yet.\nOBSERVATIONS: {obs}\n'
    if arm=='RAW_RECONSTRUCT': tail='Infer the best reusable rule. Return only LAW: <concise rule>.'
    elif arm=='JOIN_DOTS': tail='Join the dispersed observations into the latent common structure. Return only LAW: <concise rule>.'
    elif arm=='RIVAL_SEPARATOR': tail='Form the strongest simpler rival rule, compare its predictions with the observations, and retain the law that best separates the rivals. Return only LAW: <concise retained rule>.'
    elif arm=='VERIFIED_RESIDUAL': tail='Use the verified residual process: preserve live rivals, identify mismatches each rival leaves, prefer the smallest rule consistent with all verified observations, and do not add structure not forced by the evidence. Return only LAW: <concise retained rule>.'
    else: return 'LAW: '+c['oracle']
    return base+tail

def application_prompt(c,law):
    return f'Use only the retained law below to answer the held-out query in this arbitrary world. Return exactly CHOICE: <J|K|L|M>.\nRETAINED LAW:\n{law}\nHELD-OUT QUERY: {c["query"]}'

jobs=[(c,a) for c in DATA['cases'] for a in ARMS]
random.Random(SEED).shuffle(jobs)
out=[]
for i,(c,a) in enumerate(jobs,1):
    print(f'[{i}/{len(jobs)}] {c["id"]} {a}',flush=True)
    law=induction_prompt(c,a) if a=='ORACLE_LAW' else call(induction_prompt(c,a),180)
    ans=call(application_prompt(c,law),60)
    out.append({'case_id':c['id'],'arm':a,'law':law,'answer':ans})
(ROOT/'answers.json').write_text(json.dumps(out,indent=2))
(ROOT/'run_metadata.json').write_text(json.dumps({'schema':'law.induction.v1.run','model':MODEL,'temperature':0,'induction_max_tokens':180,'application_max_tokens':60,'calls':len(jobs)*2-len(DATA['cases']),'seed':SEED,'arms':ARMS},indent=2))
