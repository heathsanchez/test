#!/usr/bin/env python3
"""Qualify the AnyIO mutable-closure observation and equivalence-class gate.

This is intentionally posthoc training-only. It never reads the repaired AnyIO
head production or the previously sealed executing future.
"""
from __future__ import annotations

import ast
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import time
import xml.etree.ElementTree as ET

from research.unified_consequence_runtime import typed_v104_msi_bridge_v7 as bridge

ROOT = Path(__file__).resolve().parents[2]
PROTOCOL_PATH = Path("research/unified_consequence_runtime/G2_MUTABLE_CLOSURE_EQUIVALENCE_FIX_PROTOCOL_V2.json")
PROTOCOL_COMMIT = "7cc32cabf2f749e13aa7813fb2dc62cfb1a1d9ff"
COLD = "COLD_V104_ORDER"


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def canonical(value: object) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False)


def git(repo: Path, *args: str, raw: bool = False):
    out = subprocess.check_output(["git", "--no-replace-objects", "-C", str(repo), *args])
    return out if raw else out.decode().strip()


def frozen_protocol() -> dict[str, object]:
    live = (ROOT / PROTOCOL_PATH).read_bytes()
    frozen = git(ROOT, "show", f"{PROTOCOL_COMMIT}:{PROTOCOL_PATH}", raw=True)
    if live != frozen:
        raise ValueError("PROTOCOL_MUTATED_AFTER_FREEZE")
    p = json.loads(frozen)
    if p.get("state") != "FROZEN_BEFORE_IMPLEMENTATION_AND_NATIVE_OUTCOME":
        raise ValueError("INVALID_PROTOCOL_STATE")
    return p


def attr_path(node: ast.AST) -> tuple[str, ...] | None:
    parts: list[str] = []
    cur = node
    while isinstance(cur, ast.Attribute):
        parts.append(cur.attr)
        cur = cur.value
    if not isinstance(cur, ast.Name):
        return None
    return (cur.id, *reversed(parts))


class OuterVisitor(ast.NodeVisitor):
    def __init__(self, root: ast.FunctionDef | ast.AsyncFunctionDef):
        self.root = root
        self.assigns: list[ast.Assign] = []
        self.ifs: list[ast.If] = []
        self.stores: set[str] = set()

    def visit_FunctionDef(self, node):
        if node is self.root:
            for stmt in node.body:
                self.visit(stmt)

    def visit_AsyncFunctionDef(self, node):
        if node is self.root:
            for stmt in node.body:
                self.visit(stmt)

    def visit_Lambda(self, node):
        return

    def visit_Assign(self, node):
        self.assigns.append(node)
        for target in node.targets:
            for child in ast.walk(target):
                if isinstance(child, ast.Name) and isinstance(child.ctx, ast.Store):
                    self.stores.add(child.id)
        self.generic_visit(node.value)

    def visit_AnnAssign(self, node):
        if isinstance(node.target, ast.Name):
            self.stores.add(node.target.id)
        if node.value is not None:
            self.visit(node.value)

    def visit_NamedExpr(self, node):
        if isinstance(node.target, ast.Name):
            self.stores.add(node.target.id)
        self.visit(node.value)

    def visit_For(self, node):
        for child in ast.walk(node.target):
            if isinstance(child, ast.Name) and isinstance(child.ctx, ast.Store):
                self.stores.add(child.id)
        self.visit(node.iter)
        for stmt in node.body + node.orelse:
            self.visit(stmt)

    def visit_If(self, node):
        self.ifs.append(node)
        self.visit(node.test)
        for stmt in node.body + node.orelse:
            self.visit(stmt)


def nested_free_names(node: ast.FunctionDef | ast.AsyncFunctionDef) -> set[str]:
    args = {
        a.arg for a in (
            list(node.args.posonlyargs)
            + list(node.args.args)
            + list(node.args.kwonlyargs)
        )
    }
    if node.args.vararg:
        args.add(node.args.vararg.arg)
    if node.args.kwarg:
        args.add(node.args.kwarg.arg)
    stores = set(args)
    loads: set[str] = set()
    for child in ast.walk(node):
        if isinstance(child, ast.Name):
            if isinstance(child.ctx, ast.Store):
                stores.add(child.id)
            elif isinstance(child.ctx, ast.Load):
                loads.add(child.id)
    return loads - stores


