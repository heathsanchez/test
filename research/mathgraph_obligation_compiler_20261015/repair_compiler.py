#!/usr/bin/env python3
"""Source-AST candidate repairs with independently re-executed native controls.

Not L7: both repair constructor families were human written and predeclared
in FROZEN_REPAIR_PROTOCOL.md before this file. No original author patch copied.
"""
from __future__ import annotations

import ast
import hashlib
import json
import os
import pathlib
import re
import subprocess
import sys
import tempfile
import time

import observer_genesis as obs

HERE = pathlib.Path(__file__).resolve().parent


def locate_method(text, discovered):
    tree = ast.parse(text)
    matches = []
    for owner in tree.body:
        if not isinstance(owner, ast.ClassDef):
            continue
        if owner.name != discovered["class"]:
            continue
        for method in owner.body:
            if isinstance(method, (ast.FunctionDef, ast.AsyncFunctionDef)):
                if method.name == discovered["method"]:
                    matches.append((tree, owner, method))
    if len(matches) != 1:
        raise ValueError("UNKNOWN_AMBIGUOUS_METHOD_OWNER")
    return matches[0]


def replace_ast_segment(text, node, replacement):
    if node.lineno != node.end_lineno:
        raise ValueError("UNKNOWN_MULTILINE_SOURCE_EXPRESSION")
    lines = text.splitlines(keepends=True)
    ix = node.lineno - 1
    line = lines[ix]
    if node.end_col_offset <= node.col_offset:
        raise ValueError("UNKNOWN_SOURCE_SPAN")
    lines[ix] = (line[:node.col_offset] + replacement +
                 line[node.end_col_offset:])
    return "".join(lines)


def candidate_hoist_exception_expr(source, subject):
    tree, owner, method = locate_method(source, subject)
    withs = [
        n for n in ast.walk(method)
        if isinstance(n, ast.With)
        and len(n.items) == 1
        and isinstance(n.items[0].optional_vars, ast.Name)
        and n.body
    ]
    candidates = []
    for node in withs:
        bound_clock = node.items[0].optional_vars.id
        for later in ast.walk(method):
            if not isinstance(later, ast.Assign):
                continue
            if later.lineno <= node.end_lineno:
                continue
            if not any(isinstance(t, ast.Attribute) for t in later.targets):
                continue
            rhs = later.value
            if not isinstance(rhs, ast.BinOp):
                continue
            if not isinstance(rhs.op, ast.Add):
                continue
            read_names = {
                n.id for n in ast.walk(rhs) if isinstance(n, ast.Name)
            }
            if not {bound_clock, "self"}.issubset(read_names):
                continue
            # Candidate needs only source-bound values already in scope at
            # start of the with-block, not a value assigned by mutation.
            if read_names - {bound_clock, "self"}:
                continue
            candidates.append((node, later))
    if len(candidates) != 1:
        raise ValueError("UNKNOWN_NO_UNIQUE_EXCEPTION_HOIST")

    context, assignment = candidates[0]
    original_rhs = ast.get_source_segment(source, assignment.value)
    if not original_rhs:
        raise ValueError("UNKNOWN_UNREADABLE_RHS")
    tempvar = "_mgcheck_prechecked_value"
    if tempvar in source:
        raise ValueError("UNKNOWN_FRESH_NAME")
    # First compile the expression in its original lexical scope; no
    # expression is re-created from head patch bytes.
    replaced = replace_ast_segment(source, assignment.value, tempvar)
    lines = replaced.splitlines(keepends=True)
    anchor = context.body[0].lineno - 1
    indent = re.match(r"^\s*", lines[anchor]).group()
    lines.insert(anchor, indent + tempvar + " = " + original_rhs + "\n")
    patched = "".join(lines)
    compile(patched, "<candidate>", "exec")
    return patched, {
        "repair_rule": "exceptional-expression-before-mutation",
        "source_method": method.name,
        "original_expr": original_rhs,
        "new_var": tempvar,
        "source_line": assignment.lineno,
    }


