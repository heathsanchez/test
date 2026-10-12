"""Independent full rebuild baseline for the frozen FLASH V13 fixture.

Does not import/call flash_engine or reuse its closure implementation.
"""
import copy
from collections import defaultdict

class FullReference:
 def __init__(self,fixture):
  self.f=copy.deepcopy(fixture)
  self.ground=set(fixture['base_facts'])
  self.rebuilds=0
  self.checks=0
  self.frontier_checks=0
  self.current=self.rebuild()
 def rebuild(self):
  known=set(self.ground)
  rule_checks=0
  # Independent wave semantics: each wave considers the entire universe,
  # with a separate partial graph and repeated simultaneous consequences.
  while True:
   outgoing=[]
   for rule in self.f['rules']:
    rule_checks+=1
    if set(rule['when']).issubset(known):
     outgoing.append(rule['then'])
   future=known | set(outgoing)
   if future==known:break
   known=future
  supports=defaultdict(set)
  for g in self.ground:supports[g].add('BASE:'+g)
  for rule in self.f['rules']:
   if set(rule['when'])<=known:
    supports[rule['then']].add('RULE:'+rule['id'])
  assert all(supports[fact] for fact in known)
  frontiers={}
  for q in self.f['frontiers']:
   candidates=[]
   for option in q['options']:
    needed=sorted(set(option['when'])-known)
    banned=sorted(set(option['unless'])&known)
    budget=option['cost']>q['budget']
    ok=(not needed and not banned and not budget)
    candidates.append({'id':option['id'],'cost':option['cost'],'eligible':ok,'missing':needed,
       'forbidden':banned,'over_budget':budget})
   admissible=sorted((c for c in candidates if c['eligible']),key=lambda c:(c['cost'],c['id']))
   frontiers[q['id']]={'status':'SELECTED' if admissible else 'UNKNOWN',
      'selected':admissible[0]['id'] if admissible else None,
      'selected_cost':admissible[0]['cost'] if admissible else None,
      'candidates':sorted(candidates,key=lambda c:c['id'])}
  self.rebuilds+=1
  self.checks+=rule_checks
  self.frontier_checks+=len(self.f['frontiers'])
  return {'active':sorted(known),'base':sorted(self.ground),
     'supports':{k:sorted(v) for k,v in sorted(supports.items())},
     'frontiers':frontiers}
 def apply(self,event):
  kind=event['kind'];fact=event['fact']
  assert fact in self.f['allowed_events'][kind]
  assert event['authority']==('synthetic_event' if kind=='promote' else 'synthetic_revoker')
  if kind=='promote':self.ground.add(fact)
  elif kind=='revoke':self.ground.discard(fact)
  else:raise ValueError(kind)
  self.current=self.rebuild()
  return self.current
