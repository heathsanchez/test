from __future__ import annotations

from dataclasses import dataclass, field
import json
from typing import Any, Callable, Iterable, Mapping

from .commitment import RuntimeDomain, optimal_experiment_policy
from .state import DevelopmentalState


def _candidate_state(domain: RuntimeDomain, state: DevelopmentalState, pid: str) -> DevelopmentalState:
    hook = getattr(domain, "prepare_probe_extension", None)
    if hook is not None:
        return hook(state, pid)
    return state.evolve(probe_language=frozenset(set(state.probe_language) | {pid}))


ProbeOperator = Mapping[str, Any]
ProbeOperatorInducer = Callable[[RuntimeDomain, DevelopmentalState, DevelopmentalState, str, Any], Iterable[ProbeOperator]]
ProbeOperatorExpander = Callable[[RuntimeDomain, DevelopmentalState, ProbeOperator], Iterable[str]]


@dataclass
class SynthesisRegistry:
    probe_generators: list[Callable[[RuntimeDomain, DevelopmentalState], Iterable[str]]] = field(default_factory=list)
    probe_operator_inducers: list[ProbeOperatorInducer] = field(default_factory=list)
    probe_operator_expanders: list[ProbeOperatorExpander] = field(default_factory=list)

    def register_probe_generator(self, fn: Callable[[RuntimeDomain, DevelopmentalState], Iterable[str]]) -> None:
        self.probe_generators.append(fn)

    def register_probe_operator_inducer(self, fn: ProbeOperatorInducer) -> None:
        self.probe_operator_inducers.append(fn)

    def register_probe_operator_expander(self, fn: ProbeOperatorExpander) -> None:
        self.probe_operator_expanders.append(fn)

    def observe_verified_probe_transition(
        self,
        domain: RuntimeDomain,
        before: DevelopmentalState,
        after: DevelopmentalState,
        probe_id: str,
        record: Any,
    ) -> DevelopmentalState:
        """Induce reusable probe operators from a verified probe transition.

        The registry owns the handoff: experiment code does not install operators.
        Learned operators are serialized into explicit developmental state so later
        synthesis can depend on them and ablation can remove them.
        """
        learned = [dict(x) for x in after.metadata.get("learned_probe_operators", ())]
        seen = {json.dumps(x, sort_keys=True) for x in learned}
        added = []
        for inducer in self.probe_operator_inducers:
            for op in inducer(domain, before, after, probe_id, record):
                op = dict(op)
                key = json.dumps(op, sort_keys=True)
                if key not in seen:
                    seen.add(key)
                    learned.append(op)
                    added.append(op)
        if not added:
            return after
        law_ids = tuple(after.lawbook) + tuple(str(op.get("id", json.dumps(op, sort_keys=True))) for op in added)
        return after.evolve(
            lawbook=law_ids,
            metadata={**after.metadata, "learned_probe_operators": tuple(learned)},
        )

    def _operator_candidates(self, domain: RuntimeDomain, state: DevelopmentalState) -> set[str]:
        out: set[str] = set()
        for op in state.metadata.get("learned_probe_operators", ()):
            for expander in self.probe_operator_expanders:
                out.update(expander(domain, state, op))
        return out

    def synthesize_probe_extension(self, domain: RuntimeDomain, state: DevelopmentalState) -> str | None:
        old = optimal_experiment_policy(domain, state, state.hypotheses, state.probe_language, state.capability_language)
        if old is not None:
            return None
        candidates: set[str] = set()
        for generator in self.probe_generators:
            candidates.update(generator(domain, state))
        candidates.update(self._operator_candidates(domain, state))
        best: tuple[tuple[float, float, str], str] | None = None
        for pid in sorted(candidates - set(state.probe_language)):
            candidate_state = _candidate_state(domain, state, pid)
            policy = optimal_experiment_policy(
                domain,
                candidate_state,
                candidate_state.hypotheses,
                candidate_state.probe_language,
                candidate_state.capability_language,
            )
            if policy is None:
                continue
            p = domain.intervention(pid)
            objective = (p.cost, policy.cost, pid)
            if best is None or objective < best[0]:
                best = (objective, pid)
        return None if best is None else best[1]
