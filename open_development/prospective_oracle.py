"""Independent evaluator for the prospective finite AST substrate.

This deliberately reimplements state projection, enumeration, interpretation,
and minimal-survivor checking rather than calling the developer's methods.
"""
from __future__ import annotations

import json
from typing import Any, Mapping

from .prospective_genesis import (D4, FORM_OPS, ITERATIONS, MAX_AST_DEPTH, MAX_AST_SIZE,
                                  OBJECT_MODES, PLACEMENTS, SELECTORS, SUBSTRATE)


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


def BG(g: Any) -> int:
    values = [x for row in G(g) for x in row]
    return min(set(values), key=lambda x: (-values.count(x), x))


def OS(value: Any, mode: str) -> tuple[Any, ...]:
    g = G(value); h, w = len(g), len(g[0]); bg = BG(g)
    if mode == "color-class":
        return tuple(tuple((g[i][j], i, j) for i in range(h) for j in range(w) if g[i][j] == c)
                     for c in sorted({x for row in g for x in row} - {bg}))
    diag, mono = mode.endswith("8"), mode.startswith("mono")
    ds = tuple((a, b) for a in (-1, 0, 1) for b in (-1, 0, 1) if (a, b) != (0, 0)) if diag else ((1, 0), (-1, 0), (0, 1), (0, -1))
    used: set[tuple[int, int]] = set(); found = []
    for i in range(h):
        for j in range(w):
            if (i, j) in used or g[i][j] == bg:
                continue
            seed, todo, cells = g[i][j], [(i, j)], []
            used.add((i, j))
            while todo:
                r, c = todo.pop(); cells.append((g[r][c], r, c))
                for dr, dc in ds:
                    nr, nc = r + dr, c + dc
                    if (0 <= nr < h and 0 <= nc < w and (nr, nc) not in used
                            and g[nr][nc] != bg and (not mono or g[nr][nc] == seed)):
                        used.add((nr, nc)); todo.append((nr, nc))
            found.append(tuple(sorted(cells)))
    return tuple(sorted(found))


def PICK(objs: Any, criterion: str) -> Any:
    if not objs:
        return None
    if criterion == "only":
        return objs[0] if len(objs) == 1 else None
    fun = {"largest": lambda o: len(o), "smallest": lambda o: len(o),
           "topmost": lambda o: min(r for _, r, _ in o),
           "bottommost": lambda o: max(r for _, r, _ in o),
           "leftmost": lambda o: min(c for _, _, c in o),
           "rightmost": lambda o: max(c for _, _, c in o)}[criterion]
    pairs = [(fun(o), o) for o in objs]
    target = max(v for v, _ in pairs) if criterion in {"largest", "bottommost", "rightmost"} else min(v for v, _ in pairs)
    winners = [o for v, o in pairs if v == target]
    return winners[0] if len(winners) == 1 else None


def OT(obj: Any, name: str) -> Any:
    if not obj:
        return None
    top, left = min(r for _, r, _ in obj), min(c for _, _, c in obj)
    cells = tuple((v, r - top, c - left) for v, r, c in obj)
    h, w = max(r for _, r, _ in cells) + 1, max(c for _, _, c in cells) + 1
    def p(r: int, c: int) -> tuple[int, int]:
        return {"id": (r, c), "r90": (c, h - 1 - r), "r180": (h - 1 - r, w - 1 - c),
                "r270": (w - 1 - c, r), "flip-h": (r, w - 1 - c),
                "flip-v": (h - 1 - r, c), "transpose": (c, r),
                "anti": (w - 1 - c, h - 1 - r)}[name]
    return tuple(sorted((v, top + p(r, c)[0], left + p(r, c)[1]) for v, r, c in cells))


