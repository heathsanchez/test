#!/usr/bin/env python3
"""Adversarial single-source resource discovery on actual no-descent prefixes.

No population counts. For each source, retain its actual prefix until first
strict descent below source. Mine theorem-shaped source-anchored quantities
and reject any candidate that increases along a prefix. This is falsification,
not proof.
"""
from collections import defaultdict
import json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT/"source_product_v1"))
from source_product import initial,advance
BITS=20; DEPTH=2048
# Candidate resources are integer-valued and source anchored.
def feats(s):
 n=s.source;y=s.endpoint
 gap=y-n
 return {
  "height_gap":gap,
  "positive_gap_bits":max(0,gap).bit_length(),
  "endpoint_bits_minus_source":y.bit_length()-n.bit_length(),
  "residue_gap_abs":abs(s.endpoint_residue-s.source_residue),
  "tail":s.tail,
  "source_tail_plus_gap":s.tail+max(0,gap),
 }
viol=defaultdict(list); records=[]; maxlife=0
for n in range(3,1<<BITS,2):
 s=initial(n); xs=[]
 for k in range(DEPTH+1):
  if k and s.endpoint<n: break
  xs.append(s); s=advance(s)
 life=len(xs)-1
 if life>maxlife:
  maxlife=life;records.append({"source":n,"life":life,"peak":max(x.endpoint for x in xs)})
 for a,b in zip(xs,xs[1:]):
  fa,fb=feats(a),feats(b)
  for key in fa:
   if not fb[key] < fa[key] and len(viol[key])<8:
    viol[key].append({"source":n,"depth":a.depth,"before":fa[key],"after":fb[key],
      "y":a.endpoint,"ynext":b.endpoint})
out={"schema":"COLLATZ_CRYSTAL_SINGLE_SOURCE_RESOURCE_V1","sources":(1<<19)-1,
 "depth_limit":DEPTH,"record_survivors":records[-30:],
 "candidate_strict_rank_failures":dict(viol),
 "status":"NO_SNAPSHOT_RANK" if all(viol.values()) else "CANDIDATE_SURVIVED",
 "next":"If all snapshot ranks fail, search macro/event-defined source-anchored rank on record survivors only.",
 "global_collatz":"UNKNOWN"}
print(json.dumps(out,indent=2))
