"""V130 exact external-prover regression: pump P(r)=64*r+21.

P preserves odd multiples of three and actual future coalescence
T^7(P(r))=T(r); its iterates generate unbounded distinct positive odd
three roots in ANY positive coalescence class. This is a FORMAL theorem
candidate; this bounded program is not its universal proof.

All witnessed class edges are CLASS IDENTITY only: a pumped root is
larger than the original root, not a strictly-earlier source.
"""
import hashlib, json

from research.collatz_v126_three_root_normal_form import T,replay
from research.collatz_v127_odd_three_root_replay import odd_root_view

def pump(r):
    return 64*r+21

def pumped(r,k):
    for _ in range(k):
        r=pump(r)
    return r

def main():
    rows=[]
    for r in (3,9,15,21,33,51,123,195,333):
        assert r%6==3
        for k in range(0,21):
            q=pumped(r,k)
            assert q%6==3
            assert q>=k and q>=r
            assert replay(q,6*k+1)==T(r)
            if k:
                assert q>r
            if k in (0,1,2,5,10,20):
                rows.append({"root":r,"pump_count":k,
                    "expanded_root":str(q),
                    "expanded_clock":6*k+1,
                    "root_clock":1,"common_endpoint":T(r)})
    count=0
    for n in range(1,2001):
        w=odd_root_view(n)
        r,a,b=w['odd_three_root'],w['source_clock'],w['root_clock']
        for k in range(0,6):
            q=pumped(r,k)
            assert q%6==3
            assert replay(n,a+1)==replay(q,6*k+1+b)
            count+=1
    data={
        "schema":"COLLATZ_V130_UNBOUNDED_ODD_ROOT_FUTURE_CLASS_PUMP",
        "status":"BOUNDED_EXACT_AND_FORMAL_CANDIDATE",
        "pump_rule":"P(r)=64*r+21",
        "pump_actual_future_rule":"T^(6k+1)(P^k(r))=T(r)",
        "pump_input":"r>0 and r%6=3",
        "symbolic_unbounded_growth":"P^k(r)>=k, with strict increase",
        "initial_root_regressions":9*21,
        "general_source_root_two_clock_regressions":count,
        "selected_examples":rows,
        "all_classes_have_arbitrarily_large_odd3_roots_FORMAL_PENDING":True,
        "class_identity_NOT_smaller_source_progress":True,
        "universal_collatz":"UNKNOWN","qed":False
    }
    payload=json.dumps(data,sort_keys=True,separators=(",",":"))
    data["payload_sha256"]=hashlib.sha256(payload.encode()).hexdigest()
    print(json.dumps(data,sort_keys=True,indent=2))

if __name__=="__main__":
    main()
