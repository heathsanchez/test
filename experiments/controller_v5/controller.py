from dataclasses import dataclass, replace
from typing import FrozenSet, Optional

OutcomeSet = FrozenSet[str]

@dataclass(frozen=True)
class Budget:
    model_calls: int
    verifier_calls: int
    candidate_count: int
    tokens: int
    wall_units: int

@dataclass(frozen=True)
class ResearchState:
    name: str
    hypotheses: tuple[str, ...]
    apparatus_valid: bool = True
    residual_sharp: bool = True
    existing_structure_unknown: bool = False
    repeated_local_failures: int = 0
    conditional_regimes: bool = False
    transfer_candidate_ready: bool = False
    retention_candidate_ready: bool = False
    target_verified: bool = False
    # Candidate-generation evidence. Absence of a separator is not structural
    # evidence unless the declared generator boundary has been exhausted.
    candidate_generation_exhausted: bool = False
    independent_generators_used: int = 1
    # Strategic/proxy gate: local success against a misaligned objective should
    # trigger goal/metric audit rather than further optimization.
    objective_metric_aligned: bool = True

@dataclass(frozen=True)
class ImportArtifact:
    name: str
    proposed_hypothesis: str
    has_structural_mapping: bool
    has_differential_prediction: bool

@dataclass(frozen=True)
class CandidateAction:
    name: str
    lifecycle: str
    mode: str
    predictions: tuple[OutcomeSet, ...]
    model_calls: int = 0
    verifier_calls: int = 0
    candidate_count: int = 0
    tokens: int = 0
    wall_units: int = 0
    scaffold_additions: int = 0
    semantic_risk: int = 0
    changes_representation: bool = False
    inspects_existing_closure: bool = False
    is_ablation_or_control: bool = False
    # Provenance matters: imported / local / search / human / synthesis, etc.
    source: str = "local"

@dataclass(frozen=True)
class Decision:
    kind: str  # ACTION or DIRECTIVE
    value: str
    reason: str


def fits_budget(a: CandidateAction, b: Budget) -> bool:
    return (a.model_calls <= b.model_calls and a.verifier_calls <= b.verifier_calls
            and a.candidate_count <= b.candidate_count and a.tokens <= b.tokens
            and a.wall_units <= b.wall_units)


def cost_vector(a: CandidateAction):
    return (a.model_calls, a.verifier_calls, a.candidate_count, a.tokens, a.wall_units)


def robust_worst_case_elimination(a: CandidateAction, n: int) -> int:
    if len(a.predictions) != n:
        raise ValueError(f"{a.name}: predictions must match live hypotheses")
    outcomes = set().union(*a.predictions) if a.predictions else set()
    if not outcomes:
        return 0
    max_survivors = max(sum(o in poss for poss in a.predictions) for o in outcomes)
    return n - max_survivors


def adversarially_expand_predictions(a: CandidateAction,
                                     critic_predictions: tuple[OutcomeSet, ...]) -> CandidateAction:
    """Independent critic may only WIDEN possible outcomes, never sharpen them.

    This makes self-serving overconfident predictions lose, not gain,
    discrimination after audit.
    """
    if len(critic_predictions) != len(a.predictions):
        raise ValueError("critic prediction count mismatch")
    widened = tuple(p | c for p, c in zip(a.predictions, critic_predictions))
    return replace(a, predictions=widened)


def buffer_import(hypotheses: tuple[str, ...], artifact: ImportArtifact):
    """Imports may arrive at any time. Testable structural imports enter the
    candidate hypothesis buffer without forcing a mode switch or belief update."""
    if not (artifact.has_structural_mapping and artifact.has_differential_prediction):
        return hypotheses
    if artifact.proposed_hypothesis in hypotheses:
        return hypotheses
    return hypotheses + (artifact.proposed_hypothesis,)


def warranted_mode(s: ResearchState):
    if not s.apparatus_valid:
        lifecycle = "REPAIR"
    elif s.target_verified and not s.retention_candidate_ready:
        lifecycle = "VERIFY"
    elif s.retention_candidate_ready:
        lifecycle = "RETAIN"
    elif s.transfer_candidate_ready:
        lifecycle = "TRANSFER"
    else:
        lifecycle = "DISCOVER"

    if s.existing_structure_unknown:
        mode = "INSPECT"
    elif not s.residual_sharp:
        mode = "MAP"
    elif s.target_verified:
        mode = "DISCRIMINATE"
    elif s.repeated_local_failures >= 2 or s.conditional_regimes:
        mode = "REFRAME"
    else:
        mode = "EXPLOIT"
    return lifecycle, mode


def admissible(s: ResearchState, b: Budget, actions: list[CandidateAction]):
    pool = [a for a in actions if fits_budget(a,b)]
    if not s.apparatus_valid:
        return [a for a in pool if a.lifecycle == "REPAIR"]
    if s.existing_structure_unknown:
        inspections = [a for a in pool if a.inspects_existing_closure]
        if inspections:
            return inspections
        pool = [a for a in pool if not a.changes_representation]
    if s.target_verified:
        controls = [a for a in pool if a.is_ablation_or_control]
        if controls:
            return controls
    return pool


def action_rank(s: ResearchState, a: CandidateAction):
    lifecycle, mode = warranted_mode(s)
    d = robust_worst_case_elimination(a, len(s.hypotheses))
    return (-d, -(a.lifecycle==lifecycle), -(a.mode==mode), a.scaffold_additions,
            a.semantic_risk, cost_vector(a), a.name)


def choose_next(s: ResearchState, b: Budget, actions: list[CandidateAction]) -> Optional[Decision]:
    if not s.objective_metric_aligned:
        return Decision("DIRECTIVE","AUDIT_GOAL_METRIC",
                        "Current objective/metric is not established as aligned with the real target")
    for a in actions:
        if len(a.predictions) != len(s.hypotheses):
            raise ValueError(f"{a.name}: predictions must match live hypotheses")
    pool = admissible(s,b,actions)
    if not pool:
        if not s.apparatus_valid:
            return Decision("DIRECTIVE","REPAIR_APPARATUS","No budget-feasible repair exists")
        if not s.candidate_generation_exhausted:
            return Decision("DIRECTIVE","EXPAND_CANDIDATES",
                            "No admissible action; candidate-generation boundary is not exhausted")
        if not s.residual_sharp:
            return Decision("DIRECTIVE","MAP","Residual remains unsharp after candidate-generation exhaustion")
        return Decision("DIRECTIVE","REFRAME","No admissible action remains inside the exhausted declared frame")

    best = min(pool,key=lambda a: action_rank(s,a))
    d = robust_worst_case_elimination(best,len(s.hypotheses))
    if d == 0 and not s.target_verified:
        # Critical anti-overreach rule: a sampled candidate set with no separator
        # is a search residual unless its declared generation boundary is exhausted.
        if not s.candidate_generation_exhausted:
            return Decision("DIRECTIVE","EXPAND_CANDIDATES",
                            "Current candidate pool has zero robust discrimination but search boundary remains open")
        if not s.residual_sharp:
            return Decision("DIRECTIVE","MAP","Exhausted candidate pool cannot discriminate and residual is unsharp")
        return Decision("DIRECTIVE","REFRAME",
                        "Exhausted same-frame candidate pool has zero robust discrimination")
    return Decision("ACTION",best.name,f"robust_worst_case_elimination={d};source={best.source}")


def update_hypotheses(s: ResearchState, a: CandidateAction, observed: str):
    compatible = tuple(h for h, poss in zip(s.hypotheses,a.predictions) if observed in poss)
    return (compatible,False) if compatible else (s.hypotheses,True)
