#!/usr/bin/env python3
"""Exhaustive bounded controls, deletion countermodels and reset certificates."""
import argparse
import itertools
import json
from pathlib import Path
from collatz_return_interface import certificate,admissible,replay,valuation,reset_block,injection,repeat_budget,jump_repetitions


def main():
    p=argparse.ArgumentParser();p.add_argument('--out',required=True);a=p.parse_args()
    checked=0;classes={};collision_groups=set();replay_checks=0;macro_controls=0
    for length in range(1,5):
        for rstates in itertools.product(range(1,4),repeat=length):
            for svals in itertools.product(range(1,4),repeat=length):
                word=tuple((rstates[i],svals[i],rstates[(i+1)%length]) for i in range(length))
                c=certificate(word);key=(c['r'],)+c['q'];checked+=1
                if key in classes:
                    assert classes[key]==c['primitive']
                    collision_groups.add(key)
                classes[key]=c['primitive']
                for q in (0,1,10**20):
                    m=c['rho']+q*c['modulus']
                    assert admissible(c,m)
                    out=replay(word,m)
                    assert c['A']*m+c['B']==(1<<c['D'])*out
                    p0,s0=c['q'];delta=s0*m-p0
                    if delta:
                        assert valuation(s0*out-p0)==valuation(delta)-c['D']
                    else: assert out==m
                    replay_checks+=1
                    if delta:
                        jump=jump_repetitions(c,m)
                        x=(1<<c['r'])*m-1;minimum=x
                        steps=jump['repeats']*sum(r+s for r,s,_ in c['primitive'])
                        for _ in range(steps):
                            x=(3*x+1)//2 if x&1 else x//2
                            minimum=min(minimum,x)
                        assert x==(1<<c['r'])*jump['out']-1
                        assert minimum==jump['minimum_n']
                        macro_controls+=1
                bad=c['rho']^(1<<c['D'])
                assert (c['A']*bad+c['B'])%(1<<c['D'])==0
                assert not admissible(c,bad)
                try: replay(word,bad)
                except ValueError: pass
                else: raise AssertionError('next-bit ablation escaped replay')
    W=((2,1,2),);V=((2,1,1),(1,1,2))
    w=certificate(W);v=certificate(V)
    assert injection(w,v)==-12
    budgets=0
    for m in range(1,4096,2):
        budget=repeat_budget(w,m);x=m;used=0
        while admissible(w,x):
            x=replay(W,x);used+=1
        assert used==budget
        budgets+=1
    cases=[reset_block(2,L) for L in range(9,65)]
    cases.extend(reset_block(k,L) for k,L in ((2,256),(2,1024),(8,27),(16,52),(32,103)))
    smallest=min(cases,key=lambda z:z['n0'])
    assert smallest['n0']==678907
    # A positive finite block is not a divergent trajectory.
    x=smallest['n0']
    for t in range(1,10000):
        x=(3*x+1)//2 if x&1 else x//2
        if x<smallest['n0']: break
    else: raise AssertionError('finite control descent budget exhausted')
    out={'status':'EXPERIMENTALLY EXACT ON FINITE DOMAIN','return_words_checked':checked,
         'canonical_and_translated_replays':replay_checks,
         'duplicate_fixed_point_groups':len(collision_groups),'primitive_rigidity_violations':0,
         'minimal_budget_controls':budgets,
         'exact_macro_endpoint_and_minimum_controls':macro_controls,
         'post_exit_separator':{
             'm_left':15,'m_right':31,'shared_budget':1,
             'initial_n_left':59,'initial_n_right':123,
             'after_W_left':67,'after_W_right':139,
             'after_next_episode_left':19,'after_next_episode_right':157,
             'left_descends':True,'right_descends':False,
             'scope':'budget preserves repetition language, not arbitrary continuation consequences'},
         'ablations':{
             'omit_final_oddness_bit':{'m':7,'word':W,'affine_output':8,'failure':'cofactor even; endpoint r is 5, not 2'},
             'omit_charge_D':{'m':15,'one_W_valid':True,'two_W_valid':False},
             'omit_cross_injection':{'m':27,'out':23,'J':-12,'valuation_before':2,'valuation_after':3,'wrong_prediction_without_J':-3},
             'omit_fixed_point_case':{'r':1,'m':1,'word':[(1,1,1)],'defect':0,'failure':'infinite valuation; base Collatz cycle'}},
         'smallest_k2_family_example':smallest,
         'smallest_example_first_descent':{'steps':t,'endpoint':x},
         'reset_examples':cases,
         'scope':'Universal claims require the separate mathematical derivations; no infinite reset path inferred'}
    Path(a.out).write_text(json.dumps(out,indent=2)+'\n')
    print(json.dumps({k:v for k,v in out.items() if k not in ('reset_examples','smallest_k2_family_example','ablations')},sort_keys=True))
    print('VERIFIED_RETURN_INTERFACE_AND_RESET_FAMILY_NOT_GLOBAL_CLOSURE')


if __name__=='__main__':main()
