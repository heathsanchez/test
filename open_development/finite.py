"""A complete finite-world adapter using the existing V30 developmental runtime.

The input table is the declared model, not a discovery of external reality.
Every negative conclusion is relative to its finite worlds, supplied probes,
and the current executable language. The actual world is used only after routing.
"""
from __future__ import annotations

from dataclasses import asdict
from typing import Any, Mapping

from developmental_runtime import (
    DevelopmentalRuntime, DevelopmentalState, Intervention, InterventionKind,
    ObligationEvidence, Route, SynthesisRegistry, Terminal, TransitionRecord,
    lawful, route,
)

from .runtime import Evidence, Obligation, Repair, assessment_claim, canonical, digest
from .lean_gate import LeanGate


def freeze(value: Any) -> str:
    """Canonical JSON equality, not Python's bool/int or mutable-list equality."""
    return canonical(value)


class FiniteTableDomain:
    def __init__(self, spec: Mapping[str, Any]):
        self.spec = dict(spec)
        self.worlds = tuple(str(x) for x in spec["worlds"])
        if not self.worlds or len(set(self.worlds)) != len(self.worlds):
            raise ValueError("worlds must be nonempty and distinct")
        self.index = {w: i for i, w in enumerate(self.worlds)}
        self.probes = {str(k): tuple(freeze(x) for x in v)
                       for k, v in spec["probes"].items()}
        if any(len(v) != len(self.worlds) for v in self.probes.values()):
            raise ValueError("probe table has wrong width")
        self.initial = frozenset(spec.get("initial_probes", []))
        self.candidates = tuple(sorted(set(spec.get("candidate_probes", self.probes))))
        if not self.initial <= self.probes.keys() or not set(self.candidates) <= self.probes.keys():
            raise ValueError("unknown probe")
        self.tasks = {str(t): {str(a): frozenset(str(w) for w in ws)
                               for a, ws in actions.items()}
                      for t, actions in spec["tasks"].items()}
        for actions in self.tasks.values():
            if not actions or any(not ws <= self.index.keys() for ws in actions.values()):
                raise ValueError("invalid action table")
            if set(actions) & set(self.probes):
                raise ValueError("probe and action identifiers must be disjoint")
        self.model_hash = digest(self.spec)

    def intervention(self, intervention_id: str) -> Intervention:
        if intervention_id in self.probes:
            return Intervention(intervention_id, InterventionKind.PROBE, intervention_id, 1.0)
        return Intervention(intervention_id, InterventionKind.CONSTRUCT, intervention_id, 1.0)

    def prepare_probe_extension(self, state: DevelopmentalState, pid: str) -> DevelopmentalState:
        return state.evolve(probe_language=state.probe_language | {pid})

    def probe_outcome(self, state: DevelopmentalState, world_id: str, probe_id: str) -> Any:
        return self.probes[probe_id][self.index[world_id]]

    def execute(self, state: DevelopmentalState, world_id: str,
                intervention: Intervention) -> TransitionRecord:
        iid = intervention.id
        if world_id not in self.index:
            raise ValueError("unknown world")
        if iid in self.probes:
            allowed = iid in state.probe_language
            effect = {"observation": self.probe_outcome(state, world_id, iid)}
            kind = InterventionKind.PROBE
        else:
            task = state.problem_state["task"]
            allowed = iid in state.capability_language and world_id in self.tasks[task].get(iid, ())
            effect = {"action": iid, "world": world_id}
            kind = InterventionKind.CONSTRUCT
        required = ("VERIFIED", "ADMISSIBLE", "OBSERVATION_SOUND") if kind is InterventionKind.PROBE else (
            "VERIFIED", "ADMISSIBLE", "PRESERVE", "CHANGE_SATISFIED")
        certificate = {"model": self.model_hash, "world": world_id, "intervention": iid,
                       "effect": effect, "allowed": allowed}
        obligations = {key: ObligationEvidence(allowed, certificate if allowed else None) for key in required}
        successor = state.evolve(problem_state={**state.problem_state, "last_effect": effect})
        return TransitionRecord(intervention, effect, obligations, successor,
                                Terminal.NONE, certificate if allowed else None, 1.0)


