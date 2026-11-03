"""Observed Nat.beq_refl 4x UNKNOWN → minimal larger-budget screen.

An observational screen, NOT an Arena submission or qualified kernel release.
"""

import difflib
import hashlib
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
OUT = Path("/tmp/nucleus-beq-screen")
SOURCE_SHA = "d1c35f6a0de8644817b404e225a16de460e897e0b34c129fcb2a37483e630738"
BINARY_4X = "659d68f956fefac853e3b4b9c6a402a317de362588f3ddc7962e950cfce8161a"
PARENT_PATCH = "9d55735a77d69febdfb0b3d02ee1d5d29bb98011c9e534c17e25ca0f661bbfaa"


def run_case(binary, blob, env):
    return subprocess.run([str(binary)], input=blob, capture_output=True,
                          env=env, timeout=300)


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    source = Path("/tmp/beq-prefix.ndjson")
    assert t.digest(source) == SOURCE_SHA
    raw = source.read_bytes()
    records = raw.splitlines(keepends=True)
    last = json.loads(records[-1])
    assert "thm" in last and "type" in last["thm"] and "value" in last["thm"]
    official = Path("/tmp/beq-oracle/bundle/run")
    assert t.digest(official.parent / "kernel") == "ae92c625e612fff1c90e329344d22e3c3c330383cb335ce28fd41435be3b3b94"
    official.chmod(0o755)
    authority = []
    for label, args, expected in (
        ("parse", ["--parse-only", str(source)], 0),
        ("authentic", [str(source)], 0),
    ):
        result = subprocess.run([str(official), *args], capture_output=True,
                                timeout=300)
        authority.append(dict(label=label, rc=result.returncode,
                              tail=result.stdout[-240:].decode(errors="replace")))
        assert result.returncode == expected, authority[-1]
    # Independent forged-source controls.
    for key in ("type", "value"):
        modified = json.loads(records[-1])
        modified["thm"][key] = 0
        forged = b"".join(records[:-1]) + json.dumps(
            modified, separators=(",", ":")
        ).encode("utf-8") + b"\n"
        path = OUT / ("forged-" + key + ".ndjson")
        path.write_bytes(forged)
        result = subprocess.run([str(official), str(path)], capture_output=True,
                                timeout=300)
        authority.append(dict(label="forged-" + key,
                              rc=result.returncode, expected="nonaccept"))
        assert result.returncode != 0, authority[-1]
    t.write_json(OUT / "official-authority.json", authority)

    baseline = Path("/tmp/beq-budget4x/budget4x/nucleus")
    assert t.digest(baseline) == BINARY_4X
    baseline.chmod(0o755)
    env = R.N.runtime(True)
    env["NUCLEUS_TRACE_DOWNSTREAM"] = "1"
    red = t.measure(baseline, source, env, OUT / "red", timeout=300, perf=False)
    terminal = (OUT / "red/stderr").read_text(errors="replace")
    assert red["rc"] == 2
    assert "NUCLEUS_DOWNSTREAM:name=Nat.beq_refl:" in terminal
    rows = [dict(arm="budget4x", budget=262144,
                 rc=red["rc"], result=red, binary_sha=BINARY_4X)]
    t.write_json(OUT / "screen.json", dict(official=authority, rows=rows))

    arm = OUT / "source"
    kernel = L.materialize(arm, True)
    p = ROOT.parent / "nucleus-let-index-stack-20261104/owner-index.patch"
    applied = t.run_group(["patch", "--batch", "--fuzz=0", "-p1", "-i", str(p)],
                          cwd=arm, capture_output=True, timeout=30)
    assert applied.returncode == 0, applied.stderr
    with (arm / "source.patch").open("a") as dest:
        dest.write(p.read_text())
    assert t.digest(arm / "source.patch") == PARENT_PATCH
    file = kernel / "src/checker.rs"
    original = file.read_text()
    old = "judgment_steps: 65_536,"
    assert original.count(old) == 1

    for budget in (1048576, 4194304):
        variant = OUT / ("budget" + str(budget))
        variant.mkdir(exist_ok=True)
        changed = original.replace(old, f"judgment_steps: {budget:_},", 1)
        file.write_text(changed)
        patch = "".join(difflib.unified_diff(
            original.splitlines(True), changed.splitlines(True),
            fromfile="a/metatron-kernel/src/checker.rs",
            tofile="b/metatron-kernel/src/checker.rs",
        ))
        (variant / "budget.patch").write_text(patch)
        cargo_env = dict(os.environ, CARGO_TARGET_DIR=str(OUT / "shared-target"))
        build = t.run_group([
            "cargo", "build", "--release", "--locked", "--features", "diagnostics",
            "--manifest-path", str(kernel / "Cargo.toml"),
        ], env=cargo_env, capture_output=True, timeout=600)
        (variant / "build.log").write_bytes(build.stdout + build.stderr)
        if build.returncode != 0:
            rows.append(dict(arm="budget" + str(budget), budget=budget, build_rc=build.returncode))
            break
        binary = variant / "nucleus"
        shutil.copy2(OUT / "shared-target/release/metatron-kernel", binary)
        native = t.run_group([
            "cargo", "test", "--release", "--locked", "--lib",
            "--manifest-path", str(kernel / "Cargo.toml"),
        ], env=cargo_env | env, capture_output=True, timeout=300)
        (variant / "native-lib.log").write_bytes(native.stdout + native.stderr)
        measurement = t.measure(binary, source, env, variant / "proof", timeout=300, perf=False)
        row = dict(arm="budget" + str(budget), budget=budget,
                   rc=measurement["rc"], result=measurement,
                   binary_sha=t.digest(binary), native_lib_rc=native.returncode,
                   source_patch_sha=hashlib.sha256((arm / "source.patch").read_bytes() +
                                                    patch.encode()).hexdigest())
        rows.append(row)
        t.write_json(OUT / "screen.json", dict(official=authority, rows=rows,
                                             status="CANDIDATE_CAUSAL_SCREEN"))
        print("SCREEN", json.dumps(row), flush=True)
        if measurement["rc"] == 0 and native.returncode == 0:
            negative = []
            for key in ("type", "value"):
                forged = (OUT / ("forged-" + key + ".ndjson")).read_bytes()
                r = run_case(binary, forged, env)
                negative.append(dict(case=key, rc=r.returncode))
                assert r.returncode in (1, 2), negative[-1]
            row["forged"] = negative
            t.write_json(OUT / "screen.json", dict(official=authority, rows=rows,
                                                 status="CANDIDATE_CAUSAL_SCREEN"))
            break
    file.write_text(original)
    shutil.rmtree(OUT / "shared-target", ignore_errors=True)


if __name__ == "__main__":
    main()
