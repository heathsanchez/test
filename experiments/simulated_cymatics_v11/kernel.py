#!/usr/bin/env python3
"""Frozen V11 analyzer for anonymous exact vibration traces.

The kernel has no coordinate, spectral, mode, node, phase, or wave-equation
primitive.  It combines:
- exact inference of one-step influence relations;
- relational composition for multi-step organization;
- exact finite temporal replay/equality;
- verified reification of persistent consequential structure.
"""
from __future__ import annotations

from dataclasses import dataclass, field
import hashlib
import json
from typing import Any, Dict, List, Mapping, Optional, Sequence, Tuple

from basis import (
    BasisConfig,
    FrameTrace,
    InfluenceRelation,
    compose_relations,
    digest_json,
    induced_relation,
)


@dataclass(frozen=True)
class PatternAtom:
    atom_id: str
    channel_count: int
    signature: Dict[str, Any]
    provenance: Tuple[str, ...]

    def data(self) -> Any:
        return {
            "atom_id": self.atom_id,
            "channel_count": self.channel_count,
            "signature": self.signature,
            "provenance": list(self.provenance),
        }


@dataclass
class PatternUsage:
    signature: Dict[str, Any]
    origins: List[str] = field(default_factory=list)


class Kernel:
    def __init__(self, config: BasisConfig):
        self.config = config
        self.pattern_usage: Dict[str, PatternUsage] = {}
        self.pattern_atoms: Dict[int, PatternAtom] = {}

    # ------------------------------------------------------------------
    # Exact one-step causal relation
    # ------------------------------------------------------------------

    @staticmethod
    def _row_from_bits(bits: Sequence[int], n: int) -> frozenset[int]:
        if len(bits) != n:
            raise ValueError("intervention width mismatch")
        if any(int(x) not in (0, 1) for x in bits):
            raise ValueError("intervention consequences must be binary")
        return frozenset(i for i, x in enumerate(bits) if int(x) == 1)

    def infer_influence(
        self,
        channel_count: int,
        observations: Mapping[int, Sequence[int]],
        search_complete: bool,
    ) -> Dict[str, Any]:
        n = int(channel_count)
        rows: List[frozenset[int]] = []
        tested = 0

        for source in range(n):
            if source not in observations:
                return {
                    "status": (
                        "UNKNOWN_INFLUENCE"
                        if not search_complete
                        else "CERTIFIED_INCOMPLETE_INTERVENTION_SET"
                    ),
                    "missing_source": source,
                    "tested_row_candidates": tested,
                }

            target = self._row_from_bits(observations[source], n)
            matches: List[frozenset[int]] = []

            for mask in range(1 << n):
                row = frozenset(j for j in range(n) if mask & (1 << j))
                tested += 1
                if row == target:
                    matches.append(row)

            if len(matches) != 1:
                return {
                    "status": "UNKNOWN_INFLUENCE",
                    "source": source,
                    "accepted_row_count": len(matches),
                    "tested_row_candidates": tested,
                }
            rows.append(matches[0])

        rel = InfluenceRelation(n, tuple(rows))
        return {
            "status": "VERIFIED",
            "relation": rel,
            "relation_data": rel.data(),
            "tested_row_candidates": tested,
        }

    # ------------------------------------------------------------------
    # Generic relational organization
    # ------------------------------------------------------------------

    def _component_classes(
        self,
        relation: InfluenceRelation,
    ) -> Optional[Tuple[Tuple[int, ...], ...]]:
        n = relation.size
        if n == 0:
            return tuple()
        if n == 1:
            return ((0,),)
        if not self.config.compose:
            return None

        reach = [set([i]) for i in range(n)]
        power = relation

        for _depth in range(1, n):
            for i in range(n):
                reach[i].update(power.rows[i])
            power = compose_relations(power, relation)

        unseen = set(range(n))
        classes: List[Tuple[int, ...]] = []
        while unseen:
            i = min(unseen)
            cls = tuple(
                j for j in range(n)
                if j in reach[i] and i in reach[j]
            )
            classes.append(tuple(sorted(cls)))
            unseen.difference_update(cls)

        classes.sort(key=lambda c: (len(c), c))
        return tuple(classes)

    def _spatial_record(
        self,
        relation: InfluenceRelation,
        persistent: Sequence[int],
    ) -> Optional[Dict[str, Any]]:
        if not self.config.compose:
            return None

        n = relation.size
        pset = set(int(x) for x in persistent)
        other = [i for i in range(n) if i not in pset]

        full_classes = self._component_classes(relation)
        p_rel = induced_relation(relation, sorted(pset))
        o_rel = induced_relation(relation, other)
        p_classes = self._component_classes(p_rel)
        o_classes = self._component_classes(o_rel)

        if full_classes is None or p_classes is None or o_classes is None:
            return None

        cut_out = sum(
            1
            for i in pset
            for j in relation.rows[i]
            if j not in pset
        )

        return {
            "influence_edge_count": sum(len(r) for r in relation.rows),
            "degree_pairs": [
                list(x)
                for x in sorted(
                    zip(relation.out_degrees(), relation.in_degrees())
                )
            ],
            "full_component_sizes": sorted(len(c) for c in full_classes),
            "persistent_component_sizes": sorted(len(c) for c in p_classes),
            "other_component_sizes": sorted(len(c) for c in o_classes),
            "persistent_to_other_incidence_count": cut_out,
        }

    # ------------------------------------------------------------------
    # Temporal equality / recurrence
    # ------------------------------------------------------------------

    def _least_verified_return(
        self,
        trace: FrameTrace,
        max_return: int,
    ) -> Dict[str, Any]:
        if not self.config.temporal_replay:
            return {
                "status": "UNKNOWN_TEMPORAL_REPLAY",
                "tested_displacements": 0,
                "reason": "temporal_replay_unavailable",
            }

        frames = trace.frames
        tested = 0

        for k in range(1, int(max_return) + 1):
            # Need two full observed copies plus one successor frame to replay
            # consecutive-frame state pairs rather than a single coincidence.
            if len(frames) < 2 * k + 2:
                return {
                    "status": "UNKNOWN_TEMPORAL_REPLAY",
                    "tested_displacements": tested,
                    "required_frames_for_next_candidate": 2 * k + 2,
                    "available_frames": len(frames),
                }

            tested += 1
            initial_pair = (frames[0], frames[1])
            returned_pair = (frames[k], frames[k + 1])
            if returned_pair != initial_pair:
                continue

            # Replay more than the return point: verify one complete observed
            # block plus its next frame repeats exactly.
            if all(frames[t] == frames[t + k] for t in range(k + 2)):
                return {
                    "status": "VERIFIED",
                    "return_displacement": k,
                    "tested_displacements": tested,
                    "replayed_frame_equalities": k + 2,
                }

        return {
            "status": "UNKNOWN_TEMPORAL_REPLAY",
            "tested_displacements": tested,
        }

    @staticmethod
    def _persistent_baseline(
        trace: FrameTrace,
        return_displacement: int,
    ) -> Tuple[int, ...]:
        k = int(return_displacement)
        return tuple(
            i
            for i in range(trace.channel_count)
            if all(trace.frames[t][i] == trace.baseline for t in range(k))
        )

    # ------------------------------------------------------------------
    # Pattern signature / compilation
    # ------------------------------------------------------------------

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
        return "pat_" + hashlib.sha256(raw).hexdigest()[:16]

    def _record_pattern(
        self,
        request_id: str,
        signature: Dict[str, Any],
    ) -> Optional[PatternAtom]:
        key = self._signature_key(signature)
        u = self.pattern_usage.get(key)
        if u is None:
            u = PatternUsage(signature)
            self.pattern_usage[key] = u

        if request_id not in u.origins:
            u.origins.append(request_id)

        if len(u.origins) < 2:
            return None

        n = int(signature["channel_count"])
        atom = self.pattern_atoms.get(n)
        if atom is None:
            atom = PatternAtom(
                atom_id=self._atom_id(n, signature),
                channel_count=n,
                signature=signature,
                provenance=tuple(u.origins),
            )
            self.pattern_atoms[n] = atom
        return atom

    def ablate_pattern_atom(self, channel_count: int) -> bool:
        return self.pattern_atoms.pop(int(channel_count), None) is not None

    def _construct_signature(
        self,
        relation: InfluenceRelation,
        trace: FrameTrace,
        max_return: int,
    ) -> Dict[str, Any]:
        temporal = self._least_verified_return(trace, max_return)
        if temporal.get("status") != "VERIFIED":
            return {
                "status": temporal.get("status"),
                "temporal": temporal,
            }

        k = int(temporal["return_displacement"])
        persistent = self._persistent_baseline(trace, k)
        spatial = self._spatial_record(relation, persistent)

        if spatial is None:
            return {
                "status": "UNKNOWN_COMPOSITION_UNAVAILABLE",
                "temporal": temporal,
                "persistent_channels": list(persistent),
            }

        signature = {
            "channel_count": relation.size,
            "return_displacement": k,
            "persistent_count": len(persistent),
            **spatial,
        }

        return {
            "status": "VERIFIED",
            "temporal": temporal,
            "persistent_channels": list(persistent),
            "signature": signature,
        }

    def analyze(
        self,
        request_id: str,
        channel_count: int,
        interventions: Mapping[int, Sequence[int]],
        trace: FrameTrace,
        max_return: int,
        intervention_search_complete: bool = True,
        allow_pattern_search: bool = True,
    ) -> Dict[str, Any]:
        inferred = self.infer_influence(
            channel_count,
            interventions,
            intervention_search_complete,
        )

        if inferred.get("status") != "VERIFIED":
            return {
                "request_id": request_id,
                "status": inferred.get("status"),
                "route": "STOP",
                "inference": inferred,
            }

        relation = inferred["relation"]
        constructed = self._construct_signature(
            relation,
            trace,
            max_return,
        )

        if constructed.get("status") != "VERIFIED":
            return {
                "request_id": request_id,
                "status": constructed.get("status"),
                "route": "STOP",
                "inference": inferred,
                "construction": constructed,
            }

        signature = constructed["signature"]
        atom = self.pattern_atoms.get(int(channel_count))
        failed_reuse = None

        if atom is not None:
            if signature == atom.signature:
                self._record_pattern(request_id, signature)
                return {
                    "request_id": request_id,
                    "status": "VERIFIED",
                    "route": "REUSE_PATTERN_ATOM",
                    "inference": inferred,
                    "construction": constructed,
                    "signature": signature,
                    "pattern_atom": atom.data(),
                    "pattern_search_count": 0,
                }

            failed_reuse = {
                "pattern_atom": atom.data(),
                "reason": "pattern_replay_failed",
                "actual_signature": signature,
            }

        if not allow_pattern_search:
            return {
                "request_id": request_id,
                "status": "UNKNOWN_PATTERN",
                "route": "STOP",
                "inference": inferred,
                "construction": constructed,
                "signature": signature,
                "pattern_search_count": 0,
                "failed_reuse": failed_reuse,
            }

        promoted = self._record_pattern(request_id, signature)

        return {
            "request_id": request_id,
            "status": "VERIFIED",
            "route": "SEARCH",
            "inference": inferred,
            "construction": constructed,
            "signature": signature,
            "pattern_search_count": 1,
            "promoted_pattern_atom": (
                promoted.data() if promoted is not None else None
            ),
            "failed_reuse": failed_reuse,
        }
