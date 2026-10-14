#!/usr/bin/env python3
"""2026 hydrogen: source-anchored, HUMAN-MAPPED, bounded consequence replay.

This program does NOT extract equations or scientific semantics autonomously.
Its manually declared mapping is frozen in FROZEN_PROTOCOL.md; the original
publisher/author manuscript source must be independently byte-pinned in CI.
"""
import hashlib,html,json,re,subprocess,sys,unicodedata
from decimal import Decimal as D,getcontext
from fractions import Fraction as F
from html.parser import HTMLParser
from pathlib import Path
from consequence_core import (C,q,canonical,robust_consistency,Ledger,UnknownEvidence,
                              contrast_measured_predicted,joint_covariance_diagnostic,
                              independent_pooled_mean,declared_within_source_correlation)
getcontext().prec=55
ROOT=Path(__file__).resolve().parent
EVIDENCE=ROOT/"evidence"
EVIDENCE.mkdir(exist_ok=True)

# SOURCE PINS acquired by the prior separate source reachability run,
# before this method's implementation. Failure is evidence; never repin
# automatically from content found in the current run.
SOURCES={
 "nature2026":{
  "url":"https://arxiv.org/pdf/2602.14980v1",
  "sha256":"758181d221327797c87758f17cabfece0632a9f0394138da0c9ebac10d4b25f4",
  "hints":["0.8406(15)","10,973,731.568152","0.94","730,690,248,610.79"]},
 "bullis2026":{
  "url":"https://arxiv.org/pdf/2604.26401v1",
  "sha256":"79b0e291be20049b5df9bf895722c6b39a4c2e68e5e17bc86669de5a6e0ebe7e",
  "hints":["0.8433(31)","0.8422(31)","3289841960252.9"]}}

def fail_closed_source(raw,expected):
    digest=hashlib.sha256(raw).hexdigest()
    if digest!=expected:
        raise UnknownEvidence("SOURCE_BYTES_NOT_EQUAL_FROZEN_PIN")
    return digest

def fetch_sources():
    rec={}
    for sid,source in SOURCES.items():
        path=Path("/tmp/hydrogen_"+sid+".pdf")
        x=subprocess.run(
            ["curl","-A","Mozilla/5.0","-L","--fail","--silent",
             "--show-error","--max-time","50","--retry","2",
             "-o",str(path),source["url"]],
            capture_output=True,text=True,timeout=160)
        if x.returncode or not path.exists():
            raise UnknownEvidence("ORIGINAL_PDF_FETCH_FAILED_"+sid+":"+x.stderr[-150:])
        raw=path.read_bytes()
        if raw[:4]!=b"%PDF":
            raise UnknownEvidence("NON_PDF_ORIGINAL")
        dig=fail_closed_source(raw,source["sha256"])
        out=Path("/tmp/hydrogen_"+sid+".txt")
        subprocess.run(["pdftotext","-layout",str(path),str(out)],check=True)
        normalized=re.sub(r"\s+","",out.read_text(errors="replace"))
        if not all(hint.replace(" ","") in normalized for hint in source["hints"]):
            missing=[hint for hint in source["hints"] if hint.replace(" ","") not in normalized]
            raise UnknownEvidence("ORIGINAL_SOURCE_VALUE_ANCHOR_MISSING_"+sid+":"+repr(missing))
        rec[sid]={"url":source["url"],"sha256":dig,
                  "original_pdf_bytes":len(raw),
                  "human_semantic_mapping":"DECLARED_ADAPTER_NOT_MACHINE_DISCOVERED",
                  "text_anchors_present":True,
                  "version_immutable":"arxiv_v1"}
    original=Path("/tmp/hydrogen_bullis2026.pdf").read_bytes()
    modified=bytearray(original);modified[9]^=1
    try:
        fail_closed_source(bytes(modified),SOURCES["bullis2026"]["sha256"])
        raise AssertionError("SOURCE_BYTE_CORRUPTION_ACCEPTED")
    except UnknownEvidence as ex:
        assert str(ex)=="SOURCE_BYTES_NOT_EQUAL_FROZEN_PIN"
    return rec

