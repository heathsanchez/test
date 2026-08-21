from __future__ import annotations
from itertools import product

# This module is deliberately separate from the blind constructor.
# It is allowed to ask post-hoc mathematical questions about the object emitted
# by the constructor. Its vocabulary is not imported by constructor.py.

def compose_map(f,g):
    return tuple(g[f[i]] for i in range(len(f)))

def law_audit(model):
    states=range(model["state_count"])
    beh=model["behaviors"]
    by_behavior={tuple(v):k for k,v in beh.items()}
    table=[[None]*model["state_count"] for _ in states]
    for a in states:
        for b in states:
            out=compose_map(tuple(beh[a]),tuple(beh[b]))
            table[a][b]=by_behavior.get(out)

    closed=all(table[a][b] is not None for a in states for b in states)
    identities=[]
    if closed:
        identities=[e for e in states if all(table[e][x]==x and table[x][e]==x for x in states)]
    associative=False
    if closed:
        associative=all(
            table[table[a][b]][c]==table[a][table[b][c]]
            for a,b,c in product(states,repeat=3)
        )
    inv={}
    if len(identities)==1 and closed:
        e=identities[0]
        inv={a:[b for b in states if table[a][b]==e and table[b][a]==e] for a in states}
    all_inv=bool(inv) and all(inv[a] for a in states)
    commutative=closed and all(table[a][b]==table[b][a] for a in states for b in states)
    return {
        "closed":closed,
        "identity_count":len(identities),
        "identity":identities[0] if len(identities)==1 else None,
        "associative":associative,
        "all_elements_invertible":all_inv,
        "commutative":commutative,
        "group_axiom_bundle":closed and len(identities)==1 and associative and all_inv,
        "table":table,
    }

def element_orders(audit):
    T=audit["table"]; e=audit["identity"]
    if e is None: return {}
    out={}
    for a in range(len(T)):
        x=e
        found=None
        for k in range(1,len(T)*3+3):
            x=T[x][a]
            if x==e:
                found=k; break
        out[a]=found
    return out
