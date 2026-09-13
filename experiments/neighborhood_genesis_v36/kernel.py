from __future__ import annotations
from itertools import combinations, permutations
from typing import Any

from basis import World

class Kernel:
    @staticmethod
    def authority(world: World) -> dict[str,Any] | None:
        if not world.complete or not world.rows:
            return {"status":"UNKNOWN_AUTHORITY"}
        n=len(world.rows[0].sites)
        if n<1:
            return {"status":"INVALID_EMPTY_BOUNDARY"}
        if any(len(r.sites)!=n or r.consequence is None for r in world.rows):
            return {"status":"UNKNOWN_AUTHORITY"}
        if any(any(int(v) not in (0,1) for v in r.sites) for r in world.rows):
            return {"status":"INVALID_SYMBOL_ALPHABET"}
        observed={tuple(r.sites) for r in world.rows}
        if len(observed)!=(1<<n) or len(observed)!=len(world.rows):
            return {"status":"UNKNOWN_AUTHORITY"}
        return None

    @staticmethod
    def edge_universe(n: int) -> tuple[tuple[int,int],...]:
        return tuple((i,j) for i in range(n) for j in range(i+1,n))

    @classmethod
    def adjacency(cls,n: int,mask: int) -> tuple[tuple[int,...],...]:
        edges=cls.edge_universe(n)
        a=[[] for _ in range(n)]
        for k,(i,j) in enumerate(edges):
            if (int(mask)>>k)&1:
                a[i].append(j); a[j].append(i)
        return tuple(tuple(sorted(x)) for x in a)

    @classmethod
    def local_signature(cls,values: tuple[int,...],mask: int) -> tuple[tuple[int,int,int],...]:
        a=cls.adjacency(len(values),mask)
        rows=[]
        for i,ns in enumerate(a):
            rows.append((int(values[i]),len(ns),sum(int(values[j]) for j in ns)))
        return tuple(sorted(rows))

    @staticmethod
    def canonical_partition(values) -> tuple[int,...]:
        ids={}; out=[]
        for v in values:
            if v not in ids:
                ids[v]=len(ids)
            out.append(ids[v])
        return tuple(out)

    @classmethod
    def induced_partition(cls,world: World,mask: int) -> tuple[int,...]:
        return cls.canonical_partition(
            cls.local_signature(tuple(r.sites),mask)
            for r in world.rows
        )

    @classmethod
    def target_partition(cls,world: World) -> tuple[int,...]:
        return cls.canonical_partition(int(r.consequence) for r in world.rows)

    @classmethod
    def mismatch_witness(cls,world: World,mask: int) -> dict[str,Any] | None:
        sigs=[cls.local_signature(tuple(r.sites),mask) for r in world.rows]
        # Underfit: same topology signature but different verified consequence.
        first={}
        for idx,(s,r) in enumerate(zip(sigs,world.rows)):
            y=int(r.consequence)
            if s in first:
                j=first[s]
                if int(world.rows[j].consequence)!=y:
                    return {
                        "kind":"MERGE_OBSTRUCTION",
                        "row_a":j,
                        "row_b":idx,
                        "signature":s,
                        "consequences":[int(world.rows[j].consequence),y],
                    }
            else:
                first[s]=idx
        # Overfit: same verified consequence but different topology signatures.
        first_y={}
        for idx,(s,r) in enumerate(zip(sigs,world.rows)):
            y=int(r.consequence)
            if y in first_y:
                j=first_y[y]
                if sigs[j]!=s:
                    return {
                        "kind":"EXCESS_DISTINCTION",
                        "row_a":j,
                        "row_b":idx,
                        "consequence":y,
                    }
            else:
                first_y[y]=idx
        return None

    @classmethod
    def permute_mask(cls,n: int,mask: int,p: tuple[int,...]) -> int:
        edges=cls.edge_universe(n)
        index={e:k for k,e in enumerate(edges)}
        out=0
        for k,(i,j) in enumerate(edges):
            if (int(mask)>>k)&1:
                a,b=sorted((int(p[i]),int(p[j])))
                out |= 1<<index[(a,b)]
        return out

    @classmethod
    def canonical_graph(cls,n: int,mask: int) -> int:
        return min(cls.permute_mask(n,mask,p) for p in permutations(range(n)))

    @classmethod
    def edge_count(cls,mask: int) -> int:
        return int(mask).bit_count()

    def synthesize(self,world: World,*,verification_enabled: bool=True,maximum_edges: int | None=None) -> dict[str,Any]:
        auth=self.authority(world)
        if auth:
            return auth
        if not verification_enabled:
            return {"status":"UNKNOWN_NO_VERIFIER","tested_graphs":0}

        n=len(world.rows[0].sites)
        edge_total=n*(n-1)//2
        max_e=n*(n-1)//2 if maximum_edges is None else min(int(maximum_edges),edge_total)
        target=self.target_partition(world)

        tested_by_edge={}
        obstruction_by_edge={}
        exact=[]
        first_exact_edges=None

        for e in range(max_e+1):
            count=0
            first_obstruction=None
            for mask in range(1<<edge_total):
                if self.edge_count(mask)!=e:
                    continue
                count+=1
                part=self.induced_partition(world,mask)
                if part==target:
                    exact.append(mask)
                elif first_obstruction is None:
                    first_obstruction=self.mismatch_witness(world,mask)
            tested_by_edge[str(e)]=count
            if first_obstruction is not None:
                obstruction_by_edge[str(e)]=first_obstruction
            if exact:
                first_exact_edges=e
                break

        if first_exact_edges is None:
            return {
                "status":"CERTIFIED_NEIGHBORHOOD_INADEQUACY",
                "site_count":n,
                "tested_graphs":sum(tested_by_edge.values()),
                "tested_by_edge_count":tested_by_edge,
                "obstruction_by_edge_count":obstruction_by_edge,
                "maximum_edges":max_e,
            }

        canon_classes=sorted({self.canonical_graph(n,m) for m in exact})
        return {
            "status":"VERIFIED",
            "site_count":n,
            "minimum_edge_count":first_exact_edges,
            "frontier_masks":sorted(exact),
            "frontier_size":len(exact),
            "canonical_graph_classes":canon_classes,
            "canonical_class_count":len(canon_classes),
            "tested_graphs":sum(tested_by_edge.values()),
            "tested_by_edge_count":tested_by_edge,
            "obstruction_by_edge_count":obstruction_by_edge,
        }
