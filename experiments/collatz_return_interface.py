#!/usr/bin/env python3
"""Exact episode-return interface and cross-pattern defect transport.

Theorems are documented separately. This module checks finite certificates;
neither class coverage nor countdown exit is a global descent certificate.
"""
import argparse
import json
from collections import Counter
from fractions import Fraction
from functools import lru_cache
from pathlib import Path
from collatz_odd_episode_grammar import episode
from collatz_witness_compiler import read_rows


def valuation(n):
    if n==0: return None  # Infinite valuation is an explicit fixed-point case.
    n=abs(n)
    return (n & -n).bit_length()-1


def primitive(word):
    for n in range(1,len(word)+1):
        if len(word)%n==0 and word[:n]*(len(word)//n)==word:
            return word[:n]
    raise AssertionError('nonempty word required')


def certificate(word):
    word=tuple(tuple(z) for z in word)
    if not word or any(len(z)!=3 or any(type(v) is not int or v<1 for v in z) for z in word):
        raise ValueError('positive nonempty episode word required')
    if any(a[2]!=b[0] for a,b in zip(word,word[1:])) or word[-1][2]!=word[0][0]:
        raise ValueError('connected same-r return required')
    A,B,D=1,0,0
    for r,s,rp in word:
        A,B,D=3**r*A,3**r*B+((1<<s)-1)*(1<<D),D+s+rp
    C=(1<<D)-A
    q=Fraction(B,C)
    p,den=q.numerator,q.denominator
    mod=1<<(D+1)
    rho=((1<<D)-B)*pow(A,-1,mod)%mod
    assert rho==p*pow(den,-1,mod)%mod
    return {'word':word,'r':word[0][0],'A':A,'B':B,'D':D,
            'q':(p,den),'rho':rho,'modulus':mod,'primitive':primitive(word)}


def admissible(c,m):
    p,s=c['q']
    return m>0 and m%2==1 and (s*m-p)%c['modulus']==0


def repeat_budget(c,m):
    """Minimal state for repetitions of this primitive word only.

    None means the exact fixed point, with unlimited repeats, not UNKNOWN.
    The budget intentionally makes no prediction about post-exit behavior.
    """
    if m<=0 or m%2==0: raise ValueError('positive odd cofactor required')
    p,s=c['q'];v=valuation(s*m-p)
    charge=sum(z[1]+z[2] for z in c['primitive'])
    return None if v is None else (v-1)//charge


def power_value(c,m,k):
    if k<0: raise ValueError('negative repeat count')
    p,s=c['q'];M=1<<c['D'];Mk=M**k
    numerator=p*Mk+c['A']**k*(s*m-p)
    denominator=s*Mk
    if numerator%denominator: raise ValueError('nonintegral return power')
    return numerator//denominator


@lru_cache(maxsize=None)
def prefix_lines(word):
    """Exact affine value of every shortcut prefix as a function of cofactor."""
    A,B,t=1<<word[0][0],-1,0
    result=[(A,B,t)]
    for r,s,_ in word:
        for _ in range(r):
            A,B=3*A,3*B+(1<<t);t+=1
            result.append((A,B,t))
        for _ in range(s):
            t+=1;result.append((A,B,t))
    return tuple(result)


def jump_repetitions(c,m):
    """Jump all legal primitive repetitions, preserving the exact block minimum.

    The exact exit cofactor is retained. A budget alone is not a global state.
    Prefix lines are monotone in m; the return iterates are monotone, so the
    minimum over all repetitions occurs in the first or last repetition.
    """
    if c['word']!=c['primitive']: c=certificate(c['primitive'])
    k=repeat_budget(c,m)
    if k is None: raise ValueError('fixed point requires separate handling')
    if k==0: return {'out':m,'repeats':0,'minimum_n':(1<<c['r'])*m-1,'prefix_evaluations':0}
    out=power_value(c,m,k)
    extreme=m if out>=m else power_value(c,m,k-1)
    values=[]
    for A,B,t in prefix_lines(c['word']):
        numerator=A*extreme+B
        assert numerator%(1<<t)==0
        values.append(numerator//(1<<t))
    return {'out':out,'repeats':k,'minimum_n':min(values),
            'prefix_evaluations':len(values)}


def replay(word,m):
    """Independent ordinary-integer episode replay, with exact schema checks."""
    if m<=0 or not m&1: raise ValueError('positive odd cofactor required')
    x=(1<<word[0][0])*m-1
    for expected in word:
        r,actual_m,s,rp,mp,y=episode(x)
        if (r,s,rp)!=tuple(expected): raise ValueError('word not admissible')
        x=y
    return mp


def injection(w,v):
    return (v['A']-(1<<v['D']))*w['B']+((1<<w['D'])-w['A'])*v['B']


def cylinder_separation(w,v):
    """Exact 2-adic separation of two same-anchor return cylinders.

    Each return certificate has exact domain m == q (mod 2^(D+1)), because
    the reduced fixed-point denominator is odd.  Since C=2^D-A is odd,

        J = C_w B_v - C_v B_w = C_w C_v (q_v-q_w),

    so v2(J) is exactly the 2-adic distance between the two fixed points.
    Distinct cylinders are disjoint iff their residues differ before the end
    of the shorter exact domain, equivalently v2(J)<min(D_w+1,D_v+1).
    """
    if w['r']!=v['r']: raise ValueError('same return anchor required')
    J=injection(w,v)
    same=(J==0)
    assert same==(w['q']==v['q'])
    bits=min(w['D']+1,v['D']+1)
    mask=(1<<bits)-1
    disjoint=((w['rho']-v['rho'])&mask)!=0
    h=valuation(J)
    if same:
        assert not disjoint and h is None
    elif disjoint:
        assert h is not None and h<bits
    else:
        assert h is not None and h>=bits
    return {'same_fixed_point':same,'disjoint':disjoint,
            'separation_valuation':h,'injection_valuation':h,
            'shorter_domain_bits':bits,
            'old_domain_bits':w['D']+1,'new_domain_bits':v['D']+1,
            'J':J}


def switch_resonance(w,v,m_start,m_end=None):
    """Classify one exact same-anchor pattern switch by its 2-adic resonance.

    For the old-pattern defect Delta=C*m-B and the new return V=(a,b,d),

        2^d Delta' = a Delta + J.

    If v2(Delta) != v2(J), oddness of a forces

        v2(Delta') = min(v2(Delta),v2(J)) - d,

    so recharge is impossible.  Positive valuation gain can therefore occur
    only at exact resonance v2(Delta)=v2(J), where additional cancellation in
    a*(Delta/2^j)+J/2^j controls the gain.
    """
    if w['r']!=v['r']: raise ValueError('same return anchor required')
    if not admissible(v,m_start): raise ValueError('new return not admissible at start')
    numerator=v['A']*m_start+v['B']
    denominator=1<<v['D']
    if numerator%denominator: raise ValueError('nonintegral new return')
    exact_end=numerator//denominator
    if m_end is None: m_end=exact_end
    if m_end!=exact_end: raise ValueError('supplied exit does not match exact return')

    J=injection(w,v)
    C=(1<<w['D'])-w['A']
    before=C*m_start-w['B'];after=C*m_end-w['B']
    combined=v['A']*before+J
    assert (1<<v['D'])*after==combined

    vb=valuation(before);vj=valuation(J);va=valuation(after)
    same=(J==0)
    assert same==(w['q']==v['q'])
    resonant=(not same and vb is not None and vj is not None and vb==vj)
    recharge=(vb is not None and va is not None and va>vb)
    if not same and vb is not None and vj is not None and vb!=vj:
        assert va==min(vb,vj)-v['D']
    if recharge:
        assert resonant

    if resonant:
        vc=valuation(combined)
        cancellation_depth=None if vc is None else vc-vb
    else:
        cancellation_depth=0

    return {'J':J,'defect_before':before,'defect_after':after,
            'valuation_before':vb,'injection_valuation':vj,'valuation_after':va,
            'same_fixed_point':same,'resonant':resonant,'recharge':recharge,
            'cancellation_depth':cancellation_depth,'exit':m_end}


def reset_witness(L):
    """V=(2,1,1)(1,1,2) raises v2(m+1) from 2 to any L>=3."""
    if L<3: raise ValueError('L>=3 required')
    z=(39*pow(pow(2,L+5,27),-1,27))%27
    if z%2==0: z+=27
    m=((1<<(L+5))*z-39)//27
    out=(1<<L)*z-1
    assert 27*m+7==32*out and m>0 and z>0 and z%2==1
    return m,out


def reset_block(k,L):
    """Construct an exact W^k V block, k>=2,L>=3k+3.

    It increases ordinary size and the W-defect valuation, with no prior
    descent during the block. This is not a claim about subsequent behavior.
    """
    if k<2 or L<3*k+3: raise ValueError('require k>=2 and L>=3k+3')
    mod=3**(2*k+3)
    z=12*pow(pow(2,L+5,mod),-1,mod)%mod
    if z%2==0: z+=mod
    mid=((1<<(L+5))*z-39)//27
    assert (mid+1)%(9**k)==0
    m0=8**k*((mid+1)//9**k)-1
    out=(1<<L)*z-1
    word=((2,1,2),)*k+((2,1,1),(1,1,2))
    c=certificate(word)
    assert admissible(c,m0) and replay(word,m0)==out
    assert m0>0 and out>m0
    assert valuation(m0+1)==3*k+2 and valuation(out+1)==L
    x0=4*m0-1;x=x0;path=[x]
    for _ in range(3*k+5):
        x=(3*x+1)//2 if x&1 else x//2
        assert x>=x0
        path.append(x)
    assert x==4*out-1
    return {'k':k,'L':L,'z':z,'m0':m0,'mid':mid,'out':out,
            'n0':x0,'n_out':x,'shortcut_steps':3*k+5,
            'initial_defect_valuation':3*k+2,'final_defect_valuation':L,
            'initial_odd_part':(m0+1)>>(3*k+2),'final_odd_part':z,
            'no_intermediate_descent':True,'path':path,
            'A':c['A'],'B':c['B'],'D':c['D']}


def trace(n,cap=4096):
    if n<=1 or not n&1: raise ValueError('odd nonbase source required')
    x=n; branches=[]; states=[]; A,B,D=1,0,0
    r0=valuation(n+1);m0=(n+1)>>r0
    for _ in range(cap):
        r,m,s,rp,mp,y=episode(x)
        states.append((r,m,x,(1<<(D+1))>m0));branches.append((r,s,rp))
        A,B,D=3**r*A,3**r*B+((1<<s)-1)*(1<<D),D+s+rp
        assert A*m0+B==(1<<D)*mp
        if y<n:
            states.append((rp,mp,y,(1<<(D+1))>m0))
            return states,branches
        x=y
    raise ValueError('episode budget exhausted: UNKNOWN')


def collect(rows,known_words,known_classes,cache):
    words=set();classes={};counts=Counter();max_reset=None
    first_reset=None; first_stable_reset=None
    new_word_known_class=set();new_primitive_known_class=set()
    for row in rows:
        n=row['b'];states,branches=trace(n)
        last={states[0][0]:0};last_return={}
        for end in range(1,len(states)):
            r,mend,_,_=states[end]
            if r in last:
                start=last[r];mstart=states[start][1]
                word=tuple(branches[start:end])
                if word not in cache:
                    c=certificate(word)
                    assert replay(word,c['rho'])==(c['A']*c['rho']+c['B'])//(1<<c['D'])
                    cache[word]=c
                c=cache[word]
                assert admissible(c,mstart)
                assert c['A']*mstart+c['B']==(1<<c['D'])*mend
                key=(r,)+c['q'];root=c['primitive']
                if key in classes: assert classes[key]==root
                classes[key]=root;words.add(word);counts['returns']+=1
                p,den=c['q'];delta=den*mstart-p;delta_end=den*mend-p
                assert delta!=0
                assert valuation(delta_end)==valuation(delta)-c['D']
                if word not in known_words and key in known_classes:
                    new_word_known_class.add(word)
                    if root!=known_classes[key]: new_primitive_known_class.add(word)
                if r in last_return:
                    old=last_return[r]
                    J=injection(old,c)
                    C=(1<<old['D'])-old['A']
                    before=C*mstart-old['B'];after=C*mend-old['B']
                    assert (1<<c['D'])*after==c['A']*before+J
                    same=old['q']==c['q']
                    assert (J==0)==same
                    counts['same_fixed_point' if same else 'different_fixed_point']+=1
                    if before==0 or after==0:
                        counts['zero_cross_defect']+=1
                    else:
                        gain=valuation(after)-valuation(before)
                        counts['reset' if gain>0 else 'equal' if gain==0 else 'decrease']+=1
                        if same: assert gain==-c['D']
                        if gain>0:
                            item={'seed':n,'r':r,'m_start':mstart,'m_end':mend,
                                  'old_word':old['word'],'new_word':word,
                                  'old_q':old['q'],'new_q':c['q'],'J':J,
                                  'valuation_before':valuation(before),'valuation_after':valuation(after),
                                  'pullback_already_stable':states[start][3]}
                            if first_reset is None or n<first_reset['seed']: first_reset=item
                            if states[start][3]:
                                counts['stable_reset']+=1
                                if first_stable_reset is None or n<first_stable_reset['seed']:
                                    first_stable_reset=item
                            if max_reset is None or gain>max_reset['gain']:
                                max_reset={'gain':gain,**item}
                last_return[r]=c
            last[r]=end
    result={'K':rows[0]['K'],'families':len(rows),'unique_words':len(words),
            'fixed_point_classes':len(classes),'primitive_words':len({c for c in classes.values()}),
            'known_classes_before':len(known_classes),'new_words_in_known_class':len(new_word_known_class),
            'new_primitive_patterns_in_known_class':len(new_primitive_known_class),
            'counts':dict(counts),'first_reset':first_reset,
            'first_stable_reset':first_stable_reset,'largest_reset':max_reset}
    assert result['new_primitive_patterns_in_known_class']==0
    return result,words,classes


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('inputs',nargs='+');ap.add_argument('--out',required=True)
    a=ap.parse_args()
    known_words=set();known_classes={};cache={};results=[]
    for path in a.inputs:
        rows=read_rows(path)
        result,words,classes=collect(rows,known_words,known_classes,cache)
        known_words.update(words);known_classes.update(classes)
        results.append(result)
        print(json.dumps({k:v for k,v in result.items() if k not in ('first_reset','first_stable_reset','largest_reset')},sort_keys=True),flush=True)
        Path(a.out).write_text(json.dumps({'status':'EXPERIMENTALLY EXACT ON FINITE DOMAIN',
            'results':results,'scope':'return progress only; no seed closure or global rank inferred'},indent=2)+'\n')


if __name__=='__main__': main()
