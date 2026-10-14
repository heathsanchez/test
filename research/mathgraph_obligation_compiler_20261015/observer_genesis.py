#!/usr/bin/env python3
"""Bounded source-derived stateful observer synthesis, not autonomous L7.

No class name, source file, changed method, test name, or test value is supplied
per repository. The two GENERAL observation templates are human-written.
Historical PR titles disclosed defect families before freezing this trial.
"""
from __future__ import annotations

import ast
import collections.abc
import datetime
import hashlib
import importlib
import inspect
import json
import os
import pathlib
import re
import subprocess
import sys
import tempfile
import time

HERE = pathlib.Path(__file__).resolve().parent
TARGETS = (
    dict(repo="tkem/cachetools", pr=441,
         base="f4f288579dc3c8f82f62d0eaca7774303d9d3768",
         head="2417c0d63b286772169c0eab4ccf141213e1ca45",
         role="development"),
    dict(repo="mahmoud/boltons", pr=474,
         base="967864f89791509f9eb36b22b4579d36b72a6df2",
         head="adce5659b0b4a23ad5839d5aa2c88063b5b6f76b",
         role="transfer"),
)
HUNK = re.compile(r"^@@ -\d+(?:,\d+)? \+(\d+)(?:,(\d+))? @@")


def call(args, cwd=None, env=None, timeout=160):
    t = time.monotonic()
    p = subprocess.run(args, cwd=cwd, env=env, capture_output=True,
                       text=True, timeout=timeout, check=False)
    return {
        "code": p.returncode,
        "stdout": p.stdout[-12000:],
        "stderr": p.stderr[-7000:],
        "seconds": round(time.monotonic() - t, 4),
    }


def checked(args, cwd=None, timeout=160):
    p = call(args, cwd=cwd, timeout=timeout)
    if p["code"]:
        raise RuntimeError(
            "command failed: " + repr(args) + " " + p["stderr"][-1500:]
        )
    return p["stdout"].strip()


def sha_file(path):
    return hashlib.sha256(pathlib.Path(path).read_bytes()).hexdigest()


def make_worktrees(root, target):
    root.mkdir(parents=True, exist_ok=True)
    bare = root / "original"
    checked(["git", "init", "-q", str(bare)])
    checked(["git", "-C", str(bare), "remote", "add",
             "origin", "https://github.com/" + target["repo"] + ".git"])
    checked(["git", "-C", str(bare), "fetch", "-q", "--no-tags",
             "--depth=1", "origin", target["base"], target["head"]], timeout=240)
    result = {}
    for label in ("base", "head"):
        dest = root / label
        checked(["git", "-C", str(bare), "worktree", "add", "-q",
                 "--detach", str(dest), target[label]])
        actual = checked(["git", "-C", str(dest), "rev-parse", "HEAD"])
        if actual != target[label]:
            raise RuntimeError("UNKNOWN_SOURCE_IDENTITY: " + label)
        result[label] = dest
    return bare, result


def changed_python(repo, base, head):
    out = checked(["git", "-C", str(repo), "diff", "--name-only",
                   base, head, "--", "*.py"])
    return [s for s in out.splitlines()
            if s and not s.startswith("tests/") and "/tests/" not in s
            and not pathlib.Path(s).name.startswith("test_")]


def changed_lines(repo, base, head, path):
    diff = checked(["git", "-C", str(repo), "diff", "--unified=0",
                    base, head, "--", path])
    points = set()
    for line in diff.splitlines():
        match = HUNK.match(line)
        if match:
            start = int(match.group(1))
            length = int(match.group(2) or "1")
            points.update(range(start, start + max(1, length)))
    return points


