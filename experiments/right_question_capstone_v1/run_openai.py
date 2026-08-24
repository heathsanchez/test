import json, math, os, random, time, urllib.request
from collections import Counter, defaultdict
from itertools import product
from pathlib import Path

ROOT=Path(__file__).parent
DATA=json.loads((ROOT.parent/'law_induction_v1b'/'cases.json').read_text())
MODEL=os.environ.get('UVRM_MODEL','gpt-4.1-mini')
TOKEN=os.environ['OPENAI_API_KEY']
URL='https://api.openai.com/v1/chat/completions'
SEED=2026082506
CODES={'J':0,'K':1,'L':2,'M':3}; INV={v:k for k,v in CODES.items()}
TEMPLATES=[
 {'id':'t1','initial':['CX','CY','DX','DY'],'target':'BY','queries':['AX','AY','BX']},
 {'id':'t2','initial':['BX','BY','DX','DY'],'target':'CY','queries':['AX','AY','CX']},
 {'id':'t3','initial':['AX','AY','DX','DY'],'target':'CY','queries':['BX','BY','CX']},
 {'id':'t4','initial':['AX','AY','BX','BY'],'target':'CY','queries':['CX','DX','DY']},
]
ARMS=['GENERIC_EXPLICIT','RIVAL_EXPLICIT','TARGET_INFO_GAIN_EXPLICIT','TARGET_INFO_GAIN_OBS_ONLY']

def parse_oracle(c):
 import re
 b={k:int(v) for k,v in re.findall(r'([ABCD])=(\d)',c['oracle'])}; o={k:int(v) for k,v in re.findall(r'([XY])=(\d)',c['oracle'])}; return b,o

def world_value(c,p):
 b,o=parse_oracle(c); return (b[p[0]]+o[p[1]])%4

def all_hypotheses():
 return [(dict(zip('ABCD',v[:4])),{'X':0,'Y':v[4]}) for v in product(range(4),repeat=5)]
H=all_hypotheses()
def pred(h,p): return (h[0][p[0]]+h[1][p[1]])%4
def survivors(c,pairs): return [h for h in H if all(pred(h,p)==world_value(c,p) for p in pairs)]
def entropy(vals):
 n=len(vals); cnt=Counter(vals)
 return 0.0 if not n else -sum((v/n)*math.log2(v/n) for v in cnt.values() if v)
def target_entropy(hs,target): return entropy([pred(h,target) for h in hs])
def expected_target_entropy(hs,q,target):
 groups=defaultdict(list)
 for h in hs: groups[pred(h,q)].append(h)
 return sum(len(g)/len(hs)*target_entropy(g,target) for g in groups.values())
def update(hs,q,a): return [h for h in hs if pred(h,q)==a]
def majority(hs,target):
 cnt=Counter(pred(h,target) for h in hs); m=max(cnt.values()); return sorted(k for k,v in cnt.items() if v==m)[0]
def htxt(h):
 b,o=h; return f"A={b['A']},B={b['B']},C={b['C']},D={b['D']},Y={o['Y']}"
def call(prompt):
 body=json.dumps({'model':MODEL,'messages':[{'role':'user','content':prompt}],'temperature':0,'max_tokens':40,'response_format':{'type':'json_object'}}).encode()
 req=urllib.request.Request(URL,data=body,headers={'Authorization':f'Bearer {TOKEN}','Content-Type':'application/json'})
 last=None
 for i in range(4):
  try:
   with urllib.request.urlopen(req,timeout=90) as r: obj=json.loads(r.read().decode())
   return obj['choices'][0]['message']['content']
  except Exception as e: last=e; time.sleep(2**i)
 raise last

def prompt(c,t,hs,arm):
 init='; '.join(f'{p}->{INV[world_value(c,p)]}' for p in t['initial'])
 qs=', '.join(t['queries'])
 base=f'Hidden law family: action=(base[prefix]+offset[suffix]) mod 4 with J=0,K=1,L=2,M=3 and gauge X=0. Verified observations: {init}. Target whose action must ultimately be known: {t["target"]}. Allowed one extra query: {qs}. Return only JSON {{"query":"PAIR"}}.'
 if arm!='TARGET_INFO_GAIN_OBS_ONLY':
  base += '\nCurrent surviving latent worlds (A,B,C,D,Y):\n'+'\n'.join(htxt(h) for h in hs)
 if arm=='GENERIC_EXPLICIT': tail='\nChoose the most useful next query.'
 elif arm=='RIVAL_EXPLICIT': tail='\nIdentify the strongest live rival predictions about the TARGET and choose the allowed query that best separates those rival target-relevant worlds.'
 else: tail='\nChoose the allowed query that minimizes expected uncertainty (entropy) of the TARGET action after its answer is observed. Do not optimize uncertainty about irrelevant latent details.'
 return base+tail

rng=random.Random(SEED); rows=[]
for c in DATA['cases']:
 for t in TEMPLATES:
  hs=survivors(c,t['initial']); assert len(hs)==16
  e0=target_entropy(hs,t['target']); truth=world_value(c,t['target'])
  ig={q:e0-expected_target_entropy(hs,q,t['target']) for q in t['queries']}
  optimal=sorted(t['queries'],key=lambda q:(-ig[q],q))[0]
  # deterministic baselines
  for arm,q in [('RANDOM_QUERY',rng.choice(t['queries'])),('OPTIMAL_QUERY',optimal)]:
   a=world_value(c,q); h2=update(hs,q,a); tp=majority(h2,t['target'])
   rows.append({'case_id':c['id'],'template':t['id'],'arm':arm,'query':q,'optimal_query':optimal,'query_optimal':q==optimal,'target_truth':INV[truth],'target_pred':INV[tp],'correct':tp==truth,'entropy_before':e0,'entropy_after':target_entropy(h2,t['target']),'expected_info_gain':ig[q],'optimal_info_gain':ig[optimal]})
  for arm in ARMS:
   raw=call(prompt(c,t,hs,arm))
   try: q=json.loads(raw).get('query')
   except Exception: q=None
   valid=q in t['queries']
   if valid:
    a=world_value(c,q); h2=update(hs,q,a); tp=majority(h2,t['target']); ea=target_entropy(h2,t['target'])
   else:
    tp=majority(hs,t['target']); ea=e0
   rows.append({'case_id':c['id'],'template':t['id'],'arm':arm,'raw':raw,'query':q,'query_valid':valid,'optimal_query':optimal,'query_optimal':q==optimal,'target_truth':INV[truth],'target_pred':INV[tp],'correct':tp==truth,'entropy_before':e0,'entropy_after':ea,'expected_info_gain':ig.get(q,0.0),'optimal_info_gain':ig[optimal]})
(ROOT/'answers.json').write_text(json.dumps(rows,indent=2))
(ROOT/'run_metadata.json').write_text(json.dumps({'schema':'right.question.capstone.v1','model':MODEL,'temperature':0,'seed':SEED,'tasks':32,'llm_arms':ARMS},indent=2))
print('RIGHT_QUESTION_CAPSTONE_V1_RUN_PASS',len(rows),flush=True)
