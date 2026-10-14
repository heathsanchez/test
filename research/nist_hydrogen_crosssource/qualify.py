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
                              independent_pooled_mean)
getcontext().prec=55
ROOT=Path(__file__).resolve().parent
EVIDENCE=ROOT/"evidence"
EVIDENCE.mkdir(exist_ok=True)

# SOURCE PINS acquired by the prior separate source reachability run,
# before this method's implementation. Failure is evidence; never repin
# automatically from content found in the current run.
SOURCES={
 "nature2026":{
  "url":"https://www.nature.com/articles/s41586-026-10124-3",
  "sha256":"b83251eae9a24e40deb2500008b75763a47d506a34d94c80edbed1e9b6e12737",
  "hints":["0.8406","0.94","s41586-026-10124-3"]},
 "bullis2026":{
  "url":"https://arxiv.org/html/2604.26401",
  "sha256":"cdbb6027f1b175acd4f1e1a02cbbe173018b176c75d48eb25a7f914555845c26",
  "hints":["0.8433","0.8422","2604.26401"]}}
class Text(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.parts=[]
    def handle_data(self,v):
        self.parts.append(v)
def visible_text(raw):
    parser=Text()
    parser.feed(raw.decode("utf-8",errors="replace"))
    return unicodedata.normalize("NFKC",html.unescape(" ".join(parser.parts)))
def normalized_numeric_text(txt):
    # Only use for presence of manually interpreted source values.
    # This is NOT a scientific PDF/HTML semantic parser.
    t=txt
    for _ in range(8):
        new=re.sub(r"(?<=\d)[\s,\u2009\u202f]+(?=\d)", "", t)
        if new==t: break
        t=new
    return t
def fail_closed_source(raw,expected):
    digest=hashlib.sha256(raw).hexdigest()
    if digest!=expected:
        raise UnknownEvidence("SOURCE_BYTES_NOT_EQUAL_FROZEN_PIN")
    return digest
def fetch_sources():
    rec={}
    for sid,source in SOURCES.items():
        path=Path("/tmp/hydrogen_"+sid+".html")
        x=subprocess.run(
            ["curl","-A","Mozilla/5.0 (compatible; ResearchEvidence/1.0)",
             "-L","--fail","--silent","--show-error","--max-time","40",
             "--retry","2","-o",str(path),source["url"]],
            capture_output=True,text=True,timeout=150)
        if x.returncode or not path.exists():
            raise UnknownEvidence("SOURCE_FETCH_FAILED_"+sid+":"+x.stderr[-150:])
        raw=path.read_bytes()
        dig=fail_closed_source(raw,source["sha256"])
        visible=normalized_numeric_text(visible_text(raw))
        # Every published value is manually mapped below, not inferred
        # from source syntax; require at least frozen unambiguous anchors.
        if not all(hint in visible or hint in raw.decode("utf-8","replace") for hint in source["hints"]):
            raise UnknownEvidence("SOURCE_TEXT_ANCHOR_MISSING_"+sid)
        rec[sid]={"url":source["url"],"sha256":dig,
                  "source_bytes":len(raw),"human_semantic_mapping":"DECLARED_ADAPTER",
                  "text_anchors_present":True}
    # Independent one-byte corruption negative.
    original=Path("/tmp/hydrogen_bullis2026.html").read_bytes()
    mutated=bytearray(original);mutated[9]^=1
    try:
        fail_closed_source(bytes(mutated),SOURCES["bullis2026"]["sha256"])
        raise AssertionError("CORRUPTED_SOURCE_ACCEPTED")
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
    corr=joint_covariance_diagnostic(F("0.94"))
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
