"""Exact lawful source-guarded reverse bank for F(n)=3*n+2.

Every F-preimage witness is CONDITIONAL on the actual V115 initial
odd-run/even/odd critical pair. No unconditional Collatz result.
"""
import json
import hashlib
from collections import Counter

MOD = 3**7


def shortcut(n):
    return n//2 if n%2==0 else (3*n+1)//2


def bank(a, shift=False, M=MOD, depth=12):
    x,c = (3*a+2,3*M) if shift else (a,M)
    states=[(x,c,"")]
    seen={(x,c)}
    for _ in range(depth):
        nxt=[]
        for b,s,w in states:
            B,S=2*b,2*s
            if B>0 and S<=100*M and (B,S) not in seen:
                nxt.append((B,S,w+"E"))
                seen.add((B,S))
            if b>=2 and b%3==2 and s%3==0:
                B,S=(2*b-1)//3,(2*s)//3
                assert 3*B+1==2*b and 3*S==2*s
                if B>0 and (B,S) not in seen:
                    nxt.append((B,S,w+"O"))
                    seen.add((B,S))
        for b,s,w in nxt:
            if 0<b<a and s<=M:
                return dict(intercept=b,slope=s,reverse_word=w,steps=len(w))
        states=nxt
        if not states:
            break
    return None


def validate(a,M,w,shift=True):
    b,s=w["intercept"],w["slope"]
    assert 0<b<a and 0<s<=M
    x,c=(3*a+2,3*M) if shift else (a,M)
    for op in w["reverse_word"]:
        if op=="E":
            x,c=2*x,2*c
        else:
            assert op=="O" and x>=2 and x%3==2 and c%3==0
            old_x,old_c=x,c
            x,c=(2*x-1)//3,(2*c)//3
            assert 3*x+1==2*old_x and 3*c==2*old_c
    assert (x,c)==(b,s)
    for q in (0,1,2,7,14):
        n,p=a+M*q,b+s*q
        assert 0<p<n
        u=p
        for _ in w["reverse_word"]:
            u=shortcut(u)
        assert u==(3*n+2 if shift else n)


def has_collision(n,k):
    x=n
    for _ in range(k):
        if x%2!=1:
            return False
        x=shortcut(x)
    return x%2==0 and shortcut(x)%2==1


def main():
    old=[bank(a) for a in range(MOD)]
    shifted=[bank(a,True) for a in range(MOD)]
    assert sum(w is not None for w in old)==1013
    assert sum(w is not None for w in shifted)==333
    novel=[a for a in range(MOD)
           if old[a] is None and shifted[a] is not None]
    assert len(novel)==49
    for a,w in enumerate(shifted):
        if w is not None:
            validate(a,MOD,w)
    word_types=Counter(shifted[a]["reverse_word"] for a in novel)
    assert len(word_types)==17

    example=dict(intercept=31,slope=512,reverse_word="OEOEOOOOO",steps=9)
    validate(45,729,example)
    q=14
    n,p=45+729*q,31+512*q
    assert (n,p)==(10251,7199)
    assert has_collision(n,2)
    x,y=n,p
    for _ in range(4): x=shortcut(x)
    for _ in range(13): y=shortcut(y)
    assert x==y==17300 and x>n

    result=dict(
        schema="COLLATZ_F_TRANSPORT_REVERSE_AFFINE_BANK",
        status="BOUNDED_EXECUTABLE_CONDITIONAL_PARITY_COLLISION",
        original_q7_source_certified=1013, F_reverse_certified=333,
        F_new_outside_q7=49, F_overlap=284,
        remaining_outside_union=1125,
        F_word_types_novel=dict(sorted(word_types.items())),
        all_offset_witnesses_lean_reified=False,
        universal_source_hit=False,
        global_collatz="UNKNOWN",qed=False,
        source_45_family=dict(n_base=45,n_slope=729,p_base=31,p_slope=512,
                              word="OEOEOOOOO",steps=9),
        sample=dict(n=n,p=p,odd_prefix_length=2,
                    source_clock=4,predecessor_clock=13,
                    common_endpoint=x),
        novel_witnesses=[dict(residue=a,**shifted[a]) for a in novel])
    canonical=json.dumps(result,sort_keys=True,separators=(",",":"))
    result["payload_sha256"]=hashlib.sha256(canonical.encode()).hexdigest()
    print(json.dumps(result,sort_keys=True,indent=2))


if __name__=="__main__":
    main()
