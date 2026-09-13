#!/usr/bin/env python3
"""
Frozen generic developmental kernel.

The kernel is intentionally ignorant of challenge semantics.  It receives:
  * an initial state (or a previously retained context state),
  * opaque state-transforming actions,
  * an external evaluator returning accepted/loss/protected_ok/witness,
  * optional frozen future evaluators,
  * optional held-out evaluator,
  * a finite search depth and completeness flag.

It never inspects challenge source, action implementations, action names beyond
opaque IDs, or expected answers.
"""
from __future__ import annotations

import copy
import hashlib
import json
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, Iterable, List, Optional, Sequence, Tuple


Json = Dict[str, Any]
State = Dict[str, Any]


def _canon(x: Any) -> Any:
    if isinstance(x, dict):
        return {str(k): _canon(v) for k, v in sorted(x.items(), key=lambda kv: str(kv[0]))}
    if isinstance(x, (list, tuple)):
        return [_canon(v) for v in x]
    if isinstance(x, set):
        return sorted((_canon(v) for v in x), key=lambda v: json.dumps(v, sort_keys=True))
    return x


def state_key(state: State) -> str:
    return json.dumps(_canon(state), sort_keys=True, separators=(",", ":"))


def digest(x: Any) -> str:
    return hashlib.sha256(
        json.dumps(_canon(x), sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()


@dataclass(frozen=True)
class Action:
    action_id: str
    apply: Callable[[State], Optional[State]]
    cost: int = 1


@dataclass
class Challenge:
    challenge_id: str
    initial_state: State
    actions: Sequence[Action]
    evaluate: Callable[[State], Json]
    max_depth: int
    future: Sequence[Callable[[State], Json]] = field(default_factory=tuple)
    holdout: Optional[Callable[[State], Json]] = None
    context_id: Optional[str] = None
    use_context: bool = False
    retain_program: bool = True
    completeness_certified: bool = True


@dataclass
class RetainedProgram:
    origin: str
    action_ids: Tuple[str, ...]


class DevelopmentalKernel:
    def __init__(self) -> None:
        self.retained: List[RetainedProgram] = []
        self.contexts: Dict[str, State] = {}

    @staticmethod
    def _accepted(ev: Json) -> bool:
        return bool(ev.get("accepted")) and bool(ev.get("protected_ok", True))

    @staticmethod
    def _safe_eval(fn: Callable[[State], Json], state: State) -> Json:
        ev = fn(copy.deepcopy(state))
        if not isinstance(ev, dict):
            raise TypeError("evaluator must return a dict")
        if "accepted" not in ev:
            raise ValueError("evaluator result missing accepted")
        out = _canon(ev)
        out.setdefault("protected_ok", True)
        out.setdefault("loss", 0 if out["accepted"] else 1)
        return out

    @staticmethod
    def _apply_program(
        start: State,
        program: Sequence[str],
        action_map: Dict[str, Action],
    ) -> Optional[State]:
        s = copy.deepcopy(start)
        for aid in program:
            a = action_map.get(aid)
            if a is None:
                return None
            nxt = a.apply(copy.deepcopy(s))
            if nxt is None:
                return None
            s = nxt
        return s

    def _future_trace(self, ch: Challenge, state: State) -> Tuple[bool, List[Json]]:
        trace: List[Json] = []
        for fn in ch.future:
            ev = self._safe_eval(fn, state)
            trace.append(ev)
            if not self._accepted(ev):
                return False, trace
        return True, trace

    def _finish(
        self,
        ch: Challenge,
        start: State,
        final: State,
        route: str,
        program: Sequence[str],
        baseline: Json,
        search_levels: List[Json],
        future_trace: Sequence[Json] = (),
        retained_origin: Optional[str] = None,
    ) -> Json:
        final_eval = self._safe_eval(ch.evaluate, final)
        holdout = self._safe_eval(ch.holdout, final) if ch.holdout is not None else None

        if ch.context_id is not None:
            self.contexts[ch.context_id] = copy.deepcopy(final)

        if program and ch.retain_program and route != "REUSE":
            rp = RetainedProgram(ch.challenge_id, tuple(program))
            if all(x.action_ids != rp.action_ids for x in self.retained):
                self.retained.append(rp)

        return {
            "challenge_id": ch.challenge_id,
            "status": "RESOLVED",
            "route": route,
            "start_state": _canon(start),
            "start_state_digest": digest(start),
            "baseline": baseline,
            "program": list(program),
            "program_length": len(program),
            "retained_origin": retained_origin,
            "final_state": _canon(final),
            "final_state_digest": digest(final),
            "final_evaluation": final_eval,
            "future_trace": list(future_trace),
            "holdout": holdout,
            "search_levels": search_levels,
            "retained_library_size_after": len(self.retained),
        }

    def run(self, ch: Challenge) -> Json:
        if ch.max_depth < 0:
            raise ValueError("max_depth must be nonnegative")
        action_map = {a.action_id: a for a in ch.actions}
        if len(action_map) != len(ch.actions):
            raise ValueError("action IDs must be unique inside a challenge")

        if ch.use_context and ch.context_id is not None and ch.context_id in self.contexts:
            start = copy.deepcopy(self.contexts[ch.context_id])
            start_source = "context"
        else:
            start = copy.deepcopy(ch.initial_state)
            start_source = "initial"

        baseline = self._safe_eval(ch.evaluate, start)

        # Constitution: never change an already sufficient present.
        if self._accepted(baseline):
            ok_future, future_trace = self._future_trace(ch, start)
            if ok_future:
                result = self._finish(
                    ch, start, start, "NO_CHANGE", (), baseline, [], future_trace
                )
                result["start_source"] = start_source
                return result

        # Try previously retained mechanisms before rediscovering them.
        for rp in sorted(self.retained, key=lambda r: (len(r.action_ids), r.action_ids, r.origin)):
            candidate = self._apply_program(start, rp.action_ids, action_map)
            if candidate is None:
                continue
            ev = self._safe_eval(ch.evaluate, candidate)
            if not self._accepted(ev):
                continue
            ok_future, future_trace = self._future_trace(ch, candidate)
            if not ok_future:
                continue
            result = self._finish(
                ch, start, candidate, "REUSE", rp.action_ids, baseline, [],
                future_trace, retained_origin=rp.origin,
            )
            result["start_source"] = start_source
            return result

        # Level-complete state-space search.  States, not syntactic programs,
        # are the semantic candidates; equivalent programs are deduplicated.
        frontier: Dict[str, Tuple[State, Tuple[str, ...]]] = {
            state_key(start): (copy.deepcopy(start), tuple())
        }
        seen = {state_key(start)}
        search_levels: List[Json] = []

        for depth in range(1, ch.max_depth + 1):
            nxt: Dict[str, Tuple[State, Tuple[str, ...]]] = {}
            generated_records: List[Json] = []

            for _, (state, program) in sorted(frontier.items()):
                for aid, action in sorted(action_map.items()):
                    out = action.apply(copy.deepcopy(state))
                    if out is None:
                        continue
                    key = state_key(out)
                    new_program = program + (aid,)
                    if key in seen or key in nxt:
                        continue
                    nxt[key] = (out, new_program)

            accepted_now: List[Tuple[State, Tuple[str, ...], Json]] = []
            for key, (state, program) in sorted(nxt.items()):
                ev = self._safe_eval(ch.evaluate, state)
                generated_records.append({
                    "state_digest": digest(state),
                    "program": list(program),
                    "accepted": self._accepted(ev),
                    "loss": ev.get("loss"),
                    "protected_ok": ev.get("protected_ok", True),
                    "witness_digest": digest(ev.get("witness")) if ev.get("witness") is not None else None,
                })
                if self._accepted(ev):
                    accepted_now.append((state, program, ev))

            level_record: Json = {
                "depth": depth,
                "generated_state_count": len(nxt),
                "accepted_current_count": len(accepted_now),
                "records": generated_records,
            }

            if accepted_now:
                survivors = accepted_now
                stage_counts = [len(survivors)]
                traces_by_state: Dict[str, List[Json]] = {
                    state_key(s): [] for s, _, _ in survivors
                }

                for fn in ch.future:
                    kept = []
                    for s, p, ev in survivors:
                        fev = self._safe_eval(fn, s)
                        traces_by_state[state_key(s)].append(fev)
                        if self._accepted(fev):
                            kept.append((s, p, ev))
                    survivors = kept
                    stage_counts.append(len(survivors))
                    if not survivors:
                        break

                level_record["future_survivor_counts"] = stage_counts
                search_levels.append(level_record)

                if len(survivors) == 1:
                    s, p, _ = survivors[0]
                    route = "SEARCH_SELECTED"
                    if len(accepted_now) > 1 and len(ch.future) > 0:
                        route = "FUTURE_SELECTED"
                    result = self._finish(
                        ch, start, s, route, p, baseline, search_levels,
                        traces_by_state.get(state_key(s), []),
                    )
                    result["start_source"] = start_source
                    return result

                if len(survivors) > 1:
                    return {
                        "challenge_id": ch.challenge_id,
                        "status": "UNKNOWN_NONCANONICAL",
                        "route": "STOP",
                        "start_source": start_source,
                        "start_state": _canon(start),
                        "baseline": baseline,
                        "survivor_count": len(survivors),
                        "survivor_state_digests": [digest(s) for s, _, _ in survivors],
                        "search_levels": search_levels,
                        "retained_library_size_after": len(self.retained),
                    }

            else:
                search_levels.append(level_record)

            seen.update(nxt)
            frontier = nxt
            if not frontier:
                break

        status = (
            "CERTIFIED_NO_REPAIR_IN_CLASS"
            if ch.completeness_certified
            else "UNKNOWN_SEARCH"
        )
        return {
            "challenge_id": ch.challenge_id,
            "status": status,
            "route": "STOP",
            "start_source": start_source,
            "start_state": _canon(start),
            "baseline": baseline,
            "search_levels": search_levels,
            "retained_library_size_after": len(self.retained),
        }

    def run_sequence(self, challenges: Iterable[Challenge]) -> Json:
        results = []
        for ch in challenges:
            results.append(self.run(ch))
        return {
            "results": results,
            "retained_programs": [
                {"origin": r.origin, "action_ids": list(r.action_ids)}
                for r in self.retained
            ],
            "contexts": {k: _canon(v) for k, v in sorted(self.contexts.items())},
        }
