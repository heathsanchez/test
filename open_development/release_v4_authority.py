"""Final release authority binding scientific v4 to current-head regression."""
from __future__ import annotations
import argparse,json,re
from pathlib import Path
from .release_v4 import validate as validate_science
from .runtime import digest

SCHEMA="open-development-release/v4-authority"
SCIENCE_COMMIT="7505fbf047b9684fbde417705528ef0d6b37895d"
SCIENCE_RUN=34449939382
SCIENCE_ARTIFACT=10141138082
SCIENCE_ARTIFACT_SHA256="411e289fe70830682f75a3497981c5815491785cc712b89d20cff02276647b59"

def need(x,msg):
    if not x: raise ValueError(msg)

def build(repository,source_commit,run_id,science,freeze,stream,decisions,evaluation,regression):
    validate_science(science,freeze,stream,decisions,evaluation)
    need(science["source_commit"]==SCIENCE_COMMIT and science["run_id"]==SCIENCE_RUN,"wrong scientific authority")
    need(regression.get("source_commit")==source_commit and regression.get("run_id",0)>0,"wrong current-head regression")
    need(re.fullmatch(r"[0-9a-f]{40}",regression.get("checkout_merge_commit","")),"missing regression checkout identity")
    need(regression.get("core_result")=="RELEASE_EVIDENCE_PASS" and re.fullmatch(r"[0-9a-f]{64}",regression.get("core_evidence_digest","")),"core regression failed")
    need(regression.get("semantics_result")=="TYPED_PROGRAM_SEMANTICS_LEAN_PASS" and regression.get("axioms_pass_count")==11,"Lean semantics regression failed")
    need(all(re.fullmatch(r"sha256:[0-9a-f]{64}",x) for x in regression.get("artifact_digests",[])),"regression artifact identity failed")
    body={"schema":SCHEMA,"claim":science["claim"],"repository":repository,"source_commit":source_commit,"run_id":run_id,
          "canonical_parent":science["canonical_parent"],"canonical_v3":science["v3"],
          "scientific_authority":{"source_commit":SCIENCE_COMMIT,"run_id":SCIENCE_RUN,"artifact_id":SCIENCE_ARTIFACT,
                                  "artifact_sha256":SCIENCE_ARTIFACT_SHA256,"manifest":science,"manifest_digest":digest(science)},
          "current_head_regression":regression,"regression_digest":digest(regression),"limitations":science["limitations"]}
    return {**body,"evidence_digest":digest(body)}

def validate(manifest,science,freeze,stream,decisions,evaluation,regression):
    need(manifest.get("schema")==SCHEMA,"wrong v4 authority schema")
    need(manifest.get("evidence_digest")==digest({k:v for k,v in manifest.items() if k!="evidence_digest"}),"stale v4 authority")
    need(manifest==build(manifest["repository"],manifest["source_commit"],manifest["run_id"],science,freeze,stream,decisions,evaluation,regression),"v4 authority mismatch")

def main():
    p=argparse.ArgumentParser();p.add_argument("--repository",required=True);p.add_argument("--source-commit",required=True);p.add_argument("--run-id",type=int,required=True)
    for x in ("science","freeze","stream","decisions","evaluation","regression","output"):p.add_argument("--"+x,type=Path,required=True)
    a=p.parse_args();load=lambda x:json.loads(x.read_text())
    vals=[load(getattr(a,x)) for x in ("science","freeze","stream","decisions","evaluation","regression")]
    m=build(a.repository,a.source_commit,a.run_id,*vals);validate(m,*vals);a.output.write_text(json.dumps(m,indent=2,sort_keys=True)+"\n")
    print("OPEN_DEVELOPMENT_RELEASE_V4_AUTHORITY_PASS",m["evidence_digest"])
if __name__=="__main__":main()