def candidate_flatten_variadic(source, subject):
    tree, owner, method = locate_method(source, subject)
    if not method.args.vararg:
        raise ValueError("UNKNOWN_NOT_VARIADIC")
    vararg_name = method.args.vararg.arg
    doc = (ast.get_docstring(method) or "").lower()
    if "iterable" not in doc:
        raise ValueError("UNKNOWN_NO_SOURCE_DOC_CONTRACT")
    allowed = set()
    for node in tree.body:
        if isinstance(node, ast.ImportFrom) and node.module == "itertools":
            for alias in node.names:
                if alias.name == "chain":
                    allowed.add(alias.asname or alias.name)
    candidates = []
    for node in ast.walk(method):
        if not isinstance(node, ast.Call) or len(node.args) != 1:
            continue
        if not (isinstance(node.func, ast.Name)
                and node.func.id in allowed):
            continue
        if not (isinstance(node.args[0], ast.Name)
                and node.args[0].id == vararg_name):
            continue
        if node.keywords:
            continue
        candidates.append(node)
    if len(candidates) != 1:
        raise ValueError("UNKNOWN_NO_UNIQUE_VARIADIC_FLATTEN")
    source_node = candidates[0]
    replacement = (ast.get_source_segment(source, source_node.func)
                   + ".from_iterable(" + vararg_name + ")")
    patched = replace_ast_segment(source, source_node, replacement)
    compile(patched, "<candidate>", "exec")
    return patched, {
        "repair_rule": "one-level-iterable-flatten",
        "source_line": source_node.lineno,
        "original_expr": ast.get_source_segment(source, source_node),
        "replacement_expr": replacement,
        "vararg_kind": "VAR_POSITIONAL",
    }


def synthesize(source, subject):
    if subject["kind"] == "timer-exception-continuation":
        return candidate_hoist_exception_expr(source, subject)
    if subject["kind"] == "variadic-iterable-state":
        return candidate_flatten_variadic(source, subject)
    raise ValueError("UNKNOWN_UNSUPPORTED_REPAIR_GRAMMAR")


def native_rerun(worktree, subject, sha):
    return obs.native_worker(worktree, subject, sha)


def original_test_files(repo, target):
    text = obs.checked(["git", "-C", str(repo), "diff", "--name-only",
                        target["base"], target["head"], "--", "*.py"])
    return [p for p in text.splitlines()
            if p.startswith("tests/") or "/tests/" in p]


