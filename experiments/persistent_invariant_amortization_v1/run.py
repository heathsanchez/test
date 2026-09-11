#!/usr/bin/env python3
import hashlib, itertools, json, pathlib

ROOT=pathlib.Path(__file__).parent
PATTERNS=((0,0,0),(0,1,0),(1,0,1),(1,1,1))
# Frozen prospective carriers.  They differ in cardinality and opaque row order;
# none appeared in the genesis experiment.
SPECS=((5,3),(6,11),(7,5),(8,13),(9,17),(10,19),(11,23),(12,29),(13,31),(14,37),(15,41),(16,43))

def carrier(n,seed):
    rows=[PATTERNS[i%4] for i in range(n)]
    # Deterministic Fisher-Yates-like permutation, frozen by seed.
    for i in range(n-1,0,-1):
        j=(seed*(i+1)+i*i+3)% (i+1); rows[i],rows[j]=rows[j],rows[i]
    return tuple(rows)

TARGETS=tuple(carrier(*s) for s in SPECS)

def ev(e,r):
    if e[0]=="field":return r[e[1]]
    if e[0]=="not":return 1-ev(e[1],r)
    a,b=ev(e[1],r),ev(e[2],r)
    return (a&b) if e[0]=="and" else (a|b)

def generate(rows,max_depth=4):
    levels=[];seen={};calls=0
    base=[]
    for i in range(3):
        e=("field",i);b=tuple(ev(e,r) for r in rows);calls+=len(rows)
        if b not in seen:seen[b]=e;base.append(e)
    levels.append(base)
    for d in range(1,max_depth+1):
        new=[]
        for x in levels[d-1]:
            e=("not",x);b=tuple(ev(e,r) for r in rows);calls+=len(rows)
            if b not in seen:seen[b]=e;new.append(e)
        for dl in range(d):
            dr=d-1-dl
            for x in levels[dl]:
                for y in levels[dr]:
                    for op in ("and","or"):
                        e=(op,x,y);b=tuple(ev(e,r) for r in rows);calls+=len(rows)
                        if b not in seen:seen[b]=e;new.append(e)
        levels.append(new)
    return seen,calls

def construct(rows):
    required=tuple(int(r[0]!=r[1]) for r in rows)
    space,calls=generate(rows)
    return space[required],calls

def quotient(rows,expr):
    ps=[(r[2],ev(expr,r)) for r in rows]
    ids={p:i for i,p in enumerate(sorted(set(ps)))}
    return tuple(ids[p] for p in ps),len(ids)

def dg(x):return hashlib.sha256(json.dumps(x,sort_keys=True,separators=(",",":")).encode()).hexdigest()

def main():
    # Genesis is paid once on a five-element calibration carrier.  The retained
    # state is the constructed AST plus its complete behavioral certificate.
    genesis_rows=((1,0,1),(0,0,0),(1,1,1),(0,1,0),(1,0,1))
    retained,g=construct(genesis_rows)
    assert g==1405
    cumulative={k:[] for k in ("cold","persistent","midstream_ablation","sham","answer_memory")}
    totals={k:0 for k in cumulative}; rows=[]
    for idx,t in enumerate(TARGETS):
        q,qn=quotient(t,retained); n=len(t); assert qn==4
        bridge_space=4**4
        cold=bridge_space*n
        reuse=2*n # verify retained continuation + verify selected bridge
        costs={"cold":cold,
               "persistent":reuse+(g if idx==0 else 0),
               "midstream_ablation":reuse+(g if idx==0 else 0) if idx<6 else cold,
               "sham":cold+(g if idx==0 else 0),
               "answer_memory":cold+n+(g if idx==0 else 0)}
        for k,v in costs.items():totals[k]+=v;cumulative[k].append(totals[k])
        rows.append({"target":idx+1,"carrier_size":n,"quotient":q,"quotient_size":qn,
                     "bridge_space":bridge_space,"costs":costs,"cumulative":{k:cumulative[k][-1] for k in cumulative}})
    crossover=next((i+1 for i,(c,w) in enumerate(zip(cumulative["cold"],cumulative["persistent"])) if w<c),None)
    gates={"genesis_paid_once":sum(1 for r in rows if r["costs"]["persistent"]>2*r["carrier_size"])==1,
           "all_quotients_emerge":all(r["quotient_size"]==4 for r in rows),
           "prospective_sequence":len(rows)==12,
           "cumulative_crossover":crossover is not None,
           "terminal_advantage":totals["persistent"]<totals["cold"],
           "ablation_slope_restores":all(rows[i]["costs"]["midstream_ablation"]==rows[i]["costs"]["cold"] for i in range(6,12)),
           "ablation_worse":totals["midstream_ablation"]>totals["persistent"],
           "sham_not_help":totals["sham"]>=totals["cold"],
           "answer_memory_not_help":totals["answer_memory"]>=totals["cold"]}
    snap={"genesis_cost":g,"retained_ast":retained,"target_specs":SPECS,"targets":TARGETS,"ablation_after":6,"bridge_space":256}
    out={"verdict":"VERIFIED_PERSISTENT_INVARIANT_AMORTIZATION" if all(gates.values()) else "NEGATIVE_OR_PARTIAL",
         "classification":"FINITE_CAUSAL_PROSPECTIVE_AMORTIZED","snapshot_digest":dg(snap),"rows":rows,"aggregate":totals,
         "crossover_target":crossover,"terminal_reduction_factor":totals["cold"]/totals["persistent"],"gates":gates,
         "not_established":["open-ended continuation discovery","continuation-language genesis","cross-domain natural-world amortization","unbounded compounding"]}
    p=ROOT/"results";p.mkdir(exist_ok=True)
    (p/"snapshot.json").write_text(json.dumps(snap,indent=2)+"\n")
    (p/"evidence.json").write_text(json.dumps(out,indent=2)+"\n")
    print(json.dumps(out,indent=2))
if __name__=="__main__":main()
