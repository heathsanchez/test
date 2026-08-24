import json, os, random, time, urllib.request
from pathlib import Path

ROOT = Path(__file__).parent
DATA = json.loads((ROOT / 'cases.json').read_text())
MODEL = os.environ.get('UVRM_MODEL', 'gpt-4.1-mini')
TOKEN = os.environ['OPENAI_API_KEY']
URL = 'https://api.openai.com/v1/chat/completions'
ARMS = ['RAW_OUTCOME','PROSE_MEMORY','STRUCTURED_STATE','STRUCTURED_ABLATION']
SEED = 2026082405


def memory_block(case, arm):
    if arm == 'RAW_OUTCOME':
        return 'RETAINED PRIOR RESULT:\n' + case['separator_outcome']
    if arm == 'PROSE_MEMORY':
        return 'RETAINED PRIOR RESULT:\n' + case['separator_outcome'] + '\n\nRETAINED MEMORY:\n' + case['prose_memory']
    if arm == 'STRUCTURED_STATE':
        return 'RETAINED PRIOR RESULT:\n' + case['separator_outcome'] + '\n\nRETAINED VERIFIED STATE:\n' + case['structured_state']
    return 'RETAINED PRIOR RESULT:\n' + case['separator_outcome'] + '\n\nRETAINED VERIFIED STATE:\n' + case['ablated_state']


def prompt(case, arm):
    opts = '\n'.join(f'{k}) {v}' for k,v in case['options'].items())
    return (
        'You are making a later research decision after an earlier verified experiment. '
        'Use only the information below. Select the single best next action. '
        'Return exactly two lines: CHOICE: <A|B|C|D> and REASON: <one short sentence>.\n\n'
        + memory_block(case, arm)
        + '\n\nLATER PROBLEM:\n' + case['later_problem']
        + '\n\nCANDIDATE ACTIONS:\n' + opts
    )


def call(p):
    body = json.dumps({
        'model': MODEL,
        'messages': [{'role':'user','content':p}],
        'temperature': 0,
        'max_tokens': 180
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
    'schema':'representation.change.v1.run',
    'model':MODEL,
    'provider':'openai',
    'temperature':0,
    'max_tokens':180,
    'calls':len(jobs),
    'seed':SEED,
    'arms':ARMS
}, indent=2))
