#!/usr/bin/env python3
"""Frozen V10 kernel: infer anonymous causal relations, then replay generic
relation invariants without coordinates or geometry labels."""
from __future__ import annotations

from dataclasses import dataclass, field
import hashlib
import json
from typing import Any, Dict, List, Mapping, Optional, Sequence, Tuple

from basis import (
    BasisConfig,
    ComponentCarrier,
    InfluenceRelation,
    component_carrier,
    compose_relations,
    digest_json,
)


@dataclass(frozen=True)
class StructureAtom:
    atom_id: str
    channel_count: int
    signature: Dict[str, Any]
    provenance: Tuple[str, ...]

    def data(self):
        return {
            "atom_id": self.atom_id,
            "channel_count": self.channel_count,
            "signature": self.signature,
            "provenance": list(self.provenance),
        }


@dataclass
class SignatureUsage:
    signature: Dict[str, Any]
    origins: List[str] = field(default_factory=list)


class Kernel:
    def __init__(self, config: BasisConfig):
        self.config = config
        self.signature_usage: Dict[str, SignatureUsage] = {}
        self.structure_atoms: Dict[int, StructureAtom] = {}

    @staticmethod
    def _row_from_observation(bits: Sequence[int], n: int) -> frozenset[int]:
        if len(bits) != n:
            raise ValueError("observation width mismatch")
        if any(int(x) not in (0, 1) for x in bits):
            raise ValueError("observations must be binary")
        return frozenset(i for i, x in enumerate(bits) if int(x) == 1)

    def infer_relation(
        self,
        channel_count: int,
        observations: Mapping[int, Sequence[int]],
        search_complete: bool,
    ) -> Dict[str, Any]:
        n = int(channel_count)
        tested_rows = 0
        rows: List[frozenset[int]] = []

        for source in range(n):
            if source not in observations:
                return {
                    "status": (
                        "UNKNOWN_INFLUENCE"
                        if not search_complete
                        else "CERTIFIED_INCOMPLETE_OBSERVATION_SET"
                    ),
                    "missing_source": source,
                    "tested_row_candidates": tested_rows,
                }

            target = self._row_from_observation(observations[source], n)
            accepted: List[frozenset[int]] = []

            for mask in range(1 << n):
                candidate = frozenset(
                    j for j in range(n)
                    if mask & (1 << j)
                )
                tested_rows += 1
                if candidate == target:
                    accepted.append(candidate)

            if len(accepted) != 1:
                return {
                    "status": "UNKNOWN_INFLUENCE",
                    "source": source,
                    "accepted_row_count": len(accepted),
                    "tested_row_candidates": tested_rows,
                }
            rows.append(accepted[0])

        relation = InfluenceRelation(n, tuple(rows))
        return {
            "status": "VERIFIED",
            "relation": relation,
            "relation_data": relation.data(),
            "tested_row_candidates": tested_rows,
        }

    def _relation_signature(
        self,
        relation: InfluenceRelation,
    ) -> Dict[str, Any]:
        if not self.config.compose:
            raise RuntimeError("COMPOSE unavailable")

        n = relation.size
        reach = [set([i]) for i in range(n)]
        distances: List[List[Optional[int]]] = [
            [0 if i == j else None for j in range(n)]
            for i in range(n)
        ]

        power = relation
        for depth in range(1, n):
            for i in range(n):
                for j in power.rows[i]:
                    reach[i].add(j)
                    if distances[i][j] is None:
                        distances[i][j] = depth
            power = compose_relations(power, relation)

        unseen = set(range(n))
        components: List[Tuple[int, ...]] = []

        while unseen:
            i = min(unseen)
            cls = tuple(
                j for j in range(n)
                if j in reach[i] and i in reach[j]
            )
            components.append(tuple(sorted(cls)))
            unseen.difference_update(cls)

        components.sort(key=lambda c: (len(c), c))

        finite_distances = sorted(
            d
            for row in distances
            for d in row
            if d is not None and d > 0
        )

        degree_pairs = sorted(
            zip(relation.out_degrees(), relation.in_degrees())
        )

        signature = {
            "channel_count": n,
            "edge_count": sum(relation.out_degrees()),
            "degree_pairs": [list(p) for p in degree_pairs],
            "component_sizes": sorted(len(c) for c in components),
            "distance_multiset": finite_distances,
        }

        return {
            "signature": signature,
            "components": components,
            "component_carrier": component_carrier(components),
            "reach": [sorted(x) for x in reach],
            "distances": distances,
        }

    @staticmethod
    def _signature_key(signature: Mapping[str, Any]) -> str:
        return digest_json(dict(signature))

    @staticmethod
    def _atom_id(channel_count: int, signature: Mapping[str, Any]) -> str:
        raw = json.dumps(
            {
                "channel_count": int(channel_count),
                "signature": dict(signature),
            },
            sort_keys=True,
        ).encode()
        return "s_" + hashlib.sha256(raw).hexdigest()[:16]

    def _record_signature(
        self,
        request_id: str,
        signature: Dict[str, Any],
    ) -> Optional[StructureAtom]:
        key = self._signature_key(signature)
        u = self.signature_usage.get(key)
        if u is None:
            u = SignatureUsage(signature)
            self.signature_usage[key] = u

        if request_id not in u.origins:
            u.origins.append(request_id)

        if len(u.origins) < 2:
            return None

        n = int(signature["channel_count"])
        atom = self.structure_atoms.get(n)
        if atom is None:
            atom = StructureAtom(
                atom_id=self._atom_id(n, signature),
                channel_count=n,
                signature=signature,
                provenance=tuple(u.origins),
            )
            self.structure_atoms[n] = atom
        return atom

    def ablate_structure_atom(self, channel_count: int) -> bool:
        return self.structure_atoms.pop(int(channel_count), None) is not None

    def analyze(
        self,
        request_id: str,
        channel_count: int,
        observations: Mapping[int, Sequence[int]],
        observation_search_complete: bool = True,
        allow_structure_search: bool = True,
    ) -> Dict[str, Any]:
        inferred = self.infer_relation(
            channel_count,
            observations,
            observation_search_complete,
        )

        if inferred.get("status") != "VERIFIED":
            return {
                "request_id": request_id,
                "status": inferred.get("status"),
                "route": "STOP",
                "inference": inferred,
            }

        relation = inferred["relation"]
        n = relation.size
        atom = self.structure_atoms.get(n)
        failed_reuse = None

        # Direct replay of a retained anonymous structural signature.
        if atom is not None:
            if not self.config.compose:
                return {
                    "request_id": request_id,
                    "status": "UNKNOWN_COMPOSITION_UNAVAILABLE",
                    "route": "STOP",
                    "inference": inferred,
                    "signature_search_count": 0,
                }

            actual = self._relation_signature(relation)
            if actual["signature"] == atom.signature:
                self._record_signature(request_id, actual["signature"])
                return {
                    "request_id": request_id,
                    "status": "VERIFIED",
                    "route": "REUSE_STRUCTURE_ATOM",
                    "inference": inferred,
                    "signature": actual["signature"],
                    "components": [list(c) for c in actual["components"]],
                    "component_carrier": actual["component_carrier"].data(),
                    "structure_atom": atom.data(),
                    "signature_search_count": 0,
                }

            failed_reuse = {
                "structure_atom": atom.data(),
                "reason": "signature_replay_failed",
                "actual_signature": actual["signature"],
            }

        if not allow_structure_search:
            return {
                "request_id": request_id,
                "status": "UNKNOWN_STRUCTURE",
                "route": "STOP",
                "inference": inferred,
                "signature_search_count": 0,
                "failed_reuse": failed_reuse,
            }

        if not self.config.compose:
            return {
                "request_id": request_id,
                "status": "UNKNOWN_COMPOSITION_UNAVAILABLE",
                "route": "SEARCH",
                "inference": inferred,
                "signature_search_count": 0,
            }

        actual = self._relation_signature(relation)
        promoted = self._record_signature(
            request_id,
            actual["signature"],
        )

        return {
            "request_id": request_id,
            "status": "VERIFIED",
            "route": "SEARCH",
            "inference": inferred,
            "signature": actual["signature"],
            "components": [list(c) for c in actual["components"]],
            "component_carrier": actual["component_carrier"].data(),
            "signature_search_count": 1,
            "promoted_structure_atom": (
                promoted.data() if promoted is not None else None
            ),
            "failed_reuse": failed_reuse,
        }
