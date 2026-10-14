#!/usr/bin/env python3
"""Conservative V3 source-bound paper reanalysis: manual mapping, no new physics."""
from pathlib import Path
import hashlib,json,subprocess
from fractions import Fraction as F
from decimal import Decimal as D
from canonical_probe import extract as extract_scientific_abstract
from rounding_envelope import (Unknown,nature,qattan_first,qattan_second,
    qattan_magnetic,rounded_covariance_envelope,unsafe_midpoint_only,
    independent_decimal_check)
ROOT=Path(__file__).resolve().parent
OUT=ROOT/"evidence"
OUT.mkdir(exist_ok=True)
PUB_URL="https://journals.aps.org/prc/abstract/10.1103/f6gq-ghvh"
# Frozen from separate original publisher source-probe run #38492414481,
# BEFORE this qualification. Do not silently update to force acceptance.
CANONICAL_PUBLISHER_ABSTRACT_SHA="e9edf0fe447fa17611608610ff9ead098fba23fb056547a544a394c738da7cb6"
FIRST_RAW_WRAPPER_SHA="74c110d63bed05650e9ae13a9d5611ae80c77e4ac8fcfda99adeaa34fded0d4d"
NATURE_AUTHOR_SHA="758181d221327797c87758f17cabfece0632a9f0394138da0c9ebac10d4b25f4"

def get_source():
    raw_path=Path("/tmp/scattering_2026_original.html")
    p=subprocess.run(["curl","-L","--fail","--silent","--show-error","--max-time","40",
      "-A","Mozilla/5.0","-o",str(raw_path),PUB_URL],capture_output=True,text=True,timeout=55)
    if p.returncode or not raw_path.is_file():
        raise Unknown("PUBLISHER_SOURCE_NOT_RETRIEVED:"+p.stderr[-200:])
    raw=raw_path.read_bytes()
    h=hashlib.sha256(raw).hexdigest()
    canonical=extract_scientific_abstract(raw)
    if canonical.get("strategy")!="PUBLISHER_DESCRIPTION_META" or "abstract" not in canonical:
        raise Unknown("SCIENTIFIC_ABSTRACT_NOT_EXTRACTED")
    digest=hashlib.sha256(canonical["abstract"].encode("utf-8")).hexdigest()
    if digest!=CANONICAL_PUBLISHER_ABSTRACT_SHA:
        raise Unknown("SCIENTIFIC_ABSTRACT_CONTENT_CHANGED_NO_WARRANT:"+digest)
    needed=["f6gq-ghvh","0.854","0.851","2012","2015","stat","sys"]
    text=raw.decode("utf-8",errors="replace").lower()
    matched={t:t.lower() in text for t in needed}
    if not all(matched.values()):
        raise Unknown("PUBLISHER_SOURCE_ANCHORS_MISSING:"+str(matched))
    altered=canonical["abstract"].replace("0.851","0.850",1)
    if hashlib.sha256(altered.encode()).hexdigest()==digest:
        raise AssertionError("SCIENTIFIC_CONTENT_MUTATION_NOT_DETECTED")
    return {"source":"original_prc_canonical_abstract_content",
      "url":PUB_URL,"canonical_sha256":digest,
      "canonical_source_probe":"https://github.com/heathsanchez/test/actions/runs/38492956938",
      "raw_transport_sha256":h,"raw_bytes":len(raw),
      "raw_html_equal_first_probe":h==FIRST_RAW_WRAPPER_SHA,
      "source_content_not_full_bytes":True,
      "matched":matched,
      "publisher_full_pdf":"INACCESSIBLE_401",
      "semantic_mapping":"HUMAN_DECLARED_NOT_AUTONOMOUS"}

