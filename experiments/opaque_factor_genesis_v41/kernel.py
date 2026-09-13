from __future__ import annotations
from functools import lru_cache
from itertools import permutations, product
from math import prod
from typing import Any

from basis import World

Partition = tuple[tuple[int,...],...]
Factorization = tuple[Partition,...]

class Kernel:
    @staticmethod
    @lru_cache(maxsize=None)
    def multiplicative_shapes(n:int,minimum_factor:int=2)->tuple[tuple[int,...],...]:
        out={(int(n),)}
        for f in range(int(minimum_factor),int(n)+1):
            if f*f>n:
                break
            if n%f!=0:
                continue
            for tail in Kernel.multiplicative_shapes(n//f,f):
                out.add((f,)+tail)
        return tuple(sorted(out,key=lambda shape:(len(shape),shape)))

    @staticmethod
    def authority(world:World)->dict[str,Any] | None:
        if not world.complete or world.state_count!=8 or world.action_count<1:
            return {"status":"UNKNOWN_AUTHORITY"}
        if any(
            not (0<=int(r.state)<world.state_count)
            or not (0<=int(r.after)<world.state_count)
            or not (0<=int(r.action)<world.action_count)
            or r.consequence is None
            for r in world.rows
        ):
            return {"status":"UNKNOWN_AUTHORITY"}
        observed={(int(r.state),int(r.action)) for r in world.rows}
        expected=set(product(range(world.state_count),range(world.action_count)))
        if observed!=expected or len(observed)!=len(world.rows):
            return {"status":"UNKNOWN_AUTHORITY"}
        return None

    @staticmethod
    def canonical_partition(values)->tuple[int,...]:
        ids={}; out=[]
        for value in values:
            if value not in ids:
                ids[value]=len(ids)
            out.append(ids[value])
        return tuple(out)

    @staticmethod
    def codes(shape:tuple[int,...])->tuple[tuple[int,...],...]:
        return tuple(product(*(range(a) for a in shape)))

    @staticmethod
    def partition_from_coordinate(
        assignment:tuple[tuple[int,...],...],coord:int
    )->Partition:
        groups={}
        for state,code in enumerate(assignment):
            groups.setdefault(int(code[coord]),[]).append(state)
        return tuple(sorted(tuple(sorted(v)) for v in groups.values()))

    @classmethod
    def factorization_from_assignment(
        cls,assignment:tuple[tuple[int,...],...],shape:tuple[int,...]
    )->Factorization:
        factors=[
            cls.partition_from_coordinate(assignment,j)
            for j in range(len(shape))
        ]
        return tuple(sorted(factors,key=lambda p:(len(p),p)))

    @classmethod
    @lru_cache(maxsize=None)
    def factorizations_for_shape(cls,shape:tuple[int,...])->tuple[Factorization,...]:
        if prod(shape)!=8:
            return ()
        codes=cls.codes(shape)
        out=set()
        for perm in permutations(codes):
            out.add(cls.factorization_from_assignment(tuple(perm),shape))
        return tuple(sorted(out))

    @classmethod
    def candidates(cls,max_factors:int | None=None)->tuple[Factorization,...]:
        out=[]
        for shape in cls.multiplicative_shapes(8):
            if max_factors is not None and len(shape)>int(max_factors):
                continue
            out.extend(cls.factorizations_for_shape(shape))
        return tuple(sorted(set(out),key=lambda f:(len(f),tuple(len(p) for p in f),f)))

    @staticmethod
    def state_factor_values(f:Factorization)->tuple[tuple[int,...],...]:
        # State labels are opaque 0..7 symbols. Build only candidate coordinate values.
        vals=[]
        for state in range(8):
            row=[]
            for part in f:
                idx=next(i for i,b in enumerate(part) if state in b)
                row.append(idx)
            vals.append(tuple(row))
        return tuple(vals)

    @classmethod
    def action_target(
        cls,world:World,f:Factorization,action:int
    )->int | None:
        values=cls.state_factor_values(f)
        rows=[r for r in world.rows if int(r.action)==int(action)]
        possible=[]
        for j,part in enumerate(f):
            mapping={}
            ok=True
            changed=False
            for r in rows:
                before=values[int(r.state)]
                after=values[int(r.after)]
                if any(before[k]!=after[k] for k in range(len(f)) if k!=j):
                    ok=False
                    break
                a=int(before[j]); b=int(after[j])
                if a in mapping and mapping[a]!=b:
                    ok=False
                    break
                mapping[a]=b
                changed = changed or (a!=b)
            if not ok or not changed:
                continue
            if set(mapping)!=set(range(len(part))):
                continue
            if set(mapping.values())!=set(range(len(part))):
                continue
            possible.append(j)
        return possible[0] if len(possible)==1 else None

    @classmethod
    def induced_partition(
        cls,world:World,f:Factorization
    )->tuple[int,...] | None:
        targets=[]
        by_action={}
        for action in range(world.action_count):
            t=cls.action_target(world,f,action)
            if t is None:
                return None
            by_action[action]=t
        for r in world.rows:
            targets.append(by_action[int(r.action)])
        return cls.canonical_partition(targets)

    @classmethod
    def target_partition(cls,world:World)->tuple[int,...]:
        return cls.canonical_partition(int(r.consequence) for r in world.rows)

    @classmethod
    def mismatch_witness(
        cls,world:World,f:Factorization
    )->dict[str,Any] | None:
        induced=cls.induced_partition(world,f)
        if induced is None:
            return {"kind":"INTERVENTION_NOT_FACTOR_LOCAL"}
        target=cls.target_partition(world)
        for i,(a,b) in enumerate(zip(induced,target)):
            for j in range(i):
                if (induced[j]==a)!=(target[j]==b):
                    return {
                        "kind":"TARGET_CLASS_OBSTRUCTION",
                        "row_a":j,
                        "row_b":i,
                    }
        return None

    @staticmethod
    def transform_factorization(f:Factorization,p:tuple[int,...])->Factorization:
        mapped=[]
        for part in f:
            blocks=tuple(sorted(
                tuple(sorted(int(p[s]) for s in block))
                for block in part
            ))
            mapped.append(blocks)
        return tuple(sorted(mapped,key=lambda part:(len(part),part)))

    def synthesize(
        self,world:World,*,
        verification_enabled:bool=True,
        maximum_factors:int | None=None,
    )->dict[str,Any]:
        auth=self.authority(world)
        if auth:
            return auth
        if not verification_enabled:
            return {"status":"UNKNOWN_NO_VERIFIER","tested_factorizations":0}

        target=self.target_partition(world)
        tested_by_factor_count={}
        obstruction_by_factor_count={}
        frontier=[]
        winning=None

        candidates=self.candidates(maximum_factors)
        for k in sorted({len(f) for f in candidates}):
            batch=[f for f in candidates if len(f)==k]
            tested_by_factor_count[str(k)]=len(batch)
            first_obstruction=None
            exact=[]
            for f in batch:
                induced=self.induced_partition(world,f)
                if induced==target:
                    exact.append(f)
                elif first_obstruction is None:
                    first_obstruction=self.mismatch_witness(world,f)
            if first_obstruction is not None:
                obstruction_by_factor_count[str(k)]=first_obstruction
            if exact:
                winning=k
                frontier=exact
                break

        if winning is None:
            return {
                "status":"CERTIFIED_FACTOR_LANGUAGE_INADEQUACY",
                "tested_factorizations":sum(tested_by_factor_count.values()),
                "tested_by_factor_count":tested_by_factor_count,
                "obstruction_by_factor_count":obstruction_by_factor_count,
                "maximum_factors":maximum_factors,
            }

        return {
            "status":"VERIFIED",
            "minimum_factor_count":winning,
            "frontier_size":len(frontier),
            "frontier":[[[list(block) for block in part] for part in f] for f in frontier],
            "tested_factorizations":sum(tested_by_factor_count.values()),
            "tested_by_factor_count":tested_by_factor_count,
            "obstruction_by_factor_count":obstruction_by_factor_count,
        }