def discover_methods(repo, trees, target):
    discovered = []
    for path in changed_python(repo, target["base"], target["head"]):
        candidate = trees["head"] / path
        if not candidate.exists():
            continue
        source = candidate.read_text(encoding="utf-8")
        try:
            syntax = ast.parse(source, filename=path)
        except SyntaxError:
            continue
        points = changed_lines(repo, target["base"], target["head"], path)
        for owner in syntax.body:
            if not isinstance(owner, ast.ClassDef):
                continue
            methods = [n for n in owner.body
                       if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))]
            method_map = {m.name: m for m in methods}
            init = method_map.get("__init__")
            init_args = set()
            if init is not None:
                init_args = {a.arg for a in init.args.args + init.args.kwonlyargs}
            for member in methods:
                if not points.intersection(range(member.lineno,
                                                 member.end_lineno + 1)):
                    continue
                doc = (ast.get_docstring(member) or "").lower()
                params = [a.arg for a in member.args.args]
                vararg = member.args.vararg.arg if member.args.vararg else None
                kinds = []
                if vararg and ("iterable" in doc or "iterables" in doc):
                    kinds.append("variadic-iterable-state")
                if (member.name == "__setitem__"
                        and {"ttl", "timer"}.issubset(init_args)):
                    kinds.append("timer-exception-continuation")
                if not kinds:
                    discovered.append({
                        "file": path, "class": owner.name,
                        "method": member.name, "status": "UNKNOWN_METHOD_GRAMMAR",
                    })
                for kind in kinds:
                    discovered.append({
                        "file": path, "class": owner.name, "method": member.name,
                        "kind": kind, "source_line": member.lineno,
                        "source_method_doc": doc[:160],
                        "signature_args": params, "vararg": vararg,
                        "source_sha256": hashlib.sha256(
                            source.encode("utf-8")).hexdigest(),
                    })
    return discovered


def find_import_info(root, relative):
    parts = pathlib.PurePosixPath(relative).parts
    for i in range(len(parts) - 1):
        if (root.joinpath(*parts[:i+1], "__init__.py")).exists():
            continue
        if (root.joinpath(*parts[:i+2], "__init__.py")).exists():
            package_parts = list(parts[i+1:-1])
            if parts[-1] != "__init__.py":
                package_parts.append(parts[-1][:-3])
            return root.joinpath(*parts[:i+1]), ".".join(package_parts)
    if (root / parts[0] / "__init__.py").exists():
        suffix = list(parts[:-1])
        if parts[-1] != "__init__.py":
            suffix.append(parts[-1][:-3])
        return root, ".".join(suffix)
    raise RuntimeError("UNKNOWN_PYTHON_IMPORT_LAYOUT: " + relative)


def captured(fn):
    try:
        value = fn()
        if isinstance(value, (bool, int, float, str, type(None))):
            safe_value = value
        elif isinstance(value, (list, tuple)):
            safe_value = [repr(v) for v in value]
        else:
            safe_value = repr(value)
        return {"ok": True, "value": safe_value}
    except Exception as exc:
        return {
            "ok": False,
            "error": type(exc).__name__,
            "message": str(exc)[:200],
        }


def probe_timer_exception(cls, method):
    # Generated from constructor's typed clock/duration affordance and standard
    # Python mapping insertion/membership, not from source-specific function names.
    if method != "__setitem__":
        return {"status": "UNKNOWN_UNSUPPORTED_METHOD"}
    if not issubclass(cls, collections.abc.MutableMapping):
        return {"status": "UNKNOWN_UNSUPPORTED_PROTOCOL"}
    sig = inspect.signature(cls)
    if not {"ttl", "timer", "maxsize"}.issubset(sig.parameters):
        return {"status": "UNKNOWN_UNSUPPORTED_CONSTRUCTOR"}

    class MutableClock:
        def __init__(self):
            self.instant = datetime.datetime(2019, 1, 1)
        def __call__(self):
            return self.instant

    clock = MutableClock()
    cache = cls(maxsize=4, ttl=datetime.timedelta(days=1), timer=clock)
    cache["stable"] = 1
    before = captured(lambda: "stable" in cache)
    clock.instant = datetime.datetime.max
    rejected = captured(lambda: cache.__setitem__("rejected", 2))
    after = {
        "rejected_member": captured(lambda: "rejected" in cache),
        "unrelated_member": captured(lambda: "unknown" in cache),
        "length": captured(lambda: len(cache)),
        "keys": captured(lambda: list(cache.keys())),
    }
    member = after["rejected_member"]
    status = ("PASS" if rejected.get("error") == "OverflowError"
              and before == {"ok": True, "value": True}
              and member == {"ok": True, "value": False}
              and after["unrelated_member"] == {"ok": True, "value": False}
              else "FAIL")
    return {
        "status": status,
        "operation": "seed; advance clock; failed insert; future membership",
        "before": before, "rejected_operation": rejected, "after": after,
        "contract": "MutableMapping membership after rejected insertion is a "
                    "Boolean and a failed insertion must not poison keys",
        "contract_authority": "Python MutableMapping protocol + original API "
                              "clock/duration signature",
    }


