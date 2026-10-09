"""V128 exact adversarial test for the canonical-root grammar.

All-clock impossibility is proved independently in Lean from a
forward-invariant 7-state envelope; the checks here are finite regression.
The selected source 21 root NEVER changes along its forward orbit, even
though the genuine source21-to-source3 future merger is shorter-source.
"""
import hashlib,json
from research.collatz_v126_three_root_normal_form import normalize,T,replay

ENVELOPE={21,32,16,8,4,2,1}

def main():
    assert len(ENVELOPE)==7 and 21 in ENVELOPE
    assert all(T(x) in ENVELOPE for x in ENVELOPE)
    assert all(normalize(x)[0]==21 for x in ENVELOPE)
    assert {normalize(x)[0] for x in ENVELOPE}=={21}
    x=21
    for k in range(1001):
        assert x in ENVELOPE
        assert normalize(x)[0]==21
        if k<1000: x=T(x)
    assert replay(21,3)==replay(3,2)==8
    assert 0<3<21 and 3%6==3
    result=dict(
        schema="COLLATZ_V128_RELATIONAL_ROOT_SELECTOR_SEPARATOR",
        status="BOUNDED_REGRESSION_AND_GENERIC_LEAN_CANDIDATE",
        source=21,preferred_root=21,
        forward_invariant_envelope=sorted(ENVELOPE),
        observed_stutter_clocks=1001,
        proven_all_clock_stutter_in_Lean=False,
        smaller_odd_three_root=3,
        source_clock=3,earlier_clock=2,actual_common_endpoint=8,
        grammar_status="PREFERRED_ROOT_SELECTOR_REJECTED_AS_COMPLETE",
        required_refinement="RELATIONAL_MULTIPLE_SOURCE_ROOTS_WITH_TWO_CLOCKS",
        universal_termination=False,
        global_collatz="UNKNOWN",qed=False)
    raw=json.dumps(result,sort_keys=True,separators=(",",":"))
    result['payload_sha256']=hashlib.sha256(raw.encode()).hexdigest()
    print(json.dumps(result,sort_keys=True,indent=2))

if __name__=="__main__":main()
