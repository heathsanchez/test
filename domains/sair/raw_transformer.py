from __future__ import annotations

from typing import Any, Iterable, Mapping


# Program-table records contain both executable probe syntax and runtime metadata.
# Raw transformer synthesis is defined over syntax only.  In particular, `cost`
# is an execution/planning annotation, and `ast` is the external program id/string;
# neither is an editable AST coordinate nor part of structural materialization.
_NON_SYNTAX_FIELDS = frozenset({"ast", "cost"})


def _atom(domain, pid: str):
    p = domain.programs.get(pid)
    if not p or p.get("kind") != "atom":
        return None
    return p


def _syntax_fields(program: Mapping[str, Any]) -> tuple[str, ...]:
    return tuple(sorted(k for k in program if k not in _NON_SYNTAX_FIELDS))


def _same_probe_syntax(a: Mapping[str, Any], b: Mapping[str, Any]) -> bool:
    keys = (set(a) | set(b)) - _NON_SYNTAX_FIELDS
    return all(a.get(k) == b.get(k) for k in keys)


def enumerate_raw_literal_rewrites(domain, state, literal_carrier=(1, 2, 3, 4)) -> Iterable[tuple[str, Mapping[str, Any]]]:
    """Enumerate generic one-literal syntax rewrites over installed atomic probes.

    The carrier has no semantic operator names. It selects an integer-valued probe
    syntax field, replaces its value by another literal from the frozen carrier,
    and copies all other syntax unchanged. Runtime metadata such as execution cost
    is deliberately outside the transformer language.
    """
    out = []
    for source_id in sorted(state.probe_language):
        src = _atom(domain, source_id)
        if src is None:
            continue
        int_paths = sorted(
            k for k in _syntax_fields(src)
            if isinstance(src.get(k), int) and not isinstance(src.get(k), bool)
        )
        for path in int_paths:
            old = int(src[path])
            for new in literal_carrier:
                if new == old:
                    continue
                candidate = dict(src)
                candidate[path] = int(new)
                for pid, p in domain.programs.items():
                    if p.get("kind") != "atom":
                        continue
                    if _same_probe_syntax(candidate, p):
                        rec = {
                            "kind": "RAW_LITERAL_REWRITE",
                            "path": path,
                            "from_literal": old,
                            "to_literal": int(new),
                            "source_probe": source_id,
                            "candidate_probe": pid,
                            "edit_count": 1,
                            "cost": 1,
                        }
                        out.append((pid, rec))
    seen = set()
    for pid, rec in sorted(out, key=lambda x: (x[1]["cost"], x[1]["path"], x[1]["from_literal"], x[1]["to_literal"], x[0])):
        key = (pid, rec["path"], rec["from_literal"], rec["to_literal"])
        if key in seen:
            continue
        seen.add(key)
        yield pid, rec


def induce_verified_raw_literal_rewrite(domain, before, after, probe_id: str, record: Any) -> Iterable[Mapping[str, Any]]:
    """Type a verified raw syntax edit only after selection and execution."""
    target = _atom(domain, probe_id)
    if target is None:
        return ()
    candidates = []
    for source_id in sorted(before.probe_language):
        src = _atom(domain, source_id)
        if src is None:
            continue
        differing = []
        compatible = True
        keys = (set(src) | set(target)) - _NON_SYNTAX_FIELDS
        for k in keys:
            a, b = src.get(k), target.get(k)
            if a == b:
                continue
            if isinstance(a, int) and not isinstance(a, bool) and isinstance(b, int) and not isinstance(b, bool):
                differing.append((k, int(a), int(b)))
            else:
                compatible = False
                break
        if compatible and len(differing) == 1:
            path, old, new = differing[0]
            candidates.append((source_id, path, old, new))
    if not candidates:
        return ()
    source_id, path, old, new = sorted(candidates, key=lambda x: (x[1], x[2], x[3], x[0]))[0]
    return ({
        "id": f"RAW_LITERAL_REWRITE[{path}:{old}->{new}]",
        "kind": "RAW_LITERAL_REWRITE",
        "path": path,
        "from_literal": old,
        "to_literal": new,
        "source_probe": source_id,
        "verified_probe": probe_id,
        "cost": 1,
    },)


def expand_raw_literal_rewrite(domain, state, operator: Mapping[str, Any]) -> Iterable[str]:
    """Reuse a frozen literal-rewrite schema on compatible installed probes."""
    if operator.get("kind") != "RAW_LITERAL_REWRITE":
        return ()
    path = str(operator["path"])
    old = int(operator["from_literal"])
    new = int(operator["to_literal"])
    out = []
    for source_id in sorted(state.probe_language):
        src = _atom(domain, source_id)
        if src is None or src.get(path) != old:
            continue
        candidate = dict(src)
        candidate[path] = new
        for pid, p in domain.programs.items():
            if p.get("kind") != "atom":
                continue
            if _same_probe_syntax(candidate, p):
                out.append(pid)
    return tuple(sorted(set(out)))
