#!/usr/bin/env python3
"""Frozen V25 unrestricted-relation repair and structural abstraction kernel."""
from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
from typing import Any, Dict, Mapping as TMapping, Optional, Sequence, Tuple

from basis import (
    Cell, ConsequenceWorld, Mapping, Relation,
    all_relations, compose_mappings,
    consequence_preserving_factorized_mappings,
    difference_edges, difference_term, extensional_distance,
    factorized_mapping_set, mapping_is_bijection,
    mapping_preserves_consequence, orbit_partition_from_mappings,
)


Term = Any


@dataclass(frozen=True)
class Residual:
    left: Cell
    right: Cell
    consequence: int
    left_orbit: int
    right_orbit: int

    def data(self):
        return {
            "left":list(self.left),"right":list(self.right),
            "consequence":self.consequence,
            "left_orbit":self.left_orbit,"right_orbit":self.right_orbit,
        }


@dataclass(frozen=True)
class CompiledSchema:
    schema_id: str
    term: Term
    provenance: Tuple[str,...]

    def data(self):
        return {
            "schema_id":self.schema_id,
            "term":term_to_json(self.term),
            "provenance":list(self.provenance),
            "variable_count":len(schema_variables(self.term)),
            "concrete_constant_count":count_constants(self.term),
        }


def term_to_json(term):
    if isinstance(term,tuple):
        return [term_to_json(x) for x in term]
    return term


def is_var(term):
    return isinstance(term,tuple) and len(term)==2 and term[0]=="VAR" and isinstance(term[1],int)


def schema_variables(term):
    out=set()
    def walk(t):
        if is_var(t): out.add(t)
        elif isinstance(t,tuple):
            for x in t: walk(x)
    walk(term)
    return tuple(sorted(out,key=lambda x:x[1]))


def count_constants(term):
    if is_var(term): return 0
    if isinstance(term,tuple):
        if term and term[0] in ("DIFF","EDGE"):
            return sum(count_constants(x) for x in term[1:])
        return sum(count_constants(x) for x in term)
    if isinstance(term,str) and term in ("DIFF","EDGE"): return 0
    return 1


def generic_anti_unify(left,right):
    disagreements={}
    next_id=[0]
    def freeze(x):
        return json.dumps(term_to_json(x),sort_keys=True,separators=(",",":"))
    def rec(a,b):
        if a==b:return a
        if isinstance(a,tuple) or isinstance(b,tuple):
            if not (isinstance(a,tuple) and isinstance(b,tuple)):return None
            if is_var(a) or is_var(b):return None
            if not a or not b or a[0]!=b[0] or len(a)!=len(b):return None
            children=[]
            for xa,xb in zip(a[1:],b[1:]):
                y=rec(xa,xb)
                if y is None:return None
                children.append(y)
            return (a[0],*children)
        key=(freeze(a),freeze(b))
        if key not in disagreements:
            disagreements[key]=("VAR",next_id[0]); next_id[0]+=1
        return disagreements[key]
    return rec(left,right)


def match_schema(schema,ground,seed=None):
    bindings=dict(seed or {})
    def rec(s,g):
        if is_var(s):
            old=bindings.get(s)
            if old is None:
                bindings[s]=g; return True
            return old==g
        if isinstance(s,tuple):
            if not isinstance(g,tuple) or not s or not g or len(s)!=len(g) or s[0]!=g[0]:
                return False
            return all(rec(xs,xg) for xs,xg in zip(s[1:],g[1:]))
        return s==g
    return bindings if rec(schema,ground) else None


def instantiate_schema(schema,bindings):
    if is_var(schema):return bindings.get(schema)
    if isinstance(schema,tuple):
        out=[]
        for x in schema[1:]:
            y=instantiate_schema(x,bindings)
            if y is None:return None
            out.append(y)
        return (schema[0],*out)
    return schema


def find_constructor_subterms(term,constructor):
    out=[]
    def walk(t):
        if isinstance(t,tuple):
            if t and t[0]==constructor:out.append(t)
            for x in t[1:]:walk(x)
    walk(term)
    return tuple(out)


