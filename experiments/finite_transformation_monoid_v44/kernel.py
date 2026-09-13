from __future__ import annotations
from itertools import product
from math import prod
from typing import Any

from basis import World

Map = tuple[int,...]

class Kernel:
    @staticmethod
    def authority(world:World)->dict[str,Any] | None:
        if not world.complete or world.state_count<2 or world.action_count<1:
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

        for action in range(world.action_count):
            rows=[r for r in world.rows if int(r.action)==action]
            labels={int(r.consequence) for r in rows}
            if len(rows)!=world.state_count or len(labels)!=1:
                return {"status":"UNKNOWN_AUTHORITY"}
        return None

    @staticmethod
    def canonical_labels(values)->tuple[int,...]:
        ids={}; out=[]
        for value in values:
            if value not in ids:
                ids[value]=len(ids)
            out.append(ids[value])
        return tuple(out)

    @classmethod
    def action_classes(cls,world:World)->tuple[tuple[int,...],...]:
        labels=[]
        for action in range(world.action_count):
            row=next(r for r in world.rows if int(r.action)==action)
            labels.append(int(row.consequence))
        canon=cls.canonical_labels(labels)
        groups={}
        for action,c in enumerate(canon):
            groups.setdefault(int(c),[]).append(action)
        return tuple(tuple(v) for _,v in sorted(groups.items()))

    @staticmethod
    def action_maps(world:World)->tuple[Map,...]:
        out=[]
        for action in range(world.action_count):
            rows=sorted(
                (r for r in world.rows if int(r.action)==action),
                key=lambda r:int(r.state),
            )
            out.append(tuple(int(r.after) for r in rows))
        return tuple(out)

    @staticmethod
    def identity(n:int)->Map:
        return tuple(range(n))

    @staticmethod
    def compose(a:Map,b:Map)->Map:
        return tuple(int(a[b[i]]) for i in range(len(a)))

    @classmethod
    def generated_monoid(cls,n:int,generators:tuple[Map,...])->tuple[Map,...]:
        identity=cls.identity(n)
        seen={identity}
        frontier=[identity]
        gens=tuple(dict.fromkeys(generators))
        while frontier:
            x=frontier.pop()
            for g in gens:
                for y in (cls.compose(g,x),cls.compose(x,g)):
                    if y not in seen:
                        seen.add(y)
                        frontier.append(y)
        return tuple(sorted(seen))

    @staticmethod
    def map_rank(f:Map)->int:
        return len(set(int(x) for x in f))

    @classmethod
    def monoid_profile(cls,n:int,monoid:tuple[Map,...])->dict[str,Any]:
        identity=cls.identity(n)
        ranks=[cls.map_rank(f) for f in monoid]
        idempotents=[f for f in monoid if cls.compose(f,f)==f]
        unit_count=sum(1 for r in ranks if r==n)
        min_rank=min(ranks)
        if min_rank==n:
            rank_behavior="NO_RANK_LOSS"
        elif min_rank==1:
            rank_behavior="GLOBAL_COLLAPSE_PRESENT"
        else:
            rank_behavior="PARTIAL_RANK_LOSS"
        return {
            "order":len(monoid),
            "unit_count":unit_count,
            "all_elements_units":unit_count==len(monoid),
            "rank_spectrum":sorted(set(ranks)),
            "minimum_rank":min_rank,
            "idempotent_count":len(idempotents),
            "nonidentity_idempotent_count":sum(1 for f in idempotents if f!=identity),
            "constant_map_count":sum(1 for r in ranks if r==1),
            "rank_behavior":rank_behavior,
        }

    @staticmethod
    def commute(a:Map,b:Map)->bool:
        return Kernel.compose(a,b)==Kernel.compose(b,a)

    @classmethod
    def monoids_commute(cls,monoids:tuple[tuple[Map,...],...])->bool:
        for i in range(len(monoids)):
            for j in range(i+1,len(monoids)):
                if any(not cls.commute(a,b) for a in monoids[i] for b in monoids[j]):
                    return False
        return True

    @classmethod
    def pairwise_identity_intersection(
        cls,n:int,monoids:tuple[tuple[Map,...],...]
    )->bool:
        identity=cls.identity(n)
        for i in range(len(monoids)):
            for j in range(i+1,len(monoids)):
                if set(monoids[i]).intersection(monoids[j])!={identity}:
                    return False
        return True

    @classmethod
    def multiplication_image(
        cls,n:int,monoids:tuple[tuple[Map,...],...]
    )->tuple[Map,...]:
        current={cls.identity(n)}
        for monoid in monoids:
            current={
                cls.compose(a,b)
                for a in current
                for b in monoid
            }
        return tuple(sorted(current))

    @staticmethod
    def weak_action_components(
        n:int,maps:tuple[Map,...]
    )->tuple[tuple[int,...],...]:
        adj={i:set() for i in range(n)}
        for f in maps:
            for i,j in enumerate(f):
                adj[i].add(int(j))
                adj[int(j)].add(i)
        unseen=set(range(n))
        out=[]
        while unseen:
            seed=min(unseen)
            comp={seed}
            frontier=[seed]
            unseen.remove(seed)
            while frontier:
                x=frontier.pop()
                for y in adj[x]:
                    if y not in comp:
                        comp.add(y)
                        if y in unseen:
                            unseen.remove(y)
                        frontier.append(y)
            out.append(tuple(sorted(comp)))
        return tuple(sorted(out))

    def synthesize(
        self,world:World,*,
        verification_enabled:bool=True,
        allowed_action_classes:int | None=None,
    )->dict[str,Any]:
        auth=self.authority(world)
        if auth:
            return auth
        if not verification_enabled:
            return {"status":"UNKNOWN_NO_VERIFIER","algebra_steps":0}

        classes=self.action_classes(world)
        if allowed_action_classes is not None and len(classes)>int(allowed_action_classes):
            return {
                "status":"CERTIFIED_ACTION_CLASS_BOUND_INADEQUACY",
                "action_class_count":len(classes),
                "allowed_action_classes":int(allowed_action_classes),
                "algebra_steps":0,
            }

        maps=self.action_maps(world)
        n=world.state_count

        class_monoids=tuple(
            self.generated_monoid(n,tuple(maps[a] for a in cls_actions))
            for cls_actions in classes
        )
        class_profiles=[
            self.monoid_profile(n,m) for m in class_monoids
        ]
        full=self.generated_monoid(n,tuple(maps))
        full_profile=self.monoid_profile(n,full)
        weak_components=self.weak_action_components(n,tuple(maps))

        if len(classes)==1:
            return {
                "status":"VERIFIED",
                "action_classes":[list(classes[0])],
                "class_count":1,
                "class_profiles":class_profiles,
                "full_profile":full_profile,
                "weak_action_component_count":len(weak_components),
                "weak_action_component_sizes":sorted(len(c) for c in weak_components),
                "classification":"UNDECOMPOSED_SINGLE_CLASS",
                "algebra_steps":2,
            }

        commute=self.monoids_commute(class_monoids)
        identity_intersections=self.pairwise_identity_intersection(n,class_monoids)
        product_cardinality=prod(len(m) for m in class_monoids)
        image=self.multiplication_image(n,class_monoids)
        unique_coordinates=(len(image)==product_cardinality)
        spans_full=(set(image)==set(full))
        internal_direct=(
            commute and identity_intersections
            and unique_coordinates and spans_full
        )

        if internal_direct and len(weak_components)==1:
            classification="DERIVED_DIRECT_MONOID_COMPLEMENTARITY"
        elif internal_direct:
            classification="UNDERRESOLVED_MULTIPLE_ACTION_COMPONENTS"
        else:
            classification="COUPLED_TRANSFORMATION_MONOID"

        return {
            "status":"VERIFIED",
            "action_classes":[list(c) for c in classes],
            "class_count":len(classes),
            "class_profiles":class_profiles,
            "full_profile":full_profile,
            "pairwise_commuting":commute,
            "pairwise_identity_intersections":identity_intersections,
            "class_order_product":product_cardinality,
            "multiplication_image_size":len(image),
            "unique_product_coordinates":unique_coordinates,
            "multiplication_image_spans_full_monoid":spans_full,
            "internal_direct_product":internal_direct,
            "weak_action_component_count":len(weak_components),
            "weak_action_component_sizes":sorted(len(c) for c in weak_components),
            "classification":classification,
            "algebra_steps":len(class_monoids)+2,
        }
