"""Causal RED/GREEN for source-definition delta on an evaluated neutral.

Experimental and bounded: only real registered definition bodies may reduce;
no equality between unrelated neutral heads is ever manufactured.
"""

import difflib
import hashlib
import importlib.util
import json
from pathlib import Path
import shutil
import subprocess


ROOT = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location(
    "projection", ROOT.parent / "nucleus-beq-projection-replay-20261104/runner.py"
)
P = importlib.util.module_from_spec(spec)
spec.loader.exec_module(P)
L, t, R = P.L, P.t, P.R
OUT = Path("/tmp/nucleus-beq-neutral-delta")


def patch_source(kernel, arm):
    changes = []
    machine = kernel / "src/machine.rs"
    before = machine.read_text()
    needle = "    /// Unfold exactly the definition at an application's head, then resume"
    assert before.count(needle) == 1
    addition = """    /// Unfold a real registered definition after an earlier exposure left
    /// its evaluated head neutral. Reapply only its *actual* captured spine.
    /// This is source delta, not a constructor guess or an equality rule.
    pub(crate) fn source_neutral_delta_for_conversion(
        &self, neutral:&Neutral, budget:usize,
    ) -> Judgment<Value> {
        if budget < 32 { return Judgment::unknown("neutral-delta-budget"); }
        let NeutralHead::Const { name, levels } = &neutral.head else {
            return Judgment::unknown("neutral-delta-nonconst");
        };
        let Some(definition) = self.definitions.get(name) else {
            return Judgment::unknown("neutral-delta-no-definition");
        };
        if definition.level_params.len() != levels.len() {
            return Judgment::unknown("neutral-delta-level-arity");
        }
        let substitution = definition.level_params.iter().copied()
            .zip(levels.iter().cloned()).collect::<Vec<_>>();
        let source = Closure::with_levels(definition.value, EnvFrame::empty(),
            LevelSubstitution::new(substitution));
        self.expose_internal_with_pending(source, Transparency::Full, budget,
            false, true, neutral.spine.iter().rev().cloned().collect())
            .map(|exposure| exposure.value)
    }

"""
    after = before.replace(needle, addition + needle, 1)
    machine.write_text(after)
    changes.append(("machine.rs", before, after))

    convert = kernel / "src/convert.rs"
    before = convert.read_text()
    needle = ("                        if let Some((is_left, value)) = reduced {\n"
              "                            if is_left { current_left = value; } else { current_right = value; }\n"
              "                            current_budget = available.saturating_sub(1);\n"
              "                            continue;\n"
              "                        }\n"
              "                        return other;")
    assert before.count(needle) == 1
    addition = """                        // Fail-closed fallback: a registered source
                        // definition can be unfolded despite a neutral head
                        // mismatch. Reduce only its actual source body, with
                        // the original captures, and spend the same budget.
                        if reduced.is_none() && available >= 256 && left.head != right.head {
                            for (is_left, candidate) in [(false, right), (true, left)] {
                                let NeutralHead::Const { name, .. } = &candidate.head else {
                                    continue;
                                };
                                if checker.definition_value(*name).is_none() || available < 128 {
                                    continue;
                                }
                                let probe_budget = available / 2;
                                available -= probe_budget;
                                if let Judgment::Proven { value, .. } = checker.machine()
                                    .source_neutral_delta_for_conversion(candidate, probe_budget)
                                    && !matches!(&value, Value::Neutral(n) if n == candidate)
                                {
                                    reduced = Some((is_left, value));
                                    break;
                                }
                            }
                        }
"""
    after = before.replace(needle, addition + needle, 1)
    convert.write_text(after)
    changes.append(("convert.rs", before, after))

    unified = "".join("".join(difflib.unified_diff(
        before.splitlines(True), after.splitlines(True),
        fromfile="a/metatron-kernel/src/" + name,
        tofile="b/metatron-kernel/src/" + name))
        for name, before, after in changes)
    (arm / "neutral-delta.patch").write_text(unified)
    with (arm / "source.patch").open("a") as out:
        out.write(unified)


