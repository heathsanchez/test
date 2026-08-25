#!/usr/bin/env python3
import json, math, random
from collections import Counter, defaultdict
from pathlib import Path
SEED=2026082519; RNG=random.Random(SEED)
OUT=Path('artifacts/behavioral_object_equivalence_condition_v4'); OUT.mkdir(parents=True,exist_ok=True)
MEASURES=('true_target_entropy','unweighted_target_ambiguity','weighted_target_setsize','negative_singleton_mass','max_target_setsize')
def entropy(vals):
 c=Counter(vals); n=len(vals); return -sum((v/n)*math.log2(v/n) for v in c.values()) if n else 0.0
def feats(y,q):
 by=defaultdict(list)
 for yy,o in zip(y,q): by[o].append(yy)
 n=len(y); mass={o:len(v)/n for o,v in by.items()}; sup={o:set(v) for o,v in by.items()}
 return {'true_target_entropy':sum(mass[o]*entropy(by[o]) for o in by),'unweighted_target_ambiguity':sum(math.log2(len(sup[o])) for o in by)/len(by),'weighted_target_setsize':sum(mass[o]*len(sup[o]) for o in by),'negative_singleton_mass':-sum(mass[o] for o in by if len(sup[o])==1),'max_target_setsize':max(len(sup[o]) for o in by)}
def det(y,q):
 by=defaultdict(set)
 for yy,o in zip(y,q): by[o].add(yy)
 return all(len(s)==1 for s in by.values())
def choose(y,qs,m):
 vals=[feats(y,q)[m] for q in qs]; b=min(vals); return min(i for i,v in enumerate(vals) if abs(v-b)<1e-12)
def acts(y,qs): return {m:choose(y,qs,m) for m in MEASURES}
def rtarget():
 while True:
  y=[RNG.randrange(3) for _ in range(12)]
  if len(set(y))==3:return y
def rq(): return [RNG.randrange(3) for _ in range(12)]
D_N=5000; fail=[]
for i in range(D_N):
 y=rtarget(); qs=[list(y)]+[rq() for _ in range(3)]; RNG.shuffle(qs); a=acts(y,qs)
 if len(set(a.values()))!=1: fail.append({'i':i,'actions':a}); break
y0=[0,0,1,1,2,2]; q0=list(y0); dv=feats(y0,q0)
mins={'true_target_entropy':0.0,'unweighted_target_ambiguity':0.0,'weighted_target_setsize':1.0,'negative_singleton_mass':-1.0,'max_target_setsize':1.0}
minima_ok=all(abs(dv[k]-v)<1e-12 for k,v in mins.items())
def uq():
 q=[0]*4+[1]*4+[2]*4; RNG.shuffle(q); return q
def U(q): return sorted(Counter(q).values())==[4,4,4]
def E(y,q):
 by=defaultdict(set)
 for yy,o in zip(y,q): by[o].add(yy)
 return len(set(len(s) for s in by.values()))==1
def find_ce(limit=200000):
 y=[0]*6+[1]*6; RNG.shuffle(y)
 for at in range(1,limit+1):
  qs=[uq() for _ in range(4)]
  if not all(E(y,q) for q in qs) or any(det(y,q) for q in qs): continue
  a=acts(y,qs); ev=[feats(y,q)['true_target_entropy'] for q in qs]
  if len(set(a.values()))>1 and sum(abs(v-min(ev))<1e-12 for v in ev)==1:
   return {'attempt':at,'target':y,'queries':qs,'actions':a,'features':{m:[feats(y,q)[m] for q in qs] for m in MEASURES},'U':all(U(q) for q in qs),'E':all(E(y,q) for q in qs),'D':any(det(y,q) for q in qs)}
ce=find_ce()
out={'schema':'behavioral.object.equivalence.condition.v4','parent_run':32808509116,'seed':SEED,'D_stress_n':D_N,'D_action_equivalence_failures':len(fail),'deterministic_measure_values':dv,'deterministic_global_minima':mins,'deterministic_minima_check':minima_ok,'UE_counterexample_found':ce is not None,'UE_counterexample':ce}
(OUT/'summary.json').write_text(json.dumps(out,indent=2)); print(json.dumps(out,indent=2))
assert minima_ok and not fail and ce is not None
assert ce['U'] and ce['E'] and not ce['D'] and len(set(ce['actions'].values()))>1
print('PASS_BEHAVIORAL_OBJECT_EQUIVALENCE_CONDITION_V4')