def repair_subject(target, workspace, out):
    started = time.monotonic()
    out.mkdir(parents=True, exist_ok=True)
    try:
        gitdir, trees = obs.make_worktrees(workspace, target)
        candidates = [
            x for x in obs.discover_methods(gitdir, trees, target)
            if "kind" in x
        ]
        test_files = original_test_files(gitdir, target)
        experiments = []
        for subject in candidates:
            code_path = trees["base"] / subject["file"]
            original_bytes = code_path.read_bytes()
            native_original = native_rerun(trees["base"], subject, target["base"])
            native_author = native_rerun(trees["head"], subject, target["head"])
            if not (native_original.get("status") == "FAIL"
                    and native_author.get("status") == "PASS"):
                experiments.append({
                    "subject": subject, "status": "UNKNOWN_WITNESS_NOT_REPRODUCED",
                    "original": native_original, "author_head": native_author})
                continue
            try:
                proposed, generator_receipt = synthesize(
                    original_bytes.decode("utf-8"), subject)
            except Exception as exc:
                experiments.append({
                    "subject": subject, "status": "UNKNOWN_REPAIR_GENERATOR",
                    "error": str(exc)[:600]})
                continue
            proposed_bytes = proposed.encode("utf-8")
            if proposed_bytes == original_bytes:
                experiments.append({
                    "subject": subject, "status": "UNKNOWN_IDENTITY_PATCH"})
                continue

            before_sha = hashlib.sha256(original_bytes).hexdigest()
            patch_sha = hashlib.sha256(proposed_bytes).hexdigest()
            actual_original_blob = obs.checked([
                "git", "-C", str(trees["base"]), "hash-object",
                str(code_path)])
            code_path.write_bytes(proposed_bytes)
            diff = obs.checked(["git", "-C", str(trees["base"]), "diff",
                                "--", subject["file"]])
            patch_path = out / (
                target["repo"].replace("/", "_") + "_" +
                generator_receipt["repair_rule"] + ".patch")
            patch_path.write_text(diff + "\n", encoding="utf-8")
            try:
                native_patched = native_rerun(
                    trees["base"], subject, target["base"])
                suite_patched = obs.pytest_baseline(
                    trees["base"], target, test_files)
            finally:
                # Actual removal: exact original base file bytes, followed by
                # a fresh independent original-native probe process.
                code_path.write_bytes(original_bytes)
            native_removed = native_rerun(
                trees["base"], subject, target["base"])
            restored_bytes = code_path.read_bytes()
            code_path.write_bytes(proposed_bytes)
            unchanged_patch_digest = (
                hashlib.sha256(code_path.read_bytes()).hexdigest() == patch_sha
            )
            code_path.write_bytes(original_bytes)
            repaired = (
                native_patched.get("status") == "PASS"
                and suite_patched.get("status") == "PASS"
                and native_removed.get("status") == "FAIL"
                and restored_bytes == original_bytes
                and unchanged_patch_digest
            )
            experiments.append({
                "subject": subject,
                "status": ("WARRANTED_BOUNDED_SOURCE_NATIVE_REPAIR"
                           if repaired else "REJECTED_OR_UNKNOWN_REPAIR"),
                "generator_receipt": generator_receipt,
                "original_clean_sha256": before_sha,
                "original_git_blob": actual_original_blob,
                "candidate_source_sha256": patch_sha,
                "candidate_patch_sha256": obs.sha_file(patch_path),
                "candidate_patch_path": patch_path.name,
                "native_original": native_original,
                "native_author_head": native_author,
                "native_generated_repair": native_patched,
                "native_after_physical_patch_removal": native_removed,
                "original_native_suite_on_generated_patch": suite_patched,
                "physical_restoration_byte_identical": restored_bytes == original_bytes,
                "candidate_replay_byte_identical": unchanged_patch_digest,
                "source_clean_after_trial": code_path.read_bytes() == original_bytes,
                "qualified": repaired,
            })
        report = {
            "repo": target["repo"], "role": target["role"],
            "original_source": target["base"], "author_head": target["head"],
            "derived_without_named_target_method": True,
            "source_pins": {
                label: obs.checked(["git", "-C", str(tree), "rev-parse", "HEAD"])
                for label, tree in trees.items()
            },
            "original_test_files_discovered_not_transplanted": test_files,
            "repair_candidates": experiments,
            "qualified": any(e.get("qualified") for e in experiments),
            "seconds": round(time.monotonic() - started, 3),
        }
        return report
    except Exception as exc:
        return {
            "repo": target["repo"], "qualified": False,
            "status": "UNKNOWN_REPAIR_HARNESS",
            "type": type(exc).__name__, "exception": str(exc)[:1100],
            "seconds": round(time.monotonic() - started, 3),
        }


def main():
    out = pathlib.Path(sys.argv[1] if len(sys.argv) > 1 else "repair-evidence")
    out.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="mgcheck-repair-native-") as work:
        result = [
            repair_subject(target, pathlib.Path(work) / ("subject" + str(i)),
                           out)
            for i, target in enumerate(obs.TARGETS)
        ]
    report = {
        "status": ("WARRANTED_BOUNDED_TWO_NATIVE_HUMAN_GRAMMAR_REPAIRS"
                   if all(x["qualified"] for x in result)
                   else "UNKNOWN_OR_REJECTED_REPAIR_GATE"),
        "contract_is_not_universal": True,
        "generator_language_was_human_coded": True,
        "author_patch_was_not_read_by_generator": True,
        "no_upstream_writes": True,
        "scientific_L7": "UNKNOWN",
        "full_equal_information_coding_agent_baseline": "NOT_RUN",
        "protocol_sha256": obs.sha_file(HERE / "FROZEN_REPAIR_PROTOCOL.md"),
        "source_sha256": obs.sha_file(__file__),
        "repos": result,
    }
    report_path = out / "repair_report.json"
    report_path.write_text(
        json.dumps(report, sort_keys=True, indent=2) + "\n",
        encoding="utf-8")
    print(json.dumps({
        "status": report["status"],
        "repo_results": [
            {
                "repo": r["repo"], "qualified": r["qualified"],
                "native": [
                    {k: e.get(k) for k in (
                        "status", "qualified", "candidate_patch_sha256")}
                    for e in r.get("repair_candidates", [])
                ]}
            for r in result],
        "report_sha256": obs.sha_file(report_path),
        "scientific_L7": report["scientific_L7"],
    }, sort_keys=True))
    return 0 if all(r["qualified"] for r in result) else 1


if __name__ == "__main__":
    raise SystemExit(main())
