"""Source-qualified causal screen for nullary Prop singleton recursor-K metadata.

This is deliberately not a proof-rule shortcut. The only change is the
expected exported recursor metadata bit for a source-derived Prop singleton
with zero constructor fields. Every current type, constructor, recursor,
rule and environment derivation remains mandatory.
"""

import difflib
import importlib.util
import json
from pathlib import Path
import subprocess


ROOT = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location(
    "qualified_delta", ROOT.parent / "nucleus-beq-neutral-delta-20261104/qualify.py"
)
Q = importlib.util.module_from_spec(spec)
spec.loader.exec_module(Q)
OUT = Path("/tmp/nucleus-std-left-k")
STD_SHA = "282a7cf85e897f1e246fc25bc0cf6a6b69afdce72856f2fb500299504b8488ef"
NAT_SHA = "d1c35f6a0de8644817b404e225a16de460e897e0b34c129fcb2a37483e630738"
DELTA_SHA = "33e039f3a2fdd9e18b223a428531ca689583a2c9bfb4f8143123f13dc532eaa4"


def patch_k_source(kernel: Path, arm: Path) -> None:
    path = kernel / "src/checker.rs"
    before = path.read_text()
    start = before.index("fn check_generic_prop_singleton_large_elim(")
    stop = before.index("fn generic_nonrecursive_prop_small_candidate(", start)
    original = before[start:stop]
    anchor = "    let recursor_metadata_ok = recursor_metadata_admissible("
    assert original.count(anchor) == 1
    needle = "        recursor,\n        false,\n        recursor.level_params.len()"
    assert original.count(needle) == 1
    # The inductive checker has already independently checked that the result
    # is Prop and there is precisely one nonrecursive constructor. K for the
    # fieldless case is a source-derived predicate, never recursor.k itself.
    addition = (
        "    let source_warrants_k = constructor.num_fields == 0\n"
        "        && pi_spine(export, inductive.ty, parameter_count)\n"
        "            .is_some_and(|(_, result)| is_prop_sort(export, result));\n"
    )
    changed = original.replace(anchor, addition + anchor, 1)
    changed = changed.replace(needle,
        "        recursor,\n        source_warrants_k,\n        recursor.level_params.len()", 1)
    after = before[:start] + changed + before[stop:]
    path.write_text(after)
    diff = "".join(difflib.unified_diff(
        before.splitlines(True), after.splitlines(True),
        fromfile="a/metatron-kernel/src/checker.rs",
        tofile="b/metatron-kernel/src/checker.rs",
    ))
    (arm / "k-source.patch").write_text(diff)
    with (arm / "source.patch").open("a") as stream:
        stream.write(diff)


def run_case(binary: Path, source: Path, env: dict, label: str):
    target = OUT / label
    result = Q.t.measure(binary, source, env, target, timeout=150, perf=False)
    return {"name": label, "sha256": Q.t.digest(source), "rc": result["rc"],
            "terminal": (target / "stderr").read_text(errors="replace")[-2000:]}


def mutate_final(source: Path, label: str, change) -> Path:
    # Preserve the exact first 130113 source records; change just one claim
    # in the final source-encoded inductive block. No untrusted text replace.
    lines = source.read_bytes().splitlines(keepends=True)
    assert lines[-1].startswith(b'{"inductive":')
    parsed = json.loads(lines[-1])
    change(parsed["inductive"])
    path = OUT / (label + ".ndjson")
    path.write_bytes(b"".join(lines[:-1]) +
                     json.dumps(parsed, separators=(",", ":"), sort_keys=True).encode() + b"\n")
    return path


def main():
    OUT.mkdir(exist_ok=True)
    delta = Path("/tmp/delta-qualified")
    old = json.loads((delta / "qualification.json").read_text())["candidate"]
    assert old["qualified"] and old["binary_sha"] == DELTA_SHA
    original = delta / "candidate/nucleus"
    assert Q.t.digest(original) == DELTA_SHA
    original.chmod(0o755)
    reference = json.loads((Path("/tmp/dense-qualified") / "qualification.json").read_text())["candidate"]
    assert reference["qualified"] and reference["binary_sha"] == Q.BASE_SHA

    source = Path("/tmp/std-prefix.ndjson")
    nat_source = Path("/tmp/beq-prefix.ndjson")
    assert Q.t.digest(source) == STD_SHA
    assert Q.t.digest(nat_source) == NAT_SHA
    env = Q.R.N.runtime(True)
    assert {k: v for k, v in env.items() if k.startswith("NUCLEUS_")} == reference["configuration"]
    env["NUCLEUS_TRACE_DOWNSTREAM"] = "1"
    red = run_case(original, source, env, "red-std")
    assert red["rc"] == 2 and "Std.LeftIdentity" in red["terminal"]

    original_patch = Q.D.patch_source
    def combined_patch(kernel, arm):
        original_patch(kernel, arm)
        assert Q.t.digest(arm / "source.patch") == old["source_patch_sha"]
        patch_k_source(kernel, arm)
    Q.D.patch_source = combined_patch
    try:
        kernel, binary, build_env, arm = Q.source_qualified_candidate(reference)
    finally:
        Q.D.patch_source = original_patch
    positives = [run_case(binary, source, env, "green-std"),
                 run_case(binary, nat_source, env, "retained-nat")]
    forged = [
        run_case(binary, mutate_final(source, "forged-k-off",
            lambda block: block["recs"][0].__setitem__("k", False)), env, "forged-k-off"),
        run_case(binary, mutate_final(source, "forged-extra-field",
            lambda block: block["ctors"][0].__setitem__("numFields", 1)), env, "forged-extra-field"),
        run_case(binary, mutate_final(source, "forged-recursor-level",
            lambda block: block["recs"][0]["levelParams"].__setitem__(1, 326)), env,
            "forged-recursor-level"),
        run_case(binary, mutate_final(source, "forged-rule-count",
            lambda block: block["recs"][0]["rules"][0].__setitem__("nfields", 1)), env,
            "forged-rule-count"),
    ]
    status = ("CANDIDATE_POSITIVE" if all(x["rc"] == 0 for x in positives)
              and all(x["rc"] != 0 for x in forged) else "REJECTED_AS_SUFFICIENT")
    report = {"status": status, "source": STD_SHA,
              "comparator_sha": DELTA_SHA, "candidate_binary": Q.t.digest(binary),
              "source_patch_sha": Q.t.digest(arm / "source.patch"),
              "red": red, "positive": positives, "forged": forged,
              "protected_full_qualification": "NOT_RUN", "complete_mathlib": "UNKNOWN"}
    Q.t.write_json(OUT / "report.json", report)
    print("STD_LEFT_K_SCREEN", json.dumps(report), flush=True)
    assert status == "CANDIDATE_POSITIVE", status


if __name__ == "__main__":
    main()
