#!/usr/bin/env python3
"""Expose the native grammar behind the bounded zero-block switch DAG."""
from __future__ import annotations
import json
from collections import defaultdict,Counter
import collatz_zero_block_rank_crystal_20260930 as z

seqs=z.collect(3,32767,128)
# Recover a representative exact return word for every semantic law.
words=defaultdict(set)
for n in range(3,32768,2):
    for _,seq in z.returns(n,128).items():
        for c,_,_ in seq:
            words[z.sid(c)].add(tuple(tuple(x) for x in c["word"]))

nodes=set();succ=defaultdict(set);witness={}
for sw in seqs:
    for i,(a,b) in enumerate(zip(sw,sw[1:])):
        if a["zero"] and b["zero"]:
            u=(a["old"],a["new"]);v=(b["old"],b["new"])
            nodes|={u,v};succ[u].add(v);succ.setdefault(v,set())
            witness.setdefault((u,v),{
                "source":a["source"],"anchor":a["anchor"],
                "precisions":[a["p0"],a["p1"],b["p1"]],
            })
for n in nodes:succ.setdefault(n,set())
rank,left,layers=z.elim_rank(nodes,succ);assert not left

# Enumerate all source-free maximal paths from top rank to sinks.
tops=sorted((n for n in nodes if rank[n]==max(rank.values())),key=repr)
paths=[]
def walk(path):
    u=path[-1]
    if not succ[u]:
        paths.append(tuple(path));return
    for v in sorted(succ[u],key=repr):walk(path+[v])
for t in tops:walk([t])

def chart(c):
    r,A,B,D=c
    return {
      "id":[r,A,B,D],"q":z.log3pow(A),"D":D,
      "word_variants":[[list(x) for x in w] for w in sorted(words.get(c,set()),key=repr)],
    }
def path_json(p):
    # edge-state path (W0,W1),(W1,W2),... -> chart chain W0,W1,...
    chain=[p[0][0]]+[x[1] for x in p]
    ws=[]
    for a,b in zip(p,p[1:]):ws.append(witness.get((a,b)))
    return {
      "ranks":[rank[x] for x in p],
      "charts":[chart(c) for c in chain],
      "transition_witnesses":ws,
    }

# Direct source-wise zero streaks with exact chart chains and termination type.
source_streaks=[]
for sw in seqs:
    i=0
    while i<len(sw):
        if not sw[i]["zero"]:i+=1;continue
        j=i
        while j+1<len(sw) and sw[j+1]["zero"]:j+=1
        if j-i+1>=2:
            chain=[sw[i]["old"]]+[sw[k]["new"] for k in range(i,j+1)]
            source_streaks.append({
              "length":j-i+1,"source":sw[i]["source"],"anchor":sw[i]["anchor"],
              "precisions":[sw[i]["p0"]]+[sw[k]["p1"] for k in range(i,j+1)],
              "charts":[chart(c) for c in chain],
              "next_switch_kind":(
                "NONZERO" if j+1<len(sw) and not sw[j+1]["zero"]
                else "NO_FURTHER_SWITCH"
              ),
            })
        i=j+1
source_streaks.sort(key=lambda x:(-x["length"],x["source"],x["anchor"]))

result={
 "schema":"COLLATZ_ZERO_BLOCK_GRAMMAR_CRYSTAL_20260930",
 "graph":{"nodes":len(nodes),"edges":sum(len(v) for v in succ.values()),
          "layers":layers,"top_nodes":len(tops),"maximal_paths":len(paths)},
 "maximal_rank_paths":[path_json(p) for p in paths],
 "longest_source_streaks":source_streaks[:30],
 "termination_histogram":dict(Counter(x["next_switch_kind"] for x in source_streaks)),
 "global_collatz":"UNKNOWN",
}
print(json.dumps(result,indent=2))
