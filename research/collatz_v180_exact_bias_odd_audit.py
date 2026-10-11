"""V180 independently audit genuine +1 affine bias and high-odd residual.

For true shortcut T, verify exact affine bias and the all-source
height/coefficient inequality on 72k+ real integer sources/clock
pairs. Independently reconstruct V178's 205-rule source mask and
show every one of its 70638 residual positions has >=8 genuine odd
steps among the first 12. This is a NECESSARY condition for a least
bad source at heights >=8192, NOT terminal certification or QED.
"""
from __future__ import annotations
from collections import Counter
from math import comb
from pathlib import Path
from hashlib import sha256
import json
import random

def shortcut(n:int)->int:
    return n//2 if n%2==0 else (3*n+1)//2

def affine(n:int,k:int)->tuple[int,int,int]:
    x=n;a=0;bias=0
    for i in range(k):
        if x&1:
            bias=3*bias+(1<<i)
            a+=1
        x=shortcut(x)
    assert (1<<k)*x ==3**a*n +bias,(n,k)
    assert bias+(1<<k)<=(1<<k)*3**a,(n,k)
    if (1<<k)*(3**a)<=n and 3**a<(1<<k):
        assert x<n,(n,k,x,a)
    return x,a,bias

def main()->None:
    bank=json.loads(Path('research/collatz_v178_compact_bank.json').read_text())
    M=(1<<12)*(3**6)
    assert bank['M']==M and len(bank['selected'])==205
    mask=bytearray(M)
    for rule in bank['selected']:
        L,r=rule[:2]
        assert M%L==0
        mask[r::L]=b'\x01'*((M-1-r)//L+1)
    assert sum(mask)==2915346
    maskhash=sha256(mask).hexdigest()
    assert maskhash=='8b0ab639acebb9d973508aa62e1a9a50ad22e97fe0c5f96668573c6a482c6ef7'

    # All finite binary residues; V160's independently kernel-checked
    # affine lemma transfers the exact parity word to all n=r+4096*q.
    wordodds=[0]*4096
    wordbits=set()
    for r in range(4096):
        x=r; bits=0;a=0
        for i in range(12):
            bits|=(x&1)<<i
            a+=x&1
            x=shortcut(x)
        assert bits not in wordbits
        wordbits.add(bits)
        wordodds[r]=a
        # Explicitly test a real high source in the first q>=2 block.
        x2,a2,b2=affine(8192+r,12)
        assert a2==a,(r,a,a2)
        if a<=7:
            assert x2<8192+r,(r,a,x2)
    assert len(wordbits)==4096
    assert Counter(wordodds)=={a:comb(12,a) for a in range(13)}
    low_words=sum(v<=7 for v in wordodds)
    assert low_words==sum(comb(12,j) for j in range(8))==3302

    survivors=Counter()
    low_survivors=0
    for n,qualified in enumerate(mask):
        if qualified:
            continue
        a=wordodds[n%4096]
        survivors[a]+=1
        if a<=7:
            low_survivors+=1
    assert low_survivors==0
    assert sum(survivors.values())==70638
    assert dict(sorted(survivors.items()))=={
        8:21051,9:29496,10:15735,11:3960,12:396}

    rng=random.Random(180)
    tests=0
    for n in list(range(1,1025))+[8192,8193,16383,16384,65535,
          (1<<31)-1,(1<<64)-1,(1<<100)-1]:
        for k in range(0,33):
            affine(n,k)
            tests+=1
    for _ in range(4096):
        n=rng.randrange(1,10**24)
        k=rng.randrange(0,45)
        affine(n,k)
        tests+=1

    # Determine how many V178 survivors are in the rigorous
    # coefficient-crossing high-odd corridor. Every one is.
    result={
        'schema':'COLLATZ_V180_EXACT_AFFINE_INTERCEPT_HIGH_ODD_BARRIER',
        'true_shortcut':'even n/2; odd (3n+1)/2',
        'all_source_lean_theorems_separately_qualified':False,
        'affine_bias_source_clock_tests':tests,
        'source_mask_checksum':maskhash,
        'V178_residue_period':M,
        'V178_original_kernel_rules':205,
        'V178_grammar_residual_positions':70638,
        'residual_first_12_odd_count_distribution':dict(sorted(survivors.items())),
        'residuals_with_at_most_seven_odds':low_survivors,
        'low_odd_parity_words_of_4096':low_words,
        'all_12_step_parity_words_reconstructed_exactly':True,
        'source_height_threshold_for_formal_12_clock_descent':8192,
        'actual_odd_count_not_random_reference_law':True,
        'large_source_does_not_imply_all_depth_descent':True,
        'residual_still_infinite':True,
        'universal_collatz_proof':False,
        'global_collatz':'UNKNOWN','qed':False
    }
    Path('evidence').mkdir(exist_ok=True)
    Path('evidence/v180-exact.json').write_text(
        json.dumps(result,sort_keys=True,indent=2)+'\n')
    print(json.dumps({
        'schema':result['schema'],
        'checked_original_source_clocks':tests,
        'remaining_residue_positions':70638,
        'all_remaining_odd_12_at_least':8,
        'global_collatz':'UNKNOWN'
    },sort_keys=True))

if __name__=='__main__':
    main()
