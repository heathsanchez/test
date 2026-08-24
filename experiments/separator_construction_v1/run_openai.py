import json, os, random, time, urllib.request
from pathlib import Path

ROOT=Path(__file__).parent
CASES=json.loads((ROOT/'cases.json').read_text())['cases']
MODEL=os.environ.get('UVRM_MODEL','gpt-4.1-mini')
TOKEN=os.environ['OPENAI_API_KEY']
URL='https://api.openai.com/v1/chat/completions'
ARMS=['GENERIC','RIVAL_FIRST','COUNTERFACTUAL_WORLDS','VERIFIED_RESIDUAL']
SEED=20260824

def prompt(c,a):
    allowed=c['allowed']
    grammar=("TEST must be exactly probe(<probe>,<control>,<metric>) using only these tokens:\n"
             f"probe={allowed['probe']}\ncontrol={allowed['control']}\nmetric={allowed['metric']}\n")
    base=(f"EVIDENCE: {c['evidence']}\nLATENT ABSTRACTION (assume correct): {c['latent']}\n\n"
          "Return exactly two lines:\nRIVAL: <strongest simpler alternative explanation>\nTEST: probe(<probe>,<control>,<metric>)\n"
          + grammar)
    if a=='GENERIC': return base+"Construct the best next experiment."
    if a=='RIVAL_FIRST': return base+"First identify the strongest simpler rival, then choose the smallest experiment whose outcome should differ if the latent abstraction is right versus that rival."
    if a=='COUNTERFACTUAL_WORLDS': return base+"Mentally simulate both worlds: one where the latent abstraction is causal and one where the strongest simpler rival is causal. Choose the cheapest intervention that should produce different observable outcomes between those worlds."
    return base+"Use verified-residual discipline: state the strongest live rival; inspect closure before invention; choose the smallest deciding intervention under the given DSL whose outcomes differ across the two live worlds; prefer matched/ablation controls when needed."

def call(p):
    body=json.dumps({'model':MODEL,'messages':[{'role':'user','content':p}],'temperature':0,'max_tokens':220}).encode()
    req=urllib.request.Request(URL,data=body,headers={'Authorization':f'Bearer {TOKEN}','Content-Type':'application/json'})
    last=None
    for i in range(4):
        try:
            with urllib.request.urlopen(req,timeout=90) as r: obj=json.loads(r.read().decode())
            return obj['choices'][0]['message']['content']
        except Exception as e:
            last=e; time.sleep(2**i)
    raise last

jobs=[(c,a) for c in CASES for a in ARMS]
random.Random(SEED).shuffle(jobs)
out=[]
for i,(c,a) in enumerate(jobs,1):
    print(f'[{i}/{len(jobs)}] {c["id"]} {a}',flush=True)
    out.append({'case_id':c['id'],'arm':a,'answer':call(prompt(c,a))})
(ROOT/'answers.json').write_text(json.dumps(out,indent=2))
(ROOT/'run_metadata.json').write_text(json.dumps({'schema':'separator.construction.v1.run','model':MODEL,'temperature':0,'max_tokens':220,'calls':len(jobs),'seed':SEED,'arms':ARMS},indent=2))
