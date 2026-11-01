#!/usr/bin/env python3
"""Evidence gate for full legacy CDR controls across PR625 and new preflight."""
import collections
import json
def read(arm):
    rows=json.load(open("/evidence/legacy-results-"+arm+".json"))["cases"]
    assert len(rows)==224,(arm,len(rows))
    return {(r["backend"],r["type"],r["case"]):r for r in rows}
a=read("patched")
b=read("preflight")
assert set(a)==set(b)
for arm,rows in (("patched",a),("preflight",b)):
    valid=[r for k,r in rows.items() if k[2]=="valid"]
    assert len(valid)==14 and all(r["outcome"]=="accepted" for r in valid)
    assert all(rows[k]["outcome"]=="error" for k in rows if
               k[0]=="rmw_cyclonedds_cpp" and k[2] in ("empty","header_1","header_2","header_3"))
    print(arm,"COUNTS",{
      backend:dict(collections.Counter(r["outcome"] for k,r in rows.items() if k[0]==backend))
      for backend in ("rmw_cyclonedds_cpp","rmw_fastrtps_cpp")})
cyclone_changed=[{"key":k,"a":v["outcome"],"b":b[k]["outcome"]} for k,v in a.items()
                if k[0]=="rmw_cyclonedds_cpp" and v["outcome"]!=b[k]["outcome"]]
print("CYCLONE_OUTCOME_DIFFERENCES",json.dumps(cyclone_changed))
assert all(x["b"] not in ("signal","timeout","process_error","unparseable","accepted")
           for x in cyclone_changed),cyclone_changed
with open("/evidence/legacy-differential.json","w") as f:json.dump(cyclone_changed,f,indent=2)
print("LEGACY_GATE_PASS: 224 per arm, all valid controls retained, no new Cyclone faults.")
