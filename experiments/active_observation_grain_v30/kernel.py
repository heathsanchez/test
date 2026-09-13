#!/usr/bin/env python3
from __future__ import annotations
from basis import InstrumentWorld,all_partitions,sufficient,incomparable,block_sizes

class Kernel:
 @staticmethod
 def _auth(w):
  if not w.complete:return {"status":"UNKNOWN_AUTHORITY"}
  return None

 def full_signatures(self,w,sequence):
  sigs=[]
  finals=[]
  for x0 in range(w.state_count):
   x=x0; record=[]
   for m in sequence:
    record.append(w.outcomes[m][x]); x=w.post_states[m][x]
   sigs.append(tuple(record)+tuple(w.future_signatures[x])); finals.append(x)
  return tuple(sigs),tuple(finals)

 def outcome_only_signatures(self,w,m):
  return tuple((w.outcomes[m][x],) for x in range(w.state_count))

 def no_disturb_signatures(self,w,m):
  return tuple((w.outcomes[m][x],)+tuple(w.future_signatures[x]) for x in range(w.state_count))

 def coarsest(self,w,sigs,consequence_enabled=True):
  a=self._auth(w)
  if a:return a
  if not consequence_enabled:return {"status":"UNKNOWN_NO_CONSEQUENCE_AUTHORITY"}
  parts=tuple(all_partitions(w.state_count)); good=[p for p in parts if sufficient(p,sigs)]
  n=min(len(p) for p in good); mins=tuple(sorted(p for p in good if len(p)==n))
  return {"status":"VERIFIED","tested_partition_count":len(parts),"minimum_block_count":n,
          "minimum_partitions":[[list(b) for b in p] for p in mins],"_minimum":mins}

 def analyze_sequence(self,w,sequence,consequence_enabled=True):
  a=self._auth(w)
  if a:return a
  if not consequence_enabled:return {"status":"UNKNOWN_NO_CONSEQUENCE_AUTHORITY"}
  sigs,finals=self.full_signatures(w,sequence)
  row=self.coarsest(w,sigs,True)
  return {"status":"VERIFIED","sequence":list(sequence),"signatures":[list(s) for s in sigs],
          "final_states":list(finals),"tested_partition_count":row["tested_partition_count"],
          "minimum_block_count":row["minimum_block_count"],"minimum_partitions":row["minimum_partitions"],
          "_minimum":row["_minimum"],"_signatures":sigs}

 def analyze_instrument(self,w,m,consequence_enabled=True):
  full=self.analyze_sequence(w,(m,),consequence_enabled)
  if full.get("status")!="VERIFIED":return full
  out=self.coarsest(w,self.outcome_only_signatures(w,m),consequence_enabled)
  nod=self.coarsest(w,self.no_disturb_signatures(w,m),consequence_enabled)
  changed=[x for x in range(w.state_count) if w.post_states[m][x]!=x]
  future_changed=[x for x in range(w.state_count) if tuple(w.future_signatures[w.post_states[m][x]])!=tuple(w.future_signatures[x])]
  return {"status":"VERIFIED","instrument":m,"changed_states":changed,"future_changed_states":future_changed,
          "full":{k:v for k,v in full.items() if not k.startswith("_")},
          "outcome_only":{k:v for k,v in out.items() if not k.startswith("_")},
          "no_disturbance":{k:v for k,v in nod.items() if not k.startswith("_")},
          "_full_partition":full["_minimum"][0],"_out_partition":out["_minimum"][0],"_nod_partition":nod["_minimum"][0],
          "_full_signatures":full["_signatures"]}

 def analyze(self,w,consequence_enabled=True):
  a=self._auth(w)
  if a:return a
  if not consequence_enabled:return {"status":"UNKNOWN_NO_CONSEQUENCE_AUTHORITY"}
  inst=[self.analyze_instrument(w,m,True) for m in range(len(w.instrument_names))]
  pair=[]
  for i in range(len(inst)):
   for j in range(i+1,len(inst)):
    pair.append({"instruments":[i,j],"incomparable":incomparable(inst[i]["_full_partition"],inst[j]["_full_partition"])})
  return {"status":"VERIFIED","instruments":[{k:v for k,v in r.items() if not k.startswith("_")} for r in inst],
          "pairwise":pair,"_inst":inst}
