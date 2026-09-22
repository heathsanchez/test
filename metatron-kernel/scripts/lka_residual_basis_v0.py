#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
from collections import Counter, defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable


EXPR_TAGS = {"bvar", "sort", "const", "app", "lam", "forallE", "letE"}
LEVEL_TAGS = {"zero", "succ", "max", "imax", "param"}
DECL_TAGS = {"axiom", "def", "thm", "inductive"}
META_KEYS = {"meta", "in", "il", "ie"}


def canonical(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"))


def digest(value: Any) -> str:
    return hashlib.sha256(canonical(value).encode()).hexdigest()


@dataclass(frozen=True)
class Case:
    number: int
    path: Path
    expected: int
    actual: int
    features: dict[str, Any]


def load_records(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for line_no, line in enumerate(path.read_text().splitlines(), 1):
        if not line.strip():
            continue
        value = json.loads(line)
        if not isinstance(value, dict):
            raise ValueError(f"{path}:{line_no}: expected object")
        rows.append(value)
    return rows


def run_checker(checker: Path, path: Path) -> int:
    with path.open("rb") as stream:
        return subprocess.run(
            [str(checker.resolve())],
            stdin=stream,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            check=False,
        ).returncode


def run_diagnostic_checker(checker: Path, path: Path) -> tuple[int, dict[str, int]]:
    env = dict(__import__("os").environ)
    env["METATRON_KERNEL_DIAGNOSTICS"] = "1"
    with path.open("rb") as stream:
        run = subprocess.run(
            [str(checker.resolve())],
            stdin=stream,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.PIPE,
            env=env,
            check=False,
            text=False,
        )
    text = run.stderr.decode(errors="replace").strip().splitlines()
    payload: dict[str, int] = {}
    for line in reversed(text):
        try:
            value = json.loads(line)
        except json.JSONDecodeError:
            continue
        if isinstance(value, dict) and all(
            isinstance(value.get(k), int)
            for k in ("declarations", "inductive_signatures", "type_judgments", "conversions")
        ):
            payload = {k: int(value[k]) for k in value}
            break
    if not payload:
        payload = {
            "declarations": -1,
            "inductive_signatures": -1,
            "type_judgments": -1,
            "conversions": -1,
        }
    return run.returncode, payload


def numbered_cases(root: Path, start: int, end: int) -> list[tuple[int, Path, int]]:
    out: list[tuple[int, Path, int]] = []
    for n in range(start, end + 1):
        matches = sorted(root.glob(f"*/{n:03d}_*.ndjson"))
        if len(matches) != 1:
            raise ValueError(f"case {n:03d}: expected one file, found {len(matches)}")
        path = matches[0]
        if path.parent.name == "good":
            expected = 0
        elif path.parent.name == "bad":
            expected = 1
        else:
            raise ValueError(path)
        out.append((n, path, expected))
    return out


def expr_tag(record: dict[str, Any]) -> str | None:
    if "ie" not in record:
        return None
    keys = [k for k in record if k != "ie"]
    if len(keys) == 1:
        return keys[0]
    return "multi:" + ",".join(sorted(keys))


def level_tag(record: dict[str, Any]) -> str | None:
    if "il" not in record:
        return None
    keys = [k for k in record if k != "il"]
    if len(keys) == 1:
        return keys[0]
    return "multi:" + ",".join(sorted(keys))


def expr_refs(records: list[dict[str, Any]]) -> dict[int, dict[str, Any]]:
    table: dict[int, dict[str, Any]] = {}
    for row in records:
        if isinstance(row.get("ie"), int):
            table[int(row["ie"])] = row
    return table


def level_refs(records: list[dict[str, Any]]) -> dict[int, dict[str, Any]]:
    table: dict[int, dict[str, Any]] = {}
    for row in records:
        if isinstance(row.get("il"), int):
            table[int(row["il"])] = row
    return table


def name_depths(records: list[dict[str, Any]]) -> Counter[int]:
    parents: dict[int, int | None] = {0: None}
    for row in records:
        if not isinstance(row.get("in"), int):
            continue
        idx = int(row["in"])
        if isinstance(row.get("str"), dict):
            pre = row["str"].get("pre")
            parents[idx] = int(pre) if isinstance(pre, int) else None
        elif isinstance(row.get("num"), dict):
            pre = row["num"].get("pre")
            parents[idx] = int(pre) if isinstance(pre, int) else None

    depths: Counter[int] = Counter()
    for idx in parents:
        seen: set[int] = set()
        cur: int | None = idx
        depth = 0
        while cur is not None and cur != 0 and cur not in seen:
            seen.add(cur)
            cur = parents.get(cur)
            depth += 1
        depths[depth] += 1
    return depths


def expr_outer(table: dict[int, dict[str, Any]], eid: int) -> str:
    row = table.get(eid, {})
    tag = expr_tag(row)
    return tag or "missing"


def level_shape(levels: dict[int, dict[str, Any]], lid: int, depth: int = 0) -> str:
    if depth > 12:
        return "deep"
    row = levels.get(lid)
    if row is None:
        return "missing"
    tag = level_tag(row)
    if tag == "param":
        return "param"
    if tag == "zero":
        return "zero"
    if tag == "succ":
        child = row.get("succ")
        return f"succ({level_shape(levels, int(child), depth + 1)})" if isinstance(child, int) else "succ(?)"
    if tag in {"max", "imax"}:
        body = row.get(tag)
        if isinstance(body, dict):
            a, b = body.get("a"), body.get("b")
            if isinstance(a, int) and isinstance(b, int):
                return f"{tag}({level_shape(levels,a,depth+1)},{level_shape(levels,b,depth+1)})"
        return f"{tag}(?)"
    return tag or "unknown"


def pi_domains(exprs: dict[int, dict[str, Any]], start: int, limit: int = 64) -> tuple[list[int], int]:
    domains: list[int] = []
    current = start
    for _ in range(limit):
        row = exprs.get(current)
        if row is None or "forallE" not in row or not isinstance(row["forallE"], dict):
            return domains, current
        node = row["forallE"]
        domain, body = node.get("type"), node.get("body")
        if not isinstance(domain, int) or not isinstance(body, int):
            return domains, current
        domains.append(domain)
        current = body
    return domains, current


def app_spine(exprs: dict[int, dict[str, Any]], start: int, limit: int = 128) -> tuple[int, list[int]]:
    args: list[int] = []
    current = start
    for _ in range(limit):
        row = exprs.get(current)
        if row is None or "app" not in row or not isinstance(row["app"], dict):
            break
        node = row["app"]
        fun, arg = node.get("fn"), node.get("arg")
        if not isinstance(fun, int) or not isinstance(arg, int):
            break
        args.append(arg)
        current = fun
    args.reverse()
    return current, args


def contains_const(exprs: dict[int, dict[str, Any]], start: int, target: int, limit: int = 4096) -> bool:
    stack = [start]
    seen: set[int] = set()
    while stack and len(seen) < limit:
        eid = stack.pop()
        if eid in seen:
            continue
        seen.add(eid)
        row = exprs.get(eid, {})
        if isinstance(row.get("const"), dict) and row["const"].get("name") == target:
            return True
        for key in ("app", "lam", "forallE", "letE"):
            node = row.get(key)
            if not isinstance(node, dict):
                continue
            for field in ("fn", "arg", "type", "body", "value"):
                value = node.get(field)
                if isinstance(value, int):
                    stack.append(value)
    return False


def negative_self_occurrence(exprs: dict[int, dict[str, Any]], start: int, target: int) -> bool:
    stack = [(start, True)]
    seen: set[tuple[int, bool]] = set()
    while stack:
        eid, positive = stack.pop()
        if (eid, positive) in seen:
            continue
        seen.add((eid, positive))
        row = exprs.get(eid, {})
        const = row.get("const")
        if isinstance(const, dict) and const.get("name") == target and not positive:
            return True
        app = row.get("app")
        if isinstance(app, dict):
            for field in ("fn", "arg"):
                v = app.get(field)
                if isinstance(v, int):
                    stack.append((v, positive))
        pi = row.get("forallE")
        if isinstance(pi, dict):
            d, b = pi.get("type"), pi.get("body")
            if isinstance(d, int):
                stack.append((d, not positive))
            if isinstance(b, int):
                stack.append((b, positive))
        for key in ("lam", "letE"):
            node = row.get(key)
            if not isinstance(node, dict):
                continue
            for field in ("type", "body", "value"):
                v = node.get(field)
                if isinstance(v, int):
                    stack.append((v, positive))
    return False


def aggregate_inductive_features(
    records: list[dict[str, Any]],
    exprs: dict[int, dict[str, Any]],
    levels: dict[int, dict[str, Any]],
) -> dict[str, Any]:
    blocks = [row["inductive"] for row in records if isinstance(row.get("inductive"), dict)]
    if not blocks:
        return {"has_inductive": False}

    all_types: list[dict[str, Any]] = []
    all_ctors: list[dict[str, Any]] = []
    all_recs: list[dict[str, Any]] = []
    for b in blocks:
        all_types.extend(x for x in b.get("types", []) if isinstance(x, dict))
        all_ctors.extend(x for x in b.get("ctors", []) if isinstance(x, dict))
        all_recs.extend(x for x in b.get("recs", []) if isinstance(x, dict))

    type_names = {int(t["name"]) for t in all_types if isinstance(t.get("name"), int)}
    ctor_field_sort_shapes: list[str] = []
    ctor_field_outer_tags: list[str] = []
    ctor_negative_self = False
    ctor_self_any = False
    ctor_result_head_self = 0
    ctor_result_arg_counts: list[int] = []

    for c in all_ctors:
        ty = c.get("type")
        owner = c.get("induct")
        if not isinstance(ty, int):
            continue
        domains, result = pi_domains(exprs, ty)
        num_params = int(c.get("numParams", 0))
        num_fields = int(c.get("numFields", 0))
        field_domains = domains[num_params:num_params + num_fields]
        for field in field_domains:
            ctor_field_outer_tags.append(expr_outer(exprs, field))
            row = exprs.get(field, {})
            if isinstance(row.get("sort"), int):
                ctor_field_sort_shapes.append(level_shape(levels, int(row["sort"])))
            if isinstance(owner, int):
                ctor_negative_self = ctor_negative_self or negative_self_occurrence(exprs, field, owner)
                ctor_self_any = ctor_self_any or contains_const(exprs, field, owner)

        if isinstance(owner, int):
            head, args = app_spine(exprs, result)
            hrow = exprs.get(head, {})
            const = hrow.get("const")
            if isinstance(const, dict) and const.get("name") == owner:
                ctor_result_head_self += 1
                ctor_result_arg_counts.append(len(args))

    rec_rule_fields: list[int] = []
    for r in all_recs:
        for rule in r.get("rules", []) if isinstance(r.get("rules"), list) else []:
            if isinstance(rule, dict):
                rec_rule_fields.append(int(rule.get("nfields", 0)))

    type_result_outer: list[str] = []
    type_result_sort_shapes: list[str] = []
    for t in all_types:
        ty = t.get("type")
        if not isinstance(ty, int):
            continue
        binders = int(t.get("numParams", 0)) + int(t.get("numIndices", 0))
        domains, result = pi_domains(exprs, ty)
        if len(domains) >= binders:
            row = exprs.get(result, {})
            type_result_outer.append(expr_outer(exprs, result))
            if isinstance(row.get("sort"), int):
                type_result_sort_shapes.append(level_shape(levels, int(row["sort"])))

    return {
        "has_inductive": True,
        "inductive_block_count": len(blocks),
        "type_count": len(all_types),
        "ctor_count": len(all_ctors),
        "recursor_count": len(all_recs),
        "type_num_params": sorted(int(t.get("numParams", 0)) for t in all_types),
        "type_num_indices": sorted(int(t.get("numIndices", 0)) for t in all_types),
        "type_num_nested": sorted(int(t.get("numNested", 0)) for t in all_types),
        "type_recursive": sorted(bool(t.get("isRec")) for t in all_types),
        "type_reflexive": sorted(bool(t.get("isReflexive")) for t in all_types),
        "type_unsafe": sorted(bool(t.get("isUnsafe")) for t in all_types),
        "type_level_arity": sorted(len(t.get("levelParams", [])) for t in all_types),
        "type_result_outer": sorted(type_result_outer),
        "type_result_sort_shapes": sorted(type_result_sort_shapes),
        "ctor_num_params": sorted(int(c.get("numParams", 0)) for c in all_ctors),
        "ctor_num_fields": sorted(int(c.get("numFields", 0)) for c in all_ctors),
        "ctor_level_arity": sorted(len(c.get("levelParams", [])) for c in all_ctors),
        "ctor_unsafe": sorted(bool(c.get("isUnsafe")) for c in all_ctors),
        "ctor_field_outer_tags": sorted(ctor_field_outer_tags),
        "ctor_field_sort_shapes": sorted(ctor_field_sort_shapes),
        "ctor_negative_self": ctor_negative_self,
        "ctor_self_any": ctor_self_any,
        "ctor_result_head_self_count": ctor_result_head_self,
        "ctor_result_arg_counts": sorted(ctor_result_arg_counts),
        "rec_num_params": sorted(int(r.get("numParams", 0)) for r in all_recs),
        "rec_num_indices": sorted(int(r.get("numIndices", 0)) for r in all_recs),
        "rec_num_motives": sorted(int(r.get("numMotives", 0)) for r in all_recs),
        "rec_num_minors": sorted(int(r.get("numMinors", 0)) for r in all_recs),
        "rec_k": sorted(bool(r.get("k")) for r in all_recs),
        "rec_level_arity": sorted(len(r.get("levelParams", [])) for r in all_recs),
        "rec_unsafe": sorted(bool(r.get("isUnsafe")) for r in all_recs),
        "rec_rule_count": sorted(
            len(r.get("rules", [])) if isinstance(r.get("rules"), list) else 0 for r in all_recs
        ),
        "rec_rule_fields": sorted(rec_rule_fields),
        "distinct_type_name_count": len(type_names),
    }



def collect_bvars(exprs: dict[int, dict[str, Any]], start: int, limit: int = 4096) -> set[int]:
    stack = [start]
    seen: set[int] = set()
    out: set[int] = set()
    while stack and len(seen) < limit:
        eid = stack.pop()
        if eid in seen:
            continue
        seen.add(eid)
        row = exprs.get(eid, {})
        if isinstance(row.get("bvar"), int):
            out.add(int(row["bvar"]))
        for key in ("app", "lam", "forallE", "letE"):
            node = row.get(key)
            if not isinstance(node, dict):
                continue
            for field in ("fn", "arg", "type", "body", "value"):
                value = node.get(field)
                if isinstance(value, int):
                    stack.append(value)
    return out


def expr_fingerprint(exprs: dict[int, dict[str, Any]], eid: int, depth: int = 0) -> Any:
    if depth > 64:
        return ("deep",)
    row = exprs.get(eid, {})
    if "bvar" in row:
        return ("bvar", row["bvar"])
    if "sort" in row:
        return ("sort", row["sort"])
    if isinstance(row.get("const"), dict):
        return ("const", row["const"].get("name"), tuple(row["const"].get("us", [])))
    if isinstance(row.get("app"), dict):
        return ("app",
            expr_fingerprint(exprs, int(row["app"]["fn"]), depth + 1),
            expr_fingerprint(exprs, int(row["app"]["arg"]), depth + 1))
    for key in ("lam", "forallE"):
        node = row.get(key)
        if isinstance(node, dict) and isinstance(node.get("type"), int) and isinstance(node.get("body"), int):
            return (key,
                expr_fingerprint(exprs, int(node["type"]), depth + 1),
                expr_fingerprint(exprs, int(node["body"]), depth + 1))
    node = row.get("letE")
    if isinstance(node, dict):
        vals=[]
        for field in ("type","value","body"):
            v=node.get(field)
            vals.append(expr_fingerprint(exprs,int(v),depth+1) if isinstance(v,int) else None)
        return ("letE",*vals)
    if isinstance(row.get("proj"), dict):
        p=row["proj"]
        return ("proj",p.get("typeName"),p.get("idx"),
            expr_fingerprint(exprs,int(p["struct"]),depth+1) if isinstance(p.get("struct"),int) else None)
    if "natVal" in row:
        return ("natVal",row["natVal"])
    return ("unknown", tuple(sorted(k for k in row if k != "ie")))


def level_is_zero(
    levels: dict[int, dict[str, Any]],
    lid: int,
    subst: dict[int, int],
    depth: int = 0,
) -> bool | None:
    if depth > 32:
        return None
    # lean4export reserves level index 0 for Level.zero and does not need an
    # explicit IL record for it.
    if lid == 0:
        return True
    row = levels.get(lid)
    if row is None:
        return None
    tag = level_tag(row)
    if tag == "zero":
        return True
    if tag == "succ":
        return False
    if tag == "param":
        name = row.get("param")
        if isinstance(name, int) and name in subst:
            return level_is_zero(levels, subst[name], subst, depth + 1)
        return None
    if tag == "max":
        body = row.get("max")
        if isinstance(body, list) and len(body) == 2 and all(isinstance(x, int) for x in body):
            a = level_is_zero(levels, int(body[0]), subst, depth + 1)
            b = level_is_zero(levels, int(body[1]), subst, depth + 1)
            if a is None or b is None:
                return None
            return a and b
        if isinstance(body, dict):
            a, b = body.get("a"), body.get("b")
            if isinstance(a, int) and isinstance(b, int):
                za = level_is_zero(levels, a, subst, depth + 1)
                zb = level_is_zero(levels, b, subst, depth + 1)
                if za is None or zb is None:
                    return None
                return za and zb
    if tag == "imax":
        body = row.get("imax")
        if isinstance(body, list) and len(body) == 2 and all(isinstance(x, int) for x in body):
            return level_is_zero(levels, int(body[1]), subst, depth + 1)
        if isinstance(body, dict) and isinstance(body.get("b"), int):
            return level_is_zero(levels, int(body["b"]), subst, depth + 1)
    return None


def level_term(
    levels: dict[int, dict[str, Any]],
    lid: int,
    depth: int = 0,
) -> tuple[Any, ...] | None:
    if depth > 32:
        return None
    if lid == 0:
        return ("zero",)
    row = levels.get(lid)
    if row is None:
        return None
    tag = level_tag(row)
    if tag == "param":
        name = row.get("param")
        return ("param", int(name)) if isinstance(name, int) else None
    if tag == "succ":
        child = row.get("succ")
        if not isinstance(child, int):
            return None
        term = level_term(levels, child, depth + 1)
        return ("succ", term) if term is not None else None
    if tag in {"max", "imax"}:
        node = row.get(tag)
        if isinstance(node, list) and len(node) == 2:
            left, right = node
        elif isinstance(node, dict):
            left, right = node.get("a"), node.get("b")
        else:
            return None
        if not isinstance(left, int) or not isinstance(right, int):
            return None
        a = level_term(levels, left, depth + 1)
        b = level_term(levels, right, depth + 1)
        if a is None or b is None:
            return None
        return (tag, a, b)
    if tag == "zero":
        return ("zero",)
    return None


def level_leq_term(left: tuple[Any, ...], right: tuple[Any, ...]) -> bool | None:
    if left == right:
        return True
    if left == ("zero",):
        return True
    if right and right[0] == "succ":
        inner = right[1]
        if left == inner:
            return True
        return level_leq_term(left, inner)
    if right and right[0] in {"max", "imax"}:
        a = level_leq_term(left, right[1])
        b = level_leq_term(left, right[2])
        if a is True or b is True:
            return True
        if a is False and b is False:
            return False
    if left and left[0] == "succ" and right and right[0] == "succ":
        return level_leq_term(left[1], right[1])
    if left and left[0] == "param" and right and right[0] == "param":
        return left == right
    return None


def level_lt_term(left: tuple[Any, ...], right: tuple[Any, ...]) -> bool | None:
    if left == right:
        return False
    if right and right[0] == "succ":
        # u < succ v iff u <= v for the conservative symbolic cases handled here.
        return level_leq_term(left, right[1])
    if right and right[0] in {"max", "imax"}:
        a = level_lt_term(left, right[1])
        b = level_lt_term(left, right[2])
        if a is True or b is True:
            return True
    if left == ("zero",):
        z = level_is_zero_term(right)
        return None if z is None else not z
    return None


def level_is_zero_term(term: tuple[Any, ...]) -> bool | None:
    if term == ("zero",):
        return True
    if term and term[0] == "succ":
        return False
    if term and term[0] == "max":
        a = level_is_zero_term(term[1])
        b = level_is_zero_term(term[2])
        if a is None or b is None:
            return None
        return a and b
    if term and term[0] == "imax":
        return level_is_zero_term(term[2])
    return None


def field_universe_admissibility(
    records: list[dict[str, Any]],
    exprs: dict[int, dict[str, Any]],
    levels: dict[int, dict[str, Any]],
) -> str:
    blocks = [row["inductive"] for row in records if isinstance(row.get("inductive"), dict)]
    if not blocks:
        return "not_applicable"

    saw_direct_sort_field = False
    saw_unknown = False

    for block in blocks:
        types = {
            int(t["name"]): t
            for t in block.get("types", [])
            if isinstance(t, dict) and isinstance(t.get("name"), int)
        }
        for ctor in block.get("ctors", []):
            if not isinstance(ctor, dict):
                continue
            owner = ctor.get("induct")
            ty = ctor.get("type")
            if not isinstance(owner, int) or not isinstance(ty, int) or owner not in types:
                continue
            ind = types[owner]
            ind_ty = ind.get("type")
            if not isinstance(ind_ty, int):
                saw_unknown = True
                continue

            ind_binders = int(ind.get("numParams", 0)) + int(ind.get("numIndices", 0))
            ind_domains, ind_result = pi_domains(exprs, ind_ty)
            if len(ind_domains) < ind_binders:
                saw_unknown = True
                continue
            ind_row = exprs.get(ind_result, {})
            ind_lid = ind_row.get("sort")
            if not isinstance(ind_lid, int):
                saw_unknown = True
                continue
            ind_level = level_term(levels, ind_lid)
            if ind_level is None:
                saw_unknown = True
                continue

            domains, _result = pi_domains(exprs, ty)
            nparams = int(ctor.get("numParams", 0))
            nfields = int(ctor.get("numFields", 0))
            if len(domains) < nparams + nfields:
                saw_unknown = True
                continue

            prop_result = level_is_zero_term(ind_level) is True
            for field in domains[nparams:nparams + nfields]:
                row = exprs.get(field, {})
                field_lid = row.get("sort")
                if not isinstance(field_lid, int):
                    # This probe deliberately handles only fields whose domain is
                    # itself a Sort. Other field types belong to later semantic
                    # obligations and remain UNKNOWN here.
                    continue
                saw_direct_sort_field = True

                # Lean's Prop is impredicative: a constructor field may itself
                # range over an arbitrary universe.
                if prop_result:
                    continue

                field_level = level_term(levels, field_lid)
                if field_level is None:
                    saw_unknown = True
                    continue
                admissible = level_lt_term(field_level, ind_level)
                if admissible is False:
                    return "refuted"
                if admissible is None:
                    saw_unknown = True

    if saw_unknown:
        return "unknown"
    if saw_direct_sort_field:
        return "proven"
    return "not_applicable"


def peel_lambda_final_bvar(
    exprs: dict[int, dict[str, Any]],
    start: int,
    limit: int = 32,
) -> tuple[int, int | None]:
    current = start
    depth = 0
    for _ in range(limit):
        row = exprs.get(current, {})
        node = row.get("lam")
        if not isinstance(node, dict) or not isinstance(node.get("body"), int):
            bvar = row.get("bvar")
            return depth, int(bvar) if isinstance(bvar, int) else None
        depth += 1
        current = int(node["body"])
    return depth, None


def identity_like_definition_names(
    records: list[dict[str, Any]],
    exprs: dict[int, dict[str, Any]],
) -> set[int]:
    names: set[int] = set()
    for row in records:
        d = row.get("def")
        if not isinstance(d, dict):
            continue
        name, value = d.get("name"), d.get("value")
        if not isinstance(name, int) or not isinstance(value, int):
            continue
        depth, final_bvar = peel_lambda_final_bvar(exprs, value)
        # Any lambda tower that returns its most recently introduced argument
        # is observationally identity-like for a fully applied final argument.
        if depth > 0 and final_bvar == 0:
            names.add(int(name))
    return names


def expression_whnf_prop_status(
    records: list[dict[str, Any]],
    exprs: dict[int, dict[str, Any]],
    levels: dict[int, dict[str, Any]],
    expression: int,
    identity_like: set[int],
    depth: int = 0,
) -> str:
    if depth > 16:
        return "unknown"
    row = exprs.get(expression, {})
    lid = row.get("sort")
    if isinstance(lid, int):
        zero = level_is_zero(levels, lid, {})
        if zero is True:
            return "prop"
        if zero is False:
            return "nonprop"
        return "unknown"

    head, args = app_spine(exprs, expression)
    hrow = exprs.get(head, {})
    const = hrow.get("const")
    if (
        isinstance(const, dict)
        and isinstance(const.get("name"), int)
        and int(const["name"]) in identity_like
        and args
    ):
        return expression_whnf_prop_status(
            records, exprs, levels, args[-1], identity_like, depth + 1
        )

    node = row.get("letE")
    if isinstance(node, dict) and isinstance(node.get("body"), int):
        return expression_whnf_prop_status(
            records, exprs, levels, int(node["body"]), identity_like, depth + 1
        )
    return "unknown"


def semantic_probe_features(records: list[dict[str, Any]]) -> dict[str, Any]:
    exprs = expr_refs(records)
    levels = level_refs(records)
    blocks = [row["inductive"] for row in records if isinstance(row.get("inductive"), dict)]

    type_by_name: dict[int, dict[str, Any]] = {}
    ctor_by_owner: dict[int, list[dict[str, Any]]] = defaultdict(list)
    ctor_owner_by_name: dict[int, int] = {}
    recursor_by_name: dict[int, tuple[int, dict[str, Any]]] = {}
    k_recursor_owner: dict[int, int] = {}
    for block in blocks:
        types = [x for x in block.get("types", []) if isinstance(x, dict)]
        ctors = [x for x in block.get("ctors", []) if isinstance(x, dict)]
        recs = [x for x in block.get("recs", []) if isinstance(x, dict)]
        for t in types:
            if isinstance(t.get("name"), int):
                type_by_name[int(t["name"])] = t
        for ctor in ctors:
            if isinstance(ctor.get("induct"), int):
                owner = int(ctor["induct"])
                ctor_by_owner[owner].append(ctor)
                if isinstance(ctor.get("name"), int):
                    ctor_owner_by_name[int(ctor["name"])] = owner
        for rec in recs:
            if isinstance(rec.get("name"), int):
                all_types = rec.get("all")
                if isinstance(all_types, list) and len(all_types) == 1 and isinstance(all_types[0], int):
                    owner = int(all_types[0])
                    recursor_by_name[int(rec["name"])] = (owner, rec)
                    if bool(rec.get("k")):
                        k_recursor_owner[int(rec["name"])] = owner

    def result_sort_is_prop(
        type_name: int,
        const_levels: list[int],
        ambient_subst: dict[int, int] | None = None,
    ) -> bool | None:
        t = type_by_name.get(type_name)
        if t is None or not isinstance(t.get("type"), int):
            return None
        binders = int(t.get("numParams", 0)) + int(t.get("numIndices", 0))
        domains, result = pi_domains(exprs, int(t["type"]))
        if len(domains) < binders:
            return None
        row = exprs.get(result, {})
        lid = row.get("sort")
        if not isinstance(lid, int):
            return None
        lparams = t.get("levelParams", [])
        if not isinstance(lparams, list) or len(lparams) != len(const_levels):
            return None
        subst = dict(ambient_subst or {})
        subst.update({
            int(name): int(actual)
            for name, actual in zip(lparams, const_levels)
            if isinstance(name, int) and isinstance(actual, int)
        })
        return level_is_zero(levels, lid, subst)

    def field_sort_is_prop(
        field: int,
        universe_instance: list[int],
        owner_level_params: list[int],
    ) -> bool | None:
        head, _args = app_spine(exprs, field)
        row = exprs.get(head, {})
        const = row.get("const")
        if isinstance(const, dict) and isinstance(const.get("name"), int):
            us = const.get("us", [])
            if isinstance(us, list):
                ambient = {
                    int(name): int(actual)
                    for name, actual in zip(owner_level_params, universe_instance)
                    if isinstance(name, int) and isinstance(actual, int)
                }
                return result_sort_is_prop(
                    int(const["name"]),
                    [int(x) for x in us if isinstance(x, int)],
                    ambient,
                )
        # A field directly declared as a proposition expression is itself a type
        # whose head inductive result sort should have been handled above.
        return None

    projection_results: list[str] = []
    projection_target_prop: list[str] = []
    projection_barrier: list[str] = []

    proj_rows = [
        (eid, row["proj"])
        for eid, row in exprs.items()
        if isinstance(row.get("proj"), dict)
    ]
    for _eid, proj in proj_rows:
        type_name = proj.get("typeName")
        idx = proj.get("idx")
        if not isinstance(type_name, int) or not isinstance(idx, int):
            projection_results.append("unknown")
            projection_target_prop.append("unknown")
            projection_barrier.append("unknown")
            continue
        t = type_by_name.get(type_name)
        ctors = ctor_by_owner.get(type_name, [])
        if t is None:
            projection_results.append("unknown")
            projection_target_prop.append("unknown")
            projection_barrier.append("unknown")
            continue
        if len(ctors) != 1:
            projection_results.append("deny")
            projection_target_prop.append("unknown")
            projection_barrier.append("unknown")
            continue
        ctor = ctors[0]
        if not isinstance(ctor.get("type"), int):
            projection_results.append("unknown")
            projection_target_prop.append("unknown")
            projection_barrier.append("unknown")
            continue

        # Recover a concrete universe instance from any occurrence of the
        # projected structure type in this export. Prefer fully concrete levels.
        instances: list[list[int]] = []
        for row in exprs.values():
            const = row.get("const")
            if isinstance(const, dict) and const.get("name") == type_name and isinstance(const.get("us"), list):
                us = [int(x) for x in const["us"] if isinstance(x, int)]
                if len(us) == len(t.get("levelParams", [])):
                    instances.append(us)
        instance = None
        for us in instances:
            if all(level_is_zero(levels, u, {}) is not None for u in us):
                instance = us
                break
        if instance is None and instances:
            instance = instances[0]
        if instance is None:
            projection_results.append("unknown")
            projection_target_prop.append("unknown")
            projection_barrier.append("unknown")
            continue

        domains, _result = pi_domains(exprs, int(ctor["type"]))
        nparams = int(ctor.get("numParams", 0))
        nfields = int(ctor.get("numFields", 0))
        fields = domains[nparams:nparams + nfields]
        if idx < 0 or idx >= len(fields):
            projection_results.append("deny")
            projection_target_prop.append("unknown")
            projection_barrier.append("unknown")
            continue

        owner_level_params = [
            int(x) for x in t.get("levelParams", []) if isinstance(x, int)
        ]
        field_is_prop = [
            field_sort_is_prop(field, instance, owner_level_params)
            for field in fields
        ]
        deps: list[set[int]] = []
        for j, field in enumerate(fields):
            refs = collect_bvars(exprs, field)
            dep = {
                j - 1 - b
                for b in refs
                if 0 <= b < j
            }
            deps.append(dep)

        target_prop = field_is_prop[idx]
        barrier = False
        barrier_unknown = False
        for later in range(0, idx + 1):
            for earlier in deps[later]:
                if earlier < 0 or earlier >= len(field_is_prop):
                    continue
                prop = field_is_prop[earlier]
                if prop is False:
                    barrier = True
                elif prop is None:
                    barrier_unknown = True
        if target_prop is True and not barrier and not barrier_unknown:
            allowed = "allow"
        elif target_prop is False or barrier:
            allowed = "deny"
        else:
            allowed = "unknown"
        projection_results.append(allowed)
        projection_target_prop.append(
            "prop" if target_prop is True else "data" if target_prop is False else "unknown"
        )
        projection_barrier.append(
            "barrier" if barrier else "unknown" if barrier_unknown else "clear"
        )

    projection_source_by_eid: dict[int, str] = {}
    recursor_reduction_results: list[str] = []

    def owner_is_unit_like(owner: int) -> bool:
        t = type_by_name.get(owner)
        ctors = ctor_by_owner.get(owner, [])
        if t is None or len(ctors) != 1:
            return False
        ctor = ctors[0]
        return (
            int(t.get("numIndices", 0)) == 0
            and int(t.get("numNested", 0)) == 0
            and not bool(t.get("isRec"))
            and not bool(t.get("isReflexive"))
            and int(ctor.get("numFields", 0)) == 0
        )

    # Rule-K probe: when a k-enabled recursor is fully applied to a bound major
    # premise whose owner-inductive application has two final endpoint
    # arguments, record whether those endpoints are structurally identical.
    # This is a discovery witness only; any admitted kernel law must replace
    # structural identity by definitional equality.
    rule_k_reflexive: list[str] = []

    roots: list[int] = []
    declaration_types: list[int] = []
    for row in records:
        for tag in ("def", "thm", "axiom"):
            d = row.get(tag)
            if isinstance(d, dict):
                ty = d.get("type")
                if isinstance(ty, int):
                    declaration_types.append(ty)
                for field in ("type", "value"):
                    v = d.get(field)
                    if isinstance(v, int):
                        roots.append(v)

    seen_ctx: set[tuple[int, tuple[int, ...]]] = set()
    def walk(eid: int, ctx: tuple[int, ...]) -> None:
        key = (eid, ctx)
        if key in seen_ctx:
            return
        seen_ctx.add(key)
        row = exprs.get(eid, {})

        proj = row.get("proj")
        if isinstance(proj, dict) and isinstance(proj.get("typeName"), int):
            type_name = int(proj["typeName"])
            struct = proj.get("struct")
            source = "unknown"
            if isinstance(struct, int):
                srow = exprs.get(struct, {})
                bvar = srow.get("bvar")
                if isinstance(bvar, int) and bvar < len(ctx):
                    source_ty = ctx[bvar]
                    shead, _sargs = app_spine(exprs, source_ty)
                    shrow = exprs.get(shead, {})
                    sconst = shrow.get("const")
                    if isinstance(sconst, dict) and isinstance(sconst.get("name"), int):
                        source = (
                            "match"
                            if int(sconst["name"]) == type_name
                            else "mismatch"
                        )
                else:
                    shead, _sargs = app_spine(exprs, struct)
                    shrow = exprs.get(shead, {})
                    sconst = shrow.get("const")
                    if isinstance(sconst, dict) and isinstance(sconst.get("name"), int):
                        head_name = int(sconst["name"])
                        owner = ctor_owner_by_name.get(head_name)
                        if owner is not None:
                            source = "match" if owner == type_name else "mismatch"
            projection_source_by_eid[eid] = source

        head, args = app_spine(exprs, eid)
        hrow = exprs.get(head, {})
        const = hrow.get("const")
        if isinstance(const, dict) and isinstance(const.get("name"), int):
            rec_info = recursor_by_name.get(int(const["name"]))
            if rec_info is not None:
                owner, rec = rec_info
                required = (
                    int(rec.get("numParams", 0))
                    + int(rec.get("numMotives", 0))
                    + int(rec.get("numMinors", 0))
                    + int(rec.get("numIndices", 0))
                    + 1
                )
                if len(args) >= required:
                    major = args[-1]
                    mhead, _margs = app_spine(exprs, major)
                    mhrow = exprs.get(mhead, {})
                    mconst = mhrow.get("const")
                    ctor_owner = (
                        ctor_owner_by_name.get(int(mconst["name"]))
                        if isinstance(mconst, dict) and isinstance(mconst.get("name"), int)
                        else None
                    )
                    if ctor_owner == owner:
                        recursor_reduction_results.append("allow")
                    else:
                        mrow = exprs.get(major, {})
                        if isinstance(mrow.get("bvar"), int):
                            if owner_is_unit_like(owner):
                                recursor_reduction_results.append("allow")
                            elif bool(rec.get("k")):
                                # Rule-K on a non-constructor major is a separate
                                # low-bandwidth law already probed below.
                                recursor_reduction_results.append("unknown")
                            else:
                                recursor_reduction_results.append("deny")
                        else:
                            recursor_reduction_results.append("unknown")

            owner = k_recursor_owner.get(int(const["name"]))
            if owner is not None and args:
                major = args[-1]
                mrow = exprs.get(major, {})
                bvar = mrow.get("bvar")
                if isinstance(bvar, int) and bvar < len(ctx):
                    major_ty = ctx[bvar]
                    mhead, margs = app_spine(exprs, major_ty)
                    mhrow = exprs.get(mhead, {})
                    mconst = mhrow.get("const")
                    if isinstance(mconst, dict) and mconst.get("name") == owner and len(margs) >= 2:
                        left, right = margs[-2], margs[-1]
                        same = expr_fingerprint(exprs, left) == expr_fingerprint(exprs, right)
                        rule_k_reflexive.append("reflexive" if same else "nonreflexive")

        node = row.get("forallE")
        if isinstance(node, dict):
            ty, body = node.get("type"), node.get("body")
            if isinstance(ty, int):
                walk(ty, ctx)
            if isinstance(body, int) and isinstance(ty, int):
                walk(body, (ty,) + ctx)
            return
        node = row.get("lam")
        if isinstance(node, dict):
            ty, body = node.get("type"), node.get("body")
            if isinstance(ty, int):
                walk(ty, ctx)
            if isinstance(body, int) and isinstance(ty, int):
                walk(body, (ty,) + ctx)
            return
        node = row.get("letE")
        if isinstance(node, dict):
            ty, val, body = node.get("type"), node.get("value"), node.get("body")
            if isinstance(ty, int):
                walk(ty, ctx)
            if isinstance(val, int):
                walk(val, ctx)
            if isinstance(body, int) and isinstance(ty, int):
                walk(body, (ty,) + ctx)
            return
        node = row.get("app")
        if isinstance(node, dict):
            for field in ("fn", "arg"):
                v = node.get(field)
                if isinstance(v, int):
                    walk(v, ctx)
        node = row.get("proj")
        if isinstance(node, dict) and isinstance(node.get("struct"), int):
            walk(int(node["struct"]), ctx)

    for root in roots:
        walk(root, ())

    eta_results: list[str] = []
    proof_irrelevance_results: list[str] = []
    equality_owners = set(k_recursor_owner.values())
    identity_like = identity_like_definition_names(records, exprs)

    def constructor_owner(expression: int) -> int | None:
        head, _args = app_spine(exprs, expression)
        row = exprs.get(head, {})
        const = row.get("const")
        if isinstance(const, dict) and isinstance(const.get("name"), int):
            return ctor_owner_by_name.get(int(const["name"]))
        return None

    def is_bvar_expr(expression: int) -> bool:
        return isinstance(exprs.get(expression, {}).get("bvar"), int)

    for ty in declaration_types:
        context: tuple[int, ...] = ()
        result = ty
        for _ in range(128):
            row = exprs.get(result, {})
            node = row.get("forallE")
            if not isinstance(node, dict):
                break
            domain, body = node.get("type"), node.get("body")
            if not isinstance(domain, int) or not isinstance(body, int):
                break
            context = (int(domain),) + context
            result = int(body)

        head, args = app_spine(exprs, result)
        hrow = exprs.get(head, {})
        hconst = hrow.get("const")
        if (
            not isinstance(hconst, dict)
            or not isinstance(hconst.get("name"), int)
            or int(hconst["name"]) not in equality_owners
            or len(args) < 3
        ):
            continue

        carrier, left, right = args[-3], args[-2], args[-1]

        carrier_row = exprs.get(carrier, {})
        carrier_bvar = carrier_row.get("bvar")
        if isinstance(carrier_bvar, int) and carrier_bvar < len(context):
            binder_type = context[int(carrier_bvar)]
            prop_status = expression_whnf_prop_status(
                records, exprs, levels, binder_type, identity_like
            )
            if prop_status == "prop":
                proof_irrelevance_results.append("allow")
            elif prop_status == "nonprop":
                proof_irrelevance_results.append("deny")
            else:
                proof_irrelevance_results.append("unknown")

        carrier_head, _carrier_args = app_spine(exprs, carrier)
        crow = exprs.get(carrier_head, {})
        cconst = crow.get("const")
        if not isinstance(cconst, dict) or not isinstance(cconst.get("name"), int):
            continue
        owner = int(cconst["name"])
        t = type_by_name.get(owner)
        ctors = ctor_by_owner.get(owner, [])
        if t is None:
            continue

        left_ctor = constructor_owner(left)
        right_ctor = constructor_owner(right)
        eta_shape = (
            (is_bvar_expr(left) and is_bvar_expr(right))
            or (is_bvar_expr(left) and right_ctor == owner)
            or (is_bvar_expr(right) and left_ctor == owner)
        )
        if not eta_shape:
            continue

        if (
            len(ctors) == 1
            and int(t.get("numIndices", 0)) == 0
            and int(t.get("numNested", 0)) == 0
            and not bool(t.get("isRec"))
            and not bool(t.get("isReflexive"))
        ):
            eta_results.append("allow")
        else:
            eta_results.append("deny")

    if not proof_irrelevance_results:
        proof_irrelevance_scalar = "not_applicable"
    elif any(result == "deny" for result in proof_irrelevance_results):
        proof_irrelevance_scalar = "deny"
    elif any(result == "unknown" for result in proof_irrelevance_results):
        proof_irrelevance_scalar = "unknown"
    else:
        proof_irrelevance_scalar = "allow"

    if not eta_results:
        inductive_eta_scalar = "not_applicable"
    elif any(result == "deny" for result in eta_results):
        inductive_eta_scalar = "deny"
    else:
        inductive_eta_scalar = "allow"

    if not recursor_reduction_results:
        recursor_reduction_scalar = "not_applicable"
    elif any(result == "deny" for result in recursor_reduction_results):
        recursor_reduction_scalar = "deny"
    elif any(result == "unknown" for result in recursor_reduction_results):
        recursor_reduction_scalar = "unknown"
    else:
        recursor_reduction_scalar = "allow"

    projection_sources = [
        projection_source_by_eid.get(eid, "unknown")
        for eid, _proj in proj_rows
    ]
    if not proj_rows:
        projection_scalar = "not_applicable"
    elif any(source == "mismatch" for source in projection_sources):
        projection_scalar = "deny"
    elif any(result == "deny" for result in projection_results):
        projection_scalar = "deny"
    elif any(source == "unknown" for source in projection_sources) or any(
        result == "unknown" for result in projection_results
    ):
        projection_scalar = "unknown"
    else:
        projection_scalar = "allow"

    return {
        "semantic:field_universe_admissibility": field_universe_admissibility(
            records, exprs, levels
        ),
        "semantic:proof_irrelevance_applicability": proof_irrelevance_scalar,
        "semantic:inductive_eta_admissibility": inductive_eta_scalar,
        "semantic:recursor_reduction_admissibility": recursor_reduction_scalar,
        "semantic:projection_admissibility_scalar": projection_scalar,
        "semantic:projection_source_coherence": sorted(projection_sources),
        "semantic:projection_admissibility": sorted(projection_results),
        "semantic:projection_target_sort": sorted(projection_target_prop),
        "semantic:projection_dependency_barrier": sorted(projection_barrier),
        "semantic:rule_k_major_reflexivity": sorted(rule_k_reflexive),
    }


def generic_features(records: list[dict[str, Any]]) -> dict[str, Any]:
    exprs = expr_refs(records)
    levels = level_refs(records)

    expr_counts: Counter[str] = Counter()
    level_counts: Counter[str] = Counter()
    decl_counts: Counter[str] = Counter()
    top_unknown: Counter[str] = Counter()
    bvars: list[int] = []
    const_level_arities: list[int] = []
    def_safety: Counter[str] = Counter()
    def_hints: Counter[str] = Counter()
    decl_names: list[int] = []
    decl_name_kinds: dict[int, set[str]] = defaultdict(set)

    max_pi = max_app = max_lam = 0

    for row in records:
        et = expr_tag(row)
        if et is not None:
            expr_counts[et] += 1
        lt = level_tag(row)
        if lt is not None:
            level_counts[lt] += 1
        for tag in DECL_TAGS:
            if tag in row:
                decl_counts[tag] += 1
                value = row[tag]
                if isinstance(value, dict) and isinstance(value.get("name"), int):
                    name = int(value["name"])
                    decl_names.append(name)
                    decl_name_kinds[name].add(tag)
                if tag in {"def", "thm"} and isinstance(value, dict):
                    if isinstance(value.get("safety"), str):
                        def_safety[value["safety"]] += 1
                    if isinstance(value.get("hints"), str):
                        def_hints[value["hints"]] += 1
        if not any(k in row for k in META_KEYS | DECL_TAGS):
            for key in row:
                top_unknown[key] += 1
        if isinstance(row.get("bvar"), int):
            bvars.append(int(row["bvar"]))
        if isinstance(row.get("const"), dict):
            us = row["const"].get("us", [])
            if isinstance(us, list):
                const_level_arities.append(len(us))

    for eid in exprs:
        pi, _ = pi_domains(exprs, eid)
        max_pi = max(max_pi, len(pi))
        _, apps = app_spine(exprs, eid)
        max_app = max(max_app, len(apps))
        cur = eid
        depth = 0
        while True:
            row = exprs.get(cur, {})
            node = row.get("lam")
            if not isinstance(node, dict) or not isinstance(node.get("body"), int):
                break
            depth += 1
            cur = int(node["body"])
        max_lam = max(max_lam, depth)

    same_name_multi_kind = sum(1 for kinds in decl_name_kinds.values() if len(kinds) > 1)
    duplicate_decl_name_count = len(decl_names) - len(set(decl_names))

    features: dict[str, Any] = {
        "record_count": len(records),
        "expr_tag_counts": sorted(expr_counts.items()),
        "level_tag_counts": sorted(level_counts.items()),
        "decl_tag_counts": sorted(decl_counts.items()),
        "unknown_top_tag_counts": sorted(top_unknown.items()),
        "name_depth_histogram": sorted(name_depths(records).items()),
        "expr_max_pi_chain": max_pi,
        "expr_max_app_spine": max_app,
        "expr_max_lam_chain": max_lam,
        "bvar_max": max(bvars) if bvars else -1,
        "bvar_distinct": len(set(bvars)),
        "const_level_arities": sorted(const_level_arities),
        "def_safety_counts": sorted(def_safety.items()),
        "def_hints_counts": sorted(def_hints.items()),
        "duplicate_decl_name_count": duplicate_decl_name_count,
        "same_name_multi_kind_count": same_name_multi_kind,
    }
    features.update(aggregate_inductive_features(records, exprs, levels))
    features.update(semantic_probe_features(records))
    return features


def atomic_observations(features: dict[str, Any]) -> dict[str, Any]:
    out: dict[str, Any] = {}
    for key, value in features.items():
        out[f"raw:{key}"] = value
        if isinstance(value, bool):
            continue
        if isinstance(value, int):
            out[f"zero:{key}"] = value == 0
            out[f"positive:{key}"] = value > 0
        if isinstance(value, list):
            out[f"len:{key}"] = len(value)
            out[f"empty:{key}"] = len(value) == 0
            if value and all(isinstance(x, (int, bool, str)) for x in value):
                out[f"set:{key}"] = sorted(set(value), key=lambda x: str(x))
    return out


def build_cases(
    root: Path,
    checker: Path,
    start: int,
    end: int,
    lineage: list[tuple[str, Path]],
    diagnostic_checker: Path | None,
) -> list[Case]:
    out: list[Case] = []
    for n, path, expected in numbered_cases(root, start, end):
        records = load_records(path)
        actual = run_checker(checker, path)
        features = atomic_observations(generic_features(records))

        lineage_vector: list[int] = []
        for label, binary in lineage:
            verdict = run_checker(binary, path)
            features[f"behavior:lineage:{label}"] = verdict
            lineage_vector.append(verdict)
        if lineage_vector:
            features["behavior:lineage_vector"] = lineage_vector
            features["behavior:lineage_change_count"] = sum(
                a != b for a, b in zip(lineage_vector, lineage_vector[1:])
            )
            features["behavior:lineage_conclusive_count"] = sum(v in (0, 1) for v in lineage_vector)
            features["behavior:lineage_unknown_count"] = sum(v == 2 for v in lineage_vector)
            features["behavior:lineage_error_count"] = sum(v == 3 for v in lineage_vector)

        if diagnostic_checker is not None:
            diag_verdict, operations = run_diagnostic_checker(diagnostic_checker, path)
            if diag_verdict != actual:
                raise ValueError(
                    f"diagnostic verdict drift on {path}: normal={actual}, diagnostic={diag_verdict}"
                )
            for key, value in sorted(operations.items()):
                features[f"behavior:diag:{key}"] = value
            features["behavior:diag:vector"] = [
                operations["declarations"],
                operations["inductive_signatures"],
                operations["type_judgments"],
                operations["conversions"],
            ]
            features["behavior:diag:conversion_pressure"] = (
                operations["conversions"],
                operations["type_judgments"],
            )

        out.append(
            Case(
                number=n,
                path=path,
                expected=expected,
                actual=actual,
                features=features,
            )
        )
    return out


def discordant_pairs(cases: list[Case], indices: Iterable[int] | None = None) -> list[tuple[int, int]]:
    use = list(range(len(cases))) if indices is None else list(indices)
    pairs: list[tuple[int, int]] = []
    for pos, i in enumerate(use):
        for j in use[pos + 1:]:
            if cases[i].actual == cases[j].actual and cases[i].expected != cases[j].expected:
                pairs.append((i, j))
    return pairs


def candidate_edges(
    cases: list[Case],
    pairs: list[tuple[int, int]],
    feature_names: list[str],
) -> dict[str, int]:
    edges: dict[str, int] = {}
    for name in feature_names:
        bits = 0
        for k, (i, j) in enumerate(pairs):
            if cases[i].features.get(name) != cases[j].features.get(name):
                bits |= 1 << k
        if bits:
            edges[name] = bits
    return edges


def dedupe_edges(edges: dict[str, int]) -> dict[str, int]:
    best: dict[int, str] = {}
    for name, bits in sorted(edges.items()):
        best.setdefault(bits, name)
    return {name: bits for bits, name in best.items()}


def exact_min_cover(universe_size: int, edges: dict[str, int]) -> list[str] | None:
    if universe_size == 0:
        return []
    full = (1 << universe_size) - 1
    if not edges:
        return None
    union = 0
    for bits in edges.values():
        union |= bits
    if union != full:
        return None

    items_to_candidates: list[list[str]] = [[] for _ in range(universe_size)]
    for name, bits in edges.items():
        for i in range(universe_size):
            if bits >> i & 1:
                items_to_candidates[i].append(name)
    for bucket in items_to_candidates:
        bucket.sort()

    best: list[str] | None = None

    def dfs(covered: int, chosen: list[str], available: set[str]) -> None:
        nonlocal best
        if covered == full:
            if best is None or (len(chosen), chosen) < (len(best), best):
                best = chosen.copy()
            return
        if best is not None and len(chosen) >= len(best):
            return

        uncovered = full ^ (full & covered)
        remaining_edges = [edges[n] & uncovered for n in available]
        max_gain = max((x.bit_count() for x in remaining_edges), default=0)
        if max_gain == 0:
            return
        lower = (uncovered.bit_count() + max_gain - 1) // max_gain
        if best is not None and len(chosen) + lower >= len(best):
            return

        candidates_for_item: list[str] | None = None
        target_item = -1
        for i in range(universe_size):
            if not (uncovered >> i) & 1:
                continue
            opts = [n for n in items_to_candidates[i] if n in available]
            if not opts:
                return
            if candidates_for_item is None or len(opts) < len(candidates_for_item):
                candidates_for_item = opts
                target_item = i
        assert target_item >= 0 and candidates_for_item is not None

        ranked = sorted(
            candidates_for_item,
            key=lambda n: (-(edges[n] & uncovered).bit_count(), n),
        )
        for name in ranked:
            gain = edges[name] & uncovered
            if not gain:
                continue
            new_available = {
                n for n in available
                if n > name or n not in ranked
            }
            dfs(covered | edges[name], chosen + [name], new_available)

    dfs(0, [], set(edges))
    return best


def basis_covers_pairs(
    cases: list[Case],
    pairs: list[tuple[int, int]],
    basis: list[str],
) -> tuple[int, list[tuple[int, int]]]:
    missed: list[tuple[int, int]] = []
    for i, j in pairs:
        if not any(cases[i].features.get(name) != cases[j].features.get(name) for name in basis):
            missed.append((i, j))
    return len(pairs) - len(missed), missed


def stable_case_id(case: Case) -> str:
    return "s_" + hashlib.sha256(f"case:{case.number}".encode()).hexdigest()[:12]


def stable_feature_id(name: str) -> str:
    return "g_" + hashlib.sha256(f"feature:{name}".encode()).hexdigest()[:12]


def build_public_hidden(cases: list[Case], feature_names: list[str]) -> tuple[dict[str, Any], dict[str, Any]]:
    feature_ids = {name: stable_feature_id(name) for name in feature_names}
    public = {
        "schema": "lka-residual-basis-public-v0",
        "states": [
            {
                "id": stable_case_id(case),
                "current": case.actual,
                "target": case.expected,
                "observations": {
                    feature_ids[name]: case.features.get(name)
                    for name in feature_names
                },
            }
            for case in cases
        ],
        "candidate_ids": sorted(feature_ids.values()),
    }
    hidden = {
        "schema": "lka-residual-basis-hidden-v0",
        "case_numbers": {stable_case_id(case): case.number for case in cases},
        "feature_names": {feature_ids[name]: name for name in feature_names},
    }
    public["commitment"] = digest(hidden)
    return public, hidden


def solve_public(public: dict[str, Any]) -> dict[str, Any]:
    states = public["states"]
    pairs: list[tuple[int, int]] = []
    for i in range(len(states)):
        for j in range(i + 1, len(states)):
            if states[i]["current"] == states[j]["current"] and states[i]["target"] != states[j]["target"]:
                pairs.append((i, j))

    edges: dict[str, int] = {}
    for gid in public["candidate_ids"]:
        bits = 0
        for k, (i, j) in enumerate(pairs):
            if states[i]["observations"].get(gid) != states[j]["observations"].get(gid):
                bits |= 1 << k
        if bits:
            edges[gid] = bits
    edges = dedupe_edges(edges)
    basis = exact_min_cover(len(pairs), edges)
    return {
        "schema": "lka-residual-basis-prediction-v0",
        "public_digest": digest(public),
        "residual_pairs": len(pairs),
        "candidate_edges": len(edges),
        "basis": basis,
        "basis_size": None if basis is None else len(basis),
        "covered": 0 if basis is None else len(pairs),
    }


def deterministic_sham(cases: list[Case], feature_names: list[str]) -> list[Case]:
    by_current: dict[int, list[int]] = defaultdict(list)
    for i, case in enumerate(cases):
        by_current[case.actual].append(i)

    shams = [
        Case(c.number, c.path, c.expected, c.actual, dict(c.features))
        for c in cases
    ]
    for name in feature_names:
        for actual, indices in sorted(by_current.items()):
            if len(indices) <= 1:
                continue
            offset = int(hashlib.sha256(f"{name}:{actual}".encode()).hexdigest()[:8], 16) % len(indices)
            if offset == 0:
                offset = 1
            values = [cases[i].features.get(name) for i in indices]
            rotated = values[offset:] + values[:offset]
            for i, value in zip(indices, rotated):
                shams[i].features[name] = value
    return shams


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--tutorial-output", required=True, type=Path)
    parser.add_argument("--checker", required=True, type=Path)
    parser.add_argument("--output-dir", required=True, type=Path)
    parser.add_argument("--start", type=int, default=56)
    parser.add_argument("--end", type=int, default=141)
    parser.add_argument(
        "--lineage",
        action="append",
        default=[],
        metavar="LABEL=PATH",
        help="sealed semantic observation binary; may be repeated",
    )
    parser.add_argument("--diagnostic-checker", type=Path)
    args = parser.parse_args()

    lineage: list[tuple[str, Path]] = []
    for item in args.lineage:
        if "=" not in item:
            raise ValueError(f"bad --lineage value {item!r}")
        label, raw_path = item.split("=", 1)
        lineage.append((label, Path(raw_path)))

    cases = build_cases(
        args.tutorial_output,
        args.checker,
        args.start,
        args.end,
        lineage,
        args.diagnostic_checker,
    )
    feature_names = sorted(set.intersection(*(set(c.features) for c in cases)))
    # Drop globally constant observations: they cannot separate anything.
    feature_names = [
        name for name in feature_names
        if len({canonical(c.features.get(name)) for c in cases}) > 1
    ]

    # Minimum-basis cardinality is meaningful only when one "candidate" cannot
    # smuggle an arbitrarily rich vector. Restrict the rewrite search to
    # low-bandwidth observations: at most four distinct outcomes on the frozen
    # suffix. High-cardinality vectors remain available in the archived scout
    # run, but cannot count as one primitive law here.
    feature_cardinality = {
        name: len({canonical(c.features.get(name)) for c in cases})
        for name in feature_names
    }
    feature_names = [
        name for name in feature_names
        if feature_cardinality[name] <= 4
    ]

    public, hidden = build_public_hidden(cases, feature_names)
    prediction = solve_public(public)

    pairs = discordant_pairs(cases)
    real_edges = dedupe_edges(candidate_edges(cases, pairs, feature_names))
    real_basis = exact_min_cover(len(pairs), real_edges)

    semantic_feature_names = sorted(
        name for name in feature_names
        if name.startswith("raw:semantic:")
    )
    semantic_edges = dedupe_edges(
        candidate_edges(cases, pairs, semantic_feature_names)
    )
    semantic_basis = exact_min_cover(len(pairs), semantic_edges)
    semantic_full_mask = (1 << len(pairs)) - 1 if pairs else 0
    semantic_covered_mask = 0
    for bits in semantic_edges.values():
        semantic_covered_mask |= bits
    semantic_uncovered_mask = semantic_full_mask & ~semantic_covered_mask
    semantic_uncovered_pairs = [
        pairs[k] for k in range(len(pairs))
        if (semantic_uncovered_mask >> k) & 1
    ]

    full_mask = (1 << len(pairs)) - 1 if pairs else 0
    covered_mask = 0
    for bits in real_edges.values():
        covered_mask |= bits
    uncovered_mask = full_mask & ~covered_mask
    uncovered_pairs = [
        pairs[k] for k in range(len(pairs))
        if (uncovered_mask >> k) & 1
    ]
    coverage_ranking = sorted(
        (
            {
                "candidate": name,
                "coverage": bits.bit_count(),
                "outcomes": feature_cardinality.get(name),
            }
            for name, bits in real_edges.items()
        ),
        key=lambda row: (-row["coverage"], row["candidate"]),
    )

    train_idx = [i for i, c in enumerate(cases) if c.number % 5 != 0]
    hold_idx = [i for i, c in enumerate(cases) if c.number % 5 == 0]
    train_pairs = discordant_pairs(cases, train_idx)
    hold_pairs = discordant_pairs(cases, hold_idx)
    train_edges = dedupe_edges(candidate_edges(cases, train_pairs, feature_names))
    train_basis = exact_min_cover(len(train_pairs), train_edges)
    real_hold_covered, real_hold_missed = (
        (0, hold_pairs) if train_basis is None
        else basis_covers_pairs(cases, hold_pairs, train_basis)
    )

    sham_cases = deterministic_sham(cases, feature_names)
    sham_train_edges = dedupe_edges(candidate_edges(sham_cases, train_pairs, feature_names))
    sham_basis = exact_min_cover(len(train_pairs), sham_train_edges)
    sham_hold_covered, sham_hold_missed = (
        (0, hold_pairs) if sham_basis is None
        else basis_covers_pairs(sham_cases, hold_pairs, sham_basis)
    )

    reveal_ok = hidden["schema"] == "lka-residual-basis-hidden-v0" and digest(hidden) == public["commitment"]
    predicted_names = None
    if prediction["basis"] is not None:
        predicted_names = [hidden["feature_names"][gid] for gid in prediction["basis"]]

    if real_basis is None:
        verdict = "INSUFFICIENT_GRAMMAR"
    elif hold_pairs and real_hold_covered < sham_hold_covered:
        verdict = "NEGATIVE_SHAM_DOMINATES"
    elif real_hold_covered == len(hold_pairs) and (
        sham_hold_covered < len(hold_pairs)
        or sham_basis is None
        or train_basis is not None and len(train_basis) <= len(sham_basis)
    ):
        verdict = "BOUNDED_POSITIVE"
    else:
        verdict = "BOUNDED_INCONCLUSIVE"

    summary = {
        "schema": "lka-residual-basis-v0",
        "authority": "read-only discovery; cannot grant or revoke checker semantics",
        "verdict": verdict,
        "case_range": [args.start, args.end],
        "case_count": len(cases),
        "current_correct": sum(c.actual == c.expected for c in cases),
        "current_incorrect": sum(c.actual not in (2, 3) and c.actual != c.expected for c in cases),
        "current_unknown": sum(c.actual == 2 for c in cases),
        "current_error": sum(c.actual == 3 for c in cases),
        "candidate_observations": len(feature_names),
        "candidate_outcome_cap": 4,
        "residual_pairs": len(pairs),
        "separable_residual_pairs": len(pairs) - len(uncovered_pairs),
        "unseparated_residual_pairs": len(uncovered_pairs),
        "first_unseparated_pairs": [
            [cases[i].number, cases[j].number]
            for i, j in uncovered_pairs[:40]
        ],
        "top_candidate_coverage": coverage_ranking[:20],
        "semantic_only": {
            "candidate_observations": len(semantic_feature_names),
            "basis_size": None if semantic_basis is None else len(semantic_basis),
            "basis": semantic_basis,
            "separable_residual_pairs": len(pairs) - len(semantic_uncovered_pairs),
            "unseparated_residual_pairs": len(semantic_uncovered_pairs),
            "first_unseparated_pairs": [
                [cases[i].number, cases[j].number]
                for i, j in semantic_uncovered_pairs[:40]
            ],
        },
        "exact_basis_size": None if real_basis is None else len(real_basis),
        "exact_basis": real_basis,
        "blind_prediction_basis_ids": prediction["basis"],
        "blind_reveal_basis": predicted_names,
        "blind_commitment_ok": reveal_ok,
        "heldout": {
            "split": "case_number_mod_5_equals_0",
            "train_cases": len(train_idx),
            "heldout_cases": len(hold_idx),
            "train_residual_pairs": len(train_pairs),
            "heldout_residual_pairs": len(hold_pairs),
            "real_basis_size": None if train_basis is None else len(train_basis),
            "real_basis": train_basis,
            "real_heldout_covered": real_hold_covered,
            "real_heldout_total": len(hold_pairs),
            "real_heldout_missed": [
                [cases[i].number, cases[j].number] for i, j in real_hold_missed
            ],
            "sham_basis_size": None if sham_basis is None else len(sham_basis),
            "sham_heldout_covered": sham_hold_covered,
            "sham_heldout_total": len(hold_pairs),
            "sham_heldout_missed": [
                [cases[i].number, cases[j].number] for i, j in sham_hold_missed
            ],
        },
        "first_mismatch": next(
            (
                {
                    "number": c.number,
                    "expected": c.expected,
                    "actual": c.actual,
                    "file": c.path.name,
                }
                for c in cases if c.actual != c.expected
            ),
            None,
        ),
    }

    out = args.output_dir
    out.mkdir(parents=True, exist_ok=True)
    (out / "public.json").write_text(json.dumps(public, indent=2, sort_keys=True) + "\n")
    (out / "hidden.json").write_text(json.dumps(hidden, indent=2, sort_keys=True) + "\n")
    (out / "prediction.json").write_text(json.dumps(prediction, indent=2, sort_keys=True) + "\n")
    (out / "summary.json").write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n")
    (out / "cases.json").write_text(json.dumps([
        {
            "number": c.number,
            "file": c.path.name,
            "expected": c.expected,
            "actual": c.actual,
            "case_id": stable_case_id(c),
        }
        for c in cases
    ], indent=2, sort_keys=True) + "\n")

    print("LKA_RESIDUAL_BASIS_V0")
    print(json.dumps(summary, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
