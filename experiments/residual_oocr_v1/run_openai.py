import json, os, random, time, urllib.request
from pathlib import Path

ROOT = Path(__file__).parent
CASES = json.loads((ROOT / 'cases.json').read_text())
MODEL = os.environ.get('UVRM_MODEL', 'gpt-4.1-mini')
TOKEN = os.environ['OPENAI_API_KEY']
URL = 'https://api.openai.com/v1/chat/completions'
ARMS = ['LOCAL','RAW_GLOBAL','OOCR_JOIN','OOCR_VERIFY','SHUFFLED']
SEED = 20260824


def evidence_for(case, arm):
    if arm != 'SHUFFLED':
        return case['evidence']
    other_id = CASES['shuffle_map'][case['id']]
    other = next(c for c in CASES['cases'] if c['id'] == other_id)
    return other['evidence']


def prompt(case, arm):
    ev = evidence_for(case, arm)
    lines = '\n'.join(f'- {x}' for x in ev)
    common = (
        'You are given pre-discovery research evidence. Do not use knowledge of later outcomes. '
        'Return exactly two labeled fields: LATENT: <candidate hidden structure>; TEST: <smallest next experiment>. '
        'Be concrete and technical.\n\nEVIDENCE:\n' + lines + '\n\n'
    )
    if arm == 'LOCAL':
        return common + (
            'Treat each observation independently. Do not assume they share one hidden mechanism. '
            'Choose the best local next step supported by the individual observations.'
        )
    if arm == 'RAW_GLOBAL':
        return common + (
            'Use all evidence normally to recommend the most justified next research move.'
        )
    if arm == 'OOCR_JOIN':
        return common + (
            'Infer the single latent structure, relation, abstraction, or missing distinction jointly implied by the scattered evidence, '
            'even if no observation states it explicitly. Then propose the next experiment that follows from that inferred structure.'
        )
    return common + (
        'Infer the single latent structure, relation, abstraction, or missing distinction jointly implied by the scattered evidence. '
        'Then state the smallest differential experiment that would distinguish this hypothesis from the strongest simpler rival. '
        'Prefer closure/composition before inventing a new representation unless the evidence has exhausted the old family.'
    )


def call(p):
    body = json.dumps({
        'model': MODEL,
        'messages': [{'role':'user','content':p}],
        'temperature': 0,
        'max_tokens': 260
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


jobs = [(c, a) for c in CASES['cases'] for a in ARMS]
random.Random(SEED).shuffle(jobs)
answers = []
for i, (case, arm) in enumerate(jobs, 1):
    print(f'[{i}/{len(jobs)}] {case["id"]} {arm}', flush=True)
    answers.append({'case_id': case['id'], 'domain': case['domain'], 'arm': arm, 'answer': call(prompt(case, arm))})

(ROOT / 'answers.json').write_text(json.dumps(answers, indent=2))
(ROOT / 'run_metadata.json').write_text(json.dumps({
    'schema': 'residual.oocr.v1.run',
    'model': MODEL,
    'provider': 'openai',
    'temperature': 0,
    'max_tokens': 260,
    'calls': len(jobs),
    'seed': SEED,
    'arms': ARMS
}, indent=2))
