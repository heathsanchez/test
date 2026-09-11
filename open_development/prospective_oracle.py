"""Independent evaluator for the prospective finite AST substrate.

This deliberately reimplements state projection, enumeration, interpretation,
and minimal-survivor checking rather than calling the developer's methods.
"""
from __future__ import annotations

import json
from typing import Any, Mapping

from .prospective_genesis import (D4, FORM_OPS, INTERACTION_PROBES,
                                   INTERACTION_PROBE_MANIFEST, MAX_AST_DEPTH,
                                   MAX_AST_SIZE, SUBSTRATE)


def G(value: Any) -> tuple[tuple[int, ...], ...]:
    return tuple(tuple(int(x) for x in row) for row in value)


def R(value: Any) -> tuple[tuple[int, ...], ...]:
    return tuple(zip(*G(value)[::-1]))


def T(value: Any, name: str) -> tuple[tuple[int, ...], ...]:
    g = G(value)
    r1, r2 = R(g), R(R(g))
    r3 = R(r2)
    return {"id": g, "r90": r1, "r180": r2, "r270": r3,
            "flip-h": tuple(tuple(reversed(row)) for row in g),
            "flip-v": tuple(reversed(g)), "transpose": tuple(zip(*g)),
            "anti": tuple(zip(*tuple(reversed(g))))[::-1]}[name]


def C(value: Any) -> tuple[tuple[int, ...], ...]:
    g = G(value)
    points = [(i, j) for i, row in enumerate(g) for j, x in enumerate(row) if x]
    if not points:
        return g
    top, bottom = min(i for i, _ in points), max(i for i, _ in points)
    left, right = min(j for _, j in points), max(j for _, j in points)
    return tuple(row[left:right + 1] for row in g[top:bottom + 1])


def F(left: Any, right: Any, operation: str) -> Any:
    a, b = G(left), G(right)
    if operation == "concat-h" and len(a) == len(b):
        return tuple(x + y for x, y in zip(a, b))
    if operation == "concat-v" and len(a[0]) == len(b[0]):
        return a + b
    if operation == "overlay" and (len(a), len(a[0])) == (len(b), len(b[0])):
        return tuple(tuple(max(x, y) for x, y in zip(ar, br)) for ar, br in zip(a, b))
    return None


def key(ast: Mapping[str, Any]) -> str:
    return json.dumps(ast, sort_keys=True, separators=(",", ":"))


def size(ast: Mapping[str, Any]) -> int:
    if ast["op"] == "input":
        return 1
    if ast["op"] in {"call", "crop"}:
        return 1 + size(ast["arg"])
    return 1 + size(ast["left"]) + size(ast["right"])


def depth(ast: Mapping[str, Any]) -> int:
    if ast["op"] == "input":
        return 1
    if ast["op"] in {"call", "crop"}:
        return 1 + depth(ast["arg"])
    return 1 + max(depth(ast["left"]), depth(ast["right"]))


def dependencies(ast: Mapping[str, Any]) -> tuple[str, ...]:
    found: list[str] = []

    def visit(node: Mapping[str, Any]) -> None:
        if node["op"] == "call":
            if node["callee"] not in found:
                found.append(node["callee"])
            visit(node["arg"])
        elif node["op"] == "crop":
            visit(node["arg"])
        elif node["op"] in FORM_OPS:
            visit(node["left"])
            visit(node["right"])

    visit(ast)
    return tuple(found)


def state_at(events: list[Mapping[str, Any]], count: int) -> dict[str, Any]:
    active: dict[str, Any] = {}
    for event in events[:count]:
        if event["type"] == "admit":
            active[event["record"]["id"]] = event["record"]
        elif event["type"] == "revoke":
            for rid in event["ids"]:
                active.pop(rid, None)
    observations = sorted(rid for rid, rec in active.items() if rec["repair"]["kind"] == "observation")
    policies = {rec["repair"]["scope"]: rid for rid, rec in active.items()
                if rec["repair"]["kind"] == "policy"}
    return {"capabilities": active, "observations": observations, "policies": policies}


