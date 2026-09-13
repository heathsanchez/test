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
        print("witness_a",{
            x:r["witness_a"].get(x)
            for x in ("law_kind","floor_status","floor_future_depth","state_count","token_classes")
        })
        print("witness_b",{
            x:r["witness_b"].get(x)
            for x in ("law_kind","floor_status","floor_future_depth","state_count","token_classes")
        })

print("\n== constant single-open closure ablations ==")
bad=[]
for i,h in enumerate(UNIVERSE):
    r=k.synthesize(constant_single_open(i))
    print(i,h,r.get("status"),r.get("completion_count"),r.get("tested_completions"),
          r.get("witness_a",{}).get("state_count"),r.get("witness_b",{}).get("state_count"),
          r.get("witness_b",{}).get("floor_status"))
    if r.get("status")!="UNKNOWN_IDENTIFIABILITY":
        bad.append((i,h,r))
print("non_unknown_count",len(bad))
