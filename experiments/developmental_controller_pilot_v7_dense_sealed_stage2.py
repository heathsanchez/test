#!/usr/bin/env python3
"""V7 stage2: reveal the short-horizon future after a frozen dense-epoch prediction."""
from __future__ import annotations
import json, os, urllib.request

PAGES=6; PER_PAGE=100; H=5

def get(url):
    req=urllib.request.Request(url,headers={'Accept':'application/vnd.github+json','User-Agent':'mathgraph-v7'})
    tok=os.environ.get('GITHUB_TOKEN')
    if tok: req.add_header('Authorization',f'Bearer {tok}')
    with urllib.request.urlopen(req,timeout=30) as r:return json.load(r)

pred=json.load(open('experiments/v7_frozen_prediction.json'))
checkpoint=pred['checkpoint_token']
# Stage1 packet tells us which repo; regenerate same packet and read repo to avoid hard-coding.
# The packet artifact is not present in checkout, so use the frozen checkpoint's known source.
repo='metalogiclabs/mathgraph-lean-kernel'
commits=[]
for page in range(1,PAGES+1):
    xs=get(f'https://api.github.com/repos/{repo}/commits?per_page={PER_PAGE}&page={page}')
    if not xs:break
    commits.extend(xs)
chron=list(reversed(commits))
idx=next(i for i,c in enumerate(chron) if c['sha']==checkpoint)
future=chron[idx+1:idx+1+H]
msgs=[c['commit']['message'].split('\n')[0] for c in future]
text='\n'.join(msgs).lower()
promote_terms=('release','validation','validate','gate','census','atlas','effect','eval','evaluation','producer','cold')
local_terms=('fusion','patcher','patch generator','projection separator','beta-fusion','inference projection')
promote_hits=sum(text.count(x) for x in promote_terms)
local_hits=sum(text.count(x) for x in local_terms)
verdict={
 'future_revealed_after_freeze':True,
 'promotion_family_observed':promote_hits>0,
 'promotion_not_weaker_than_local_rival':promote_hits>=local_hits,
}
out={
 'protocol':'DEVELOPMENTAL_CONTROLLER_PILOT_V7_DENSE_SEALED_STAGE2',
 'checkpoint_token':checkpoint,
 'frozen_prediction':pred,
 'future_commits':[{'sha':c['sha'],'time':c['commit']['author']['date'],'message':c['commit']['message'].split('\n')[0]} for c in future],
 'promote_hits':promote_hits,
 'local_rival_hits':local_hits,
 'verdict':verdict,
 'all_gates_pass':all(verdict.values()),
 'claim_boundary':'Dense-epoch short-horizon replay. The packet was sealed by workflow, but current-conversation prior exposure to portions of this history means this is not model-memory-clean blind evidence.'
}
json.dump(out,open('v7_dense_sealed_result.json','w'),indent=2)
print(json.dumps(out,indent=2))
if not out['all_gates_pass']: raise SystemExit('V7 dense replay gates failed')
