from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping

from developmental_runtime import (
    DevelopmentalState,
    Intervention,
    InterventionKind,
    ObligationEvidence,
    Terminal,
    TransitionRecord,
)


@dataclass
class SAIRRuntimeAdapter:
    rows: list[dict[str, Any]]
    programs: Mapping[str, dict[str, Any]]

    def prepare_probe_extension(self, state: DevelopmentalState, probe_id: str) -> DevelopmentalState:
        return state.evolve(
            probe_language=frozenset(set(state.probe_language) | {probe_id}),
            metadata={**state.metadata, "candidate_probe_id": probe_id},
        )

    def assume_probe_outcome(self, state: DevelopmentalState, probe_id: str, outcome: Any, cell) -> DevelopmentalState:
        return state.evolve(
            hypotheses=frozenset(cell),
            metadata={**state.metadata, "decision_probe_id": probe_id, "assumed_probe_outcome": outcome},
        )

    def intervention(self, intervention_id: str) -> Intervention:
        if intervention_id in self.programs:
            p = self.programs[intervention_id]
            return Intervention(intervention_id, InterventionKind.PROBE, p, float(p["cost"]))
        if intervention_id == "ACCEPT_COUNTERMODEL_WITNESS":
            return Intervention(intervention_id, InterventionKind.TERMINAL, intervention_id, 0.0)
        if intervention_id == "ADVANCE_PROOF_SEARCH_FRONTIER":
            return Intervention(intervention_id, InterventionKind.SEARCH, intervention_id, 1.0)
        raise KeyError(intervention_id)

    def probe_outcome(self, state: DevelopmentalState, world_id: int, probe_id: str) -> Any:
        row = self.rows[world_id]
        p = self.programs[probe_id]
        if p["kind"] == "atom":
            return row["atom_values"][probe_id]
        return tuple(row["atom_values"][child] for child in p["children"])

    def probe_order(self, probe_id: str) -> int | None:
        p = self.programs.get(probe_id)
        if not p or p.get("kind") != "atom":
            return None
        return int(p.get("order")) if p.get("order") is not None else None

    def probe_direction(self, probe_id: str) -> str | None:
        p = self.programs.get(probe_id)
        if not p or p.get("kind") != "atom":
            return None
        d = p.get("direction")
        return str(d) if d is not None else None

    def execute(self, state: DevelopmentalState, world_id: int, intervention: Intervention) -> TransitionRecord:
        row = self.rows[world_id]
        yes = lambda cert=None: ObligationEvidence(True, cert)
        no = lambda cert=None: ObligationEvidence(False, cert)

        if intervention.kind is InterventionKind.PROBE:
            outcome = self.probe_outcome(state, world_id, intervention.id)
            successor = state.evolve(metadata={
                **state.metadata,
                "decision_probe_id": intervention.id,
                "last_probe": intervention.id,
                "last_probe_outcome": outcome,
            })
            return TransitionRecord(
                intervention=intervention,
                effect={"observation": outcome},
                obligations={"VERIFIED": yes("exact-model-query"), "ADMISSIBLE": yes(), "OBSERVATION_SOUND": yes()},
                successor=successor,
                terminal=Terminal.NONE,
                certificate={"probe": intervention.id, "outcome": outcome},
                cost=intervention.cost,
            )

        decision_probe = state.metadata.get("decision_probe_id")
        if not decision_probe:
            return TransitionRecord(intervention, {}, {"VERIFIED": no(), "ADMISSIBLE": no()}, state)
        world_outcome = self.probe_outcome(state, world_id, decision_probe)
        order = self.probe_order(decision_probe)
        direction = self.probe_direction(decision_probe)
        target_oriented = direction == "FORWARD"

        if intervention.id == "ACCEPT_COUNTERMODEL_WITNESS":
            ok = bool(target_oriented and world_outcome == 1)
            obligations = {
                "VERIFIED": yes("independently-rechecked-model") if ok else no(),
                "ADMISSIBLE": yes() if ok else no(),
                "TARGET_ORIENTED": yes("premise-true/target-false") if target_oriented else no("reverse query is not a target countermodel"),
                "TERMINAL_CERTIFIED": yes("countermodel") if ok else no(),
            }
            return TransitionRecord(
                intervention,
                {"accepted_countermodel": ok, "order": order, "direction": direction},
                obligations,
                state,
                terminal=Terminal.REFUTED if ok else Terminal.NONE,
                certificate={"world": row["id"], "probe": decision_probe, "order": order, "direction": direction} if ok else None,
            )

        if intervention.id == "ADVANCE_PROOF_SEARCH_FRONTIER":
            exhausted = int(state.problem_state.get("countermodel_exhausted_through_order", 0)) if isinstance(state.problem_state, dict) else 0
            ok = bool(target_oriented and world_outcome == 0 and order is not None and order > exhausted)
            successor = state.evolve(
                problem_state={
                    "source": row["id"],
                    "countermodel_exhausted_through_order": order if ok else exhausted,
                },
                metadata={**state.metadata, "proof_frontier_advanced_to": order if ok else exhausted},
            )
            obligations = {
                "VERIFIED": yes(f"order{order}-exhaustion") if ok else no(),
                "ADMISSIBLE": yes() if ok else no(),
                "TARGET_ORIENTED": yes("target countermodel search") if target_oriented else no("reverse nonexistence does not exhaust target countermodels"),
                "SEARCH_COVERAGE_INCREASED": yes(f"no-order{order}-countermodel successor") if ok else no(),
            }
            return TransitionRecord(
                intervention,
                {"search_frontier": f"proof-after-order{order}" if ok else "unchanged", "order": order, "direction": direction},
                obligations,
                successor,
                terminal=Terminal.NONE,
                certificate={"world": row["id"], "countermodel_absent_through_order": order, "direction": direction} if ok else None,
            )

        raise KeyError(intervention.id)