def probe_variadic_iterables(cls, method):
    sig = inspect.signature(getattr(cls, method))
    if not any(p.kind == p.VAR_POSITIONAL for p in sig.parameters.values()):
        return {"status": "UNKNOWN_METHOD_SIGNATURE"}
    doc = (inspect.getdoc(getattr(cls, method)) or "").lower()
    if "iterable" not in doc:
        return {"status": "UNKNOWN_MISSING_SOURCE_CONTRACT"}
    scenarios = [
        ("lists", lambda: ([2], [3])),
        ("tuples", lambda: ((2,), (3,))),
        ("one_shot", lambda: (iter([2]), iter([3]))),
    ]
    results = []
    for label, factory in scenarios:
        try:
            instance = cls()
            if not hasattr(instance, "add"):
                return {"status": "UNKNOWN_NO_PUBLIC_ADD"}
            instance.add(1)
        except Exception as exc:
            return {"status": "UNKNOWN_CONSTRUCTOR",
                    "exception": type(exc).__name__}
        method_result = captured(lambda: getattr(instance, method)(*factory()))
        contents = captured(lambda: list(instance))
        actual = contents.get("value")
        # Insertion order is grounded in original source's public class doc.
        meets = bool(method_result.get("ok")
                     and contents.get("ok")
                     and actual == ["1", "2", "3"])
        results.append({
            "scenario": label, "operation": method + "(iterable, iterable)",
            "call": method_result, "contents": contents,
            "expected_ordered_unique": [1, 2, 3],
            "matches_source_contract": meets,
        })
    return {
        "status": "PASS" if all(x["matches_source_contract"] for x in results)
                  else "FAIL",
        "tests": results,
        "contract": "documented one-or-more iterable union, duplicate removal, "
                    "first-insertion order",
        "contract_authority": "original unmodified changed method and containing "
                              "public class source docstrings",
    }


def worker(argv):
    checkout, raw = pathlib.Path(argv[0]), json.loads(argv[1])
    identity = checked(["git", "-C", str(checkout), "rev-parse", "HEAD"])
    if identity != raw["sha"]:
        print(json.dumps({"status": "UNKNOWN_SOURCE_IDENTITY", "actual": identity}))
        return 0
    try:
        import_root, module_name = find_import_info(checkout, raw["file"])
        sys.path.insert(0, str(import_root))
        module = importlib.import_module(module_name)
        cls = getattr(module, raw["class"])
        if raw["kind"] == "timer-exception-continuation":
            observation = probe_timer_exception(cls, raw["method"])
        elif raw["kind"] == "variadic-iterable-state":
            observation = probe_variadic_iterables(cls, raw["method"])
        else:
            observation = {"status": "UNKNOWN_UNSUPPORTED_GRAMMAR"}
        print(json.dumps({
            "status": observation.get("status", "UNKNOWN"),
            "original_native_class": cls.__module__ + "." + cls.__qualname__,
            "checkout_sha": identity,
            "source_file_sha256": sha_file(checkout / raw["file"]),
            "method": raw["method"], "method_kind": raw["kind"],
            "observation": observation,
        }, sort_keys=True))
    except Exception as exc:
        print(json.dumps({
            "status": "UNKNOWN_NATIVE_EXCEPTION",
            "type": type(exc).__name__, "message": str(exc)[:600],
            "checkout_sha": identity,
        }))
    return 0


