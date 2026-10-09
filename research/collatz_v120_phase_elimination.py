"""V120: original-source-guarded phase-aware exact elimination.

This is *not* universal Collatz. The existing V108/V109/V110 and V112
candidate compilers define a fixed, bounded grammar. We reclose its remaining
CRT source cylinders using actual F(n)=3*n+2 collisions and lawful reverse
predecessor paths, and then contract each consequence into a minimal source
modulus. Every source family remains infinite; its warrant is grammar-relative.
"""
import argparse
from collections import Counter
import hashlib
import json
from research.collatz_v108_reclosure import MODULUS as DYADIC, candidates, shortcut
from research.collatz_v109_reverse_reclosure import reverse_witness
from research.collatz_v110_q7_crt_reclosure import TERNARY, PRODUCT, ternary_reverse, crt_base

PERIODS = sorted(2**d * 3**q for d in range(13) for q in range(8))
assert len(PERIODS) == 104 and DYADIC * TERNARY == PRODUCT

def reverse_search(x, slope, n0, source_slope, depth=12, cap_factor=50):
    """Real reverse words E(y)=2y, O(y)=(2y-1)/3 under all-offset guards."""
    seen = {(x,slope)}
    states = [(x,slope,"")]
    cap = cap_factor*source_slope
    for step in range(1,depth+1):
        remaining=depth-step
        nxt=[]
        for b,c,w in states:
            # Safe optimistic all-odd bound: cannot produce c<=source_slope.
            if c*2**(remaining+1) > source_slope*3**(remaining+1):
                continue
            bb,cc=2*b,2*c
            if bb>0 and cc<cap and (bb,cc) not in seen:
                nxt.append((bb,cc,w+"E"))
                seen.add((bb,cc))
            if b>=2 and b%3==2 and c%3==0:
                bb,cc=(2*b-1)//3,2*c//3
                assert 3*bb+1==2*b and 3*cc==2*c
                if bb>0 and (bb,cc) not in seen:
                    nxt.append((bb,cc,w+"O"))
                    seen.add((bb,cc))
        for b,c,w in nxt:
            if 0<b<n0 and 0<c<=source_slope:
                return b,c,w
        states=nxt
        if not states: break
    return None

def v112_predecessor(n0):
    """Exact baseline: all genuine forward prefixes up to 12, reverse up to 12."""
    x,odd=n0,0
    for j in range(1,13):
        odd+=x%2
        x=shortcut(x)
        slope=(DYADIC>>j)*3**odd*TERNARY
        found=reverse_search(x,slope,n0,PRODUCT,12,50)
        if found:return (j,)+found
    return None

def F_collision_affine(n0,m):
    """All-offset F collision grammar, restricted to odd transport and close.
    Swap is deliberately not in the V120 bounded discovery grammar.
    """
    clock=0
    path=[]
    for _ in range(15):
        if n0%4==2 and m%4==0:
            return clock+2,path+["close"]
        if n0%2==1 and m%2==0:
            n0,m=shortcut(n0),3*m//2
            path.append("odd")
            clock+=1
        else:return None
        if clock>12:return None
    return None

def reverse_replay(x,a,word):
    for op in word:
        if op=="E":x,a=2*x,2*a
        elif op=="O" and x>=2 and x%3==2 and a%3==0:
            x,a=(2*x-1)//3,2*a//3
        else:return None
    return x,a

def compact_rule(n0,m,word):
    fc=F_collision_affine(n0,m)
    if fc is None:return None
    z=reverse_replay(3*n0+2,3*m,word)
    if z is None:return None
    p,c=z
    if not(0<p<n0 and 0<c<=m):return None
    return dict(residue=n0,modulus=m,collision_clock=fc[0],
        collision_path=fc[1],reverse_word=word,reverse_clock=len(word),
        predecessor=p,slope=c)

def build():
    dyadic=[r for r in range(DYADIC)
        if not candidates(r) and reverse_witness(r) is None]
    ternary=[a for a in range(TERNARY) if ternary_reverse(a) is None]
    assert len(dyadic)==144 and len(ternary)==1174
    counts=Counter()
    records=[]
    for r in dyadic:
        for a in ternary:
            n0=crt_base(r,a)
            if v112_predecessor(n0) is not None:
                counts["v112_covered"]+=1
                continue
            counts["v112_unknown"]+=1
            if n0%16==11 and n0%729==45:
                counts["earlier_F_93"]+=1
                continue
            collision=F_collision_affine(n0,PRODUCT)
            if collision is None:continue
            found=reverse_search(3*n0+2,3*PRODUCT,n0,PRODUCT,14,80)
            if not found:continue
            p,c,word=found
            records.append(dict(residue=n0,dyadic=r,ternary=a,
                predecessor=p,slope=c,reverse_word=word,
                reverse_clock=len(word),collision_clock=collision[0],
                collision_path=collision[1]))
    assert counts["v112_covered"]==4617
    assert counts["v112_unknown"]==164439
    assert counts["earlier_F_93"]==93
    assert len(records)==4408
    # Contract to the least exact source modulus. No strengthened claim from
    # finite samples: guard and affine predecessor relation must hold for all q.
    compact={}
    for record in records:
        n0=record["residue"]
        word=record["reverse_word"]
        chosen=None
        for m in PERIODS:
            chosen=compact_rule(n0%m,m,word)
            if chosen is not None:break
        assert chosen is not None
        key=(chosen["modulus"],chosen["residue"],word,
             tuple(chosen["collision_path"]))
        compact[key]=chosen
    rules=sorted(compact.values(),key=lambda z:(
        z["modulus"],z["residue"],z["reverse_word"]))
    assert len(rules)==149
    assert len(set(r["reverse_word"] for r in rules))==17
    assert len(set(tuple(r["collision_path"]) for r in rules))==9
    unknown=counts["v112_unknown"]-counts["earlier_F_93"]-len(records)
    assert unknown==159938
    payload=dict(schema="COLLATZ_V120_PHASE_AWARE_ELIMINATION",
        source_modulus=PRODUCT,source_guard="0<p0<n0 AND 0<c<=M",
        v112_covered=4617,v112_unresolved=164439,
        earlier_F_covered=93,new_classes=len(records),
        minimized_rules=len(rules),reverse_word_types=17,
        collision_path_types=9,unknown_classes=unknown,
        global_collatz="UNKNOWN",qed=False,
        kernel_reified_individual_rules=False,rules=rules,records=records)
    c=json.dumps(payload,sort_keys=True,separators=(",",":")).encode()
    payload["payload_sha256"]=hashlib.sha256(c).hexdigest()
    return payload

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("--out",required=True)
    args=parser.parse_args()
    payload=build()
    with open(args.out,"w") as f:
        json.dump(payload,f,indent=2,sort_keys=True)
    print(json.dumps({k:payload[k] for k in (
        "source_modulus","v112_covered","v112_unresolved",
        "earlier_F_covered","new_classes","minimized_rules",
        "reverse_word_types","collision_path_types","unknown_classes",
        "payload_sha256","global_collatz","qed")},sort_keys=True))
if __name__=="__main__":main()