def _grid_cap(record: Mapping[str, Any]) -> bool:
    contract = record["repair"].get("contract") or {}
    return contract.get("input_type") == "Grid" and contract.get("output_type") == "Grid"


def enumerate_asts(state: Mapping[str, Any]) -> tuple[dict[str, Any], ...]:
    inp = {"op": "input"}
    terms = [inp, {"op": "crop", "arg": inp}]
    for rid, record in sorted(state["capabilities"].items()):
        body = record["repair"]["payload"].get("body", {})
        if _grid_cap(record) and body != {"op": "d4", "name": "id"}:
            terms.append({"op": "call", "callee": rid, "arg": inp})
    terms = list({key(ast): ast for ast in terms}.values())
    terms.sort(key=key)
    generated: dict[str, dict[str, Any]] = {}
    for operation in FORM_OPS:
        for left in terms:
            for right in terms:
                if operation == "overlay" and key(left) > key(right):
                    continue
                ast = {"op": operation, "left": left, "right": right}
                if size(ast) <= MAX_AST_SIZE and depth(ast) <= MAX_AST_DEPTH:
                    generated[key(ast)] = ast
    return tuple(sorted(generated.values(), key=lambda ast: (size(ast), key(ast))))


def _eval_ast(state: Mapping[str, Any], ast: Mapping[str, Any], value: Any,
              trace: list[str], active: tuple[str, ...]) -> Any:
    operation = ast.get("op")
    if operation == "input":
        return G(value)
    if operation == "crop":
        child = _eval_ast(state, ast["arg"], value, trace, active)
        return None if child is None else C(child)
    if operation == "call":
        child = _eval_ast(state, ast["arg"], value, trace, active)
        return None if child is None else execute(state, ast["callee"], child, trace, active)
    if operation in FORM_OPS:
        left = _eval_ast(state, ast["left"], value, trace, active)
        right = _eval_ast(state, ast["right"], value, trace, active)
        return None if left is None or right is None else F(left, right, operation)
    return None


def execute(state: Mapping[str, Any], rid: str, value: Any, trace: list[str] | None = None,
            active: tuple[str, ...] = ()) -> Any:
    trace = [] if trace is None else trace
    if rid in active:
        return None
    record = state["capabilities"].get(rid)
    if not record:
        return None
    trace.append(rid)
    repair = record["repair"]
    body = repair["payload"].get("body", {})
    if body.get("op") == "d4":
        return T(value, body["name"])
    if body.get("op") == "crop-call":
        parent = body.get("callee")
        if repair["dependencies"] != [parent]:
            return None
        return execute(state, parent, C(value), trace, (*active, rid))
    if body.get("op") == "generated-ast":
        ast = body.get("ast")
        if (body.get("substrate_id") != SUBSTRATE["substrate_id"]
                or not isinstance(ast, Mapping)
                or repair["dependencies"] != list(dependencies(ast))):
            return None
        return _eval_ast(state, ast, value, trace, (*active, rid))
    return None


def ast_semantic_key(state: Mapping[str, Any], ast: Mapping[str, Any]) -> str:
    from .runtime import digest
    operation = ast.get("op")
    if operation == "input":
        body: Any = {"op": "input"}
    elif operation == "crop":
        body = {"op": "crop", "arg": ast_semantic_key(state, ast["arg"])}
    elif operation == "call":
        body = {
            "op": "call",
            "callee_semantics": capability_semantic_key(state, ast["callee"]),
            "arg": ast_semantic_key(state, ast["arg"]),
        }
    elif operation in FORM_OPS:
        left = ast_semantic_key(state, ast["left"])
        right = ast_semantic_key(state, ast["right"])
        if operation == "overlay" and left > right:
            left, right = right, left
        body = {"op": operation, "left": left, "right": right}
    else:
        body = {"invalid": key(ast)}
    return digest(body)


