#!/usr/bin/env python3
"""Crystal V32: exact K-density tradeoff on the complete no-B chamber graph.

Parents:
  V27 cost-aware chamber
  V30 universal cost20 contraction
  V31 complete K rewind alphabet

For every non-B transition define
  w_c = 19*bit - 12 + c*drop
where drop is the lower-cost K rewind amount (0 for I and same-cost K).

At c=19, an exact difference-constraint potential proves every directed cycle
has nonnegative total weight:
  19*q - 12*k + 19*D >= 0.

At c=18 the inequality is false.  A concrete 49-edge cycle has
  k=49, q=29, D=2
and weight -1.  Hence coefficient 19 is sharp on this finite quotient.

Interpretation: any no-B path whose actual parity density falls below 12/19
must pay lower-cost K rewind at a quantitatively coupled rate.  This is not yet
a source-order contradiction; V31 local rewind must still be coupled to the
original-source/canonical-M register.
"""
from collections import Counter, defaultdict, deque
from itertools import combinations
import hashlib, json

O=12
MOD=3**O

def compositions(total, parts):
    for cuts in combinations(range(1,total),parts-1):
        p=0; w=[]
        for c in cuts+(total,):
            w.append(c-p); p=c
        yield tuple(w)

def cocycle(w):
    c=0
    for i,a in enumerate(w):
        c=(1<<a)*c+3**i
    return c

all_by_res=defaultdict(list)
for S in range(12,20):
    inv=pow(1<<S,-1,MOD)
    for w in compositions(S,O):
        C=cocycle(w)
        r=(C*inv)%MOD
        all_by_res[r].append((S,C,w))
best={r:min(vals,key=lambda x:(x[0],-x[1],x[2])) for r,vals in all_by_res.items()}
assert len(best)==27469

def word_to_bits(w):
    out=[]
    for a in reversed(w):
        out.append(1); out.extend([0]*(a-1))
    return tuple(out)

def bits_to_word(bits):
    assert bits and bits[0]==1 and sum(bits)==O
    ones=[i for i,b in enumerate(bits) if b]
    seg=[]
    for j,i in enumerate(ones):
        nxt=ones[j+1] if j+1<len(ones) else len(bits)
        seg.append(nxt-i)
    return tuple(reversed(seg))

def next_window(w,bit):
    bits=list(word_to_bits(w))
    bits.append(bit)
    if bit==1:
        ones=[i for i,b in enumerate(bits) if b]
        bits=bits[ones[1]:]
    assert sum(bits)==O
    return bits_to_word(tuple(bits))

def classify_word(w):
    S=sum(w)
    if S>19:
        return "B",None
    C=cocycle(w)
    r=(C*pow(1<<S,-1,MOD))%MOD
    bS,bC,bw=best[r]
    if (S,C)==(bS,bC):
        assert w==bw
        return "I",r
    assert bS<S or (bS==S and bC>C)
    return "K",r

edges=[]
adj=defaultdict(list)
outcomes=Counter()
for u,(S,C,w) in sorted(best.items()):
    for bit in (0,1):
        nw=next_window(w,bit)
        cls,v=classify_word(nw)
        outcomes[(bit,cls)]+=1
        if cls=="B":
            continue
        drop=0
        if cls=="K":
            rawS=sum(nw)
            bestS,bestC,bestW=best[v]
            drop=rawS-bestS
            assert drop>=0
        row=(u,v,bit,cls,drop)
        edges.append(row)
        adj[u].append((v,bit,cls,drop))

assert len(edges)==38991
assert Counter((cl,d) for _u,_v,_b,cl,d in edges if cl=="K")==Counter({
    ("K",0):450,("K",1):3702,("K",2):107,("K",3):13,("K",4):9,("K",5):1
})

# SPFA construction of a potential for c=19.  Initial distance 0 at every
# vertex is equivalent to a zero-cost super-source.  No negative cycle and
# final dist[v] <= dist[u] + w imply reduced cost >=0 on every edge.
N=len(best)
dist={v:0 for v in best}
q=deque(best)
inq=set(best)
relax_count={v:0 for v in best}
relaxations=0
while q:
    u=q.popleft(); inq.discard(u)
    du=dist[u]
    for v,bit,cls,drop in adj[u]:
        w=19*bit-12+19*drop
        cand=du+w
        if cand<dist[v]:
            dist[v]=cand
            relax_count[v]+=1
            relaxations+=1
            assert relax_count[v] <= N, "negative cycle under c=19"
            if v not in inq:
                q.append(v); inq.add(v)