class FiniteAdapter:
    name = "finite"

    def __init__(self, spec: Mapping[str, Any], gate: LeanGate | None = None):
        self.domain = FiniteTableDomain(spec)
        self.gate = gate
        authority = gate.verifier_id if gate is not None else "finite-only-v1"
        self.verifier_id = "finite-table-v2:" + digest(
            {"model": self.domain.model_hash, "authority": authority})
        self.registry = SynthesisRegistry()
        self.registry.register_probe_generator(lambda _d, _s: self.domain.candidates)
        self.engine = DevelopmentalRuntime(self.domain, self.registry)

    def _state(self, state: Mapping[str, Any], obligation: Obligation) -> DevelopmentalState:
        target = obligation.target
        task = target["task"]
        if task not in self.domain.tasks:
            raise ValueError("unknown task")
        worlds = frozenset(str(w) for w in target.get("worlds", self.domain.worlds))
        if not worlds or not worlds <= self.domain.index.keys():
            raise ValueError("invalid world cell")
        retained = {rec["repair"]["payload"]["probe"]
                    for rec in state["capabilities"].values()
                    if rec["repair"]["kind"] == "observation"
                    and rec["repair"]["scope"] == self.name
                    and rec["evidence"]["verifier"] == self.verifier_id
                    and rec["repair"]["payload"].get("model") == self.domain.model_hash
                    and rec["repair"]["payload"].get("probe") in self.domain.probes}
        return DevelopmentalState(
            problem_state={"task": task}, hypotheses=worlds,
            quotient={"cell": tuple(sorted(worlds))},
            probe_language=frozenset(self.domain.initial | retained),
            capability_language=frozenset(self.domain.tasks[task]),
            metadata={"model": self.domain.model_hash})

    def _certificate(self, state: DevelopmentalState, decision: Any) -> dict[str, Any]:
        return {"model": self.domain.model_hash, "worlds": sorted(state.hypotheses),
                "probes": sorted(state.probe_language), "actions": sorted(state.capability_language),
                "route": decision.route.name, "reason": decision.reason}

    def assess(self, state: Mapping[str, Any], obligation: Obligation) -> Evidence:
        ds = self._state(state, obligation)
        claim = assessment_claim(state, obligation)
        decision = route(self.domain, ds)
        if decision.route is Route.DEVELOP_PROBES:
            return Evidence("unknown", claim, self.verifier_id,
                            self._certificate(ds, decision),
                            {"class": "CURRENT_PROBE_CLOSURE", "cell": sorted(ds.hypotheses)},
                            self.name)
        trace = []
        mode = obligation.target.get("mode", "execute")
        if mode not in ("execute", "plan"):
            raise ValueError("unknown execution mode")
        actual = str(obligation.target.get("actual_world", ""))
        if mode == "execute" and not actual:
            raise ValueError("execution requires an actual world")
        if actual and actual not in ds.hypotheses:
            raise ValueError("actual world outside cell")
        # The world is deliberately not used by the router or synthesizer.
        while decision.route is Route.PROBE and actual:
            before = ds.hypotheses
            ds, event = self.engine.execute_probe(ds, actual)
            trace.append(asdict(event))
            if len(ds.hypotheses) >= len(before):
                raise RuntimeError("non-refining probe")
            decision = route(self.domain, ds)
        if decision.route is Route.ACT:
            if actual and mode == "execute":
                ds, event = self.engine.execute_common_continuation(ds, actual)
                trace.append(asdict(event))
            cert = self._certificate(ds, decision)
            cert["mode"] = mode
            if mode == "execute":
                cert["successor_route"] = route(self.domain, ds).route.name
            cert["trace"] = trace
            cert["common_actions"] = sorted(decision.commitments)
            return Evidence("verified", claim, self.verifier_id, cert, None, self.name)
        if decision.route is Route.PROBE and mode == "plan":
            cert = self._certificate(ds, decision)
            cert["probe_policy"] = decision.policy.tree.probe_id if decision.policy else None
            cert["policy_cost"] = decision.policy.cost if decision.policy else None
            cert["mode"] = mode
            return Evidence("verified", claim, self.verifier_id, cert, None, self.name)
        return Evidence("unknown", claim, self.verifier_id, None, None, self.name)

    def propose(self, state: Mapping[str, Any], obligation: Obligation, residual: Any):
        if residual.get("class") != "CURRENT_PROBE_CLOSURE":
            return
        ds = self._state(state, obligation)
        # Reuse the actual V30 engine -> registry -> router path.
        _, events = self.engine.develop_until_intervention(ds)
        for event in events:
            if event.route == "SYNTHESIZE_PROBE":
                yield Repair("observation", event.intervention_id,
                             {"model": self.domain.model_hash, "probe": event.intervention_id}, self.name)

    def verify(self, state: Mapping[str, Any], obligation: Obligation, repair: Repair) -> Evidence:
        claim = repair.id
        if repair.kind != "observation" or repair.payload.get("model") != self.domain.model_hash:
            return Evidence("unknown", claim, self.verifier_id)
        pid = repair.payload["probe"]
        if pid not in self.domain.candidates:
            return Evidence("unknown", claim, self.verifier_id)
        ds = self._state(state, obligation)
        if pid in ds.probe_language:
            return Evidence("unknown", claim, self.verifier_id)
        candidate = self.domain.prepare_probe_extension(ds, pid)
        table = []
        for world in self.domain.worlds:
            record = self.domain.execute(candidate, world, self.domain.intervention(pid))
            if not lawful(record) or record.certificate is None:
                return Evidence("unknown", claim, self.verifier_id)
            if record.effect["observation"] != self.domain.probe_outcome(candidate, world, pid):
                return Evidence("unknown", claim, self.verifier_id)
            table.append(record.effect["observation"])
        decision = route(self.domain, candidate)
        if decision.route not in (Route.PROBE, Route.ACT):
            return Evidence("unknown", claim, self.verifier_id)
        cert = {"model": self.domain.model_hash, "probe": pid, "table": table,
                "coverage": list(self.domain.worlds), "old_probes": sorted(ds.probe_language),
                "new_route": decision.route.name}
        if self.gate is not None:
            lean = self.gate.verify(self.domain.probes, tuple(sorted(ds.probe_language)), pid)
            if lean is None:
                return Evidence("unknown", claim, self.verifier_id,
                                {"gate": "rejected"}, {"class": "LEAN_CERTIFICATE_REJECTED"},
                                self.name)
            cert["lean"] = lean
        return Evidence("verified", claim, self.verifier_id, cert, None, self.name)

    def attach(self, state: Mapping[str, Any], repair: Repair, evidence: Evidence) -> Mapping[str, Any]:
        if evidence.verdict != "verified" or evidence.claim != repair.id:
            raise ValueError("unverified attachment")
        if repair.payload.get("model") != self.domain.model_hash:
            raise ValueError("wrong model")
        return {"model": self.domain.model_hash, "probe": repair.payload["probe"]}
