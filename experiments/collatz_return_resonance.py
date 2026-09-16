#!/usr/bin/env python3
"""Exact hierarchical 2-adic decomposition of Collatz first-return switches.

Distinct exact first-return cylinders at one anchor are disjoint. Their fixed
points therefore separate before the shorter exact domain ends, forcing every
actual cross-pattern switch into first-order defect resonance. The selective
condition is one level deeper: a switch recharges the old-pattern defect iff
the new-cylinder excess depth equals separation_depth-1.

This census retains only those exact second-order recharge edges for the hard
transition graph. Finite SCC structure is theorem-discovery data, not a global
Collatz proof.
"""
import argparse
import json
from collections import Counter,defaultdict
from pathlib import Path

from collatz_return_interface import certificate,cylinder_separation,switch_recharge_law,trace
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


def graph_summary(edge_counter):
    edges=set(edge_counter);nodes={x for e in edges for x in e};cyc=cyclic_sccs(nodes,edges)
    return {'nodes':len(nodes),'unique_edges':len(edges),'occurrences':sum(edge_counter.values()),
            'cyclic_scc_count':len(cyc),
            'cyclic_scc_sizes':sorted((len(c) for c in cyc),reverse=True)}


def analyze_rows(rows,cache=None):
    """Build exact first-order and second-order switch graphs before descent."""
    if cache is None: cache={}
    counts=Counter();resonant_edges=Counter();stable_edges=Counter()
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
                    if old['q']==c['q']:
                        counts['same_fixed_point']+=1
                    else:
                        sep=cylinder_separation(old,c)
                        # Consecutive distinct first-return words are deterministic
                        # alternatives, so their exact execution cylinders cannot overlap.
                        assert sep['disjoint']
                        z=switch_recharge_law(old,c,mstart,mend)
                        assert z['resonant']
                        assert z['valuation_before']==sep['separation_valuation']
                        counts['cross_pattern']+=1;counts['resonant']+=1
                        counts['forced_resonance_by_disjoint_cylinders']+=1
                        counts['second_order_'+z['outcome']]+=1
                        edge=(node_key(old),node_key(c));resonant_edges[edge]+=1
                        stable=states[start][3]
                        if stable:
                            counts['stable_cross_pattern']+=1;counts['stable_resonant']+=1
                            counts['stable_forced_resonance_by_disjoint_cylinders']+=1
                            counts['stable_second_order_'+z['outcome']]+=1
                            stable_edges[edge]+=1

                        cd=z['cancellation_depth']
                        if cd is not None:
                            edge_cancel_max[edge]=max(edge_cancel_max[edge],cd)
                            if max_cancel is None or cd>max_cancel['cancellation_depth']:
                                max_cancel={'seed':n,'edge':edge_json(edge),
                                            'cancellation_depth':cd,
                                            'separation_valuation':sep['separation_valuation'],
                                            'new_domain_excess':z['new_domain_excess'],
                                            'valuation_after':z['valuation_after']}
                        if first_resonance is None:
                            first_resonance={'seed':n,'edge':edge_json(edge),
                                             'separation_valuation':sep['separation_valuation'],
                                             'new_domain_excess':z['new_domain_excess'],
                                             'outcome':z['outcome']}
                        if z['recharge']:
                            counts['recharge']+=1;recharge_edges[edge]+=1
                            if stable:
                                counts['stable_recharge']+=1;stable_recharge_edges[edge]+=1
                            if first_recharge is None:
                                first_recharge={'seed':n,'edge':edge_json(edge),
                                                'separation_valuation':sep['separation_valuation'],
                                                'new_domain_excess':z['new_domain_excess'],
                                                'valuation_after':z['valuation_after'],
                                                'cancellation_depth':cd,'stable':stable}
                last_return[r]=c
            last[r]=end

    for key in ('same_fixed_point','cross_pattern','stable_cross_pattern','resonant',
                'stable_resonant','nonresonant','stable_nonresonant','recharge',
                'stable_recharge','forced_resonance_by_disjoint_cylinders',
                'stable_forced_resonance_by_disjoint_cylinders','second_order_drop',
                'second_order_flat','second_order_recharge','stable_second_order_drop',
                'stable_second_order_flat','stable_second_order_recharge'):
        counts.setdefault(key,0)

    assert counts['nonresonant']==counts['stable_nonresonant']==0
    assert counts['cross_pattern']==counts['resonant']==counts['forced_resonance_by_disjoint_cylinders']
    assert counts['stable_cross_pattern']==counts['stable_resonant']==counts['stable_forced_resonance_by_disjoint_cylinders']
    assert counts['cross_pattern']==counts['second_order_drop']+counts['second_order_flat']+counts['second_order_recharge']
    assert counts['stable_cross_pattern']==counts['stable_second_order_drop']+counts['stable_second_order_flat']+counts['stable_second_order_recharge']
    assert counts['recharge']==counts['second_order_recharge']
    assert counts['stable_recharge']==counts['stable_second_order_recharge']

    first_graph=graph_summary(resonant_edges);stable_first_graph=graph_summary(stable_edges)
    second_graph=graph_summary(recharge_edges);stable_second_graph=graph_summary(stable_recharge_edges)

    result={
        'K':rows[0]['K'],'families':len(rows),'counts':dict(counts),
        'first_order_resonant_graph':first_graph,
        'stable_first_order_resonant_graph':stable_first_graph,
        'second_order_recharge_graph':second_graph,
        'stable_second_order_recharge_graph':stable_second_graph,
        # Backward-compatible headline fields.
        'resonant_nodes':first_graph['nodes'],'resonant_unique_edges':first_graph['unique_edges'],
        'stable_resonant_nodes':stable_first_graph['nodes'],'stable_resonant_unique_edges':stable_first_graph['unique_edges'],
        'resonant_cyclic_scc_count':first_graph['cyclic_scc_count'],
        'resonant_cyclic_scc_sizes':first_graph['cyclic_scc_sizes'],
        'stable_resonant_cyclic_scc_count':stable_first_graph['cyclic_scc_count'],
        'stable_resonant_cyclic_scc_sizes':stable_first_graph['cyclic_scc_sizes'],
        'first_resonance':first_resonance,'first_recharge':first_recharge,
        'largest_cancellation':max_cancel,
        'recharge_requires_resonance':True,
        'distinct_first_return_switches_force_resonance':True,
        'recharge_iff_second_order_resonance':True,
    }
    aux={
        'resonant_edges':resonant_edges,'stable_edges':stable_edges,
        'recharge_edges':recharge_edges,'stable_recharge_edges':stable_recharge_edges,
        'edge_cancel_max':edge_cancel_max,
    }
    return result,aux