class Kernel:
    @staticmethod
    def _authority(world):
        if not world.complete:
            return {"status":"UNKNOWN_AUTHORITY","reason":"consequence_table_incomplete"}
        return None

    def exhaust_current_language(self,world):
        a=self._authority(world)
        if a:return a
        all_l0=factorized_mapping_set(world)
        lawful=consequence_preserving_factorized_mappings(world)
        orbits=orbit_partition_from_mappings(world,lawful)
        return {
            "status":"VERIFIED",
            "candidate_count":len(all_l0),
            "lawful_count":len(lawful),
            "orbits":[[list(c) for c in o] for o in orbits],
            "_all_l0":all_l0,"_orbits":orbits,
        }

    def diagnose_residual(self,world,exhausted=None):
        a=self._authority(world)
        if a:return a
        ex=exhausted or self.exhaust_current_language(world)
        orbits=ex["_orbits"]
        for i in range(len(orbits)):
            for j in range(i+1,len(orbits)):
                for left in orbits[i]:
                    for right in orbits[j]:
                        lv=world.consequence(left)
                        if lv is not None and lv==world.consequence(right):
                            r=Residual(left,right,int(lv),i,j)
                            return {"status":"CERTIFIED_RESIDUAL","residual":r.data(),"_residual":r}
        return {"status":"NO_RESIDUAL"}

    @staticmethod
    def inspect_relation(world,relation):
        cells=world.cells()
        outgoing={cell:[] for cell in cells}
        incoming={cell:[] for cell in cells}
        edge_domain_ok=True
        for source,target in relation:
            if source not in outgoing or target not in incoming:
                edge_domain_ok=False
                continue
            outgoing[source].append(target)
            incoming[target].append(source)

        total=edge_domain_ok and all(len(outgoing[s])>=1 for s in cells)
        functional=edge_domain_ok and all(len(outgoing[s])<=1 for s in cells)
        mapping=None
        if total and functional:
            mapping=tuple(outgoing[s][0] for s in cells)

        bijection=(
            mapping is not None
            and all(len(incoming[t])==1 for t in cells)
            and mapping_is_bijection(world,mapping)
        )

        return {
            "edge_domain_ok":edge_domain_ok,
            "total":total,
            "functional":functional,
            "bijection":bijection,
            "_mapping":mapping,
        }

    @staticmethod
    def verify_relation(world,residual,relation,all_l0,verification_enabled=True):
        if not verification_enabled:
            return {"status":"UNKNOWN_NO_VERIFIER","accepted":False}

        shape=Kernel.inspect_relation(world,relation)
        mapping=shape["_mapping"]
        cells=world.cells(); idx={c:i for i,c in enumerate(cells)}

        discharge=(
            mapping is not None
            and mapping[idx[residual.left]]==residual.right
        )
        consequence=(
            shape["bijection"]
            and mapping_preserves_consequence(world,mapping)
        )
        novel=(
            mapping is not None
            and mapping not in all_l0
        )

        accepted=(
            shape["total"]
            and shape["functional"]
            and shape["bijection"]
            and discharge
            and consequence
            and novel
        )

        return {
            "status":"VERIFIED" if accepted else "REJECTED",
            "accepted":accepted,
            "total":shape["total"],
            "functional":shape["functional"],
            "bijection":shape["bijection"],
            "residual_discharge":discharge,
            "consequence_preserving":consequence,
            "novel_outside_current_language":novel,
            "distance":extensional_distance(world,relation),
            "mapping":[list(c) for c in mapping] if mapping is not None else None,
        }

    def exhaustive_repair(self,world,residual,verification_enabled=True):
        a=self._authority(world)
        if a:return a
        if not verification_enabled:
            return {"status":"UNKNOWN_NO_VERIFIER","acquisition_search_count":0}

        all_l0=factorized_mapping_set(world)
        tested=0; accepted=[]
        reject_counts={
            "not_total":0,
            "not_functional":0,
            "not_bijective":0,
        }

        for relation in all_relations(world):
            tested+=1
            verdict=self.verify_relation(world,residual,relation,all_l0,True)
            if not verdict["total"]:reject_counts["not_total"]+=1
            if not verdict["functional"]:reject_counts["not_functional"]+=1
            if not verdict["bijection"]:reject_counts["not_bijective"]+=1
            if verdict["accepted"]:
                accepted.append((relation,verdict))

        if not accepted:
            return {
                "status":"CERTIFIED_NO_REPAIR_IN_UNRESTRICTED_RELATION_LANGUAGE",
                "tested_relation_count":tested,
                "rejection_counts":reject_counts,
                "acquisition_search_count":1,
                "_frontier_objects":tuple(),
            }

        best=min(v["distance"] for _,v in accepted)
        frontier=[(r,v) for r,v in accepted if v["distance"]==best]
        frontier.sort(key=lambda row:tuple(sorted(row[0])))

        return {
            "status":"VERIFIED",
            "tested_relation_count":tested,
            "rejection_counts":reject_counts,
            "minimum_extensional_distance":best,
            "frontier":[
                {
                    "relation":[[list(a),list(b)] for a,b in sorted(r)],
                    "difference_edges":[[list(a),list(b)] for a,b in difference_edges(world,r)],
                    "verdict":v,
                }
                for r,v in frontier
            ],
            "_frontier_objects":tuple(r for r,_ in frontier),
            "acquisition_search_count":1,
        }

    def compile_schema(self,training):
        if len(training)<2:return {"status":"INSUFFICIENT_INDEPENDENT_REPAIRS"}
        terms=[difference_term(world,relation) for origin,world,residual,relation in training]
        schema=terms[0]
        for term in terms[1:]:
            schema=generic_anti_unify(schema,term)
            if schema is None:return {"status":"NO_SCHEMA"}
        if not schema_variables(schema):return {"status":"NO_ABSTRACTION"}
        replay=[]
        for term in terms:
            b=match_schema(schema,term)
            if b is None:return {"status":"SCHEMA_REPLAY_FAILED"}
            replay.append(instantiate_schema(schema,b)==term)
        if not all(replay):return {"status":"SCHEMA_REPLAY_FAILED"}
        sc=count_constants(schema); ic=[count_constants(t) for t in terms]
        if not all(sc<n for n in ic):return {"status":"NO_COMPRESSION"}
        sid="ur_"+hashlib.sha256(json.dumps(term_to_json(schema),sort_keys=True,separators=(",",":")).encode()).hexdigest()[:16]
        compiled=CompiledSchema(sid,schema,tuple(origin for origin,*_ in training))
        return {
            "status":"VERIFIED","schema":compiled.data(),
            "training_terms":[term_to_json(t) for t in terms],
            "training_replay":replay,
            "instance_constant_counts":ic,
            "schema_constant_count":sc,
            "_compiled":compiled,
        }

    @staticmethod
    def predict_difference(world,residual,schema):
        obligation=("EDGE",
            f"{world.world_id}::{residual.left[0]}:{residual.left[1]}",
            f"{world.world_id}::{residual.right[0]}:{residual.right[1]}")
        variables=set(schema_variables(schema.term))
        predictions=[]
        for sub in find_constructor_subterms(schema.term,"EDGE"):
            b=match_schema(sub,obligation)
            if b is None or not variables.issubset(set(b)):continue
            ground=instantiate_schema(schema.term,b)
            if ground is not None:predictions.append(ground)
        uniq={json.dumps(term_to_json(t),sort_keys=True):t for t in predictions}
        return tuple(uniq[k] for k in sorted(uniq))

    def develop(self,world,verification_enabled=True):
        a=self._authority(world)
        if a:return a
        ex=self.exhaust_current_language(world)
        diag=self.diagnose_residual(world,ex)

        if diag.get("status")=="NO_RESIDUAL":
            return {
                "status":"VERIFIED_NO_GROWTH",
                "constructor_growth_authorized":False,
                "current_language":{k:v for k,v in ex.items() if not k.startswith("_")},
                "diagnosis":diag,
                "acquisition_search_count":0,
            }

        if diag.get("status")!="CERTIFIED_RESIDUAL":return diag

        repair=self.exhaustive_repair(world,diag["_residual"],verification_enabled)
        relation=repair.get("_frontier_objects",(None,))[0] if repair.get("_frontier_objects") else None
        mapping=None
        if relation is not None:
            mapping=self.inspect_relation(world,relation)["_mapping"]

        return {
            "status":repair.get("status"),
            "constructor_growth_authorized":True,
            "current_language":{k:v for k,v in ex.items() if not k.startswith("_")},
            "diagnosis":{k:v for k,v in diag.items() if not k.startswith("_")},
            "repair":{k:v for k,v in repair.items() if not k.startswith("_")},
            "_residual":diag["_residual"],
            "_relation":relation,
            "_mapping":mapping,
            "acquisition_search_count":repair.get("acquisition_search_count",0),
        }

    @staticmethod
    def compose_verified(world,first,second):
        composed=compose_mappings(world,first,second)
        return {
            "mapping":[list(c) for c in composed],
            "bijection":mapping_is_bijection(world,composed),
            "consequence_preserving":mapping_preserves_consequence(world,composed),
        }
