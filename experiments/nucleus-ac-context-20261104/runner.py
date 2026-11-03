"""Causal source-bound test: Sort-u record eligibility, not a new proof rule.

The complete qualified K+neutral+dense4x stack is reconstructed by exact
source patch hashes. Only the gate into existing dependent record obligations
may change; forged claims must stay non-ACCEPT. No full Mathlib qualification
is implied by a positive screen.
"""

import difflib
import importlib.util
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location(
    "std_k_causal", ROOT.parent / "nucleus-std-left-k-20261104/runner.py")
K = importlib.util.module_from_spec(spec)
spec.loader.exec_module(K)
Q = K.Q
OUT = Path("/tmp/nucleus-ac-context")
AC_SHA = "e08afe0a4ce9c0cd64308ee6eef52d0952316784d72175c843846762e2eb4d0b"
K_SHA = "7417b6f935df16191d848e5e272d87ac9034a7a982f8e8ebdb883dbf5131d13e"
K_PATCH_SHA = "60b65d341f589b502a89620451c0e92fc505ebd501fb032952a05b93d86a461f"
DELTA_PATCH_SHA = "a788f92fd0471f1dc20cce9f42f8c94f9e3309ea1becb1da1ecd88aa5a9b58a6"


def patch_source(kernel: Path, arm: Path):
    path = kernel / "src/checker.rs"
    before = path.read_text()
    start = before.index("fn parameter_record_scope(")
    stop = before.index("fn parameter_record_candidate(", start)
    section = before[start:stop]
    anchor = (
        "    is_sort_succ_parameter(export,parameters[0],inductive.level_params[0])\n"
        "        && is_sort_succ_parameter(export,result,inductive.level_params[0])"
    )
    assert section.count(anchor) == 1
    # Lean permits a record over a type in Sort u while its structure itself
    # inhabits Sort (u+1). Derive that relationship from the SOURCE universe,
    # never from the recursor's untrusted universe claims.
    replacement = (
        "    let source_sort_parameter = matches!(export.exprs.get(parameters[0]),\n"
        "        Some(Expr::Sort(level)) if matches!(export.levels.get(*level),\n"
        "            Some(Level::Param(name)) if *name == inductive.level_params[0]));\n"
        "    (is_sort_succ_parameter(export,parameters[0],inductive.level_params[0])\n"
        "        || source_sort_parameter)\n"
        "        && is_sort_succ_parameter(export,result,inductive.level_params[0])"
    )
    after = before[:start] + section.replace(anchor, replacement, 1) + before[stop:]
    path.write_text(after)
    diff = "".join(difflib.unified_diff(before.splitlines(True), after.splitlines(True),
        fromfile="a/metatron-kernel/src/checker.rs", tofile="b/metatron-kernel/src/checker.rs"))
    (arm / "sort-parameter.patch").write_text(diff)
    with (arm / "source.patch").open("a") as out:
        out.write(diff)


def main():
    OUT.mkdir(exist_ok=True)
    K.OUT = OUT
    k_prior = json.loads((Path("/tmp/k-qualified") / "qualification.json").read_text())["candidate"]
    assert k_prior["qualified"] and k_prior["binary_sha"] == K_SHA
    assert k_prior["source_patch_sha"] == K_PATCH_SHA
    old = Path("/tmp/k-qualified/candidate/nucleus")
    assert Q.t.digest(old) == K_SHA
    old.chmod(0o755)
    reference = json.loads((Path("/tmp/dense-qualified") / "qualification.json").read_text())["candidate"]
    assert reference["qualified"] and reference["binary_sha"] == Q.BASE_SHA
    source = Path("/tmp/ac-prefix.ndjson")
    assert Q.t.digest(source) == AC_SHA
    env = Q.R.N.runtime(True)
    assert {k: v for k, v in env.items() if k.startswith("NUCLEUS_")} == reference["configuration"]
    env["NUCLEUS_TRACE_DOWNSTREAM"] = "1"
    red = K.run_case(old, source, env, "red-ac")
    assert red["rc"] == 2 and "Lean.Data.AC.Context" in red["terminal"]
    original_patch = Q.D.patch_source
    def compose_patch(kernel, arm):
        original_patch(kernel, arm)
        assert Q.t.digest(arm / "source.patch") == DELTA_PATCH_SHA
        K.patch_k_source(kernel, arm)
        assert Q.t.digest(arm / "source.patch") == K_PATCH_SHA
        patch_source(kernel, arm)
    Q.D.patch_source = compose_patch
    try:
        kernel, binary, _, arm = Q.source_qualified_candidate(reference)
    finally:
        Q.D.patch_source = original_patch
    green = K.run_case(binary, source, env, "green-ac")
    positives, forgeries = [], []
    if green["rc"] == 0:
        positives = [K.run_case(binary, Path("/tmp/std-prefix.ndjson"), env, "retained-std"),
                     K.run_case(binary, Path("/tmp/beq-prefix.ndjson"), env, "retained-nat")]
        forgeries = [
            K.run_case(binary, K.mutate_final(source, "forged-fields",
                lambda b: b["ctors"][0].__setitem__("numFields", 7)), env, "forged-fields"),
            K.run_case(binary, K.mutate_final(source, "forged-k",
                lambda b: b["recs"][0].__setitem__("k", True)), env, "forged-k"),
            K.run_case(binary, K.mutate_final(source, "forged-owner",
                lambda b: b["ctors"][0].__setitem__("induct", b["ctors"][0]["name"])),
                env, "forged-owner"),
            K.run_case(binary, K.mutate_final(source, "forged-rule-count",
                lambda b: b["recs"][0]["rules"][0].__setitem__("nfields", 7)),
                env, "forged-rule-count"),
            K.run_case(binary, K.mutate_final(source, "forged-level-owner",
                lambda b: b["recs"][0]["levelParams"].__setitem__(1, 27)),
                env, "forged-level-owner"),
        ]
    pass_ = (green["rc"] == 0 and len(positives) == 2
             and all(x["rc"] == 0 for x in positives)
             and len(forgeries) == 5 and all(x["rc"] != 0 for x in forgeries))
    result = {"status":"CANDIDATE_POSITIVE" if pass_ else "REJECTED_AS_SUFFICIENT",
              "source_sha":AC_SHA,"old_binary_sha":K_SHA,"candidate_binary_sha":Q.t.digest(binary),
              "source_patch_sha":Q.t.digest(arm / "source.patch"),
              "red":red,"green":green,"retained":positives,"forged":forgeries,
              "protected_full_qualification":"NOT_RUN","complete_mathlib":"UNKNOWN"}
    Q.t.write_json(OUT / "report.json", result)
    print("AC_CONTEXT_SCREEN", json.dumps(result), flush=True)
    assert pass_, result["status"]


if __name__ == "__main__":
    main()