def cumulative_graph_summary(edge_sets):
    edges=set().union(*edge_sets) if edge_sets else set()
    nodes={x for e in edges for x in e};cyc=cyclic_sccs(nodes,edges)
    return {'nodes':len(nodes),'unique_edges':len(edges),'cyclic_scc_count':len(cyc),
            'cyclic_scc_sizes':sorted((len(c) for c in cyc),reverse=True)}


def frozen_transfer(train_edges,future_aux,key='stable_edges'):
    train=set(train_edges);occ=future_aux[key]
    unique=set(occ);known=unique&train;novel=unique-train
    return {'frozen_unique_edges':len(train),'future_unique_edges':len(unique),
            'known_unique_edges':len(known),'novel_unique_edges':len(novel),
            'future_occurrences':sum(occ.values()),
            'known_occurrences':sum(v for e,v in occ.items() if e in train),
            'novel_occurrences':sum(v for e,v in occ.items() if e not in train)}


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('inputs',nargs='+');ap.add_argument('--out',required=True)
    a=ap.parse_args()
    cache={};results=[];aux_by_k={};cumulative=[];cumulative_recharge=[]
    cum_sets=[];cum_recharge_sets=[]
    for path in a.inputs:
        rows=read_rows(path);result,aux=analyze_rows(rows,cache)
        results.append(result);aux_by_k[result['K']]=aux
        cum_sets.append(set(aux['stable_edges']))
        cs=cumulative_graph_summary(cum_sets);cs['through_K']=result['K'];cumulative.append(cs)
        cum_recharge_sets.append(set(aux['stable_recharge_edges']))
        cr=cumulative_graph_summary(cum_recharge_sets);cr['through_K']=result['K'];cumulative_recharge.append(cr)
        print('RESONANCE_CENSUS',json.dumps(result,separators=(',',':'),sort_keys=True),flush=True)
        print('RESONANCE_CUMULATIVE',json.dumps(cs,separators=(',',':'),sort_keys=True),flush=True)
        print('RECHARGE_CUMULATIVE',json.dumps(cr,separators=(',',':'),sort_keys=True),flush=True)

    transfer={};recharge_transfer={}
    if 12 in aux_by_k and 16 in aux_by_k:
        frozen=set(aux_by_k[12]['stable_edges'])|set(aux_by_k[16]['stable_edges'])
        frozen_recharge=set(aux_by_k[12]['stable_recharge_edges'])|set(aux_by_k[16]['stable_recharge_edges'])
        for K in (20,24):
            if K in aux_by_k:
                transfer[str(K)]=frozen_transfer(frozen,aux_by_k[K],'stable_edges')
                recharge_transfer[str(K)]=frozen_transfer(frozen_recharge,aux_by_k[K],'stable_recharge_edges')

    out={'status':'EXACT FINITE RESONANCE DECOMPOSITION; NOT GLOBAL CLOSURE',
         'results':results,'cumulative_stable_resonant_graph':cumulative,
         'cumulative_stable_second_order_recharge_graph':cumulative_recharge,
         'frozen_B12_B16_transfer':transfer,
         'frozen_B12_B16_second_order_recharge_transfer':recharge_transfer,
         'scope':'first-return switches before direct descent on supplied boundary families'}
    Path(a.out).write_text(json.dumps(out,indent=2,sort_keys=True)+'\n')
    print('VERIFIED_DISTINCT_FIRST_RETURN_SWITCHES_FORCE_2ADIC_RESONANCE')
    print('VERIFIED_RECHARGE_IFF_SECOND_ORDER_RESONANCE')
    print('VERIFIED_FINITE_SECOND_ORDER_RECHARGE_GRAPH_NOT_GLOBAL_PROOF')


if __name__=='__main__': main()
