from dataclasses import dataclass, replace
from typing import FrozenSet, Optional
from collections import defaultdict

OutcomeSet = FrozenSet[str]


@dataclass(frozen=True)
class Budget:
    model_calls: int
    verifier_calls: int
    candidate_count: int
    tokens: int
    wall_units: int


@dataclass(frozen=True)
class GeneratorSpec:
    name: str
    family: str
    quota: int
    required: bool = True


@dataclass(frozen=True)
class GeneratorRun:
    generator: str
    attempts: int
    audited_candidates: int
    pending_candidates: int = 0
    leaked: bool = False


@dataclass(frozen=True)
class ResearchState:
    name: str
    hypotheses: tuple[str, ...]
    apparatus_valid: bool = True
    residual_sharp: bool = True
    existing_structure_unknown: bool = False
    repeated_local_failures: int = 0
    conditional_regimes: bool = False
    objective_metric_aligned: bool = True

    # Result/attack lifecycle. Success cannot flow directly to retention.
    target_verified: bool = False
    attack_passed: bool = False
    transfer_passed: bool = False
    reconstruction_passed: bool = False

    # A surprise invalidates claims that the current hypothesis/generator
    # boundary has been exhausted.
    unresolved_surprise: bool = False


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
    generator: str
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
    is_transfer_test: bool = False
    is_reconstruction_test: bool = False
    protected_outcome_access: bool = False
    source: str = "local"


@dataclass(frozen=True)
class Decision:
    kind: str  # ACTION or DIRECTIVE
    value: str
    reason: str


def fits_budget(a: CandidateAction, b: Budget) -> bool:
    return (
        a.model_calls <= b.model_calls
        and a.verifier_calls <= b.verifier_calls
        and a.candidate_count <= b.candidate_count
        and a.tokens <= b.tokens
        and a.wall_units <= b.wall_units
    )


def cost_vector(a: CandidateAction):
    return (a.model_calls, a.verifier_calls, a.candidate_count, a.tokens, a.wall_units)


def robust_worst_case_survivors(a: CandidateAction, n: int) -> int:
    if len(a.predictions) != n:
        raise ValueError(f"{a.name}: predictions must match live hypotheses")
    outcomes = set().union(*a.predictions) if a.predictions else set()
    if not outcomes:
        return n
    return max(sum(o in poss for poss in a.predictions) for o in outcomes)


def robust_worst_case_elimination(a: CandidateAction, n: int) -> int:
    return n - robust_worst_case_survivors(a, n)


def robust_split_fraction(a: CandidateAction, n: int) -> float:
    """Normalized minimax discrimination. 1 is perfect; 0 guarantees nothing."""
    if n <= 1:
        return 1.0
    return robust_worst_case_elimination(a, n) / (n - 1)


def adversarially_expand_predictions(
    a: CandidateAction, critic_predictions: tuple[OutcomeSet, ...]
) -> CandidateAction:
    """A critic may only widen possible outcomes, never sharpen them."""
    if len(critic_predictions) != len(a.predictions):
        raise ValueError("critic prediction count mismatch")
    widened = tuple(p | c for p, c in zip(a.predictions, critic_predictions))
    return replace(a, predictions=widened)


def buffer_import(hypotheses: tuple[str, ...], artifact: ImportArtifact):
    """Outside material may arrive at any time, but only testable structure enters."""
    if not (artifact.has_structural_mapping and artifact.has_differential_prediction):
        return hypotheses
    if artifact.proposed_hypothesis in hypotheses:
        return hypotheses
    return hypotheses + (artifact.proposed_hypothesis,)


def validate_generator_ledger(
    specs: tuple[GeneratorSpec, ...], runs: tuple[GeneratorRun, ...]
) -> None:
    spec_names = {s.name for s in specs}
    if len(spec_names) != len(specs):
        raise ValueError("generator names must be unique")
    for r in runs:
        if r.generator not in spec_names:
            raise ValueError(f"unknown generator in ledger: {r.generator}")
        if min(r.attempts, r.audited_candidates, r.pending_candidates) < 0:
            raise ValueError("generator counts cannot be negative")
        if r.audited_candidates + r.pending_candidates > r.attempts:
            raise ValueError("candidate counts cannot exceed attempts")


def generator_boundary_exhausted(
    specs: tuple[GeneratorSpec, ...],
    runs: tuple[GeneratorRun, ...],
    unresolved_surprise: bool = False,
) -> bool:
    """Exhaustion is derived from a frozen ledger, never a hand-set boolean."""
    validate_generator_ledger(specs, runs)
    if unresolved_surprise:
        return False

    by_name = defaultdict(lambda: GeneratorRun("", 0, 0, 0, False))
    for r in runs:
        prev = by_name[r.generator]
        by_name[r.generator] = GeneratorRun(
            r.generator,
            prev.attempts + r.attempts,
            prev.audited_candidates + r.audited_candidates,
            prev.pending_candidates + r.pending_candidates,
            prev.leaked or r.leaked,
        )

    for spec in specs:
        if not spec.required:
            continue
        r = by_name.get(spec.name)
        if r is None or r.attempts < spec.quota or r.pending_candidates != 0 or r.leaked:
            return False
    return True


