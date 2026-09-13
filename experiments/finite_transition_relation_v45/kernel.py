from __future__ import annotations
from itertools import product
from math import prod
from typing import Any

from basis import World

Relation = tuple[tuple[int,...],...]

class Kernel:
    @staticmethod
    def authority(world:World)->dict[str,Any] | None:
        if not world.complete or world.state_count<2 or world.action_count<1:
            return {"status":"UNKNOWN_AUTHORITY"}

        observed=set()
        for r in world.rows:
            if not (0<=int(r.state)<world.state_count):
                return {"status":"UNKNOWN_AUTHORITY"}
            if not (0<=int(r.action)<world.action_count):
                return {"status":"UNKNOWN_AUTHORITY"}
            if r.consequence is None:
                return {"status":"UNKNOWN_AUTHORITY"}
            ys=tuple(int(y) for y in r.afters)
            if tuple(sorted(set(ys)))!=ys:
                return {"status":"INVALID_RELATION_ROW"}
            if any(not (0<=y<world.state_count) for y in ys):
                return {"status":"INVALID_RELATION_ROW"}
            key=(int(r.state),int(r.action))
            if key in observed:
                return {"status":"UNKNOWN_AUTHORITY"}
            observed.add(key)

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
    def action_relations(world:World)->tuple[Relation,...]:
        out=[]
        for action in range(world.action_count):
            rows=sorted(
                (r for r in world.rows if int(r.action)==action),
                key=lambda r:int(r.state),
            )
            out.append(tuple(tuple(int(y) for y in r.afters) for r in rows))
        return tuple(out)

    @staticmethod
    def identity(n:int)->Relation:
        return tuple((i,) for i in range(n))

    @staticmethod
    def compose(a:Relation,b:Relation)->Relation:
        out=[]
        for x in range(len(b)):
            ys=set()
            for mid in b[x]:
                ys.update(int(z) for z in a[int(mid)])
            out.append(tuple(sorted(ys)))
        return tuple(out)

    @classmethod
    def generated_relation_monoid(
        cls,n:int,generators:tuple[Relation,...]
    )->tuple[Relation,...]:
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
    def relation_kind(r:Relation)->str:
        sizes=[len(row) for row in r]
        if all(k==1 for k in sizes):
            return "TOTAL_FUNCTION"
        if all(k<=1 for k in sizes):
            return "PARTIAL_FUNCTION"
        return "NONDETERMINISTIC_RELATION"

    @staticmethod
    def domain_size(r:Relation)->int:
        return sum(1 for row in r if row)

    @staticmethod
    def image_size(r:Relation)->int:
        return len({y for row in r for y in row})

    @staticmethod
    def max_branching(r:Relation)->int:
        return max((len(row) for row in r),default=0)

    @classmethod
    def monoid_profile(
        cls,n:int,monoid:tuple[Relation,...]
    )->dict[str,Any]:
        identity=cls.identity(n)
        kinds=[cls.relation_kind(r) for r in monoid]
        idempotents=[r for r in monoid if cls.compose(r,r)==r]
        return {
            "order":len(monoid),
            "total_function_count":sum(k=="TOTAL_FUNCTION" for k in kinds),
            "partial_function_count":sum(k=="PARTIAL_FUNCTION" for k in kinds),
            "nondeterministic_relation_count":sum(k=="NONDETERMINISTIC_RELATION" for k in kinds),
            "relation_kinds":sorted(set(kinds)),
            "domain_size_spectrum":sorted({cls.domain_size(r) for r in monoid}),
            "image_size_spectrum":sorted({cls.image_size(r) for r in monoid}),
            "max_branching_spectrum":sorted({cls.max_branching(r) for r in monoid}),
            "idempotent_count":len(idempotents),
            "nonidentity_idempotent_count":sum(r!=identity for r in idempotents),
            "empty_relation_count":sum(all(len(row)==0 for row in r) for r in monoid),
        }

    @staticmethod
    def commute(a:Relation,b:Relation)->bool:
        return Kernel.compose(a,b)==Kernel.compose(b,a)

    @classmethod
    def monoids_commute(
        cls,monoids:tuple[tuple[Relation,...],...]
    )->bool:
        for i in range(len(monoids)):
            for j in range(i+1,len(monoids)):
                if any(not cls.commute(a,b) for a in monoids[i] for b in monoids[j]):
                    return False
        return True

    @classmethod
    def pairwise_identity_intersection(
        cls,n:int,monoids:tuple[tuple[Relation,...],...]
    )->bool:
        identity=cls.identity(n)
        for i in range(len(monoids)):
            for j in range(i+1,len(monoids)):
                if set(monoids[i]).intersection(monoids[j])!={identity}:
                    return False
        return True

    @classmethod
    def multiplication_image(
        cls,n:int,monoids:tuple[tuple[Relation,...],...]
    )->tuple[Relation,...]:
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
        n:int,relations:tuple[Relation,...]
    )->tuple[tuple[int,...],...]:
        adj={i:set() for i in range(n)}
        for r in relations:
            for x,row in enumerate(r):
                for y in row:
                    adj[x].add(int(y))
                    adj[int(y)].add(x)

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
        minimum_successors_per_state:int | None=None,
        maximum_successors_per_state:int | None=None,
    )->dict[str,Any]:
        auth=self.authority(world)
        if auth:
            return auth
        if not verification_enabled:
            return {"status":"UNKNOWN_NO_VERIFIER","algebra_steps":0}

        successor_sizes=[len(r.afters) for r in world.rows]
        if (
            minimum_successors_per_state is not None
            and min(successor_sizes)<int(minimum_successors_per_state)
        ):
            return {
                "status":"CERTIFIED_SUCCESSOR_MULTIPLICITY_BOUND_INADEQUACY",
                "minimum_successors_per_state":int(minimum_successors_per_state),
                "observed_minimum_successors":min(successor_sizes),
                "algebra_steps":0,
            }
        if (
            maximum_successors_per_state is not None
            and max(successor_sizes)>int(maximum_successors_per_state)
        ):
            return {
                "status":"CERTIFIED_SUCCESSOR_MULTIPLICITY_BOUND_INADEQUACY",
                "maximum_successors_per_state":int(maximum_successors_per_state),
                "observed_maximum_successors":max(successor_sizes),
                "algebra_steps":0,
            }

        classes=self.action_classes(world)
        if allowed_action_classes is not None and len(classes)>int(allowed_action_classes):
            return {
                "status":"CERTIFIED_ACTION_CLASS_BOUND_INADEQUACY",
                "action_class_count":len(classes),
                "allowed_action_classes":int(allowed_action_classes),
                "algebra_steps":0,
            }

        relations=self.action_relations(world)
        n=world.state_count

        class_monoids=tuple(
            self.generated_relation_monoid(
                n,tuple(relations[a] for a in cls_actions)
            )
            for cls_actions in classes
        )
        class_profiles=[
            self.monoid_profile(n,m) for m in class_monoids
        ]
        full=self.generated_relation_monoid(n,tuple(relations))
        full_profile=self.monoid_profile(n,full)
        weak_components=self.weak_action_components(n,tuple(relations))

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
            classification="DERIVED_DIRECT_RELATION_COMPLEMENTARITY"
        elif internal_direct:
            classification="UNDERRESOLVED_MULTIPLE_ACTION_COMPONENTS"
        else:
            classification="COUPLED_TRANSITION_RELATIONS"

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
