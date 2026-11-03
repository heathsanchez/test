"""Source-exact, soundness-gated 4x judgment-budget qualification.

No new typing/conversion rule is added. The previously source-pinned red
test (Range prefix, budget=65536) is recorded before the candidate green.
"""

import argparse
import difflib
import importlib.util
import json
import os
import shutil
import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location(
    "let_wave", ROOT.parent / "nucleus-let-preservation-20261104/runner.py"
)
L = importlib.util.module_from_spec(spec)
spec.loader.exec_module(L)
R = L.R
t = L.t

BASE_SHA = "2cc176dc026091ad3e1c6479fdd5599728eec309813d6fcc989f90ad083fee9a"
SOURCE_SHA = "d9d7b1fe7267a0806f65200abc64a9c7114fb8097a9da1f3687f2560a2568bb9"
EXPECTED_FAILURE = (
    "_private.Init.Data.List.Nat.Range.0.List.pairwise_lt_range'._proof_1_4"
)


def signature(row):
    return tuple((key, row.get(key)) for key in
                 ("file", "case", "sha256", "expected", "native_expected", "rc"))


def verify_red(binary, source, env, out):
    proof = t.measure(binary, source, env, out, timeout=300, perf=False)
    stderr = (out / "stderr").read_text(errors="replace")
    assert proof["rc"] == 2, proof
    assert "NUCLEUS_DOWNSTREAM:name=" + EXPECTED_FAILURE in stderr, stderr[-2000:]
    t.write_json(out / "red.json", proof)
    return proof


def prepare_candidate(out, qualified):
    arm = out / "candidate"
    kernel = L.materialize(arm, True)
    for label in ("owner-index.patch", "tagged.patch", "dense.patch"):
        path = (ROOT.parent / "nucleus-dense-composition-20261104/dense.patch"
                if label == "dense.patch"
                else ROOT.parent / "nucleus-tagged-let-20261104" / label)
        result = t.run_group(
            ["patch", "--batch", "--fuzz=0", "-p1", "-i", str(path)],
            cwd=arm, capture_output=True, timeout=30,
        )
        (arm / (label + ".log")).write_bytes(result.stdout + result.stderr)
        assert result.returncode == 0, (label, result.stdout, result.stderr)
        with (arm / "source.patch").open("a") as dest:
            dest.write(path.read_text())
    assert t.digest(arm / "source.patch") == qualified["source_patch_sha"]

    # The one allowed behavior change is increasing bounded proof search.
    path = kernel / "src/checker.rs"
    before = path.read_text()
    old = "judgment_steps: 65_536,"
    assert before.count(old) == 1
    after = before.replace(old, "judgment_steps: 262_144,", 1)
    path.write_text(after)
    patch = "".join(difflib.unified_diff(
        before.splitlines(True), after.splitlines(True),
        fromfile="a/metatron-kernel/src/checker.rs",
        tofile="b/metatron-kernel/src/checker.rs",
    ))
    (arm / "budget.patch").write_text(patch)
    with (arm / "source.patch").open("a") as dest:
        dest.write(patch)
    binary, build_env = t.build(kernel, arm)
    assert binary is not None, (arm / "build.log").read_text()[-6000:]
    return kernel, binary, build_env, arm


def validate_proof_and_forgery(binary, source, env, out):
    source_bytes = source.read_bytes()
    assert source_bytes.endswith(b"\n")
    lines = source_bytes.splitlines(keepends=True)
    last = json.loads(lines[-1])
    assert "thm" in last and "type" in last["thm"] and "value" in last["thm"]
    rows = []
    for label, blob in [("authentic", source_bytes)]:
        p = subprocess.run([str(binary)], input=blob, capture_output=True,
                           env=env, timeout=300)
        rows.append(dict(label=label, rc=p.returncode,
                         source_sha=t.digest(source),
                         tail=p.stderr[-300:].decode(errors="replace")))
        assert p.returncode == 0, rows[-1]
    # Bad proof/value IDs must not be accepted just because computation
    # receives more steps. This is a kernel boundary, not a mutation score.
    for key in ("type", "value"):
        changed = json.loads(lines[-1])
        assert key in changed["thm"]
        changed["thm"][key] = 0
        blob = b"".join(lines[:-1]) + json.dumps(
            changed, separators=(",", ":")
        ).encode("utf-8") + b"\n"
        p = subprocess.run([str(binary)], input=blob, capture_output=True,
                           env=env, timeout=300)
        rows.append(dict(label="forged-" + key, rc=p.returncode,
                         tail=p.stderr[-300:].decode(errors="replace")))
        assert p.returncode in (1, 2), rows[-1]
    t.write_json(out / "source-proofs.json", rows)
    return rows


