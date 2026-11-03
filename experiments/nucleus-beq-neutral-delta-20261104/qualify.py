"""Promote source-neutral delta only after protected native, corpus, and Mathlib replay.

The RED baseline and GREEN candidate share the complete dense+4x source
composition. The only candidate change is source-registered neutral delta.
"""

import difflib
import importlib.util
import json
from pathlib import Path
import re
import shutil
import subprocess


ROOT = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location("neutral_delta", ROOT / "runner.py")
D = importlib.util.module_from_spec(spec)
spec.loader.exec_module(D)
spec = importlib.util.spec_from_file_location(
    "budget_qual", ROOT.parent / "nucleus-budget4x-qualification-20261104/runner.py")
Q = importlib.util.module_from_spec(spec)
spec.loader.exec_module(Q)
L, R, t = D.L, D.R, D.t
BASE_SHA = "7897fdf50b447ec1bb38dd4a409d3a3bc690eeac7868d58848f6046b099684a6"
PREFIX_SHA = "d1c35f6a0de8644817b404e225a16de460e897e0b34c129fcb2a37483e630738"
OUT = Path("/tmp/nucleus-beq-neutral-delta-qualified")


def source_qualified_candidate(baseline):
    arm = OUT / "candidate"
    kernel = L.materialize(arm, True)
    for label in ("owner-index.patch", "tagged.patch", "dense.patch"):
        path = (ROOT.parent / "nucleus-dense-composition-20261104/dense.patch"
                if label == "dense.patch"
                else ROOT.parent / "nucleus-tagged-let-20261104" / label)
        r = t.run_group(["patch", "--batch", "--fuzz=0", "-p1", "-i", str(path)],
                        cwd=arm, capture_output=True, timeout=30)
        (arm / (label + ".log")).write_bytes(r.stdout + r.stderr)
        assert r.returncode == 0, (label, r.stdout, r.stderr)
        with (arm / "source.patch").open("a") as file:
            file.write(path.read_text())
    checker = kernel / "src/checker.rs"
    before = checker.read_text()
    assert before.count("judgment_steps: 65_536,") == 1
    after = before.replace("judgment_steps: 65_536,", "judgment_steps: 262_144,", 1)
    checker.write_text(after)
    with (arm / "source.patch").open("a") as file:
        file.write("".join(difflib.unified_diff(before.splitlines(True), after.splitlines(True),
            fromfile="a/metatron-kernel/src/checker.rs", tofile="b/metatron-kernel/src/checker.rs")))
    # Verify exact source-equivalence to already protected qualified 4x stack
    # BEFORE adding a single new source-neutral delta behavior.
    assert t.digest(arm / "source.patch") == baseline["source_patch_sha"]
    D.patch_source(kernel, arm)
    binary, build_env = t.build(kernel, arm)
    assert binary is not None, (arm / "build.log").read_text()[-6000:]
    return kernel, binary, build_env, arm


