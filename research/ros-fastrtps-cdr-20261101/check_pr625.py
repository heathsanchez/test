#!/usr/bin/env python3
"""A bounded native differential verdict; not an assertion of global input safety."""
import collections
import json

def read(arm):
    rows=json.load(open("/evidence/"+arm+"-results.json"))["cases"]
    assert len(rows)==224, (arm,len(rows))
    return {(r["backend"],r["type"],r["case"]):r for r in rows}
b=read("baseline")
p=read("patched")
assert set(b)==set(p)
affected=("empty","header_1","header_2","header_3")
positive=[k for k in b if k[2]=="valid"]
assert len(positive)==14, positive
for k in positive:
    assert b[k]["outcome"]=="accepted", ("baseline-positive",k,b[k])
    assert p[k]["outcome"]=="accepted", ("patched-positive",k,p[k])

short_keys=[k for k in b if k[0]=="rmw_cyclonedds_cpp" and k[2] in affected]
assert len(short_keys)==28
old_bad=[k for k in short_keys if b[k]["outcome"] in ("signal","timeout","accepted")]
assert len(old_bad)>=10, [b[k] for k in short_keys]
for k in short_keys:
    assert p[k]["outcome"]=="error", ("patched-short-buffer",k,p[k])

delta=[{"backend":k[0],"message":k[1],"case":k[2],
        "before":b[k]["outcome"],"after":p[k]["outcome"]}
       for k in sorted(b) if b[k]["outcome"]!=p[k]["outcome"]]
for arm,d in (("baseline",b),("patched",p)):
    for backend in ("rmw_cyclonedds_cpp","rmw_fastrtps_cpp"):
        counts=collections.Counter(v["outcome"] for k,v in d.items() if k[0]==backend)
        print(arm,backend,dict(counts))
print("SHORT_CDR_BOUNDARY:",json.dumps([{"type":k[1],"case":k[2],
          "before":b[k]["outcome"],"after":p[k]["outcome"]} for k in sorted(short_keys)]))
print("DIFFERENCES:",json.dumps(delta))
with open("/evidence/differential.json","w") as file:
    json.dump({"short_boundary":[{"type":k[1],"case":k[2],
        "before":b[k]["outcome"],"after":p[k]["outcome"]} for k in sorted(short_keys)],
        "deltas":delta},file,indent=2)
print("GATE PASS: 28/28 short CDR buffers safely rejected after PR625; "
      "original bug reproduced and 14 valid controls preserved across both RMWs.")
