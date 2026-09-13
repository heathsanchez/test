#!/usr/bin/env python3
"""Frozen V15 consequence-governed parametric schema learner."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Iterable, List, Mapping, Optional, Sequence, Tuple

from basis import (
    Pattern,
    Token,
    VerifiedLiteral,
    bindings_for,
    generate_partitions,
    instantiate,
    is_refinement,
    parameter_count,
    pattern_fits,
    pattern_fits_all,
    schema_id,
)


@dataclass(frozen=True)
class CompiledSchema:
    schema_id: str
    pattern: Pattern
    parameter_count: int
    provenance: Tuple[str, ...]
    lower_dependency: str = "V14"

    def data(self) -> Any:
        return {
            "schema_id": self.schema_id,
            "pattern": list(self.pattern),
            "parameter_count": self.parameter_count,
            "provenance": list(self.provenance),
            "lower_dependency": self.lower_dependency,
        }


class Kernel:
    @staticmethod
    def _authority(literals: Sequence[VerifiedLiteral]) -> Optional[Dict[str, Any]]:
        if not literals:
            return {
                "status": "UNKNOWN_AUTHORITY",
                "reason": "no_verified_literals",
            }
        if any(not lit.authoritative() for lit in literals):
            return {
                "status": "UNKNOWN_AUTHORITY",
                "reason": "literal_not_authoritative",
            }
        n = len(literals[0].tokens)
        if any(len(lit.tokens) != n for lit in literals):
            return {
                "status": "TYPE_MISMATCH",
                "reason": "literal_lengths_differ",
            }
        return None

    @staticmethod
    def exact_minimum(literals: Sequence[VerifiedLiteral]) -> Dict[str, Any]:
        auth = Kernel._authority(literals)
        if auth:
            return auth
        n = len(literals[0].tokens)
        universe = generate_partitions(n)
        fits = [p for p in universe if pattern_fits_all(p, literals)]
        if not fits:
            return {
                "status": "CERTIFIED_NO_SCHEMA",
                "candidate_count": len(universe),
            }
        min_params = min(parameter_count(p) for p in fits)
        minima = [p for p in fits if parameter_count(p) == min_params]
        return {
            "status": "VERIFIED",
            "candidate_count": len(universe),
            "fitting_count": len(fits),
            "minimum_parameter_count": min_params,
            "minimum_patterns": [list(p) for p in minima],
            "all_fitting_patterns": [list(p) for p in fits],
        }

    @staticmethod
    def first_obstruction(
        pattern: Pattern,
        literals: Sequence[VerifiedLiteral],
    ) -> Optional[Dict[str, Any]]:
        for li, lit in enumerate(literals):
            if pattern_fits(pattern, lit):
                continue
            for i in range(len(pattern)):
                for j in range(i + 1, len(pattern)):
                    if (
                        pattern[i] == pattern[j]
                        and lit.tokens[i] != lit.tokens[j]
                    ):
                        return {
                            "literal_index": li,
                            "position_pair": [i, j],
                            "observed_tokens": [lit.tokens[i], lit.tokens[j]],
                        }
        return None

    def develop(
        self,
        batches: Sequence[Sequence[VerifiedLiteral]],
        *,
        allow_split: bool = True,
    ) -> Dict[str, Any]:
        all_literals: List[VerifiedLiteral] = []
        if not batches or not batches[0]:
            return {
                "status": "UNKNOWN_AUTHORITY",
                "reason": "no_training_batch",
            }

        first_lit = batches[0][0]
        n = len(first_lit.tokens)
        current: Pattern = tuple(0 for _ in range(n))
        generations = []

        for bi, batch in enumerate(batches):
            all_literals.extend(batch)
            auth = self._authority(all_literals)
            if auth:
                return {
                    **auth,
                    "generations": generations,
                }

            if pattern_fits_all(current, all_literals):
                generations.append({
                    "batch": bi,
                    "status": "NO_CHANGE",
                    "pattern_before": list(current),
                    "pattern_after": list(current),
                    "parameter_count": parameter_count(current),
                    "obstruction": None,
                })
                continue

            obstruction = self.first_obstruction(current, all_literals)
            if not allow_split:
                generations.append({
                    "batch": bi,
                    "status": "BLOCKED",
                    "pattern_before": list(current),
                    "obstruction": obstruction,
                })
                return {
                    "status": "CERTIFIED_SCHEMA_INADEQUACY",
                    "current_pattern": list(current),
                    "obstruction": obstruction,
                    "generations": generations,
                }

            universe = generate_partitions(n)
            lawful = [
                p
                for p in universe
                if is_refinement(p, current)
                and pattern_fits_all(p, all_literals)
            ]
            if not lawful:
                return {
                    "status": "CERTIFIED_NO_REFINEMENT",
                    "current_pattern": list(current),
                    "obstruction": obstruction,
                    "generations": generations,
                }

            min_params = min(parameter_count(p) for p in lawful)
            minima = [
                p for p in lawful if parameter_count(p) == min_params
            ]

            if len(minima) > 1:
                generations.append({
                    "batch": bi,
                    "status": "FRONTIER",
                    "pattern_before": list(current),
                    "obstruction": obstruction,
                    "frontier": [list(p) for p in minima],
                    "minimum_parameter_count": min_params,
                })
                return {
                    "status": "VERIFIED_FRONTIER",
                    "frontier": [list(p) for p in minima],
                    "generations": generations,
                }

            new_pattern = minima[0]
            generations.append({
                "batch": bi,
                "status": "SPLIT",
                "pattern_before": list(current),
                "pattern_after": list(new_pattern),
                "obstruction": obstruction,
                "minimum_parameter_count": min_params,
                "candidate_count": len(universe),
            })
            current = new_pattern

        exact = self.exact_minimum(all_literals)
        return {
            "status": "VERIFIED",
            "pattern": list(current),
            "parameter_count": parameter_count(current),
            "generations": generations,
            "exact_minimum": exact,
            "literal_count": len(all_literals),
        }

    @staticmethod
    def distinction_support(
        pattern: Pattern,
        literals: Sequence[VerifiedLiteral],
    ) -> Dict[str, Any]:
        """
        A literal witnesses every schema distinction if it instantiates all
        parameter classes with pairwise-distinct lower tokens.
        """
        pc = parameter_count(pattern)
        witnesses = []
        for i, lit in enumerate(literals):
            b = bindings_for(pattern, lit)
            if b is None:
                continue
            if len(set(b)) == pc:
                witnesses.append(i)
        return {
            "witness_indices": witnesses,
            "witness_count": len(witnesses),
        }

    def compile_schema(
        self,
        pattern: Pattern,
        literals: Sequence[VerifiedLiteral],
    ) -> Dict[str, Any]:
        auth = self._authority(literals)
        if auth:
            return auth
        if not pattern_fits_all(pattern, literals):
            return {
                "status": "REPLAY_FAILED",
                "reason": "schema_does_not_fit_training_literals",
            }

        support = self.distinction_support(pattern, literals)
        if support["witness_count"] < 2:
            return {
                "status": "PROVISIONAL_SCHEMA",
                "pattern": list(pattern),
                "support": support,
            }

        provenance = []
        for i in support["witness_indices"]:
            provenance.extend(literals[i].provenance)

        compiled = CompiledSchema(
            schema_id=schema_id(pattern),
            pattern=tuple(pattern),
            parameter_count=parameter_count(pattern),
            provenance=tuple(sorted(set(provenance))),
        )
        return {
            "status": "VERIFIED",
            "compiled_schema": compiled.data(),
            "support": support,
        }

    @staticmethod
    def apply_schema(
        compiled: Mapping[str, Any],
        bindings: Sequence[Token],
    ) -> Dict[str, Any]:
        pattern = tuple(int(x) for x in compiled["pattern"])
        try:
            out = instantiate(pattern, bindings)
        except ValueError as exc:
            return {
                "status": "TYPE_MISMATCH",
                "reason": str(exc),
            }
        return {
            "status": "VERIFIED",
            "output": list(out),
            "constructor_cost": 1,
        }

    @staticmethod
    def replay_target(
        compiled: Mapping[str, Any],
        target: Sequence[Token],
    ) -> Dict[str, Any]:
        pattern = tuple(int(x) for x in compiled["pattern"])
        lit = VerifiedLiteral(
            tokens=tuple(target),
            provenance=("heldout_replay",),
            verified=True,
        )
        b = bindings_for(pattern, lit)
        if b is None:
            return {
                "status": "REPLAY_FAILED",
                "reason": "target_violates_schema_equalities",
                "target": list(target),
            }
        out = instantiate(pattern, b)
        return {
            "status": "VERIFIED" if tuple(out) == tuple(target) else "REPLAY_FAILED",
            "bindings": list(b),
            "output": list(out),
        }

    @staticmethod
    def construct_under_budget(
        target: Sequence[Token],
        compiled: Optional[Mapping[str, Any]],
        budget: int,
    ) -> Dict[str, Any]:
        target = tuple(target)
        if compiled is not None:
            replay = Kernel.replay_target(compiled, target)
            if replay.get("status") == "VERIFIED":
                cost = 1
                return {
                    **replay,
                    "route": "COMPILED_SCHEMA",
                    "constructor_cost": cost,
                    "budget": int(budget),
                    "within_budget": cost <= int(budget),
                    "status": "VERIFIED" if cost <= int(budget) else "UNKNOWN_BUDGET",
                }

        # Cold direct binary concatenation.
        cost = max(0, len(target) - 1)
        return {
            "status": "VERIFIED" if cost <= int(budget) else "UNKNOWN_BUDGET",
            "route": "DIRECT_CONCAT",
            "constructor_cost": cost,
            "budget": int(budget),
            "within_budget": cost <= int(budget),
            "output": list(target),
        }
