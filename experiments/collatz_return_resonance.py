#!/usr/bin/env python3
"""Exact 2-adic resonance decomposition of Collatz first-return switches.

This experiment deletes every cross-pattern switch whose old-pattern defect
valuation differs from the exact injection valuation.  Those switches have a
theorem-forced valuation drop.  The retained graph contains only exact
resonances, the only switches capable of valuation recharge.

Finite SCC structure is a theorem-discovery signal, not a global Collatz
proof.  Every transition is reconstructed from the exact return interface.
"""
import argparse
import json
from collections import Counter,defaultdict
from pathlib import Path

from collatz_return_interface import certificate,switch_resonance,trace
from collatz_witness_compiler import read_rows


def _sort_key(x):
    return repr(x)


def strongly_connected_components(nodes,edges):
    """Iterative Kosaraju SCC decomposition for large finite graphs."""
    nodes=set(nodes);edges=set(edges)
    graph={v:[] for v in nodes};rev={v:[] for v in nodes}
    for a,b in edges:
        nodes.add(a);nodes.add(b)
        graph.setdefault(a,[]).append(b);graph.setdefault(b,[])
        rev.setdefault(b,[]).append(a);rev.setdefault(a,[])
    for g in (graph,rev):
        for v in g: g[v].sort(key=_sort_key)

    seen=set();order=[]
    for root in sorted(nodes,key=_sort_key):
        if root in seen: continue
        seen.add(root);stack=[(root,0)]
        while stack:
            v,i=stack[-1];adj=graph[v]
            if i<len(adj):
                w=adj[i];stack[-1]=(v,i+1)
                if w not in seen:
                    seen.add(w);stack.append((w,0))
            else:
                order.append(v);stack.pop()

    seen.clear();comps=[]
    for root in reversed(order):
        if root in seen: continue
        seen.add(root);stack=[root];comp=[]
        while stack:
            v=stack.pop();comp.append(v)
            for w in rev[v]:
                if w not in seen:
                    seen.add(w);stack.append(w)
        comps.append(sorted(comp,key=_sort_key))
    comps.sort(key=lambda c:_sort_key(c[0]) if c else '')
    return comps


def cyclic_sccs(nodes,edges):
    edges=set(edges)
    return [c for c in strongly_connected_components(nodes,edges)
            if len(c)>1 or (len(c)==1 and (c[0],c[0]) in edges)]


def node_key(c):
    p,u=c['q']
    return (c['r'],p,u)


def node_json(k):
    return {'r':k[0],'fixed_num':k[1],'fixed_den':k[2]}


def edge_json(e):
    return {'from':node_json(e[0]),'to':node_json(e[1])}


def analyze_rows(rows,cache=None):
    """Build the exact resonant cross-pattern graph before first descent."""
    if cache is None: cache={}
    counts=Counter();nodes=set();resonant_edges=Counter();stable_edges=Counter()
    recharge_edges=Counter();stable_recharge_edges=Counter()
    edge_cancel_max=defaultdict(int)
    max_cancel=None;first_resonance=None;first_recharge=None

    for row in rows:
        n=row['b'];states,branches=trace(n)
        last={states[0][0]:0};last_return={}
        for end in range(1,len(states)):
            r,mend,_,_=states[end]
            if r in last:
                start=last[r];mstart=states[start][1]
                word=tuple(branches[start:end])
                if word not in cache: cache[word]=certificate(word)
                c=cache[word]
                if r in last_return:
                    old=last_return[r]
                    z=switch_resonance(old,c,mstart,mend)
                    if z['same_fixed_point']:
                        counts['same_fixed_point']+=1
                    else:
                        counts['cross_pattern']+=1
                        edge=(node_key(old),node_key(c));nodes.update(edge)
                        stable=states[start][3]
                        if stable: counts['stable_cross_pattern']+=1
                        if z['resonant']:
                            counts['resonant']+=1;resonant_edges[edge]+=1
                            if stable:
                                counts['stable_resonant']+=1;stable_edges[edge]+=1
                            cd=z['cancellation_depth']
                            if cd is not None:
                                edge_cancel_max[edge]=max(edge_cancel_max[edge],cd)
                                if max_cancel is None or cd>max_cancel['cancellation_depth']:
                                    max_cancel={'seed':n,'edge':edge_json(edge),
                                                'cancellation_depth':cd,
                                                'valuation_before':z['valuation_before'],
                                                'valuation_after':z['valuation_after']}
                            if first_resonance is None:
                                first_resonance={'seed':n,'edge':edge_json(edge),
                                                 'valuation_before':z['valuation_before'],
                                                 'valuation_after':z['valuation_after'],
                                                 'cancellation_depth':cd}
                            if z['recharge']:
                                counts['recharge']+=1;recharge_edges[edge]+=1
                                if stable:
                                    counts['stable_recharge']+=1;stable_recharge_edges[edge]+=1
                                if first_recharge is None:
                                    first_recharge={'seed':n,'edge':edge_json(edge),
                                                    'valuation_before':z['valuation_before'],
                                                    'valuation_after':z['valuation_after'],
                                                    'cancellation_depth':cd,
                                                    'stable':stable}
                        else:
                            counts['nonresonant']+=1
                            if stable: counts['stable_nonresonant']+=1
                            # The exact interface proves this can never recharge.
                            assert not z['recharge']
                last_return[r]=c
            last[r]=end

    for key in ('same_fixed_point','cross_pattern','stable_cross_pattern','resonant',
                'stable_resonant','nonresonant','stable_nonresonant','recharge',
                'stable_recharge'):
        counts.setdefault(key,0)
    assert counts['cross_pattern']==counts['resonant']+counts['nonresonant']
    assert counts['stable_cross_pattern']==counts['stable_resonant']+counts['stable_nonresonant']
    assert counts['recharge']<=counts['resonant']
    assert counts['stable_recharge']<=counts['stable_resonant']

    res_edge_set=set(resonant_edges);stable_edge_set=set(stable_edges)
    res_nodes={x for e in res_edge_set for x in e}
    stable_nodes={x for e in stable_edge_set for x in e}
    cyc=cyclic_sccs(res_nodes,res_edge_set)
    stable_cyc=cyclic_sccs(stable_nodes,stable_edge_set)

    result={
        'K':rows[0]['K'],'families':len(rows),'counts':dict(counts),
        'resonant_nodes':len(res_nodes),'resonant_unique_edges':len(res_edge_set),
        'stable_resonant_nodes':len(stable_nodes),'stable_resonant_unique_edges':len(stable_edge_set),
        'resonant_cyclic_scc_count':len(cyc),
        'resonant_cyclic_scc_sizes':sorted((len(c) for c in cyc),reverse=True),
        'stable_resonant_cyclic_scc_count':len(stable_cyc),
        'stable_resonant_cyclic_scc_sizes':sorted((len(c) for c in stable_cyc),reverse=True),
        'first_resonance':first_resonance,'first_recharge':first_recharge,
        'largest_cancellation':max_cancel,
        'recharge_requires_resonance':True,
    }
    aux={
        'resonant_edges':resonant_edges,'stable_edges':stable_edges,
        'recharge_edges':recharge_edges,'stable_recharge_edges':stable_recharge_edges,
        'edge_cancel_max':edge_cancel_max,
    }
    return result,aux


