#!/usr/bin/env python3
"""Frozen V18 KT predictive evidence + monotone raw-accessor structural code."""
from __future__ import annotations

from dataclasses import dataclass, field
import itertools
import math
from typing import Any, Dict, Iterable, List, Optional, Sequence, Tuple

from basis import Accessor, StochasticWorld, partition, readout_digest


@dataclass(frozen=True)
class ReadoutCode:
    code_id: str
    interface_key: Tuple[Any, ...]
    accessors: Tuple[Accessor, ...]
    provenance: Tuple[str, ...]

    def data(self) -> Any:
        return {
            "code_id": self.code_id,
            "accessors": list(self.accessors),
            "provenance": list(self.provenance),
        }


@dataclass
class Usage:
    accessors: Tuple[Accessor, ...]
    origins: List[str] = field(default_factory=list)


class Kernel:
    def __init__(self):
        self.compiled: Dict[Tuple[Any, ...], ReadoutCode] = {}
        self.usage: Dict[Tuple[Any, ...], Usage] = {}

    @staticmethod
    def _authority(world: StochasticWorld) -> Optional[Dict[str, Any]]:
        if not world.complete:
            return {
                "status": "UNKNOWN_AUTHORITY",
                "reason": "stochastic_count_table_incomplete",
            }
        return None

    @staticmethod
    def _model_code_bits(m: int, k: int) -> float:
        # V18 structural MDL repair: each retained ACCESS token costs one
        # bit of present machinery. This is monotone in representation size,
        # has no fitted sparsity coefficient, and directly inherits V16's
        # one-unit-per-accessor structural objective.
        return float(k)

    @staticmethod
    def _kt_binary_code_bits(n0: int, n1: int) -> float:
        # Jeffreys / Krichevsky-Trofimov beta-binomial marginal code.
        # p(data counts | model cell), ignoring order because counts are the
        # sufficient statistic supplied by the authority.
        n0 = int(n0)
        n1 = int(n1)
        n = n0 + n1
        log_evidence = (
            math.lgamma(1.0)
            - math.lgamma(n + 1.0)
            + math.lgamma(n0 + 0.5)
            - math.lgamma(0.5)
            + math.lgamma(n1 + 0.5)
            - math.lgamma(0.5)
        )
        return -log_evidence / math.log(2.0)

    def score(
        self,
        world: StochasticWorld,
        accessors: Sequence[Accessor],
        statistical_enabled: bool = True,
    ) -> Dict[str, Any]:
        auth = self._authority(world)
        if auth:
            return auth
        if not statistical_enabled:
            return {
                "status": "UNKNOWN_NO_STATISTICAL_AUTHORITY",
            }

        aa = tuple(sorted(set(int(a) for a in accessors)))
        cells = partition(world, aa)

        data_bits = 0.0
        pooled = []
        for cls in cells:
            test_rows = []
            for t in range(len(world.future_tests)):
                n0 = sum(world.counts[i][t][0] for i in cls)
                n1 = sum(world.counts[i][t][1] for i in cls)
                bits = self._kt_binary_code_bits(n0, n1)
                data_bits += bits
                test_rows.append({
                    "counts": [n0, n1],
                    "code_bits": bits,
                })
            pooled.append({
                "contexts": list(cls),
                "tests": test_rows,
            })

        model_bits = self._model_code_bits(world.channel_count, len(aa))
        total = model_bits + data_bits

        return {
            "status": "VERIFIED",
            "accessors": list(aa),
            "cell_count": len(cells),
            "model_bits": model_bits,
            "data_bits": data_bits,
            "total_bits": total,
            "pooled": pooled,
        }

    def exhaustive_search(
        self,
        world: StochasticWorld,
        statistical_enabled: bool = True,
    ) -> Dict[str, Any]:
        auth = self._authority(world)
        if auth:
            return auth
        if not statistical_enabled:
            return {
                "status": "UNKNOWN_NO_STATISTICAL_AUTHORITY",
            }

        rows = []
        m = world.channel_count
        for k in range(m + 1):
            for subset in itertools.combinations(range(m), k):
                s = self.score(world, subset, statistical_enabled=True)
                rows.append(s)

        best_bits = min(r["total_bits"] for r in rows)
        eps = 1e-9
        minima = [
            r for r in rows
            if abs(r["total_bits"] - best_bits) <= eps
        ]
        minima.sort(key=lambda r: (len(r["accessors"]), r["accessors"]))

        empty = next(r for r in rows if r["accessors"] == [])
        growth_authorized = best_bits + eps < empty["total_bits"]

        return {
            "status": "VERIFIED",
            "tested_subset_count": len(rows),
            "best_total_bits": best_bits,
            "empty_total_bits": empty["total_bits"],
            "growth_authorized": growth_authorized,
            "minimum_codes": [
                {
                    "accessors": r["accessors"],
                    "total_bits": r["total_bits"],
                    "model_bits": r["model_bits"],
                    "data_bits": r["data_bits"],
                    "cell_count": r["cell_count"],
                }
                for r in minima
            ],
            "all_rows": rows,
        }

    @staticmethod
    def qualify_codes(
        candidate_codes: Sequence[Sequence[int]],
        qualification: StochasticWorld,
        helper: "Kernel",
    ) -> Dict[str, Any]:
        if not qualification.complete:
            return {"status": "UNKNOWN_AUTHORITY", "survivors": []}

        global_result = helper.exhaustive_search(qualification)
        if global_result.get("status") != "VERIFIED":
            return {
                "status": global_result.get("status"),
                "survivors": [],
            }

        best = global_result["best_total_bits"]
        eps = 1e-9
        rows = []
        survivors = []
        for code0 in candidate_codes:
            code = tuple(sorted(set(int(a) for a in code0)))
            s = helper.score(qualification, code)
            ok = abs(s["total_bits"] - best) <= eps
            rows.append({
                "accessors": list(code),
                "total_bits": s["total_bits"],
                "qualified": ok,
            })
            if ok:
                survivors.append(code)

        return {
            "status": "VERIFIED",
            "rows": rows,
            "survivors": [list(c) for c in survivors],
            "qualification_global": {
                "best_total_bits": best,
                "minimum_codes": global_result["minimum_codes"],
            },
        }

    def _record(
        self,
        request_id: str,
        world: StochasticWorld,
        accessors: Sequence[int],
    ) -> Optional[ReadoutCode]:
        code = tuple(sorted(set(int(a) for a in accessors)))
        interface = world.interface_key()
        key = (interface, code)
        u = self.usage.get(key)
        if u is None:
            u = Usage(code)
            self.usage[key] = u
        if request_id not in u.origins:
            u.origins.append(request_id)

        if len(u.origins) < 2:
            return None

        compiled = ReadoutCode(
            code_id="sr_" + readout_digest(world, code)[:16],
            interface_key=interface,
            accessors=code,
            provenance=tuple(u.origins),
        )
        self.compiled[interface] = compiled
        return compiled

    def ablate(self, world: StochasticWorld) -> bool:
        return self.compiled.pop(world.interface_key(), None) is not None

    def replay(
        self,
        request_id: str,
        world: StochasticWorld,
        code: ReadoutCode,
    ) -> Dict[str, Any]:
        auth = self._authority(world)
        if auth:
            return {"request_id": request_id, **auth, "route": "STOP"}

        if code.interface_key != world.interface_key():
            return {
                "request_id": request_id,
                "status": "TYPE_MISMATCH",
                "route": "STOP",
            }

        full = self.score(world, code.accessors)
        empty = self.score(world, ())
        eps = 1e-9
        deletion_scores = []
        for a in code.accessors:
            sub = tuple(x for x in code.accessors if x != a)
            s = self.score(world, sub)
            deletion_scores.append({
                "deleted": a,
                "accessors": list(sub),
                "total_bits": s["total_bits"],
            })

        strictly_beats_empty = full["total_bits"] + eps < empty["total_bits"]
        deletion_minimal = all(
            full["total_bits"] + eps < row["total_bits"]
            for row in deletion_scores
        )
        ok = strictly_beats_empty and deletion_minimal

        return {
            "request_id": request_id,
            "status": "VERIFIED" if ok else "REPLAY_FAILED",
            "route": "REPLAY_STOCHASTIC_READOUT",
            "accessors": list(code.accessors),
            "total_bits": full["total_bits"],
            "empty_total_bits": empty["total_bits"],
            "deletion_scores": deletion_scores,
            "acquisition_search_count": 0,
            "code": code.data(),
        }

    def solve(
        self,
        request_id: str,
        world: StochasticWorld,
        *,
        qualification: Optional[StochasticWorld] = None,
        allow_acquisition_search: bool = True,
        statistical_enabled: bool = True,
    ) -> Dict[str, Any]:
        auth = self._authority(world)
        if auth:
            return {"request_id": request_id, **auth, "route": "STOP"}

        retained = self.compiled.get(world.interface_key())
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

        search = self.exhaustive_search(
            world,
            statistical_enabled=statistical_enabled,
        )
        if search.get("status") != "VERIFIED":
            return {
                "request_id": request_id,
                "status": search.get("status"),
                "route": "DEVELOP",
                "search": search,
                "acquisition_search_count": 1,
                "failed_reuse": failed_reuse,
            }

        if not search["growth_authorized"]:
            return {
                "request_id": request_id,
                "status": "PROVISIONAL_NO_GROWTH",
                "route": "DEVELOP",
                "search": search,
                "accessors": [],
                "acquisition_search_count": 1,
                "failed_reuse": failed_reuse,
            }

        candidates = [
            tuple(int(a) for a in row["accessors"])
            for row in search["minimum_codes"]
        ]

        qualification_result = None
        selected = candidates
        if qualification is not None:
            qualification_result = self.qualify_codes(
                candidates,
                qualification,
                self,
            )
            if qualification_result.get("status") != "VERIFIED":
                return {
                    "request_id": request_id,
                    "status": qualification_result.get("status"),
                    "route": "DEVELOP",
                    "search": search,
                    "qualification": qualification_result,
                    "acquisition_search_count": 1,
                    "failed_reuse": failed_reuse,
                }
            selected = [
                tuple(int(a) for a in code)
                for code in qualification_result.get("survivors", [])
            ]

        if not selected:
            return {
                "request_id": request_id,
                "status": "CERTIFIED_FRONTIER_ELIMINATED",
                "route": "DEVELOP",
                "search": search,
                "qualification": qualification_result,
                "acquisition_search_count": 1,
                "failed_reuse": failed_reuse,
            }

        if len(selected) > 1:
            return {
                "request_id": request_id,
                "status": "VERIFIED_FRONTIER",
                "route": "DEVELOP",
                "selected_frontier": [list(c) for c in selected],
                "search": search,
                "qualification": qualification_result,
                "acquisition_search_count": 1,
                "failed_reuse": failed_reuse,
            }

        code = selected[0]
        promoted = self._record(request_id, world, code)
        score = self.score(world, code)

        return {
            "request_id": request_id,
            "status": "VERIFIED",
            "route": "DEVELOP",
            "accessors": list(code),
            "total_bits": score["total_bits"],
            "search": search,
            "qualification": qualification_result,
            "promoted_code": promoted.data() if promoted else None,
            "acquisition_search_count": 1,
            "failed_reuse": failed_reuse,
        }
