#!/usr/bin/env python3
from __future__ import annotations

import itertools
from dataclasses import dataclass
from typing import Any, Dict, Iterable, List, Sequence, Tuple

from basis import RelationalWorld, Permutation, identity, compose, inverse


@dataclass(frozen=True)
class SymmetryCode:
    interface_key: Tuple[int,int,int]
    transformations: Tuple[Permutation, ...]
    provenance: Tuple[str, ...]

    def data(self)->Dict[str,Any]:
        return {
            "interface_key": list(self.interface_key),
            "transformations": [list(p) for p in self.transformations],
            "provenance": list(self.provenance),
        }


class Kernel:
    def __init__(self):
        self.compiled: Dict[Tuple[int,int,int], SymmetryCode] = {}
        self.usage: Dict[Tuple[Any,...], List[str]] = {}

    @staticmethod
    def _authority(world:RelationalWorld):
        if not world.complete:
            return {"status":"UNKNOWN_AUTHORITY"}
        return None

    @staticmethod
    def preserves(world:RelationalWorld,p:Permutation)->bool:
        n=world.n
        for i in range(n):
            if world.consequences[i] != world.consequences[p[i]]:
                return False
        for R in world.relations:
            for i in range(n):
                for j in range(n):
                    if R[i][j] != R[p[i]][p[j]]:
                        return False
        return True

    def discover(self,world:RelationalWorld,allow_nonidentity:bool=True)->Dict[str,Any]:
        auth=self._authority(world)
        if auth:
            return auth
        perms=(identity(world.n),) if not allow_nonidentity else tuple(itertools.permutations(range(world.n)))
        admitted=[p for p in perms if self.preserves(world,p)]
        admitted=tuple(sorted(admitted))
        S=set(admitted)
        gid=identity(world.n)
        identity_ok=gid in S
        inverse_ok=all(inverse(p) in S for p in admitted)
        closure_ok=all(compose(p,q) in S for p in admitted for q in admitted)
        return {
            "status":"VERIFIED",
            "tested_bijections":len(perms),
            "transformations":[list(p) for p in admitted],
            "group_size":len(admitted),
            "group_laws":{
                "identity":identity_ok,
                "inverse":inverse_ok,
                "closure":closure_ok,
            },
        }

    @staticmethod
    def point_orbits(n:int,group:Sequence[Permutation])->Tuple[Tuple[int,...],...]:
        unseen=set(range(n))
        out=[]
        while unseen:
            x=min(unseen)
            orb={p[x] for p in group}
            changed=True
            while changed:
                changed=False
                new=set(orb)
                for y in list(orb):
                    new.update(p[y] for p in group)
                if new!=orb:
                    orb=new
                    changed=True
            out.append(tuple(sorted(orb)))
            unseen-=orb
        return tuple(sorted(out,key=lambda z:(len(z),z)))

    @staticmethod
    def pair_orbits(n:int,group:Sequence[Permutation])->Tuple[Tuple[Tuple[int,int],...],...]:
        unseen={(i,j) for i in range(n) for j in range(n)}
        out=[]
        while unseen:
            x=min(unseen)
            orb={(p[x[0]],p[x[1]]) for p in group}
            changed=True
            while changed:
                changed=False
                new=set(orb)
                for y in list(orb):
                    new.update((p[y[0]],p[y[1]]) for p in group)
                if new!=orb:
                    orb=new
                    changed=True
            out.append(tuple(sorted(orb)))
            unseen-=orb
        return tuple(sorted(out,key=lambda z:(len(z),z)))

    @staticmethod
    def reconstructible(world:RelationalWorld,pair_orbits)->bool:
        for R in world.relations:
            for orb in pair_orbits:
                vals={R[i][j] for i,j in orb}
                if len(vals)!=1:
                    return False
        return True

    def analyze(self,world:RelationalWorld,allow_nonidentity:bool=True)->Dict[str,Any]:
        d=self.discover(world,allow_nonidentity=allow_nonidentity)
        if d.get("status")!="VERIFIED":
            return d
        group=tuple(tuple(p) for p in d["transformations"])
        po=self.point_orbits(world.n,group)
        qo=self.pair_orbits(world.n,group)
        raw=world.n*world.n*len(world.relations)
        compressed=len(qo)*len(world.relations)
        exact=self.reconstructible(world,qo)
        return {
            **d,
            "point_orbits":[list(o) for o in po],
            "pair_orbits":[[list(x) for x in o] for o in qo],
            "raw_relation_comparisons":raw,
            "orbit_relation_comparisons":compressed,
            "exact_orbit_reconstruction":exact,
            "qualification_reduction":raw-compressed,
        }

    def _record(self,request_id:str,world:RelationalWorld,group:Sequence[Permutation]):
        key=(world.interface_key(),tuple(group))
        origins=self.usage.setdefault(key,[])
        if request_id not in origins:
            origins.append(request_id)
        if len(origins)<2:
            return None
        code=SymmetryCode(
            interface_key=world.interface_key(),
            transformations=tuple(group),
            provenance=tuple(origins),
        )
        self.compiled[world.interface_key()]=code
        return code

    def replay(self,request_id:str,world:RelationalWorld,code:SymmetryCode)->Dict[str,Any]:
        auth=self._authority(world)
        if auth:
            return {"request_id":request_id,**auth,"route":"STOP"}
        if code.interface_key!=world.interface_key():
            return {"request_id":request_id,"status":"TYPE_MISMATCH","route":"STOP"}
        failed=[p for p in code.transformations if not self.preserves(world,p)]
        ok=not failed
        group=tuple(p for p in code.transformations if p not in failed)
        po=self.pair_orbits(world.n,group if group else (identity(world.n),))
        return {
            "request_id":request_id,
            "status":"VERIFIED" if ok else "REPLAY_FAILED",
            "route":"REPLAY_SYMMETRY",
            "failed_transformations":[list(p) for p in failed],
            "group_size":len(group),
            "orbit_relation_comparisons":len(po)*len(world.relations),
            "acquisition_search_count":0,
        }

    def ablate(self,world:RelationalWorld)->bool:
        return self.compiled.pop(world.interface_key(),None) is not None

    def solve(self,request_id:str,world:RelationalWorld,allow_search:bool=True,allow_nonidentity:bool=True)->Dict[str,Any]:
        auth=self._authority(world)
        if auth:
            return {"request_id":request_id,**auth,"route":"STOP"}
        retained=self.compiled.get(world.interface_key())
        failed_reuse=None
        if retained is not None:
            r=self.replay(request_id,world,retained)
            if r["status"]=="VERIFIED":
                return {**r,"route":"REUSE_COMPILED_SYMMETRY"}
            failed_reuse=r
        if not allow_search:
            return {
                "request_id":request_id,
                "status":"UNKNOWN_SYMMETRY",
                "route":"STOP",
                "acquisition_search_count":0,
                "failed_reuse":failed_reuse,
            }
        result=self.analyze(world,allow_nonidentity=allow_nonidentity)
        if result.get("status")!="VERIFIED":
            return {"request_id":request_id,**result,"route":"DEVELOP"}
        group=tuple(tuple(p) for p in result["transformations"])
        promoted=None
        if result["group_size"]>1 and result["qualification_reduction"]>0 and result["exact_orbit_reconstruction"]:
            promoted=self._record(request_id,world,group)
        return {
            "request_id":request_id,
            "status":"VERIFIED",
            "route":"DEVELOP",
            "analysis":result,
            "promoted_code":promoted.data() if promoted else None,
            "acquisition_search_count":1,
            "failed_reuse":failed_reuse,
        }
