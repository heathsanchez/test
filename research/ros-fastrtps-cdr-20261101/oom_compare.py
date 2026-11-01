#!/usr/bin/env python3
"""Conservative exploratory comparison. No auto-promotion from a green workflow."""
import collections
import json

def read(arm):
    r=json.load(open("/evidence/results-"+arm+".json"))
    return {(x["type"],x["variant"],x["budget_mib"],x.get("count")):x for x in r}

b=read("baseline")
p=read("patched")
assert set(b)==set(p)
controls=[k for k in b if k[1]=="control"]
assert len(controls)==8
for k in controls:
    assert b[k]["outcome"]=="accepted" and p[k]["outcome"]=="accepted",(k,b[k],p[k])

for arm,results in (("baseline",b),("patched",p)):
    c=collections.Counter(x["outcome"] for x in results.values())
    print(arm,"OUTCOMES",dict(c))
    for key in sorted(results, key=lambda x:str(x)):
        if key[1]!="control" and results[key]["outcome"] not in ("error",):
            x=results[key]
            print(arm,"NON_ERROR",json.dumps({"case":key,"outcome":x["outcome"],
                "detail":x.get("detail"),"rss_kib":x.get("maxrss_kib")}))
delta=[{"case":key,"before":b[key],"after":p[key]} for key in b
       if b[key]["outcome"]!=p[key]["outcome"]]
print("DIFFERENCES",json.dumps(delta))
with open("/evidence/residual-differential.json","w") as file:
    json.dump({"deltas":delta,"baseline":list(b.values()),"patched":list(p.values())},file,indent=2)
patched_nonerror=[x for k,x in p.items()
                  if k[1]!="control" and x["outcome"] not in ("error",)]
print("RESIDUAL_NONERROR_COUNT",len(patched_nonerror))
print("CONTROL_GATE_PASS",len(controls),"/",len(controls))
print("EPIS_FAILURES_NEED_ANALYSIS: experiment is bounded to available test_msgs layouts and virtual-memory caps.")
