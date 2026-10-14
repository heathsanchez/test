#!/usr/bin/env python3
"""Source-byte-qualified replay of two original spectroscopy presentations.

All published source identities are pinned and checked, but Nature's Eq. 7
semantic coefficients are human-declared. No autonomous theory extraction.
"""
from dataclasses import replace
from decimal import Decimal as D, localcontext, ROUND_HALF_UP
from fractions import Fraction as F
from pathlib import Path
import hashlib,json,re,subprocess
from affine_core import (Datum,SourceParseFailure,table_rows,reproduce_table,
                         holdout_centroid,linear_map,independent_variance)
ROOT=Path(__file__).resolve().parent
EVIDENCE=ROOT/"evidence"
EVIDENCE.mkdir(exist_ok=True)
ORIGINALS={
 "bullis2026":{"source":Path("/tmp/hydrogen_bullis2026.pdf"),
               "digest":"79b0e291be20049b5df9bf895722c6b39a4c2e68e5e17bc86669de5a6e0ebe7e",
               "url":"https://arxiv.org/pdf/2604.26401v1"},
 "nature2026":{"source":Path("/tmp/hydrogen_nature2026.pdf"),
               "digest":"758181d221327797c87758f17cabfece0632a9f0394138da0c9ebac10d4b25f4",
               "url":"https://arxiv.org/pdf/2602.14980v1"}}

def input_source_text():
    out={}
    for identity,info in ORIGINALS.items():
        if not info["source"].exists():
            raise SourceParseFailure("PREDECESSOR_ORIGINAL_PDF_NOT_AVAILABLE_"+identity)
        raw=info["source"].read_bytes()
        if not raw.startswith(b"%PDF") or hashlib.sha256(raw).hexdigest()!=info["digest"]:
            raise SourceParseFailure("ORIGINAL_AUTHOR_PDF_IDENTITY_MISMATCH_"+identity)
        textpath=Path("/tmp/nist_native_"+identity+".txt")
        subprocess.run(["pdftotext","-layout",str(info["source"]),str(textpath)],check=True)
        out[identity]=textpath.read_text(errors="replace")
    return out

def as_decimal(v:F):
    with localcontext() as ctx:
        ctx.prec=50
        return D(v.numerator)/D(v.denominator)

