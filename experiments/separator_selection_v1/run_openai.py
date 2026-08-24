import json, os, random, time, urllib.request
from pathlib import Path

ROOT = Path(__file__).parent
CASES = json.loads((ROOT / 'cases.json').read_text())
MODEL = os.environ.get('UVRM_MODEL', 'gpt-4.1-mini')
TOKEN = os.environ['OPENAI_API_KEY']
URL = 'https://api.openai.com/v1/chat/completions'
ARMS = ['GENERIC','VERIFY','RIVAL','INFO_GAIN','VERIFIED_RESIDUAL']
SEED = 20260824


def prompt(case, arm):
    ev = '\n'.join(f'- {x}' for x in case['evidence'])
    common = (
      'You are choosing the next experiment in an active research programme. The latent abstraction below is GIVEN and should not be rediscovered. '
      'Return exactly: TEST: <experiment>; SEPARATOR: <what different outcomes distinguish>; NEXT: <what each outcome would imply>. '
      'Be concrete and technical.\n\nEVIDENCE:\n' + ev + '\n\nLATENT ABSTRACTION:\n' + case['latent'] + '\n\n'
    )
    if arm == 'GENERIC':
        return common + 'What should we try next?'
    if arm == 'VERIFY':
        return common + 'Design a direct test of the supplied abstraction.'
    if arm == 'RIVAL':
        return common + 'STRONGEST RIVAL:\n' + case['rival'] + '\nDesign the smallest test that distinguishes the abstraction from this rival.'
    if arm == 'INFO_GAIN':
        return common + 'STRONGEST RIVAL:\n' + case['rival'] + '\nChoose the smallest experiment whose possible outcomes most change which of these two explanations survives. Prefer matched controls and a direct differential prediction.'
    return common + (
        'STRONGEST RIVAL:\n' + case['rival'] + '\nFollow verified-residual discipline. Choose the smallest deciding experiment; use matched controls; freeze the relevant workload/resource boundary before protected outcomes; '
        'do not invent a new representation if existing closure can decide the question; state what each outcome changes; and if neither prediction fits, preserve surprise as a new residual rather than forcing a conclusion.'
    )


def call(p):
    body = json.dumps({'model': MODEL,'messages':[{'role':'user','content':p}],'temperature':0,'max_tokens':280}).encode()
    req = urllib.request.Request(URL,data=body,headers={'Authorization':f'Bearer {TOKEN}','Content-Type':'application/json'})
    last=None
    for i in range(4):
        try:
            with urllib.request.urlopen(req, timeout=90) as r:
                obj=json.loads(r.read().decode())
            return obj['choices'][0]['message']['content']
        except Exception as e:
            last=e; time.sleep(2**i)
    raise last

jobs=[(c,a) for c in CASES['cases'] for a in ARMS]
random.Random(SEED).shuffle(jobs)
answers=[]
for i,(case,arm) in enumerate(jobs,1):
    print(f'[{i}/{len(jobs)}] {case["id"]} {arm}', flush=True)
    answers.append({'case_id':case['id'],'domain':case['domain'],'arm':arm,'answer':call(prompt(case,arm))})
(ROOT/'answers.json').write_text(json.dumps(answers,indent=2))
(ROOT/'run_metadata.json').write_text(json.dumps({'schema':'separator.selection.v1.run','model':MODEL,'temperature':0,'max_tokens':280,'calls':len(jobs),'seed':SEED,'arms':ARMS},indent=2))