def qualname_guard(node: ast.If, read_name: str, wrapper_name: str) -> bool:
    names = {x.id for x in ast.walk(node.test) if isinstance(x, ast.Name)}
    attrs = {x.attr for x in ast.walk(node.test) if isinstance(x, ast.Attribute)}
    ops = [x for x in ast.walk(node.test) if isinstance(x, ast.cmpop)]
    return (
        read_name in names
        and wrapper_name in names
        and "__qualname__" in attrs
        and any(isinstance(op, (ast.Eq, ast.NotEq)) for op in ops)
    )


def scan_patterns(path: str, source: bytes) -> list[dict[str, object]]:
    text = source.decode("utf-8")
    tree = ast.parse(text, filename=path)
    patterns: list[dict[str, object]] = []
    for fn in [x for x in tree.body if isinstance(x, (ast.FunctionDef, ast.AsyncFunctionDef))]:
        nested = [x for x in fn.body if isinstance(x, (ast.FunctionDef, ast.AsyncFunctionDef))]
        ov = OuterVisitor(fn)
        ov.visit(fn)
        for inner in nested:
            free = nested_free_names(inner)
            reads = []
            writes = []
            for ass in ov.assigns:
                if len(ass.targets) != 1:
                    continue
                target = ass.targets[0]
                if isinstance(target, ast.Name):
                    path_value = attr_path(ass.value)
                    if path_value is not None:
                        reads.append((target.id, path_value, ass.lineno))
                target_path = attr_path(target)
                if (
                    target_path is not None
                    and isinstance(ass.value, ast.Name)
                    and ass.value.id == inner.name
                ):
                    writes.append((target_path, ass.lineno))
            for read_name, read_path, read_line in reads:
                if read_name not in free:
                    continue
                for write_path, write_line in writes:
                    if write_path != read_path or write_line <= read_line:
                        continue
                    guards = [
                        g for g in ov.ifs
                        if read_line < g.lineno < write_line and qualname_guard(g, read_name, inner.name)
                    ]
                    if not guards:
                        continue
                    dynamic = sorted((free & ov.stores) - {read_name})
                    if not dynamic:
                        continue
                    guard = min(guards, key=lambda g: g.lineno)
                    code_first_line = min(
                        [fn.lineno, *[d.lineno for d in fn.decorator_list]]
                    )
                    base = {
                        "path": path,
                        "function": fn.name,
                        "function_line": fn.lineno,
                        "code_first_line": code_first_line,
                        "wrapper": inner.name,
                        "wrapper_line": inner.lineno,
                        "read_variable": read_name,
                        "attribute_path": list(read_path),
                        "read_line": read_line,
                        "guard_line": guard.lineno,
                        "write_line": write_line,
                        "dynamic_captures": dynamic,
                    }
                    base["pattern_id"] = "mutable-closure:" + sha256(canonical(base).encode())[:24]
                    patterns.append(base)
    unique = {row["pattern_id"]: row for row in patterns}
    return sorted(unique.values(), key=lambda row: (row["function_line"], row["read_line"], row["pattern_id"]))


def stable_trace_rows(log_path: Path) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    if not log_path.exists():
        return rows
    seen: set[str] = set()
    for line in log_path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        record = json.loads(line)
        for event in record.get("events", []):
            key = canonical(event)
            if key not in seen:
                seen.add(key)
                rows.append(event)
    return rows


