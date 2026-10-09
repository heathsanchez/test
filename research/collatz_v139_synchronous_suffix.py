"""V139 independent regression for synchronous clock suffix gauge invariance.

The universal proof is a pinned Lean theorem, not finite observation.
When actual T^i(a)=T^j(p), extending both clocks by a common k
preserves the sign of
    2^j*3^oddCount(a,i) - 2^i*3^oddCount(p,j).
The scalar ratio is unchanged because both get common factor
    (3/2)^(oddCount(shared_endpoint,k)/k) in exact integer form.

Combined with V137 multiplier completeness, a rejected chart clock
orientation cannot be repaired by more integer multipliers OR
synchronous waiting; only changing the relative phase/meeting
endpoint/protected earlier-source base can alter admissibility.
"""
import hashlib,json

def T(n):
    assert n>0
    return n//2 if n%2==0 else (3*n+1)//2

def trace(n,k):
    o=0;x=n
    for _ in range(k):
        o+=x%2
        x=T(x)
    return x,o

def case(a,p,i,j,limit=150):
    endpoint,alpha=trace(a,i)
    other,beta=trace(p,j)
    assert 0<p<a and endpoint==other
    h0=2**j*3**alpha<=2**i*3**beta
    suffixes=[]
    for k in range(limit+1):
        ya,alphak=trace(a,i+k)
        yp,betak=trace(p,j+k)
        y,gamma=trace(endpoint,k)
        assert ya==yp==y
        assert alphak==alpha+gamma
        assert betak==beta+gamma
        hg=2**(j+k)*3**alphak<=2**(i+k)*3**betak
        assert hg==h0
        suffixes.append([k,gamma,int(hg)])
    return dict(source=a,earlier=p,
        initial_source_clock=i,initial_earlier_clock=j,
        initial_source_odds=alpha,initial_earlier_odds=beta,
        initial_meeting_endpoint=endpoint,
        source_guard_admitted=h0,
        exact_checked_common_suffixes=len(suffixes),
        sampled_suffixes=[suffixes[k] for k in (0,1,2,7,31,limit)],
        no_common_suffix_changes_guard=True)

def main():
    examples=[
       case(5,3,1,2),
       case(5,3,3,8),
       case(21,3,3,2),
       case(9,3,9,1),
       case(23,3,7,1),
       case(27,3,66,1),
       case(27,23,59,0),
    ]
    assert examples[0]["source_guard_admitted"] is True
    assert examples[1]["source_guard_admitted"] is False
    assert examples[0]["source"]==examples[1]["source"]==5
    assert examples[0]["earlier"]==examples[1]["earlier"]==3
    assert all(x["no_common_suffix_changes_guard"] for x in examples)
    assert all(x["exact_checked_common_suffixes"]==151 for x in examples)
    r=dict(schema="COLLATZ_V139_SYNCHRONOUS_CLOCK_GAUGE_INVARIANCE",
      status="BOUNDED_REGRESSION_PLUS_FORMAL_CANDIDATE",
      exact_trace_pairs=len(examples),
      common_suffixes_per_pair=151,
      separate_formal_lemma="oddCount(n,i+k)=oddCount(n,i)+oddCount(T^i(n),k)",
      orientation_unchanged_under_common_suffix=True,
      rejected_5_to3_bad_clock_never_rescued=True,
      alternate_5_to3_good_clock_admissible=True,
      multiplier_search_after_rejection_unnecessary_by_V137=True,
      fixed_source_nonconvergence_NOT_implied=True,
      universal_collatz="UNKNOWN",qed=False,
      regressions=examples)
    canon=json.dumps(r,sort_keys=True,separators=(",",":"))
    r["payload_sha256"]=hashlib.sha256(canon.encode()).hexdigest()
    print(json.dumps(r,indent=2,sort_keys=True))

if __name__=="__main__":
    main()