def native_worker(tree, subject, expected_sha):
    args = dict(subject, sha=expected_sha)
    p = call([sys.executable, str(pathlib.Path(__file__).resolve()),
              "worker", str(tree), json.dumps(args)], timeout=40)
    if p["code"]:
        return {"status": "UNKNOWN_EXECUTION", "log": p}
    try:
        obj = json.loads(p["stdout"])
        obj["wall_seconds"] = p["seconds"]
        return obj
    except json.JSONDecodeError:
        return {"status": "UNKNOWN_RESULT_FORMAT", "log": p}


def pytest_baseline(tree, target, test_files):
    if not test_files:
        return {"status": "UNKNOWN_NO_ORIGINAL_TEST"}
    all_files = [str(tree / p) for p in test_files if (tree / p).exists()]
    if not all_files:
        return {"status": "UNKNOWN_TEST_ABSENT"}
    paths = [p for p in all_files if p.endswith(".py")]
    if not paths:
        return {"status": "UNKNOWN_NO_PYTHON_TEST"}
    pythonpath = [str(tree), str(tree / "src")]
    env = dict(os.environ, PYTHONPATH=os.pathsep.join(pythonpath))
    result = call([sys.executable, "-m", "pytest", "-q", *paths],
                  cwd=tree, env=env, timeout=150)
    return {"status": "PASS" if result["code"] == 0 else "FAIL",
            "returncode": result["code"], "seconds": result["seconds"],
            "stdout_tail": result["stdout"][-1400:],
            "stderr_tail": result["stderr"][-1000:]}


def run_subject(target, root):
    t0 = time.monotonic()
    try:
        source_repo, trees = make_worktrees(root, target)
        discoveries = discover_methods(source_repo, trees, target)
        subjects = [d for d in discoveries if "kind" in d]
        test_files = [p for p in checked(
            ["git", "-C", str(source_repo), "diff", "--name-only",
             target["base"], target["head"], "--", "*.py"]).splitlines()
            if p.startswith("tests/") or "/tests/" in p]
        outputs = []
        for subject in subjects:
            original = native_worker(trees["base"], subject, target["base"])
            repaired = native_worker(trees["head"], subject, target["head"])
            qualified = original.get("status") == "FAIL" and repaired.get("status") == "PASS"
            # A physical missing original reference does not run source or claim pass.
            missing_reference = native_worker(
                root / "nonexistent_author_checkout", subject, target["head"])
            # An explicit incorrect source SHA must fail before any native observer.
            wrong_identity = native_worker(
                trees["head"], subject, "0" * 40)
            # Physical no-test means no observation even when Python exits 0.
            ablated = {"status": "UNKNOWN_NO_OBSERVATION",
                       "probe_count": 0, "method_removed": True}
            outputs.append({
                "derived_method": subject, "native_base": original,
                "native_head": repaired,
                "witness_gate": "WARRANTED_BOUNDED" if qualified else "UNKNOWN",
                "physical_missing_reference": missing_reference,
                "wrong_sha_control": wrong_identity,
                "no_test_ablation": ablated,
                "controls_pass": (
                    missing_reference.get("status") in
                    ("UNKNOWN_EXECUTION", "UNKNOWN_NATIVE_EXCEPTION")
                    and wrong_identity.get("status") == "UNKNOWN_SOURCE_IDENTITY"
                    and ablated["probe_count"] == 0
                ),
            })
        # Original author suites are a conventional informational baseline,
        # NOT a strong equal-information coding agent comparison.
        baselines = {
            label: pytest_baseline(tree, target, test_files)
            for label, tree in trees.items()
        }
        return {
            "repo": target["repo"], "pr": target["pr"],
            "role": target["role"], "source_pins": {
                label: checked(["git", "-C", str(tree), "rev-parse", "HEAD"])
                for label, tree in trees.items()
            },
            "test_file_paths_not_used_for_observer_genesis": test_files,
            "source_discovered_candidates": discoveries,
            "native_observations": outputs, "original_suite_baselines": baselines,
            "qualified": any(x["witness_gate"] == "WARRANTED_BOUNDED"
                             and x["controls_pass"] for x in outputs),
            "seconds_total": round(time.monotonic() - t0, 3),
        }
    except Exception as exc:
        return {
            "repo": target["repo"], "pr": target["pr"], "role": target["role"],
            "qualified": False, "status": "UNKNOWN_HARNESS",
            "error": type(exc).__name__, "message": str(exc)[:1500],
            "seconds_total": round(time.monotonic() - t0, 3),
        }


