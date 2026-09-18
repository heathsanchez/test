#!/usr/bin/env python3
"""RIGID-filtered return/recharge audit on the q=0 boundary.

For a fixed ordinary source n, once source refinement reaches q=0 the boundary
state is (k,n,c_k,T^k(n)).  This audit follows only the unresolved symbolic
segment on which every shortcut-depth classifier result is exactly RIGID.

That segment is collapsed into exact odd/even episodes.  Consecutive distinct
same-anchor first-return words are compared with the exact defect-transport
law.  Only strict recharge switches are retained in the final graph.

The output answers the current discovery question:
    can strict recharge itself recur inside the bounded q=0 RIGID language?

Acyclicity on this bounded sample is evidence only, not a global proof.
"""
from __future__ import annotations

import argparse
from collections import Counter, defaultdict
from fractions import Fraction

import collatz_q0_coalescence_component_audit as base


def v2(x:int)->int:
    assert x>0
    return (x & -x).bit_length()-1


def episode(x:int):
    assert x>0 and x&1
    r=v2(x+1)
    m=(x+1)>>r
    y=x
    for _ in range(r):
        assert y&1
        y=base.T(y)
    assert y>0 and y%2==0
    s=v2(y)
    for _ in range(s):
        y=base.T(y)
    assert y&1
    rp=v2(y+1)
    mp=(y+1)>>rp
    assert y==((3**r)*m-1)//(2**s)
    assert mp==((3**r)*m+(1<<s)-1)//(2**(s+rp))
    return (r,m,s,rp,mp,y)


def certificate(word):
    word=tuple(tuple(z) for z in word)
    assert word
    assert all(len(z)==3 and all(type(v) is int and v>=1 for v in z) for z in word)
    assert all(a[2]==b[0] for a,b in zip(word,word[1:]))
    assert word[-1][2]==word[0][0]
    A,B,D=1,0,0
    for r,s,rp in word:
        A,B,D=3**r*A,3**r*B+((1<<s)-1)*(1<<D),D+s+rp
    C=(1<<D)-A
    q=Fraction(B,C)
    p,u=q.numerator,q.denominator
    mod=1<<(D+1)
    rho=((1<<D)-B)*pow(A,-1,mod)%mod
    assert rho==p*pow(u,-1,mod)%mod
    return {'word':word,'r':word[0][0],'A':A,'B':B,'D':D,
            'C':C,'q':(p,u),'rho':rho,'modulus':mod}


def admissible(c,m):
    p,u=c['q']
    return m>0 and m&1 and (u*m-p)%c['modulus']==0


def replay(c,m):
    x=(1<<c['r'])*m-1
    for expected in c['word']:
        r,mm,s,rp,mp,y=episode(x)
        assert (r,s,rp)==expected
        x=y
    return (x+1)>>c['r']


def injection(w,v):
    return (v['A']-(1<<v['D']))*w['B']+((1<<w['D'])-w['A'])*v['B']


def separation(w,v):
    assert w['r']==v['r']
    J=injection(w,v)
    same=(J==0)
    assert same==(w['q']==v['q'])
    bits=min(w['D']+1,v['D']+1)
    mask=(1<<bits)-1
    disjoint=((w['rho']-v['rho'])&mask)!=0
    h=None if J==0 else v2(abs(J))
    if same:
        assert not disjoint and h is None
    elif disjoint:
        assert h<bits
    return same,disjoint,h,J


def switch_law(w,v,m_start,m_end):
    assert w['r']==v['r']
    assert admissible(v,m_start)
    assert replay(v,m_start)==m_end

    same,disjoint,h,J=separation(w,v)
    if same or not disjoint:
        return None

    C=w['C']
    before=C*m_start-w['B']
    after=C*m_end-w['B']
    assert (1<<v['D'])*after==v['A']*before+J

    vb=v2(abs(before)); va=v2(abs(after))
    assert vb==h  # distinct deterministic return cylinders force resonance

    p,u=v['q']
    vv=v2(abs(u*m_start-p))
    base=v['D']+1
    assert vv>=base
    excess=vv-base
    threshold=h-1

    if excess<threshold:
        outcome='drop'
        assert va==excess+1<h
    elif excess>threshold:
        outcome='flat'
        assert va==h
    else:
        outcome='recharge'
        assert va>h
    return {'outcome':outcome,'before':vb,'after':va,'h':h,
            'excess':excess,'threshold':threshold}