def DRAW(root: Any, obj: Any, canvas: str, placement: str, iteration: str) -> Any:
    if not obj:
        return None
    g = G(root); bg = BG(g)
    top, left = min(r for _, r, _ in obj), min(c for _, _, c in obj)
    cells = tuple((v, r - top, c - left) for v, r, c in obj)
    oh, ow = max(r for _, r, _ in cells) + 1, max(c for _, _, c in cells) + 1
    if canvas == "crop":
        out = [[bg] * ow for _ in range(oh)]
        for v, r, c in cells: out[r][c] = v
        return G(out)
    h, w = len(g), len(g[0])
    if canvas == "remove":
        out = [list(row) for row in g]
        for _, r, c in obj: out[r][c] = bg
        return G(out)
    out = [list(row) for row in g] if canvas == "input" else [[bg] * w for _ in range(h)]
    anchor = {"original": (top, left), "upper-left": (0, 0), "upper-right": (0, w - ow),
              "lower-left": (h - oh, 0), "lower-right": (h - oh, w - ow),
              "center": ((h - oh) // 2, (w - ow) // 2)}[placement]
    anchors = [anchor]
    if iteration != "once":
        direction = iteration.split("-")[-1]
        step = {"up": (-oh, 0), "down": (oh, 0), "left": (0, -ow), "right": (0, ow)}[direction]
        pos = (anchor[0] + step[0], anchor[1] + step[1])
        while 0 <= pos[0] and 0 <= pos[1] and pos[0] + oh <= h and pos[1] + ow <= w:
            anchors.append(pos); pos = (pos[0] + step[0], pos[1] + step[1])
    for ar, ac in anchors:
        for v, r, c in cells:
            if 0 <= ar + r < h and 0 <= ac + c < w: out[ar + r][ac + c] = v
    return G(out)


def key(ast: Mapping[str, Any]) -> str:
    return json.dumps(ast, sort_keys=True, separators=(",", ":"))


def size(ast: Mapping[str, Any]) -> int:
    if ast["op"] == "input":
        return 1
    if ast["op"] in {"call", "crop", "objects", "select", "transform-object", "recolor-object", "render-object"}:
        return 1 + size(ast["arg"])
    return 1 + size(ast["left"]) + size(ast["right"])


def depth(ast: Mapping[str, Any]) -> int:
    if ast["op"] == "input":
        return 1
    if ast["op"] in {"call", "crop", "objects", "select", "transform-object", "recolor-object", "render-object"}:
        return 1 + depth(ast["arg"])
    return 1 + max(depth(ast["left"]), depth(ast["right"]))


def dependencies(ast: Mapping[str, Any]) -> tuple[str, ...]:
    found: list[str] = []

    def visit(node: Mapping[str, Any]) -> None:
        if node["op"] == "call":
            if node["callee"] not in found:
                found.append(node["callee"])
            visit(node["arg"])
        elif node["op"] in {"crop", "objects", "select", "transform-object", "recolor-object", "render-object"}:
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


def _colors(task: Mapping[str, Any]) -> tuple[int, ...]:
    return tuple(sorted({int(x) for e in task["train"] for side in ("input", "output")
                         for row in e[side] for x in row}))


def enumerate_asts(state: Mapping[str, Any], task: Mapping[str, Any] | None = None) -> tuple[dict[str, Any], ...]:
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
    if task is not None:
        sources = [inp]
        for rid, record in sorted(state["capabilities"].items()):
            if _grid_cap(record) and record["repair"]["payload"].get("body", {}).get("op") == "generated-ast":
                sources.append({"op": "call", "callee": rid, "arg": inp})
        color_values: tuple[int | None, ...] = (None, *_colors(task))
        d4_ids = {record["repair"]["payload"]["body"]["name"]: rid
                  for rid, record in state["capabilities"].items()
                  if record["repair"]["payload"].get("body", {}).get("op") == "d4"}
        extraction_transforms = ("id", *(name for name in D4 if name != "id" and name in d4_ids))
        for source in sources:
            for mode in OBJECT_MODES:
                objects = {"op": "objects", "mode": mode, "arg": source}
                for selector in SELECTORS:
                    selected = {"op": "select", "criterion": selector, "arg": objects}
                    for transform in extraction_transforms:
                        for color in color_values:
                            obj = selected if color is None else {
                                "op": "recolor-object", "color": color, "arg": selected}
                            ast = {"op": "render-object", "canvas": "crop", "placement": "origin",
                                   "iteration": "once", "arg": obj}
                            if transform != "id":
                                ast = {"op": "call", "callee": d4_ids[transform], "arg": ast}
                            if size(ast) <= MAX_AST_SIZE and depth(ast) <= MAX_AST_DEPTH:
                                generated[key(ast)] = ast
                    for canvas in ("input", "blank"):
                        for color in color_values:
                            obj = selected if color is None else {
                                "op": "recolor-object", "color": color, "arg": selected}
                            ast = {"op": "render-object", "canvas": canvas, "placement": "original",
                                   "iteration": "once", "arg": obj}
                            generated[key(ast)] = ast
                    removal = {"op": "render-object", "canvas": "remove", "placement": "original",
                               "iteration": "once", "arg": selected}
                    generated[key(removal)] = removal
                    for transform in D4:
                        transformed = selected if transform == "id" else {
                            "op": "transform-object", "name": transform, "arg": selected}
                        for canvas in ("input", "blank"):
                            for placement in PLACEMENTS:
                                ast = {"op": "render-object", "canvas": canvas,
                                       "placement": placement, "iteration": "once", "arg": transformed}
                                if size(ast) <= MAX_AST_SIZE and depth(ast) <= MAX_AST_DEPTH:
                                    generated[key(ast)] = ast
                    for canvas in ("input", "blank"):
                        for iteration in ITERATIONS:
                            for color in color_values:
                                obj = selected if color is None else {
                                    "op": "recolor-object", "color": color, "arg": selected}
                                ast = {"op": "render-object", "canvas": canvas,
                                       "placement": "original", "iteration": iteration, "arg": obj}
                                generated[key(ast)] = ast
    return tuple(sorted(generated.values(), key=lambda ast: (size(ast), key(ast))))


def _eval_ast(state: Mapping[str, Any], ast: Mapping[str, Any], value: Any,
              trace: list[str], active: tuple[str, ...], cache: dict[str, Any] | None = None) -> Any:
    cache_key = key(ast) + ":" + json.dumps(value, separators=(",", ":"))
    if cache is not None and cache_key in cache:
        return cache[cache_key]
    operation = ast.get("op")
    if operation == "input":
        result = G(value)
    elif operation == "crop":
        child = _eval_ast(state, ast["arg"], value, trace, active, cache)
        result = None if child is None else C(child)
    elif operation == "call":
        child = _eval_ast(state, ast["arg"], value, trace, active, cache)
        result = None if child is None else execute(state, ast["callee"], child, trace, active)
    elif operation in FORM_OPS:
        left = _eval_ast(state, ast["left"], value, trace, active, cache)
        right = _eval_ast(state, ast["right"], value, trace, active, cache)
        result = None if left is None or right is None else F(left, right, operation)
    elif operation == "objects":
        child = _eval_ast(state, ast["arg"], value, trace, active, cache)
        result = None if child is None else OS(child, ast["mode"])
    elif operation == "select":
        result = PICK(_eval_ast(state, ast["arg"], value, trace, active, cache), ast["criterion"])
    elif operation == "transform-object":
        result = OT(_eval_ast(state, ast["arg"], value, trace, active, cache), ast["name"])
    elif operation == "recolor-object":
        child = _eval_ast(state, ast["arg"], value, trace, active, cache)
        result = None if child is None else tuple((ast["color"], r, c) for _, r, c in child)
    elif operation == "render-object":
        child = _eval_ast(state, ast["arg"], value, trace, active, cache)
        result = DRAW(value, child, ast["canvas"], ast["placement"], ast["iteration"])
    else:
        result = None
    if cache is not None:
        cache[cache_key] = result
    return result


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


def analyze(state: Mapping[str, Any], task: Mapping[str, Any]) -> dict[str, Any]:
    candidates = enumerate_asts(state, task)
    source_count = 1 + sum(1 for record in state["capabilities"].values()
                           if _grid_cap(record)
                           and record["repair"]["payload"].get("body", {}).get("op") == "generated-ast")
    raw_object_count = (source_count * len(OBJECT_MODES) * len(SELECTORS)
                        * (129 + 19 * len(_colors(task))))
    raw_count = len(enumerate_asts(state)) + raw_object_count
    counts: dict[int, int] = {}
    survivors: dict[int, list[dict[str, Any]]] = {}
    caches = [dict() for _ in task["train"]]
    for ast in candidates:
        n = size(ast)
        counts[n] = counts.get(n, 0) + 1
        try:
            passed = all(_eval_ast(state, ast, example["input"], [], (), cache) == G(example["output"])
                         for example, cache in zip(task["train"], caches))
        except Exception:
            passed = False
        if passed:
            survivors.setdefault(n, []).append(ast)
    minimum = min(survivors) if survivors else None
    winners = survivors.get(minimum, []) if minimum is not None else []
    return {"candidate_count": len(candidates), "raw_candidate_count": raw_count,
            "normalized_candidate_count": len(candidates),
            "candidate_count_by_size": {str(k): counts[k] for k in sorted(counts)},
            "complete_through_size": MAX_AST_SIZE, "minimum_size": minimum,
            "smaller_survivor_count": sum(len(v) for k, v in survivors.items()
                                          if minimum is not None and k < minimum),
            "minimum_survivors": winners, "minimum_survivor_count": len(winners)}


def any_solves(state: Mapping[str, Any], task: Mapping[str, Any]) -> bool:
    for rid in state["capabilities"]:
        try:
            if all(execute(state, rid, example["input"], []) == G(example["output"])
                   for example in tuple(task["train"]) + tuple(task["test"])):
                return True
        except Exception:
            pass
    return False
