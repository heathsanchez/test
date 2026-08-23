from dataclasses import dataclass
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
    external_import_active: bool = False
    target_verified: bool = False

@dataclass(frozen=True)
class CandidateAction:
    name: str
    lifecycle: str
    mode: str
    # One SET of possible observable outcomes per live hypothesis. Overlap means
    # the action does not distinguish those hypotheses for that outcome.
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

@dataclass(frozen=True)
class Decision:
    kind: str  # ACTION or DIRECTIVE
    value: str
    reason: str


def fits_budget(a: CandidateAction, b: Budget) -> bool:
    return (
        a.model_calls <= b.model_calls and
        a.verifier_calls <= b.verifier_calls and
        a.candidate_count <= b.candidate_count and
        a.tokens <= b.tokens and
        a.wall_units <= b.wall_units
    )


def cost_vector(a: CandidateAction):
    return (a.model_calls, a.verifier_calls, a.candidate_count, a.tokens, a.wall_units)


def robust_worst_case_elimination(a: CandidateAction, n_hypotheses: int) -> int:
    """Worst-case eliminations allowing uncertain/overlapping predictions."""
    if len(a.predictions) != n_hypotheses:
        raise ValueError(f"{a.name}: predictions must match live hypotheses")
    outcomes = set().union(*a.predictions) if a.predictions else set()
    if not outcomes:
        return 0
    max_survivors = 0
    for outcome in outcomes:
        survivors = sum(outcome in possible for possible in a.predictions)
        max_survivors = max(max_survivors, survivors)
    return n_hypotheses - max_survivors


def warranted_mode(s: ResearchState) -> tuple[str, str]:
    if not s.apparatus_valid:
        lifecycle = "REPAIR"
    elif s.target_verified and not s.retention_candidate_ready:
        lifecycle = "VERIFY"  # success must be attacked before retention
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
        mode = "DISCRIMINATE"  # ablation/surrogate/scaffold audit
    elif s.repeated_local_failures >= 2 or s.conditional_regimes:
        mode = "REFRAME"
    else:
        mode = "EXPLOIT"
    return lifecycle, mode


def admissible(s: ResearchState, b: Budget, actions: list[CandidateAction]) -> list[CandidateAction]:
    pool = [a for a in actions if fits_budget(a, b)]
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
    return (
        -d,
        -(a.lifecycle == lifecycle),
        -(a.mode == mode),
        a.scaffold_additions,
        a.semantic_risk,
        cost_vector(a),
        a.name,
    )


def choose_next(s: ResearchState, b: Budget, actions: list[CandidateAction]) -> Optional[Decision]:
    for a in actions:
        if len(a.predictions) != len(s.hypotheses):
            raise ValueError(f"{a.name}: predictions must match live hypotheses")
    pool = admissible(s, b, actions)
    if not pool:
        if not s.apparatus_valid:
            return Decision("DIRECTIVE", "REPAIR_APPARATUS", "No budget-feasible repair action exists")
        if not s.residual_sharp:
            return Decision("DIRECTIVE", "MAP", "Residual is not sharp enough for a deciding experiment")
        if s.repeated_local_failures >= 2 or s.conditional_regimes:
            value = "REFRAME_WITH_IMPORT" if s.external_import_active else "REFRAME"
            return Decision("DIRECTIVE", value, "Local action set has stalled; change altitude and generate new rivals/actions")
        return Decision("DIRECTIVE", "PUSH", "No deciding action is available; continue current-frame closure")

    best = min(pool, key=lambda a: action_rank(s, a))
    d = robust_worst_case_elimination(best, len(s.hypotheses))
    if d == 0 and not s.target_verified:
        if not s.residual_sharp:
            return Decision("DIRECTIVE", "MAP", "Available actions cannot separate live rivals and residual remains unsharp")
        if s.repeated_local_failures >= 2 or s.conditional_regimes:
            value = "REFRAME_WITH_IMPORT" if s.external_import_active else "REFRAME"
            return Decision("DIRECTIVE", value, "Available actions have zero robust discrimination after repeated/conditional residuals")
    return Decision("ACTION", best.name, f"robust_worst_case_elimination={d}")


def update_hypotheses(s: ResearchState, a: CandidateAction, observed: str):
    """Never force an observation into a favored hypothesis.

    Returns (new_hypotheses, surprise). If no live hypothesis predicted the
    observed outcome, preserve all live rivals and mark surprise=True; the caller
    should MAP/REFRAME rather than declaring the hypothesis set empty.
    """
    compatible = tuple(
        h for h, possible in zip(s.hypotheses, a.predictions)
        if observed in possible
    )
    if not compatible:
        return s.hypotheses, True
    return compatible, False


def admit_import(s: ResearchState, new_hypothesis: str, has_structural_mapping: bool,
                 has_measurable_differential_prediction: bool):
    """Outside material proposes a rival; it does not become evidence."""
    triggered = (
        not s.residual_sharp or s.repeated_local_failures >= 2 or
        s.conditional_regimes or s.existing_structure_unknown
    )
    if not (s.external_import_active and triggered and has_structural_mapping and
            has_measurable_differential_prediction):
        return s.hypotheses
    if new_hypothesis in s.hypotheses:
        return s.hypotheses
    return s.hypotheses + (new_hypothesis,)
