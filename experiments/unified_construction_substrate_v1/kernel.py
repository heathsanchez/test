#!/usr/bin/env python3
"""
Frozen-candidate generic developmental kernel over MDC-L1.

The kernel never receives a repair label such as "representation", "memory",
"solver", or "edit".  It sees only:
  * a current typed program,
  * an external authority,
  * finite search bounds,
  * retained verified programs.

It searches two standardized continuation channels from the same substrate:
  1. replacement programs of the current signature;
  2. meta-programs Code[A,B] -> Code[A,B] applied to the current program.

Both object programs and edits are MDC-L1 Program values.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable, Dict, Iterable, List, Mapping, Optional, Sequence, Tuple

from mdc_l1 import CODE, Program, Ty, synthesize, synthesize_meta


Eval = Dict[str, Any]


@dataclass(frozen=True)
class CostVector:
    discovery: int
    program: int
    retained: int = 0

    def key(self) -> Tuple[int, int, int]:
        return (self.discovery, self.program, self.retained)


@dataclass
class Candidate:
    program: Program
    route: str
    generator: Optional[Program]
    cost: CostVector

    def identity(self) -> str:
        return self.program.digest()


@dataclass
class Retained:
    program: Program
    origin: str
    warrant: Any = None
    scope: Any = None
    dependencies: Tuple[str, ...] = ()
    revocation: Any = None


@dataclass
class Authority:
    """External authority contract.

    evaluate(program) must return:
      accepted: bool
      protected_ok: bool (default True)
      witness: optional finite evidence
      loss: optional diagnostic only

    coherent() checks the protected evidence / authority regime itself.
    It is deliberately separate from candidate evaluation.
    """

    evaluate: Callable[[Program], Eval]
    coherent: Callable[[], bool] = lambda: True
    residual: Optional[Callable[[Program], Any]] = None


@dataclass
class DevelopmentRequest:
    request_id: str
    current: Program
    authority: Authority
    max_object_cost: int
    max_edit_cost: int
    object_search_complete: bool
    edit_search_complete: bool
    allow_replacements: bool = True
    allow_edits: bool = True


@dataclass
class KernelState:
    retained: List[Retained] = field(default_factory=list)


def _accepted(ev: Mapping[str, Any]) -> bool:
    return bool(ev.get("accepted")) and bool(ev.get("protected_ok", True))


def _normalize_eval(ev: Mapping[str, Any]) -> Eval:
    if "accepted" not in ev:
        raise ValueError("authority result missing accepted")
    out = dict(ev)
    out.setdefault("protected_ok", True)
    out.setdefault("loss", 0 if out["accepted"] else 1)
    return out


class DevelopmentalKernel:
    def __init__(self) -> None:
        self.state = KernelState()

    def _eval(self, auth: Authority, program: Program) -> Eval:
        return _normalize_eval(auth.evaluate(program))

    def _retained_candidates(self, req: DevelopmentRequest) -> Iterable[Candidate]:
        for r in self.state.retained:
            if r.program.inputs == req.current.inputs and r.program.output == req.current.output:
                yield Candidate(
                    program=r.program,
                    route="REUSE",
                    generator=None,
                    cost=CostVector(discovery=0, program=r.program.cost, retained=1),
                )

    def _replacement_candidates(self, req: DevelopmentRequest) -> Iterable[Candidate]:
        if not req.allow_replacements:
            return
        for discovery_cost, program in synthesize(
            req.current.inputs, req.current.output, req.max_object_cost
        ):
            yield Candidate(
                program=program,
                route="REPLACE",
                generator=None,
                cost=CostVector(
                    discovery=discovery_cost,
                    program=program.cost,
                    retained=0,
                ),
            )

    def _edit_candidates(self, req: DevelopmentRequest) -> Iterable[Candidate]:
        if not req.allow_edits:
            return

        code_ty = CODE(req.current.inputs, req.current.output)
        # Meta-program signature:
        #     Code[A,B] -> Code[A,B]
        for discovery_cost, edit in synthesize_meta(
            [code_ty], code_ty, req.max_edit_cost
        ):
            produced = edit.run(req.current)
            if not isinstance(produced, Program):
                raise TypeError("well-typed edit did not return Program")
            yield Candidate(
                program=produced,
                route="EDIT",
                generator=edit,
                cost=CostVector(
                    discovery=discovery_cost,
                    program=produced.cost,
                    retained=0,
                ),
            )

    def _finish(
        self,
        req: DevelopmentRequest,
        candidate: Candidate,
        evaluation: Eval,
        frontier: Sequence[Candidate],
        baseline: Eval,
        residual: Any,
    ) -> Eval:
        if candidate.route not in {"NO_CHANGE", "REUSE"}:
            if all(r.program.digest() != candidate.program.digest() for r in self.state.retained):
                self.state.retained.append(
                    Retained(
                        program=candidate.program,
                        origin=req.request_id,
                        warrant=evaluation.get("witness"),
                    )
                )

        return {
            "request_id": req.request_id,
            "status": "VERIFIED",
            "route": candidate.route,
            "baseline": baseline,
            "residual": residual,
            "active_program_digest": candidate.program.digest(),
            "active_program_cost": candidate.program.cost,
            "generator_digest": (
                candidate.generator.digest() if candidate.generator is not None else None
            ),
            "generator_cost": (
                candidate.generator.cost if candidate.generator is not None else None
            ),
            "frontier": [
                {
                    "program_digest": c.program.digest(),
                    "route": c.route,
                    "cost": c.cost.key(),
                    "generator_digest": (
                        c.generator.digest() if c.generator is not None else None
                    ),
                }
                for c in frontier
            ],
            "frontier_size": len(frontier),
            "evaluation": evaluation,
            "retained_count": len(self.state.retained),
        }

    def run(self, req: DevelopmentRequest) -> Eval:
        if req.max_object_cost < 0 or req.max_edit_cost < 0:
            raise ValueError("search costs must be nonnegative")

        if not bool(req.authority.coherent()):
            return {
                "request_id": req.request_id,
                "status": "AUTHORITY_CONFLICT",
                "route": "STOP",
            }

        baseline = self._eval(req.authority, req.current)

        # No change when the present already settles the encounter.
        if _accepted(baseline):
            cand = Candidate(
                req.current,
                "NO_CHANGE",
                None,
                CostVector(discovery=0, program=req.current.cost, retained=0),
            )
            return self._finish(
                req, cand, baseline, [cand], baseline, residual=None
            )

        residual = (
            req.authority.residual(req.current)
            if req.authority.residual is not None
            else None
        )

        # Reuse is tested before developmental search.
        for cand in sorted(
            self._retained_candidates(req),
            key=lambda c: (c.cost.key(), c.program.digest()),
        ):
            ev = self._eval(req.authority, cand.program)
            if _accepted(ev):
                return self._finish(
                    req, cand, ev, [cand], baseline, residual
                )

        # The candidate universe is generated only by the frozen MDC-L1
        # substrate.  No challenge-specific host repair operation is admitted.
        by_digest: Dict[str, Candidate] = {}

        def admit_candidate(c: Candidate) -> None:
            d = c.identity()
            old = by_digest.get(d)
            if old is None or (c.cost.key(), c.route) < (old.cost.key(), old.route):
                by_digest[d] = c

        for c in self._replacement_candidates(req):
            admit_candidate(c)
        for c in self._edit_candidates(req):
            admit_candidate(c)

        accepted: List[Tuple[Candidate, Eval]] = []
        tested = 0
        for c in sorted(
            by_digest.values(),
            key=lambda x: (x.cost.key(), x.route, x.program.digest()),
        ):
            tested += 1
            ev = self._eval(req.authority, c.program)
            if _accepted(ev):
                accepted.append((c, ev))

        if accepted:
            best_cost = min(c.cost.key() for c, _ in accepted)
            survivors = [(c, ev) for c, ev in accepted if c.cost.key() == best_cost]
            frontier = [c for c, _ in survivors]

            # Preserve non-canonicity rather than silently selecting by hash.
            if len(survivors) > 1:
                return {
                    "request_id": req.request_id,
                    "status": "UNKNOWN_CHOICE",
                    "route": "STOP",
                    "baseline": baseline,
                    "residual": residual,
                    "tested_candidate_count": tested,
                    "frontier": [
                        {
                            "program_digest": c.program.digest(),
                            "route": c.route,
                            "cost": c.cost.key(),
                            "generator_digest": (
                                c.generator.digest() if c.generator is not None else None
                            ),
                        }
                        for c, _ in survivors
                    ],
                    "frontier_size": len(survivors),
                }

            c, ev = survivors[0]
            out = self._finish(req, c, ev, frontier, baseline, residual)
            out["tested_candidate_count"] = tested
            return out

        # Conservative stopping: distinguish ordinary object-search
        # incompleteness from edit-language incompleteness.
        if req.allow_replacements and not req.object_search_complete:
            status = "UNKNOWN_SEARCH"
        elif req.allow_edits and not req.edit_search_complete:
            status = "UNKNOWN_EXPRESSIVITY"
        elif req.object_search_complete and req.edit_search_complete:
            status = "CERTIFIED_NO_REPAIR_IN_DECLARED_CLASS"
        else:
            status = "UNKNOWN"

        return {
            "request_id": req.request_id,
            "status": status,
            "route": "STOP",
            "baseline": baseline,
            "residual": residual,
            "tested_candidate_count": tested,
            "retained_count": len(self.state.retained),
        }