min_rc=10**9
zero_rc=0
for u,v,bit,cls,drop in edges:
    w=19*bit-12+19*drop
    rc=w+dist[u]-dist[v]
    assert rc>=0
    min_rc=min(min_rc,rc)
    zero_rc += (rc==0)
assert min_rc==0

# Exact sharpness witness for c=18.
cycle=[
169775,254663,381995,41552,328049,492074,246037,369056,184528,
92264,46132,23066,300320,184760,92380,46190,335006,236789,384115,
44732,332819,499229,217403,374422,187211,359326,179663,269495,
404243,74924,378107,35720,17860,8930,279116,139558,475058,237529,
356294,178147,267221,399331,67556,33778,316388,158194,503012,
488798,467477,169775
]
edge_lookup=defaultdict(list)
for row in edges:
    edge_lookup[(row[0],row[1])].append(row)
w18=qsum=dsum=0
cycle_rows=[]
for a,b in zip(cycle[:-1],cycle[1:]):
    opts=edge_lookup[(a,b)]
    assert opts
    # The witness is unique at the minimum c=18 weight if parallel edges exist.
    row=min(opts,key=lambda z:19*z[2]-12+18*z[4])
    _u,_v,bit,cls,drop=row
    ww=19*bit-12+18*drop
    w18+=ww; qsum+=bit; dsum+=drop
    cycle_rows.append({"u":a,"v":b,"bit":bit,"class":cls,"drop":drop,"w18":ww})
assert len(cycle_rows)==49
assert qsum==29 and dsum==2 and w18==-1
w19=19*qsum-12*len(cycle_rows)+19*dsum
assert w19==1

potential_rows=[[v,dist[v]] for v in sorted(dist)]
potential_sha=hashlib.sha256(json.dumps(potential_rows,separators=(",",":")).encode()).hexdigest()

result={
  "schema":"COLLATZ_CRYSTAL_K_DENSITY_TRADEOFF_V32",
  "parents":{
    "V27":"collatz-crystal-cost-aware-chamber-v27@f11de4820166b3d87e6a5bb0d571334fe8d97449",
    "V30":"collatz-crystal-cost20-contraction-v30@f07e244b2ae64277037f0d51ece84b4a91067ae7",
    "V31":"collatz-crystal-k-rewind-v31@dcc994ab36741ac1bc42edb29001631530f70835"
  },
  "graph":{
    "states":len(best),
    "non_B_edges":len(edges),
    "outcomes":{f"{b}:{c}":n for (b,c),n in sorted(outcomes.items())},
  },
  "tradeoff_certificate":{
    "cycle_inequality":"19*q - 12*k + 19*D >= 0",
    "D":"sum of lower-cost K rewind drops; same-cost K contributes 0",
    "relaxations":relaxations,
    "zero_reduced_edges":zero_rc,
    "potential_sha256":potential_sha,
    "consequence":"parity deficit below 12/19 can occur only by paying K-drop D"
  },
  "sharpness":{
    "coefficient_18_rejected":True,
    "cycle_length":49,
    "odd_steps":qsum,
    "K_drop":dsum,
    "weight_c18":w18,
    "weight_c19":w19,
    "cycle":cycle_rows,
  },
  "scientific_verdict":"WARRANTED_FINITE_GRAPH_K_DENSITY_TRADEOFF; SOURCE_ORDER_COUPLING_STILL_REQUIRED",
  "next_residual":{
    "name":"K_DROP_TO_SOURCE_MARGIN",
    "statement":"Use V31 2^d*p=x+E with p>=original minimal source to convert positive asymptotic K-drop D into a source-relative height/canonical-M cost, then test whether the exact V32 tradeoff permits an infinite rational-natural no-Exit path.",
    "forbidden_shortcuts":["larger chamber","deeper parameter census","treat local owner descent as original-source descent"]
  },
  "universal_status":"UNKNOWN",
  "global_collatz":"UNKNOWN"
}
result["certificate_sha256"]=hashlib.sha256(json.dumps(result,sort_keys=True,separators=(",",":")).encode()).hexdigest()
print(json.dumps(result,indent=2,sort_keys=True))
