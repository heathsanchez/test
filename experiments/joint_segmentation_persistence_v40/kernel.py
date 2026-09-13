from __future__ import annotations
from itertools import combinations, permutations, product
from typing import Any

from basis import World

Block = tuple[int,...]
Segmentation = tuple[Block,...]
Matching = tuple[tuple[int,int],...]

class Kernel:
    @staticmethod
    def authority(world: World) -> dict[str,Any] | None:
        if not world.complete or not world.rows:
            return {"status":"UNKNOWN_AUTHORITY"}
        n=len(world.rows[0].before)
        if n<1:
            return {"status":"INVALID_EMPTY_BOUNDARY"}
        if any(
            len(r.before)!=n or len(r.after)!=n or r.consequence is None
            for r in world.rows
        ):
            return {"status":"UNKNOWN_AUTHORITY"}
        if any(any(int(v) not in (0,1) for v in r.before+r.after) for r in world.rows):
            return {"status":"INVALID_SYMBOL_ALPHABET"}

        has_active=any(r.action_before>=0 or r.response_after>=0 for r in world.rows)
        state_rows={}
        for r in world.rows:
            key=(tuple(int(v) for v in r.before),tuple(int(v) for v in r.after))
            state_rows.setdefault(key,[]).append(r)

        expected_states=set(product((0,1),repeat=2*n))
        observed_states={
            tuple(b)+tuple(a)
            for b,a in state_rows
        }
        if observed_states!=expected_states:
            return {"status":"UNKNOWN_AUTHORITY"}

        for rows in state_rows.values():
            passive=[
                r for r in rows
                if r.action_before==-1 and r.response_after==-1
            ]
            if len(passive)!=1:
                return {"status":"UNKNOWN_AUTHORITY"}
            active=[
                r for r in rows
                if r.action_before>=0 or r.response_after>=0
            ]
            if not has_active:
                if active:
                    return {"status":"INVALID_INTERVENTION_MARKERS"}
                continue
            if len(active)!=n:
                return {"status":"UNKNOWN_AUTHORITY"}
            seen=set()
            for r in active:
                if not (0<=int(r.action_before)<n and 0<=int(r.response_after)<n):
                    return {"status":"INVALID_INTERVENTION_MARKERS"}
                if int(r.action_before) in seen:
                    return {"status":"UNKNOWN_AUTHORITY"}
                seen.add(int(r.action_before))
            if seen!=set(range(n)):
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
    def segmentations(n:int) -> tuple[Segmentation,...]:
        out=[]
        for mask in range(1<<(n-1)):
            blocks=[]
            start=0
            for i in range(n-1):
                if (mask>>i)&1:
                    blocks.append(tuple(range(start,i+1)))
                    start=i+1
            blocks.append(tuple(range(start,n)))
            out.append(tuple(blocks))
        return tuple(sorted(out,key=lambda s:(len(s),s)))

    @staticmethod
    def matchings(m:int,n:int) -> tuple[Matching,...]:
        out=[()]
        for k in range(1,min(m,n)+1):
            for left in combinations(range(m),k):
                for right in permutations(range(n),k):
                    out.append(tuple(sorted(zip(left,right))))
        return tuple(sorted(out,key=lambda x:(len(x),x)))

    @staticmethod
    def segment_state(values:tuple[int,...],block:Block)->tuple[int,...]:
        return tuple(int(values[i]) for i in block)

    @classmethod
    def signature(
        cls,row,
        before_segments:Segmentation,
        after_segments:Segmentation,
        matching:Matching,
    ):
        bs=tuple(cls.segment_state(tuple(row.before),b) for b in before_segments)
        aa=tuple(cls.segment_state(tuple(row.after),b) for b in after_segments)
        used_b={i for i,j in matching}
        used_a={j for i,j in matching}
        paired=tuple(sorted((bs[i],aa[j]) for i,j in matching))
        free_b=tuple(sorted(bs[i] for i in range(len(bs)) if i not in used_b))
        free_a=tuple(sorted(aa[j] for j in range(len(aa)) if j not in used_a))
        return (paired,free_b,free_a)

    @classmethod
    def induced_partition(
        cls,world:World,
        kind:str,
        before_segments:Segmentation|None,
        after_segments:Segmentation|None,
        matching:Matching,
    )->tuple[int,...]:
        if kind=="VOID":
            sigs=[() for _ in world.rows]
        elif kind=="BAGS":
            sigs=[
                (
                    tuple(sorted(int(v) for v in r.before)),
                    tuple(sorted(int(v) for v in r.after)),
                )
                for r in world.rows
            ]
        else:
            sigs=[
                cls.signature(r,before_segments or (),after_segments or (),matching)
                for r in world.rows
            ]
        return cls.canonical_partition(sigs)

    @classmethod
    def intervention_consistent(
        cls,world:World,
        before_segments:Segmentation,
        after_segments:Segmentation,
        matching:Matching,
    )->tuple[bool,dict[str,Any] | None]:
        links=set(matching)
        for idx,row in enumerate(world.rows):
            if row.action_before<0 and row.response_after<0:
                continue
            bi=next(
                i for i,b in enumerate(before_segments)
                if int(row.action_before) in b
            )
            aj=next(
                j for j,b in enumerate(after_segments)
                if int(row.response_after) in b
            )
            if (bi,aj) not in links:
                return False,{
                    "kind":"INTERVENTION_OBSTRUCTION",
                    "row":idx,
                    "before_segment":bi,
                    "after_segment":aj,
                }
        return True,None

    @classmethod
    def mismatch_witness(
        cls,world:World,
        kind:str,
        before_segments:Segmentation|None,
        after_segments:Segmentation|None,
        matching:Matching,
    )->dict[str,Any] | None:
        if kind=="VOID":
            sigs=[() for _ in world.rows]
        elif kind=="BAGS":
            sigs=[
                (
                    tuple(sorted(int(v) for v in r.before)),
                    tuple(sorted(int(v) for v in r.after)),
                )
                for r in world.rows
            ]
        else:
            sigs=[
                cls.signature(r,before_segments or (),after_segments or (),matching)
                for r in world.rows
            ]

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
    def metric(
        kind:str,
        before_segments:Segmentation|None,
        after_segments:Segmentation|None,
        matching:Matching,
    )->tuple[int,int,int]:
        if kind=="VOID":
            return (0,0,0)
        if kind=="BAGS":
            return (0,1,0)
        cuts=(len(before_segments or ())-1)+(len(after_segments or ())-1)
        return (1,cuts,len(matching))

    @classmethod
    def candidate_rows(cls,n:int):
        yield ("VOID",None,None,())
        yield ("BAGS",None,None,())
        for sb in cls.segmentations(n):
            for sa in cls.segmentations(n):
                for m in cls.matchings(len(sb),len(sa)):
                    yield ("SEGMENTS",sb,sa,m)

    def synthesize(
        self,
        world:World,
        *,
        verification_enabled:bool=True,
        maximum_cuts:int | None=None,
        maximum_links:int | None=None,
    )->dict[str,Any]:
        auth=self.authority(world)
        if auth:
            return auth
        if not verification_enabled:
            return {"status":"UNKNOWN_NO_VERIFIER","tested_candidates":0}

        n=len(world.rows[0].before)
        target=self.target_partition(world)
        candidates=[]
        for candidate in self.candidate_rows(n):
            kind,sb,sa,m=candidate
            metric=self.metric(*candidate)
            if kind=="SEGMENTS":
                if maximum_cuts is not None and metric[1]>int(maximum_cuts):
                    continue
                if maximum_links is not None and metric[2]>int(maximum_links):
                    continue
            candidates.append(candidate)
        candidates.sort(key=lambda c:(self.metric(*c),repr(c)))

        tested_by_metric={}
        obstruction_by_metric={}
        frontier=[]
        winning_metric=None

        i=0
        while i<len(candidates):
            metric=self.metric(*candidates[i])
            batch=[]
            while i<len(candidates) and self.metric(*candidates[i])==metric:
                batch.append(candidates[i]); i+=1
            key=":".join(str(x) for x in metric)
            tested_by_metric[key]=len(batch)
            first_obstruction=None
            exact=[]
            for candidate in batch:
                kind,sb,sa,m=candidate
                if self.induced_partition(world,*candidate)!=target:
                    if first_obstruction is None:
                        first_obstruction=self.mismatch_witness(world,*candidate)
                    continue
                if kind=="SEGMENTS":
                    ok,witness=self.intervention_consistent(
                        world,sb or (),sa or (),m
                    )
                    if not ok:
                        if first_obstruction is None:
                            first_obstruction=witness
                        continue
                exact.append(candidate)
            if first_obstruction is not None:
                obstruction_by_metric[key]=first_obstruction
            if exact:
                winning_metric=metric
                frontier=exact
                break

        if winning_metric is None:
            return {
                "status":"CERTIFIED_SEGMENTATION_PERSISTENCE_INADEQUACY",
                "tested_candidates":sum(tested_by_metric.values()),
                "tested_by_metric":tested_by_metric,
                "obstruction_by_metric":obstruction_by_metric,
                "maximum_cuts":maximum_cuts,
                "maximum_links":maximum_links,
            }

        rendered=[]
        for kind,sb,sa,m in frontier:
            if kind in ("VOID","BAGS"):
                rendered.append({"kind":kind})
            else:
                rendered.append({
                    "kind":"SEGMENTS",
                    "before_segments":[list(b) for b in sb or ()],
                    "after_segments":[list(b) for b in sa or ()],
                    "matching":[list(x) for x in m],
                })

        return {
            "status":"VERIFIED",
            "minimum_metric":list(winning_metric),
            "frontier":rendered,
            "frontier_size":len(rendered),
            "tested_candidates":sum(tested_by_metric.values()),
            "tested_by_metric":tested_by_metric,
            "obstruction_by_metric":obstruction_by_metric,
        }
