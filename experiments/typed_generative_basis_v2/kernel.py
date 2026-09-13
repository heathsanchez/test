#!/usr/bin/env python3
"""Generic developmental kernel over the frozen typed generative basis B2."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable, Dict, Iterable, List, Mapping, Optional, Sequence, Tuple

from basis import (
    Language, Program, Synthesizer, enumerate_languages, language_distance
)


Eval = Dict[str, Any]


@dataclass
class Authority:
    evaluate: Callable[[Language, Program], Eval]
    coherent: Callable[[], bool] = lambda: True
    residual: Optional[Callable[[Language, Program], Any]] = None


@dataclass
class Request:
    request_id: str
    current: Program
    authority: Authority
    max_type_depth: int
    max_language_edit: int
    max_program_cost: int
    search_complete: bool
    retain: bool = True


@dataclass
class Retained:
    language: Language
    program: Program
    origin: str
    warrant: Any = None


@dataclass
class Candidate:
    language: Language
    program: Program
    route: str
    transition_cost: int
    prospective_cost: int

    def cost_key(self) -> Tuple[int, int]:
        return (self.prospective_cost, self.transition_cost)

    def semantic_key(self) -> Tuple[str, str, str]:
        # Behavior quotient within an exact signature.  Different grammars
        # reaching the same function collapse to one developmental candidate.
        return (
            str(self.language.input_ty),
            str(self.language.output_ty),
            self.program.behavior_key(),
        )


class Kernel:
    def __init__(self) -> None:
        self.retained: List[Retained] = []

    @staticmethod
    def _norm(ev: Mapping[str, Any]) -> Eval:
        if "accepted" not in ev:
            raise ValueError("authority result missing accepted")
        out = dict(ev)
        out.setdefault("protected_ok", True)
        out.setdefault("loss", 0 if out["accepted"] else 1)
        return out

    @staticmethod
    def _accepted(ev: Mapping[str, Any]) -> bool:
        return bool(ev.get("accepted")) and bool(ev.get("protected_ok", True))

    def _eval(self, req: Request, p: Program) -> Eval:
        return self._norm(req.authority.evaluate(p.language, p))

    def _route(self, current: Program, candidate: Program) -> str:
        a, b = current.language, candidate.language
        if (
            candidate.digest() == current.digest()
            and a == b
        ):
            return "NO_CHANGE"
        if a.input_ty != b.input_ty or a.output_ty != b.output_ty:
            return "SIGNATURE"
        if a.ops != b.ops:
            if (
                b.ops.issubset(a.ops)
                and candidate.cost <= current.cost
            ):
                return "CONTRACT"
            return "GRAMMAR"
        if candidate.cost < current.cost:
            return "CONTRACT"
        return "REWRITE"

    def _candidate(self, req: Request, p: Program) -> Candidate:
        return Candidate(
            language=p.language,
            program=p,
            route=self._route(req.current, p),
            transition_cost=language_distance(req.current.language, p.language),
            prospective_cost=p.language.complexity() + p.cost,
        )

    def run(self, req: Request) -> Eval:
        if not req.authority.coherent():
            return {
                "request_id": req.request_id,
                "status": "AUTHORITY_CONFLICT",
                "route": "STOP",
            }

        baseline = self._eval(req, req.current)
        residual = (
            req.authority.residual(req.current.language, req.current)
            if req.authority.residual is not None
            else None
        )

        # Reuse previously compiled language+program before developmental search.
        for r in sorted(
            self.retained,
            key=lambda x: (
                x.language.complexity() + x.program.cost,
                x.program.digest(),
            ),
        ):
            ev = self._norm(req.authority.evaluate(r.language, r.program))
            if self._accepted(ev):
                return {
                    "request_id": req.request_id,
                    "status": "VERIFIED",
                    "route": "REUSE",
                    "baseline": baseline,
                    "residual": residual,
                    "language": r.language.data(),
                    "program_digest": r.program.digest(),
                    "program_cost": r.program.cost,
                    "evaluation": ev,
                    "tested_language_count": 0,
                    "tested_program_count": 0,
                }

        # Current realization participates in the same quotient/cost comparison.
        # This permits NO_CHANGE when minimal and CONTRACTION when a cheaper
        # behaviorally equivalent realization exists.
        semantic_best: Dict[Tuple[str, str, str], Tuple[Candidate, Eval]] = {}
        tested_languages = 0
        tested_programs = 0

        for lang in enumerate_languages(
            req.current.language,
            req.max_type_depth,
            req.max_language_edit,
        ):
            tested_languages += 1
            synth = Synthesizer(lang, req.max_program_cost)
            for p in synth.programs():
                tested_programs += 1
                ev = self._norm(req.authority.evaluate(lang, p))
                if not self._accepted(ev):
                    continue
                c = self._candidate(req, p)
                sk = c.semantic_key()
                old = semantic_best.get(sk)
                if old is None or (
                    c.cost_key(), c.program.digest()
                ) < (
                    old[0].cost_key(), old[0].program.digest()
                ):
                    semantic_best[sk] = (c, ev)

        # If the literal current program is accepted but the bounded synthesizer
        # did not regenerate it, preserve it as an admissible candidate.
        if self._accepted(baseline):
            cur = self._candidate(req, req.current)
            sk = cur.semantic_key()
            old = semantic_best.get(sk)
            if old is None or cur.cost_key() < old[0].cost_key():
                semantic_best[sk] = (cur, baseline)

        if semantic_best:
            accepted = list(semantic_best.values())
            best_cost = min(c.cost_key() for c, _ in accepted)
            frontier = [(c, ev) for c, ev in accepted if c.cost_key() == best_cost]

            if len(frontier) > 1:
                return {
                    "request_id": req.request_id,
                    "status": "UNKNOWN_CHOICE",
                    "route": "STOP",
                    "baseline": baseline,
                    "residual": residual,
                    "frontier_size": len(frontier),
                    "frontier": [
                        {
                            "language": c.language.data(),
                            "program_digest": c.program.digest(),
                            "program_cost": c.program.cost,
                            "prospective_cost": c.prospective_cost,
                            "transition_cost": c.transition_cost,
                            "behavior": c.program.behavior(),
                        }
                        for c, _ in frontier
                    ],
                    "tested_language_count": tested_languages,
                    "tested_program_count": tested_programs,
                }

            c, ev = frontier[0]
            if req.retain and c.route not in {"NO_CHANGE", "REUSE"}:
                # Deduplicate retained capabilities by exact language+behavior.
                if not any(
                    r.language == c.language
                    and r.program.behavior_key() == c.program.behavior_key()
                    for r in self.retained
                ):
                    self.retained.append(
                        Retained(c.language, c.program, req.request_id, ev.get("witness"))
                    )

            return {
                "request_id": req.request_id,
                "status": "VERIFIED",
                "route": c.route,
                "baseline": baseline,
                "residual": residual,
                "language": c.language.data(),
                "language_digest": c.language.digest(),
                "program_digest": c.program.digest(),
                "program_cost": c.program.cost,
                "prospective_cost": c.prospective_cost,
                "transition_cost": c.transition_cost,
                "behavior": c.program.behavior(),
                "evaluation": ev,
                "frontier_size": 1,
                "tested_language_count": tested_languages,
                "tested_program_count": tested_programs,
                "retained_count": len(self.retained),
            }

        return {
            "request_id": req.request_id,
            "status": (
                "CERTIFIED_NO_LANGUAGE_IN_DECLARED_BASIS_REGION"
                if req.search_complete
                else "UNKNOWN_SEARCH"
            ),
            "route": "STOP",
            "baseline": baseline,
            "residual": residual,
            "tested_language_count": tested_languages,
            "tested_program_count": tested_programs,
            "retained_count": len(self.retained),
        }
