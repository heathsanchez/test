#!/usr/bin/env python3
"""Frozen semantic-family challenge; imports original extraction method unchanged."""
import datetime, hashlib, importlib.util, json, re, urllib.request
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
ORIGINAL=ROOT/"independent_obligation_acquisition_v1"/"experiment.py"
URL="https://www.sqlite.org/foreignkeys.html"
def main():
    spec=importlib.util.spec_from_file_location("frozen_original_compiler",ORIGINAL)
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    request=urllib.request.Request(URL,headers={"User-Agent":"Metalogic-Research-Evidence-Audit/1.0"})
    with urllib.request.urlopen(request,timeout=30) as resp:
        raw=resp.read(2_000_001)
        actual=resp.geturl()
    if len(raw)>2_000_000 or actual!=URL:raise RuntimeError("SOURCE_INTEGRITY_FAILURE")
    text=raw.decode("utf-8")
    extracted=module.extract(text) # exact previous algorithm, no semantics injected
    # Independently confirm topical presence, but this is NOT an automatic semantic interpretation.
    # Known topic labels were preregistered to test false positives and source suitability.
    source_text=re.sub(r"<[^>]+>"," ",text)
    source_text=re.sub(r"\s+"," ",source_text)
    i=source_text.lower().find("on delete cascade")
    suitability = i>=0
    excerpt=source_text[max(0,i-110):i+260] if i>=0 else ""
    if not suitability:
        verdict="UNKNOWN_SOURCE_DOES_NOT_EXPOSE_LOCKED_TOPIC"
    elif extracted.get("status")!="CLAUSE_EXTRACTED":
        verdict="REJECTED_UNANTICIPATED_FAMILY_TRANSFER"
    elif extracted.get("kind")=="CHECK_ZERO_VIOLATION":
        verdict="FALSE_TOPIC_CHECK_CLAUSE_NOT_CASCADE"
    else:
        verdict="CANDIDATE_REQUIRES_NATIVE_QUALIFICATION"
    report={
      "verification_scope":"unaltered lexical extractor; no new source-specific semantic compiler",
      "frozen_compiler_import":str(ORIGINAL.relative_to(ROOT)),
      "source_url":URL,
      "retrieved_utc":datetime.datetime.now(datetime.timezone.utc).isoformat(),
      "source_sha256":hashlib.sha256(raw).hexdigest(),
      "source_size":len(raw),
      "topic_cascade_exists":suitability,
      "source_excerpt":excerpt,
      "extractor_output":extracted,
      "verdict":verdict,
      "native_cascade_test":"NOT_ATTEMPTED_UNLESS_CORRECT_OBLIGATION_ACQUIRED",
      "comparison":"UNMEASURED_FULL_INFORMATION_EXPERT",
      "g2_general_observer_invention":"UNKNOWN"
    }
    Path(__file__).with_name("result.json").write_text(json.dumps(report,indent=2)+"\n")
    print(json.dumps({k:report[k] for k in ("source_sha256","topic_cascade_exists","extractor_output","verdict","native_cascade_test")},sort_keys=True))
if __name__=="__main__":main()