def q0_status(k,n):
    out,data=base.cylinder_status(k,n)
    if out=='TAIL_CLOSED':
        return 'CLOSED' if data[-1]==0 else 'TAIL_EXCEPTION'
    return out


def rigid_episode_segment(n,K):
    """Return exact episode starts/branches while the q=0 obligation stays RIGID."""
    k=n.bit_length()
    if k>K or q0_status(k,n)!='RIGID':
        return [],[]
    # Actual endpoint at q=0.
    c,x=base.forward_state(k,n)
    starts=[]
    branches=[]
    # Move through complete episodes, but only while every shortcut state is RIGID.
    while k<K:
        if not (x&1):
            # Even boundary states are single shortcut steps before the next
            # episode anchor. They must remain RIGID too.
            if q0_status(k,n)!='RIGID':
                break
            x=base.T(x); k+=1
            if k>K or q0_status(k,n)!='RIGID':
                break
            c2,x2=base.forward_state(k,n)
            assert x==x2
            continue

        r,m,s,rp,mp,y=episode(x)
        end=k+r+s
        if end>K:
            break
        ok=True
        z=x
        for j in range(k,end+1):
            if q0_status(j,n)!='RIGID':
                ok=False;break
            if j<end:
                z=base.T(z)
        if not ok:
            break
        assert z==y
        starts.append((k,r,m,x))
        branches.append((r,s,rp))
        k=end;x=y
    return starts,branches


def tarjan(nodes,edges):
    g={v:[] for v in nodes}
    for a,b in edges:
        g.setdefault(a,[]).append(b);g.setdefault(b,[])
    idx=0;stack=[];on=set();ind={};low={};comps=[]
    def visit(v):
        nonlocal idx
        ind[v]=low[v]=idx;idx+=1;stack.append(v);on.add(v)
        for w in g[v]:
            if w not in ind:
                visit(w);low[v]=min(low[v],low[w])
            elif w in on:
                low[v]=min(low[v],ind[w])
        if low[v]==ind[v]:
            c=[]
            while True:
                w=stack.pop();on.remove(w);c.append(w)
                if w==v:break
            comps.append(c)
    for v in list(g):
        if v not in ind:visit(v)
    return comps


