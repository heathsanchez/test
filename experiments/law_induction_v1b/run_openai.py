import json, os, random, re, time, urllib.request
from pathlib import Path

ROOT=Path(__file__).parent
DATA=json.loads((ROOT/'cases.json').read_text())
MODEL=os.environ.get('UVRM_MODEL','gpt-4.1-mini')
TOKEN=os.environ['OPENAI_API_KEY']
URL='https://api.openai.com/v1/chat/completions'
ARMS=['RAW_RECONSTRUCT','JOIN_DOTS','RIVAL_SEPARATOR','VERIFIED_RESIDUAL']
SEED=2026082501

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
    else: tail='Use the verified residual process: preserve live rivals, identify mismatches each rival leaves, prefer the smallest rule consistent with all verified observations, and do not add structure not forced by the evidence. Return only LAW: <concise retained rule>.'
    return base+tail

def application_prompt(c,law):
    return (
        'Use only the retained law to answer the held-out query. '
        'Output exactly one line of the form CHOICE: J, CHOICE: K, CHOICE: L, or CHOICE: M. '
        'Do not explain, calculate aloud, or output any other text.\n'
        f'RETAINED LAW:\n{law}\nHELD-OUT QUERY: {c["query"]}'
    )

def parsed_choice(text):
    m=re.fullmatch(r'\s*CHOICE:\s*([JKLM])\s*',text.upper())
    return m.group(1) if m else None

# Measurement validity gate: oracle must work through the exact application boundary.
out=[]
print('ORACLE_GATE_BEGIN', flush=True)
for c in DATA['cases']:
    law='LAW: '+c['oracle']
    ans=call(application_prompt(c,law),20)
    pred=parsed_choice(ans)
    ok=(pred==c['correct'])
    print(f'ORACLE_GATE {c["id"]} pred={pred} truth={c["correct"]} ok={ok}',flush=True)
    out.append({'case_id':c['id'],'arm':'ORACLE_LAW','law':law,'answer':ans})
if any(parsed_choice(x['answer']) != next(c['correct'] for c in DATA['cases'] if c['id']==x['case_id']) for x in out):
    (ROOT/'measurement_invalid.json').write_text(json.dumps({'status':'MEASUREMENT_INVALID','oracle_rows':out},indent=2))
    raise SystemExit('MEASUREMENT_INVALID_ORACLE_GATE')
print('ORACLE_GATE_PASS_8_OF_8', flush=True)

jobs=[(c,a) for c in DATA['cases'] for a in ARMS]
random.Random(SEED).shuffle(jobs)
for i,(c,a) in enumerate(jobs,1):
    print(f'[{i}/{len(jobs)}] {c["id"]} {a}',flush=True)
    law=call(induction_prompt(c,a),180)
    ans=call(application_prompt(c,law),20)
    out.append({'case_id':c['id'],'arm':a,'law':law,'answer':ans})
(ROOT/'answers.json').write_text(json.dumps(out,indent=2))
(ROOT/'run_metadata.json').write_text(json.dumps({'schema':'law.induction.v1b.run','model':MODEL,'temperature':0,'induction_max_tokens':180,'application_max_tokens':20,'oracle_gate':'8/8 required before scientific arms','seed':SEED,'arms':['ORACLE_LAW']+ARMS},indent=2))
