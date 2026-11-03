"""Attempt source-certified projection replay, never arbitrary neutral equality."""

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
OUT = Path("/tmp/nucleus-beq-projection")


def apply_source_patch(kernel, arm):
    source_patch = []
    machine = kernel / "src/machine.rs"
    old = machine.read_text()
    needle = "    fn checked_neutral_projection_result(&self,neutral:&Neutral,budget:usize)->Judgment<Value>{"
    assert old.count(needle) == 1
    replacement = (
        "    pub(crate) fn checked_neutral_projection_result(&self,neutral:&Neutral,budget:usize)->Judgment<Value>{\n"
        "        // A conversion probe may own a fresh bounded replay scope; when\n"
        "        // nested, retain the parent source-work allowance unchanged.\n"
        "        let _owner = if self.exposure_fuel.get().is_none() {\n"
        "            self.exposure_fuel.set(Some(budget));\n"
        "            Some(ConstructorFuelScope { fuel: &self.exposure_fuel })\n"
        "        } else { None };"
    )
    after = old.replace(needle, replacement, 1)
    machine.write_text(after)
    source_patch.append(("machine.rs", old, after))

    convert = kernel / "src/convert.rs"
    old = convert.read_text()
    needle = (
        "                        if let Some((is_left, value)) = reduced {\n"
        "                            if is_left { current_left = value; } else { current_right = value; }\n"
        "                            current_budget = available.saturating_sub(1);\n"
        "                            continue;\n"
        "                        }\n"
        "                        return other;"
    )
    assert old.count(needle) == 1
    probe = (
        "                        // Only a source-registered recursor producing\n"
        "                        // the actual constructor may authorize field\n"
        "                        // selection. Failure never compares distinct\n"
        "                        // neutral heads as equal.\n"
        "                        if reduced.is_none() && available >= 128 && left.head != right.head {\n"
        "                            for (is_left, candidate) in [(false, right), (true, left)] {\n"
        "                                if !matches!(candidate.head, NeutralHead::Projection { .. }) { continue; }\n"
        "                                let probe_budget = available / 2;\n"
        "                                available -= probe_budget;\n"
        "                                if let Judgment::Proven { value, .. } = checker.machine()\n"
        "                                    .checked_neutral_projection_result(candidate, probe_budget)\n"
        "                                    && !matches!(&value, Value::Neutral(n) if n == candidate)\n"
        "                                { reduced = Some((is_left, value)); break; }\n"
        "                            }\n"
        "                        }\n"
    )
    after = old.replace(needle, probe + needle, 1)
    convert.write_text(after)
    source_patch.append(("convert.rs", old, after))
    unified = "".join("".join(difflib.unified_diff(
        before.splitlines(True), after.splitlines(True),
        fromfile="a/metatron-kernel/src/" + name,
        tofile="b/metatron-kernel/src/" + name,
    )) for name, before, after in source_patch)
    (arm / "projection.patch").write_text(unified)
    with (arm / "source.patch").open("a") as dst:
        dst.write(unified)


def main():
    OUT.mkdir(exist_ok=True)
    source = Path("/tmp/beq-prefix.ndjson")
    assert t.digest(source) == "d1c35f6a0de8644817b404e225a16de460e897e0b34c129fcb2a37483e630738"
    original = Path("/tmp/beq-budget4x/budget4x/nucleus")
    assert t.digest(original) == "659d68f956fefac853e3b4b9c6a402a317de362588f3ddc7962e950cfce8161a"
    original.chmod(0o755)
    env = R.N.runtime(True)
    env["NUCLEUS_TRACE_DOWNSTREAM"] = "1"
    red = t.measure(original, source, env, OUT / "red", timeout=300, perf=False)
    assert red["rc"] == 2
    assert "Nat.beq_refl" in (OUT / "red/stderr").read_text(errors="replace")

    arm = OUT / "source"
    kernel = L.materialize(arm, True)
    owner = ROOT.parent / "nucleus-let-index-stack-20261104/owner-index.patch"
    p = t.run_group(["patch", "--batch", "--fuzz=0", "-p1", "-i", str(owner)],
                    cwd=arm, capture_output=True, timeout=30)
    assert p.returncode == 0, p.stderr
    with (arm / "source.patch").open("a") as dst:
        dst.write(owner.read_text())
    assert t.digest(arm / "source.patch") == "9d55735a77d69febdfb0b3d02ee1d5d29bb98011c9e534c17e25ca0f661bbfaa"
    checker = kernel / "src/checker.rs"
    before = checker.read_text()
    old = "judgment_steps: 65_536,"
    assert before.count(old) == 1
    after = before.replace(old, "judgment_steps: 262_144,", 1)
    checker.write_text(after)
    with (arm / "source.patch").open("a") as dst:
        dst.write("".join(difflib.unified_diff(before.splitlines(True), after.splitlines(True),
            fromfile="a/metatron-kernel/src/checker.rs", tofile="b/metatron-kernel/src/checker.rs")))
    apply_source_patch(kernel, arm)
    binary, build_env = t.build(kernel, arm)
    assert binary is not None, (arm / "build.log").read_text()[-6000:]
    native = t.run_group([
        "cargo", "test", "--release", "--locked", "--lib",
        "--manifest-path", str(kernel / "Cargo.toml"),
    ], env=build_env | env, capture_output=True, timeout=300)
    (OUT / "native-lib.log").write_bytes(native.stdout + native.stderr)
    green = t.measure(binary, source, env, OUT / "green", timeout=300, perf=False)
    negative = []
    rows = source.read_bytes().splitlines(keepends=True)
    for key in ("type", "value"):
        altered = json.loads(rows[-1]);assert "thm" in altered
        altered["thm"][key] = 0
        blob = b"".join(rows[:-1]) + json.dumps(altered,separators=(",", ":")).encode() + b"\n"
        p = subprocess.run([str(binary)], input=blob, capture_output=True, env=env,timeout=300)
        negative.append(dict(key=key,rc=p.returncode))
        assert p.returncode in (1,2), negative[-1]
    info = dict(status="CANDIDATE_SOURCE_EXACT_SCREEN",red=red,green=green,
                positive_source_checked_by_official=True,native_rc=native.returncode,
                negatives=negative,binary_sha=t.digest(binary),
                source_patch_sha=t.digest(arm / "source.patch"),
                full_qualification_pending=green["rc"]==0,
                no_new_neutral_equality_rule=True)
    t.write_json(OUT / "summary.json",info)
    print("PROJECTION_REPLAY",json.dumps(info),flush=True)
    shutil.rmtree(arm / "target", ignore_errors=True)
    assert native.returncode == 0 and green["rc"] in (0,1,2)


if __name__ == "__main__":
    main()
