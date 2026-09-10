"""Fail-closed authority for developmental discrimination, emitted only on PASS."""
from .arc_discrimination import PARENT, ARC_COMMIT, ARC_REPOSITORY
from .runtime import digest
V3_RUN=34418702843
V3_EVIDENCE="8c6cd75bb2e776d1b6cf7a0a777200045f16077bb1c62eae45f5ff52626434b1"
V3_ARTIFACT_SHA256="8501e4df13c6c9eddb1cf68fe0eabbd26c7ed60df639e17cee696e17dfc51651"
def require(x,m):
    if not x:raise ValueError(m)
def build(source_commit,run_id,freeze,stream,decisions,evaluation):
    require(evaluation.get("outcome")=="DEVELOPMENTAL_DISCRIMINATION_V1_PASS" and evaluation.get("v4_eligible") is True,"discrimination did not qualify")
    require(evaluation.get("accuracy")==1.0 and all(evaluation["route_counts"].get(k,0)>0 for k in ("REUSE","EXAPTATION","EXPANSION","UNKNOWN")),"route gate failed")
    require(freeze["canonical_parent"]==PARENT and freeze["source_commit"]==source_commit,"freeze mismatch")
    require(stream["external_repository"]==ARC_REPOSITORY and stream["external_commit"]==ARC_COMMIT and stream["route_labels_present"] is False,"external stream failed")
    require(decisions["stream_digest"]==stream["stream_digest"] and decisions["labels_seen"] is False,"decision chronology failed")
    require(evaluation["stream_digest"]==stream["stream_digest"] and evaluation["decisions_digest"]==decisions["decisions_digest"],"evaluation binding failed")
    require(freeze.get("freeze_digest")==digest({k:v for k,v in freeze.items() if k!="freeze_digest"}),"stale freeze")
    require(stream.get("stream_digest")==digest({k:v for k,v in stream.items() if k!="stream_digest"}),"stale stream")
    require(decisions.get("decisions_digest")==digest({k:v for k,v in decisions.items() if k!="decisions_digest"}),"stale decisions")
    require(evaluation.get("evidence_digest")==digest({k:v for k,v in evaluation.items() if k!="evidence_digest"}),"stale evaluation")
    require(len(decisions["results"])==len(stream["tasks"])==evaluation["task_count"] and evaluation["task_count"]>=12,"task binding failed")
    for row,scored in zip(decisions["results"],evaluation["rows"]):
        route=row["predicted_route"]; residual=row.get("residual"); admissions=row["controls"]["new_admissions"]
        require(route==scored["predicted"]==scored["ground_truth"] and scored["match"] and scored["causal_held_out_verified"] and (route=="UNKNOWN" or scored["held_out_verified"]),"route or held-out gate failed")
        require(row["warm_verdict"] in ("verified","unknown"),"invalid verdict")
        require(row["verifier_identity"].startswith("arc-exact-grid-replay-v1:"),"stale verifier")
        if route=="REUSE":
            require(row["cold_verdict"]=="verified" and not admissions and row["cold_certificate"].get("executed") in row["pre_state"]["capabilities"],"false REUSE")
        if route=="EXAPTATION":
            w=residual.get("verifier_certified_witness",{}) if residual else {}
            require(row["cold_verdict"]=="unknown" and residual.get("class")=="ROLE_REQUALIFICATION_REQUIRED" and w.get("direct_survivors")==[] and w.get("role_survivors") and len(admissions)==1,"false EXAPTATION")
        if route=="EXPANSION":
            w=residual.get("verifier_certified_witness",{}) if residual else {}
            require(row["cold_verdict"]=="unknown" and residual.get("class")=="OLD_LANGUAGE_OBSTRUCTION" and residual.get("evidence_strength")=="finite-exhaustive" and w.get("old_language_complete") is True and w.get("old_program_count")==16 and w.get("direct_survivors")==[] and w.get("role_survivors")==[] and len(admissions)==1,"false EXPANSION")
        if route in ("EXAPTATION","EXPANSION"):
            c=row["controls"];require(c.get("restart")=="verified" and c.get("exact_removal")=="unknown" and c.get("ancestor_removal")=="unknown" and c.get("restoration")=="verified" and c.get("unrelated_removal")=="verified" and c.get("sham")=="unknown" and c.get("wrong_direction")=="unknown" and c.get("fixed_policy")=="unknown" and c.get("raw_history_without_admission")=="unknown","causal controls failed")
            require(c.get("original_scope_unchanged") is True and set(row["admitted_records"])==set(admissions),"scope or admission mismatch")
        if route=="UNKNOWN":require(row["cold_verdict"]=="unknown" and residual.get("class")=="NO_JUSTIFIED_CHANGE" and not admissions and not row["admitted_records"],"hidden UNKNOWN admission")
    body={"schema":"open-development-release/v4","claim":"bounded externally selected developmental route discrimination","canonical_parent":PARENT,"source_commit":source_commit,"run_id":run_id,
          "v3":{"run_id":V3_RUN,"evidence_digest":V3_EVIDENCE,"artifact_sha256":V3_ARTIFACT_SHA256},"freeze_digest":freeze["freeze_digest"],"external":{"repository":ARC_REPOSITORY,"commit":ARC_COMMIT,"corpus_digest":stream["corpus_identity"]["corpus_digest"]},"stream_digest":stream["stream_digest"],"decisions_digest":decisions["decisions_digest"],"evaluation_digest":evaluation["evidence_digest"],"route_counts":evaluation["route_counts"],"confusion_matrix":evaluation["confusion_matrix"],"limitations":["finite supplied grid languages","ARC training outputs are verifier targets","Python operational qualification","no human blinding","no unrestricted grammar invention"]}
    return {**body,"evidence_digest":digest(body)}
def validate(m,freeze,stream,decisions,evaluation):
    require(m.get("evidence_digest")==digest({k:v for k,v in m.items() if k!="evidence_digest"}),"stale v4")
    require(m==build(m["source_commit"],m["run_id"],freeze,stream,decisions,evaluation),"v4 mismatch")
