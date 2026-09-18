#!/usr/bin/env python3
"""Tournament of two-replay lifts for observed low-charge concrete RIGID cycles.

For each selected source, reconstruct concrete same-anchor return-pattern cycles
from the exact RIGID boundary audit. For each unique cycle with charge D <=
--max-D, impose enough 2-adic defect precision to replay the whole cycle twice:

    v2(((2^D-A)m-B)) >= 2D+1.

This gives one residue m mod 2^(2D+1), hence episode endpoint x=2^r m-1.
Enumerate the exact shortcut-Collatz reverse tree of x.

A reverse predecessor n at depth k is q=0-compatible iff 1<n<2^k.
If n>x, T^k(n)=x<n gives direct descent.
If n<=x, test the stronger condition actually relevant to a hypothetical
minimal counterexample: n must survive every earlier fixed-source prefix and
arrive at q=0 as RIGID.

Bounded discovery only. This is not a proof of Collatz.
"""
from __future__ import annotations
import argparse
from collections import defaultdict

import collatz_q0_rigid_recharge_audit as ra
import collatz_q0_coalescence_component_audit as base


def compose_targets(edges, cert_by_edge):
    A,B,D=1,0,0
    for e in edges:
        c=cert_by_edge[e][1]
        B=c['A']*B + c['B']*(1<<D)
        A=c['A']*A
        D+=c['D']
    return A,B,D


def cycles_for_source(n:int,H:int):
    starts,branches=ra.rigid_episode_segment(n,H)
    if not branches:
        return []
    cache={}
    last={}
    last_return={}
    seqs=defaultdict(list)
    cert_by_edge={}

    for end in range(1,len(starts)):
        r=starts[end][1]
        if r in last:
            start=last[r]
            word=tuple(branches[start:end])
            c=cache.setdefault(word,ra.certificate(word))
            m0=starts[start][2]
            m1=starts[end][2]
            assert ra.admissible(c,m0)
            assert ra.replay(c,m0)==m1
            if r in last_return:
                old=last_return[r]
                if old['q']!=c['q']:
                    z=ra.switch_law(old,c,m0,m1)
                    if z is not None:
                        e=((old['r'],)+old['q'],(c['r'],)+c['q'])
                        cert_by_edge[e]=(old,c)
                        seqs[r].append((e,m0,m1,z['outcome'],starts[start][0]))
            last_return[r]=c
        last[r]=end

    out=[]
    for r,seq in seqs.items():
        if not seq: continue
        nodes=[seq[0][0][0]]
        for row in seq:
            assert nodes[-1]==row[0][0]
            nodes.append(row[0][1])
        first={}
        for i,node in enumerate(nodes):
            if node in first:
                a=first[node]; b=i
                edges=tuple(seq[j][0] for j in range(a,b))
                A,B,D=compose_targets(edges,cert_by_edge)
                out.append({
                    'source':n,'r':r,'edges':edges,'A':A,'B':B,'D':D,
                    'entry_m':seq[a][1],'exit_m':seq[b-1][2],
                    'entry_k':seq[a][4],
                    'outcomes':tuple(seq[j][3] for j in range(a,b)),
                })
            else:
                first[node]=i
    return out


def reverse_children(x:int):
    yield 2*x,'E'
    z=2*x-1
    if z%3==0:
        p=z//3
        if p>0 and p&1:
            yield p,'O'


def two_replay_seed(A:int,B:int,D:int):
    C=(1<<D)-A
    assert C&1
    bits=2*D+1
    mod=1<<bits
    rho=(B*pow(C,-1,mod))%mod
    if rho==0:
        rho=mod
    assert rho&1
    return rho,bits


def reverse_audit(x:int,max_depth:int):
    states={x:''}
    q0=direct=non_direct=hereditary=0
    first_non=None
    first_hered=None
    max_front=1

    for k in range(1,max_depth+1):
        nxt={}
        for y,w in states.items():
            for p,ch in reverse_children(y):
                nxt.setdefault(p,w+ch)
        states=nxt
        max_front=max(max_front,len(states))
        for n,w in states.items():
            if not (1<n<(1<<k)):
                continue
            q0+=1
            if n>x:
                direct+=1
                continue
            non_direct+=1
            if first_non is None:
                first_non=(k,n,w)
            ok,_=base.survives_to_q0(n)
            if ok and base.birth_status(n)[0]=='RIGID':
                hereditary+=1
                if first_hered is None:
                    first_hered=(k,n,w)
        if first_hered is not None:
            break
    return {
        'q0':q0,'direct':direct,'non_direct':non_direct,
        'hereditary':hereditary,'first_non':first_non,
        'first_hered':first_hered,'max_frontier':max_front,
    }


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--H',type=int,default=128)
    ap.add_argument('--max-D',type=int,default=12)
    ap.add_argument('--reverse-depth',type=int,default=45)
    a=ap.parse_args()

    sources=[16551,16777,16937,19055,20073,26763,26863,28583,28671]
    raw=[]
    for n in sources:
        raw.extend(cycles_for_source(n,a.H))

    uniq={}
    for c in raw:
        key=(c['r'],c['A'],c['B'],c['D'])
        uniq.setdefault(key,c)
    selected=[c for c in uniq.values() if c['D']<=a.max_D]
    selected.sort(key=lambda c:(c['D'],c['r'],c['A'],c['B']))

    print('OBSERVED_UNIQUE_CYCLES',len(uniq))
    print('LOW_CHARGE_CYCLES',len(selected))
    dangerous=[]
    for c in selected:
        m,bits=two_replay_seed(c['A'],c['B'],c['D'])
        x=(1<<c['r'])*m-1
        depth=max(a.reverse_depth,x.bit_length()+4)
        res=reverse_audit(x,depth)
        row=(c['source'],c['r'],c['A'],c['B'],c['D'],c['outcomes'],
             m,bits,x,depth,res)
        print('CYCLE_HIGH_FUEL_AUDIT',row)
        if res['hereditary']:
            dangerous.append(row)

    print('DANGEROUS_HEREDITARY_HIGH_FUEL_LIFTS',len(dangerous))
    if dangerous:
        print('SEPARATOR_HIGH_FUEL_CAN_SURVIVE_TO_RIGID_Q0',dangerous[0])
    else:
        print('OBSERVED_ALL_LOW_CHARGE_TWO_REPLAY_LIFTS_CLOSE_BEFORE_RIGID_Q0')
    print('STATUS BOUNDED_MULTI_CYCLE_DISCOVERY_ONLY')


if __name__=='__main__':
    main()