def main():
    # Reuse exact green V2 evidence as a preserved prior product, not new data.
    v2_path=ROOT.parent/"nist_hydrogen_crosssource"/"evidence"/"hydrogen_v2_result.json"
    if not v2_path.is_file():
        raise Unknown("PRIOR_V2_ORIGINAL_SOURCE_RUN_REQUIRED")
    v2=json.loads(v2_path.read_text())
    if v2.get("status")!="WARRANTED_BOUNDED_SOURCE_BOUND_TWO_STUDY_CONTRAST":
        raise Unknown("PRIOR_V2_NOT_QUALIFIED")
    if v2["source_retrieval"]["nature2026"]["sha256"]!=NATURE_AUTHOR_SHA:
        raise Unknown("ORIGINAL_NATURE_AUTHOR_SOURCE_CHANGED")
    src=get_source()
    first=rounded_covariance_envelope(nature(),qattan_first())
    second=rounded_covariance_envelope(nature(),qattan_second())
    assert first["verdict"]=="UNKNOWN_UNDER_ROUNDING_OR_COVARIANCE"
    assert second["verdict"]=="WARRANTED_BOUNDED_ROUNDING_COVARIANCE_ROBUST_2SIGMA_TENSION"
    assert F(first["guaranteed_z_lower"])==F(257,151)
    assert F(second["guaranteed_z_lower"])==F(197,91)
    assert unsafe_midpoint_only(nature(),qattan_first())>2
    # Independent traditional Decimal implementation (not shared engine).
    for r,model in [(first,qattan_first()),(second,qattan_second())]:
        exact=F(r["guaranteed_z_lower"])
        check=independent_decimal_check(nature(),model)
        self_value=D(exact.numerator)/D(exact.denominator)
        assert abs(check-self_value)<D("1e-45")
    try:
        rounded_covariance_envelope(qattan_first(),qattan_second())
        raise AssertionError("SAME_SCATTERING_DATA_WAS_DOUBLE_COUNTED")
    except Unknown as exc:
        assert str(exc)=="SAME_UNDERLYING_DATA_NO_INDEPENDENT_CONTRAST"
    try:
        rounded_covariance_envelope(nature(),qattan_magnetic())
        raise AssertionError("MAGNETIC_RADIUS_WAS_CAST_AS_ELECTRIC_RADIUS")
    except Unknown as exc:
        assert str(exc)=="MEASURAND_MISMATCH"
    result={
      "status":"WARRANTED_BOUNDED_SOURCE_CONTENT_ROUNDING_SAFE_CONTRAST",
      "source":src,"inherited_source":v2["source_retrieval"]["nature2026"],
      "independent_raw_scattering_experiments_added":0,
      "scattering_source_event_count":1,"scattering_fit_approaches_count":2,
      "source_model":"ORIGINAL_2012_AND_2015_FORM_FACTOR_DATA_REANALYZED",
      "old_source_consequence_unchanged":v2["consequences"]["preserved_2022_atomic_velocity"],
      "first_fit":{"naive_midpoint_z":str(unsafe_midpoint_only(nature(),qattan_first())),
                   "conservative":first},
      "second_fit":{"conservative":second},
      "scientific_interpretation":"CONDITIONAL_ON_COMPARABLE_RADIUS_DEFINITIONS_AND_STATED_ERRORS",
      "new_physical_measurement":False,
      "actual_unmodeled_systematic_errors":"UNKNOWN",
      "new_effective_semantic_extraction_method":"NOT_GENERATED_HUMAN_ADAPTER",
      "independent_theory_qed_recheck":False,
      "independent_baseline":"EXACT_FRACTION_AGREES_WITH_DECIMAL",
      "full_source_claim_statement_binding":"NOT_CHECKED_CANONICAL_ABSTRACT_PLUS_MANUAL_MAPPING",
      "cross_source_likelihood_pooled":"WITHHELD",
      "autonomous_experiment_design":"UNKNOWN",
      "E2E_SYSTEM_L7":"UNKNOWN"}
    (OUT/"v3_result.json").write_text(json.dumps(result,indent=2)+"\n")
    print(json.dumps(result,indent=2))
if __name__=="__main__":
    main()
