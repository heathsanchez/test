from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable, Iterable, Mapping, Sequence


@dataclass(frozen=True)
class RawEdit:
    """Generic structural edit. No semantic operator type is attached."""

    path: tuple[Any, ...]
    replacement: Any
    cost: float = 1.0


@dataclass(frozen=True)
class RawTransformer:
    """A first-class transformer represented only by raw structural edits."""

    id: str
    edits: tuple[RawEdit, ...]
    cost: float
    induction_source: str | None = None
    induction_target: str | None = None


def _replace_at_path(obj: Any, path: Sequence[Any], replacement: Any) -> Any:
    if not path:
        return replacement
    head, *tail = path
    if isinstance(obj, dict):
        out = dict(obj)
        out[head] = _replace_at_path(obj[head], tail, replacement)
        return out
    if isinstance(obj, tuple):
        out = list(obj)
        out[int(head)] = _replace_at_path(obj[int(head)], tail, replacement)
        return tuple(out)
    if isinstance(obj, list):
        out = list(obj)
        out[int(head)] = _replace_at_path(obj[int(head)], tail, replacement)
        return out
    raise TypeError(f"cannot descend through {type(obj)!r} at {head!r}")


def apply_transformer(ast: Any, transformer: RawTransformer) -> Any:
    out = ast
    for edit in transformer.edits:
        out = _replace_at_path(out, edit.path, edit.replacement)
    return out


def iter_literal_paths(obj: Any, path: tuple[Any, ...] = ()) -> Iterable[tuple[tuple[Any, ...], int]]:
    if isinstance(obj, bool):
        return
    if isinstance(obj, int):
        yield path, obj
        return
    if isinstance(obj, dict):
        for key in sorted(obj):
            yield from iter_literal_paths(obj[key], path + (key,))
        return
    if isinstance(obj, (list, tuple)):
        for i, value in enumerate(obj):
            yield from iter_literal_paths(value, path + (i,))


def structural_skeleton(obj: Any, ignored_paths: frozenset[tuple[Any, ...]], path: tuple[Any, ...] = ()) -> Any:
    if path in ignored_paths:
        return ("EDIT",)
    if isinstance(obj, dict):
        return ("dict", tuple((k, structural_skeleton(obj[k], ignored_paths, path + (k,))) for k in sorted(obj)))
    if isinstance(obj, tuple):
        return ("tuple", tuple(structural_skeleton(v, ignored_paths, path + (i,)) for i, v in enumerate(obj)))
    if isinstance(obj, list):
        return ("list", tuple(structural_skeleton(v, ignored_paths, path + (i,)) for i, v in enumerate(obj)))
    return (type(obj).__name__, obj)


def shape_preserved_except_edits(source: Any, candidate: Any, transformer: RawTransformer) -> bool:
    ignored = frozenset(edit.path for edit in transformer.edits)
    return structural_skeleton(source, ignored) == structural_skeleton(candidate, ignored)


def enumerate_raw_literal_transformers(
    source_ast: Any,
    literal_carrier: Iterable[int],
    *,
    max_edits: int = 1,
) -> Iterable[RawTransformer]:
    """Exhaustive finite carrier of generic literal-replacement programs.

    The carrier knows nothing about order, successor, arithmetic roles, or probe semantics.
    """
    if max_edits != 1:
        raise NotImplementedError("V32 frozen carrier uses exactly one raw edit")
    literals = list(iter_literal_paths(source_ast))
    for path, old in literals:
        for replacement in sorted(set(int(x) for x in literal_carrier)):
            if replacement == old:
                continue
            tid = f"RAW_REPLACE({path!r},{replacement!r})"
            yield RawTransformer(tid, (RawEdit(path, replacement, 1.0),), 1.0)


@dataclass(frozen=True)
class TransformerCandidateResult:
    transformer: RawTransformer
    generated_id: str | None
    obligations: Mapping[str, bool]
    decision_effect: float
    objective: tuple[float, str]

    @property
    def admissible(self) -> bool:
        return all(self.obligations.values())


def synthesize_minimal_transformer(
    *,
    source_id: str,
    source_ast: Any,
    literal_carrier: Iterable[int],
    materialize: Callable[[Any], str | None],
    evaluate_decision_effect: Callable[[str], float],
    require_transfer: Callable[[RawTransformer], bool],
) -> tuple[RawTransformer | None, list[TransformerCandidateResult]]:
    """Search the frozen raw-transformer carrier against K_meta.

    Semantic names and intended numeric deltas are absent. `materialize` is a domain
    parser/registry hook from raw AST back to an executable intervention id.
    """
    audit: list[TransformerCandidateResult] = []
    winners: list[TransformerCandidateResult] = []
    for raw in enumerate_raw_literal_transformers(source_ast, literal_carrier):
        candidate_ast = apply_transformer(source_ast, raw)
        generated_id = materialize(candidate_ast)
        effect = 0.0 if generated_id is None else float(evaluate_decision_effect(generated_id))
        obligations = {
            "NON_IDENTITY": candidate_ast != source_ast,
            "SHAPE_PRESERVED_EXCEPT_EDIT": shape_preserved_except_edits(source_ast, candidate_ast, raw),
            "VERIFIED_DECISION_EFFECT": generated_id is not None and effect > 0.0,
            "TRANSFER": require_transfer(raw),
        }
        result = TransformerCandidateResult(
            transformer=raw,
            generated_id=generated_id,
            obligations=obligations,
            decision_effect=effect,
            objective=(raw.cost, raw.id),
        )
        audit.append(result)
        if result.admissible:
            winners.append(result)
    if not winners:
        return None, audit
    winners.sort(key=lambda r: r.objective)
    best_cost = winners[0].transformer.cost
    minimum = [r for r in winners if r.transformer.cost == best_cost]
    # Falsify instead of choosing semantically when distinct minimum effects survive.
    distinct = {(r.generated_id, round(r.decision_effect, 12)) for r in minimum}
    if len(distinct) != 1:
        return None, audit
    chosen = minimum[0].transformer
    return RawTransformer(
        id=chosen.id,
        edits=chosen.edits,
        cost=chosen.cost,
        induction_source=source_id,
        induction_target=minimum[0].generated_id,
    ), audit
