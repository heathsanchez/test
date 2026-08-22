from __future__ import annotations

from dataclasses import dataclass
from enum import Enum, auto
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


def _assume_probe_outcome(domain: RuntimeDomain, state: DevelopmentalState, probe_id: str, outcome: Any, cell: FrozenSet[Any]) -> DevelopmentalState:
    """Planning-only successor for a hypothetical verified probe outcome.

    This is deliberately separate from actual state update: policy search may ask
    whether a probe *would* restore a common lawful continuation, but routing may
    not treat that continuation as licensed until the probe is really executed.
    """
    hook = getattr(domain, "assume_probe_outcome", None)
    if hook is not None:
        return hook(state, probe_id, outcome, cell)
    return state.evolve(
        hypotheses=cell,
        metadata={**state.metadata, "decision_probe_id": probe_id, "assumed_probe_outcome": outcome},
    )


def optimal_experiment_policy(domain: RuntimeDomain, state: DevelopmentalState, cell: FrozenSet[Any], probe_ids: Iterable[str], action_ids: Iterable[str]) -> ExperimentPolicy | None:
    probes = tuple(sorted(set(probe_ids)))
    actions = tuple(sorted(set(action_ids)))
    memo: dict[tuple[FrozenSet[Any], str | None, Any], ExperimentPolicy | None] = {}

    def solve(E: FrozenSet[Any], planning_state: DevelopmentalState, last_probe: str | None = None, last_outcome: Any = None) -> ExperimentPolicy | None:
        key = (E, last_probe, repr(last_outcome))
        if key in memo:
            return memo[key]

        commitments = common_interventions(domain, planning_state, E, actions)
        if commitments:
            ans = ExperimentPolicy(0.0, ProbeTree(None, {}, commitments))
            memo[key] = ans
            return ans

        best: ExperimentPolicy | None = None
        for pid in probes:
            parts = split_cell(domain, planning_state, E, pid)
            if len(parts) <= 1:
                continue
            children: dict[Any, ProbeTree] = {}
            worst = 0.0
            feasible = True
            for outcome, subcell in parts.items():
                assumed = _assume_probe_outcome(domain, planning_state, pid, outcome, subcell)
                sub = solve(subcell, assumed, pid, outcome)
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

        memo[key] = best
        return best

    return solve(cell, state)


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
