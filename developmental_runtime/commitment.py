from __future__ import annotations

from dataclasses import dataclass
from enum import Enum, auto
from functools import lru_cache
from typing import Any, FrozenSet, Iterable, Mapping, Protocol

from .intervention import Intervention, TransitionRecord, lawful
from .state import DevelopmentalState

INF = float("inf")


class Route(Enum):
    ACT = auto()
    PROBE = auto()
    DEVELOP_PROBES = auto()
    DEVELOP_CAPABILITY = auto()
    DEVELOP_WORLD_MODEL = auto()
    TERMINATE = auto()


class RuntimeDomain(Protocol):
    def intervention(self, intervention_id: str) -> Intervention: ...
    def execute(self, state: DevelopmentalState, world_id: Any, intervention: Intervention) -> TransitionRecord: ...
    def probe_outcome(self, state: DevelopmentalState, world_id: Any, probe_id: str) -> Any: ...


@dataclass(frozen=True)
class ProbeTree:
    probe_id: str | None
    children: Mapping[Any, "ProbeTree"]
    commitments: FrozenSet[str]


@dataclass(frozen=True)
class ExperimentPolicy:
    cost: float
    tree: ProbeTree


@dataclass(frozen=True)
class RoutingDecision:
    route: Route
    commitments: FrozenSet[str] = frozenset()
    policy: ExperimentPolicy | None = None
    reason: str = ""


def lawful_interventions(domain: RuntimeDomain, state: DevelopmentalState, world_id: Any, ids: Iterable[str]) -> FrozenSet[str]:
    out = set()
    for iid in ids:
        record = domain.execute(state, world_id, domain.intervention(iid))
        if lawful(record):
            out.add(iid)
    return frozenset(out)


def common_interventions(domain: RuntimeDomain, state: DevelopmentalState, cell: FrozenSet[Any], ids: Iterable[str]) -> FrozenSet[str]:
    if not cell:
        return frozenset()
    ids = tuple(ids)
    it = iter(cell)
    common = set(lawful_interventions(domain, state, next(it), ids))
    for h in it:
        common.intersection_update(lawful_interventions(domain, state, h, ids))
        if not common:
            break
    return frozenset(common)


def split_cell(domain: RuntimeDomain, state: DevelopmentalState, cell: FrozenSet[Any], probe_id: str) -> dict[Any, FrozenSet[Any]]:
    groups: dict[Any, set[Any]] = {}
    for h in cell:
        groups.setdefault(domain.probe_outcome(state, h, probe_id), set()).add(h)
    return {y: frozenset(v) for y, v in groups.items()}


def optimal_experiment_policy(domain: RuntimeDomain, state: DevelopmentalState, cell: FrozenSet[Any], probe_ids: Iterable[str], action_ids: Iterable[str]) -> ExperimentPolicy | None:
    probes = tuple(sorted(set(probe_ids)))
    actions = tuple(sorted(set(action_ids)))

    @lru_cache(None)
    def solve(E: FrozenSet[Any]) -> ExperimentPolicy | None:
        commitments = common_interventions(domain, state, E, actions)
        if commitments:
            return ExperimentPolicy(0.0, ProbeTree(None, {}, commitments))
        best: ExperimentPolicy | None = None
        for pid in probes:
            parts = split_cell(domain, state, E, pid)
            if len(parts) <= 1:
                continue
            children: dict[Any, ProbeTree] = {}
            worst = 0.0
            feasible = True
            for outcome, subcell in parts.items():
                sub = solve(subcell)
                if sub is None:
                    feasible = False
                    break
                children[outcome] = sub.tree
                worst = max(worst, sub.cost)
            if not feasible:
                continue
            p = domain.intervention(pid)
            candidate = ExperimentPolicy(p.cost + worst, ProbeTree(pid, children, frozenset()))
            if best is None or (candidate.cost, pid) < (best.cost, best.tree.probe_id or ""):
                best = candidate
        return best

    return solve(cell)


def route(domain: RuntimeDomain, state: DevelopmentalState, *, world_cover: bool = True) -> RoutingDecision:
    if not world_cover:
        return RoutingDecision(Route.DEVELOP_WORLD_MODEL, reason="WorldCover boundary failed")
    common = common_interventions(domain, state, state.hypotheses, state.capability_language)
    if common:
        return RoutingDecision(Route.ACT, common, reason="Common lawful continuation exists")
    policy = optimal_experiment_policy(domain, state, state.hypotheses, state.probe_language, state.capability_language)
    if policy is not None:
        return RoutingDecision(Route.PROBE, policy=policy, reason="Current probe closure resolves commitment defect")
    return RoutingDecision(Route.DEVELOP_PROBES, reason="Commitment-incoherent and J_P(E)=infinity")