def trace_has_stale_capture(pattern: dict[str, object], events: list[dict[str, object]]) -> dict[str, object]:
    relevant = [e for e in events if e.get("function") == pattern["function"] and e.get("guard_line") == pattern["guard_line"]]
    distinct: dict[str, set[str]] = {name: set() for name in pattern["dynamic_captures"]}
    mismatches: list[dict[str, object]] = []
    for event in relevant:
        current = event.get("dynamic_captures", {})
        closure = event.get("read_callable", {}).get("closure", {})
        for name in pattern["dynamic_captures"]:
            cur = current.get(name)
            old = closure.get(name)
            if isinstance(cur, dict) and cur.get("kind") == "primitive":
                distinct[name].add(canonical(cur.get("value")))
            if (
                isinstance(cur, dict) and cur.get("kind") == "primitive"
                and isinstance(old, dict) and old.get("kind") == "primitive"
                and cur.get("value") != old.get("value")
            ):
                mismatches.append({
                    "capture": name,
                    "current": cur.get("value"),
                    "persisted": old.get("value"),
                    "nodeid": event.get("nodeid"),
                })
    changed = sorted(name for name, values in distinct.items() if len(values) >= 2)
    return {
        "event_count": len(relevant),
        "distinct_context_captures": changed,
        "stale_capture_mismatches": mismatches,
        "pass": bool(changed and mismatches),
    }


def unique_name(source: str, stem: str) -> str:
    names = {n.id for n in ast.walk(ast.parse(source)) if isinstance(n, ast.Name)}
    if stem not in names:
        return stem
    i = 2
    while f"{stem}_{i}" in names:
        i += 1
    return f"{stem}_{i}"


def repair_source(source: bytes, pattern: dict[str, object]) -> bytes:
    text = source.decode("utf-8")
    lines = text.splitlines(keepends=True)
    idx = int(pattern["read_line"]) - 1
    if idx < 0 or idx >= len(lines):
        raise ValueError("READ_LINE_OUT_OF_RANGE")
    indent = re.match(r"\s*", lines[idx]).group(0)
    read_var = str(pattern["read_variable"])
    wrapper = str(pattern["wrapper"])
    cells = unique_name(text, "__udm_closure_cells")
    cell = unique_name(text + "\n" + cells, "__udm_original_cell")
    snippet = [
        f'{indent}if getattr({read_var}, "__qualname__", None) == {wrapper}.__qualname__ and getattr({read_var}, "__closure__", None):\n',
        f'{indent}    {cells} = dict(zip({read_var}.__code__.co_freevars, {read_var}.__closure__))\n',
        f'{indent}    {cell} = {cells}.get({read_var!r})\n',
        f'{indent}    if {cell} is not None:\n',
        f'{indent}        {read_var} = {cell}.cell_contents\n',
    ]
    repaired = "".join(lines[: idx + 1] + snippet + lines[idx + 1 :])
    ast.parse(repaired, filename=str(pattern["path"]))
    return repaired.encode("utf-8")


def junit_counts(path: Path) -> dict[str, int]:
    root = ET.parse(path).getroot()
    suite = root if root.tag == "testsuite" else next(root.iter("testsuite"))
    return {k: int(suite.get(k, 0)) for k in ("tests", "failures", "errors", "skipped")}


