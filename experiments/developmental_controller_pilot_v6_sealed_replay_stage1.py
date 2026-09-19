#!/usr/bin/env python3
"""V6 stage 1: generate a sealed historical replay packet from mathgraph-lean-kernel.

The script fetches commit history from the public repository, deterministically selects
one checkpoint from an eligible middle band, emits only the N commits immediately
preceding the checkpoint, and withholds all future commit messages.

The selected checkpoint is identified only by a SHA token so a prediction can be
frozen before the future is revealed. Stage 2 scores the frozen prediction against
subsequent commits.
"""
from __future__ import annotations
import hashlib, json, os, urllib.request

REPO='metalogiclabs/mathgraph-lean-kernel'
PER_PAGE=100
PAGES=4
CONTEXT_N=12
SEED='V6_SEALED_REPLAY_20260821'


def get(url):
    req=urllib.request.Request(url, headers={'Accept':'application/vnd.github+json','User-Agent':'mathgraph-v6'})
    tok=os.environ.get('GITHUB_TOKEN')
    if tok: req.add_header('Authorization', f'Bearer {tok}')
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.load(r)

commits=[]
for page in range(1,PAGES+1):
    xs=get(f'https://api.github.com/repos/{REPO}/commits?per_page={PER_PAGE}&page={page}')
    if not xs: break
    commits.extend(xs)

# GitHub returns newest first; use chronological order.
chron=list(reversed(commits))
# Eligible checkpoints must have enough past context and >=8 future commits.
elig=list(range(CONTEXT_N, max(CONTEXT_N, len(chron)-8)))
if not elig:
    raise SystemExit('not enough history')
# Hash every eligible SHA with the fixed seed and select minimum hash. This makes the
# choice deterministic but not hand-picked by the benchmark author.
def score(i):
    sha=chron[i]['sha']
    return hashlib.sha256((SEED+'|'+sha).encode()).hexdigest()
idx=min(elig, key=score)
checkpoint=chron[idx]
context=chron[idx-CONTEXT_N:idx]
packet={
  'protocol':'DEVELOPMENTAL_CONTROLLER_PILOT_V6_SEALED_REPLAY_STAGE1',
  'repo':REPO,
  'seed_commitment':hashlib.sha256(SEED.encode()).hexdigest(),
  'checkpoint_token':checkpoint['sha'],
  'checkpoint_time':checkpoint['commit']['author']['date'],
  'context_count':len(context),
  'instructions':[
    'Use only the context commits below; do not inspect later repository history.',
    'Infer the latent residual/representation coordinate that best explains the trajectory.',
    'Freeze 3-6 required/prohibited properties of the next useful intervention.',
    'Predict one or more semantic families for the next high-information experiment.',
    'Give at least one falsifier or rival explanation.'
  ],
  'context':[{
      'sha':c['sha'],
      'time':c['commit']['author']['date'],
      'message':c['commit']['message'].split('\n')[0]
  } for c in context]
}
with open('v6_sealed_packet.json','w') as f: json.dump(packet,f,indent=2)
print(json.dumps(packet,indent=2))
