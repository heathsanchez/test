#!/usr/bin/env python3
"""V6 stage 2: reveal future history only after frozen prediction exists."""
from __future__ import annotations
import json, os, urllib.request

REPO='metalogiclabs/mathgraph-lean-kernel'
PAGES=4
PER_PAGE=100
FUTURE_N=12


def get(url):
    req=urllib.request.Request(url,headers={'Accept':'application/vnd.github+json','User-Agent':'mathgraph-v6'})
    tok=os.environ.get('GITHUB_TOKEN')
    if tok: req.add_header('Authorization', f'Bearer {tok}')
    with urllib.request.urlopen(req,timeout=30) as r: return json.load(r)

with open('experiments/v6_frozen_prediction.json') as f: pred=json.load(f)
assert pred.get('prediction_frozen_before_future_reveal') is True
checkpoint=pred['checkpoint_token']
commits=[]
for page in range(1,PAGES+1):
    xs=get(f'https://api.github.com/repos/{REPO}/commits?per_page={PER_PAGE}&page={page}')
    if not xs: break
    commits.extend(xs)
chron=list(reversed(commits))
idx=next(i for i,c in enumerate(chron) if c['sha']==checkpoint)
future=chron[idx+1:idx+1+FUTURE_N]
msgs=[c['commit']['message'].split('\n')[0] for c in future]
# Predeclared lightweight family scorer. These keyword buckets were frozen in code
# before this stage queried the future and are intentionally broad.
buckets={
 'lean4_compat':['lean4','lean 4','compat','feature','parser','kernel','declar'],
 'build_api':['build','cargo','rust','api','dependency','deps','compile','edition'],
 'tests_integration':['test','example','binary','cli','integration','debug'],
 'low_level_perf':['cache','alloc','index','layout','perf','fast','optimi'],
}
low='\n'.join(msgs).lower()
counts={k:sum(low.count(w) for w in ws) for k,ws in buckets.items()}
predicted_score=counts['lean4_compat']+counts['build_api']+counts['tests_integration']
rival_score=counts['low_level_perf']
verdict={
 'future_revealed_after_freeze':True,
 'predicted_family_has_support':predicted_score>0,
 'predicted_family_not_weaker_than_rival':predicted_score>=rival_score,
}
out={
 'protocol':'DEVELOPMENTAL_CONTROLLER_PILOT_V6_SEALED_REPLAY_STAGE2',
 'checkpoint_token':checkpoint,
 'frozen_prediction':pred,
 'future_commits':[{'sha':c['sha'],'time':c['commit']['author']['date'],'message':c['commit']['message'].split('\n')[0]} for c in future],
 'bucket_counts':counts,
 'predicted_score':predicted_score,
 'rival_score':rival_score,
 'verdict':verdict,
 'all_gates_pass':all(verdict.values()),
 'claim_boundary':'Single sealed historical replay selected deterministically from commit history. Scoring is coarse keyword-family support and does not establish causal recovery of a breakthrough.'
}
with open('v6_sealed_replay_result.json','w') as f: json.dump(out,f,indent=2)
print(json.dumps(out,indent=2))
if not out['all_gates_pass']: raise SystemExit('V6 sealed replay gates failed')
