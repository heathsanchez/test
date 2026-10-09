"""V110 source-coalescence replay: dyadic V109 frontier x q7 3-adic bank.

This is an exact finite source-family certificate compiler, not global Collatz.
For every certified pair (r mod 4096, a mod 2187), CRT gives a unique
natural residue n0 mod 4096*2187. The q7 reverse word yields
p(n0+L*t)=p0+c*(s0+4096*t)<n0+L*t for every t>=0.
Proof schemata are in Collatz.ReverseAffineMerger.lean (subject to Lean gate).
"""
import json
from collections import Counter
from research.collatz_v108_reclosure import MODULUS as DYADIC, candidates, shortcut
from research.collatz_v109_reverse_reclosure import reverse_witness

TERNARY = 3**7
PRODUCT = DYADIC * TERNARY
MAX_REVERSE = 12

def ternary_reverse(a):
    """Strict base-and-slope merger at n=a+2187*s, valid for all s>=0."""
    states = [(a, TERNARY, "")]
    seen = {(a, TERNARY)}
    for _ in range(MAX_REVERSE):
        nxt = []
        for b,c,w in states:
            bb,cc = 2*b,2*c
            if bb>0 and cc <= 100*TERNARY and (bb,cc) not in seen:
                nxt.append((bb,cc,w+"E"))
                seen.add((bb,cc))
            if b>=2 and b%3==2 and c%3==0:
                bb,cc = (2*b-1)//3,2*c//3
                assert 3*bb+1 == 2*b and 3*cc == 2*c
                if bb>0 and (bb,cc) not in seen:
                    nxt.append((bb,cc,w+"O"))
                    seen.add((bb,cc))
        for b,c,w in nxt:
            if 0<b<a and c<=TERNARY:
                return dict(residue=a,predecessor=b,slope=c,word=w)
        states=nxt
        if not states: break
    return None

def replay_word(w):
    """This checks the *symbolic* inverse-affine identities, not just samples."""
    x,c = w["residue"],TERNARY
    for op in w["word"]:
        if op=="E":
            x,c = 2*x,2*c
        else:
            assert op=="O" and x>=2 and x%3==2 and c%3==0
            before_x,before_c=x,c
            x,c=(2*x-1)//3,2*c//3
            assert 3*x+1==2*before_x and 3*c==2*before_c
    assert (x,c)==(w["predecessor"],w["slope"])
    assert 0<x<w["residue"] and c<=TERNARY

def crt_base(r,a):
    # 4096 and 2187 are coprime, and the pair has one residue mod product.
    q0 = ((a-r)*pow(DYADIC,-1,TERNARY)) % TERNARY
    n0 = r + DYADIC*q0
    assert 0<=n0<PRODUCT and n0%DYADIC==r and n0%TERNARY==a
    return n0

def main():
    bank = [ternary_reverse(a) for a in range(TERNARY)]
    earned = [w for w in bank if w is not None]
    for w in earned: replay_word(w)
    words=Counter(w["word"] for w in earned)
    assert len(earned)==1013 and len(words)==13

    residual=[]
    for r in range(DYADIC):
        if not candidates(r) and reverse_witness(r) is None:
            residual.append(r)
    assert len(residual)==144

    # Verify every CRT intersection, with exact affine formula and sample traces.
    count=0
    example=None
    for r in residual:
        for w in earned:
            a,p,c = w["residue"],w["predecessor"],w["slope"]
            n0=crt_base(r,a)
            s0=(n0-a)//TERNARY
            assert s0>=0 and n0==a+TERNARY*s0
            pbase=p+c*s0
            assert 0<pbase<n0
            assert c*DYADIC<=PRODUCT
            for t in (0,1):
                n=n0+PRODUCT*t
                source=pbase+c*DYADIC*t
                assert 0<source<n
                y=source
                for _ in w["word"]: y=shortcut(y)
                assert y==n
            count+=1
            if example is None:
                example=dict(dyadic_residue=r,ternary_residue=a,
                    crt_source=n0,earlier_source=pbase,
                    reverse_word=w["word"],source_slope=c*DYADIC)
    assert count==144*1013
    covered=3952*TERNARY+count
    unknown=144*(TERNARY-1013)
    assert covered+unknown==PRODUCT
    result=dict(schema="COLLATZ_V110_Q7_CRT_SOURCE_COALESCENCE",
                status="BOUNDED_EXACT_ONLY",global_collatz="UNKNOWN",qed=False,
                dyadic_depth=12,ternary_depth=7,combined_modulus=PRODUCT,
                predecessor_word_types=dict(sorted(words.items())),
                q7_covered_ternary=1013,q7_unknown_ternary=1174,
                v109_covered_dyadic=3952,v109_unknown_dyadic=144,
                additional_crt_source_families=count,
                total_covered_crt_source_families=covered,
                remaining_unknown_crt_source_families=unknown,
                remaining_unknown_dyadic_residues=residual,
                witness_bank=earned,example=example)
    print(json.dumps(result,indent=2,sort_keys=True))

if __name__=="__main__":
    main()
