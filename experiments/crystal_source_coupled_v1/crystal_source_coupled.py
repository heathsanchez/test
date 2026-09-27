"""Crystal V2: source-coupled Collatz no-exit residual discovery.

Only states strictly before the first bounded OrdinaryExit witness enter the
census. Protected future is only the bounded exit outcome (kind and delay);
raw residues are candidate observables, never labels. A bounded miss is UNKNOWN.
"""
from collections import defaultdict
import json, random

def T(n): return n//2 if n%2==0 else (3*n+1)//2
def zero_tail_depth(n): return max(0,n.bit_length())

def lower_basin(n,h):
    hit={}
    for p in range(1,n):
        x=p
        for r in range(h+1):
            hit.setdefault(x,(p,r)); x=T(x)
    return hit

def actual_trace(n,h):
    xs=[n]
    for _ in range(h): xs.append(T(xs[-1]))
    q=b=0; rows=[]
    for k,y in enumerate(xs):
        rows.append((k,y,q,b,y%2,y%3,y%9,y%12,y%27))
        if k<h and y%2:
            b=3*b+2**k; q+=1
    return rows

def exit_at(n,y,basin):
    if y in (1,2): return ("terminal",)
    if y<n: return ("descent",)
    if y in basin:
        p,r=basin[y]; return ("merge",p,r)
    return None

def protected_future(n,x,h,basin):
    for j in range(h+1):
        e=exit_at(n,x,basin)
        if e is not None: return ("EXIT",j,e[0])
        x=T(x)
    return ("UNKNOWN",)

def candidate(row,name):
    k,y,q,b,p2,m3,m9,m12,m27=row
    return {
      "parity":p2, "mod3":m3, "mod9":m9, "mod12":m12, "mod27":m27,
      "q_parity":q%2, "b_mod3":b%3, "b_mod9":b%9,
      "endpoint_vs_source":None, # filled source-relatively below
    }[name]

FEATURES=["parity","mod3","mod9","mod12","mod27","q_parity","b_mod3","b_mod9"]

def key_for(n,row,features):
    vals=[]
    for f in features:
        vals.append(candidate(row,f))
    # source-relative sign is consequential candidate, but not source identity.
    if "rel" in features:
        vals.append(-1 if row[1]<n else (0 if row[1]==n else 1))
    return tuple(vals)

def build_records(sources,post=48,future=48,reverse=128):
    rec=[]
    for n in sources:
        basin=lower_basin(n,reverse); K=zero_tail_depth(n)
        rows=actual_trace(n,K+post)
        # only actual no-exit states; once exit occurs, persistence makes later
        # states irrelevant to the residual.
        for row in rows[K:]:
            if exit_at(n,row[1],basin) is not None: break
            lab=protected_future(n,row[1],future,basin)
            rec.append((n,row,lab))
    return rec

def impurity(records,features):
    groups=defaultdict(set)
    examples=defaultdict(list)
    for n,row,lab in records:
        k=key_for(n,row,features); groups[k].add(lab); examples[k].append((n,row,lab))
    bad=[k for k,v in groups.items() if len(v)>1]
    return groups,bad,examples

def greedy_crystal(records):
    chosen=["parity","mod3"]; history=[]
    groups,bad,ex=impurity(records,chosen)
    history.append((list(chosen),len(groups),len(bad)))
    while bad:
        best=None
        for f in FEATURES+["rel"]:
            if f in chosen: continue
            g,b,e=impurity(records,chosen+[f])
            score=(len(b),len(g))
            if best is None or score<best[0]: best=(score,f,g,b,e)
        if best is None or best[0][0]>=len(bad): break
        _,f,groups,bad,ex=best; chosen.append(f)
        history.append((list(chosen),len(groups),len(bad)))
    sep=[]
    for k in bad[:10]:
        vals=ex[k]; a=vals[0]
        b=next(z for z in vals[1:] if z[2]!=a[2])
        sep.append({"class":k,"a":{"n":a[0],"row":a[1],"future":a[2]},
                    "b":{"n":b[0],"row":b[1],"future":b[2]}})
    return {"chosen":chosen,"history":history,"classes":len(groups),
            "impure_classes":len(bad),"first_unresolved_separators":sep}

def run(sources):
    records=build_records(sources)
    return {"sources":len(sources),"actual_pre_exit_states":len(records),
            "crystal":greedy_crystal(records)}

if __name__=="__main__":
    rng=random.Random(28092026)
    train=list(range(3,1025))
    prospective=[rng.randrange(1025,8193) for _ in range(512)]
    print(json.dumps({"schema":"COLLATZ_CRYSTAL_SOURCE_COUPLED_V2",
      "epistemic":"DISCOVERY_ONLY_BOUNDED",
      "train":run(train),"prospective":run(prospective),
      "boundary":"UNKNOWN labels are bounded misses; global Collatz UNKNOWN."},indent=2))
