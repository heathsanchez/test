#!/usr/bin/env python3
"""Frozen V9 developmental analyzer using only finite relations + COMPOSE.

The kernel searches for least identity-return exponents, constructs
consequence-relative future-trace equivalence classes, and may compile a
verified return hypothesis for later direct replay.  It does not contain
frequency/phase/cycle primitives.
"""
from __future__ import annotations

from dataclasses import dataclass, field
import hashlib
import json
from typing import Any, Dict, List, Optional, Sequence, Tuple

from basis import (
    BasisConfig,
    Carrier,
    FunctionRelation,
    compose,
    digest_json,
    identity_relation,
)


@dataclass(frozen=True)
class ReturnAtom:
    atom_id: str
    state_count: int
    observation_count: int
    exponent: int
    provenance: Tuple[str, ...]

    def data(self):
        return {
            "atom_id": self.atom_id,
            "state_count": self.state_count,
            "observation_count": self.observation_count,
            "exponent": self.exponent,
            "provenance": list(self.provenance),
        }


@dataclass
class ReturnUsage:
    state_count: int
    observation_count: int
    exponent: int
    origins: List[str] = field(default_factory=list)


class Kernel:
    def __init__(self, config: BasisConfig):
        self.config = config
        self.return_usage: Dict[Tuple[int, int, int], ReturnUsage] = {}
        self.return_atoms: Dict[Tuple[int, int], ReturnAtom] = {}

    @staticmethod
    def _is_identity(r: FunctionRelation) -> bool:
        return (
            r.domain.carrier_id == r.codomain.carrier_id
            and r.outputs == tuple(range(r.domain.size))
        )

    def _power(
        self,
        transition: FunctionRelation,
        exponent: int,
    ) -> Optional[FunctionRelation]:
        exponent = int(exponent)
        if exponent <= 0:
            raise ValueError("exponent must be positive")

        if exponent == 1:
            return transition

        if not self.config.compose:
            return None

        p = transition
        for _ in range(2, exponent + 1):
            p = compose(p, transition)
        return p

    def _least_identity_return(
        self,
        transition: FunctionRelation,
        max_steps: int,
    ) -> Dict[str, Any]:
        if (
            transition.domain.carrier_id
            != transition.codomain.carrier_id
        ):
            return {
                "status": "TYPE_MISMATCH",
                "tested_exponents": 0,
            }

        # A non-bijection can never have a positive power equal to identity.
        if not transition.is_bijection():
            return {
                "status": "CERTIFIED_NO_GLOBAL_IDENTITY_RETURN",
                "tested_exponents": 0,
                "certificate": {
                    "kind": "non_bijection",
                    "outputs": list(transition.outputs),
                },
            }

        tested = 0
        for k in range(1, int(max_steps) + 1):
            p = self._power(transition, k)
            if p is None:
                return {
                    "status": "UNKNOWN_COMPOSITION_UNAVAILABLE",
                    "tested_exponents": tested,
                }
            tested += 1
            if self._is_identity(p):
                return {
                    "status": "VERIFIED",
                    "exponent": k,
                    "tested_exponents": tested,
                    "witness": p.data(),
                }

        return {
            "status": "UNKNOWN_RECURRENCE",
            "tested_exponents": tested,
        }

    def _future_trace_classes(
        self,
        transition: FunctionRelation,
        observer: FunctionRelation,
        depth: int,
    ) -> Dict[str, Any]:
        if observer.domain.carrier_id != transition.domain.carrier_id:
            return {"status": "TYPE_MISMATCH"}

        depth = int(depth)
        if depth <= 0:
            raise ValueError("depth must be positive")

        # Build O after T^j, j=0..depth-1.
        observation_maps: List[FunctionRelation] = [observer]

        if depth > 1 and not self.config.compose:
            return {
                "status": "UNKNOWN_COMPOSITION_UNAVAILABLE",
                "depth": depth,
            }

        p = identity_relation(transition.domain)
        for j in range(1, depth):
            p = compose(p, transition)
            observation_maps.append(compose(p, observer))

        traces: List[Tuple[int, ...]] = []
        for i in range(transition.domain.size):
            traces.append(
                tuple(obs.outputs[i] for obs in observation_maps)
            )

        groups: Dict[Tuple[int, ...], List[int]] = {}
        for i, tr in enumerate(traces):
            groups.setdefault(tr, []).append(i)

        classes = tuple(
            tuple(v)
            for _, v in sorted(groups.items(), key=lambda kv: kv[0])
        )

        qid = "ft_" + digest_json({
            "transition": transition.digest(),
            "observer": observer.digest(),
            "depth": depth,
            "classes": [list(c) for c in classes],
        })[:16]

        carrier = Carrier(
            qid,
            tuple(
                ("future_trace_class", qid, idx, tuple(cls))
                for idx, cls in enumerate(classes)
            ),
        )

        return {
            "status": "VERIFIED",
            "depth": depth,
            "traces": [list(t) for t in traces],
            "classes": [list(c) for c in classes],
            "carrier": carrier,
            "carrier_data": carrier.data(),
        }

    @staticmethod
    def _shape_key(
        transition: FunctionRelation,
        observer: Optional[FunctionRelation],
    ) -> Tuple[int, int]:
        return (
            transition.domain.size,
            observer.codomain.size if observer is not None else 0,
        )

    @staticmethod
    def _atom_id(
        state_count: int,
        observation_count: int,
        exponent: int,
    ) -> str:
        raw = json.dumps({
            "state_count": state_count,
            "observation_count": observation_count,
            "exponent": exponent,
        }, sort_keys=True).encode()
        return "t_" + hashlib.sha256(raw).hexdigest()[:16]

    def _record_verified_return(
        self,
        request_id: str,
        transition: FunctionRelation,
        observer: Optional[FunctionRelation],
        exponent: int,
    ) -> Optional[ReturnAtom]:
        n, m = self._shape_key(transition, observer)
        key = (n, m, int(exponent))

        u = self.return_usage.get(key)
        if u is None:
            u = ReturnUsage(n, m, int(exponent))
            self.return_usage[key] = u

        if request_id not in u.origins:
            u.origins.append(request_id)

        if len(u.origins) < 2:
            return None

        scope = (n, m)
        atom = self.return_atoms.get(scope)
        if atom is None:
            atom = ReturnAtom(
                atom_id=self._atom_id(n, m, int(exponent)),
                state_count=n,
                observation_count=m,
                exponent=int(exponent),
                provenance=tuple(u.origins),
            )
            self.return_atoms[scope] = atom
        return atom

    def ablate_return_atom(
        self,
        state_count: int,
        observation_count: int,
    ) -> bool:
        key = (int(state_count), int(observation_count))
        return self.return_atoms.pop(key, None) is not None

    def analyze(
        self,
        request_id: str,
        transition: FunctionRelation,
        observer: Optional[FunctionRelation],
        max_steps: int,
        allow_search: bool = True,
    ) -> Dict[str, Any]:
        n, m = self._shape_key(transition, observer)
        scope = (n, m)

        failed_reuse = None
        atom = self.return_atoms.get(scope)

        # Retained structural hypothesis is replayed first.
        if atom is not None:
            p = self._power(transition, atom.exponent)
            if p is None:
                return {
                    "request_id": request_id,
                    "status": "UNKNOWN_COMPOSITION_UNAVAILABLE",
                    "route": "STOP",
                    "tested_exponents": 0,
                }

            if self._is_identity(p):
                trace = None
                if observer is not None:
                    trace = self._future_trace_classes(
                        transition,
                        observer,
                        atom.exponent,
                    )
                    if trace.get("status") != "VERIFIED":
                        return {
                            "request_id": request_id,
                            "status": trace.get("status"),
                            "route": "STOP",
                            "tested_exponents": 0,
                        }

                self._record_verified_return(
                    request_id,
                    transition,
                    observer,
                    atom.exponent,
                )
                return {
                    "request_id": request_id,
                    "status": "VERIFIED",
                    "route": "REUSE_RETURN_ATOM",
                    "exponent": atom.exponent,
                    "tested_exponents": 0,
                    "direct_replay_count": 1,
                    "return_atom": atom.data(),
                    "trace": trace,
                }

            failed_reuse = {
                "return_atom": atom.data(),
                "reason": "direct_replay_failed",
            }

        if not allow_search:
            return {
                "request_id": request_id,
                "status": "UNKNOWN_ANALYSIS",
                "route": "STOP",
                "tested_exponents": 0,
                "failed_reuse": failed_reuse,
            }

        ret = self._least_identity_return(
            transition,
            max_steps,
        )

        if ret.get("status") != "VERIFIED":
            return {
                "request_id": request_id,
                "status": ret.get("status"),
                "route": "SEARCH",
                "tested_exponents": ret.get("tested_exponents", 0),
                "certificate": ret.get("certificate"),
                "failed_reuse": failed_reuse,
            }

        exponent = int(ret["exponent"])
        trace = None
        if observer is not None:
            trace = self._future_trace_classes(
                transition,
                observer,
                exponent,
            )
            if trace.get("status") != "VERIFIED":
                return {
                    "request_id": request_id,
                    "status": trace.get("status"),
                    "route": "SEARCH",
                    "tested_exponents": ret.get("tested_exponents", 0),
                }

        promoted = self._record_verified_return(
            request_id,
            transition,
            observer,
            exponent,
        )

        return {
            "request_id": request_id,
            "status": "VERIFIED",
            "route": "SEARCH",
            "exponent": exponent,
            "tested_exponents": ret.get("tested_exponents", 0),
            "identity_return_witness": ret.get("witness"),
            "trace": trace,
            "promoted_return_atom": (
                promoted.data() if promoted is not None else None
            ),
            "failed_reuse": failed_reuse,
        }
