#!/usr/bin/env python3
"""V8 stage1: SAIR/MathGraph-only dense sealed replay.

Motivation: V7's selected Lean-kernel window had prior conversational exposure. V8
therefore precommits to heathsanchez/mathgraph, chooses a checkpoint solely from its
preceding dense experimental context, and emits no future commits.
"""
from __future__ import annotations
import datetime as dt, hashlib, json, os, urllib.request
REPO='heathsanchez/mathgraph'; PAGES=8; PER_PAGE=100; N=10
SEED='V8_SAIR_BLIND_20260821'
MARKERS=('experiment','residual','constructor','transfer','benchmark','atlas','lawbook','counter','witness','grammar','schema','closure','etp','sair','proof','model','ablation','recursive','route')

def get(url):
    req=urllib.request.Request(url,headers={'Accept':'application/vnd.github+json','User-Agent':'mathgraph-v8'})
    tok=os.environ.get('GITHUB_TOKEN')
    if tok: req.add_header('Authorization',f'Bearer {tok}')
    with urllib.request.urlopen(req,timeout=30) as r:return json.load(r)
def parse(s):return dt.datetime.fromisoformat(s.replace('Z','+00:00'))
commits=[]
for page in range(1,PAGES+1):
    xs=get(f'https://api.github.com/repos/{REPO}/commits?per_page={PER_PAGE}&page={page}')
    if not xs:break
    commits.extend(xs)
chron=list(reversed(commits))
el=[]
for i in range(N,len(chron)-6):
    ctx=chron[i-N:i]
    hours=(parse(ctx[-1]['commit']['author']['date'])-parse(ctx[0]['commit']['author']['date'])).total_seconds()/3600
    texts=[c['commit']['message'].split('\n')[0].lower() for c in ctx]
    mc=sum(any(m in x for m in MARKERS) for x in texts)
    if hours<=72 and mc>=4: el.append((i,hours,mc))
if not el: raise SystemExit('no eligible SAIR dense checkpoint')
def key(e):
    i,_,_=e
    return hashlib.sha256((SEED+'|'+chron[i]['sha']).encode()).hexdigest()
i,hours,mc=min(el,key=key); checkpoint=chron[i]; ctx=chron[i-N:i]
out={
 'protocol':'DEVELOPMENTAL_CONTROLLER_PILOT_V8_SAIR_BLIND_STAGE1',
 'repo':REPO,
 'checkpoint_token':checkpoint['sha'],
 'checkpoint_time':checkpoint['commit']['author']['date'],
 'seed_commitment':hashlib.sha256(SEED.encode()).hexdigest(),
 'selection_stats':{'context_hours':hours,'marker_commits':mc,'eligible_candidates':len(el)},
 'instructions':[
  'Use only these ten commits; do not inspect future history.',
  'Infer the latent obstruction or capability frontier that the sequence is converging on.',
  'Freeze a zoom decision, 3-6 constraints, one predicted next semantic experiment family, one rival, and a 3-5 commit falsifier.'
 ],
 'context':[{'sha':c['sha'],'time':c['commit']['author']['date'],'message':c['commit']['message'].split('\n')[0]} for c in ctx]
}
json.dump(out,open('v8_sair_blind_packet.json','w'),indent=2); print(json.dumps(out,indent=2))