def evidence_model(source_records):
    l=Ledger()
    assert l.add_event("nature2026",source_records["nature2026"]["sha256"],
                       source_records["nature2026"]["url"])
    assert l.add_event("bullis2026",source_records["bullis2026"]["sha256"],
                       source_records["bullis2026"]["url"])
    assert not l.add_event("bullis2026",source_records["bullis2026"]["sha256"],
                           source_records["bullis2026"]["url"])
    assert l.count_events()==2
    nature_rp=q("proton_radius","0.8406","0.0015","fm","nature2026","nature-QED",
            ("nature-2S6P-experiment","shared-1S2S","nature-QED","alpha2022"))
    nature_R=q("rydberg_constant","10973731.568152","0.000014","m^-1",
            "nature2026","nature-QED",
            ("nature-2S6P-experiment","shared-1S2S","nature-QED","alpha2022"))
    bullis_current=q("proton_radius","0.8433","0.0031","fm",
            "bullis2026","bullis-updated-QED",
            ("bullis-2S8S-9S-10S-experiment","shared-1S2S","bullis-updated-QED","alpha2022"))
    bullis_old=q("proton_radius","0.8422","0.0031","fm",
            "bullis2026","bullis-CODATA2022-theory",
            ("bullis-2S8S-9S-10S-experiment","shared-1S2S","bullis-CODATA2022-theory","alpha2022"))
    bullis_cR=q("rydberg_frequency","3289841960252.9","9.7","kHz",
            "bullis2026","bullis-updated-QED",
            ("bullis-2S8S-9S-10S-experiment","shared-1S2S","bullis-updated-QED","alpha2022"))
    items={"nature_rp":nature_rp,"nature_R":nature_R,
           "bullis_rp_new":bullis_current,"bullis_rp_old":bullis_old,
           "bullis_cR":bullis_cR}
    for name,v in items.items():
        assert l.add_product(name,v)
    assert l.count_events()==2 and len(l.products)==5
    # Nature's measured and theory-predicted frequency share the same
    # reporter paper but their actual experimental and model supports differ.
    nature_obs=q("hydrogen_transition_frequency","730690248610.79","0.48","kHz",
             "nature2026","measurement",("nature-2S6P-experiment",))
    nature_SM=q("hydrogen_transition_frequency","730690248610.79","0.23","kHz",
             "nature2026","SM-QED+muonic-radius",
             ("shared-1S2S","muonic-proton-radius","nature-QED","alpha2022"))
    # Nature's +0.94 reported correlation is a WITHIN-STUDY covariance.
    corr=joint_covariance_diagnostic(declared_within_source_correlation("0.94","nature2026:rp_vs_Rinf"))
    for forged in [None,"0", "-0.94", "0.4"]:
        try:
            declared_within_source_correlation(forged,"nature2026:rp_vs_Rinf")
            raise AssertionError("FORGED_CORRELATION_ACCEPTED")
        except UnknownEvidence:
            pass
    # Exact rational, uncertainty-only conclusion even when unknown
    # cross-paper rho ranges freely through [-1,+1].
    rp=robust_consistency(nature_rp,bullis_current)
    ryd=robust_consistency(nature_R,bullis_cR)
    old=robust_consistency(nature_rp,bullis_old)
    assert all(r["verdict"]=="WARRANTED_BOUNDED_ROBUST_CONSISTENCY" for r in [rp,ryd,old])
    # NIST R to Nature R is NOT uniformly <2sigma under every unknown
    # covariance; the result must fail closed despite numerical closeness.
    nist_R=q("rydberg_constant","10973731.568157","0.000012","m^-1",
             "codata2022","published-adjustment",("nist2022-adjustment",))
    nist_contrast=robust_consistency(nature_R,nist_R)
    assert nist_contrast["verdict"].startswith("UNKNOWN")
    # Duplicate campaign, fake alias, source conflict negative controls.
    try:
        l.add_event("invented-second-bullis",source_records["bullis2026"]["sha256"],
                    source_records["bullis2026"]["url"])
        raise AssertionError("SOURCE_ALIAS_ACCEPTED")
    except UnknownEvidence as ex:
        assert str(ex)=="SOURCE_ALIAS_DUPLICATE"
    try:
        l.insert_claim("nature2026","inverse_alpha","FIXED_INPUT")
        raise AssertionError("ALPHA_INPUT_PROMOTED_AS_NEW_OBSERVATION")
    except UnknownEvidence as ex:
        assert str(ex)=="INPUT_NOT_INDEPENDENT_ALPHA_OBSERVATION"
    try:
        independent_pooled_mean(nature_rp,bullis_current)
        raise AssertionError("UNKNOWN_COVARIANCE_MEAN_PROMOTED")
    except UnknownEvidence as ex:
        assert str(ex)=="UNKNOWN_CROSS_STUDY_COVARIANCE_NO_POOLED_MEAN"
    try:
        joint_covariance_diagnostic(None)
        raise AssertionError("MISSING_COVARIANCE_ACCEPTED")
    except UnknownEvidence as ex:
        assert str(ex)=="UNKNOWN_WITHIN_SOURCE_COVARIANCE"
    # Source-preserving theory-version switch: NO new measurement event.
    assert bullis_current.value-bullis_old.value==F("0.0011")
    before=l.resolve("bullis_rp_new")
    l.revoke("bullis-updated-QED")
    revoked_new=l.resolve("bullis_rp_new")
    unaffected_old=l.resolve("bullis_rp_old")
    unaffected_nature=l.resolve("nature_rp")
    unaffected_nature_R=l.resolve("nature_R")
    l.restore("bullis-updated-QED")
    restored=l.resolve("bullis_rp_new")
    assert before.startswith("WARRANTED") and restored.startswith("WARRANTED")
    assert revoked_new=="UNKNOWN_REVOKED_SUPPORT"
    assert unaffected_old.startswith("WARRANTED")
    assert unaffected_nature.startswith("WARRANTED")
    assert unaffected_nature_R.startswith("WARRANTED")
    assert l.count_events()==2
    # Strong conventional baseline: a separate decimal backend must agree
    # to high precision with exact-rational unit comparison.
    dC=D(299792458)
    nature_freq=D("10973731.568152")*dC/D(1000)
    nature_unc=D("0.000014")*dC/D(1000)
    delta=abs(nature_freq-D("3289841960252.9"))
    lower=abs(nature_unc-D("9.7"))
    r_delta=F(ryd["delta_exact"])
    r_lower=F(ryd["minimum_difference_sigma_exact"])
    expected_delta=D(r_delta.numerator)/D(r_delta.denominator)
    expected_lower=D(r_lower.numerator)/D(r_lower.denominator)
    assert abs(delta-expected_delta)<D("1e-27")
    assert abs(lower-expected_lower)<D("1e-27")
    assert delta < D(2)*lower
    # SM-predicted contrast only in the paper's exact supplied model scope.
    model_contrast=contrast_measured_predicted(nature_obs,nature_SM)
    assert model_contrast["difference_kHz"]=="0"
    assert F(model_contrast["variance_kHz_sq"])==F("0.2833")
    return {
      "source_events":l.count_events(),"derived_products":len(l.products),
      "same_experiment_theory_versions":["bullis_rp_old","bullis_rp_new"],
      "delta_rp_theory_update_fm":str(bullis_current.value-bullis_old.value),
      "rp_robust":rp,"rydberg_robust":ryd,"rp_old_theory_robust":old,
      "nist_2022_rydberg_robust":nist_contrast,
      "nature_within_study_covariance":corr,
      "nature_measurement_vs_model":model_contrast,
      "supports_requalification":{"new_before":before,"new_revoked":revoked_new,
              "old_unaffected":unaffected_old,"other_paper_unaffected":unaffected_nature,
              "unrelated_nature_R_unaffected":unaffected_nature_R,"new_restored":restored},
      "withheld_cross_source_covariance":"UNKNOWN_NO_POOLED_ESTIMATE",
      "fixed_input_alpha_from_previous_NIST_adjustment":"NO_NEW_ALPHA_OBSERVATION",
      "independent_baseline":"MATCHED_CONVENTIONAL_DECIMAL_RATIONAL_UNITS",
      "automated_source_semantic_extraction":"NOT_DONE_HUMAN_MAPPED",
      "new_physical_experiment_selected":"UNKNOWN"
    }
