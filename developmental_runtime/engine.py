from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from .commitment import Route, route, split_cell
from .intervention import lawful
from .state import DevelopmentalState
from .synthesis import SynthesisRegistry


@dataclass(frozen=True)
class EngineEvent:
    route: str
    intervention_id: str | None
    detail: Any


class DevelopmentalRuntime:
    def __init__(self, domain, synthesis: SynthesisRegistry):
        self.domain = domain
        self.synthesis = synthesis

    def develop_until_intervention(self, state: DevelopmentalState) -> tuple[DevelopmentalState, list[EngineEvent]]:
        events: list[EngineEvent] = []
        decision = route(self.domain, state)
        events.append(EngineEvent(decision.route.name, None, decision.reason))
        if decision.route is Route.DEVELOP_PROBES:
            pid = self.synthesis.synthesize_probe_extension(self.domain, state)
            if pid is None:
                return state.evolve(obstructions=state.obstructions + ("PROBE_LANGUAGE_OBSTRUCTION",)), events
            hook = getattr(self.domain, "prepare_probe_extension", None)
            state = hook(state, pid) if hook is not None else state.evolve(probe_language=frozenset(set(state.probe_language) | {pid}))
            events.append(EngineEvent("SYNTHESIZE_PROBE", pid, {"added": pid}))
            decision = route(self.domain, state)
            events.append(EngineEvent(decision.route.name, None, decision.reason))
        return state, events

    def execute_probe(self, state: DevelopmentalState, actual_world: Any) -> tuple[DevelopmentalState, EngineEvent]:
        decision = route(self.domain, state)
        if decision.route is not Route.PROBE or decision.policy is None or decision.policy.tree.probe_id is None:
            raise RuntimeError(f"probe not licensed: {decision}")
        pid = decision.policy.tree.probe_id
        record = self.domain.execute(state, actual_world, self.domain.intervention(pid))
        if not lawful(record):
            raise RuntimeError("unlawful probe transition")
        observed = record.effect["observation"]
        survivors = split_cell(self.domain, state, state.hypotheses, pid)[observed]
        successor = record.successor.evolve(
            hypotheses=survivors,
            quotient={"probe": pid, "outcome": observed, "cell": tuple(sorted(survivors))},
            certificates=state.certificates + (record.certificate,),
        )
        successor = self.synthesis.observe_verified_probe_transition(self.domain, state, successor, pid, record)
        learned = successor.metadata.get("learned_probe_operators", ())
        return successor, EngineEvent(
            "EXECUTE_PROBE",
            pid,
            {"outcome": observed, "survivors": sorted(survivors), "learned_probe_operators": list(learned)},
        )

    def execute_common_continuation(self, state: DevelopmentalState, actual_world: Any) -> tuple[DevelopmentalState, EngineEvent]:
        decision = route(self.domain, state)
        if decision.route is not Route.ACT or not decision.commitments:
            raise RuntimeError(f"action not licensed: {decision}")
        iid = sorted(decision.commitments)[0]
        record = self.domain.execute(state, actual_world, self.domain.intervention(iid))
        if not lawful(record):
            raise RuntimeError("selected continuation was not lawful")
        successor = record.successor.evolve(certificates=state.certificates + ((record.certificate or {"intervention": iid}),))
        return successor, EngineEvent("EXECUTE_CONTINUATION", iid, {"terminal": record.terminal.name, "effect": record.effect})