def run_pytest(world: Path, nodes: list[str], out: Path, *, patterns=None, timeout=150) -> dict[str, object]:
    out.mkdir(parents=True, exist_ok=False)
    junit = out / "junit.xml"
    log = out / "mutable-closure-trace.jsonl"
    env = dict(os.environ)
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    env["PYTHONHASHSEED"] = "0"
    pythonpath = [str(ROOT), str(world / "src"), str(world)]
    if env.get("PYTHONPATH"):
        pythonpath.append(env["PYTHONPATH"])
    env["PYTHONPATH"] = os.pathsep.join(pythonpath)
    if patterns is not None:
        env["PYTEST_PLUGINS"] = "research.unified_consequence_runtime.g2_mutable_closure_trace_plugin_v2"
        env["UDM_G2_MUTABLE_CLOSURE_PATTERNS"] = canonical(patterns)
        env["UDM_G2_WORLD_ROOT"] = str(world)
        env["UDM_G2_MUTABLE_CLOSURE_LOG"] = str(log)
    else:
        env.pop("UDM_G2_MUTABLE_CLOSURE_PATTERNS", None)
        env.pop("UDM_G2_WORLD_ROOT", None)
        env.pop("UDM_G2_MUTABLE_CLOSURE_LOG", None)
        if env.get("PYTEST_PLUGINS") == "research.unified_consequence_runtime.g2_mutable_closure_trace_plugin_v2":
            env.pop("PYTEST_PLUGINS", None)
    argv = [
        sys.executable, "-m", "pytest", "-q", "-p", "no:cacheprovider", "-p", "pytest_cov",
        "--junitxml=" + str(junit), "--rootdir=" + str(world), "-c", str(world / "pyproject.toml"),
        *nodes,
    ]
    start = time.monotonic()
    try:
        proc = subprocess.run(argv, cwd=world, env=env, capture_output=True, text=True, timeout=timeout)
        rc = proc.returncode
        timeout_hit = False
    except subprocess.TimeoutExpired as exc:
        rc = 124
        timeout_hit = True
        proc = exc
    counts = junit_counts(junit) if junit.is_file() else {"tests": 0, "failures": 0, "errors": 1, "skipped": 0}
    stdout = getattr(proc, "stdout", "") or ""
    stderr = getattr(proc, "stderr", "") or ""
    return {
        "returncode": rc,
        "timeout": timeout_hit,
        "counts": counts,
        "wall_seconds": time.monotonic() - start,
        "stdout_sha256": sha256(stdout.encode()),
        "stderr_sha256": sha256(stderr.encode()),
        "stdout_tail": stdout[-2000:],
        "stderr_tail": stderr[-2000:],
        "trace_events": stable_trace_rows(log),
    }


def policy_classes(world: Path, triskelion: Path, msi: Path, production_path: str) -> dict[str, object]:
    catalog = bridge.catalog_v104_typed(
        world, git(world, "rev-parse", "HEAD"), [production_path], triskelion, msi, cap=64, observation={}
    )
    groups: dict[tuple[str, ...], list[str]] = {}
    for name, order in catalog["orders"].items():
        prefix = tuple(order[:8])
        groups.setdefault(prefix, []).append(name)
    classes = []
    for prefix, names in groups.items():
        class_id = "policy-class:" + sha256(canonical(list(prefix)).encode())[:24]
        classes.append({
            "class_id": class_id,
            "members": sorted(names),
            "prefix": list(prefix),
            "is_cold": COLD in names,
        })
    classes.sort(key=lambda row: (not row["is_cold"], row["class_id"]))
    return {
        "candidate_count": len(catalog["rows"]),
        "policy_name_count": len(catalog["orders"]),
        "class_count": len(classes),
        "classes": classes,
        "source_manifest_sha256": catalog["original_typed_source_sha256"],
    }


