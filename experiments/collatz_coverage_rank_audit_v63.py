"""Exact fixed-origin rank falsifier; no protected grammar membership claimed."""
import hashlib
import json


def shortcut(n):
    return n//2 if n%2==0 else (3*n+1)//2


def order(x):
    assert x!=0
    v=0
    while x%2==0:
        x//=2
        v+=1
    return v


def main():
    lower_bank=set()
    for p in range(1,27):
        seen=set()
        while p not in seen:
            assert len(seen)<1000
            seen.add(p)
            lower_bank.add(p)
            p=shortcut(p)
    assert len(lower_bank)==34 and max(lower_bank)==80
    assert all(shortcut(p) in lower_bank for p in lower_bank)
    path=[27]
    for _ in range(15):
        path.append(shortcut(path[-1]))
    witness=path[12:16]
    assert witness==[137,206,103,155]
    assert all(x>27 and x not in lower_bank and x not in [1,2] for x in witness)
    assert 27//2**12==0
    A,B,P,L=9,7,8,27
    x,y=witness[0],witness[-1]
    assert P*y==A*x+B
    W=(P-A)*L-B
    defects=[-x-1,-y-1]
    injection=(-1)*B-(P-A)
    assert P*defects[1]==A*defects[0]+injection
    valuations=list(map(order,defects))
    assert W==-34 and valuations==[1,2] and order(injection)==1
    d=dict(schema='COLLATZ_COVERAGE_RANK_AUDIT_V63',
        source=27,depths=[12,13,14,15],actual_macro=witness,
        lower_source_forward_closed_bank=sorted(lower_bank),
        source_tail=0,no_exit_at_all_four_witness_states=True,
        affine_law=dict(A=A,B=B,P=P,original_floor=L,budget=W),
        reference=dict(A=3,B=1,P=2),defects=defects,dyadic_orders=valuations,
        injection=injection,injection_order=order(injection),
        coverage='universal exact source-product zero-tail admission proved; protected-return grammar admission remains UNKNOWN',
        progress='zero-injection strict rank proved; fixed-reference strict rank on arbitrary nonpositive-budget natural macros REFUTED',
        well_foundedness='natural rank chain exhaustion proved; globally decreasing rank not supplied',
        protected_return_grammar_membership='NOT_ESTABLISHED',
        universal_progress='UNKNOWN',global_collatz='UNKNOWN',qed=False,
        boundary='finite actual no-exit segment; does not refute eventual progress or assert an infinite counterexample',
        adaptation='require an exact grammar exclusion or an additional warranted progress coordinate for this recharge; do not infer either from observed recurrence')
    d['certificate_sha256']=hashlib.sha256(json.dumps(d,sort_keys=True).encode()).hexdigest()
    print(json.dumps(d,indent=2,sort_keys=True))

if __name__=='__main__':
    main()
