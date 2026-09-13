from __future__ import annotations
from functools import lru_cache
from itertools import combinations, permutations, product
from math import prod
from typing import Any

from basis import World

Word = tuple[int,...]
Unit = tuple[Word,...]
Partition = tuple[tuple[int,...],...]
Structure = tuple[Unit,...]

class Kernel:
    def __init__(self,max_arity: int=3,max_units: int=2,max_objects: int | None=None):
        self.max_arity=int(max_arity)
        self.max_units=int(max_units)
        self.max_objects=max_objects

    @staticmethod
    def authority(world: World) -> dict[str,Any] | None:
        if not world.complete or not world.rows:
            return {"status":"UNKNOWN_AUTHORITY"}
        n=len(world.rows[0].marks)
        if n<1:
            return {"status":"INVALID_EMPTY_BOUNDARY"}
        if any(len(r.marks)!=n or r.consequence is None for r in world.rows):
            return {"status":"UNKNOWN_AUTHORITY"}
        alphabets=[]
        for i in range(n):
            vals=tuple(sorted({int(r.marks[i]) for r in world.rows}))
            if not vals:
                return {"status":"UNKNOWN_AUTHORITY"}
            alphabets.append(vals)
        expected=prod(len(a) for a in alphabets)
        observed={tuple(int(v) for v in r.marks) for r in world.rows}
        if len(observed)!=len(world.rows) or len(observed)!=expected:
            return {"status":"UNKNOWN_AUTHORITY"}
        if observed != set(product(*alphabets)):
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
    def set_partitions(cls,n: int) -> tuple[Partition,...]:
        out=set()
        def rec(i:int,labels:list[int],max_label:int):
            if i==n:
                out.add(tuple(
                    tuple(j for j,x in enumerate(labels) if x==lab)
                    for lab in range(max_label+1)
                ))
                return
            if i==0:
                rec(1,[0],0)
                return
            for lab in range(max_label+2):
                if lab<=max_label+1:
                    rec(i+1,labels+[lab],max(max_label,lab))
        rec(0,[],-1)
        return tuple(sorted(out,key=lambda p:(len(p),p)))

    @staticmethod
    def compose(p: tuple[int,...],q: tuple[int,...]) -> tuple[int,...]:
        return tuple(p[q[i]] for i in range(len(p)))

    @classmethod
    @lru_cache(maxsize=None)
    def coordinate_subgroups(cls,k: int) -> tuple[tuple[tuple[int,...],...],...]:
        perms=tuple(permutations(range(k)))
        identity=tuple(range(k))
        groups=[]
        for mask in range(1<<len(perms)):
            H=tuple(perms[i] for i in range(len(perms)) if (mask>>i)&1)
            if identity not in H:
                continue
            hs=set(H)
            if all(cls.compose(a,b) in hs for a in H for b in H):
                groups.append(tuple(sorted(H)))
        return tuple(sorted(set(groups),key=lambda H:(len(H),H)))

    @staticmethod
    def apply_coordinate_permutation(word: Word,p: tuple[int,...]) -> Word:
        return tuple(word[p[i]] for i in range(len(p)))

    @classmethod
    def incidence_units(cls,n_objects:int,max_arity:int) -> tuple[Unit,...]:
        units=set()
        for k in range(1,min(int(max_arity),n_objects)+1):
            for H in cls.coordinate_subgroups(k):
                for word in permutations(range(n_objects),k):
                    orbit=tuple(sorted({
                        cls.apply_coordinate_permutation(tuple(word),p)
                        for p in H
                    }))
                    units.add(orbit)
        return tuple(sorted(units,key=lambda u:(len(u[0]),len(u),u)))

    @staticmethod
    def unit_arity(unit:Unit)->int:
        return len(unit[0])

    @classmethod
    def incidence_metric(cls,structure:Structure)->tuple[int,int,int]:
        return (
            len(structure),
            sum(cls.unit_arity(u) for u in structure),
            sum(len(u) for u in structure),
        )

    @classmethod
    def candidate_incidence(cls,n_objects:int,max_arity:int,max_units:int) -> tuple[Structure,...]:
        units=cls.incidence_units(n_objects,max_arity)
        out=[()]
        for count in range(1,int(max_units)+1):
            out.extend(tuple(x) for x in combinations(units,count))
        return tuple(sorted(out,key=lambda s:(cls.incidence_metric(s),s)))

    @staticmethod
    def object_states(values:tuple[int,...],partition:Partition) -> tuple[tuple[int,...],...]:
        return tuple(
            tuple(sorted(int(values[i]) for i in block))
            for block in partition
        )

    @classmethod
    def object_signature(cls,values:tuple[int,...],partition:Partition,structure:Structure):
        states=cls.object_states(values,partition)
        inventory=tuple(sorted(states))
        incidence=[]
        for unit in structure:
            words=[]
            for word in unit:
                words.append(tuple(states[i] for i in word))
            incidence.append(tuple(sorted(words)))
        return (inventory,tuple(sorted(incidence)))

    @classmethod
    def induced_partition(cls,world:World,kind:str,partition:Partition|None,structure:Structure) -> tuple[int,...]:
        if kind=="VOID":
            sigs=[() for _ in world.rows]
        elif kind=="BAG":
            sigs=[tuple(sorted(int(v) for v in r.marks)) for r in world.rows]
        else:
            sigs=[
                cls.object_signature(tuple(int(v) for v in r.marks),partition or (),structure)
                for r in world.rows
            ]
        return cls.canonical_partition(sigs)

    @classmethod
    def target_partition(cls,world:World)->tuple[int,...]:
        return cls.canonical_partition(int(r.consequence) for r in world.rows)

    @classmethod
    def mismatch_witness(cls,world:World,kind:str,partition:Partition|None,structure:Structure) -> dict[str,Any] | None:
        if kind=="VOID":
            sigs=[() for _ in world.rows]
        elif kind=="BAG":
            sigs=[tuple(sorted(int(v) for v in r.marks)) for r in world.rows]
        else:
            sigs=[
                cls.object_signature(tuple(int(v) for v in r.marks),partition or (),structure)
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

    @classmethod
    def map_partition_structure(
        cls,partition:Partition,structure:Structure,p:tuple[int,...]
    ) -> tuple[Partition,Structure]:
        mapped_blocks=[tuple(sorted(int(p[i]) for i in block)) for block in partition]
        order=sorted(range(len(mapped_blocks)),key=lambda i:mapped_blocks[i])
        new_partition=tuple(mapped_blocks[i] for i in order)
        old_to_new={old:new for new,old in enumerate(order)}
        mapped_structure=[]
        for unit in structure:
            mapped_structure.append(tuple(sorted(
                tuple(old_to_new[i] for i in word)
                for word in unit
            )))
        return new_partition,tuple(sorted(mapped_structure))

    @classmethod
    def canonical_object_structure(
        cls,n_marks:int,partition:Partition,structure:Structure
    ) -> tuple[Partition,Structure]:
        return min(
            cls.map_partition_structure(partition,structure,p)
            for p in permutations(range(n_marks))
        )

    @classmethod
    def metric(cls,kind:str,partition:Partition|None,structure:Structure)->tuple[int,int,int,int,int]:
        if kind=="VOID":
            return (0,0,0,0,0)
        if kind=="BAG":
            return (0,1,0,0,0)
        inc=cls.incidence_metric(structure)
        return (len(partition or ()),0,inc[0],inc[1],inc[2])

    def synthesize(
        self,
        world:World,
        *,
        verification_enabled:bool=True,
        max_objects:int | None=None,
        max_units:int | None=None,
    ) -> dict[str,Any]:
        auth=self.authority(world)
        if auth:
            return auth
        if not verification_enabled:
            return {"status":"UNKNOWN_NO_VERIFIER","tested_candidates":0}

        n=len(world.rows[0].marks)
        mo=n if (self.max_objects is None and max_objects is None) else (
            self.max_objects if max_objects is None else int(max_objects)
        )
        mu=self.max_units if max_units is None else int(max_units)
        target=self.target_partition(world)

        candidates=[
            ("VOID",None,()),
            ("BAG",None,()),
        ]
        if mo is None:
            mo=n
        for partition in self.set_partitions(n):
            if len(partition)>int(mo):
                continue
            for structure in self.candidate_incidence(len(partition),self.max_arity,mu):
                candidates.append(("OBJECTS",partition,structure))

        candidates.sort(key=lambda c:(self.metric(*c),repr(c)))
        tested_by_metric={}
        obstruction_by_metric={}
        frontier=[]
        winning_metric=None

        i=0
        while i<len(candidates):
            m=self.metric(*candidates[i])
            batch=[]
            while i<len(candidates) and self.metric(*candidates[i])==m:
                batch.append(candidates[i]); i+=1
            key=":".join(str(x) for x in m)
            tested_by_metric[key]=len(batch)
            first_obstruction=None
            exact=[]
            for candidate in batch:
                if self.induced_partition(world,*candidate)==target:
                    exact.append(candidate)
                elif first_obstruction is None:
                    first_obstruction=self.mismatch_witness(world,*candidate)
            if first_obstruction is not None:
                obstruction_by_metric[key]=first_obstruction
            if exact:
                winning_metric=m
                frontier=exact
                break

        if winning_metric is None:
            return {
                "status":"CERTIFIED_OBJECT_LANGUAGE_INADEQUACY",
                "tested_candidates":sum(tested_by_metric.values()),
                "tested_by_metric":tested_by_metric,
                "obstruction_by_metric":obstruction_by_metric,
                "max_objects":int(mo),
                "max_units":mu,
            }

        canonical=set()
        rendered=[]
        for kind,partition,structure in frontier:
            if kind in ("VOID","BAG"):
                canonical.add((kind,))
                rendered.append({"kind":kind})
            else:
                cp,cs=self.canonical_object_structure(n,partition or (),structure)
                canonical.add(("OBJECTS",cp,cs))
                rendered.append({
                    "kind":"OBJECTS",
                    "partition":[list(b) for b in partition or ()],
                    "incidence":[[[int(v) for v in word] for word in unit] for unit in structure],
                })

        canonical_rows=[]
        for item in sorted(canonical,key=repr):
            if item[0] in ("VOID","BAG"):
                canonical_rows.append({"kind":item[0]})
            else:
                _,p,s=item
                canonical_rows.append({
                    "kind":"OBJECTS",
                    "partition":[list(b) for b in p],
                    "incidence":[[[int(v) for v in word] for word in unit] for unit in s],
                })

        return {
            "status":"VERIFIED",
            "minimum_metric":list(winning_metric),
            "frontier_size":len(frontier),
            "frontier":rendered,
            "canonical_classes":canonical_rows,
            "canonical_class_count":len(canonical_rows),
            "tested_candidates":sum(tested_by_metric.values()),
            "tested_by_metric":tested_by_metric,
            "obstruction_by_metric":obstruction_by_metric,
        }
