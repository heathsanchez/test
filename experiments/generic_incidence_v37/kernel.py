from __future__ import annotations
from functools import lru_cache
from itertools import combinations, permutations, product
from math import prod
from typing import Any

from basis import World

Word = tuple[int,...]
Unit = tuple[Word,...]
Structure = tuple[Unit,...]

class Kernel:
    def __init__(self,max_arity: int=3,max_units: int=2):
        self.max_arity=int(max_arity)
        self.max_units=int(max_units)

    @staticmethod
    def authority(world: World) -> dict[str,Any] | None:
        if not world.complete or not world.rows:
            return {"status":"UNKNOWN_AUTHORITY"}
        n=len(world.rows[0].sites)
        if n<1:
            return {"status":"INVALID_EMPTY_BOUNDARY"}
        if any(len(r.sites)!=n or r.consequence is None for r in world.rows):
            return {"status":"UNKNOWN_AUTHORITY"}
        alphabets=[]
        for i in range(n):
            vals=tuple(sorted({int(r.sites[i]) for r in world.rows}))
            if not vals:
                return {"status":"UNKNOWN_AUTHORITY"}
            alphabets.append(vals)
        expected=prod(len(a) for a in alphabets)
        observed={tuple(int(v) for v in r.sites) for r in world.rows}
        if len(observed)!=len(world.rows) or len(observed)!=expected:
            return {"status":"UNKNOWN_AUTHORITY"}
        if observed != set(product(*alphabets)):
            return {"status":"UNKNOWN_AUTHORITY"}
        return None

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
            closed=True
            for a in H:
                for b in H:
                    if cls.compose(a,b) not in hs:
                        closed=False
                        break
                if not closed:
                    break
            if closed:
                groups.append(tuple(sorted(H)))
        return tuple(sorted(set(groups),key=lambda H:(len(H),H)))

    @staticmethod
    def apply_coordinate_permutation(word: Word,p: tuple[int,...]) -> Word:
        return tuple(word[p[i]] for i in range(len(p)))

    @classmethod
    def incidence_units(cls,n: int,max_arity: int) -> tuple[Unit,...]:
        units=set()
        for k in range(1,min(int(max_arity),n)+1):
            for H in cls.coordinate_subgroups(k):
                for word in permutations(range(n),k):
                    orbit=tuple(sorted({
                        cls.apply_coordinate_permutation(tuple(word),p)
                        for p in H
                    }))
                    units.add(orbit)
        return tuple(sorted(units,key=lambda u:(len(u[0]),len(u),u)))

    @staticmethod
    def unit_arity(unit: Unit) -> int:
        return len(unit[0])

    @classmethod
    def structure_metric(cls,structure: Structure) -> tuple[int,int,int]:
        return (
            len(structure),
            sum(cls.unit_arity(u) for u in structure),
            sum(len(u) for u in structure),
        )

    @staticmethod
    def unit_signature(values: tuple[int,...],unit: Unit) -> tuple[tuple[int,...],...]:
        return tuple(sorted(
            tuple(int(values[i]) for i in word)
            for word in unit
        ))

    @classmethod
    def structure_signature(cls,values: tuple[int,...],structure: Structure):
        return tuple(sorted(cls.unit_signature(values,u) for u in structure))

    @staticmethod
    def canonical_partition(values) -> tuple[int,...]:
        ids={}; out=[]
        for value in values:
            if value not in ids:
                ids[value]=len(ids)
            out.append(ids[value])
        return tuple(out)

    @classmethod
    def induced_partition(cls,world: World,structure: Structure) -> tuple[int,...]:
        return cls.canonical_partition(
            cls.structure_signature(tuple(int(v) for v in r.sites),structure)
            for r in world.rows
        )

    @classmethod
    def target_partition(cls,world: World) -> tuple[int,...]:
        return cls.canonical_partition(int(r.consequence) for r in world.rows)

    @classmethod
    def mismatch_witness(cls,world: World,structure: Structure) -> dict[str,Any] | None:
        sigs=[
            cls.structure_signature(tuple(int(v) for v in r.sites),structure)
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
    def map_structure(cls,structure: Structure,p: tuple[int,...]) -> Structure:
        mapped=[]
        for unit in structure:
            mapped.append(tuple(sorted(
                tuple(int(p[i]) for i in word)
                for word in unit
            )))
        return tuple(sorted(mapped))

    @classmethod
    def canonical_structure(cls,n: int,structure: Structure) -> Structure:
        return min(cls.map_structure(structure,p) for p in permutations(range(n)))

    @classmethod
    def candidate_structures(cls,n: int,max_arity: int,max_units: int) -> tuple[Structure,...]:
        units=cls.incidence_units(n,max_arity)
        structures=[()]
        for count in range(1,int(max_units)+1):
            structures.extend(tuple(c) for c in combinations(units,count))
        return tuple(sorted(structures,key=lambda s:(cls.structure_metric(s),s)))

    def synthesize(
        self,
        world: World,
        *,
        verification_enabled: bool=True,
        max_arity: int | None=None,
        max_units: int | None=None,
        allow_nontrivial_coordinate_symmetry: bool=True,
    ) -> dict[str,Any]:
        auth=self.authority(world)
        if auth:
            return auth
        if not verification_enabled:
            return {"status":"UNKNOWN_NO_VERIFIER","tested_structures":0}

        n=len(world.rows[0].sites)
        arity=self.max_arity if max_arity is None else int(max_arity)
        units=self.max_units if max_units is None else int(max_units)
        target=self.target_partition(world)

        all_units=self.incidence_units(n,arity)
        if not allow_nontrivial_coordinate_symmetry:
            all_units=tuple(u for u in all_units if len(u)==1)

        candidates=[()]
        for count in range(1,units+1):
            candidates.extend(tuple(c) for c in combinations(all_units,count))
        candidates.sort(key=lambda s:(self.structure_metric(s),s))

        tested_by_metric={}
        obstruction_by_metric={}
        frontier=[]
        winning_metric=None

        i=0
        while i<len(candidates):
            metric=self.structure_metric(candidates[i])
            batch=[]
            while i<len(candidates) and self.structure_metric(candidates[i])==metric:
                batch.append(candidates[i]); i+=1

            key=":".join(str(x) for x in metric)
            tested_by_metric[key]=len(batch)
            first_obstruction=None
            exact=[]
            for structure in batch:
                part=self.induced_partition(world,structure)
                if part==target:
                    exact.append(structure)
                elif first_obstruction is None:
                    first_obstruction=self.mismatch_witness(world,structure)
            if first_obstruction is not None:
                obstruction_by_metric[key]=first_obstruction
            if exact:
                winning_metric=metric
                frontier=exact
                break

        if winning_metric is None:
            return {
                "status":"CERTIFIED_INCIDENCE_LANGUAGE_INADEQUACY",
                "site_count":n,
                "tested_structures":sum(tested_by_metric.values()),
                "tested_by_metric":tested_by_metric,
                "obstruction_by_metric":obstruction_by_metric,
                "max_arity":arity,
                "max_units":units,
                "allow_nontrivial_coordinate_symmetry":bool(allow_nontrivial_coordinate_symmetry),
            }

        canonical_classes=sorted({
            self.canonical_structure(n,s)
            for s in frontier
        })

        return {
            "status":"VERIFIED",
            "site_count":n,
            "minimum_metric":list(winning_metric),
            "frontier_size":len(frontier),
            "frontier":[[[list(word) for word in unit] for unit in s] for s in frontier],
            "canonical_classes":[[[list(word) for word in unit] for unit in s] for s in canonical_classes],
            "canonical_class_count":len(canonical_classes),
            "tested_structures":sum(tested_by_metric.values()),
            "tested_by_metric":tested_by_metric,
            "obstruction_by_metric":obstruction_by_metric,
        }
