"""V135 canonical cross-valuation parity chart synthesis.

For a proven base collision T^i(a)=T^j(p), odd counts α and β,
the FREE multiplier search in V131 is unnecessary for one canonical
positive pair:
    u=3^β, v=3^α.
This guarantees both all-offset endpoint coefficients agree.

A source-relative strict earlier class merger for EVERY t>=0 follows
only if 0<p<a and 2^j*3^α <= 2^i*3^β.
Neither this weighted guard nor the base collision is universal.

The same original source pair (5,3) has an oriented good clock pair
(1,2) but an adverse one (3,8); clocks remain protected semantic data.
This is a true exact all-offset coefficient computation, not a QED.
"""
import json,hashlib

def T(n:int)->int:
    assert n>0
    return n//2 if n%2==0 else (3*n+1)//2

def affine_step(b:int,s:int):
    assert s%2==0, "parity cylinder source slope not uniformly even"
    return (b//2,s//2) if b%2==0 else ((3*b+1)//2,3*s//2)

def prefix(base:int,clock:int,coefficient:int):
    b,s=base,(1<<clock)*coefficient
    odds=0
    steps=[(b,s)]
    for _ in range(clock):
        odds+=b%2
        b,s=affine_step(b,s)
        steps.append((b,s))
    assert s==3**odds*coefficient
    return dict(base=base,clock=clock,odd_count=odds,
        offset_factor=coefficient,source_slope=(1<<clock)*coefficient,
        endpoint_base=b,endpoint_slope=s,
        prefix=steps)

def bare(base:int,clock:int):
    x=base;o=0
    for _ in range(clock):
        o+=x%2
        x=T(x)
    return x,o

def chart_pair(a:int,p:int,i:int,j:int):
    assert 0<p<a
    ya,alpha=bare(a,i)
    yp,beta=bare(p,j)
    if ya!=yp: raise ValueError("no real base collision")
    u,v=3**beta,3**alpha
    source=prefix(a,i,u)
    earlier=prefix(p,j,v)
    assert source['endpoint_base']==earlier['endpoint_base']
    assert source['endpoint_slope']==earlier['endpoint_slope']==3**(alpha+beta)
    allowed=source['source_slope']>=earlier['source_slope']
    example=dict(
        base_source=a,base_earlier=p,source_clock=i,earlier_clock=j,
        odds_source=alpha,odds_earlier=beta,
        auto_u=u,auto_v=v,
        source_slope=source['source_slope'],
        earlier_slope=earlier['source_slope'],
        meeting_endpoint=ya,
        common_endpoint_slope=source['endpoint_slope'],
        strict_original_source_guard_for_all_offsets=allowed,
        exact_source_prefix=source['prefix'],
        exact_earlier_prefix=earlier['prefix'],
    )
    if allowed:
        for t in (0,1,2,7,64):
            n=a+source['source_slope']*t
            q=p+earlier['source_slope']*t
            assert 0<q<n
            assert ya+source['endpoint_slope']*t == (
               yp+earlier['endpoint_slope']*t)
            x,y=n,q
            for _ in range(i):x=T(x)
            for _ in range(j):y=T(y)
            assert x==y==ya+3**(alpha+beta)*t
    return example

def main():
    verified=[
        chart_pair(21,3,3,2),
        chart_pair(9,3,9,1),
        chart_pair(15,3,8,1),
        chart_pair(23,3,7,1),
        chart_pair(5,3,1,2),
        chart_pair(27,23,59,0),
    ]
    assert all(x['strict_original_source_guard_for_all_offsets'] for x in verified)
    assert [(x['auto_u'],x['auto_v']) for x in verified]==[
        (9,3),(3,243),(3,81),(3,27),(9,3),(1,3**37)]
    assert [(x['source_slope'],x['earlier_slope']) for x in verified[:5]]==[
        (72,12),(1536,486),(768,162),(384,54),(18,12)]
    assert verified[5]['source_slope']==2**59
    assert verified[5]['earlier_slope']==3**37
    assert verified[5]['meeting_endpoint']==23

    negative=chart_pair(5,3,3,8)
    assert not negative['strict_original_source_guard_for_all_offsets']
    assert negative['meeting_endpoint']==2
    assert (negative['odds_source'],negative['odds_earlier'])==(1,4)
    assert (negative['source_slope'],negative['earlier_slope'])==(648,768)
    assert verified[4]['base_source']==negative['base_source']==5
    assert verified[4]['base_earlier']==negative['base_earlier']==3
    result=dict(
        schema='COLLATZ_V135_CROSS_POWER_SOURCE_CHART_CANONICALIZATION',
        status='EXACT_AFFINE_CROSS_COUNT_REPLAY_FORMAL_CANDIDATE',
        canonical_rule='u=3^oddCount(p,j),v=3^oddCount(a,i)',
        sufficient_clock_guard='2^j*3^oddCount(a,i) <= 2^i*3^oddCount(p,j)',
        examples=verified,
        adverse_clock_control=negative,
        input_pair_identity_preserved=True,
        actual_both_clocks_preserved=True,
        explicit_multiplier_search_eliminated_for_canonical_sufficient_lift=True,
        no_uniqueness_of_all_coefficients_claim=True,
        no_universal_favourable_clock_claim=True,
        only_genuinely_smaller_source_guards_admitted=True,
        universal_collatz='UNKNOWN',qed=False)
    canonical=json.dumps(result,sort_keys=True,separators=(',',':'))
    result['payload_sha256']=hashlib.sha256(canonical.encode()).hexdigest()
    print(json.dumps(result,sort_keys=True,indent=2))

if __name__=='__main__':
    main()