def main():
    evidence=fetch_sources()
    r=evidence_model(evidence)
    # Source-verifier replay is inherited, not newly authored alpha theory.
    orig=ROOT.parent/"nist_alpha_consequence"/"evidence"/"ci_report.json"
    if not orig.exists():
        raise UnknownEvidence("PINNED_2022_ALPHA_BASELINE_NOT_REPLAYED_IN_THIS_JOB")
    original=json.loads(orig.read_text())
    if original.get("result")!="PASS_BOUNDED_NUMERICAL_REPLAY_ONLY":
        raise UnknownEvidence("ORIGINAL_2022_ALPHA_NOT_QUALIFIED")
    r["preserved_2022_alpha_inverse"]=original["inverse_alpha"]
    r["preserved_2022_atomic_velocity"]=original["atomic_unit_velocity_m_s"]
    r["original_2022_source_authority"]="PREVIOUSLY_QUALIFIED_EXACT_NIST_REPORT_RUN_38490002962"
    r["original_2022_independent_script_sha256"]=original["code_sha256"]
    result={"status":"WARRANTED_BOUNDED_SOURCE_BOUND_TWO_STUDY_CONTRAST",
            "source_retrieval":evidence,"consequences":r,
            "source_bytes_pinned":True,"source_scientific_semantics":"MANUALLY_DECLARED",
            "full_native_QED_theory_recalculation":False,
            "outside_owner_adoption":False,
            "E2E_SYSTEM_L7":"UNKNOWN"}
    p=EVIDENCE/"hydrogen_v2_result.json"
    p.write_text(json.dumps(result,indent=2)+"\n")
    print(json.dumps(result,indent=2))
if __name__=="__main__":
    main()
