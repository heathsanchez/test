#!/usr/bin/env python3
"""V10 stage1: blind historical replay with top-k developmental version space.

Select a dense MathGraph checkpoint different from V8 using only preceding history.
Emit no future commits. Stage2 will score a frozen ranked version space and separators.
"""
from __future__ import annotations
import datetime as dt, hashlib, json, os, urllib.request
REPO='heathsanchez/mathgraph'; PAGES=10; PER_PAGE=100; N=12
SEED='V10_VERSION_SPACE_BLIND_20260821'
EXCLUDE={'e5119fad75f3fb9e65cc716d872b1f1cd413c8c8'}
MARKERS=('experiment','residual','constructor','transfer','benchmark','atlas','lawbook','counter','witness','grammar','schema','closure','etp','sair','proof','model','ablation','recursive','route','quotient','continuation','inventory')

def get(url):
    req=urllib.request.Request(url,headers={'Accept':'application/vnd.github+json','User-Agent':'mathgraph-v10'})
    tok=os.environ.get('GITHUB_TOKEN')
    if tok: req.add_header('Authorization',f'Bearer {tok}')
    with urllib.request.urlopen(req,timeout=30) as r:return json.load(r)
def parse(s):return dt.datetime.fromisoformat(s.replace('Z','+00:00'))
commits=[]
for page in range(1,PAGES+1):
    xs=get(f'https://api.github.com/repos/{REPO}/commits?per_page={PER_PAGE}&page={page}')
    if not xs:break
    commits.extend(xs)
chron=list(reversed(commits)); eligible=[]
for i in range(N,len(chron)-8):
    cp=chron[i]
    if cp['sha'] in EXCLUDE: continue
    ctx=chron[i-N:i]
    hours=(parse(ctx[-1]['commit']['author']['date'])-parse(ctx[0]['commit']['author']['date'])).total_seconds()/3600
    texts=[c['commit']['message'].split('\n')[0].lower() for c in ctx]
    mc=sum(any(m in x for m in MARKERS) for x in texts)
    diversity=len({next((m for m in MARKERS if m in x),'other') for x in texts})
    if hours<=96 and mc>=6 and diversity>=4: eligible.append((i,hours,mc,diversity))
if not eligible: raise SystemExit('no eligible V10 checkpoint')
def key(e):
    i,*_=e
    return hashlib.sha256((SEED+'|'+chron[i]['sha']).encode()).hexdigest()
i,hours,mc,div=min(eligible,key=key); cp=chron[i]; ctx=chron[i-N:i]
out={
 'protocol':'DEVELOPMENTAL_CONTROLLER_PILOT_V10_VERSION_SPACE_BLIND_STAGE1',
 'repo':REPO,
 'checkpoint_token':cp['sha'],
 'checkpoint_time':cp['commit']['author']['date'],
 'seed_commitment':hashlib.sha256(SEED.encode()).hexdigest(),
 'selection_stats':{'context_hours':hours,'marker_commits':mc,'diversity':div,'eligible_candidates':len(eligible)},
 'instructions':[
  'Use only these twelve commits; do not inspect future history.',
  'Do NOT collapse to one story.',
  'Freeze 3-5 ranked rival developmental hypotheses.',
  'For each rival give required evidence and a smallest discriminating next experiment.',
  'Choose one highest-information separator across the version space.',
  'Predict which observable outcome would promote each rival.'
 ],
 'context':[{'sha':c['sha'],'time':c['commit']['author']['date'],'message':c['commit']['message'].split('\n')[0]} for c in ctx]
}
json.dump(out,open('v10_version_space_blind_packet.json','w'),indent=2); print(json.dumps(out,indent=2))
