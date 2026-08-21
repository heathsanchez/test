from __future__ import annotations
from dataclasses import dataclass
from itertools import combinations

@dataclass(frozen=True)
class Predicate:
    kind: str
    a: int
    b: int

def primitive_library(n_points):
    # V4 imports exactly one V3 law: observable behavior, not syntax, is the
    # causally necessary carrier family. It does NOT import which distinctions.
    p=[]
    for i in range(n_points):
        for c in range(n_points):
            p.append(Predicate('obs_eq_const',i,c))
    for i in range(n_points):
        for j in range(i+1,n_points):
            p.append(Predicate('obs_eq_obs',i,j))
    return tuple(p)

def value(obs,p):
    if p.kind=='obs_eq_const': return obs[p.a]==p.b
    if p.kind=='obs_eq_obs': return obs[p.a]==obs[p.b]
    raise KeyError(p.kind)

def signature(obs,program):
    return tuple(value(obs,p) for p in program)

def distinct_behaviors(rows):
    return sorted({tuple(o) for _,o in rows})

def conflicts(behaviors,program):
    buckets={}
    for o in behaviors:
        s=signature(o,program)
        buckets.setdefault(s,[]).append(o)
    return sum(len(v)-1 for v in buckets.values()),len(buckets),buckets

def synthesize(rows,tokens,n_points,max_width=8):
    behaviors=distinct_behaviors(rows)
    lib=primitive_library(n_points)
    history=[]; searched=0; winner=None
    for width in range(max_width+1):
        best=None; exact=[]
        for combo in combinations(lib,width):
            searched+=1
            c,n,b=conflicts(behaviors,combo)
            score=(c,n,width,tuple((p.kind,p.a,p.b) for p in combo))
            rec=(score,combo,b)
            if best is None or score<best[0]: best=rec
            if c==0: exact.append(rec)
        history.append({'width':width,'best_score':best[0],
                        'best_program':[(p.kind,p.a,p.b) for p in best[1]],
                        'conflicts':best[0][0],'exact_count':len(exact)})
        if exact:
            # exact candidates all have n = number of behaviors; choose canonical minimum
            exact.sort(key=lambda r:r[0]); winner=exact[0]; break
    if winner is None: raise RuntimeError('no distinction basis found')
    _,prog,buckets=winner
    sigs=sorted(buckets,key=repr); sid={s:i for i,s in enumerate(sigs)}
    behavior={sid[signature(o,prog)]:o for o in behaviors}
    # Derive token transitions from exact observable dynamics supplied in rows.
    word_to_obs={w:tuple(o) for w,o in rows}
    rep={}
    for w,o in sorted(rows,key=lambda x:(len(x[0]),x[0])):
        s=sid[signature(tuple(o),prog)]
        rep.setdefault(s,w)
    trans={}
    for s,w in rep.items():
        for t in tokens:
            w2=w+(t,)
            if w2 in word_to_obs:
                trans[(s,t)]=sid[signature(word_to_obs[w2],prog)]
    start=sid[signature(word_to_obs[()],prog)]
    return {'predicates':[{'kind':p.kind,'a':p.a,'b':p.b} for p in prog],
            'history':history,'searched':searched,'state_count':len(sigs),
            'behaviors':behavior,'representatives':rep,'transitions':trans,
            'start_state':start}

def execute(model,word):
    s=model['start_state']
    for t in word:
        if (s,t) not in model['transitions']: return None
        s=model['transitions'][(s,t)]
    return s