def warranted_mode(s: ResearchState):
    if not s.apparatus_valid:
        return "REPAIR", "INSPECT"
    if s.target_verified and not s.attack_passed:
        return "VERIFY", "DISCRIMINATE"
    if s.attack_passed and not s.transfer_passed:
        return "TRANSFER", "DISCRIMINATE"
    if s.transfer_passed and not s.reconstruction_passed:
        return "TRANSFER", "INSPECT"
    if s.reconstruction_passed:
        return "RETAIN", "DISCRIMINATE"

    if s.existing_structure_unknown:
        mode = "INSPECT"
    elif not s.residual_sharp:
        mode = "MAP"
    elif s.repeated_local_failures >= 2 or s.conditional_regimes:
        mode = "REFRAME"
    else:
        mode = "EXPLOIT"
    return "DISCOVER", mode


def action_phase_ok(s: ResearchState, a: CandidateAction) -> bool:
    # These are hard gates. A green result cannot be followed by ordinary exploit.
    if s.target_verified and not s.attack_passed:
        return a.is_ablation_or_control
    if s.attack_passed and not s.transfer_passed:
        return a.is_transfer_test
    if s.transfer_passed and not s.reconstruction_passed:
        return a.is_reconstruction_test
    return True


def admissible(s: ResearchState, b: Budget, actions: list[CandidateAction]):
    # Any action with protected outcome access is excluded from evidentiary choice.
    pool = [a for a in actions if fits_budget(a, b) and not a.protected_outcome_access]

    if not s.apparatus_valid:
        return [a for a in pool if a.lifecycle == "REPAIR"]

    if s.existing_structure_unknown:
        inspections = [a for a in pool if a.inspects_existing_closure]
        if inspections:
            pool = inspections
        else:
            pool = [a for a in pool if not a.changes_representation]

    return [a for a in pool if action_phase_ok(s, a)]


def action_rank(s: ResearchState, a: CandidateAction):
    lifecycle, mode = warranted_mode(s)
    n = len(s.hypotheses)
    split = robust_split_fraction(a, n)
    return (
        -split,
        -(a.lifecycle == lifecycle),
        -(a.mode == mode),
        a.scaffold_additions,
        a.semantic_risk,
        cost_vector(a),
        a.name,
    )


def choose_next(
    s: ResearchState,
    b: Budget,
    actions: list[CandidateAction],
    generator_specs: tuple[GeneratorSpec, ...],
    generator_runs: tuple[GeneratorRun, ...],
) -> Optional[Decision]:
    if not s.objective_metric_aligned:
        return Decision(
            "DIRECTIVE",
            "AUDIT_GOAL_METRIC",
            "Operational metric is not established as aligned with the real objective",
        )

    validate_generator_ledger(generator_specs, generator_runs)
    declared = {g.name for g in generator_specs}

    for a in actions:
        if len(a.predictions) != len(s.hypotheses):
            raise ValueError(f"{a.name}: predictions must match live hypotheses")
        if a.generator not in declared:
            raise ValueError(f"{a.name}: undeclared generator {a.generator}")

    # Success is not retention. Missing attack/transfer/reconstruction actions are
    # explicit search residuals, not permission to continue ordinary optimization.
    if s.target_verified and not s.attack_passed:
        phase = "GENERATE_ATTACKS"
    elif s.attack_passed and not s.transfer_passed:
        phase = "GENERATE_TRANSFER_TESTS"
    elif s.transfer_passed and not s.reconstruction_passed:
        phase = "GENERATE_RECONSTRUCTION_TESTS"
    else:
        phase = None

    pool = admissible(s, b, actions)
    if not pool:
        if not s.apparatus_valid:
            return Decision("DIRECTIVE", "REPAIR_APPARATUS", "No budget-feasible repair exists")
        if phase:
            return Decision("DIRECTIVE", phase, "Required post-success gate has no admissible action")
        if s.reconstruction_passed:
            return Decision(
                "DIRECTIVE",
                "RETAIN",
                "Attack, transfer, and reconstruction gates have passed",
            )

        exhausted = generator_boundary_exhausted(
            generator_specs, generator_runs, s.unresolved_surprise
        )
        if not exhausted:
            return Decision(
                "DIRECTIVE",
                "EXPAND_CANDIDATES",
                "Frozen generator boundary is not exhausted or has unresolved surprise/pending/leakage",
            )
        if not s.residual_sharp:
            return Decision(
                "DIRECTIVE",
                "MAP",
                "Residual remains unsharp after audited generator exhaustion",
            )
        return Decision(
            "DIRECTIVE",
            "REFRAME",
            "Audited frozen same-frame generator boundary is exhausted",
        )

    best = min(pool, key=lambda a: action_rank(s, a))
    d = robust_worst_case_elimination(best, len(s.hypotheses))

    if d == 0 and not s.target_verified:
        exhausted = generator_boundary_exhausted(
            generator_specs, generator_runs, s.unresolved_surprise
        )
        if not exhausted:
            return Decision(
                "DIRECTIVE",
                "EXPAND_CANDIDATES",
                "Current pool has zero robust discrimination and generator boundary remains open",
            )
        if not s.residual_sharp:
            return Decision(
                "DIRECTIVE",
                "MAP",
                "Exhausted candidate pool cannot discriminate and residual is unsharp",
            )
        return Decision(
            "DIRECTIVE",
            "REFRAME",
            "Exhausted audited same-frame pool has zero robust discrimination",
        )

    return Decision(
        "ACTION",
        best.name,
        f"robust_split_fraction={robust_split_fraction(best, len(s.hypotheses)):.6f};"
        f"generator={best.generator};source={best.source}",
    )


def update_hypotheses(s: ResearchState, a: CandidateAction, observed: str):
    compatible = tuple(
        h for h, poss in zip(s.hypotheses, a.predictions) if observed in poss
    )
    return (compatible, False) if compatible else (s.hypotheses, True)
