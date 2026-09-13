from kernel import Kernel
from challenge_pack import KINDS,WORLDS,UNIVERSE,constant_single_open

k=Kernel()

for kind in KINDS:
    r=k.synthesize(WORLDS[(kind,0)])
    print("\n==",kind,"==")
    for key in (
        "status","reason","completion_count","tested_completions",
        "floor_future_depth","state_count","token_classes",
        "law_kinds_consistent_with_evidence","determinism_identifiable",
        "forced_branching_histories",
    ):
        if key in r:
            print(key,r[key])
    if r.get("status")=="UNKNOWN_IDENTIFIABILITY":
        for wname in ("witness_a","witness_b"):
            w=r[wname]
            print(wname,{
                x:w.get(x)
                for x in ("law_kind","floor_status","floor_future_depth","state_count","token_classes")
            })

print("\n== constant closure criticality ==")
critical=[]
noncritical=[]
other=[]
for i,h in enumerate(UNIVERSE):
    r=k.synthesize(constant_single_open(i))
    row=(i,h,r.get("status"),r.get("completion_count"),r.get("tested_completions"),
         r.get("state_count"),r.get("determinism_identifiable"))
    print(row)
    if r.get("status")=="UNKNOWN_IDENTIFIABILITY":
        critical.append((i,h))
    elif r.get("status")=="VERIFIED_IDENTIFIABLE_BEHAVIORAL_FLOOR":
        noncritical.append((i,h))
    else:
        other.append((i,h,r))
print("critical_count",len(critical))
print("critical_lengths",sorted({len(h) for _,h in critical}))
print("noncritical_count",len(noncritical))
print("noncritical_lengths",sorted({len(h) for _,h in noncritical}))
print("other_count",len(other))
