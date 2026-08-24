import json, os, random, time, urllib.request
from pathlib import Path

ROOT = Path(__file__).parent
DATA = json.loads((ROOT / 'cases.json').read_text())
MODEL = os.environ.get('UVRM_MODEL', 'gpt-4.1-mini')
TOKEN = os.environ['OPENAI_API_KEY']
URL = 'https://api.openai.com/v1/chat/completions'
ARMS = ['RAW_OUTCOME','PROSE_MEMORY','STRUCTURED_STATE','STRUCTURED_ABLATION']
SEED = 2026082406


def memory_block(case, arm):
    raw = 'PRIOR VERIFIED EPISODE:\n' + case['raw_outcome']
    if arm == 'RAW_OUTCOME':
        return raw
    if arm == 'PROSE_MEMORY':
        return raw + '\n\nRETAINED LESSON:\n' + case['prose_memory']
    if arm == 'STRUCTURED_STATE':
        return raw + '\n\nRETAINED VERIFIED STATE:\n' + case['structured_state']
    return raw + '\n\nRETAINED VERIFIED STATE:\n' + case['ablated_state']


def prompt(case, arm):
    opts = '\n'.join(f'{k}) {v}' for k,v in case['options'].items())
    return (
        'You have one short decision cycle. Use only the supplied prior state and the new problem. '
        'Choose the single best action. Return exactly: CHOICE: <A|B|C|D>.\n\n'
        + memory_block(case, arm)
        + '\n\nNEW SURFACE-DISJOINT PROBLEM:\n' + case['later_problem']
        + '\n\nACTIONS:\n' + opts
    )


def call(p):
    body = json.dumps({
        'model': MODEL,
        'messages': [{'role':'user','content':p}],
        'temperature': 0,
        'max_tokens': 80
    }).encode()
    req = urllib.request.Request(URL, data=body, headers={
        'Authorization': f'Bearer {TOKEN}',
        'Content-Type': 'application/json'
    })
    last = None
    for i in range(4):
        try:
            with urllib.request.urlopen(req, timeout=90) as r:
                obj = json.loads(r.read().decode())
            return obj['choices'][0]['message']['content']
        except Exception as e:
            last = e
            time.sleep(2 ** i)
    raise last

jobs = [(c,a) for c in DATA['cases'] for a in ARMS]
random.Random(SEED).shuffle(jobs)
answers = []
for i,(case,arm) in enumerate(jobs,1):
    print(f'[{i}/{len(jobs)}] {case["id"]} {arm}', flush=True)
    ans = call(prompt(case, arm))
    answers.append({'case_id':case['id'],'domain':case['domain'],'arm':arm,'answer':ans})

(ROOT / 'answers.json').write_text(json.dumps(answers, indent=2))
(ROOT / 'run_metadata.json').write_text(json.dumps({
    'schema':'representation.change.v2.run',
    'model':MODEL,
    'provider':'openai',
    'temperature':0,
    'max_tokens':80,
    'calls':len(jobs),
    'seed':SEED,
    'arms':ARMS
}, indent=2))