def main():
    OUT.mkdir(exist_ok=True)
    source = Path("/tmp/beq-prefix.ndjson")
    assert t.digest(source) == "d1c35f6a0de8644817b404e225a16de460e897e0b34c129fcb2a37483e630738"
    baseline = Path("/tmp/beq-qualified/candidate/nucleus")
    assert t.digest(baseline) == "7897fdf50b447ec1bb38dd4a409d3a3bc690eeac7868d58848f6046b099684a6"
    baseline.chmod(0o755)
    env = R.N.runtime(True) | {"NUCLEUS_TRACE_DOWNSTREAM":"1"}
    red = t.measure(baseline, source, env, OUT / "red", timeout=300, perf=False)
    assert red["rc"] == 2 and "Nat.beq_refl" in (OUT / "red/stderr").read_text(errors="replace")

    arm = OUT / "candidate"
    kernel = L.materialize(arm, True)
    owner = ROOT.parent / "nucleus-let-index-stack-20261104/owner-index.patch"
    p = t.run_group(["patch", "--batch", "--fuzz=0", "-p1", "-i", str(owner)],
                    cwd=arm, capture_output=True, timeout=30)
    assert p.returncode == 0, p.stderr
    with (arm / "source.patch").open("a") as out:
        out.write(owner.read_text())
    assert t.digest(arm / "source.patch") == "9d55735a77d69febdfb0b3d02ee1d5d29bb98011c9e534c17e25ca0f661bbfaa"
    checker = kernel / "src/checker.rs"
    before = checker.read_text()
    assert before.count("judgment_steps: 65_536,") == 1
    after = before.replace("judgment_steps: 65_536,", "judgment_steps: 262_144,", 1)
    checker.write_text(after)
    with (arm / "source.patch").open("a") as out:
        out.write("".join(difflib.unified_diff(before.splitlines(True), after.splitlines(True),
            fromfile="a/metatron-kernel/src/checker.rs", tofile="b/metatron-kernel/src/checker.rs")))
    patch_source(kernel, arm)

    binary, build_env = t.build(kernel, arm)
    assert binary is not None, (arm / "build.log").read_text()[-5000:]
    native = t.run_group(["cargo", "test", "--release", "--locked", "--lib",
                          "--manifest-path", str(kernel / "Cargo.toml")],
                         env=build_env | env, capture_output=True, timeout=300)
    (OUT / "native-lib.log").write_bytes(native.stdout + native.stderr)
    green = t.measure(binary, source, env, OUT / "green", timeout=300, perf=False)

    rows = source.read_bytes().splitlines(keepends=True)
    negatives = []
    for key in ("type", "value"):
        terminal = json.loads(rows[-1]); assert "thm" in terminal
        terminal["thm"][key] = 0
        modified = b"".join(rows[:-1]) + json.dumps(terminal,separators=(",", ":")).encode() + b"\n"
        p = subprocess.run([str(binary)],input=modified,capture_output=True,
                           env=env,timeout=300)
        negatives.append({"field":key,"rc":p.returncode})
    result = {"status":"CANDIDATE_CAUSAL_SCREEN", "baseline":red,
              "candidate":green,"native_rc":native.returncode,"negative_controls":negatives,
              "binary_sha":t.digest(binary),"patch_sha":t.digest(arm / "source.patch"),
              "source_sha":t.digest(source),
              "full_qualification_pending": green["rc"] == 0 and native.returncode == 0
              and all(x["rc"] != 0 for x in negatives),
              "no_new_equality_rule":True}
    t.write_json(OUT / "summary.json",result)
    print("SOURCE_NEUTRAL_DELTA",json.dumps(result,sort_keys=True),flush=True)
    shutil.rmtree(arm / "target", ignore_errors=True)
    assert native.returncode == 0
    assert all(x["rc"] in (1,2) for x in negatives)
    assert green["rc"] in (0,1,2)


if __name__ == "__main__":
    main()
