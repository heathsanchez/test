from __future__ import annotations
from itertools import product
from math import prod
from typing import Any

from basis import World

Perm = tuple[int,...]

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
            rows=sorted(
                (r for r in world.rows if int(r.action)==action),
                key=lambda r:int(r.state),
            )
            images=[int(r.after) for r in rows]
            if sorted(images)!=list(range(world.state_count)):
                return {"status":"INVALID_NONBIJECTIVE_TRANSFORMATION"}
            labels={int(r.consequence) for r in rows}
            if len(labels)!=1:
                return {"status":"INVALID_ACTION_CLASS_AUTHORITY"}
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
    def action_maps(world:World)->tuple[Perm,...]:
        out=[]
        for action in range(world.action_count):
            rows=sorted(
                (r for r in world.rows if int(r.action)==action),
                key=lambda r:int(r.state),
            )
            out.append(tuple(int(r.after) for r in rows))
        return tuple(out)

    @staticmethod
    def identity(n:int)->Perm:
        return tuple(range(n))

    @staticmethod
    def compose(a:Perm,b:Perm)->Perm:
        return tuple(int(a[b[i]]) for i in range(len(a)))

    @classmethod
    def generated_group(cls,n:int,generators:tuple[Perm,...])->tuple[Perm,...]:
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
    def orbit_blocks(n:int,group:tuple[Perm,...])->tuple[tuple[int,...],...]:
        unseen=set(range(n))
        blocks=[]
        while unseen:
            seed=min(unseen)
            block={int(g[seed]) for g in group}
            changed=True
            while changed:
                changed=False
                extra=set()
                for x in tuple(block):
                    extra.update(int(g[x]) for g in group)
                if not extra.issubset(block):
                    block.update(extra); changed=True
            blocks.append(tuple(sorted(block)))
            unseen.difference_update(block)
        return tuple(sorted(blocks))

    @staticmethod
    def block_index(blocks:tuple[tuple[int,...],...],n:int)->tuple[int,...]:
        idx=[-1]*n
        for i,block in enumerate(blocks):
            for x in block:
                idx[int(x)]=i
        return tuple(idx)

    @classmethod
    def induced_on_blocks(
        cls,perm:Perm,blocks:tuple[tuple[int,...],...],n:int
    )->tuple[int,...] | None:
        idx=cls.block_index(blocks,n)
        image=[]
        for block in blocks:
            targets={idx[int(perm[x])] for x in block}
            if len(targets)!=1:
                return None
            image.append(next(iter(targets)))
        if sorted(image)!=list(range(len(blocks))):
            return None
        return tuple(int(x) for x in image)

    @classmethod
    def induced_group(
        cls,n:int,acting:tuple[Perm,...],blocks:tuple[tuple[int,...],...]
    )->tuple[tuple[int,...],...] | None:
        out=[]
        for g in acting:
            q=cls.induced_on_blocks(g,blocks,n)
            if q is None:
                return None
            out.append(q)
        return tuple(sorted(set(out)))

    @staticmethod
    def commute(a:Perm,b:Perm)->bool:
        return Kernel.compose(a,b)==Kernel.compose(b,a)

    @classmethod
    def subgroups_commute(cls,groups:tuple[tuple[Perm,...],...])->bool:
        for i in range(len(groups)):
            for j in range(i+1,len(groups)):
                if any(not cls.commute(a,b) for a in groups[i] for b in groups[j]):
                    return False
        return True

    @classmethod
    def pairwise_trivial_intersection(
        cls,n:int,groups:tuple[tuple[Perm,...],...]
    )->bool:
        identity=cls.identity(n)
        for i in range(len(groups)):
            for j in range(i+1,len(groups)):
                if set(groups[i]).intersection(groups[j])!={identity}:
                    return False
        return True

    @staticmethod
    def transformed_orbit_count(
        acting:tuple[tuple[int,...],...],carrier_size:int
    )->int:
        if carrier_size<1:
            return 0
        unseen=set(range(carrier_size))
        count=0
        while unseen:
            seed=min(unseen)
            orbit={int(g[seed]) for g in acting}
            changed=True
            while changed:
                changed=False
                extra=set()
                for x in tuple(orbit):
                    extra.update(int(g[x]) for g in acting)
                if not extra.issubset(orbit):
                    orbit.update(extra); changed=True
            unseen.difference_update(orbit)
            count+=1
        return count

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
            }

        maps=self.action_maps(world)
        n=world.state_count

        if len(classes)==1:
            full=self.generated_group(n,tuple(maps[a] for a in classes[0]))
            return {
                "status":"VERIFIED",
                "action_classes":[list(classes[0])],
                "class_count":1,
                "class_group_orders":[len(full)],
                "full_group_order":len(full),
                "full_state_orbit_count":len(self.orbit_blocks(n,full)),
                "carriers":[],
                "classification":"UNDECOMPOSED_SINGLE_CLASS",
                "algebra_steps":1,
            }

        class_groups=[]
        for cls_actions in classes:
            gens=tuple(maps[a] for a in cls_actions)
            class_groups.append(self.generated_group(n,gens))
        class_groups=tuple(class_groups)

        full_group=self.generated_group(n,tuple(
            maps[a] for cls_actions in classes for a in cls_actions
        ))
        full_orbits=self.orbit_blocks(n,full_group)

        carriers=[]
        for i,cls_actions in enumerate(classes):
            other_generators=tuple(
                maps[a]
                for j,other_class in enumerate(classes)
                if j!=i
                for a in other_class
            )
            other_group=self.generated_group(n,other_generators)
            blocks=self.orbit_blocks(n,other_group)
            induced=self.induced_group(n,class_groups[i],blocks)
            if induced is None:
                carriers.append({
                    "action_class":list(cls_actions),
                    "status":"COUPLED_NONNORMAL_ACTION",
                    "other_group_order":len(other_group),
                    "orbit_block_count":len(blocks),
                    "orbit_block_sizes":sorted(len(b) for b in blocks),
                })
                continue
            orbit_count=self.transformed_orbit_count(induced,len(blocks))
            carriers.append({
                "action_class":list(cls_actions),
                "status":"DERIVED",
                "class_group_order":len(class_groups[i]),
                "other_group_order":len(other_group),
                "orbit_block_count":len(blocks),
                "orbit_block_sizes":sorted(len(b) for b in blocks),
                "induced_group_order":len(induced),
                "induced_orbit_count":orbit_count,
                "induced_orbit_size":(
                    len(blocks)//orbit_count if orbit_count and len(blocks)%orbit_count==0 else None
                ),
            })

        all_derived=all(c["status"]=="DERIVED" for c in carriers)
        commute=self.subgroups_commute(class_groups)
        trivial_intersections=self.pairwise_trivial_intersection(n,class_groups)
        generated_order_product=prod(len(g) for g in class_groups)
        full_transitive=(len(full_orbits)==1)
        regular=(len(full_group)==n and full_transitive)
        direct_order=(generated_order_product==len(full_group))

        if (
            all_derived and commute and trivial_intersections
            and direct_order and regular
        ):
            classification="DERIVED_DIRECT_COMPLEMENTARITY"
        elif all_derived and commute and trivial_intersections and direct_order:
            classification="UNDERRESOLVED_MULTIPLE_STATE_ORBITS"
        else:
            classification="COUPLED_ACTION_ALGEBRA"

        return {
            "status":"VERIFIED",
            "action_classes":[list(c) for c in classes],
            "class_count":len(classes),
            "class_group_orders":[len(g) for g in class_groups],
            "full_group_order":len(full_group),
            "full_state_orbit_count":len(full_orbits),
            "full_state_orbit_sizes":sorted(len(b) for b in full_orbits),
            "pairwise_commuting":commute,
            "pairwise_trivial_intersections":trivial_intersections,
            "class_group_order_product":generated_order_product,
            "direct_order_match":direct_order,
            "regular_transitive_action":regular,
            "carriers":carriers,
            "classification":classification,
            "algebra_steps":len(class_groups)+1,
        }
