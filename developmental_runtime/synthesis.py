from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable, Iterable

from .commitment import RuntimeDomain, optimal_experiment_policy
from .state import DevelopmentalState


@dataclass
class SynthesisRegistry:
    probe_generators: list[Callable[[RuntimeDomain, DevelopmentalState], Iterable[str]]] = field(default_factory=list)

    def register_probe_generator(self, fn: Callable[[RuntimeDomain, DevelopmentalState], Iterable[str]]) -> None:
        self.probe_generators.append(fn)

    def synthesize_probe_extension(self, domain: RuntimeDomain, state: DevelopmentalState) -> str | None:
        # Certified old-language obstruction must already hold.
        old = optimal_experiment_policy(domain, state, state.hypotheses, state.probe_language, state.capability_language)
        if old is not None:
            return None
        candidates: set[str] = set()
        for generator in self.probe_generators:
            candidates.update(generator(domain, state))
        best: tuple[tuple[float, float, str], str] | None = None
        for pid in sorted(candidates - set(state.probe_language)):
            expanded = frozenset(set(state.probe_language) | {pid})
            policy = optimal_experiment_policy(domain, state, state.hypotheses, expanded, state.capability_language)
            if policy is None:
                continue
            p = domain.intervention(pid)
            objective = (p.cost, policy.cost, pid)
            if best is None or objective < best[0]:
                best = (objective, pid)
        return None if best is None else best[1]