def capability_semantic_key(state: Mapping[str, Any], rid: str,
                            active: tuple[str, ...] = ()) -> str:
    from .runtime import digest
    if rid in active:
        return digest({"cycle": rid})
    record = state["capabilities"].get(rid)
    if not record:
        return digest({"missing": rid})
    repair = record["repair"]
    body = repair["payload"].get("body", {})
    common = {
        "verifier": record["evidence"].get("verifier"),
        "contract": repair.get("contract"),
    }
    if body.get("op") == "d4":
        desc = {**common, "op": "d4", "name": body.get("name")}
    elif body.get("op") == "crop-call":
        desc = {
            **common,
            "op": "crop-call",
            "callee_semantics": capability_semantic_key(
                state, body.get("callee"), (*active, rid)
            ),
        }
    elif body.get("op") == "generated-ast":
        desc = {
            **common,
            "op": "generated-ast",
            "substrate_id": body.get("substrate_id"),
            "ast_semantics": ast_semantic_key(state, body.get("ast", {})),
        }
    else:
        desc = {**common, "raw_body": body, "dependencies": repair.get("dependencies", [])}
    return digest(desc)


def _semantic_classes(state: Mapping[str, Any],
                      winners: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], dict[str, Any] | None]:
    from .runtime import digest
    grouped: dict[str, list[dict[str, Any]]] = {}
    for ast in winners:
        grouped.setdefault(ast_semantic_key(state, ast), []).append(ast)
    classes = []
    for class_id in sorted(grouped):
        members = sorted(grouped[class_id], key=key)
        classes.append({
            "class_id": class_id,
            "size": len(members),
            "representative": members[0],
        })
    separator = None
    if len(classes) > 1:
        representatives = [item["representative"] for item in classes]
        for index, probe in enumerate(INTERACTION_PROBES):
            outputs = [_eval_ast(state, ast, probe, [], ()) for ast in representatives]
            if len({repr(output) for output in outputs}) > 1:
                separator = {
                    "probe_index": index,
                    "input": probe,
                    "class_output_digests": [digest(output) for output in outputs],
                }
                break
    return classes, separator


def analyze(state: Mapping[str, Any], task: Mapping[str, Any]) -> dict[str, Any]:
    from .runtime import digest
    candidates = enumerate_asts(state)
    counts: dict[int, int] = {}
    survivors: dict[int, list[dict[str, Any]]] = {}
    for ast in candidates:
        n = size(ast)
        counts[n] = counts.get(n, 0) + 1
        try:
            passed = all(_eval_ast(state, ast, example["input"], [], ()) == G(example["output"])
                         for example in task["train"])
        except Exception:
            passed = False
        if passed:
            survivors.setdefault(n, []).append(ast)
    minimum = min(survivors) if survivors else None
    winners = survivors.get(minimum, []) if minimum is not None else []
    classes, separator = _semantic_classes(state, winners)
    representatives = [item["representative"] for item in classes]
    class_ids = [item["class_id"] for item in classes]
    return {
        "candidate_count": len(candidates),
        "candidate_count_by_size": {str(k): counts[k] for k in sorted(counts)},
        "complete_through_size": MAX_AST_SIZE,
        "minimum_size": minimum,
        "smaller_survivor_count": sum(len(v) for k, v in survivors.items()
                                      if minimum is not None and k < minimum),
        "minimum_survivors": winners,
        "minimum_survivor_count": len(winners),
        "minimum_syntactic_survivor_count": len(winners),
        "minimum_certified_semantic_class_count": len(classes),
        "minimum_interaction_class_count": len(classes),
        "minimum_certified_semantic_class_sizes": [item["size"] for item in classes],
        "minimum_interaction_class_sizes": [item["size"] for item in classes],
        "minimum_class_representatives": representatives,
        "certified_semantic_class_ids": class_ids,
        "interaction_class_ids": class_ids,
        "interaction_probe_manifest": INTERACTION_PROBE_MANIFEST,
        "equivalence_basis": "certified-interpreter-semantic-key",
        "separator_probe": separator,
        "version_space_id": digest({
            "equivalence_basis": "certified-interpreter-semantic-key",
            "semantic_class_ids": class_ids,
        }),
    }


def any_solves(state: Mapping[str, Any], task: Mapping[str, Any]) -> bool:
    for rid in state["capabilities"]:
        try:
            if all(execute(state, rid, example["input"], []) == G(example["output"])
                   for example in tuple(task["train"]) + tuple(task["test"])):
                return True
        except Exception:
            pass
    return False
