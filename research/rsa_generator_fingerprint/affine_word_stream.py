#!/usr/bin/env python3
"""Exact necessary-invariant test for raw affine-LCG words inside solved RSA primes.

Scope: direct concatenation of consecutive, complete, *unmodified* generator
states modulo 2**w for w=8,16,24,32. Exhausts all bit phase alignments.
Does NOT test truncated, interleaved, skipped, hashed, masked, or whitened
outputs; it does not infer the historical RSA DSP generator or RSA-270 factors.

For xi+1 = a*xi+c (mod m), di=xi+1-xi implies d1*d1=d0*d2 (mod m).
The congruence is necessary, not sufficient for a genuine LCG.
"""
from pathlib import Path
import hashlib
import json

WIDTHS = (8, 16, 24, 32)

def invariant(words, w):
    a, b, c, d = words
    return ((c-b)**2-(b-a)*(d-c)) % (1 << w) == 0

def windows(n, w):
    mask = (1 << w) - 1
    for phase in range(w):
        number = (n.bit_length()-phase)//w
        if number < 6:
            continue
        chunks = [(n >> (phase+i*w)) & mask for i in range(number)]
        # Exclude boundary words and incomplete words to avoid forced
        # top bits / low congruence and candidate-acceptance adjustments.
        for i in range(1, number-4):
            yield phase, i, chunks[i:i+4]

def evaluate(rows, w):
    total=hits=found=0
    examples=[]
    for row in rows:
        matching=0
        for phase, i, values in windows(row['factor'], w):
            total += 1
            if invariant(values, w):
                hits += 1
                matching += 1
                if len(examples) < 4:
                    examples.append(dict(name=row['name'],factor=row['which'],
                                         phase=phase,word_index=i))
        found += matching>0
    return dict(width=w,checked_windows=total,hits=hits,
                factors_with_hits=found,examples=examples)

def positive(w):
    mask = (1 << w)-1
    a = ((0x5DEECE65 & mask) & ~3) | 1
    state = 0x12345678 & mask
    chunks=[]
    for _ in range(18):
        state = (a*state+11)&mask
        chunks.append(state)
    combined = sum(x << (i*w) for i,x in enumerate(chunks))
    combined ^= 1
    combined |= 3 << (18*w-2)
    assert invariant(chunks[3:7],w)
    r = evaluate([{'name':'SYNTH','which':'positive','factor':combined}],w)
    assert r['hits'] >= 8
    return dict(width=w,hits=r['hits'])

def control(factors,w,index):
    rows=[]
    for r in factors:
        bitlen=r['factor'].bit_length()
        words=(bitlen+7)//8
        key=f"rsa-affine-control-v1/{w}/{index}/{r['name']}/{r['which']}"
        raw=int.from_bytes(hashlib.shake_256(key.encode()).digest(words),'little')
        n=(raw&((1<<(bitlen-2))-1)) | (3<<(bitlen-2))
        n += (5-n%6)%6
        if n.bit_length()!=bitlen: n-=6
        assert n.bit_length()==bitlen and n%6==5
        rows.append(dict(r,factor=n))
    return rows

def main():
    data=json.loads(Path(__file__).with_name('data.json').read_text())
    original=[]; later=[]
    for entry in data['solved']:
        p,q,n=map(int,(entry['p'],entry['q'],entry['n']))
        assert p*q==n and p%6==q%6==5
        dest=original if entry['cohort']=='original' else later
        for which,factor in (('p',p),('q',q)):
            dest.append(dict(name=entry['name'],which=which,factor=factor))
    assert len(original)==32 and len(later)==4
    assert not invariant([0,1,3,8],8)
    out={'status':'WARRANTED_LOCAL_EXACT_BOUNDED_NEGATIVE_ONLY',
         'scope':'direct full-word unwhitened adjacent affine LCG states',
         'original_factors':len(original),'separate_1997_factors':len(later),
         'evaluations':[],'positive_controls':[],'synthetic_random_controls':[]}
    for w in WIDTHS:
        out['evaluations'].append(dict(original=evaluate(original,w),
                                       later_1997=evaluate(later,w)))
        out['positive_controls'].append(positive(w))
        nulls=[evaluate(control(original,w,i),w)['hits'] for i in range(32)]
        out['synthetic_random_controls'].append(
            dict(width=w,replicates=len(nulls),mean_hits=sum(nulls)/len(nulls),
                 min_hits=min(nulls),max_hits=max(nulls),counts=nulls))
    Path(__file__).with_name('affine_word_stream_result.json').write_text(
        json.dumps(out,indent=2)+'\n')
    print(json.dumps(out,indent=2))

if __name__=='__main__':
    main()