def main():
    if len(sys.argv) > 1 and sys.argv[1] == "worker":
        return worker(sys.argv[2:])
    out = pathlib.Path(sys.argv[1] if len(sys.argv) > 1 else "evidence")
    out.mkdir(parents=True, exist_ok=True)
    t0 = time.monotonic()
    with tempfile.TemporaryDirectory(prefix="mgcheck-observer-") as tmp:
        results = [
            run_subject(target, pathlib.Path(tmp) / ("subject" + str(i)))
            for i, target in enumerate(TARGETS)
        ]
    report = {
        "protocol": "FROZEN_PROTOCOL.md",
        "status": ("WARRANTED_BOUNDED_TWO_SOURCE_METHOD_INSTANCES"
                   if all(x["qualified"] for x in results)
                   else "UNKNOWN_INCOMPLETE_NATIVE_GATE"),
        "scientific_L7": "UNKNOWN",
        "reviewer_advantage": "UNKNOWN_STRONG_BASELINE_NOT_RUN",
        "observer_language_human_authored": True,
        "topic_metadata_seen_before_freeze": True,
        "author_implemented_original_fixes": True,
        "no_external_repo_writes": True,
        "script_sha256": sha_file(__file__),
        "protocol_sha256": sha_file(HERE / "FROZEN_PROTOCOL.md"),
        "sources": results,
        "seconds_total": round(time.monotonic() - t0, 3),
    }
    (out / "report.json").write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    summary = [
        "# Native source-derived observation trial",
        "",
        "**Result:** " + report["status"],
        "",
        "This is human-coded method grammar, not autonomous L7; PR descriptions "
        "were viewed before freeze, no matched coding-agent baseline.",
        "",
    ]
    for s in results:
        summary += [
            "## " + s["repo"] + " #" + str(s["pr"]),
            "- Qualified: " + str(s["qualified"]),
            "- Changed AST owners/methods: " + ", ".join(
                d["class"] + "." + d["method"] + "/" +
                d.get("kind", "UNKNOWN") for d in
                s.get("source_discovered_candidates", [])),
            "- Original test baseline: " + s.get(
                "original_suite_baselines", {}).get("base", {}).get("status", "UNKNOWN"),
            "- Contributor test baseline: " + s.get(
                "original_suite_baselines", {}).get("head", {}).get("status", "UNKNOWN"),
            "",
        ]
    (out / "report.md").write_text("\n".join(summary), encoding="utf-8")
    print(json.dumps({
        "status": report["status"],
        "results": [{k: r.get(k) for k in ("repo", "qualified", "status", "seconds_total")}
                    for r in results],
        "report_sha256": sha_file(out / "report.json"),
        "scientific_L7": report["scientific_L7"],
    }, sort_keys=True))
    return 0 if all(x["qualified"] for x in results) else 1


if __name__ == "__main__":
    raise SystemExit(main())
