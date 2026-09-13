from __future__ import annotations
from functools import lru_cache
from itertools import product
from typing import Any

from basis import World

Partition = tuple[tuple[int,...],...]

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
    def canonical_partition(values)->tuple[int,...]:
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
        canon=cls.canonical_partition(labels)
        groups={}
        for action,c in enumerate(canon):
            groups.setdefault(int(c),[]).append(action)
        return tuple(tuple(v) for _,v in sorted(groups.items()))

    @staticmethod
    @lru_cache(maxsize=None)
    def set_partitions(n:int)->tuple[Partition,...]:
        out=set()
        labels=[0]*n
        def rec(i:int,max_label:int):
            if i==n:
                blocks=[]
                for lab in range(max_label+1):
                    blocks.append(tuple(j for j,x in enumerate(labels) if x==lab))
                out.add(tuple(blocks))
                return
            for lab in range(max_label+2):
                labels[i]=lab
                rec(i+1,max(max_label,lab))
        labels[0]=0
        rec(1,0)
        return tuple(sorted(out,key=lambda p:(len(p),p)))

    @staticmethod
    def action_maps(world:World)->tuple[tuple[int,...],...]:
        maps=[]
        for action in range(world.action_count):
            rows=sorted(
                (r for r in world.rows if int(r.action)==action),
                key=lambda r:int(r.state),
            )
            maps.append(tuple(int(r.after) for r in rows))
        return tuple(maps)

    @staticmethod
    def block_index(partition:Partition)->tuple[int,...]:
        n=sum(len(b) for b in partition)
        out=[-1]*n
        for i,block in enumerate(partition):
            for state in block:
                out[int(state)]=i
        return tuple(out)

    @classmethod
    def quotient_action(
        cls,partition:Partition,mapping:tuple[int,...]
    )->tuple[int,...] | None:
        idx=cls.block_index(partition)
        image=[]
        for block in partition:
            targets={idx[int(mapping[s])] for s in block}
            if len(targets)!=1:
                return None
            image.append(next(iter(targets)))
        if sorted(image)!=list(range(len(partition))):
            return None
        return tuple(int(x) for x in image)

    @classmethod
    def moved_actions(
        cls,partition:Partition,maps:tuple[tuple[int,...],...]
    )->tuple[int,...] | None:
        moved=[]
        for action,mapping in enumerate(maps):
            q=cls.quotient_action(partition,mapping)
            if q is None:
                return None
            if q!=tuple(range(len(partition))):
                moved.append(action)
        return tuple(moved)

    @classmethod
    def obstruction(
        cls,partition:Partition,maps:tuple[tuple[int,...],...],target:tuple[int,...]
    )->dict[str,Any] | None:
        moved=cls.moved_actions(partition,maps)
        if moved is None:
            return {"kind":"NOT_AN_INVARIANT_QUOTIENT"}
        if moved!=target:
            return {
                "kind":"MOVE_SET_MISMATCH",
                "observed_moved_actions":list(moved),
                "required_moved_actions":list(target),
            }
        return None

    def synthesize(
        self,world:World,*,
        verification_enabled:bool=True,
        maximum_blocks_per_quotient:int | None=None,
    )->dict[str,Any]:
        auth=self.authority(world)
        if auth:
            return auth
        if not verification_enabled:
            return {"status":"UNKNOWN_NO_VERIFIER","tested_partitions":0}

        classes=self.action_classes(world)
        if len(classes)==1:
            return {
                "status":"VERIFIED",
                "action_classes":[list(classes[0])],
                "quotient_class_count":0,
                "class_witnesses":[],
                "tested_partitions":0,
                "undecomposed":True,
            }

        n=world.state_count
        maps=self.action_maps(world)
        partitions=self.set_partitions(n)
        if maximum_blocks_per_quotient is not None:
            partitions=tuple(
                p for p in partitions
                if len(p)<=int(maximum_blocks_per_quotient)
            )

        all_results=[]
        total_tested=0

        for target in classes:
            tested_by_blocks={}
            first_obstruction={}
            frontier=[]
            winning_blocks=None

            for block_count in sorted({len(p) for p in partitions}):
                batch=[p for p in partitions if len(p)==block_count]
                tested_by_blocks[str(block_count)]=len(batch)
                exact=[]
                first=None
                for partition in batch:
                    total_tested+=1
                    moved=self.moved_actions(partition,maps)
                    if moved==target:
                        exact.append(partition)
                    elif first is None:
                        first=self.obstruction(partition,maps,target)
                if first is not None:
                    first_obstruction[str(block_count)]=first
                if exact:
                    winning_blocks=block_count
                    frontier=exact
                    break

            if winning_blocks is None:
                return {
                    "status":"CERTIFIED_QUOTIENT_LANGUAGE_INADEQUACY",
                    "action_classes":[list(c) for c in classes],
                    "failed_class":list(target),
                    "tested_partitions":total_tested,
                    "maximum_blocks_per_quotient":maximum_blocks_per_quotient,
                }

            all_results.append({
                "action_class":list(target),
                "minimum_block_count":winning_blocks,
                "frontier_size":len(frontier),
                "frontier":[[list(block) for block in p] for p in frontier],
                "tested_by_block_count":tested_by_blocks,
                "obstruction_by_block_count":first_obstruction,
            })

        return {
            "status":"VERIFIED",
            "action_classes":[list(c) for c in classes],
            "quotient_class_count":len(all_results),
            "class_witnesses":all_results,
            "tested_partitions":total_tested,
            "undecomposed":False,
        }
