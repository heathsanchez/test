#!/usr/bin/env python3
"""Exact rational quantum instrument history test; not an empirical prediction.
Two measurement settings use different complete diagonal instruments.
All diagonal operations commute. A rotated valid instrument is an adversarial control.
"""
from fractions import Fraction as F
from itertools import product
import json
from pathlib import Path
import numpy as np

rho=np.diag([F(2,3),F(1,3)]).astype(object)
settings={
 'a':(np.diag([F(3,5),F(4,5)]).astype(object),np.diag([F(4,5),F(3,5)]).astype(object)),
 'b':(np.diag([F(5,13),F(12,13)]).astype(object),np.diag([F(12,13),F(5,13)]).astype(object))
}
for p,m in settings.values():
 assert (p@p+m@m).tolist()==np.eye(2,dtype=object).tolist()
def trace(x):return x[0,0]+x[1,1]
def run(seq,ops):
 x=rho
 for setting,bit in seq:
  k=ops[setting][bit]
  x=k@x@k.T
 return trace(x),x
words=list(product([('a',0),('a',1),('b',0),('b',1)],repeat=4))
classes={}
for seq in words:
 key=tuple(seq.count((s,b)) for s in ('a','b') for b in (0,1))
 classes.setdefault(key,[]).append(seq)
for seqs in classes.values():
 baseline=run(seqs[0],settings)
 for seq in seqs:
  current=run(seq,settings)
  assert current[0]==baseline[0] and current[1].tolist()==baseline[1].tolist()
assert len(words)==256 and len(classes)==35
# Exact noncommuting rotation. Replace setting b Kraus by K_b U, remains complete.
U=np.array([[F(3,5),-F(4,5)],[F(4,5),F(3,5)]],dtype=object)
changed={'a':settings['a'],'b':tuple(k@U for k in settings['b'])}
for p,m in changed.values():
 assert (p.T@p+m.T@m).tolist()==np.eye(2,dtype=object).tolist()
seq1=(('a',0),('b',0));seq2=(('b',0),('a',0))
v1=run(seq1,changed)[0];v2=run(seq2,changed)[0]
assert v1!=v2
result={'status':'WARRANTED EXACT RATIONAL UNDER DECLARED INSTRUMENT',
 'records':len(words),'count_state_classes':len(classes),
 'max_within_class_difference':'0 (exact rational)',
 'noncommuting_order_first':str(v1),'noncommuting_order_second':str(v2),
 'noncommuting_difference':str(v1-v2),
 'scope':'Two distinct commuting diagonal instrument settings; adversarial noncommuting complete instrument',
 'not_claimed':'Stuttgart mixed-interval empirical validation, a new physical law or universal minimality',
 'holdout':'Stuttgart Fig3b remains unopened'}
(Path(__file__).parent/'mixed_interval_quotient_results.json').write_text(json.dumps(result,indent=2)+'\n')
print('MIXED_INTERVAL_QUOTIENT',json.dumps(result))
