"""Protected, source-pinned qualification of the singleton Prop K repair.

This composes the exact previously qualified dense+4x+source-neutral kernel
and adds only the source-derived constructor-free K expectation. The earlier
full native/corpus/Mathlib qualification is reused without weakening gates.
The extra Std.LeftIdentity RED/GREEN and forgery checks run before it.
"""

import json
from pathlib import Path

import runner as S


Q = S.Q
OUT = Path("/tmp/nucleus-std-left-k-qualified")
SCREEN_SHA = "7417b6f935df16191d848e5e272d87ac9034a7a982f8e8ebdb883dbf5131d13e"
PATCH_SHA = "60b65d341f589b502a89620451c0e92fc505ebd501fb032952a05b93d86a461f"
DELTA_PATCH_SHA = "a788f92fd0471f1dc20cce9f42f8c94f9e3309ea1becb1da1ecd88aa5a9b58a6"


def main():
    OUT.mkdir(exist_ok=True)
    S.OUT = OUT / "std-gate"
    S.OUT.mkdir(exist_ok=True)
    Q.OUT = OUT
    prior = json.loads((Path("/tmp/delta-qualified") / "qualification.json").read_text())["candidate"]
    assert prior["qualified"] and prior["binary_sha"] == S.DELTA_SHA
    assert prior["source_patch_sha"] == DELTA_PATCH_SHA
    old_binary = Path("/tmp/delta-qualified/candidate/nucleus")
    assert Q.t.digest(old_binary) == S.DELTA_SHA
    old_binary.chmod(0o755)

    old_patch = Q.D.patch_source
    old_builder = Q.source_qualified_candidate

    def composite_patch(kernel, arm):
        old_patch(kernel, arm)
        assert Q.t.digest(arm / "source.patch") == DELTA_PATCH_SHA
        S.patch_k_source(kernel, arm)
        assert Q.t.digest(arm / "source.patch") == PATCH_SHA

    def build_and_protect(baseline):
        kernel, binary, build_env, arm = old_builder(baseline)
        assert Q.t.digest(binary) == SCREEN_SHA
        run = Q.R.N.runtime(True)
        assert {k: v for k, v in run.items() if k.startswith("NUCLEUS_")} == baseline["configuration"]
        run["NUCLEUS_TRACE_DOWNSTREAM"] = "1"
        source = Path("/tmp/std-prefix.ndjson")
        nat_source = Path("/tmp/beq-prefix.ndjson")
        assert Q.t.digest(source) == S.STD_SHA
        assert Q.t.digest(nat_source) == S.NAT_SHA
        red = S.run_case(old_binary, source, run, "red-std")
        green = S.run_case(binary, source, run, "green-std")
        retained = S.run_case(binary, nat_source, run, "retained-nat")
        forgeries = [
            S.run_case(binary, S.mutate_final(source, "forged-k-off",
                lambda block: block["recs"][0].__setitem__("k", False)), run, "forged-k-off"),
            S.run_case(binary, S.mutate_final(source, "forged-extra-field",
                lambda block: block["ctors"][0].__setitem__("numFields", 1)), run, "forged-extra-field"),
            S.run_case(binary, S.mutate_final(source, "forged-recursor-level",
                lambda block: block["recs"][0]["levelParams"].__setitem__(1, 326)), run,
                "forged-recursor-level"),
            S.run_case(binary, S.mutate_final(source, "forged-rule-count",
                lambda block: block["recs"][0]["rules"][0].__setitem__("nfields", 1)), run,
                "forged-rule-count"),
        ]
        passed = (red["rc"] == 2 and "Std.LeftIdentity" in red["terminal"]
                  and green["rc"] == 0 and retained["rc"] == 0
                  and all(x["rc"] != 0 for x in forgeries))
        report = {"status": "CANDIDATE_PROTECTED_SCREEN_PASSED" if passed else "REJECTED",
                  "source_sha": S.STD_SHA, "binary_sha": Q.t.digest(binary),
                  "source_patch_sha": Q.t.digest(arm / "source.patch"),
                  "red": red, "green": green, "retained_nat": retained,
                  "forged": forgeries, "all_gates": passed}
        Q.t.write_json(OUT / "std_gate.json", report)
        print("STD_K_PROTECTED_SCREEN", json.dumps({"passed": passed,
              "red": red["rc"], "green": green["rc"], "retained_nat": retained["rc"],
              "forged": [x["rc"] for x in forgeries],
              "binary_sha": report["binary_sha"]}), flush=True)
        assert passed, "Do not run or promote Mathlib without Std protected gate"
        return kernel, binary, build_env, arm

    Q.D.patch_source = composite_patch
    Q.source_qualified_candidate = build_and_protect
    try:
        Q.main()
    finally:
        Q.D.patch_source = old_patch
        Q.source_qualified_candidate = old_builder

    protected = json.loads((OUT / "qualification.json").read_text())["candidate"]
    full = json.loads((OUT / "full.json").read_text())
    assert protected["qualified"]
    assert full["qualified"]
    summary = {"status": "WARRANTED_BOUNDED", "std_admitted": True,
               "retained_nat": True, "four_forged_nonaccept": True,
               "native_42": protected["native_nonregression"],
               "source_controls_61": protected["controls_unchanged"],
               "arena_208_unchanged": len(protected["verdict_changes"]) == 0,
               "extra_unchanged": protected["extra_unchanged"],
               "full_mathlib_accept": full["complete_mathlib_accept"],
               "mathlib_terminal": full["terminal"],
               "next_frontier": full["next_frontier"],
               "binary_sha": protected["binary_sha"],
               "source_patch_sha": protected["source_patch_sha"]}
    Q.t.write_json(OUT / "std_qualification.json", summary)
    print("STD_K_FINAL_QUALIFICATION", json.dumps(summary), flush=True)


if __name__ == "__main__":
    main()
