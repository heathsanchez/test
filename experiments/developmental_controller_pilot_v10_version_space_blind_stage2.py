#!/usr/bin/env python3
"""V10 stage2: reveal future only after frozen top-k version space exists."""
from __future__ import annotations
import json, os, urllib.request
from pathlib import Path
REPO='heathsanchez/mathgraph'; HORIZON=5
pred=json.load(open('experiments/v10_frozen_version_space.json'))
checkpoint=pred['checkpoint_token']

def get(url):
    req=urllib.request.Request(url,headers={'Accept':'application/vnd.github+json','User-Agent':'mathgraph-v10-stage2'})
    tok=os.environ.get('GITHUB_TOKEN')
    if tok: req.add_header('Authorization',f'Bearer {tok}')
    with urllib.request.urlopen(req,timeout=30) as r:return json.load(r)
# GitHub compare returns commits chronologically after base through head; use current default head.
repo=get(f'https://api.github.com/repos/{REPO}')
head=repo['default_branch']
cmp=get(f'https://api.github.com/repos/{REPO}/compare/{checkpoint}...{head}')
future=[]
for c in cmp.get('commits',[])[:HORIZON]:
    future.append({'sha':c['sha'],'time':c['commit']['author']['date'],'message':c['commit']['message'].split('\n')[0]})
if not future: raise SystemExit('no future commits revealed')

def hits(h):
    ks=[k.lower() for k in h['keywords']]
    return [f for f in future if any(k in f['message'].lower() for k in ks)]
scored=[]
for h in pred['ranked_version_space']:
    hs=hits(h)
    scored.append({'rank':h['rank'],'id':h['id'],'hit_count':len(hs),'hits':hs})
first=scored[0]
topk_any=sum(s['hit_count']>0 for s in scored)
first_future=future[0]['message']
# Conservative verdict: report, don't force semantic PASS if only keyword proxy matches.
result={
 'protocol':'DEVELOPMENTAL_CONTROLLER_PILOT_V10_VERSION_SPACE_BLIND_STAGE2',
 'checkpoint_token':checkpoint,
 'future':future,
 'single_story':first,
 'version_space_scores':scored,
 'topk_hypotheses_with_hits':topk_any,
 'first_revealed_commit':first_future,
 'verdict':'REQUIRES_SEMANTIC_AUDIT',
 'claim_boundary':pred['claim_boundary']
}
Path('v10_version_space_blind_result.json').write_text(json.dumps(result,indent=2)); print(json.dumps(result,indent=2))
