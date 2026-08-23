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
class GeneratorSpec:
    name: str
    family: str
    required_slots: tuple[str, ...]
    required: bool = True


@dataclass(frozen=True)
class GeneratorRun:
    generator: str
    attempted_slots: FrozenSet[str]
    pending_slots: FrozenSet[str] = frozenset()
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
    target_verified: bool = False
    attack_passed: bool = False
    transfer_passed: bool = False
    reconstruction_passed: bool = False
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
    generator_slot: str
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
    kind: str
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


def adversarially_expand_predictions(
    a: CandidateAction, critic_predictions: tuple[OutcomeSet, ...]
) -> CandidateAction:
    if len(critic_predictions) != len(a.predictions):
        raise ValueError("critic prediction count mismatch")
    return replace(
        a,
        predictions=tuple(p | c for p, c in zip(a.predictions, critic_predictions)),
    )


def buffer_import(hypotheses: tuple[str, ...], artifact: ImportArtifact):
    if not (artifact.has_structural_mapping and artifact.has_differential_prediction):
        return hypotheses
    if artifact.proposed_hypothesis in hypotheses:
        return hypotheses
    return hypotheses + (artifact.proposed_hypothesis,)


def _spec_map(specs: tuple[GeneratorSpec, ...]):
    names = [s.name for s in specs]
    if len(names) != len(set(names)):
        raise ValueError("generator names must be unique")
    for s in specs:
        if len(s.required_slots) != len(set(s.required_slots)):
            raise ValueError(f"{s.name}: generator slots must be unique")
    return {s.name: s for s in specs}


def validate_generator_ledger(
    specs: tuple[GeneratorSpec, ...], runs: tuple[GeneratorRun, ...]
) -> None:
    sm = _spec_map(specs)
    for r in runs:
        if r.generator not in sm:
            raise ValueError(f"unknown generator in ledger: {r.generator}")
        allowed = set(sm[r.generator].required_slots)
        if not set(r.attempted_slots).issubset(allowed):
            raise ValueError(f"{r.generator}: attempted undeclared slot")
        if not set(r.pending_slots).issubset(allowed):
            raise ValueError(f"{r.generator}: pending undeclared slot")
        if set(r.attempted_slots) & set(r.pending_slots):
            raise ValueError(f"{r.generator}: slot cannot be attempted and pending")


def generator_boundary_exhausted(
    specs: tuple[GeneratorSpec, ...],
    runs: tuple[GeneratorRun, ...],
    unresolved_surprise: bool = False,
) -> bool:
    """Close only when every frozen required search slot has actually been attempted.

    Duplicate proposals cannot pad exhaustion because coverage is over named slots,
    not raw attempt counts.
    """
    validate_generator_ledger(specs, runs)
    if unresolved_surprise:
        return False

    attempted = {s.name: set() for s in specs}
    pending = {s.name: set() for s in specs}
    leaked = {s.name: False for s in specs}
    for r in runs:
        attempted[r.generator] |= set(r.attempted_slots)
        pending[r.generator] |= set(r.pending_slots)
        leaked[r.generator] = leaked[r.generator] or r.leaked

    for spec in specs:
        if not spec.required:
            continue
        if not set(spec.required_slots).issubset(attempted[spec.name]):
            return False
        if pending[spec.name] or leaked[spec.name]:
            return False
    return True


def validate_actions(
    hypotheses: tuple[str, ...],
    specs: tuple[GeneratorSpec, ...],
    actions: list[CandidateAction],
) -> None:
    sm = _spec_map(specs)
    for a in actions:
        if len(a.predictions) != len(hypotheses):
            raise ValueError(f"{a.name}: predictions must match live hypotheses")
        if a.generator not in sm:
            raise ValueError(f"{a.name}: undeclared generator {a.generator}")
        if a.generator_slot not in sm[a.generator].required_slots:
            raise ValueError(f"{a.name}: undeclared generator slot {a.generator_slot}")


def observational_classes(actions: list[CandidateAction], n: int):
    """Collapse rivals indistinguishable in the current audited action language.

    Duplicate hypothesis labels therefore cannot inflate discrimination merely by
    increasing the raw rival count.
    """
    audited = [a for a in actions if not a.protected_outcome_access]
    if not audited:
        return tuple((i,) for i in range(n))

    by_signature: dict[tuple, list[int]] = {}
    for i in range(n):
        sig = tuple(tuple(sorted(a.predictions[i])) for a in audited)
        by_signature.setdefault(sig, []).append(i)
    return tuple(tuple(v) for v in by_signature.values())


