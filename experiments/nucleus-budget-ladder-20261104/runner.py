#!/usr/bin/env python3
"""Only resource-budget changes against the next authentic Nat.beq_refl prefix.

An ACCEPT here is a causal source-prefix result. It never means all Mathlib
accepted and never authorizes persistent MGSO graph or cache work-skipping.
"""

import difflib
import hashlib
import importlib.util
import json
import os
import shutil
from pathlib import Path


ROOT = Path(__file__).resolve().parent
EXPERIMENTS = ROOT.parent
PREFIX_SHA = "d1c35f6a0de8644817b404e225a16de460e897e0b34c129fcb2a37483e630738"
BASE_PATCH_SHA = "9d55735a77d69febdfb0b3d02ee1d5d29bb98011c9e534c17e25ca0f661bbfaa"
BUDGET4X_PATCH_SHA = "203de44b272d3f0d524e6dff8a25aaddee06d291ca565a0123d2694ca0bdd719"
BUDGET4X_BINARY_SHA = "659d68f956fefac853e3b4b9c6a402a317de362588f3ddc7962e950cfce8161a"


def patch_budget(text, budget):
    old = "judgment_steps: 65_536,"
    if text.count(old) != 1 or budget not in (262_144, 524_288, 1_048_576):
        raise ValueError("unknown judgment-budget edit; stop before changing kernel")
    changed = text.replace(old, f"judgment_steps: {budget:_},")
    diff = "".join(difflib.unified_diff(
        text.splitlines(keepends=True), changed.splitlines(keepends=True),
        fromfile="a/metatron-kernel/src/checker.rs",
        tofile="b/metatron-kernel/src/checker.rs",
    ))
    return changed, diff


def main():
    # Import the original parent causal machinery only after test discovery.
    spec = importlib.util.spec_from_file_location(
        "budget_ladder_let", EXPERIMENTS / "nucleus-let-preservation-20261104" / "runner.py")
    let = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(let)
    tournament, runtime = let.t, let.R.N.runtime(True)
    flags = {key: val for key, val in runtime.items() if key.startswith("NUCLEUS_")}
    if len(flags) != 20 or any(val != "1" for val in flags.values()):
        raise ValueError("source-prefix runtime flags diverged")
    runtime["NUCLEUS_TRACE_DOWNSTREAM"] = "1"

    out = Path("/tmp/budget-ladder/evidence")
    out.mkdir(parents=True, exist_ok=True)
    prefix = Path("/tmp/budget-ladder/nat-prefix.ndjson")
    if tournament.digest(prefix) != PREFIX_SHA:
        raise ValueError("Nat.beq_refl source prefix is not exact")
    baseline = Path("/tmp/budget-ladder/baseline/nucleus")
    source_patch = Path("/tmp/budget-ladder/baseline/source.patch")
    if tournament.digest(baseline) != BUDGET4X_BINARY_SHA \
            or tournament.digest(source_patch) != BUDGET4X_PATCH_SHA:
        raise ValueError("not the exact winning Range-prefix binary")
    baseline.chmod(0o755)

    arm = out / "base-source"
    kernel = let.materialize(arm, True)
    owner_patch = EXPERIMENTS / "nucleus-let-index-stack-20261104" / "owner-index.patch"
    applied = tournament.run_group(
        ["patch", "--batch", "--fuzz=0", "-p1", "-i", str(owner_patch)],
        cwd=arm, timeout=30, capture_output=True)
    if applied.returncode:
        raise ValueError("indexed Let source patch no longer applies")
    with (arm / "source.patch").open("a") as file:
        file.write(owner_patch.read_text())
    if tournament.digest(arm / "source.patch") != BASE_PATCH_SHA:
        raise ValueError("base source digest differs from causal tournament")
    checker = (kernel / "src/checker.rs").read_text()
    budget4x, diff4x = patch_budget(checker, 262_144)
    reproduced_sha = hashlib.sha256(((arm / "source.patch").read_text() + diff4x).encode()).hexdigest()
    if reproduced_sha != BUDGET4X_PATCH_SHA or "judgment_steps: 262_144" not in budget4x:
        raise ValueError("failed to reconstruct exact budget4x source")

    def observe(label, binary):
        directory = out / label
        directory.mkdir(exist_ok=True)
        result = tournament.measure(binary, prefix, runtime, directory, timeout=300, perf=False)
        lines = (directory / "stderr").read_text(errors="replace").splitlines()
        terminal = [line for line in lines if line.startswith("NUCLEUS_DOWNSTREAM:")]
        return dict(result=result, binary_sha256=tournament.digest(binary),
                    terminal=terminal[-1] if terminal else None)

    base = observe("baseline-4x", baseline)
    if base["result"]["rc"] != 2 or "Nat.beq_refl" not in (base["terminal"] or ""):
        raise ValueError("original Nat.beq_refl frontier did not reproduce")
    reports = [dict(arm="budget4x", **base)]
    for name, budget in (("budget8x", 524_288), ("budget16x", 1_048_576)):
        directory = out / name
        directory.mkdir(exist_ok=True)
        implementation = directory / "metatron-kernel"
        shutil.copytree(kernel, implementation)
        changed, patch = patch_budget(checker, budget)
        (implementation / "src/checker.rs").write_text(changed)
        (directory / "candidate.patch").write_text(patch)
        (directory / "source.patch").write_text((arm / "source.patch").read_text() + patch)
        env = dict(os.environ, CARGO_TARGET_DIR=str(out / "shared-target"))
        built = tournament.run_group(
            ["cargo", "build", "--release", "--locked",
             "--manifest-path", str(implementation / "Cargo.toml")],
            capture_output=True, timeout=600, env=env)
        (directory / "build.log").write_bytes(built.stdout + built.stderr)
        if built.returncode != 0:
            reports.append(dict(arm=name, budget=budget, build_rc=built.returncode))
            tournament.write_json(out / "screen.json", reports)
            continue
        binary = directory / "nucleus"
        shutil.copy2(out / "shared-target/release/metatron-kernel", binary)
        native = tournament.run_group(
            ["cargo", "test", "--release", "--locked", "--lib", "--manifest-path",
             str(implementation / "Cargo.toml")],
            capture_output=True, timeout=600, env=env | runtime)
        (directory / "native-lib.log").write_bytes(native.stdout + native.stderr)
        row = dict(arm=name, budget=budget, native_lib_rc=native.returncode,
                   source_patch_sha256=tournament.digest(directory / "source.patch"),
                   **observe(name, binary))
        reports.append(row)
        tournament.write_json(out / "screen.json", dict(
            arms=reports, source_sha256=PREFIX_SHA,
            experimental_flags=flags, full_mathlib_accept="UNKNOWN",
            source_only=True, persistent_cache_skips=0))
        print(json.dumps(row, sort_keys=True), flush=True)
    shutil.rmtree(out / "shared-target", ignore_errors=True)
    print(json.dumps(dict(arms=reports, scope="Nat.beq_refl prefix only"), sort_keys=True), flush=True)


if __name__ == "__main__":
    main()
