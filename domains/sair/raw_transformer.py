from __future__ import annotations

from typing import Any, Iterable, Mapping


def _atom(domain, pid: str):
    p = domain.programs.get(pid)
    if not p or p.get("kind") != "atom":
        return None
    return p


def enumerate_raw_literal_rewrites(domain, state, literal_carrier=(1, 2, 3, 4)) -> Iterable[tuple[str, Mapping[str, Any]]]:
    """Enumerate generic one-literal AST rewrites over installed atomic probes.

    The carrier has no semantic operator names. It simply selects an integer-valued
    AST field, replaces its value by another literal from the frozen carrier, and
    copies all other fields unchanged. Candidate program IDs must already exist in
    the domain's raw executable program table so the verifier can evaluate them.
    """
    out = []
    for source_id in sorted(state.probe_language):
        src = _atom(domain, source_id)
        if src is None:
            continue
        int_paths = sorted(k for k, v in src.items() if isinstance(v, int) and not isinstance(v, bool))
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
                    # Generic structural equality after the single raw edit.
                    keys = set(candidate) | set(p)
                    if all(candidate.get(k) == p.get(k) for k in keys if k != "ast"):
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
    # Stable unique carrier.
    seen = set()
    for pid, rec in sorted(out, key=lambda x: (x[1]["cost"], x[1]["path"], x[1]["from_literal"], x[1]["to_literal"], x[0])):
        key = (pid, rec["path"], rec["from_literal"], rec["to_literal"])
        if key in seen:
            continue
        seen.add(key)
        yield pid, rec


def induce_verified_raw_literal_rewrite(domain, before, after, probe_id: str, record: Any) -> Iterable[Mapping[str, Any]]:
    """Type a verified raw edit only after it has been selected and executed.

    This does not infer arithmetic meaning. It stores the literal substitution and
    AST path that relate a prior installed probe to the verified new probe.
    """
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
        for k in set(src) | set(target):
            if k == "ast":
                continue
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
            keys = set(candidate) | set(p)
            if all(candidate.get(k) == p.get(k) for k in keys if k != "ast"):
                out.append(pid)
    return tuple(sorted(set(out)))
