"""Full qualification for source-Sort-u AC record eligibility.

Reuses the completed RED/GREEN/forged source receipts only after verifying
their immutable artifact digest, exact input hashes, reconstruction of each
mutation, candidate source patch and binary hashes, and unchanged config.
Never reuses a prior verdict *inside* the checker or for a new input.
Native protected targets, original Arena corpus and full Mathlib are fresh.
"""

import json
from pathlib import Path

import runner as AC


K, Q = AC.K, AC.Q
OUT = Path("/tmp/nucleus-ac-context-qualified")
SOURCE_PATCH_SHA = "38f766951ec364214abe43275151803f867ad0831f63ea518c6088f7dc7d3dff"
CANDIDATE_SHA = "c48534b7b021de44f6cd1fd068c7e0824bb32a3a6285b71560b39a24c9aa96da"


def authenticate_screen():
    # Each row remains a bounded prior empirical result: it is not permission
    # for a checker to trust any proof or environment state without replay.
    source = Path("/tmp/ac-prefix.ndjson")
    assert Q.t.digest(source) == AC.AC_SHA
    receipt_dir = Path("/tmp/ac-causal/nucleus-ac-context")
    report = json.loads((receipt_dir / "report.json").read_text())
    assert report["status"] == "CANDIDATE_POSITIVE"
    assert report["source_sha"] == AC.AC_SHA
    assert report["old_binary_sha"] == AC.K_SHA
    assert report["candidate_binary_sha"] == CANDIDATE_SHA
    assert report["source_patch_sha"] == SOURCE_PATCH_SHA
    assert report["red"]["rc"] == 2 and "Lean.Data.AC.Context" in report["red"]["terminal"]
    assert report["green"]["rc"] == 0 and len(report["retained"]) == 2
    assert [x["name"] for x in report["retained"]] == ["retained-std", "retained-nat"]
    assert all(x["rc"] == 0 for x in report["retained"])
    assert [x["name"] for x in report["forged"]] == [
        "forged-fields", "forged-k", "forged-owner", "forged-rule-count", "forged-level-owner"]
    assert all(x["rc"] in (1,2) for x in report["forged"])
    assert Q.t.digest(Path("/tmp/std-prefix.ndjson")) == K.STD_SHA
    assert Q.t.digest(Path("/tmp/beq-prefix.ndjson")) == K.NAT_SHA
    assert [row["sha256"] for row in report["retained"]] == [K.STD_SHA, K.NAT_SHA]
    AC.K.OUT = OUT / "regenerated-claims"
    AC.K.OUT.mkdir(exist_ok=True)
    mutant_ops = [
        ("forged-fields", lambda b:b["ctors"][0].__setitem__("numFields",7)),
        ("forged-k", lambda b:b["recs"][0].__setitem__("k",True)),
        ("forged-owner", lambda b:b["ctors"][0].__setitem__("induct",b["ctors"][0]["name"])),
        ("forged-rule-count", lambda b:b["recs"][0]["rules"][0].__setitem__("nfields",7)),
        ("forged-level-owner", lambda b:b["recs"][0]["levelParams"].__setitem__(1,27)),
    ]
    for row, (name, operation) in zip(report["forged"], mutant_ops):
        assert row["name"] == name
        regenerated = K.mutate_final(source, name, operation)
        assert Q.t.digest(regenerated) == row["sha256"]
    for row in [report["red"],report["green"],*report["retained"],*report["forged"]]:
        stderr = (receipt_dir / row["name"] / "stderr").read_text(errors="replace")
        assert stderr.endswith(row["terminal"])
    return report


def main():
    OUT.mkdir(exist_ok=True)
    receipt = authenticate_screen()
    k_state = json.loads((Path("/tmp/k-qualified") / "qualification.json").read_text())["candidate"]
    assert k_state["qualified"] and k_state["binary_sha"] == AC.K_SHA
    assert k_state["source_patch_sha"] == AC.K_PATCH_SHA
    assert Q.t.digest(Path("/tmp/k-qualified/candidate/nucleus")) == AC.K_SHA
    Q.OUT = OUT
    old_patch = Q.D.patch_source
    old_builder = Q.source_qualified_candidate

    def compose_patch(kernel, arm):
        old_patch(kernel, arm)
        assert Q.t.digest(arm / "source.patch") == AC.DELTA_PATCH_SHA
        K.patch_k_source(kernel, arm)
        assert Q.t.digest(arm / "source.patch") == AC.K_PATCH_SHA
        AC.patch_source(kernel, arm)
        assert Q.t.digest(arm / "source.patch") == SOURCE_PATCH_SHA

    def build_and_authenticate(baseline):
        # Existing source-qualified builder retains exact prior dense+4x pin.
        assert {k:v for k,v in Q.R.N.runtime(True).items() if k.startswith("NUCLEUS_")} == baseline["configuration"]
        kernel, binary, build_env, arm = old_builder(baseline)
        assert Q.t.digest(binary) == CANDIDATE_SHA
        matched = {"status":"CAUSAL_RECEIPTS_AUTHENTICATED", "source_sha": AC.AC_SHA,
                   "screen_artifact_id":13273699027,"screen_run_id":41728821986,
                   "screen_commit":"d811332d1bb0c0f002b8fd5e7df8d42de624d293",
                   "screen_zip_sha":"c7a86e380d6acef20e18fa7a0ba150cbfa6ef414c680c0ec77708eba0bc5406c",
                   "binary_sha":Q.t.digest(binary),"source_patch_sha":Q.t.digest(arm/"source.patch"),
                   "red":receipt["red"]["rc"], "authentic":receipt["green"]["rc"],
                   "five_forged":[x["rc"] for x in receipt["forged"]],
                   "retained":[x["rc"] for x in receipt["retained"]]}
        Q.t.write_json(OUT / "authenticated_causal_receipts.json", matched)
        print("AC_CAUSAL_REUSE",json.dumps(matched),flush=True)
        return kernel,binary,build_env,arm

    Q.D.patch_source=compose_patch
    Q.source_qualified_candidate=build_and_authenticate
    try:
        Q.main()
    finally:
        Q.D.patch_source=old_patch
        Q.source_qualified_candidate=old_builder
    protected=json.loads((OUT/"qualification.json").read_text())["candidate"]
    full=json.loads((OUT/"full.json").read_text())
    assert protected["qualified"] and full["qualified"]
    summary={"status":"WARRANTED_BOUNDED", "source_patch_sha":SOURCE_PATCH_SHA,
             "binary_sha":CANDIDATE_SHA,"source_ac_prefix":AC.AC_SHA,
             "previous_k_binary":AC.K_SHA,
             "native_nonregression":protected["native_nonregression"],
             "source_controls_unchanged":protected["controls_unchanged"],
             "arena_verdict_changes":protected["verdict_changes"],
             "extra_unchanged":protected["extra_unchanged"],
             "complete_mathlib_accept":full["complete_mathlib_accept"],
             "terminal":full["terminal"],"next_frontier":full["next_frontier"],
             "arena_official_run":False}
    Q.t.write_json(OUT/"ac_qualification.json",summary)
    print("AC_PROTECTED_QUALIFICATION",json.dumps(summary),flush=True)


if __name__=="__main__":
    main()