def robust_class_split_fraction(
    a: CandidateAction, language: list[CandidateAction], n: int
) -> float:
    classes = observational_classes(language, n)
    if len(classes) <= 1:
        return 1.0 if n <= 1 else 0.0

    outcomes = set().union(*a.predictions) if a.predictions else set()
    if not outcomes:
        return 0.0

    worst_surviving_classes = 0
    for outcome in outcomes:
        survivors = 0
        for cls in classes:
            possible = set().union(*(a.predictions[i] for i in cls))
            if outcome in possible:
                survivors += 1
        worst_surviving_classes = max(worst_surviving_classes, survivors)

    return (len(classes) - worst_surviving_classes) / (len(classes) - 1)


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
    if s.target_verified and not s.attack_passed:
        return a.is_ablation_or_control
    if s.attack_passed and not s.transfer_passed:
        return a.is_transfer_test
    if s.transfer_passed and not s.reconstruction_passed:
        return a.is_reconstruction_test
    return True


def admissible(s: ResearchState, b: Budget, actions: list[CandidateAction]):
    pool = [a for a in actions if fits_budget(a, b) and not a.protected_outcome_access]
    if not s.apparatus_valid:
        return [a for a in pool if a.lifecycle == "REPAIR"]
    if s.existing_structure_unknown:
        inspections = [a for a in pool if a.inspects_existing_closure]
        pool = inspections if inspections else [a for a in pool if not a.changes_representation]
    return [a for a in pool if action_phase_ok(s, a)]


def action_rank(
    s: ResearchState,
    a: CandidateAction,
    language: list[CandidateAction],
):
    lifecycle, mode = warranted_mode(s)
    split = robust_class_split_fraction(a, language, len(s.hypotheses))
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
    validate_actions(s.hypotheses, generator_specs, actions)

    if s.target_verified and not s.attack_passed:
        phase = "GENERATE_ATTACKS"
    elif s.attack_passed and not s.transfer_passed:
        phase = "GENERATE_TRANSFER_TESTS"
    elif s.transfer_passed and not s.reconstruction_passed:
        phase = "GENERATE_RECONSTRUCTION_TESTS"
    else:
        phase = None

    pool = admissible(s, b, actions)
    language = [a for a in actions if not a.protected_outcome_access]

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
                "Frozen generator slot coverage is incomplete or invalid",
            )
        if not s.residual_sharp:
            return Decision(
                "DIRECTIVE",
                "MAP",
                "Residual remains unsharp after audited slot-complete generation",
            )
        return Decision(
            "DIRECTIVE",
            "REFRAME",
            "Audited same-frame generator slots are exhausted",
        )

    best = min(pool, key=lambda a: action_rank(s, a, language))
    split = robust_class_split_fraction(best, language, len(s.hypotheses))

    if split == 0.0 and not s.target_verified:
        exhausted = generator_boundary_exhausted(
            generator_specs, generator_runs, s.unresolved_surprise
        )
        if not exhausted:
            return Decision(
                "DIRECTIVE",
                "EXPAND_CANDIDATES",
                "Current audited language has zero class discrimination and slots remain open",
            )
        if not s.residual_sharp:
            return Decision(
                "DIRECTIVE",
                "MAP",
                "Slot-complete action language cannot distinguish observational classes",
            )
        return Decision(
            "DIRECTIVE",
            "REFRAME",
            "Slot-complete same-frame language has zero observational-class discrimination",
        )

    classes = observational_classes(language, len(s.hypotheses))
    return Decision(
        "ACTION",
        best.name,
        f"robust_class_split_fraction={split:.6f};"
        f"observational_classes={len(classes)};"
        f"generator={best.generator};slot={best.generator_slot};source={best.source}",
    )


def update_hypotheses(s: ResearchState, a: CandidateAction, observed: str):
    compatible = tuple(
        h for h, poss in zip(s.hypotheses, a.predictions) if observed in poss
    )
    return (compatible, False) if compatible else (s.hypotheses, True)
