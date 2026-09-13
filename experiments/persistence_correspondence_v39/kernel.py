from __future__ import annotations
from itertools import combinations, permutations, product
from typing import Any

from basis import World

Link = tuple[int,int]
Matching = tuple[Link,...]

class Kernel:
    @staticmethod
    def authority(world: World) -> dict[str,Any] | None:
        if not world.complete or not world.rows:
            return {"status":"UNKNOWN_AUTHORITY"}
        n=len(world.rows[0].before)
        if n<1:
            return {"status":"INVALID_EMPTY_FRAME"}
        if any(
            len(r.before)!=n or len(r.after)!=n or r.consequence is None
            for r in world.rows
        ):
            return {"status":"UNKNOWN_AUTHORITY"}
        if any(any(int(v) not in (0,1) for v in r.before+r.after) for r in world.rows):
            return {"status":"INVALID_SYMBOL_ALPHABET"}

        passive=all(r.action_before==-1 and r.response_after==-1 for r in world.rows)
        active=all(
            (r.action_before==-1 and r.response_after==-1)
            or (0<=r.action_before<n and 0<=r.response_after<n)
            for r in world.rows
        )
        if not active:
            return {"status":"INVALID_INTERVENTION_MARKERS"}

        observed={
            (
                tuple(int(v) for v in r.before),
                tuple(int(v) for v in r.after),
                int(r.action_before),
                int(r.response_after),
            )
            for r in world.rows
        }
        expected_states=list(product((0,1),repeat=2*n))
        if passive:
            expected={
                (tuple(x[:n]),tuple(x[n:]),-1,-1)
                for x in expected_states
            }
        else:
            expected=set()
            for x in expected_states:
                b=tuple(x[:n]); a=tuple(x[n:])
                expected.add((b,a,-1,-1))
                for i in range(n):
                    for j in range(n):
                        expected.add((b,a,i,j))
        if observed!=expected or len(observed)!=len(world.rows):
            return {"status":"UNKNOWN_AUTHORITY"}
        return None

    @staticmethod
    def canonical_partition(values) -> tuple[int,...]:
        ids={}; out=[]
        for value in values:
            if value not in ids:
                ids[value]=len(ids)
            out.append(ids[value])
        return tuple(out)

    @classmethod
    def target_partition(cls,world:World)->tuple[int,...]:
        return cls.canonical_partition(int(r.consequence) for r in world.rows)

    @staticmethod
    def matchings(n:int) -> tuple[Matching,...]:
        out=[()]
        for k in range(1,n+1):
            for left in combinations(range(n),k):
                for right in permutations(range(n),k):
                    out.append(tuple(sorted(zip(left,right))))
        return tuple(sorted(out,key=lambda m:(len(m),m)))

    @staticmethod
    def signature(row,matching:Matching):
        used_before={i for i,j in matching}
        used_after={j for i,j in matching}
        paired=tuple(sorted(
            (int(row.before[i]),int(row.after[j]))
            for i,j in matching
        ))
        free_before=tuple(sorted(
            int(row.before[i]) for i in range(len(row.before))
            if i not in used_before
        ))
        free_after=tuple(sorted(
            int(row.after[j]) for j in range(len(row.after))
            if j not in used_after
        ))
        causal=None
        if row.action_before>=0 and row.response_after>=0:
            causal=int((int(row.action_before),int(row.response_after)) in set(matching))
        return (paired,free_before,free_after,causal)

    @classmethod
    def induced_partition(cls,world:World,matching:Matching)->tuple[int,...]:
        return cls.canonical_partition(cls.signature(r,matching) for r in world.rows)

    @classmethod
    def mismatch_witness(cls,world:World,matching:Matching)->dict[str,Any] | None:
        sigs=[cls.signature(r,matching) for r in world.rows]
        first={}
        for i,(sig,row) in enumerate(zip(sigs,world.rows)):
            y=int(row.consequence)
            if sig in first:
                j=first[sig]
                if int(world.rows[j].consequence)!=y:
                    return {
                        "kind":"MERGE_OBSTRUCTION",
                        "row_a":j,
                        "row_b":i,
                        "consequences":[int(world.rows[j].consequence),y],
                    }
            else:
                first[sig]=i
        first_y={}
        for i,(sig,row) in enumerate(zip(sigs,world.rows)):
            y=int(row.consequence)
            if y in first_y:
                j=first_y[y]
                if sigs[j]!=sig:
                    return {
                        "kind":"EXCESS_DISTINCTION",
                        "row_a":j,
                        "row_b":i,
                        "consequence":y,
                    }
            else:
                first_y[y]=i
        return None

    @staticmethod
    def map_matching(
        matching:Matching,
        before_perm:tuple[int,...],
        after_perm:tuple[int,...],
    )->Matching:
        return tuple(sorted(
            (int(before_perm[i]),int(after_perm[j]))
            for i,j in matching
        ))

    @classmethod
    def canonical_matching(cls,n:int,matching:Matching)->Matching:
        return min(
            cls.map_matching(matching,p,q)
            for p in permutations(range(n))
            for q in permutations(range(n))
        )

    def synthesize(
        self,
        world:World,
        *,
        verification_enabled:bool=True,
        maximum_links:int | None=None,
    )->dict[str,Any]:
        auth=self.authority(world)
        if auth:
            return auth
        if not verification_enabled:
            return {"status":"UNKNOWN_NO_VERIFIER","tested_matchings":0}

        n=len(world.rows[0].before)
        limit=n if maximum_links is None else min(int(maximum_links),n)
        target=self.target_partition(world)
        tested_by_links={}
        obstruction_by_links={}
        frontier=[]
        winning=None

        all_matchings=self.matchings(n)
        for k in range(limit+1):
            batch=[m for m in all_matchings if len(m)==k]
            tested_by_links[str(k)]=len(batch)
            first_obstruction=None
            exact=[]
            for matching in batch:
                if self.induced_partition(world,matching)==target:
                    exact.append(matching)
                elif first_obstruction is None:
                    first_obstruction=self.mismatch_witness(world,matching)
            if first_obstruction is not None:
                obstruction_by_links[str(k)]=first_obstruction
            if exact:
                winning=k
                frontier=exact
                break

        if winning is None:
            return {
                "status":"CERTIFIED_CORRESPONDENCE_INADEQUACY",
                "tested_matchings":sum(tested_by_links.values()),
                "tested_by_link_count":tested_by_links,
                "obstruction_by_link_count":obstruction_by_links,
                "maximum_links":limit,
            }

        classes=sorted({self.canonical_matching(n,m) for m in frontier})
        return {
            "status":"VERIFIED",
            "minimum_link_count":winning,
            "frontier":[[list(x) for x in m] for m in frontier],
            "frontier_size":len(frontier),
            "canonical_classes":[[list(x) for x in m] for m in classes],
            "canonical_class_count":len(classes),
            "tested_matchings":sum(tested_by_links.values()),
            "tested_by_link_count":tested_by_links,
            "obstruction_by_link_count":obstruction_by_links,
        }