def calculate(texts):
    # The source parser reads signed correction values directly from pinned original PDF.
    # It does not read the targets until after computing the right hand side.
    btext=texts["bullis2026"]
    if "TABLE I. Systematic corrections" not in btext:
        nearby=[line[:220] for line in btext.splitlines() if "TABLE I" in line or "Systematic corrections" in line]
        raise SourceParseFailure("BULLIS_ORIGINAL_TABLE_HEADING_MISSING:"+repr(nearby[:5]))
    rows=table_rows(btext)
    results=reproduce_table(rows)
    if not all(r["exact_value_match"] and r["rss_rounded_sigma_match"] for r in results):
        raise SourceParseFailure("BULLIS_TABLE_ORIGINAL_NOT_RECONSTRUCTED:"+repr(results))
    # Independently repeat with Decimal arithmetic, not affine_core.linear_map.
    with localcontext() as ctx:
        ctx.prec=50
        for col in range(3):
            baseline=sum((as_decimal(vals[col].value) for role,vals in rows[:-1]),D(0))
            if baseline != as_decimal(rows[-1][1][col].value):
                raise SourceParseFailure("INDEPENDENT_BASELINE_DISAGREES")
    nature=holdout_centroid(texts["nature2026"])
    # Derivation is independent of Bullis table branch (same exact affine kernel).
    # Preserve distinct source identity and explain possible covariance dependencies.
    # Model support and predicted ν absent from this subtest; previously V2 scoped.
    # Deliberate mutation/ablation controls with all other values held fixed.
    corrupt=rows.copy()
    label,vals=corrupt[1]
    altered=vals.copy()
    altered[0]=replace(vals[0], value=-vals[0].value)
    corrupt[1]=(label,altered)
    mut=reproduce_table(corrupt)
    if mut[0]["exact_value_match"]:
        raise SourceParseFailure("DID_NOT_DETECT_SIGN_FLIP")
    # Isolated single-column sign flip must leave the other two intact.
    if not mut[1]["exact_value_match"] or not mut[2]["exact_value_match"]:
        raise SourceParseFailure("SIGN_FLIP_OVERAFFECTED_OTHER_COLUMNS")
    # Source-row deletion blocks successful normalization rather than
    # silently changing the meaning of a complete submitted source.
    try:
        reproduce_table(rows[:2]+rows[3:])
        raise AssertionError("SOURCE_CORRECTION_DELETION_ACCEPTED")
    except SourceParseFailure as exc:
        if str(exc)!="MISSING_OR_DUPLICATE_TABLE_ROW": raise
    # False amended source cannot be substituted for original author PDF.
    bullis_bytes=ORIGINALS["bullis2026"]["source"].read_bytes()
    corrupted=bytearray(bullis_bytes);corrupted[10]^=1
    if hashlib.sha256(corrupted).hexdigest()==ORIGINALS["bullis2026"]["digest"]:
        raise SourceParseFailure("SOURCE_BYTE_MUTATION_NOT_REJECTED")
    # Independent uncertainty check = conditionally reproduces displayed RSS.
    # No attempt to assume original experimental errors independent in nature,
    # so the physical covariance conclusion remains explicitly unsupported.
    return {
        "source_bullis_table":{"row_count":len(rows),
            "three_experiment_columns":3,
            "source_row_labels":[label for label,_ in rows],
            "inputs":[{"label":name,
                       "values_kHz":[str(x.value) for x in values],
                       "sigmas_kHz":[str(x.sigma) for x in values]}
                      for name,values in rows[:-1]],
            "outputs":[{"col":r["col"],"reconstructed_value_kHz":str(r["value"]),
                        "published_value_kHz":str(r["reported"]),
                        "rounded_rss_sigma_kHz":r["rss_rounded_sigma"],
                        "published_sigma_kHz":r["reported_sigma"],
                        "exact_value_reproduced":r["exact_value_match"],
                        "display_sigma_reproduced":r["rss_rounded_sigma_match"]}
                        for r in results],
            "uncertainty_interpretation":"NUMERIC_RSS_MATCH_ONLY_COVARIANCE_ASSUMPTION_NOT_INDEPENDENTLY_PROVED",
            "manual_semantic_adapter":"TABLE_I_SIGNED_ADDITIVE_CORRECTIONS",
            "three_source_columns_are_independent_experiments":"NOT_CHECKED"},
        "source_nature_centroid":nature,
        "common_reused_rule":"exact affine linear_map on source-derived fractions",
        "cross_presentation":"BULLIS_3_COLUMN_SIGNED_CORRECTIONS_AND_NATURE_WEIGHTED_CENTROID",
        "conditional_uncertainty_unknowns":{
            "bullis":"original correction covariance not independently established",
            "nature":"measured centroid uncertainty cannot be reconstructed from marginal sigmas alone"},
        "negative_controls":{
            "bullis_correction_sign_flip":"DETECTED_EXACT_CONSEQUENCE_MISMATCH",
            "unaffected_two_columns":"PASS",
            "bullis_source_row_deletion":"REJECTED",
            "upstream_pdf_byte_mutation":"REJECTED_BY_PIN"},
        "matched_conventional_baseline":"INDEPENDENT_DECIMAL_EXACT_VALUE_REPLAY_PASS",
        "autonomous_source_semantics":"NOT_ESTABLISHED_HUMAN_DECLARED_THEORY_AND_ROW_ROLE",
        "new_physical_scientific_discovery":"UNKNOWN"
    }

def main():
    texts=input_source_text()
    result=calculate(texts)
    parent=ROOT.parent/"nist_hydrogen_crosssource"/"evidence"/"hydrogen_v2_result.json"
    if not parent.exists():
        raise SourceParseFailure("V2_PREDECESSOR_EVIDENCE_ABSENT")
    previous=json.loads(parent.read_text())
    if previous.get("status")!="WARRANTED_BOUNDED_SOURCE_BOUND_TWO_STUDY_CONTRAST":
        raise SourceParseFailure("V2_ANTECEDENT_UNQUALIFIED")
    record={
        "state":"WARRANTED_BOUNDED_SOURCE_NATIVE_NUMERICAL_CORRECTION_AND_CENTROID_REPLAY",
        "original_source_pins":{k:{"url":v["url"],"sha256":v["digest"]}
                                for k,v in ORIGINALS.items()},
        "predecessor_source_check":"WARRANTED_BOUNDED_RUN_38491803250",
        "native_source_semantics":"HUMAN_MAPPED_NOT_GENERATED",
        "consequences":result,
        "E2E_SYSTEM_AUTONOMOUS_METHOD_GENESIS":"UNKNOWN",
        "outside_owner_adoption":"NOT_TESTED"}
    (EVIDENCE/"v3_affine_receipt.json").write_text(json.dumps(record,indent=2)+"\n")
    print(json.dumps(record,indent=2))

if __name__=="__main__":
    main()