def analyze(N,K,L=3):
    cache={}
    counts=Counter()
    recharge_edges=Counter()
    all_switch_edges=Counter()
    cert_by_edge={}
    switch_outcomes={}
    switch_witness={}
    first_recharge=None
    recharge_meta=[]
    switch_sequences=defaultdict(list)
    return_sequences=defaultdict(list)

    start=max(3,L)
    if start%2==0: start+=1
    for n in range(start,N+1,2):
        starts,branches=rigid_episode_segment(n,K)
        if not branches:
            continue
        counts['sources_with_rigid_episodes']+=1
        counts['rigid_episodes']+=len(branches)

        # Each starts[i] is the state before branches[i].  Add the terminal
        # episode-start state if the final anchor is available.
        # From branch i=(r,s,rp), its endpoint odd state is next start iff
        # there is another complete episode.
        last={}
        last_return={}
        for end in range(1,len(starts)):
            r,m,_,_ = starts[end][1],starts[end][2],starts[end][3],starts[end][3]
            if r in last:
                start=last[r]
                word=tuple(branches[start:end])
                if word not in cache:
                    cache[word]=certificate(word)
                c=cache[word]
                mstart=starts[start][2]
                mend=starts[end][2]
                assert admissible(c,mstart)
                assert replay(c,mstart)==mend
                counts['returns']+=1
                return_sequences[(n,r)].append((c,mstart,mend,starts[start][0]))

                if r in last_return:
                    old=last_return[r]
                    if old['q']==c['q']:
                        counts['same_pattern']+=1
                    else:
                        z=switch_law(old,c,mstart,mend)
                        if z is not None:
                            counts['switch_'+z['outcome']]+=1
                            edge=((old['r'],)+old['q'],(c['r'],)+c['q'])
                            all_switch_edges[edge]+=1
                            cert_by_edge[edge]=(old,c)
                            switch_outcomes[edge]=z['outcome']
                            switch_witness.setdefault(edge,(n,starts[start][0],old['word'],c['word'],mstart,mend,z))
                            switch_sequences[(n,r)].append((z['outcome'],mstart,mend,edge,starts[start][0]))
                            if z['outcome']=='recharge':
                                recharge_meta.append({
                                    'n':n,'k':starts[start][0],
                                    'oldD':old['D'],'newD':c['D'],
                                    'oldC':old['C'],'newC':c['C'],
                                    'oldA':old['A'],'newA':c['A'],
                                    'oldq':old['q'],'newq':c['q'],
                                    'h':z['h'],'before':z['before'],'after':z['after'],
                                    'mstart':mstart,'mend':mend,
                                })
                                recharge_edges[edge]+=1
                                if first_recharge is None:
                                    first_recharge=(n,starts[start][0],edge,z)
                last_return[r]=c
            last[r]=end

    edges=set(recharge_edges)
    nodes={x for e in edges for x in e}
    comps=tarjan(nodes,edges)
    cyc=[c for c in comps if len(c)>1 or (len(c)==1 and (c[0],c[0]) in edges)]

    print("RIGID_RETURN_COUNTS",dict(counts))
    print("RIGID_SWITCH_UNIQUE_EDGES",len(all_switch_edges))
    print("RIGID_RECHARGE_UNIQUE_EDGES",len(recharge_edges))
    print("RIGID_RECHARGE_OCCURRENCES",sum(recharge_edges.values()))
    print("RIGID_RECHARGE_CYCLIC_SCCS",len(cyc))
    print("RIGID_RECHARGE_CYCLIC_SIZES",sorted((len(c) for c in cyc),reverse=True))
    for edge,count in sorted(all_switch_edges.items(), key=lambda kv:(repr(kv[0]),kv[1])):
        print("RIGID_SWITCH_EDGE",switch_outcomes[edge],count,edge,switch_witness[edge])
    if recharge_meta:
        tests={
            'D_STRICT_UP': lambda z:z['newD']>z['oldD'],
            'D_STRICT_DOWN': lambda z:z['newD']<z['oldD'],
            'ABS_C_STRICT_UP': lambda z:abs(z['newC'])>abs(z['oldC']),
            'ABS_C_STRICT_DOWN': lambda z:abs(z['newC'])<abs(z['oldC']),
            'DEN_STRICT_UP': lambda z:z['newq'][1]>z['oldq'][1],
            'DEN_STRICT_DOWN': lambda z:z['newq'][1]<z['oldq'][1],
            'M_STRICT_DOWN': lambda z:z['mend']<z['mstart'],
            'M_STRICT_UP': lambda z:z['mend']>z['mstart'],
        }
        for name,test in tests.items():
            bad=[z for z in recharge_meta if not test(z)]
            print("RECHARGE_ORDER_TEST",name,"pass",len(recharge_meta)-len(bad),"fail",len(bad),
                  "first_fail",bad[0] if bad else None)
        hs=Counter(z['h'] for z in recharge_meta)
        print("RECHARGE_HISTOGRAM",dict(sorted(hs.items())))
    # Exact switch-to-switch transport: after a return V, its own defect
    # valuation loses exactly D_V.  Thus for consecutive distinct returns,
    # the next separation equals the previous new-domain excess + 1.
    transport_checks=0; recharge_forced_switch=0
    for key,seq in return_sequences.items():
        for i in range(len(seq)-1):
            old,m0,m1,k0=seq[i]
            new,n0,n1,k1=seq[i+1]
            assert m1==n0
            if old['q']==new['q']:
                continue
            z=switch_law(old,new,n0,n1)
            if i+2<len(seq):
                nxt,p0,p1,k2=seq[i+2]
                assert n1==p0
                if z['outcome']=="recharge":
                    assert new['q']!=nxt['q'], ("recharge repeated target",key,i)
                    recharge_forced_switch+=1
                if new['q']!=nxt['q']:
                    z2=switch_law(new,nxt,p0,p1)
                    assert z2['h']==z['excess']+1, ("h transport",key,i,z,z2)
                    transport_checks+=1
    print("SWITCH_H_TRANSPORT_CHECKS",transport_checks)
    print("RECHARGE_FORCED_NEXT_SWITCH_CHECKS",recharge_forced_switch)

    streaks=[]; expanding_streaks=[]
    for key,seq in switch_sequences.items():
        i=0
        while i<len(seq):
            if seq[i][0]!="recharge":
                i+=1; continue
            j=i
            while j+1<len(seq) and seq[j+1][0]=="recharge":
                j+=1
            row=(key, j-i+1, seq[i][1], seq[j][2],
                 tuple(x[3] for x in seq[i:j+1]))
            streaks.append(row)
            if seq[j][2] >= seq[i][1]:
                expanding_streaks.append(row)
            i=j+1
    discharge=[]; discharge_bad=[]
    for key,seq in switch_sequences.items():
        i=0
        while i<len(seq):
            if seq[i][0]!="recharge":
                i+=1; continue
            j=i
            while j+1<len(seq) and seq[j+1][0]=="recharge":
                j+=1
            if j+1<len(seq):
                assert seq[j+1][0]!="recharge"
                edges_block=tuple(x[3] for x in seq[i:j+2])
                # Compose the actually executed target return maps.
                AA,BB,DD=1,0,0
                for ed in edges_block:
                    target=cert_by_edge[ed][1]
                    BB=target['A']*BB + target['B']*(1<<DD)
                    AA=target['A']*AA
                    DD+=target['D']
                slope_contract = AA < (1<<DD)
                m0=seq[i][1]; mout=seq[j+1][2]
                assert (AA*m0+BB)==(1<<DD)*mout
                threshold = BB//((1<<DD)-AA)+1 if slope_contract else None
                # A=3^R for total odd-resource R; D=R+S for total even-resource S.
                tmp=AA; Rtot=0
                while tmp>1:
                    assert tmp%3==0
                    tmp//=3; Rtot+=1
                Stot=DD-Rtot
                target_data=tuple((cert_by_edge[ed][1]['A'],cert_by_edge[ed][1]['D'],
                                   cert_by_edge[ed][1]['word']) for ed in edges_block)
                row=(key,j-i+1,seq[j+1][0],m0,mout,
                     edges_block,AA,DD,BB,threshold,Rtot,Stot,target_data)
                discharge.append(row)
                if mout >= m0:
                    discharge_bad.append(row)
            i=j+1
    slope_bad=[x for x in discharge if not x[6] < (1<<x[7])]
    threshold_bad=[x for x in discharge if x[9] is None or x[3] < x[9]]
    print("RECHARGE_DISCHARGE_SLOPE_CONTRACTION",
          len(discharge)-len(slope_bad),"fail",len(slope_bad))
    if slope_bad:
        print("RECHARGE_DISCHARGE_SLOPE_SEPARATOR",slope_bad[:10])
    print("RECHARGE_DISCHARGE_THRESHOLD_VALID",
          len(discharge)-len(threshold_bad),"fail",len(threshold_bad))
    if threshold_bad:
        print("RECHARGE_DISCHARGE_THRESHOLD_SEPARATOR",threshold_bad[:10])
    print("RECHARGE_DISCHARGE_BLOCKS",len(discharge),
          "CONTRACTING",len(discharge)-len(discharge_bad),
          "NONCONTRACTING",len(discharge_bad))
    for row in discharge:
        print("RECHARGE_DISCHARGE_MACRO",row)
    if discharge_bad:
        print("RECHARGE_DISCHARGE_SEPARATOR",discharge_bad[:10])
    else:
        print("OBSERVED_ALL_RECHARGE_DISCHARGE_BLOCKS_CONTRACT_M")

    print("RECHARGE_STREAKS",len(streaks),
          "MAX_LENGTH",max((x[1] for x in streaks),default=0),
          "CONTRACTING",len(streaks)-len(expanding_streaks),
          "NONCONTRACTING",len(expanding_streaks))
    if expanding_streaks:
        print("RECHARGE_STREAK_SEPARATOR",expanding_streaks[:10])
    else:
        print("OBSERVED_ALL_RECHARGE_STREAKS_CONTRACT_M")
    if first_recharge is not None:
        print("FIRST_RIGID_RECHARGE",first_recharge)
    if cyc:
        for i,c in enumerate(sorted(cyc,key=len,reverse=True)[:10],1):
            print("RECHARGE_SCC",i,c)
        print("SEPARATOR_RECURRENT_RIGID_RECHARGE")
    else:
        print("OBSERVED_NO_RECURRENT_RIGID_RECHARGE")
    print("STATUS BOUNDED_DISCOVERY_ONLY")


if __name__=="__main__":
    ap=argparse.ArgumentParser()
    ap.add_argument("--source-lo",type=int,default=3)
    ap.add_argument("--source-N",type=int,default=127)
    ap.add_argument("--depth",type=int,default=16)
    a=ap.parse_args()
    analyze(a.source_N,a.depth,a.source_lo)
