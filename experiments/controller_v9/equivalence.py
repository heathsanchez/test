from dataclasses import dataclass
from typing import FrozenSet

@dataclass(frozen=True)
class Probe:
    name: str

@dataclass(frozen=True)
class Move:
    name: str
    source: str
    # Frozen pre-outcome behavioral signature over declared probes.
    # Each element is the set of possible observable effects under that probe.
    signature: tuple[FrozenSet[str], ...]
    protected_outcome_access: bool = False

@dataclass(frozen=True)
class EquivalenceProtocol:
    probes: tuple[Probe, ...]
    frozen_before_outcomes: bool


def valid_protocol(p: EquivalenceProtocol) -> bool:
    return p.frozen_before_outcomes and len(p.probes) > 0


def admissible_move(m: Move, p: EquivalenceProtocol) -> bool:
    return valid_protocol(p) and not m.protected_outcome_access and len(m.signature) == len(p.probes)


def preoutcome_equivalent(a: Move, b: Move, p: EquivalenceProtocol) -> bool:
    """Equivalence is determined only from the frozen pre-outcome probe language.

    No protected result, later success/failure, or post-hoc semantic label may be
    used to merge proposals after the fact.
    """
    if not (admissible_move(a,p) and admissible_move(b,p)):
        return False
    return a.signature == b.signature


def equivalence_classes(moves: list[Move], p: EquivalenceProtocol):
    classes: list[list[Move]] = []
    for m in moves:
        if not admissible_move(m,p):
            continue
        for c in classes:
            if preoutcome_equivalent(m,c[0],p):
                c.append(m)
                break
        else:
            classes.append([m])
    return classes


def source_substitution(moves: list[Move], p: EquivalenceProtocol, source: str):
    """For every equivalence class containing `source`, report whether a different
    source independently generated an outcome-blind equivalent move."""
    out=[]
    for c in equivalence_classes(moves,p):
        sources={m.source for m in c}
        if source in sources:
            out.append((tuple(sorted(m.name for m in c)), bool(sources-{source})))
    return out
