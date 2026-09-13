from kernel import Kernel
from challenge_pack import WORLDS

k=Kernel()
for kind in ("one_class","two_class","three_class","two_by_four","coupled_order8"):
    r=k.synthesize(WORLDS[(kind,0)])
    print("\n==",kind,"==")
    for key in (
        "status","classification","class_count","class_group_orders",
        "full_group_order","full_state_orbit_count","full_state_orbit_sizes",
        "pairwise_commuting","pairwise_trivial_intersections",
        "class_group_order_product","direct_order_match","regular_transitive_action",
        "carriers","algebra_steps",
    ):
        if key in r:
            print(key,r[key])