def main(out):
    prior = Path("/tmp/dense-qualified")
    baseline = json.loads((prior / "qualification.json").read_text())["candidate"]
    assert baseline["qualified"]
    assert baseline["binary_sha"] == BASE_SHA
    original = prior / "candidate/nucleus"
    assert t.digest(original) == BASE_SHA
    original.chmod(0o755)
    assert len(baseline["native"]["targets"]) == 42
    assert len(baseline["controls"]) == 61
    assert all(x["pass_"] for x in baseline["controls"])

    run = R.N.runtime(True)
    assert {k: v for k, v in run.items() if k.startswith("NUCLEUS_")} == baseline["configuration"]
    run["NUCLEUS_TRACE_DOWNSTREAM"] = "1"
    source = Path("/tmp/range-prefix.ndjson")
    assert t.digest(source) == SOURCE_SHA
    red = verify_red(original, source, run, out / "red")
    kernel, candidate, build_env, arm = prepare_candidate(out, baseline)
    qualified_env = {k: v for k, v in run.items() if k != "NUCLEUS_TRACE_DOWNSTREAM"}

    # First prove the exact known red becomes green; then exercise all
    # protected native/source controls before any full-Mathlib claim.
    proof_rows = validate_proof_and_forgery(candidate, source, run, out)
    inputs = Path("/tmp/current208")
    extra = inputs / "inputs/good/perf/magma-list-pair-n21.ndjson"
    extra.parent.mkdir(parents=True, exist_ok=True)
    subprocess.run([
        "zstd", "-dq", "-f",
        str(ROOT.parent / "nucleus-coverage-evidence-20261104/inputs/magma-list-pair-n21.ndjson.zst"),
        "-o", str(extra),
    ], check=True)
    assert t.digest(extra) == baseline["extra"]["input_sha"]
    native = t.native_suite(
        kernel, build_env | qualified_env |
        {"NUCLEUS_FROZEN196": str(inputs / "inputs")}, arm,
    )
    controls = L.controls(candidate, qualified_env)
    native_ok = R.N.Q.native_nonregression(native, baseline["native"])
    controls_ok = sorted(map(signature, controls)) == sorted(map(signature, baseline["controls"]))
    old_rows = json.loads((prior / "candidate/verdicts.json").read_text())
    new_rows = t.replay(
        candidate, json.loads((inputs / "inputs-manifest.json").read_text()),
        inputs, qualified_env, arm / "verdicts.json",
    )
    assert len(old_rows) == len(new_rows) == 208
    changes = []
    for before, after in zip(old_rows, new_rows):
        assert before["case"] == after["case"]
        assert before["sha256"] == after["sha256"]
        if before["rc"] != after["rc"]:
            changes.append(dict(case=before["case"], before=before["rc"], after=after["rc"]))
    with extra.open("rb") as f:
        extra_result = t.run_group([str(candidate)], stdin=f, capture_output=True,
                                   env=qualified_env, timeout=180)
    extra_ok = extra_result.returncode == baseline["extra"]["rc"]
    admissible = (native_ok and controls_ok and not changes and extra_ok and
                  all(row["pass_"] for row in controls) and
                  len(proof_rows) == 3)
    report = dict(
        status="WARRANTED_BOUNDED" if admissible else "CANDIDATE",
        qualified=admissible, baseline_binary=BASE_SHA,
        binary_sha=t.digest(candidate),
        source_patch_sha=t.digest(arm / "source.patch"),
        source_sha=SOURCE_SHA, red=red,
        green=proof_rows, native=native,
        native_nonregression=native_ok,
        controls=controls, controls_unchanged=controls_ok,
        verdict_changes=changes, extra_unchanged=extra_ok,
        configuration=baseline["configuration"],
        boundary="Raised 65536 to 262144 judgment steps only; no new proof rule",
    )
    t.write_json(out / "qualification.json", dict(candidate=report))
    print("QUALIFICATION", json.dumps({
        "qualified": admissible, "native_nonregression": native_ok,
        "controls_unchanged": controls_ok, "verdict_changes": changes,
        "extra_unchanged": extra_ok, "budget4x_proof_rc": proof_rows[0]["rc"],
        "binary_sha": report["binary_sha"],
    }), flush=True)

    # Research-only completion diagnostic if any baseline UNKNOWN changes.
    # Do not promote or submit it unless the protected gate above passes.
    mathlib = Path("/tmp/mathlib.ndjson")
    assert t.digest(mathlib) == t.INPUT_SHA
    result = t.measure(candidate, mathlib, run, out / "full", timeout=1800, perf=False)
    traces = [line for line in (out / "full/stderr").read_text(errors="replace").splitlines()
              if line.startswith("NUCLEUS_DOWNSTREAM:")]
    terminal = traces[-1] if traces else None
    frontier = None
    if result["rc"] == 2 and terminal:
        import re
        match = re.search(r"NUCLEUS_DOWNSTREAM:name=(.*?):stage=", terminal)
        if match and not match.group(1).startswith("<"):
            extracted = R.E.extract(mathlib, out / "next-frontier.ndjson", match.group(1))
            subprocess.run(["zstd", "-T0", "-3", str(out / "next-frontier.ndjson")],
                           check=True)
            (out / "next-frontier.ndjson").unlink()
            frontier = extracted
    full = dict(
        qualified=admissible, complete_mathlib_accept=admissible and result["rc"] == 0,
        source_sha=t.INPUT_SHA, binary_sha=report["binary_sha"],
        result=result, terminal=terminal, next_frontier=frontier,
        no_official_arena_score=True,
    )
    t.write_json(out / "full.json", full)
    print("MATHLIB", json.dumps(full), flush=True)
    shutil.rmtree(arm / "target", ignore_errors=True)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", required=True)
    arguments = parser.parse_args()
    output = Path(arguments.out).resolve()
    output.mkdir(parents=True, exist_ok=True)
    main(output)