def cumulative_graph_summary(edge_sets):
    edges=set().union(*edge_sets) if edge_sets else set()
    nodes={x for e in edges for x in e}
    cyc=cyclic_sccs(nodes,edges)
    return {'nodes':len(nodes),'unique_edges':len(edges),'cyclic_scc_count':len(cyc),
            'cyclic_scc_sizes':sorted((len(c) for c in cyc),reverse=True)}


def frozen_transfer(train_edges,future_aux):
    train=set(train_edges);occ=future_aux['stable_edges'];rch=future_aux['stable_recharge_edges']
    unique=set(occ);known=unique&train;novel=unique-train
    return {
        'frozen_unique_edges':len(train),
        'future_unique_edges':len(unique),'known_unique_edges':len(known),'novel_unique_edges':len(novel),
        'future_occurrences':sum(occ.values()),
        'known_occurrences':sum(v for e,v in occ.items() if e in train),
        'novel_occurrences':sum(v for e,v in occ.items() if e not in train),
        'future_recharges':sum(rch.values()),
        'known_edge_recharges':sum(v for e,v in rch.items() if e in train),
        'novel_edge_recharges':sum(v for e,v in rch.items() if e not in train),
    }


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('inputs',nargs='+');ap.add_argument('--out',required=True)
    a=ap.parse_args()
    cache={};results=[];aux_by_k={};cumulative=[];cum_sets=[]
    for path in a.inputs:
        rows=read_rows(path);result,aux=analyze_rows(rows,cache)
        results.append(result);aux_by_k[result['K']]=aux
        cum_sets.append(set(aux['stable_edges']))
        cs=cumulative_graph_summary(cum_sets);cs['through_K']=result['K'];cumulative.append(cs)
        print('RESONANCE_CENSUS',json.dumps(result,separators=(',',':'),sort_keys=True),flush=True)
        print('RESONANCE_CUMULATIVE',json.dumps(cs,separators=(',',':'),sort_keys=True),flush=True)

    transfer={}
    if 12 in aux_by_k and 16 in aux_by_k:
        frozen=set(aux_by_k[12]['stable_edges'])|set(aux_by_k[16]['stable_edges'])
        for K in (20,24):
            if K in aux_by_k: transfer[str(K)]=frozen_transfer(frozen,aux_by_k[K])

    out={'status':'EXACT FINITE RESONANCE DECOMPOSITION; NOT GLOBAL CLOSURE',
         'results':results,'cumulative_stable_resonant_graph':cumulative,
         'frozen_B12_B16_transfer':transfer,
         'scope':'first-return switches before direct descent on supplied boundary families'}
    Path(a.out).write_text(json.dumps(out,indent=2,sort_keys=True)+'\n')
    print('VERIFIED_RECHARGE_REQUIRES_EXACT_2ADIC_RESONANCE')
    print('VERIFIED_FINITE_RESONANT_RETURN_GRAPH_CENSUS_NOT_GLOBAL_PROOF')


if __name__=='__main__': main()
