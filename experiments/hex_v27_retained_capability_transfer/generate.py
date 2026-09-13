#!/usr/bin/env python3
import itertools, json, pathlib

ROOT=pathlib.Path(__file__).resolve().parent
OUT=ROOT/"results"

PERM=(1,2,0)

CASES=[
  {
    "name":"arity6",
    "arities":[1,1,6],
    "rels":[
      [(0,)],
      [(1,)],
      [(0,1,2,0,2,1),(2,0,1,2,1,0)]
    ],
    "neg_relation":2,
    "neg_replace_index":1,
    "neg_tuple":(2,0,1,2,1,2)
  },
  {
    "name":"mixed_2_3_6",
    "arities":[1,1,2,3,6],
    "rels":[
      [(0,)],
      [(1,)],
      [(0,2),(1,0)],
      [(0,1,2),(2,0,1)],
      [(0,2,1,0,1,2),(1,0,2,2,0,1)]
    ],
    "neg_relation":4,
    "neg_replace_index":1,
    "neg_tuple":(1,0,2,2,0,2)
  },
  {
    "name":"mixed_4_6",
    "arities":[1,1,4,6],
    "rels":[
      [(0,)],
      [(1,)],
      [(0,1,2,0),(2,0,1,2)],
      [(2,1,0,2,0,1),(0,2,1,1,2,0)]
    ],
    "neg_relation":3,
    "neg_replace_index":0,
    "neg_tuple":(2,1,0,2,0,2)
  }
]

def canon_rels(rels):
    return tuple(frozenset(tuple(t) for t in R) for R in rels)

def apply_perm(rels,p):
    return tuple(frozenset(tuple(p[x] for x in t) for t in R) for R in rels)

def source_iso(A,B,n=3):
    for p in itertools.permutations(range(n)):
        if apply_perm(A,p)==B:
            return True,p
    return False,None

def semantic_graph(rels,arities,n=3):
    rels=canon_rels(rels)
    nodes=[]
    colors=[]
    index={}
    color_base=[]
    c=0
    for a in arities:
        color_base.append(c)
        c+=a
    anchor_color=c
    occ_color_base=c+1
    K=occ_color_base+len(arities)

    # all role views
    for r,a in enumerate(arities):
        for pos in range(a):
            for v in range(n):
                key=("role",r,pos,v)
                index[key]=len(nodes); nodes.append(key); colors.append(color_base[r]+pos)

    # identity anchors
    for v in range(n):
        key=("anchor",v)
        index[key]=len(nodes); nodes.append(key); colors.append(anchor_color)

    # occurrence nodes
    occ_keys=[]
    for r,R in enumerate(rels):
        for t in sorted(R):
            key=("occ",r,t)
            index[key]=len(nodes); nodes.append(key); colors.append(occ_color_base+r)
            occ_keys.append(key)

    edges=set()
    for r,a in enumerate(arities):
        for pos in range(a):
            for v in range(n):
                u=index[("role",r,pos,v)]
                w=index[("anchor",v)]
                edges.add(tuple(sorted((u,w))))
    for key in occ_keys:
        _,r,t=key
        o=index[key]
        for pos,v in enumerate(t):
            u=index[("role",r,pos,v)]
            edges.add(tuple(sorted((o,u))))

    assert set(colors)==set(range(K)), (set(colors),K)
    return {"N":len(nodes),"K":K,"edges":sorted(edges),"colors":colors}

def lean_edges(es):
    return "["+", ".join(f"({a},{b})" for a,b in es)+"]"

def lean_colors(cs,K):
    return "#v["+", ".join((f"({c} : Fin {K})" if i==0 else str(c)) for i,c in enumerate(cs))+"]"

def emit_graph(prefix,g):
    N,K=g["N"],g["K"]
    cells=lean_colors(g["colors"],K)
    return f"""
def {prefix}Fallback : Coloring {N} {K} := Coloring.mod {N} {K}
def {prefix}Cells : Vector (Fin {K}) {N} := {cells}
#guard (Coloring.ofVector? {prefix}Cells).isSome
def {prefix}Coloring : Coloring {N} {K} :=
  (Coloring.ofVector? {prefix}Cells).getD {prefix}Fallback
def {prefix} : Colored {N} {K} where
  graph := Graph.ofEdges {lean_edges(g["edges"])}
  coloring := {prefix}Coloring
"""

def main():
    rows=[]
    chunks=["import HexGraphIso.Tactic\n\nopen Hex Hex.GraphIso\n"]
    for case in CASES:
        name=case["name"]
        arities=case["arities"]
        A=canon_rels(case["rels"])
        B=apply_perm(A,PERM)
        C=[set(R) for R in A]
        r=case["neg_relation"]; i=case["neg_replace_index"]
        old=sorted(C[r])[i]
        C[r].remove(old); C[r].add(tuple(case["neg_tuple"]))
        C=canon_rels(C)
        pos,pp=source_iso(A,B)
        neg,np=source_iso(A,C)
        assert pos and pp is not None
        assert not neg
        gA=semantic_graph(A,arities); gB=semantic_graph(B,arities); gC=semantic_graph(C,arities)
        assert (gA["N"],gA["K"])==(gB["N"],gB["K"])==(gC["N"],gC["K"])
        cap=name.replace("_","").title()
        chunks.append(emit_graph(cap+"A",gA))
        chunks.append(emit_graph(cap+"B",gB))
        chunks.append(emit_graph(cap+"C",gC))
        chunks.append(f"""
set_option trace.graph_iso true in
example : Isomorphic {cap}A {cap}B := by
  graph_iso

set_option trace.graph_iso true in
example : ¬ Isomorphic {cap}A {cap}C := by
  graph_iso
""")
        rows.append({
          "case":name,
          "arities":arities,
          "source_positive":pos,
          "source_positive_witness":list(pp),
          "source_negative":not neg,
          "node_count":gA["N"],
          "color_count":gA["K"],
          "representation_candidates_evaluated":0,
          "development_transitions":0
        })

    OUT.mkdir(exist_ok=True)
    (ROOT/"Generated.lean").write_text("\n".join(chunks))
    ev={
      "verdict":"SOURCE_CHALLENGE_PACK_VERIFIED",
      "frozen_representation":"IDENTITY_ANCHOR_PLUS_ALL_ACTIVE_OCCURRENCE",
      "cases":rows,
      "gates":{
        "all_source_positive":all(x["source_positive"] for x in rows),
        "all_source_negative":all(x["source_negative"] for x in rows),
        "zero_representation_search":all(x["representation_candidates_evaluated"]==0 for x in rows),
        "zero_development_transitions":all(x["development_transitions"]==0 for x in rows)
      }
    }
    (OUT/"source_evidence.json").write_text(json.dumps(ev,indent=2,sort_keys=True)+"\n")
    print(json.dumps(ev,indent=2,sort_keys=True))

if __name__=="__main__":
    main()
