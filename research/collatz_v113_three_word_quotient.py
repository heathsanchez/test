"""V113 canonical three-word quotient for V112's bounded CRT mergers.

Three exact ten-step inverse identities:
  T^10(191 +1024*s)= 410 +2187*s
  T^10(927 +1024*s)=1982 +2187*s
  T^10(1007+1024*s)=2153 +2187*s

One source-relative guard composes each with an exact forward prefix.
No claim about arbitrary CRT survivors or global Collatz.
"""
import json
from collections import Counter
from research.collatz_v108_reclosure import MODULUS as DYADIC, shortcut, candidates
from research.collatz_v109_reverse_reclosure import reverse_witness
from research.collatz_v110_q7_crt_reclosure import TERNARY, PRODUCT, ternary_reverse, crt_base

BANK = (
    (410, 191, "EEOEOOOOOO"),
    (1982, 927, "EEOOEOOOOO"),
    (2153, 1007, "EEOOOEOOOO"),
)

def check_word(r,p,word):
    x,a=r,TERNARY
    for op in word:
        if op=="E":
            x,a=2*x,2*a
        else:
            assert op=="O" and x>=2 and x%3==2 and a%3==0
            old_x,old_a=x,a
            x,a=(2*x-1)//3,2*a//3
            assert 3*x+1==2*old_x and 3*a==2*old_a
    assert (x,a)==(p,1024) and len(word)==10
    for s in (0,1,2,7,19):
        target=p+1024*s
        for _ in word: target=shortcut(target)
        assert target==r+TERNARY*s

def classify(n0):
    x=n0
    odd=0
    result=[]
    for j in range(1,13):
        odd+=x%2
        x=shortcut(x)
        A=(DYADIC >> j)*3**odd*TERNARY
        assert A%TERNARY==0
        for r,p0,word in BANK:
            if x%TERNARY!=r: continue
            s=(x-r)//TERNARY
            p=p0+1024*s
            c=1024*(A//TERNARY)
            if not 0<p<n0 or c>PRODUCT: continue
            for q in (0,1,7):
                n=n0+PRODUCT*q
                y=n
                for _ in range(j): y=shortcut(y)
                assert y==x+A*q
                earlier=p+c*q
                assert 0<earlier<n
                target=earlier
                for _ in word:target=shortcut(target)
                assert target==y
            result.append(dict(forward_prefix=j,endpoint=x,
                endpoint_slope=A,earlier_source=p,
                earlier_source_slope=c,word=word,endpoint_ternary=r))
    return result

def main():
    for entry in BANK: check_word(*entry)
    old_unknown=[r for r in range(DYADIC)
                 if not candidates(r) and reverse_witness(r) is None]
    q7_unknown=[a for a in range(TERNARY) if ternary_reverse(a) is None]
    assert (len(old_unknown),len(q7_unknown))==(144,1174)
    records=[]
    choices=Counter()
    for r in old_unknown:
        for a in q7_unknown:
            n=crt_base(r,a)
            witnesses=classify(n)
            if witnesses:
                choices[len(witnesses)]+=1
                records.append(dict(dyadic_residue=r,ternary_residue=a,
                                    original_source=n,**witnesses[0]))
    counts=Counter(z["word"] for z in records)
    assert len(records)==1701
    assert choices=={1:1701}
    assert counts=={
        "EEOEOOOOOO":432,
        "EEOOEOOOOO":432,
        "EEOOOEOOOO":837
    }
    assert len({z["dyadic_residue"] for z in records})==144
    print(json.dumps(dict(
        schema="COLLATZ_V113_THREE_WORD_SOURCE_QUOTIENT",
        status="BOUNDED_EXACT_EXECUTABLE",
        global_collatz="UNKNOWN",qed=False,
        source_modulus=PRODUCT,
        protected_output="uniform source-relative lower future merge",
        compressed_word_bank=[
            dict(endpoint_residue=r,predecessor_residue=p,
                 endpoint_slope=TERNARY,predecessor_slope=1024,
                 reverse_word=word) for r,p,word in BANK],
        all_three_words_exactly_replayed=True,
        original_unresolved=169056,newly_classified=1701,
        remaining_unknown=167355,total_covered=8790597,
        reverse_word_counts=dict(counts),
        unique_qualifying_presentation_per_family=True,
        individual_lean_witness_reification=False,
        records=records),sort_keys=True,indent=2))

if __name__=="__main__":
    main()
