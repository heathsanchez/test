#!/usr/bin/env python3
"""Surgical, source-pinned reuse of three historical Nucleus proof rules.

This is an isolated experimental patcher. It deliberately does not copy whole
files or silently adjust anchors after upstream drift. The historical source
is fetched from a full local Git checkout at the pinned commit below.
"""

import argparse
import difflib
import subprocess
from pathlib import Path

LEGACY_REF = "1a2e50777c596e20a7d2dd2fa0e591c1ab8ecfc4"


def extract_method(src: str, name: str) -> str:
    needle = "    " + name
    assert src.count(needle) == 1, (name, src.count(needle))
    start = src.index(needle)
    brace = src.index("{", start)
    depth = 0
    for index in range(brace, len(src)):
        if src[index] == "{":
            depth += 1
        elif src[index] == "}":
            depth -= 1
            if depth == 0:
                return src[start : index + 1]
    raise AssertionError("unclosed Rust method " + name)


def once(src: str, old: str, new: str, label: str) -> str:
    assert src.count(old) == 1, (label, src.count(old))
    return src.replace(old, new, 1)


def legacy_source(repo: Path, filename: str) -> str:
    return subprocess.check_output(
        ["git", "show", f"{LEGACY_REF}:metatron-kernel/src/{filename}"],
        cwd=repo,
        text=True,
    )


def port(repo: Path, kernel: Path, patch_path: Path) -> None:
    old = {name: legacy_source(repo, name) for name in ("typecheck.rs", "convert.rs", "machine.rs")}
    target = {name: (kernel / "src" / name).read_text() for name in old}
    updated = dict(target)

    for method in (
        "pub(crate) fn certified_distinct_source_proofs(",
        "pub(crate) fn certified_neutral_lambda_proof_irrelevance(",
    ):
        body = extract_method(old["typecheck.rs"], method)
        assert method not in updated["typecheck.rs"]
        anchor = "    pub(crate) fn checked_captured_prop_type_in_context("
        updated["typecheck.rs"] = once(
            updated["typecheck.rs"], anchor, body + "\n\n" + anchor, method
        )

    machine_method = extract_method(
        old["machine.rs"], "pub(crate) fn qualified_quotient_neutral_result("
    )
    assert "pub(crate) fn qualified_quotient_neutral_result(" not in updated["machine.rs"]
    anchor = "    fn try_quot_reduction("
    updated["machine.rs"] = once(
        updated["machine.rs"], anchor, machine_method + "\n\n" + anchor,
        "quotient-neutral replay",
    )
    # Retain the existing optimized evaluator, replacing only its Quot.iota
    # method. Its explicit budget argument is restored at the single callsite.
    updated["machine.rs"] = once(
        updated["machine.rs"],
        extract_method(updated["machine.rs"], "fn try_quot_reduction("),
        extract_method(old["machine.rs"], "fn try_quot_reduction("),
        "registered Quot.iota",
    )
    updated["machine.rs"] = once(
        updated["machine.rs"],
        "self.try_quot_reduction(*name, levels, &mut pending)",
        "self.try_quot_reduction(*name, levels, &mut pending, budget)",
        "Quot.iota budget callsite",
    )

    old_convert = old["convert.rs"]
    start = "                // The original closure machine can leave a registered\n"
    end = "                // A registered recursor with an actual constructor major is\n"
    assert old_convert.count(start) == 1 and old_convert.count(end) == 1
    quot_block = old_convert[old_convert.index(start) : old_convert.index(end)]
    updated["convert.rs"] = once(
        updated["convert.rs"], end, quot_block + end, "certified Quot.iota replay",
    )

    start = "                if checker.certified_distinct_source_proofs(\n"
    end = "                if certified_structure_eta(\n"
    assert old_convert.count(start) == 1 and old_convert.count(end) == 1
    distinct_block = old_convert[old_convert.index(start) : old_convert.index(end)]
    updated["convert.rs"] = once(
        updated["convert.rs"], end, distinct_block + end,
        "source-typed distinct proof neutrals",
    )

    start = "            (Value::Neutral(neutral), Value::Lam { domain, body })\n"
    old_pos = old_convert.index("checker.certified_neutral_lambda_proof_irrelevance(")
    old_arm_start = old_convert.rfind(start, 0, old_pos)
    old_arm_end = old_convert.index("            _ => {", old_pos)
    lambda_block = old_convert[old_arm_start:old_arm_end]
    assert lambda_block.count("certified_neutral_lambda_proof_irrelevance") == 1
    # The existing evaluated_free_eta arm directly precedes the fallback arm.
    pattern = (
        "                    context,\n"
        "                ) => {}\n"
        "            _ => {"
    )
    updated["convert.rs"] = once(
        updated["convert.rs"], pattern,
        pattern.replace("            _ => {", lambda_block + "            _ => {"),
        "source-typed neutral/lambda proof irrelevance",
    )

    diffs = []
    for name in old:
        file = kernel / "src" / name
        diffs.extend(
            difflib.unified_diff(
                target[name].splitlines(keepends=True),
                updated[name].splitlines(keepends=True),
                fromfile="a/metatron-kernel/src/" + name,
                tofile="b/metatron-kernel/src/" + name,
            )
        )
    assert all(updated[name] != target[name] for name in old)
    patch_path.write_text("".join(diffs))
    for name in old:
        (kernel / "src" / name).write_text(updated[name])


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo", type=Path, default=Path.cwd())
    parser.add_argument("--kernel", type=Path, required=True)
    parser.add_argument("--patch", type=Path, required=True)
    args = parser.parse_args()
    port(args.repo.resolve(), args.kernel.resolve(), args.patch.resolve())
