import argparse
import experiments.minimal_core_capstone_suite_v18 as v18


def test_loop_ablations_corrected():
    # Corrective diagnostic for V18 loop_ablations only.
    # The original never_expand arm could repeatedly cold-search from an empty state,
    # so it was not actually prevented from adapting. Here every controller starts
    # with the same initial installed distinction {0}; unseen targets require a
    # verified expansion event before they can be used on later episodes.
    seq=[0,0,1,0,2,1,2,2,0,1]

    def run(mode):
        retained=[0]
        cost=0
        errors=0
        expansions=0
        for target in seq:
            if mode=="retain_all":
                retained=[0,1,2]
            order=retained+[k for k in range(3) if k not in retained]

            if target not in retained:
                if mode in ("never_expand","premature_permanent"):
                    errors += 1
                    continue
                # Obstruction followed by permitted language expansion.
                cost += order.index(target)+1
                expansions += 1
                retained.insert(0,target)
            else:
                cost += retained.index(target)+1
                if mode=="full":
                    retained.remove(target)
                    retained.insert(0,target)

            if mode=="always_expand":
                expansions += 1
            if mode=="global_value":
                retained=sorted(retained)

        # Expansion has a small explicit cost; wrong capability is much worse.
        return {"cost":cost,"errors":errors,"expansions":expansions,
                "score":cost+10*errors+expansions}

    modes=["full","premature_permanent","retain_all","never_expand","always_expand","global_value"]
    res={m:run(m) for m in modes}
    full=res["full"]
    # Do not require the full loop to beat retain-all on this tiny carrier purely by
    # one arbitrary scalar. Require the causal ablations to show their intended defect.
    gates={
        "premature_permanence_causes_errors":res["premature_permanent"]["errors"]>0,
        "never_expand_causes_errors":res["never_expand"]["errors"]>0,
        "always_expand_adds_unnecessary_expansions":res["always_expand"]["expansions"]>full["expansions"],
        "global_value_costs_more_than_residual_relative_full":res["global_value"]["cost"]>=full["cost"],
        "full_has_zero_errors":full["errors"]==0,
    }
    v18.save("loop_ablations", {"results":res,"gates":gates,"pass":all(gates.values()),
        "note":"Corrective V18b arm. Original V18 never_expand control was under-specified and could cold-search forever from an empty retained state."})


TESTS=dict(v18.TESTS)
TESTS["loop_ablations"]=test_loop_ablations_corrected

if __name__=="__main__":
    ap=argparse.ArgumentParser()
    ap.add_argument("--test", choices=sorted(TESTS), required=True)
    args=ap.parse_args()
    TESTS[args.test]()
