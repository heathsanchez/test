from __future__ import annotations
from itertools import combinations,product
from collections import defaultdict

class DSU:
    def __init__(self,n): self.p=list(range(n)); self.count=n
    def find(self,x):
        while self.p[x]!=x:
            self.p[x]=self.p[self.p[x]]; x=self.p[x]
        return x
    def union(self,a,b):
        a=self.find(a); b=self.find(b)
        if a==b: return False
        self.p[b]=a; self.count-=1; return True
    def copy(self):
        d=DSU(0); d.p=self.p[:]; d.count=self.count; return d

def all_words(tokens,H):
    out=[()]
    for L in range(1,H+1): out.extend(product(tokens,repeat=L))
    return out

def verified_candidates(tokens, semantic, max_side=4):
    # Candidate generator proposes all short equations; external semantic oracle
    # admits only equations whose two sides have identical exact behavior.
    ws=all_words(tokens,max_side)
    return [(a,b) for a,b in combinations(ws,2) if semantic(a)==semantic(b)]

def saturate(tokens,H,rules):
    U=all_words(tokens,H); idx={w:i for i,w in enumerate(U)}
    d=DSU(len(U)); changed=True
    while changed:
        changed=False
        for w in U:
            wi=idx[w]
            for a,b in rules:
                for x,y in ((a,b),(b,a)):
                    lx=len(x)
                    positions=range(len(w)+1) if lx==0 else [i for i in range(len(w)-lx+1) if w[i:i+lx]==x]
                    for i in positions:
                        nw=w[:i]+y+w[i+lx:]
                        if len(nw)<=H and nw in idx:
                            changed |= d.union(wi,idx[nw])
    return U,d

def audit_congruence(U,d,semantic):
    root_sem=defaultdict(set)
    for i,w in enumerate(U): root_sem[d.find(i)].add(semantic(w))
    false_merges=sum(len(v)-1 for v in root_sem.values())
    semantic_classes=len({semantic(w) for w in U})
    congruence_classes=len({d.find(i) for i in range(len(U))})
    exact=(false_merges==0 and congruence_classes==semantic_classes)
    return {'false_merges':false_merges,'semantic_classes':semantic_classes,
            'congruence_classes':congruence_classes,'exact':exact}

def synthesize_theory(tokens,semantic,train_h=7,candidate_h=4,max_rules=8):
    candidates=verified_candidates(tokens,semantic,candidate_h)
    U=all_words(tokens,train_h)
    d=DSU(len(U))
    rules=[]; history=[]
    # Greedy MDL-like theory formation: at each step choose the shortest true
    # equation that gives maximum additional lawful quotient compression.
    for step in range(max_rules):
        best=None
        for c in candidates:
            if c in rules: continue
            dd=d.copy()
            # Existing d already contains previous closure; saturate candidate on
            # a fresh system with all rules to avoid order artifacts.
            _,dd=saturate(tokens,train_h,rules+[c])
            audit=audit_congruence(U,dd,semantic)
            if audit['false_merges']!=0: continue
            gain=d.count-dd.count
            complexity=len(c[0])+len(c[1])
            score=(gain,-complexity,-max(len(c[0]),len(c[1])),tuple(c[0]),tuple(c[1]))
            if best is None or score>best[0]: best=(score,c,dd,audit)
        if best is None or best[0][0]<=0: break
        _,c,d,audit=best
        rules.append(c)
        history.append({'step':step+1,'equation':[list(c[0]),list(c[1])],
                        'gain':best[0][0],'audit':audit})
        if audit['exact']: break
    final=audit_congruence(U,d,semantic)
    return {'rules':rules,'history':history,'candidate_count':len(candidates),
            'train_audit':final}