def main():
    OUT.mkdir(exist_ok=True)
    prior = Path("/tmp/dense-qualified")
    baseline = json.loads((prior / "qualification.json").read_text())["candidate"]
    assert baseline["qualified"]
    assert baseline["binary_sha"] == BASE_SHA
    assert len(baseline["native"]["targets"]) == 42
    assert len(baseline["controls"]) == 61
    assert all(x["pass_"] for x in baseline["controls"])
    original = prior / "candidate/nucleus"
    assert t.digest(original) == BASE_SHA
    original.chmod(0o755)
    run = R.N.runtime(True)
    assert {k: v for k, v in run.items() if k.startswith("NUCLEUS_")} == baseline["configuration"]
    run["NUCLEUS_TRACE_DOWNSTREAM"] = "1"
    source = Path("/tmp/beq-prefix.ndjson")
    assert t.digest(source) == PREFIX_SHA
    red = t.measure(original, source, run, OUT / "red", timeout=300, perf=False)
    assert red["rc"] == 2 and "Nat.beq_refl" in (OUT / "red/stderr").read_text(errors="replace")
    kernel, candidate, build_env, arm = source_qualified_candidate(baseline)
    proof_rows = Q.validate_proof_and_forgery(candidate, source, run, OUT)
    assert proof_rows[0]["rc"] == 0
    qualified_env = {key: value for key, value in run.items()
                     if key != "NUCLEUS_TRACE_DOWNSTREAM"}

    inputs = Path("/tmp/current208")
    extra = inputs / "inputs/good/perf/magma-list-pair-n21.ndjson"
    extra.parent.mkdir(parents=True, exist_ok=True)
    subprocess.run(["zstd", "-dq", "-f",
        str(ROOT.parent / "nucleus-coverage-evidence-20261104/inputs/magma-list-pair-n21.ndjson.zst"),
        "-o", str(extra)], check=True)
    assert t.digest(extra) == baseline["extra"]["input_sha"]
    native = t.native_suite(kernel, build_env | qualified_env |
                            {"NUCLEUS_FROZEN196": str(inputs / "inputs")}, arm)
    controls = L.controls(candidate, qualified_env)
    native_ok = R.N.Q.native_nonregression(native, baseline["native"])
    controls_ok = (sorted(map(Q.signature, controls))
                   == sorted(map(Q.signature, baseline["controls"])))
    old_rows = json.loads((prior / "candidate/verdicts.json").read_text())
    new_rows = t.replay(candidate,
        json.loads((inputs / "inputs-manifest.json").read_text()),
        inputs, qualified_env, arm / "verdicts.json")
    assert len(old_rows) == len(new_rows) == 208
    changes = []
    for before, after in zip(old_rows, new_rows):
        assert before["case"] == after["case"]
        assert before["sha256"] == after["sha256"]
        if before["rc"] != after["rc"]:
            changes.append({"case":before["case"], "before":before["rc"],
                            "after":after["rc"]})
    with extra.open("rb") as stream:
        extra_result = t.run_group([str(candidate)], stdin=stream,
            capture_output=True, env=qualified_env, timeout=180)
    extra_ok = extra_result.returncode == baseline["extra"]["rc"]
    admissible = (native_ok and controls_ok and not changes and extra_ok and
                  all(row["pass_"] for row in controls) and len(proof_rows) == 3)
    report = {"status":"WARRANTED_BOUNDED" if admissible else "CANDIDATE",
              "qualified":admissible, "baseline_binary":BASE_SHA,
              "binary_sha":t.digest(candidate), "source_patch_sha":t.digest(arm / "source.patch"),
              "source_sha":PREFIX_SHA,"red":red,"green":proof_rows,
              "native":native,"native_nonregression":native_ok,
              "controls":controls,"controls_unchanged":controls_ok,
              "verdict_changes":changes,"extra_unchanged":extra_ok,
              "configuration":baseline["configuration"],
              "boundary":"One source-registered evaluated-neutral delta fallback added to exact prequalified 4x dense checker; no new neutral equality rule"}
    t.write_json(OUT / "qualification.json", {"candidate":report})
    print("DELTA_QUALIFICATION",json.dumps({
        "qualified":admissible,"native_nonregression":native_ok,
        "controls_unchanged":controls_ok,"verdict_changes":changes,
        "extra_unchanged":extra_ok,"source_proof_rc":proof_rows[0]["rc"],
        "candidate_binary":report["binary_sha"],
        "source_patch_sha":report["source_patch_sha"]}),flush=True)
    if not admissible:
        t.write_json(OUT / "full.json", {"status":"NOT_RUN_PROTECTED_GATE_FAILED"})
        return

    full_source = Path("/tmp/mathlib.ndjson")
    assert t.digest(full_source) == t.INPUT_SHA
    result = t.measure(candidate, full_source, run, OUT / "full", timeout=1800, perf=False)
    traces = [line for line in (OUT / "full/stderr").read_text(errors="replace").splitlines()
              if line.startswith("NUCLEUS_DOWNSTREAM:")]
    terminal = traces[-1] if traces else None
    frontier = None
    if result["rc"] == 2 and terminal:
        match = re.search(r"NUCLEUS_DOWNSTREAM:name=(.*?):stage=", terminal)
        if match and not match.group(1).startswith("<"):
            extracted = R.E.extract(full_source, OUT / "next-frontier.ndjson", match.group(1))
            subprocess.run(["zstd", "-T0", "-3", str(OUT / "next-frontier.ndjson")],
                check=True)
            (OUT / "next-frontier.ndjson").unlink()
            frontier = extracted
    full = {"status":"WARRANTED_BOUNDED_FIRST_FRONTIER" if result["rc"] != 0
            else "WARRANTED_BOUNDED_COMPLETE_MATHLIB",
            "qualified":admissible,"complete_mathlib_accept":result["rc"] == 0,
            "source_sha":t.INPUT_SHA,"binary_sha":report["binary_sha"],
            "result":result,"terminal":terminal,"next_frontier":frontier,
            "no_official_arena_score":True}
    t.write_json(OUT / "full.json",full)
    print("DELTA_MATHLIB",json.dumps(full),flush=True)
    shutil.rmtree(arm / "target",ignore_errors=True)


if __name__ == "__main__":
    main()
