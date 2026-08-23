from dataclasses import dataclass
from collections import Counter

@dataclass(frozen=True)
class ResearchState:
    name: str
    apparatus_valid: bool = True
    residual_sharp: bool = True
    existing_structure_unknown: bool = False
    repeated_local_failures: int = 0
    conditional_regimes: bool = False
    transfer_candidate_ready: bool = False
    retention_candidate_ready: bool = False
    external_import_active: bool = False

@dataclass(frozen=True)
class CandidateAction:
    name: str
    lifecycle: str
    mode: str
    # One predicted observable outcome per live hypothesis, same order as hypotheses.
    # Equal symbols mean the action cannot distinguish those hypotheses.
    predictions: tuple[str, ...]
    model_calls: int = 0
    verifier_calls: int = 0
    candidate_count: int = 0
    tokens: int = 0
    wall_units: int = 0
    scaffold_additions: int = 0
    semantic_risk: int = 0
    changes_representation: bool = False
    inspects_existing_closure: bool = False


def research_mode(s: ResearchState):
    """V2 factorization retained as a prior over what kind of move is warranted."""
    if not s.apparatus_valid:
        lifecycle = "REPAIR"
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
    elif s.repeated_local_failures >= 2 or s.conditional_regimes:
        mode = "REFRAME"
    else:
        mode = "EXPLOIT"
    return lifecycle, mode


def worst_case_elimination(predictions: tuple[str, ...]) -> int:
    """Distribution-free discrimination value: hypotheses eliminated in worst case."""
    if not predictions:
        return 0
    largest_surviving_cell = max(Counter(predictions).values())
    return len(predictions) - largest_surviving_cell


def cost_vector(a: CandidateAction):
    # Lexicographic, transparent, no arbitrary weighted-dollar scalar.
    return (a.model_calls, a.verifier_calls, a.candidate_count, a.tokens, a.wall_units)


def admissible_actions(s: ResearchState, actions: list[CandidateAction]):
    if not actions:
        return []
    # Apparatus failure is upstream of semantic inference.
    if not s.apparatus_valid:
        repair = [a for a in actions if a.lifecycle == "REPAIR"]
        return repair
    # Closure-before-invention: if a proposed representation/object may already
    # exist, inspect current closure before representation-changing actions.
    if s.existing_structure_unknown:
        inspect = [a for a in actions if a.inspects_existing_closure]
        if inspect:
            return inspect
        return [a for a in actions if not a.changes_representation]
    return actions


def rank_key(s: ResearchState, a: CandidateAction):
    lifecycle, mode = research_mode(s)
    discrimination = worst_case_elimination(a.predictions)
    # Priority order is predeclared rather than tuned to historical labels:
    # 1. eliminate live rivals in the worst case;
    # 2. match the warranted lifecycle/mode when discrimination ties;
    # 3. avoid new scaffolding and semantic risk;
    # 4. minimize explicit resource vector.
    return (
        -discrimination,
        -(a.lifecycle == lifecycle),
        -(a.mode == mode),
        a.scaffold_additions,
        a.semantic_risk,
        cost_vector(a),
        a.name,
    )


def choose_action(s: ResearchState, hypotheses: tuple[str, ...], actions: list[CandidateAction]):
    for a in actions:
        if len(a.predictions) != len(hypotheses):
            raise ValueError(f"{a.name}: prediction count must match live hypotheses")
    pool = admissible_actions(s, actions)
    if not pool:
        return None
    return min(pool, key=lambda a: rank_key(s, a))


def import_is_admissible(s: ResearchState) -> bool:
    # External novelty never has authority by itself. It becomes active only when
    # internal evidence warrants a map/reframe/inspect transition.
    return s.external_import_active and (
        not s.residual_sharp or s.repeated_local_failures >= 2 or
        s.conditional_regimes or s.existing_structure_unknown
    )
