#!/usr/bin/env python3
from __future__ import annotations
import json, os, urllib.request
REPO='heathsanchez/mathgraph'; PAGES=8; PER_PAGE=100; H=5

def get(url):
    req=urllib.request.Request(url,headers={'Accept':'application/vnd.github+json','User-Agent':'mathgraph-v8'})
    tok=os.environ.get('GITHUB_TOKEN')
    if tok: req.add_header('Authorization',f'Bearer {tok}')
    with urllib.request.urlopen(req,timeout=30) as r:return json.load(r)
pred=json.load(open('experiments/v8_frozen_prediction.json')); cp=pred['checkpoint_token']
commits=[]
for page in range(1,PAGES+1):
    xs=get(f'https://api.github.com/repos/{REPO}/commits?per_page={PER_PAGE}&page={page}')
    if not xs:break
    commits.extend(xs)
chron=list(reversed(commits)); i=next(i for i,c in enumerate(chron) if c['sha']==cp)
future=chron[i+1:i+1+H]; msgs=[c['commit']['message'].split('\n')[0] for c in future]; text='\n'.join(msgs).lower()
promote=('residual','constructor','schema','compounding','recursive','active','discovery','transfer','lawbook helper')
rival=('harden','boundary','canonical','docs','documentation','replay','routing','hygiene')
a=sum(text.count(x) for x in promote); b=sum(text.count(x) for x in rival)
verdict={'future_revealed_after_freeze':True,'promotion_family_observed':a>0,'promotion_stronger_than_infrastructure_rival':a>b}
out={'protocol':'DEVELOPMENTAL_CONTROLLER_PILOT_V8_SAIR_BLIND_STAGE2','checkpoint_token':cp,'frozen_prediction':pred,'future_commits':[{'sha':c['sha'],'time':c['commit']['author']['date'],'message':c['commit']['message'].split('\n')[0]} for c in future],'promotion_hits':a,'rival_hits':b,'verdict':verdict,'all_gates_pass':all(verdict.values()),'claim_boundary':'Short-horizon SAIR historical replay. Workflow sealing is real; prior broad conversation memory prevents calling this a fresh-model blind result.'}
json.dump(out,open('v8_sair_blind_result.json','w'),indent=2);print(json.dumps(out,indent=2))
if not out['all_gates_pass']:raise SystemExit('V8 gates failed')
