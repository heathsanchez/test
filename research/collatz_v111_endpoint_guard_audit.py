"""V111 negative control: endpoint q7 certificates must lower ORIGINAL source.

The earlier V110 source-level CRT replay has 169,056 unresolved classes.
This audit checks each first-12-step actual forward endpoint in all of those
classes, and composes the old lawful q7 reverse words when admissible.
It rejects endpoint certificates with earlier source >= original n, even if
they show a real future coalescence, since this yields no minimal-bad exit.
"""
import json
from collections import Counter
from research.collatz_v108_reclosure import MODULUS as DYADIC, shortcut, candidates
from research.collatz_v109_reverse_reclosure import reverse_witness
from research.collatz_v110_q7_crt_reclosure import (
    TERNARY, PRODUCT, ternary_reverse, crt_base
)

def main():
    bank=[ternary_reverse(a) for a in range(TERNARY)]
    original_unknown=[r for r in range(DYADIC)
                      if not candidates(r) and reverse_witness(r) is None]
    ternary_unknown=[a for a,w in enumerate(bank) if w is None]
    assert len(original_unknown)==144 and len(ternary_unknown)==1174

    presentations=Counter()
    families_with=Counter()
    examples={}
    witnessed_smaller=0

    for r in original_unknown:
        for a in ternary_unknown:
            n0=crt_base(r,a)
            x=n0
            odds=0
            types=set()
            for j in range(1,13):
                odds += x%2
                x = shortcut(x)
                # Because PRODUCT=2^12*3^7, endpoint slope is integral.
                endpoint_slope=(DYADIC >> j) * 3**odds * TERNARY
                assert endpoint_slope % TERNARY == 0
                w=bank[x%TERNARY]
                if w is None:
                    continue
                p,c=w["predecessor"],w["slope"]
                source_base=p+c*((x-(x%TERNARY))//TERNARY)
                source_slope=c*(endpoint_slope//TERNARY)
                # These comparisons are exact for all t>=0:
                # p(t)=source_base+source_slope*t, n(t)=n0+PRODUCT*t.
                base_sign=("lt" if source_base<n0
                           else "eq" if source_base==n0 else "gt")
                slope_sign=("lt" if source_slope<PRODUCT
                            else "eq" if source_slope==PRODUCT else "gt")
                category=base_sign+"/"+slope_sign
                presentations[category]+=1
                types.add(category)
                if category not in examples:
                    examples[category]=dict(
                        dyadic_residue=r,ternary_residue=a,
                        forward_prefix=j,original_source=n0,
                        endpoint=x,reverse_predecessor=source_base,
                        source_slope=source_slope,
                        reverse_word=w["word"])
                if source_base<n0 and source_slope<=PRODUCT:
                    witnessed_smaller+=1
            for category in types:
                families_with[category]+=1

    assert witnessed_smaller==0
    assert dict(presentations)=={
        "eq/eq":231278,"gt/gt":1797394}
    assert dict(families_with)=={
        "eq/eq":169056,"gt/gt":169056}
    assert sum(presentations.values())==2028672
    assert len(original_unknown)*len(ternary_unknown)==169056

    print(json.dumps(dict(
        schema="COLLATZ_V111_ENDPOINT_Q7_SOURCE_GUARD_AUDIT",
        status="REJECTED_NO_NEW_SOURCE_MERGERS",
        global_collatz="UNKNOWN",qed=False,
        residual_crt_families=169056,
        endpoint_q7_presentations=2028672,
        exact_presentation_categories=dict(presentations),
        families_by_presentation=dict(families_with),
        lower_original_source_presentations=witnessed_smaller,
        no_source_relative_progress=True,
        tautological_or_larger_source_examples=examples,
        conclusion="Future quotient coalescence alone does not earn a lower-source merger. Preserve the exact original-source cap."),sort_keys=True,indent=2))

if __name__=="__main__":
    main()
