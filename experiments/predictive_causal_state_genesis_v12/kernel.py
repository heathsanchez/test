#!/usr/bin/env python3
"""Frozen V12 developmental kernel for predictive causal-state genesis.

No domain feature extractor exists here. The only lawful split predicate is:
does some admitted future intervention test produce a different verified
future observation consequence?
"""
from __future__ import annotations

from dataclasses import dataclass, field
import itertools
from typing import Any, Dict, Iterable, List, Mapping, Optional, Sequence, Tuple

from basis import (
    ConsequenceTable,
    code_cost,
    code_digest,
    full_partition,
    partition,
    same_partition,
    signature,
)


@dataclass(frozen=True)
class PredictiveCode:
    code_id: str
    interface_key: Tuple[Any, ...]
    active_test_indices: Tuple[int, ...]
    cost: Tuple[int, int]
    provenance: Tuple[str, ...]

    def data(self) -> Any:
        return {
            "code_id": self.code_id,
            "active_test_indices": list(self.active_test_indices),
            "cost": list(self.cost),
            "provenance": list(self.provenance),
        }


@dataclass
class CodeUsage:
    active_test_indices: Tuple[int, ...]
    origins: List[str] = field(default_factory=list)


class Kernel:
    def __init__(self):
        self.compiled_codes: Dict[Tuple[Any, ...], PredictiveCode] = {}
        self.code_usage: Dict[Tuple[Any, ...], CodeUsage] = {}

    # ------------------------------------------------------------------
    # Authority / verification
    # ------------------------------------------------------------------

    @staticmethod
    def _require_complete(table: ConsequenceTable) -> Optional[Dict[str, Any]]:
        if not table.complete:
            return {
                "status": "UNKNOWN_AUTHORITY",
                "reason": "future_consequence_table_incomplete",
            }
        return None

    @staticmethod
    def _is_complete_code(
        table: ConsequenceTable,
        active: Iterable[int],
    ) -> bool:
        return same_partition(
            partition(table, active),
            full_partition(table),
        )

    @staticmethod
    def _first_obstruction(
        table: ConsequenceTable,
        active: Iterable[int],
    ) -> Optional[Dict[str, Any]]:
        active = tuple(sorted(set(int(i) for i in active)))
        current = partition(table, active)
        full = full_partition(table)

        # Map history -> full-class id.
        full_class_of: Dict[int, int] = {}
        for cid, cls in enumerate(full):
            for i in cls:
                full_class_of[i] = cid

        # Find first current class that improperly merges different full states.
        for cls in current:
            for p in range(len(cls)):
                for q in range(p + 1, len(cls)):
                    i, j = cls[p], cls[q]
                    if full_class_of[i] != full_class_of[j]:
                        separators = []
                        for tid in range(len(table.tests)):
                            if tid in active:
                                continue
                            oi = table.outcome(i, tid)
                            oj = table.outcome(j, tid)
                            if oi != oj:
                                separators.append(tid)
                        return {
                            "history_pair": [i, j],
                            "current_signature": [
                                list(x)
                                for x in signature(table, i, active)
                            ],
                            "separator_test_indices": separators,
                            "separator_test_lengths": [
                                table.test_cost(t) for t in separators
                            ],
                            "witness_outcomes": {
                                str(t): [
                                    list(table.outcome(i, t)),
                                    list(table.outcome(j, t)),
                                ]
                                for t in separators
                            },
                        }
        return None

    # ------------------------------------------------------------------
    # Minimal code search
    # ------------------------------------------------------------------

    @staticmethod
    def _pareto_minimal(
        rows: Sequence[Tuple[Tuple[int, ...], Tuple[int, int]]],
    ) -> List[Tuple[Tuple[int, ...], Tuple[int, int]]]:
        out = []
        for code, cost in rows:
            dominated = False
            for other, ocost in rows:
                if other == code:
                    continue
                if (
                    ocost[0] <= cost[0]
                    and ocost[1] <= cost[1]
                    and ocost != cost
                ):
                    dominated = True
                    break
            if not dominated:
                out.append((code, cost))
        out.sort(key=lambda x: (x[1], x[0]))
        return out

    def exhaustive_minimum_codes(
        self,
        table: ConsequenceTable,
    ) -> Dict[str, Any]:
        auth = self._require_complete(table)
        if auth:
            return auth

        n = len(table.tests)
        complete_rows: List[Tuple[Tuple[int, ...], Tuple[int, int]]] = []
        tested = 0

        for mask in range(1 << n):
            ids = tuple(i for i in range(n) if mask & (1 << i))
            tested += 1
            if self._is_complete_code(table, ids):
                complete_rows.append((ids, code_cost(table, ids)))

        if not complete_rows:
            return {
                "status": "CERTIFIED_NO_COMPLETE_CODE_IN_DECLARED_UNIVERSE",
                "tested_subsets": tested,
            }

        minima = self._pareto_minimal(complete_rows)

        # Inclusion-minimal filter as an independent control.
        inclusion_minimal = []
        complete_sets = [set(code) for code, _ in complete_rows]
        for code, cost in complete_rows:
            s = set(code)
            if not any(t < s for t in complete_sets):
                inclusion_minimal.append((code, cost))
        inclusion_minimal.sort(key=lambda x: (x[1], x[0]))

        return {
            "status": "VERIFIED",
            "tested_subsets": tested,
            "complete_code_count": len(complete_rows),
            "pareto_minimal_codes": [
                {
                    "active_test_indices": list(code),
                    "cost": list(cost),
                    "partition": [
                        list(c) for c in partition(table, code)
                    ],
                }
                for code, cost in minima
            ],
            "inclusion_minimal_codes": [
                {
                    "active_test_indices": list(code),
                    "cost": list(cost),
                }
                for code, cost in inclusion_minimal
            ],
        }

    # ------------------------------------------------------------------
    # Developmental algorithm
    # ------------------------------------------------------------------

    def developmental_frontier(
        self,
        table: ConsequenceTable,
        consequence_enabled: bool = True,
        max_generations: Optional[int] = None,
    ) -> Dict[str, Any]:
        auth = self._require_complete(table)
        if auth:
            return auth

        if not consequence_enabled:
            return {
                "status": "UNKNOWN_NO_CONSEQUENCE_AUTHORITY",
                "initial_class_count": 1,
                "frontier": [[]],
                "generations": [],
            }

        if max_generations is None:
            max_generations = len(table.tests)

        frontier = {tuple()}
        generations: List[Dict[str, Any]] = []

        for generation in range(int(max_generations) + 1):
            # Behavior quotient of codes: if they induce exactly the same current
            # partition, keep the lower-cost / lexicographically first code.
            by_partition: Dict[Tuple[Tuple[int, ...], ...], Tuple[int, ...]] = {}
            for code in sorted(frontier):
                p = partition(table, code)
                old = by_partition.get(p)
                if old is None:
                    by_partition[p] = code
                else:
                    if (code_cost(table, code), code) < (
                        code_cost(table, old),
                        old,
                    ):
                        by_partition[p] = code

            frontier = set(by_partition.values())

            complete_codes = [
                code for code in frontier
                if self._is_complete_code(table, code)
            ]

            gen_record: Dict[str, Any] = {
                "generation": generation,
                "frontier_size": len(frontier),
                "frontier_codes": [list(c) for c in sorted(frontier)],
                "frontier_class_counts": [
                    len(partition(table, c)) for c in sorted(frontier)
                ],
                "complete_codes": [list(c) for c in sorted(complete_codes)],
                "repairs": [],
            }

            if complete_codes:
                generations.append(gen_record)
                return {
                    "status": "VERIFIED",
                    "initial_class_count": 1,
                    "final_generation": generation,
                    "frontier": [list(c) for c in sorted(frontier)],
                    "complete_frontier_codes": [
                        list(c) for c in sorted(complete_codes)
                    ],
                    "generations": generations,
                }

            next_frontier = set()

            for code in sorted(frontier):
                obs = self._first_obstruction(table, code)
                if obs is None:
                    continue

                separators = obs["separator_test_indices"]
                if not separators:
                    generations.append(gen_record)
                    return {
                        "status": "CERTIFIED_EXPRESSIVE_INADEQUACY",
                        "initial_class_count": 1,
                        "stuck_code": list(code),
                        "obstruction": obs,
                        "generations": generations,
                    }

                min_len = min(table.test_cost(t) for t in separators)
                minimal_separators = [
                    t for t in separators
                    if table.test_cost(t) == min_len
                ]

                repair_row = {
                    "code": list(code),
                    "obstruction": obs,
                    "minimal_separator_test_indices": minimal_separators,
                    "minimal_separator_length": min_len,
                    "candidate_extensions": [],
                }

                for t in minimal_separators:
                    new_code = tuple(sorted(set(code) | {t}))
                    next_frontier.add(new_code)
                    repair_row["candidate_extensions"].append(list(new_code))

                gen_record["repairs"].append(repair_row)

            generations.append(gen_record)

            if not next_frontier:
                return {
                    "status": "UNKNOWN_SEARCH",
                    "initial_class_count": 1,
                    "generations": generations,
                }

            frontier = next_frontier

        return {
            "status": "UNKNOWN_SEARCH",
            "initial_class_count": 1,
            "generations": generations,
        }

    # ------------------------------------------------------------------
    # Qualification / selection / compile / replay
    # ------------------------------------------------------------------

    @staticmethod
    def qualify_codes(
        candidate_codes: Sequence[Sequence[int]],
        qualification: ConsequenceTable,
    ) -> Dict[str, Any]:
        if not qualification.complete:
            return {
                "status": "UNKNOWN_AUTHORITY",
                "survivors": [],
            }

        rows = []
        survivors = []
        for code0 in candidate_codes:
            code = tuple(sorted(set(int(x) for x in code0)))
            ok = same_partition(
                partition(qualification, code),
                full_partition(qualification),
            )
            rows.append({
                "active_test_indices": list(code),
                "qualified": ok,
                "partition": [
                    list(c) for c in partition(qualification, code)
                ],
            })
            if ok:
                survivors.append(code)

        return {
            "status": "VERIFIED",
            "rows": rows,
            "survivors": [list(c) for c in survivors],
        }

    def _record_code(
        self,
        request_id: str,
        table: ConsequenceTable,
        active_test_indices: Sequence[int],
    ) -> Optional[PredictiveCode]:
        ids = tuple(sorted(set(int(x) for x in active_test_indices)))
        interface = table.interface_key()
        usage_key = (interface, ids)

        u = self.code_usage.get(usage_key)
        if u is None:
            u = CodeUsage(ids)
            self.code_usage[usage_key] = u

        if request_id not in u.origins:
            u.origins.append(request_id)

        if len(u.origins) < 2:
            return None

        code = PredictiveCode(
            code_id="pc_" + code_digest(table, ids)[:16],
            interface_key=interface,
            active_test_indices=ids,
            cost=code_cost(table, ids),
            provenance=tuple(u.origins),
        )
        self.compiled_codes[interface] = code
        return code

    def ablate_compiled_code(
        self,
        table: ConsequenceTable,
    ) -> bool:
        return self.compiled_codes.pop(table.interface_key(), None) is not None

    def replay_code(
        self,
        request_id: str,
        table: ConsequenceTable,
        code: PredictiveCode,
    ) -> Dict[str, Any]:
        auth = self._require_complete(table)
        if auth:
            return {
                "request_id": request_id,
                **auth,
                "route": "STOP",
            }

        if code.interface_key != table.interface_key():
            return {
                "request_id": request_id,
                "status": "TYPE_MISMATCH",
                "route": "STOP",
            }

        p = partition(table, code.active_test_indices)
        target = full_partition(table)
        ok = same_partition(p, target)

        return {
            "request_id": request_id,
            "status": "VERIFIED" if ok else "REPLAY_FAILED",
            "route": "REPLAY_CODE",
            "active_test_indices": list(code.active_test_indices),
            "partition": [list(c) for c in p],
            "full_partition": [list(c) for c in target],
            "acquisition_search_count": 0,
            "code": code.data(),
        }

    def solve(
        self,
        request_id: str,
        table: ConsequenceTable,
        qualification: Optional[ConsequenceTable] = None,
        allow_acquisition_search: bool = True,
        consequence_enabled: bool = True,
    ) -> Dict[str, Any]:
        auth = self._require_complete(table)
        if auth:
            return {
                "request_id": request_id,
                **auth,
                "route": "STOP",
            }

        interface = table.interface_key()
        retained = self.compiled_codes.get(interface)
        failed_reuse = None

        if retained is not None:
            replay = self.replay_code(request_id, table, retained)
            if replay.get("status") == "VERIFIED":
                self._record_code(
                    request_id,
                    table,
                    retained.active_test_indices,
                )
                return {
                    **replay,
                    "route": "REUSE_COMPILED_CODE",
                    "failed_reuse": None,
                }
            failed_reuse = replay

        if not allow_acquisition_search:
            return {
                "request_id": request_id,
                "status": "UNKNOWN_CODE",
                "route": "STOP",
                "acquisition_search_count": 0,
                "failed_reuse": failed_reuse,
            }

        developmental = self.developmental_frontier(
            table,
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

        minimum = self.exhaustive_minimum_codes(table)
        if minimum.get("status") != "VERIFIED":
            return {
                "request_id": request_id,
                "status": minimum.get("status"),
                "route": "DEVELOP",
                "developmental": developmental,
                "minimum_search": minimum,
                "acquisition_search_count": 1,
                "failed_reuse": failed_reuse,
            }

        candidates = [
            tuple(row["active_test_indices"])
            for row in minimum["pareto_minimal_codes"]
        ]

        qualification_result = None
        selected = candidates

        if qualification is not None:
            qualification_result = self.qualify_codes(
                candidates,
                qualification,
            )
            if qualification_result.get("status") != "VERIFIED":
                return {
                    "request_id": request_id,
                    "status": qualification_result.get("status"),
                    "route": "DEVELOP",
                    "developmental": developmental,
                    "minimum_search": minimum,
                    "qualification": qualification_result,
                    "acquisition_search_count": 1,
                    "failed_reuse": failed_reuse,
                }
            selected = [
                tuple(x)
                for x in qualification_result.get("survivors", [])
            ]

        if not selected:
            return {
                "request_id": request_id,
                "status": "CERTIFIED_FRONTIER_ELIMINATED",
                "route": "DEVELOP",
                "developmental": developmental,
                "minimum_search": minimum,
                "qualification": qualification_result,
                "acquisition_search_count": 1,
                "failed_reuse": failed_reuse,
            }

        # If qualification leaves several equal lawful minima, preserve them.
        if len(selected) > 1:
            return {
                "request_id": request_id,
                "status": "VERIFIED_FRONTIER",
                "route": "DEVELOP",
                "selected_frontier": [list(c) for c in selected],
                "developmental": developmental,
                "minimum_search": minimum,
                "qualification": qualification_result,
                "acquisition_search_count": 1,
                "failed_reuse": failed_reuse,
            }

        ids = selected[0]
        promoted = self._record_code(request_id, table, ids)

        return {
            "request_id": request_id,
            "status": "VERIFIED",
            "route": "DEVELOP",
            "active_test_indices": list(ids),
            "cost": list(code_cost(table, ids)),
            "partition": [list(c) for c in partition(table, ids)],
            "full_partition": [list(c) for c in full_partition(table)],
            "developmental": developmental,
            "minimum_search": minimum,
            "qualification": qualification_result,
            "promoted_code": promoted.data() if promoted else None,
            "acquisition_search_count": 1,
            "failed_reuse": failed_reuse,
        }
