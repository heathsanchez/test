from __future__ import annotations
from collections import defaultdict
from itertools import product
from math import ceil, log2
from typing import Any

from basis import Machine, View, World

class Kernel:
    def __init__(self, max_motif_len: int = 6):
        self.max_motif_len=max_motif_len

    @staticmethod
    def _orbit(boundary: tuple[int,...]) -> set[tuple[int,...]]:
        n=len(boundary)
        out=set()
        for r in range(n):
            x=boundary[r:]+boundary[:r]
            out.add(x)
            out.add(tuple(reversed(x)))
        return out

    def authority(self, world: World) -> dict[str,Any] | None:
        if not world.complete or not world.rows:
            return {"status":"UNKNOWN_AUTHORITY"}
        n=len(world.rows[0].boundary)
        if any(len(r.boundary)!=n or r.consequence is None for r in world.rows):
            return {"status":"UNKNOWN_AUTHORITY"}
        if any(any(int(b) not in (0,1) for b in r.boundary) for r in world.rows):
            return {"status":"INVALID_SYMBOL_ALPHABET"}
        by_boundary={}
        for r in world.rows:
            b=tuple(int(x) for x in r.boundary)
            y=int(r.consequence)
            if b in by_boundary and by_boundary[b]!=y:
                return {"status":"INCONSISTENT_AUTHORITY"}
            by_boundary[b]=y
        # No externally privileged origin or direction: every encountered raw
        # boundary must include its full rotation/reflection presentation orbit
        # with identical authoritative consequence.
        for b,y in list(by_boundary.items()):
            for z in self._orbit(b):
                if z not in by_boundary or by_boundary[z]!=y:
                    return {"status":"UNKNOWN_DIHEDRAL_AUTHORITY"}
        return None

    @staticmethod
    def _gamma_len(n:int)->int:
        if n<1: raise ValueError(n)
        return 2*int(log2(n))+1

    @staticmethod
    def _parse(boundary: tuple[int,...], view: View) -> tuple[int,...] | None:
        n=len(boundary); p=tuple(view.motif); m=len(p); w=int(view.width)
        if m>=n or (n-m)%w:
            return None
        matches=[]
        for i in range(n):
            for d in (1,-1):
                if tuple(boundary[(i+d*j)%n] for j in range(m))==p:
                    matches.append((i,d))
        if len(matches)!=1:
            return None
        i,d=matches[0]
        rem=n-m
        raw=[int(boundary[(i+d*(m+j))%n]) for j in range(rem)]
        seq=[]
        for k in range(0,rem,w):
            v=0
            for bit in raw[k:k+w]:
                v=(v<<1)|int(bit)
            seq.append(v)
        return tuple(seq)

    @staticmethod
    def _build_machine(pairs: list[tuple[tuple[int,...],int]]) -> Machine | None:
        mapping={}
        for seq,y in pairs:
            if seq in mapping and mapping[seq]!=y:
                return None
            mapping[seq]=int(y)
        if not mapping: return None
        seqs=list(mapping)
        L=len(seqs[0])
        if any(len(s)!=L for s in seqs): return None
        states=[]
        cache={}
        def terminal(y:int)->int:
            sig=("OUT",int(y))
            if sig not in cache:
                cache[sig]=len(states); states.append(sig)
            return cache[sig]
        def rec(items,depth):
            ys={mapping[s] for s in items}
            if len(ys)==1:
                return terminal(next(iter(ys)))
            if depth==L:
                return None
            groups=defaultdict(list)
            for s in items:
                groups[s[depth]].append(s)
            edges=[]
            for symbol,ss in sorted(groups.items()):
                child=rec(ss,depth+1)
                if child is None: return None
                edges.append((int(symbol),int(child)))
            sig=("STEP",tuple(edges))
            if sig not in cache:
                cache[sig]=len(states); states.append(sig)
            return cache[sig]
        root=rec(seqs,0)
        if root is None: return None
        return Machine(int(root),tuple(states))

    @staticmethod
    def _machine_stats(machine: Machine) -> dict[str,int]:
        transitions=sum(len(s[1]) for s in machine.states if s[0]=="STEP")
        terminals=sum(1 for s in machine.states if s[0]=="OUT")
        steps=sum(1 for s in machine.states if s[0]=="STEP")
        return {"state_count":len(machine.states),"transition_count":transitions,
                "terminal_count":terminals,"step_count":steps}

    def _description_bits(self, view: View, machine: Machine, label_count:int) -> int:
        m=len(view.motif); w=int(view.width)
        stats=self._machine_stats(machine)
        S=stats["state_count"]
        ptr=max(1,ceil(log2(max(2,S))))
        lab=max(1,ceil(log2(max(2,label_count))))
        bits=self._gamma_len(m)+m+self._gamma_len(w)+self._gamma_len(S)+ptr
        for state in machine.states:
            if state[0]=="OUT":
                bits += 1+lab
            else:
                edges=state[1]
                bits += 1+self._gamma_len(len(edges))
                bits += len(edges)*(w+ptr)
        return int(bits)

    @staticmethod
    def _replay(machine: Machine, seq: tuple[int,...]) -> int | None:
        state=int(machine.root)
        for symbol in seq:
            row=machine.states[state]
            if row[0]=="OUT":
                continue
            edges=dict(row[1])
            if int(symbol) not in edges:
                return None
            state=int(edges[int(symbol)])
        row=machine.states[state]
        if row[0]!="OUT":
            return None
        return int(row[1])

    def solve(self, world: World, *, verification_enabled: bool=True) -> dict[str,Any]:
        auth=self.authority(world)
        if auth: return auth
        if not verification_enabled:
            return {"status":"UNKNOWN_NO_VERIFIER","candidate_views_tested":0}
        labels={int(r.consequence) for r in world.rows}
        if len(labels)==1:
            y=next(iter(labels))
            machine=Machine(0,(("OUT",int(y)),))
            return {
                "status":"VERIFIED","description_bits":1,
                "frontier_size":1,"selected_view":None,
                "candidate_views_tested":0,"valid_views":0,
                "machine":machine.data(),"exact_replay":True,
                "_frontier":[(None,machine)],"_machine":machine,
            }
        n=len(world.rows[0].boundary)
        tested=0; valid=0; scored=[]
        for m in range(2,min(self.max_motif_len,n-1)+1):
            for motif in product((0,1), repeat=m):
                rem=n-m
                for w in range(1,rem+1):
                    if rem%w: continue
                    tested+=1
                    view=View(tuple(int(x) for x in motif),int(w))
                    pairs=[]
                    ok=True
                    for r in world.rows:
                        seq=self._parse(tuple(r.boundary),view)
                        if seq is None:
                            ok=False; break
                        pairs.append((seq,int(r.consequence)))
                    if not ok: continue
                    machine=self._build_machine(pairs)
                    if machine is None: continue
                    if any(self._replay(machine,seq)!=y for seq,y in pairs):
                        continue
                    valid+=1
                    bits=self._description_bits(view,machine,len(labels))
                    stats=self._machine_stats(machine)
                    score=(bits,stats["state_count"],stats["transition_count"],m,w)
                    scored.append((score,view,machine,stats))
        if not scored:
            return {"status":"CERTIFIED_VIEW_LANGUAGE_INADEQUACY",
                    "candidate_views_tested":tested,"valid_views":valid}
        scored.sort(key=lambda x:(x[0],x[1].motif))
        best_score=scored[0][0]
        frontier=[x for x in scored if x[0]==best_score]
        score,view,machine,stats=frontier[0]
        parsed=[self._parse(tuple(r.boundary),view) for r in world.rows]
        exact=all(seq is not None and self._replay(machine,seq)==int(r.consequence)
                  for seq,r in zip(parsed,world.rows))
        return {
            "status":"VERIFIED" if exact else "REPLAY_FAILED",
            "description_bits":int(score[0]),
            "frontier_size":len(frontier),
            "selected_view":{"motif":list(view.motif),"width":int(view.width)},
            "frontier_views":[{"motif":list(v.motif),"width":int(v.width)}
                              for _,v,_,_ in frontier],
            "candidate_views_tested":tested,"valid_views":valid,
            **stats,"machine":machine.data(),"exact_replay":exact,
            "_frontier":[(v,m) for _,v,m,_ in frontier],
            "_machine":machine,
        }
