#!/usr/bin/env python3
"""Frozen V16 consequence-gated raw readout developmental kernel."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, Iterable, List, Optional, Sequence, Tuple

from basis import (
    Accessor,
    MultichannelWorld,
    future_partition,
    generated_accessors,
    partition,
    readout_cost,
    readout_digest,
    same_partition,
)


@dataclass(frozen=True)
class ReadoutCode:
    code_id: str
    interface_key: Tuple[Any, ...]
    accessors: Tuple[Accessor, ...]
    cost: Tuple[int, int]
    provenance: Tuple[str, ...]

    def data(self) -> Any:
        return {
            "code_id": self.code_id,
            "accessors": [list(a) for a in self.accessors],
            "cost": list(self.cost),
            "provenance": list(self.provenance),
        }


@dataclass
class ReadoutUsage:
    accessors: Tuple[Accessor, ...]
    origins: List[str] = field(default_factory=list)


class Kernel:
    def __init__(self):
        self.compiled_codes: Dict[Tuple[Any, ...], ReadoutCode] = {}
        self.usage: Dict[Tuple[Any, ...], ReadoutUsage] = {}

    @staticmethod
    def _require_complete(world: MultichannelWorld) -> Optional[Dict[str, Any]]:
        if not world.complete:
            return {
                "status": "UNKNOWN_AUTHORITY",
                "reason": "future_consequence_table_incomplete",
            }
        return None

    @staticmethod
    def _is_complete(world: MultichannelWorld, accessors: Iterable[Accessor]) -> bool:
        return same_partition(
            partition(world, accessors),
            future_partition(world),
        )

    @staticmethod
    def _first_obstruction(
        world: MultichannelWorld,
        accessors: Iterable[Accessor],
    ) -> Optional[Tuple[int, int]]:
        current = partition(world, accessors)
        target = future_partition(world)
        target_class = {}
        for cid, cls in enumerate(target):
            for i in cls:
                target_class[i] = cid

        for cls in current:
            for p in range(len(cls)):
                for q in range(p + 1, len(cls)):
                    i, j = cls[p], cls[q]
                    if target_class[i] != target_class[j]:
                        return i, j
        return None

    def minimum_codes_at_lag(
        self,
        world: MultichannelWorld,
        authorized_lag: int,
        accessor_enabled: bool = True,
    ) -> Dict[str, Any]:
        auth = self._require_complete(world)
        if auth:
            return auth
        if not accessor_enabled:
            return {
                "status": "UNKNOWN_NO_ACCESSOR_LANGUAGE",
                "authorized_lag": authorized_lag,
            }

        accessors = generated_accessors(world, authorized_lag)
        reps = tuple(cls[0] for cls in future_partition(world))
        pairs = [
            (reps[i], reps[j])
            for i in range(len(reps))
            for j in range(i + 1, len(reps))
        ]
        target_mask = (1 << len(pairs)) - 1

        if target_mask == 0:
            return {
                "status": "VERIFIED",
                "authorized_lag": authorized_lag,
                "minimum_codes": [{"accessors": [], "cost": [0, 0]}],
                "accessor_count": len(accessors),
                "pair_count": 0,
            }

        entries = []
        for a in accessors:
            mask = 0
            for bit, (i, j) in enumerate(pairs):
                if world.accessor_value(i, a) != world.accessor_value(j, a):
                    mask |= 1 << bit
            if mask:
                entries.append((a, mask, world.accessor_cost(a)))

        # Exact dynamic programming over pair-coverage masks.
        # Store all equal-cost target solutions, one best representative per
        # intermediate mask.
        best: Dict[int, Tuple[int, int, Tuple[Accessor, ...]]] = {
            0: (0, 0, tuple())
        }

        for accessor, amask, acost in entries:
            snapshot = list(best.items())
            for mask, (count, total_cost, code) in snapshot:
                if accessor in code:
                    continue
                new_code = tuple(sorted(code + (accessor,)))
                cand = (
                    len(new_code),
                    sum(world.accessor_cost(a) for a in new_code),
                    new_code,
                )
                new_mask = mask | amask
                old = best.get(new_mask)
                if old is None or cand[:2] < old[:2] or (
                    cand[:2] == old[:2] and cand[2] < old[2]
                ):
                    best[new_mask] = cand

        if target_mask not in best:
            return {
                "status": "CERTIFIED_READOUT_INADEQUACY",
                "authorized_lag": authorized_lag,
                "accessor_count": len(accessors),
                "pair_count": len(pairs),
            }

        count, total_cost, canonical = best[target_mask]

        # Enumerate all globally equal-cost solutions for the target at the
        # typically small declared bounds, so non-canonicity is preserved.
        minima: List[Tuple[Accessor, ...]] = []
        n = len(accessors)
        from itertools import combinations
        for k in range(count, count + 1):
            for subset in combinations(accessors, k):
                if sum(world.accessor_cost(a) for a in subset) != total_cost:
                    continue
                if self._is_complete(world, subset):
                    minima.append(tuple(sorted(subset)))

        minima = sorted(set(minima))

        return {
            "status": "VERIFIED",
            "authorized_lag": authorized_lag,
            "accessor_count": len(accessors),
            "pair_count": len(pairs),
            "minimum_codes": [
                {
                    "accessors": [list(a) for a in code],
                    "cost": [count, total_cost],
                    "partition": [list(c) for c in partition(world, code)],
                }
                for code in minima
            ],
            "canonical_code": [list(a) for a in canonical],
            "lower_bound": {
                "minimum_accessor_count": count,
                "minimum_total_accessor_cost": total_cost,
            },
        }

    def developmental_search(
        self,
        world: MultichannelWorld,
        *,
        accessor_enabled: bool = True,
        consequence_enabled: bool = True,
    ) -> Dict[str, Any]:
        auth = self._require_complete(world)
        if auth:
            return auth

        if not consequence_enabled:
            return {
                "status": "UNKNOWN_NO_CONSEQUENCE_AUTHORITY",
                "initial_class_count": 1,
                "authorized_lag": 0,
                "generations": [],
            }

        if not accessor_enabled:
            return {
                "status": "UNKNOWN_NO_ACCESSOR_LANGUAGE",
                "initial_class_count": 1,
                "authorized_lag": 0,
                "generations": [],
            }

        generations = []
        for lag in range(world.max_lag + 1):
            result = self.minimum_codes_at_lag(
                world,
                lag,
                accessor_enabled=accessor_enabled,
            )
            obstruction = self._first_obstruction(world, tuple())
            row = {
                "authorized_lag": lag,
                "status": result.get("status"),
                "minimum_search": result,
                "empty_readout_obstruction": (
                    list(obstruction) if obstruction is not None else None
                ),
            }
            generations.append(row)

            if result.get("status") == "VERIFIED":
                return {
                    "status": "VERIFIED",
                    "initial_class_count": 1,
                    "selected_lag": lag,
                    "generations": generations,
                    "minimum_search": result,
                }

            if result.get("status") != "CERTIFIED_READOUT_INADEQUACY":
                return {
                    "status": result.get("status"),
                    "initial_class_count": 1,
                    "selected_lag": lag,
                    "generations": generations,
                }

        return {
            "status": "CERTIFIED_READOUT_INADEQUACY",
            "initial_class_count": 1,
            "selected_lag": world.max_lag,
            "generations": generations,
        }

    @staticmethod
    def qualify_codes(
        candidate_codes: Sequence[Sequence[Sequence[int]]],
        qualification: MultichannelWorld,
    ) -> Dict[str, Any]:
        if not qualification.complete:
            return {"status": "UNKNOWN_AUTHORITY", "survivors": []}

        survivors = []
        rows = []
        for code0 in candidate_codes:
            code = tuple(sorted((int(a[0]), int(a[1])) for a in code0))
            ok = same_partition(
                partition(qualification, code),
                future_partition(qualification),
            )
            rows.append({
                "accessors": [list(a) for a in code],
                "qualified": ok,
            })
            if ok:
                survivors.append(code)

        return {
            "status": "VERIFIED",
            "rows": rows,
            "survivors": [
                [list(a) for a in code]
                for code in survivors
            ],
        }

    def _record(
        self,
        request_id: str,
        world: MultichannelWorld,
        code: Sequence[Accessor],
    ) -> Optional[ReadoutCode]:
        accessors = tuple(sorted(set((int(l), int(c)) for l, c in code)))
        interface = world.interface_key()
        key = (interface, accessors)
        u = self.usage.get(key)
        if u is None:
            u = ReadoutUsage(accessors)
            self.usage[key] = u
        if request_id not in u.origins:
            u.origins.append(request_id)

        if len(u.origins) < 2:
            return None

        compiled = ReadoutCode(
            code_id="rd_" + readout_digest(world, accessors)[:16],
            interface_key=interface,
            accessors=accessors,
            cost=readout_cost(world, accessors),
            provenance=tuple(u.origins),
        )
        self.compiled_codes[interface] = compiled
        return compiled

    def ablate_compiled_code(self, world: MultichannelWorld) -> bool:
        return self.compiled_codes.pop(world.interface_key(), None) is not None

    def replay(
        self,
        request_id: str,
        world: MultichannelWorld,
        code: ReadoutCode,
    ) -> Dict[str, Any]:
        auth = self._require_complete(world)
        if auth:
            return {"request_id": request_id, **auth, "route": "STOP"}

        if code.interface_key != world.interface_key():
            return {
                "request_id": request_id,
                "status": "TYPE_MISMATCH",
                "route": "STOP",
            }

        ok = self._is_complete(world, code.accessors)
        return {
            "request_id": request_id,
            "status": "VERIFIED" if ok else "REPLAY_FAILED",
            "route": "REPLAY_READOUT",
            "accessors": [list(a) for a in code.accessors],
            "partition": [list(c) for c in partition(world, code.accessors)],
            "future_partition": [list(c) for c in future_partition(world)],
            "acquisition_search_count": 0,
            "code": code.data(),
        }

    def solve(
        self,
        request_id: str,
        world: MultichannelWorld,
        *,
        qualification: Optional[MultichannelWorld] = None,
        allow_acquisition_search: bool = True,
        accessor_enabled: bool = True,
        consequence_enabled: bool = True,
    ) -> Dict[str, Any]:
        auth = self._require_complete(world)
        if auth:
            return {"request_id": request_id, **auth, "route": "STOP"}

        retained = self.compiled_codes.get(world.interface_key())
        failed_reuse = None
        if retained is not None:
            replay = self.replay(request_id, world, retained)
            if replay.get("status") == "VERIFIED":
                self._record(request_id, world, retained.accessors)
                return {
                    **replay,
                    "route": "REUSE_COMPILED_READOUT",
                    "failed_reuse": None,
                }
            failed_reuse = replay

        if not allow_acquisition_search:
            return {
                "request_id": request_id,
                "status": "UNKNOWN_READOUT",
                "route": "STOP",
                "acquisition_search_count": 0,
                "failed_reuse": failed_reuse,
            }

        developmental = self.developmental_search(
            world,
            accessor_enabled=accessor_enabled,
            consequence_enabled=consequence_enabled,
        )
        if developmental.get("status") != "VERIFIED":
            return {
                "request_id": request_id,
                "status": developmental.get("status"),
                "route": "DEVELOP",
                "developmental": developmental,
                "acquisition_search_count": 1,
                "failed_reuse": failed_reuse,
            }

        minimum = developmental["minimum_search"]
        candidates = [
            tuple((int(a[0]), int(a[1])) for a in row["accessors"])
            for row in minimum.get("minimum_codes", [])
        ]

        qualification_result = None
        selected = candidates
        if qualification is not None:
            qualification_result = self.qualify_codes(
                [
                    [list(a) for a in code]
                    for code in candidates
                ],
                qualification,
            )
            if qualification_result.get("status") != "VERIFIED":
                return {
                    "request_id": request_id,
                    "status": qualification_result.get("status"),
                    "route": "DEVELOP",
                    "developmental": developmental,
                    "qualification": qualification_result,
                    "acquisition_search_count": 1,
                    "failed_reuse": failed_reuse,
                }
            selected = [
                tuple((int(a[0]), int(a[1])) for a in code)
                for code in qualification_result.get("survivors", [])
            ]

        if not selected:
            return {
                "request_id": request_id,
                "status": "CERTIFIED_FRONTIER_ELIMINATED",
                "route": "DEVELOP",
                "developmental": developmental,
                "qualification": qualification_result,
                "acquisition_search_count": 1,
                "failed_reuse": failed_reuse,
            }

        if len(selected) > 1:
            return {
                "request_id": request_id,
                "status": "VERIFIED_FRONTIER",
                "route": "DEVELOP",
                "selected_frontier": [
                    [list(a) for a in code]
                    for code in selected
                ],
                "selected_lag": developmental.get("selected_lag"),
                "developmental": developmental,
                "qualification": qualification_result,
                "acquisition_search_count": 1,
                "failed_reuse": failed_reuse,
            }

        code = selected[0]
        promoted = self._record(request_id, world, code)
        return {
            "request_id": request_id,
            "status": "VERIFIED",
            "route": "DEVELOP",
            "accessors": [list(a) for a in code],
            "cost": list(readout_cost(world, code)),
            "selected_lag": developmental.get("selected_lag"),
            "partition": [list(c) for c in partition(world, code)],
            "future_partition": [list(c) for c in future_partition(world)],
            "developmental": developmental,
            "qualification": qualification_result,
            "promoted_code": promoted.data() if promoted else None,
            "acquisition_search_count": 1,
            "failed_reuse": failed_reuse,
        }
