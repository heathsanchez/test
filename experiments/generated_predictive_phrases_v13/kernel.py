#!/usr/bin/env python3
"""Frozen V13 developmental kernel for generated predictive phrases.

Only atomic actions are primitive. Composite tests are generated breadth-first
by CONCAT. All splitting, minimization, selection, compilation, and reuse are
governed by verified future consequence.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, Iterable, List, Mapping, Optional, Sequence, Tuple

from basis import (
    Phrase,
    PhraseWorld,
    full_partition,
    generate_phrases,
    partition,
    phrase_digest,
    phrase_set_cost,
    same_partition,
)


@dataclass(frozen=True)
class PhraseAtom:
    atom_id: str
    interface_key: Tuple[int, int, int]
    expansion: Phrase
    cost: int
    consequence_signature: Tuple[Tuple[int, ...], ...]
    provenance: Tuple[str, ...]

    def data(self) -> Any:
        return {
            "atom_id": self.atom_id,
            "interface_key": list(self.interface_key),
            "expansion": list(self.expansion),
            "cost": self.cost,
            "consequence_signature": [list(x) for x in self.consequence_signature],
            "provenance": list(self.provenance),
        }


@dataclass
class PhraseUsage:
    expansion: Phrase
    origins: List[str] = field(default_factory=list)


class Kernel:
    def __init__(self):
        self.phrase_usage: Dict[Tuple[Any, ...], PhraseUsage] = {}
        self.compiled_atoms: Dict[Tuple[int, int, int], PhraseAtom] = {}

    # ------------------------------------------------------------------
    # Authority and semantic helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _require_complete(world: PhraseWorld) -> Optional[Dict[str, Any]]:
        if not world.complete:
            return {
                "status": "UNKNOWN_AUTHORITY",
                "reason": "bounded_phrase_consequence_oracle_incomplete",
            }
        return None

    @staticmethod
    def _constructible(
        world: PhraseWorld,
        concat_enabled: bool,
    ) -> Tuple[Phrase, ...]:
        return generate_phrases(
            world.action_count,
            world.max_phrase_length,
            concat_enabled=concat_enabled,
        )

    @staticmethod
    def _code_behavior_key(
        world: PhraseWorld,
        code: Sequence[Phrase],
    ) -> Tuple[Any, ...]:
        ps = tuple(sorted(set(tuple(p) for p in code)))
        return tuple(
            tuple(world.outcome(i, p) for p in ps)
            for i in range(len(world.histories))
        )

    @staticmethod
    def _is_complete(
        world: PhraseWorld,
        code: Sequence[Phrase],
    ) -> bool:
        return same_partition(
            partition(world, code),
            full_partition(world),
        )

    @staticmethod
    def _full_class_of(world: PhraseWorld) -> Dict[int, int]:
        out = {}
        for cid, cls in enumerate(full_partition(world)):
            for i in cls:
                out[i] = cid
        return out

    def _first_obstruction(
        self,
        world: PhraseWorld,
        code: Sequence[Phrase],
    ) -> Optional[Dict[str, Any]]:
        current = partition(world, code)
        class_of = self._full_class_of(world)

        for cls in current:
            for p in range(len(cls)):
                for q in range(p + 1, len(cls)):
                    i, j = cls[p], cls[q]
                    if class_of[i] == class_of[j]:
                        continue
                    return {
                        "history_pair": [i, j],
                        "current_phrase_count": len(code),
                        "current_phrases": [list(x) for x in code],
                    }
        return None

    # ------------------------------------------------------------------
    # Phrase construction from obstruction
    # ------------------------------------------------------------------

    def shortest_generated_separators(
        self,
        world: PhraseWorld,
        history_i: int,
        history_j: int,
        active: Sequence[Phrase],
        concat_enabled: bool,
    ) -> Dict[str, Any]:
        constructible = self._constructible(world, concat_enabled)
        active_set = set(tuple(p) for p in active)

        by_len: Dict[int, List[Phrase]] = {}
        generated = 0
        for phrase in constructible:
            generated += 1
            if phrase in active_set:
                continue
            if world.outcome(history_i, phrase) == world.outcome(history_j, phrase):
                continue
            by_len.setdefault(len(phrase), []).append(phrase)

        if not by_len:
            return {
                "status": (
                    "CERTIFIED_GRAMMAR_INADEQUACY"
                    if not concat_enabled
                    else "CERTIFIED_NO_SEPARATOR_IN_DECLARED_LANGUAGE"
                ),
                "generated_phrase_count": generated,
                "separators": [],
            }

        min_len = min(by_len)
        candidates = sorted(by_len[min_len])

        # Preserve behaviorally distinct equal-cost repairs. Only collapse
        # phrases with exactly identical consequence signatures on all admitted
        # histories.
        seen = {}
        for phrase in candidates:
            sig = tuple(world.outcome(i, phrase) for i in range(len(world.histories)))
            old = seen.get(sig)
            if old is None or phrase < old:
                seen[sig] = phrase

        separators = sorted(seen.values())
        return {
            "status": "VERIFIED",
            "generated_phrase_count": generated,
            "minimum_length": min_len,
            "separators": [list(p) for p in separators],
            "witness_outcomes": {
                str(list(p)): [
                    list(world.outcome(history_i, p)),
                    list(world.outcome(history_j, p)),
                ]
                for p in separators
            },
        }

    def developmental_frontier(
        self,
        world: PhraseWorld,
        *,
        concat_enabled: bool = True,
        consequence_enabled: bool = True,
        max_generations: Optional[int] = None,
    ) -> Dict[str, Any]:
        auth = self._require_complete(world)
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
            max_generations = len(full_partition(world)) + 2

        frontier = {tuple()}
        generations = []

        for generation in range(int(max_generations) + 1):
            # Quotient only genuinely identical phrase-code behavior, not merely
            # equal partitions. This preserves future-distinguishable idioms.
            by_behavior = {}
            for code in sorted(frontier):
                key = self._code_behavior_key(world, code)
                old = by_behavior.get(key)
                if old is None or (phrase_set_cost(code), code) < (
                    phrase_set_cost(old), old
                ):
                    by_behavior[key] = code
            frontier = set(by_behavior.values())

            complete = [code for code in sorted(frontier) if self._is_complete(world, code)]
            record = {
                "generation": generation,
                "frontier_size": len(frontier),
                "frontier_codes": [
                    [list(p) for p in code] for code in sorted(frontier)
                ],
                "frontier_class_counts": [
                    len(partition(world, code)) for code in sorted(frontier)
                ],
                "complete_codes": [
                    [list(p) for p in code] for code in complete
                ],
                "repairs": [],
            }

            if complete:
                generations.append(record)
                return {
                    "status": "VERIFIED",
                    "initial_class_count": 1,
                    "final_generation": generation,
                    "frontier": [
                        [list(p) for p in code] for code in sorted(frontier)
                    ],
                    "complete_frontier_codes": [
                        [list(p) for p in code] for code in complete
                    ],
                    "generations": generations,
                }

            next_frontier = set()

            for code in sorted(frontier):
                obstruction = self._first_obstruction(world, code)
                if obstruction is None:
                    continue
                i, j = obstruction["history_pair"]
                repairs = self.shortest_generated_separators(
                    world,
                    i,
                    j,
                    code,
                    concat_enabled,
                )
                row = {
                    "code": [list(p) for p in code],
                    "obstruction": obstruction,
                    "repair_search": repairs,
                    "candidate_extensions": [],
                }

                if repairs.get("status") != "VERIFIED":
                    record["repairs"].append(row)
                    generations.append(record)
                    return {
                        "status": repairs.get("status"),
                        "initial_class_count": 1,
                        "stuck_code": [list(p) for p in code],
                        "obstruction": obstruction,
                        "repair_search": repairs,
                        "generations": generations,
                    }

                for phrase0 in repairs["separators"]:
                    phrase = tuple(int(a) for a in phrase0)
                    new_code = tuple(sorted(set(code) | {phrase}))
                    next_frontier.add(new_code)
                    row["candidate_extensions"].append(
                        [list(p) for p in new_code]
                    )
                record["repairs"].append(row)

            generations.append(record)

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
    # Exact global minimum via consequential pair cover
    # ------------------------------------------------------------------

    @staticmethod
    def _class_representatives(world: PhraseWorld) -> Tuple[int, ...]:
        return tuple(cls[0] for cls in full_partition(world))

    def exact_minimum_codes(
        self,
        world: PhraseWorld,
        *,
        concat_enabled: bool = True,
    ) -> Dict[str, Any]:
        auth = self._require_complete(world)
        if auth:
            return auth

        phrases = self._constructible(world, concat_enabled)
        reps = self._class_representatives(world)
        pairs = [
            (reps[i], reps[j])
            for i in range(len(reps))
            for j in range(i + 1, len(reps))
        ]
        target = (1 << len(pairs)) - 1

        if target == 0:
            return {
                "status": "VERIFIED",
                "generated_phrase_count": len(phrases),
                "pair_count": 0,
                "minimum_codes": [{"phrases": [], "cost": [0, 0]}],
                "lower_bound": {"zero_phrase_complete": True},
            }

        entries = []
        for phrase in phrases:
            mask = 0
            for bit, (i, j) in enumerate(pairs):
                if world.outcome(i, phrase) != world.outcome(j, phrase):
                    mask |= 1 << bit
            if mask:
                entries.append((phrase, mask))

        # Single-phrase case gives a direct and particularly strong certificate.
        singles = [p for p, mask in entries if mask == target]
        if singles:
            best_len = min(len(p) for p in singles)
            minima = sorted(p for p in singles if len(p) == best_len)
            shorter_complete = sum(1 for p in singles if len(p) < best_len)
            return {
                "status": "VERIFIED",
                "generated_phrase_count": len(phrases),
                "pair_count": len(pairs),
                "minimum_codes": [
                    {"phrases": [list(p)], "cost": [1, len(p)]}
                    for p in minima
                ],
                "lower_bound": {
                    "zero_phrase_complete": False,
                    "shortest_complete_single_phrase_length": best_len,
                    "shorter_complete_single_phrase_count": shorter_complete,
                    "complete_single_phrase_count": len(singles),
                },
            }

        # Exact dynamic programming over the finite consequential pair universe.
        # Keep all equal-cost solutions for the target, while using one best
        # representative per intermediate mask.
        best = {0: (0, 0, tuple())}
        for phrase, pmask in entries:
            snapshot = list(best.items())
            for mask, (count, length, code) in snapshot:
                new_mask = mask | pmask
                new_code = tuple(sorted(set(code) | {phrase}))
                cand = (len(new_code), sum(len(p) for p in new_code), new_code)
                old = best.get(new_mask)
                if old is None or cand[:2] < old[:2]:
                    best[new_mask] = cand

        if target not in best:
            return {
                "status": (
                    "CERTIFIED_GRAMMAR_INADEQUACY"
                    if not concat_enabled
                    else "CERTIFIED_NO_COMPLETE_CODE_IN_DECLARED_LANGUAGE"
                ),
                "generated_phrase_count": len(phrases),
                "pair_count": len(pairs),
            }

        count, length, code = best[target]
        return {
            "status": "VERIFIED",
            "generated_phrase_count": len(phrases),
            "pair_count": len(pairs),
            "minimum_codes": [{
                "phrases": [list(p) for p in code],
                "cost": [count, length],
            }],
            "lower_bound": {
                "zero_phrase_complete": False,
                "minimum_phrase_count": count,
                "minimum_total_atomic_length": length,
            },
        }

    # ------------------------------------------------------------------
    # Qualification and compilation
    # ------------------------------------------------------------------

    @staticmethod
    def qualify_codes(
        candidate_codes: Sequence[Sequence[Sequence[int]]],
        qualification: PhraseWorld,
    ) -> Dict[str, Any]:
        if not qualification.complete:
            return {"status": "UNKNOWN_AUTHORITY", "survivors": []}

        rows = []
        survivors = []
        for code0 in candidate_codes:
            code = tuple(
                sorted(tuple(int(a) for a in phrase) for phrase in code0)
            )
            ok = same_partition(
                partition(qualification, code),
                full_partition(qualification),
            )
            rows.append({
                "phrases": [list(p) for p in code],
                "qualified": ok,
            })
            if ok:
                survivors.append(code)

        return {
            "status": "VERIFIED",
            "rows": rows,
            "survivors": [
                [list(p) for p in code] for code in survivors
            ],
        }

    def _record_single_phrase(
        self,
        request_id: str,
        world: PhraseWorld,
        phrase: Phrase,
    ) -> Optional[PhraseAtom]:
        key = (world.interface_key(), tuple(phrase))
        usage = self.phrase_usage.get(key)
        if usage is None:
            usage = PhraseUsage(tuple(phrase))
            self.phrase_usage[key] = usage
        if request_id not in usage.origins:
            usage.origins.append(request_id)

        if len(usage.origins) < 2:
            return None

        consequence_signature = tuple(
            world.outcome(i, phrase)
            for i in range(len(world.histories))
        )
        atom = PhraseAtom(
            atom_id="phr_" + phrase_digest(world, phrase)[:16],
            interface_key=world.interface_key(),
            expansion=tuple(phrase),
            cost=len(phrase),
            consequence_signature=consequence_signature,
            provenance=tuple(usage.origins),
        )
        self.compiled_atoms[world.interface_key()] = atom
        return atom

    def ablate_compiled_phrase(self, world: PhraseWorld) -> bool:
        return self.compiled_atoms.pop(world.interface_key(), None) is not None

    def replay_atom(
        self,
        request_id: str,
        world: PhraseWorld,
        atom: PhraseAtom,
    ) -> Dict[str, Any]:
        auth = self._require_complete(world)
        if auth:
            return {"request_id": request_id, **auth, "route": "STOP"}

        if atom.interface_key != world.interface_key():
            return {
                "request_id": request_id,
                "status": "TYPE_MISMATCH",
                "route": "STOP",
            }

        code = (atom.expansion,)
        ok = self._is_complete(world, code)
        return {
            "request_id": request_id,
            "status": "VERIFIED" if ok else "REPLAY_FAILED",
            "route": "REPLAY_COMPILED_PHRASE",
            "phrases": [list(atom.expansion)],
            "partition": [list(c) for c in partition(world, code)],
            "full_partition": [list(c) for c in full_partition(world)],
            "phrase_acquisition_search_count": 0,
            "atom": atom.data(),
        }

    # ------------------------------------------------------------------
    # Full developmental solve
    # ------------------------------------------------------------------

    def solve(
        self,
        request_id: str,
        world: PhraseWorld,
        *,
        qualification: Optional[PhraseWorld] = None,
        allow_acquisition_search: bool = True,
        concat_enabled: bool = True,
        consequence_enabled: bool = True,
    ) -> Dict[str, Any]:
        auth = self._require_complete(world)
        if auth:
            return {"request_id": request_id, **auth, "route": "STOP"}

        retained = self.compiled_atoms.get(world.interface_key())
        failed_reuse = None
        if retained is not None:
            replay = self.replay_atom(request_id, world, retained)
            if replay.get("status") == "VERIFIED":
                self._record_single_phrase(
                    request_id,
                    world,
                    retained.expansion,
                )
                return {
                    **replay,
                    "route": "REUSE_COMPILED_PHRASE",
                    "failed_reuse": None,
                }
            failed_reuse = replay

        if not allow_acquisition_search:
            return {
                "request_id": request_id,
                "status": "UNKNOWN_PHRASE",
                "route": "STOP",
                "phrase_acquisition_search_count": 0,
                "failed_reuse": failed_reuse,
            }

        developmental = self.developmental_frontier(
            world,
            concat_enabled=concat_enabled,
            consequence_enabled=consequence_enabled,
        )
        if developmental.get("status") != "VERIFIED":
            return {
                "request_id": request_id,
                "status": developmental.get("status"),
                "route": "DEVELOP",
                "developmental": developmental,
                "phrase_acquisition_search_count": 1,
                "failed_reuse": failed_reuse,
            }

        minimum = self.exact_minimum_codes(
            world,
            concat_enabled=concat_enabled,
        )
        if minimum.get("status") != "VERIFIED":
            return {
                "request_id": request_id,
                "status": minimum.get("status"),
                "route": "DEVELOP",
                "developmental": developmental,
                "minimum_search": minimum,
                "phrase_acquisition_search_count": 1,
                "failed_reuse": failed_reuse,
            }

        candidates = [
            tuple(tuple(int(a) for a in p) for p in row["phrases"])
            for row in minimum["minimum_codes"]
        ]

        qualification_result = None
        selected = candidates
        if qualification is not None:
            qualification_result = self.qualify_codes(
                [
                    [list(p) for p in code]
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
                    "minimum_search": minimum,
                    "qualification": qualification_result,
                    "phrase_acquisition_search_count": 1,
                    "failed_reuse": failed_reuse,
                }
            selected = [
                tuple(tuple(int(a) for a in p) for p in code)
                for code in qualification_result.get("survivors", [])
            ]

        if not selected:
            return {
                "request_id": request_id,
                "status": "CERTIFIED_FRONTIER_ELIMINATED",
                "route": "DEVELOP",
                "developmental": developmental,
                "minimum_search": minimum,
                "qualification": qualification_result,
                "phrase_acquisition_search_count": 1,
                "failed_reuse": failed_reuse,
            }

        if len(selected) > 1:
            return {
                "request_id": request_id,
                "status": "VERIFIED_FRONTIER",
                "route": "DEVELOP",
                "selected_frontier": [
                    [list(p) for p in code] for code in selected
                ],
                "developmental": developmental,
                "minimum_search": minimum,
                "qualification": qualification_result,
                "phrase_acquisition_search_count": 1,
                "failed_reuse": failed_reuse,
            }

        code = selected[0]
        promoted = None
        if len(code) == 1:
            promoted = self._record_single_phrase(
                request_id,
                world,
                code[0],
            )

        return {
            "request_id": request_id,
            "status": "VERIFIED",
            "route": "DEVELOP",
            "phrases": [list(p) for p in code],
            "cost": list(phrase_set_cost(code)),
            "partition": [list(c) for c in partition(world, code)],
            "full_partition": [list(c) for c in full_partition(world)],
            "developmental": developmental,
            "minimum_search": minimum,
            "qualification": qualification_result,
            "promoted_phrase": promoted.data() if promoted else None,
            "phrase_acquisition_search_count": 1,
            "failed_reuse": failed_reuse,
        }
