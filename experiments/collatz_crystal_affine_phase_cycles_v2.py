#!/usr/bin/env python3
"""Crystal V2: ablate arbitrary source residues; test exact low-word affine phase.

For each fixed odd source, follow T until first direct descent or source-relative
quarter splice. Track the current consecutive accelerated-odd low-valuation word
s_i in {1,2}. Its exact affine state is 2^S U_w(x0)=3^r x0+C.
We expose only structural coordinates from this word/source compatibility.
"""
import json
LIMIT=1<<24
CAP=4096

def T(x): return (3*x+1)//2 if x&1 else x//2
def v2(z):
    return (z&-z).bit_length()-1

def run(n):
    x=n; low=[]; C=0; S=0; r=0
    best=(0,0,0,0,0) # length,S,C mod 2^min(S,20), source phase, endpoint phase
    peak=n; returns=0; above=False
    for j in range(CAP+1):
        if x<n: return ("DESCENT",j,x,best,returns,peak)
        if x%8==5 and x<=4*n: return ("SPLICE",j,x,best,returns,peak)
        if above and x<=4*n: returns+=1; above=False
        if x>4*n: above=True
        peak=max(peak,x)
        if x&1:
            z=3*x+1; s=v2(z)
            if s in (1,2):
                # compose U_s(y)=(3y+1)/2^s after current low word
                C=3*C+(1<<S); S+=s; r+=1; low.append(s)
                m=1<<min(S,20)
                # exact source phase in realized dyadic cylinder, plus affine bias phase
                phase=n % m
                best=max(best,(r,S,C % m,phase,x % m),key=lambda q:q[0])
            else:
                low=[]; C=S=r=0
        x=T(x)
    return ("UNRESOLVED",CAP,x,best,returns,peak)

# prospective deterministic cover + historical hard sources
hard={27,31,3041391,8088063,13353631,13421671,63728127}
sources=set(hard)
for n in range(3,LIMIT,8191*2): sources.add(n|1)
sources=sorted(sources)

rows=[]
for n in sources:
    typ,j,x,b,ret,peak=run(n)
    r,S,C,phase,ephase=b
    rows.append({"n":n,"outcome":typ,"j":j,"r":r,"S":S,"C":C,
      "source_phase":phase,"endpoint_phase":ephase,"returns":ret,
      "peak_bin":(peak//n).bit_length()})

# Crystal cycles: only structural candidates, no arbitrary odd moduli.
features=["r","S","C","source_phase","endpoint_phase","returns","peak_bin"]
active=[]; cycles=[]
for cyc in range(len(features)+1):
    groups={}
    for q in rows:
        key=tuple(q[f] for f in active)
        groups.setdefault(key,set()).add(q["outcome"])
    mixed=[k for k,v in groups.items() if len(v)>1]
    if not mixed:
        cycles.append({"cycle":cyc+1,"active":active.copy(),"mixed":0,"earned":None}); break
    best=None
    for f in features:
        if f in active: continue
        # count homogeneous refinements; prefer fewer coordinates on tie
        gg={}
        for q in rows:
            key=(tuple(q[a] for a in active),q[f])
            gg.setdefault(key,set()).add(q["outcome"])
        score=(sum(len(v)==1 for v in gg.values()),len(gg),f)
        if best is None or score>best[0]: best=(score,f)
    if best is None: break
    active.append(best[1])
    cycles.append({"cycle":cyc+1,"active":active.copy(),"mixed_before":len(mixed),"earned":best[1]})

unresolved=[q for q in rows if q["outcome"]=="UNRESOLVED"]
final={}
for q in rows:
    key=tuple(q[f] for f in active); final.setdefault(key,set()).add(q["outcome"])
mixed_final=sum(len(v)>1 for v in final.values())
print(json.dumps({
 "schema":"COLLATZ_CRYSTAL_AFFINE_PHASE_CYCLES_V2",
 "boundary":{"limit":LIMIT,"cap":CAP,"sources":len(sources)},
 "ablation":["source_mod_5","source_mod_7","all arbitrary source odd-modulus residues"],
 "structural_features":features,
 "cycles":cycles,
 "final_active":active,
 "mixed_final":mixed_final,
 "unresolved":len(unresolved),
 "max_decision_steps":max(q["j"] for q in rows),
 "max_returns":max(q["returns"] for q in rows),
 "hard_rows":[q for q in rows if q["n"] in hard],
 "candidate_status":"CANDIDATE" if mixed_final==0 and not unresolved else "INSUFFICIENT",
 "universal_status":"UNKNOWN","global_collatz":"UNKNOWN"
},indent=2))
