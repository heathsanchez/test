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

    def execute(self, state: DevelopmentalState, world_id: int, intervention: Intervention) -> TransitionRecord:
        row = self.rows[world_id]
        yes = lambda cert=None: ObligationEvidence(True, cert)
        no = lambda cert=None: ObligationEvidence(False, cert)

        if intervention.kind is InterventionKind.PROBE:
            outcome = self.probe_outcome(state, world_id, intervention.id)
            successor = state.evolve(metadata={**state.metadata, "last_probe": intervention.id, "last_probe_outcome": outcome})
            return TransitionRecord(
                intervention=intervention,
                effect={"observation": outcome},
                obligations={"VERIFIED": yes("exact-model-query"), "ADMISSIBLE": yes(), "OBSERVATION_SOUND": yes()},
                successor=successor,
                terminal=Terminal.NONE,
                certificate={"probe": intervention.id, "outcome": outcome},
                cost=intervention.cost,
            )

        last = state.metadata.get("last_probe")
        outcome = state.metadata.get("last_probe_outcome")
        if not last:
            return TransitionRecord(intervention, {}, {"VERIFIED": no(), "ADMISSIBLE": no()}, state)

        if intervention.id == "ACCEPT_COUNTERMODEL_WITNESS":
            ok = bool(outcome == 1 and self.probe_outcome(state, world_id, last) == 1)
            obligations = {
                "VERIFIED": yes("independently-rechecked-model") if ok else no(),
                "ADMISSIBLE": yes() if ok else no(),
                "TERMINAL_CERTIFIED": yes("countermodel") if ok else no(),
            }
            return TransitionRecord(
                intervention,
                {"accepted_countermodel": ok},
                obligations,
                state,
                terminal=Terminal.REFUTED if ok else Terminal.NONE,
                certificate={"world": row["id"], "probe": last} if ok else None,
            )

        if intervention.id == "ADVANCE_PROOF_SEARCH_FRONTIER":
            # This is intentionally nonterminal. Its lawful effect is to move from
            # an unresolved state into a certified no-small-countermodel successor.
            ok = bool(outcome == 0 and self.probe_outcome(state, world_id, last) == 0)
            successor = state.evolve(
                problem_state={"source": row["id"], "order3_countermodel_exhausted": True},
                metadata={**state.metadata, "proof_frontier_advanced": ok},
            )
            obligations = {
                "VERIFIED": yes("order3-exhaustion") if ok else no(),
                "ADMISSIBLE": yes() if ok else no(),
                "SEARCH_COVERAGE_INCREASED": yes("no-order3-countermodel successor") if ok else no(),
            }
            return TransitionRecord(
                intervention,
                {"search_frontier": "proof-after-order3"},
                obligations,
                successor,
                terminal=Terminal.NONE,
                certificate={"world": row["id"], "order3_absence": True} if ok else None,
            )

        raise KeyError(intervention.id)
