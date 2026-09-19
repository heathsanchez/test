#!/usr/bin/env python3
"""V7 stage1: sealed replay from a dense experimental epoch.

Selection uses only the *preceding* context of each candidate checkpoint. A candidate
is eligible when its previous 10 commits are dense in time and contain multiple
experiment-like markers. The future is not used to choose the checkpoint and is not
emitted. Candidates are drawn from both MathGraph and the Lean-kernel repo.
"""
from __future__ import annotations
import datetime as dt, hashlib, json, os, urllib.request

REPOS=['heathsanchez/mathgraph','metalogiclabs/mathgraph-lean-kernel']
PAGES=6
PER_PAGE=100
CONTEXT_N=10
SEED='V7_DENSE_SEALED_20260821'
MARKERS=('experiment','separator','probe','residual','atlas','gate','census','patch','workflow','trigger','ablation','benchmark','constructor','transfer','repair','quotient')

def get(url):
    req=urllib.request.Request(url,headers={'Accept':'application/vnd.github+json','User-Agent':'mathgraph-v7'})
    tok=os.environ.get('GITHUB_TOKEN')
    if tok: req.add_header('Authorization',f'Bearer {tok}')
    with urllib.request.urlopen(req,timeout=30) as r: return json.load(r)

def parse(s): return dt.datetime.fromisoformat(s.replace('Z','+00:00'))

eligible=[]
repo_hist={}
for repo in REPOS:
    commits=[]
    for page in range(1,PAGES+1):
        xs=get(f'https://api.github.com/repos/{repo}/commits?per_page={PER_PAGE}&page={page}')
        if not xs: break
        commits.extend(xs)
    chron=list(reversed(commits)); repo_hist[repo]=chron
    for i in range(CONTEXT_N,len(chron)-6):
        ctx=chron[i-CONTEXT_N:i]
        t0=parse(ctx[0]['commit']['author']['date']); t1=parse(ctx[-1]['commit']['author']['date'])
        hours=(t1-t0).total_seconds()/3600
        texts=[c['commit']['message'].split('\n')[0].lower() for c in ctx]
        marker_commits=sum(any(m in x for m in MARKERS) for x in texts)
        # Dense enough to be a real active experimental episode; threshold allows a day.
        if hours <= 36 and marker_commits >= 4:
            eligible.append((repo,i,hours,marker_commits))
if not eligible: raise SystemExit('no dense experimental checkpoint found')

def hkey(item):
    repo,i,_,_=item; sha=repo_hist[repo][i]['sha']
    return hashlib.sha256((SEED+'|'+repo+'|'+sha).encode()).hexdigest()
repo,idx,hours,marker_commits=min(eligible,key=hkey)
chron=repo_hist[repo]; checkpoint=chron[idx]; ctx=chron[idx-CONTEXT_N:idx]
packet={
 'protocol':'DEVELOPMENTAL_CONTROLLER_PILOT_V7_DENSE_SEALED_STAGE1',
 'repo':repo,
 'checkpoint_token':checkpoint['sha'],
 'checkpoint_time':checkpoint['commit']['author']['date'],
 'seed_commitment':hashlib.sha256(SEED.encode()).hexdigest(),
 'selection_stats':{'context_hours':hours,'marker_commits':marker_commits,'eligible_candidates':len(eligible)},
 'instructions':[
   'Use only the context below. Do not inspect later history.',
   'Infer the latent obstruction/coordinate that best explains what the experiment sequence is learning.',
   'Freeze 3-6 required/prohibited properties for the next high-information intervention.',
   'Predict the next semantic experiment family and one strong rival.',
   'State a short-horizon falsifier.'
 ],
 'context':[{'sha':c['sha'],'time':c['commit']['author']['date'],'message':c['commit']['message'].split('\n')[0]} for c in ctx]
}
json.dump(packet,open('v7_dense_sealed_packet.json','w'),indent=2)
print(json.dumps(packet,indent=2))
