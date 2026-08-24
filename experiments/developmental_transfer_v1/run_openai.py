import json, os, random, time, urllib.request
from pathlib import Path

ROOT = Path(__file__).parent
DATA = json.loads((ROOT/'cases.json').read_text())
MODEL = os.environ.get('UVRM_MODEL','gpt-4.1-mini')
TOKEN = os.environ['OPENAI_API_KEY']
URL = 'https://api.openai.com/v1/chat/completions'
ARMS = ['COLD','RAW_EPISODE','PROSE_LAW','STRUCTURED_LAW','WRONG_LAW']
SEED = 2026082406

def memory(case, arm):
    if arm == 'COLD': return 'NO RETAINED EPISODE STATE.'
    if arm == 'RAW_EPISODE': return 'RETAINED EPISODE RECORD:\n'+case['raw']
    if arm == 'PROSE_LAW': return 'RETAINED VERIFIED LAW:\n'+case['prose']
    if arm == 'STRUCTURED_LAW': return 'RETAINED VERIFIED STATE:\n'+case['structured']
    return 'RETAINED VERIFIED STATE:\n'+case['wrong']

def prompt(case, arm):
    opts='\n'.join(f'{k}) {v}' for k,v in case['options'].items())
    return ('You are operating in an arbitrary synthetic world. World-specific laws are not inferable from ordinary meanings. '
            'Use only retained state if present. Return exactly one line: CHOICE: <J|K|L|M>.\n\n'+memory(case,arm)+
            '\n\nQUERY:\n'+case['query']+'\n\nACTIONS:\n'+opts)

def call(p):
    body=json.dumps({'model':MODEL,'messages':[{'role':'user','content':p}], 'temperature':0,'max_tokens':48}).encode()
    req=urllib.request.Request(URL,data=body,headers={'Authorization':f'Bearer {TOKEN}','Content-Type':'application/json'})
    last=None
    for i in range(4):
        try:
            with urllib.request.urlopen(req,timeout=90) as r:
                obj=json.loads(r.read().decode())
            return obj['choices'][0]['message']['content']
        except Exception as e:
            last=e; time.sleep(2**i)
    raise last

jobs=[(c,a) for c in DATA['cases'] for a in ARMS]
random.Random(SEED).shuffle(jobs)
answers=[]
for i,(case,arm) in enumerate(jobs,1):
    print(f'[{i}/{len(jobs)}] {case["id"]} {arm}',flush=True)
    answers.append({'case_id':case['id'],'arm':arm,'answer':call(prompt(case,arm))})
(ROOT/'answers.json').write_text(json.dumps(answers,indent=2))
(ROOT/'run_metadata.json').write_text(json.dumps({'schema':'developmental.transfer.v1.run','model':MODEL,'temperature':0,'max_tokens':48,'calls':len(jobs),'seed':SEED,'arms':ARMS},indent=2))