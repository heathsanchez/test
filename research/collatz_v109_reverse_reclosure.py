"""V109 bounded symbolic reclosure: actual even/odd reverse words, not free affine guesses."""
import json
from collections import Counter
from research.collatz_v108_reclosure import MODULUS, DEPTH, candidates, prefixes, shortcut

MAX_REVERSE = 12

def reverse_witness(r):
    for j, x, odd, a in prefixes(r):
        states = [(x,a,"")]
        seen = {(x,a)}
        for d in range(1, MAX_REVERSE+1):
            nxt = []
            for b,c,word in states:
                # shortcut(2*y)=y
                bb,cc = 2*b, 2*c
                if bb>0 and cc < 50*MODULUS and (bb,cc) not in seen:
                    nxt.append((bb,cc,word+"E"))
                    seen.add((bb,cc))
                # shortcut((2*y-1)/3)=y, with exact affine divisibility.
                if b>=2 and b%3==2 and c%3==0:
                    bb,cc = (2*b-1)//3, (2*c)//3
                    assert 3*bb+1==2*b and 3*cc==2*c
                    if bb>0 and (bb,cc) not in seen:
                        nxt.append((bb,cc,word+"O"))
                        seen.add((bb,cc))
            for b,c,word in nxt:
                if b<r and c<=MODULUS:
                    return dict(steps=j,intercept=x,coefficient=a,odd_count=odd,
                        reverse_steps=d,reverse_word=word,
                        predecessor_intercept=b,predecessor_coefficient=c)
            states=nxt
            if not states: break
    return None

def validate(r,w):
    j,t=w["steps"],w["reverse_steps"]
    assert t==len(w["reverse_word"]) and t>0
    x,a=w["intercept"],w["coefficient"]
    p,c=w["predecessor_intercept"],w["predecessor_coefficient"]
    assert 0<p<r and 0<=c<=MODULUS
    cur_x,cur_a=x,a
    for op in w["reverse_word"]:
        if op=="E":
            cur_x,cur_a=2*cur_x,2*cur_a
        else:
            assert op=="O" and cur_x>=2 and cur_x%3==2 and cur_a%3==0
            before_x,before_a=cur_x,cur_a
            cur_x,cur_a=(2*cur_x-1)//3,(2*cur_a)//3
            assert 3*cur_x+1==2*before_x and 3*cur_a==2*before_a
    assert (cur_x,cur_a)==(p,c)
    for q in (0,1,2,7,19):
        n=r+MODULUS*q
        y=n
        for _ in range(j): y=shortcut(y)
        p_q=p+c*q
        v=p_q
        for _ in range(t): v=shortcut(v)
        assert y==x+a*q==v and 0<p_q<n

def main():
    counts=Counter()
    records=[]
    for r in range(MODULUS):
        if candidates(r):
            counts["v108_cylinders"]+=1
            continue
        w=reverse_witness(r)
        if w is None:
            counts["unknown_cylinders"]+=1
            records.append(dict(residue=r,status="UNKNOWN_AFTER_MIXED_REVERSE_REPLAY"))
            continue
        validate(r,w)
        counts["new_reverse_merged_cylinders"]+=1
        records.append(dict(residue=r,status="NEW_GUARDED_LOWER_SOURCE_MERGER",**w))
    assert counts["v108_cylinders"]==3904
    assert counts["new_reverse_merged_cylinders"]==48
    assert counts["unknown_cylinders"]==144
    assert sum(counts.values())==MODULUS
    print(json.dumps(dict(schema="COLLATZ_V109_BOUNDED_MIXED_REVERSE_REPLAY",
        status="BOUNDED_EXACT_ONLY",global_collatz="UNKNOWN",qed=False,
        depth=DEPTH,max_reverse=MAX_REVERSE,counts=dict(counts),
        residual_and_new_records=records),sort_keys=True,indent=2))

if __name__=="__main__":
    main()