def main(world: Path, triskelion: Path, msi: Path, dest: Path) -> dict[str, object]:
    p = frozen_protocol()
    world = world.resolve(strict=True)
    triskelion = triskelion.resolve(strict=True)
    msi = msi.resolve(strict=True)
    dest = dest.resolve()
    dest.mkdir(parents=True, exist_ok=False)
    result: dict[str, object] = {
        "schema": "UDM_G2_MUTABLE_CLOSURE_EQUIVALENCE_FIX_RESULT_V2",
        "status": "UNKNOWN",
        "G2": "UNKNOWN", "G3": "UNKNOWN", "G4": "UNKNOWN", "G5": "UNKNOWN", "G6": "UNKNOWN",
        "heldout_future": "UNOPENED",
        "author_repaired_production_read": False,
    }
    src = p["source"]
    production = str(src["production_path"])
    test_path = str(src["author_test_path"])
    original = (world / production).read_bytes()
    author = (world / test_path).read_bytes()
    if git(world, "rev-parse", "HEAD") != src["base"]:
        raise ValueError("WRONG_ANYIO_BASE")
    if git(world, "rev-parse", "HEAD^{tree}") != src["base_tree"]:
        raise ValueError("WRONG_ANYIO_TREE")
    if sha256(original) != src["production_sha256"]:
        raise ValueError("ORIGINAL_PRODUCTION_HASH_MISMATCH")
    if sha256(author) != src["author_test_sha256"]:
        raise ValueError("AUTHOR_TEST_HASH_MISMATCH")
    changed = git(world, "diff", "--name-only").splitlines()
    if changed != [test_path]:
        raise ValueError("EXPECTED_ONLY_AUTHOR_TEST_OVERLAY")

    patterns = scan_patterns(production, original)
    result["patterns"] = patterns
    result["pattern_count"] = len(patterns)
    if not patterns:
        result["status"] = "UNKNOWN_NO_SOURCE_NEUTRAL_MUTABLE_CLOSURE_PATTERN"
        (dest / "RESULT.json").write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
        return result

    quotient = policy_classes(world, triskelion, msi, production)
    result["policy_quotient"] = quotient
    noncold = [row for row in quotient["classes"] if not row["is_cold"]]
    cold = [row for row in quotient["classes"] if row["is_cold"]]
    if not (
        quotient["policy_name_count"] == 37
        and quotient["class_count"] == 2
        and len(cold) == 1
        and len(noncold) == 1
        and len(cold[0]["members"]) == 1
        and len(noncold[0]["members"]) == 36
    ):
        result["status"] = "UNKNOWN_POLICY_EQUIVALENCE_REPRODUCTION"
        (dest / "RESULT.json").write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
        return result

    protected_nodes = [str(world / n.split("::", 1)[0]) + "::" + n.split("::", 1)[1] for n in src["protected"]]
    baseline = run_pytest(world, protected_nodes, dest / "baseline-native")
    result["baseline"] = baseline
    if not (
        baseline["returncode"] == 1
        and baseline["counts"] == {"tests": 2, "failures": 2, "errors": 0, "skipped": 0}
    ):
        result["status"] = "UNKNOWN_BASELINE_PROTECTED_FAILURE_NOT_REPRODUCED"
        (dest / "RESULT.json").write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
        return result

    observed = run_pytest(world, protected_nodes, dest / "observer-native", patterns=patterns)
    result["observer_native"] = observed
    observer_checks = [trace_has_stale_capture(pattern, observed["trace_events"]) for pattern in patterns]
    result["observer_checks"] = observer_checks
    passing = [i for i, row in enumerate(observer_checks) if row["pass"]]
    if not (
        observed["returncode"] == 1
        and observed["counts"] == {"tests": 2, "failures": 2, "errors": 0, "skipped": 0}
        and passing
    ):
        result["status"] = "UNKNOWN_NO_NATIVE_STALE_CLOSURE_CAPTURE"
        (dest / "RESULT.json").write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
        return result

    # Candidate order was determined entirely by source structure before repair outcomes.
    candidates = []
    for index in passing:
        pattern = patterns[index]
        repaired = repair_source(original, pattern)
        candidates.append({
            "pattern": pattern,
            "source": repaired,
            "source_sha256": sha256(repaired),
            "candidate_id": "mutable-closure-repair:" + sha256(repaired)[:24],
        })
    result["candidate_schedule"] = [
        {"candidate_id": c["candidate_id"], "pattern_id": c["pattern"]["pattern_id"], "source_sha256": c["source_sha256"]}
        for c in candidates
    ]

    winner = None
    evaluations = []
    for index, candidate in enumerate(candidates):
        (world / production).write_bytes(candidate["source"])
        if (world / test_path).read_bytes() != author:
            raise ValueError("AUTHOR_TEST_MUTATED")
        first = run_pytest(world, protected_nodes, dest / f"repair-{index:02d}-a")
        second = run_pytest(world, protected_nodes, dest / f"repair-{index:02d}-b")
        full = run_pytest(world, [str(world / test_path)], dest / f"repair-{index:02d}-full", timeout=240)
        good = (
            first["returncode"] == 0 and first["counts"]["failures"] == 0 and first["counts"]["errors"] == 0
            and second["returncode"] == 0 and second["counts"]["failures"] == 0 and second["counts"]["errors"] == 0
            and full["returncode"] == 0 and full["counts"]["tests"] > 0
            and full["counts"]["failures"] == 0 and full["counts"]["errors"] == 0
        )
        evaluations.append({
            "candidate_id": candidate["candidate_id"],
            "pattern_id": candidate["pattern"]["pattern_id"],
            "source_sha256": candidate["source_sha256"],
            "protected_first": first,
            "protected_second": second,
            "full_author_file": full,
            "pass": good,
        })
        if good and winner is None:
            winner = candidate
        # No outcome-dependent candidate invention; schedule stays frozen above.
    result["candidate_evaluations"] = evaluations

    if winner is None:
        (world / production).write_bytes(original)
        result["status"] = "REJECTED_OBSERVER_DERIVED_REPAIR_ON_TRAINING"
        (dest / "RESULT.json").write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
        return result

    # Physical withdrawal of the generated program.
    (world / production).write_bytes(original)
    withdrawn = run_pytest(world, protected_nodes, dest / "withdrawal-native")
    result["withdrawal"] = withdrawn
    if not (
        withdrawn["returncode"] == 1
        and withdrawn["counts"] == {"tests": 2, "failures": 2, "errors": 0, "skipped": 0}
    ):
        result["status"] = "UNKNOWN_WITHDRAWAL_DID_NOT_RESTORE_FAILURE"
        (dest / "RESULT.json").write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
        return result

    # Exact restoration of the same generated source.
    (world / production).write_bytes(winner["source"])
    restored = run_pytest(world, protected_nodes, dest / "restoration-native")
    result["restoration"] = restored
    if not (
        restored["returncode"] == 0
        and restored["counts"]["tests"] == 2
        and restored["counts"]["failures"] == 0
        and restored["counts"]["errors"] == 0
        and restored["counts"]["skipped"] == 0
    ):
        result["status"] = "UNKNOWN_RESTORATION_NOT_REVERIFIED"
        (dest / "RESULT.json").write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
        return result

    # Class-level authorization. Named aliases are preserved only as lineage metadata.
    repair_class = "repair-class:" + sha256(
        canonical({"pattern_id": winner["pattern"]["pattern_id"], "source_sha256": winner["source_sha256"]}).encode()
    )[:24]
    result["selection"] = {
        "status": "AUTHORIZED_REPAIR_CLASS",
        "unit": "EQUIVALENCE_CLASS_NOT_POLICY_NAME",
        "selected_class": repair_class,
        "selected_candidate": winner["candidate_id"],
        "cold_class": cold[0]["class_id"],
        "old_noncold_alias_class": noncold[0]["class_id"],
        "old_noncold_alias_count": len(noncold[0]["members"]),
        "canonical_old_alias_representative": noncold[0]["members"][0],
        "representative_has_no_authority_effect": True,
    }
    result["status"] = "WARRANTED_BOUNDED_POSTHOC_TRAINING_REPAIR_AND_CLASS_SELECTOR"
    result["training_repair"] = {
        "candidate_id": winner["candidate_id"],
        "pattern_id": winner["pattern"]["pattern_id"],
        "source_sha256": winner["source_sha256"],
        "causal_withdrawal": True,
        "restoration": True,
        "full_author_file_green": True,
    }
    (dest / "GENERATED_REPAIR.py").write_bytes(winner["source"])
    (dest / "RESULT.json").write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    return result


if __name__ == "__main__":
    if len(sys.argv) != 5:
        raise SystemExit("usage: g2_anyio_mutable_closure_equivalence_fix_v2.py ANYIO_BASE TRISKELION MSI OUT")
    result = main(*(Path(x) for x in sys.argv[1:]))
    print(json.dumps({
        "status": result.get("status"),
        "pattern_count": result.get("pattern_count"),
        "policy_classes": result.get("policy_quotient", {}).get("class_count"),
        "selected_class": result.get("selection", {}).get("selected_class"),
        "heldout_future": result.get("heldout_future"),
        "G2": result.get("G2"),
    }, sort_keys=True), flush=True)
    raise SystemExit(0 if result.get("status") in {
        "WARRANTED_BOUNDED_POSTHOC_TRAINING_REPAIR_AND_CLASS_SELECTOR",
        "REJECTED_OBSERVER_DERIVED_REPAIR_ON_TRAINING",
    } else 2)
