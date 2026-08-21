from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable, Iterable

from .commitment import RuntimeDomain, optimal_experiment_policy
from .state import DevelopmentalState


def _candidate_state(domain: RuntimeDomain, state: DevelopmentalState, pid: str) -> DevelopmentalState:
    hook = getattr(domain, "prepare_probe_extension", None)
    if hook is not None:
        return hook(state, pid)
    return state.evolve(probe_language=frozenset(set(state.probe_language) | {pid}))


@dataclass
class SynthesisRegistry:
    probe_generators: list[Callable[[RuntimeDomain, DevelopmentalState], Iterable[str]]] = field(default_factory=list)

    def register_probe_generator(self, fn: Callable[[RuntimeDomain, DevelopmentalState], Iterable[str]]) -> None:
        self.probe_generators.append(fn)

    def synthesize_probe_extension(self, domain: RuntimeDomain, state: DevelopmentalState) -> str | None:
        old = optimal_experiment_policy(domain, state, state.hypotheses, state.probe_language, state.capability_language)
        if old is not None:
            return None
        candidates: set[str] = set()
        for generator in self.probe_generators:
            candidates.update(generator(domain, state))
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
