import json, os, random, time, urllib.request
from pathlib import Path
ROOT=Path(__file__).parent
CASES=json.loads((ROOT/'cases.json').read_text())['cases']
MODEL=os.environ.get('UVRM_MODEL','gpt-4.1-mini'); TOKEN=os.environ['OPENAI_API_KEY']
URL='https://api.openai.com/v1/chat/completions'; ARMS=['GENERIC','RIVAL','COUNTERFACTUAL','VERIFIED_RESIDUAL']; SEED=20260824

def prompt(c,a):
    opts='\n'.join(f'{k}. {v}' for k,v in c['options'].items())
    base=f"EVIDENCE: {c['evidence']}\nLATENT ABSTRACTION: {c['latent']}\nCANDIDATE INTERVENTIONS:\n{opts}\n\nReturn exactly: CHOICE: <A|B|C|D>\nWHY: <one sentence>."
    if a=='GENERIC': return base+'\nChoose the best next experiment.'
    if a=='RIVAL': return base+'\nIdentify the strongest simpler rival to the latent abstraction and choose the intervention that best separates them.'
    if a=='COUNTERFACTUAL': return base+'\nFor each plausible rival, mentally predict how the candidate interventions would differ under the latent abstraction versus the rival; choose the intervention with the clearest differential outcome.'
    return base+'\nApply verified-residual discipline: strongest live rival, closure-before-invention, smallest deciding intervention, matched control/ablation, and choose the option whose outcomes most change the next lawful action.'

def call(p):
    body=json.dumps({'model':MODEL,'messages':[{'role':'user','content':p}],'temperature':0,'max_tokens':180}).encode()
    req=urllib.request.Request(URL,data=body,headers={'Authorization':f'Bearer {TOKEN}','Content-Type':'application/json'})
    last=None
    for i in range(4):
        try:
            with urllib.request.urlopen(req,timeout=90) as r: o=json.loads(r.read().decode())
            return o['choices'][0]['message']['content']
        except Exception as e: last=e; time.sleep(2**i)
    raise last
jobs=[(c,a) for c in CASES for a in ARMS]; random.Random(SEED).shuffle(jobs)
out=[]
for i,(c,a) in enumerate(jobs,1):
    print(f'[{i}/{len(jobs)}] {c["id"]} {a}',flush=True); out.append({'case_id':c['id'],'arm':a,'answer':call(prompt(c,a))})
(ROOT/'answers.json').write_text(json.dumps(out,indent=2)); (ROOT/'run_metadata.json').write_text(json.dumps({'model':MODEL,'temperature':0,'max_tokens':180,'calls':len(jobs),'seed':SEED},indent=2))