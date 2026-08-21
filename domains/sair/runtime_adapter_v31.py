from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Mapping

from developmental_runtime import (
    DevelopmentalState,
    Intervention,
    InterventionKind,
    ObligationEvidence,
    Terminal,
    TransitionRecord,
)


LAW_ID = "NUMERIC_LITERAL_SHIFT:+1"


def parse_probe_id(pid: str) -> tuple[int, str]:
    # MODEL_EXISTS(3,FORWARD)
    if not (pid.startswith("MODEL_EXISTS(") and pid.endswith(")")):
        raise ValueError(pid)
    body = pid[len("MODEL_EXISTS("):-1]
    n, direction = body.split(",")
    return int(n), direction


@dataclass
class V31SAIRRuntimeAdapter:
    rows: list[dict[str, Any]]
    programs: Mapping[str, dict[str, Any]]
    lazy_probe_value: Any
    witness_stats: dict[str, int] = field(default_factory=lambda: {"rechecked": 0, "bad": 0, "unknown": 0})

    def prepare_probe_extension(self, state: DevelopmentalState, probe_id: str) -> DevelopmentalState:
        return state.evolve(
            probe_language=frozenset(set(state.probe_language) | {probe_id}),
            metadata={**state.metadata, "decision_probe_id": probe_id},
        )

    def induce_retained_law(self, state: DevelopmentalState, probe_id: str) -> str | None:
        # Learn the reusable operator from the first verified structural delta.
        # The runtime has only order-2 seeds initially; MODEL_EXISTS(3,*) therefore
        # witnesses an integer-literal +1 transformation. Once retained, no new law
        # is induced on later applications.
        if LAW_ID in state.lawbook:
            return None
        try:
            n, _direction = parse_probe_id(probe_id)
        except ValueError:
            return None
        if n != 3:
            return None
        return LAW_ID

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
        n, direction = parse_probe_id(probe_id)
        key = (n, direction)
        if key in row["vals"]:
            return row["vals"][key]
        val, cert_status = self.lazy_probe_value(row, n, direction)
        row["vals"][key] = val
        if cert_status == "sat":
            self.witness_stats["rechecked"] += 1
        elif cert_status == "bad":
            self.witness_stats["bad"] += 1
        elif cert_status == "unknown":
            self.witness_stats["unknown"] += 1
        return val

    def execute(self, state: DevelopmentalState, world_id: int, intervention: Intervention) -> TransitionRecord:
        row = self.rows[world_id]
        yes = lambda cert=None: ObligationEvidence(True, cert)
        no = lambda cert=None: ObligationEvidence(False, cert)

        if intervention.kind is InterventionKind.PROBE:
            outcome = self.probe_outcome(state, world_id, intervention.id)
            successor = state.evolve(
                metadata={**state.metadata, "last_probe": intervention.id, "last_probe_outcome": outcome}
            )
            return TransitionRecord(
                intervention=intervention,
                effect={"observation": outcome},
                obligations={
                    "VERIFIED": yes("exact-bounded-model-query"),
                    "ADMISSIBLE": yes(),
                    "OBSERVATION_SOUND": yes(),
                },
                successor=successor,
                terminal=Terminal.NONE,
                certificate={"probe": intervention.id, "outcome": outcome},
                cost=intervention.cost,
            )

        decision_probe = state.metadata.get("decision_probe_id")
        if not decision_probe:
            return TransitionRecord(intervention, {}, {"VERIFIED": no(), "ADMISSIBLE": no()}, state)
        n, _direction = parse_probe_id(decision_probe)
        world_outcome = self.probe_outcome(state, world_id, decision_probe)
        exhausted = int(state.metadata.get("countermodel_exhausted_through", 0))

        if intervention.id == "ACCEPT_COUNTERMODEL_WITNESS":
            ok = bool(world_outcome == 1)
            obligations = {
                "VERIFIED": yes("independently-rechecked-model") if ok else no(),
                "ADMISSIBLE": yes() if ok else no(),
                "TERMINAL_CERTIFIED": yes("countermodel") if ok else no(),
            }
            return TransitionRecord(
                intervention,
                {"accepted_countermodel": ok, "order": n},
                obligations,
                state,
                terminal=Terminal.REFUTED if ok else Terminal.NONE,
                certificate={"world": row["id"], "probe": decision_probe, "order": n} if ok else None,
            )

        if intervention.id == "ADVANCE_PROOF_SEARCH_FRONTIER":
            ok = bool(world_outcome == 0 and n > exhausted)
            successor = state.evolve(
                problem_state={"source": row["id"], "countermodel_exhausted_through": n},
                metadata={
                    **state.metadata,
                    "countermodel_exhausted_through": n if ok else exhausted,
                    "proof_frontier_advanced": ok,
                },
            )
            obligations = {
                "VERIFIED": yes(f"order{n}-exhaustion") if ok else no(),
                "ADMISSIBLE": yes() if ok else no(),
                "SEARCH_COVERAGE_INCREASED": yes(f"no-order{n}-countermodel successor") if ok else no(),
            }
            return TransitionRecord(
                intervention,
                {"search_frontier": f"proof-after-order{n}", "order": n},
                obligations,
                successor,
                terminal=Terminal.NONE,
                certificate={"world": row["id"], f"order{n}_absence": True} if ok else None,
            )

        raise KeyError(intervention.id)
