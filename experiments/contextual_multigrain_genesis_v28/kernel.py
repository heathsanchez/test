#!/usr/bin/env python3
"""Frozen V28 contextual multigrain kernel."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Optional, Tuple

from basis import (
    MultiContextWorld,
    Partition,
    all_partitions,
    block_count,
    block_size_signature,
    incomparable,
    partition_from_signatures,
    record_lawful,
    refines,
    sufficient,
)


@dataclass(frozen=True)
class Grain:
    partition: Partition
    contexts: Tuple[int, ...]

    def data(self) -> Any:
        return {
            "partition": [list(b) for b in self.partition],
            "contexts": list(self.contexts),
            "block_count": block_count(self.partition),
            "block_size_signature": list(block_size_signature(self.partition)),
        }


class Kernel:
    @staticmethod
    def _authority(world: MultiContextWorld) -> Optional[Dict[str, Any]]:
        if not world.complete:
            return {
                "status": "UNKNOWN_AUTHORITY",
                "reason": "contextual consequence or record authority incomplete",
            }
        return None

    @staticmethod
    def _all_partitions(world: MultiContextWorld) -> Tuple[Partition, ...]:
        return tuple(all_partitions(world.state_count))

    def analyze_context(
        self,
        world: MultiContextWorld,
        context_index: int,
        *,
        consequence_enabled: bool = True,
    ) -> Dict[str, Any]:
        auth = self._authority(world)
        if auth:
            return auth
        if not consequence_enabled:
            return {
                "status": "UNKNOWN_NO_CONSEQUENCE_AUTHORITY",
                "tested_partition_count": 0,
            }

        partitions = self._all_partitions(world)
        sigs = world.future_signatures[context_index]
        sufficient_rows = [p for p in partitions if sufficient(p, sigs)]
        min_blocks = min(block_count(p) for p in sufficient_rows)
        minima = tuple(
            sorted(
                (p for p in sufficient_rows if block_count(p) == min_blocks),
                key=lambda p: p,
            )
        )

        record_rows = None
        q_record = None
        admissible = None
        if world.record_signatures is not None:
            record_sigs = world.record_signatures[context_index]
            q_record = partition_from_signatures(record_sigs)
            record_rows = [
                p for p in partitions if record_lawful(p, record_sigs)
            ]
            admissible = [
                p
                for p in sufficient_rows
                if record_lawful(p, record_sigs)
            ]

        return {
            "status": "VERIFIED",
            "context_index": int(context_index),
            "context_name": world.context_names[context_index],
            "tested_partition_count": len(partitions),
            "sufficient_partition_count": len(sufficient_rows),
            "minimum_block_count": min_blocks,
            "minimum_partitions": [
                [list(b) for b in p] for p in minima
            ],
            "_minimum_partitions": minima,
            "direct_signature_partition": [
                list(b) for b in partition_from_signatures(sigs)
            ],
            "record_partition": (
                [list(b) for b in q_record]
                if q_record is not None else None
            ),
            "record_lawful_partition_count": (
                len(record_rows) if record_rows is not None else None
            ),
            "admissible_interval_count": (
                len(admissible) if admissible is not None else None
            ),
            "admissible_partitions": (
                [[list(b) for b in p] for p in admissible]
                if admissible is not None else None
            ),
            "_record_partition": q_record,
            "_admissible": tuple(admissible) if admissible is not None else None,
        }

    def analyze_global(
        self,
        world: MultiContextWorld,
        context_indices: Tuple[int, ...],
        *,
        consequence_enabled: bool = True,
    ) -> Dict[str, Any]:
        auth = self._authority(world)
        if auth:
            return auth
        if not consequence_enabled:
            return {
                "status": "UNKNOWN_NO_CONSEQUENCE_AUTHORITY",
                "tested_partition_count": 0,
            }

        partitions = self._all_partitions(world)
        joint = tuple(
            tuple(
                item
                for ci in context_indices
                for item in world.future_signatures[ci][state]
            )
            for state in range(world.state_count)
        )
        sufficient_rows = [p for p in partitions if sufficient(p, joint)]
        min_blocks = min(block_count(p) for p in sufficient_rows)
        minima = tuple(
            sorted(
                (p for p in sufficient_rows if block_count(p) == min_blocks),
                key=lambda p: p,
            )
        )

        return {
            "status": "VERIFIED",
            "context_indices": list(context_indices),
            "tested_partition_count": len(partitions),
            "minimum_block_count": min_blocks,
            "minimum_partitions": [
                [list(b) for b in p] for p in minima
            ],
            "_minimum_partitions": minima,
        }

    def build_multigrain(
        self,
        world: MultiContextWorld,
        *,
        consequence_enabled: bool = True,
    ) -> Dict[str, Any]:
        auth = self._authority(world)
        if auth:
            return auth
        if not consequence_enabled:
            return {
                "status": "UNKNOWN_NO_CONSEQUENCE_AUTHORITY",
                "grains": [],
            }

        context_rows = [
            self.analyze_context(
                world,
                ci,
                consequence_enabled=True,
            )
            for ci in range(len(world.context_names))
        ]

        if any(row.get("status") != "VERIFIED" for row in context_rows):
            return {
                "status": "UNKNOWN_CONTEXT_ANALYSIS",
                "contexts": context_rows,
            }

        # Coarsest sufficient partition is unique for exact signatures.
        grain_by_partition: Dict[Partition, list[int]] = {}
        active_by_context: Dict[int, Partition] = {}

        for ci, row in enumerate(context_rows):
            minima = row["_minimum_partitions"]
            if len(minima) != 1:
                return {
                    "status": "NONCANONICAL_MINIMUM_FRONTIER",
                    "contexts": context_rows,
                }
            p = minima[0]
            active_by_context[ci] = p
            grain_by_partition.setdefault(p, []).append(ci)

        grains = tuple(
            Grain(partition=p, contexts=tuple(contexts))
            for p, contexts in sorted(
                grain_by_partition.items(),
                key=lambda item: item[0],
            )
        )

        global_row = self.analyze_global(
            world,
            tuple(range(len(world.context_names))),
            consequence_enabled=True,
        )

        pairwise = []
        for i in range(len(world.context_names)):
            for j in range(i + 1, len(world.context_names)):
                a = active_by_context[i]
                b = active_by_context[j]
                pairwise.append({
                    "contexts": [i, j],
                    "a_refines_b": refines(a, b),
                    "b_refines_a": refines(b, a),
                    "incomparable": incomparable(a, b),
                })

        return {
            "status": "VERIFIED",
            "tested_partition_count_per_context": context_rows[0][
                "tested_partition_count"
            ] if context_rows else 0,
            "contexts": [
                {k: v for k, v in row.items() if not k.startswith("_")}
                for row in context_rows
            ],
            "grains": [g.data() for g in grains],
            "grain_count": len(grains),
            "active_block_counts": {
                str(ci): block_count(p)
                for ci, p in active_by_context.items()
            },
            "global": {
                k: v for k, v in global_row.items()
                if not k.startswith("_")
            },
            "pairwise": pairwise,
            "_active_by_context": active_by_context,
            "_grains": grains,
            "_global": global_row,
        }

    def update_one_context(
        self,
        old_world: MultiContextWorld,
        new_world: MultiContextWorld,
        changed_context: int,
    ) -> Dict[str, Any]:
        old = self.build_multigrain(old_world)
        new = self.build_multigrain(new_world)

        if old.get("status") != "VERIFIED" or new.get("status") != "VERIFIED":
            return {
                "status": "UNKNOWN_UPDATE",
                "old": old,
                "new": new,
            }

        preserved = {}
        changed = {}
        for ci in range(len(old_world.context_names)):
            po = old["_active_by_context"][ci]
            pn = new["_active_by_context"][ci]
            if ci == changed_context:
                changed[str(ci)] = {
                    "old": [list(b) for b in po],
                    "new": [list(b) for b in pn],
                    "changed": po != pn,
                    "refined": refines(pn, po),
                }
            else:
                preserved[str(ci)] = po == pn

        return {
            "status": "VERIFIED",
            "changed_context": changed_context,
            "changed": changed,
            "unrelated_preserved": preserved,
            "_old": old,
            "_new": new,
        }
