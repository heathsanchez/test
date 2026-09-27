#!/usr/bin/env python3
"""Stateful Crystal owner-frontier campaign for the fixed-origin Collatz residual.

One process performs repeated discovery cycles. It preserves exact residual
sources between cycles and admits a new coordinate only when it separates the
current hardest consequences. This is a theorem-discovery/falsification audit,
not a proof of Collatz.
"""
import json, math

LIMIT=1<<22
CAP=2048
CYCLES=16

def T(x):
    return (3*x+1)//2 if x&1 else x//2

def owner1(x):
    return (x-1)//4 if x%8==5 else None

def classify(n, features):
    x=n; above=False; returns=0; peak=n; lowrun=0; maxlow=0
    trace=[]
    for j in range(CAP+1):
        if x<n:
            return ("DESCENT",j,x,returns,peak,maxlow,trace)
        if x%8==5 and x<=4*n:
            return ("SPLICE",j,x,returns,peak,maxlow,trace)
        if above and x<=4*n:
            returns+=1; above=False
        if x>4*n: above=True
        peak=max(peak,x)
        if x&1:
            z=3*x+1; s=(z&-z).bit_length()-1
            if s<=2: lowrun+=1; maxlow=max(maxlow,lowrun)
            else: lowrun=0
        if len(trace)<64:
            trace.append((j,x, x%8, int(x<=4*n), returns))
        x=T(x)
    return ("UNRESOLVED",CAP,x,returns,peak,maxlow,trace)

# Start with the hardest record setters plus a deterministic sparse cover.
seeds={63728127,13421671,8088063,13353631,3041391,27,31}
stride=2053
for n in range(3,LIMIT,2*stride):
    seeds.add(n|1)
sources=sorted(n for n in seeds if n>1 and n%2)

feature_order=["returns","peak_ratio_bin","max_low_run","decision_step_bin","source_mod_8",
               "source_mod_16","source_mod_3","source_mod_5","source_mod_7"]
active=[]
cycles=[]
residual=sources
prev_signature=None

for c in range(CYCLES):
    rows=[]
    for n in residual:
        q=classify(n,active)
        typ,j,x,ret,peak,mlow,tr=q
        row={"n":n,"outcome":typ,"j":j,"x":x,"returns":ret,
             "peak_ratio_bin":(peak//n).bit_length(),
             "max_low_run":mlow,"decision_step_bin":j.bit_length(),
             "source_mod_8":n%8,"source_mod_16":n%16,
             "source_mod_3":n%3,"source_mod_5":n%5,"source_mod_7":n%7}
        rows.append(row)
    unresolved=[r for r in rows if r["outcome"]=="UNRESOLVED"]
    # Consequence classes under current representation; mixed classes earn separator.
    groups={}
    for r in rows:
        key=tuple(r[k] for k in active)
        groups.setdefault(key,set()).add(r["outcome"])
    mixed=[k for k,v in groups.items() if len(v)>1]
    earned=None
    if mixed and c<len(feature_order):
        # choose coordinate that maximally splits mixed consequence classes
        best=None
        for f in feature_order:
            if f in active: continue
            score=len({(tuple(r[k] for k in active),r[f],r["outcome"]) for r in rows})
            cand=(score,f)
            if best is None or cand>best: best=cand
        if best: earned=best[1]; active.append(earned)
    # Preserve only hard tail for next cycle: top 1/3 by decision depth plus unresolved.
    ranked=sorted(rows,key=lambda r:(r["outcome"]=="UNRESOLVED",r["j"],r["returns"],r["max_low_run"]),reverse=True)
    keep=max(16,len(ranked)//3)
    residual=sorted({r["n"] for r in ranked[:keep]} | {r["n"] for r in unresolved})
    sig=(tuple(active),tuple(residual[:64]),len(unresolved),max((r["j"] for r in rows),default=0))
    cycles.append({"cycle":c+1,"input_sources":len(rows),"active_features":list(active),
                   "mixed_classes":len(mixed),"earned_separator":earned,
                   "unresolved":len(unresolved),"max_decision_steps":sig[3],
                   "max_returns":max((r["returns"] for r in rows),default=0),
                   "max_low_run":max((r["max_low_run"] for r in rows),default=0),
                   "next_residual_sources":residual[:32]})
    if not unresolved and not mixed:
        break
    if sig==prev_signature:
        break
    prev_signature=sig

print(json.dumps({
 "schema":"COLLATZ_CRYSTAL_OWNER_FRONTIER_CYCLES_V1",
 "boundary":{"limit":LIMIT,"cap":CAP,"initial_sources":len(sources),"cycles_cap":CYCLES},
 "cycles":cycles,
 "final_active_features":active,
 "final_residual_sources":residual[:128],
 "interpretation":"stateful consequence-separator discovery on fixed-origin descent-or-quarter-splice residual",
 "universal_status":"UNKNOWN",
 "global_collatz":"UNKNOWN"
},indent=2))
