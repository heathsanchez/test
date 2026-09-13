from kernel import Kernel
from challenge_pack import KINDS,WORLDS,HIDDEN_GENERATOR_STATE_COUNT

k=Kernel()
for kind in KINDS:
    r=k.synthesize(WORLDS[(kind,0)])
    print("\n==",kind,"hidden",HIDDEN_GENERATOR_STATE_COUNT[kind],"==")
    for key in (
        "status","classification","floor_future_depth","state_count",
        "token_class_count","token_classes",
        "pairwise_distinguishing_witness_count",
        "maximum_minimal_distinguishing_depth",
        "right_congruence","stable_to_next_horizon",
        "tested",
    ):
        if key in r:
            print(key,r[key])

print("\n== delayed horizon ablations ==")
for bound in (1,2,3,4):
    r=k.synthesize(WORLDS[("delayed_four",0)],maximum_future_depth_override=bound)
    print(bound,r.get("status"),r.get("floor_future_depth"),r.get("state_count"),r.get("tested"))
