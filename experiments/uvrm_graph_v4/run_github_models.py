import json, os, random, time, urllib.request, urllib.error
from pathlib import Path
from render import render, DATA

HERE=Path(__file__).parent
MODEL=os.environ.get('UVRM_MODEL','openai/gpt-4.1-mini')
TOKEN=os.environ['GITHUB_TOKEN']
URL='https://models.github.ai/inference/chat/completions'
ARMS=('TRANSCRIPT','GRAPH_ABL','GRAPH','GRAPH_RULES')

def call_model(prompt):
    payload=json.dumps({
        'model':MODEL,
        'messages':[{'role':'user','content':prompt}],
        'temperature':0,
        'max_tokens':220,
    }).encode()
    req=urllib.request.Request(URL,data=payload,headers={
        'Authorization':f'Bearer {TOKEN}',
        'Content-Type':'application/json',
        'Accept':'application/json',
    })
    last=None
    for attempt in range(4):
        try:
            with urllib.request.urlopen(req,timeout=90) as r:
                obj=json.loads(r.read().decode())
            return obj['choices'][0]['message']['content'].strip()
        except Exception as e:
            last=e
            time.sleep(2**attempt)
    raise RuntimeError(f'model call failed after retries: {last}')

def main():
    # Fixed seed changes only call ordering, never prompt contents or scoring.
    jobs=[(c,a) for c in DATA['cases'] for a in ARMS]
    random.Random(20260824).shuffle(jobs)
    answers={}
    metadata={'model':MODEL,'temperature':0,'max_tokens':220,'seed_order':20260824,'n_expected':len(jobs),'calls':[]}
    for i,(case,arm) in enumerate(jobs,1):
        key=f"{case['id']}__{arm}"
        prompt=render(case,arm)
        t0=time.time()
        text=call_model(prompt)
        dt=time.time()-t0
        answers[key]=text
        metadata['calls'].append({'key':key,'seconds':round(dt,3),'prompt_chars':len(prompt),'answer_chars':len(text)})
        print(f'[{i}/{len(jobs)}] {key} {dt:.2f}s :: {text.replace(chr(10)," | ")}',flush=True)
    (HERE/'answers_github_models.json').write_text(json.dumps(answers,indent=2,sort_keys=True)+'\n')
    (HERE/'run_metadata.json').write_text(json.dumps(metadata,indent=2,sort_keys=True)+'\n')
    print(f'model={MODEL} calls={len(answers)}')

if __name__=='__main__': main()
