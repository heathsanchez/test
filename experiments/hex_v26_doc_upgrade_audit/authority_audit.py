#!/usr/bin/env python3
import hashlib, json, pathlib, re, sys

ROOT=pathlib.Path(__file__).resolve().parents[2]
EXPECTED={
 "v20":("experiments/hex_v20_incidence_theorem","a0c56f2e60e488250c45acd7234d62661930ef33d224037175f00c6f8e88a4cc","VERIFIED_GENERAL_INCIDENCE_ISOMORPHISM_THEOREM","sourceIso_iff_incIso"),
 "v21":("experiments/hex_v21_signature_theorem","5b6273fd4d49c1863cf9c25ed379cc4af878b1dfa6d930f288a2ea94ece54191","VERIFIED_ARBITRARY_RELATIONAL_SIGNATURE_INCIDENCE_THEOREM","sourceIso_iff_incIso"),
 "v22":("experiments/hex_v22_finite_compiler","a1add522f8a2bd291c6c9067cd4d714ac92c12c702a7ea4bb2fbbd69aefa6ad8","VERIFIED_FINITE_COLORED_COMPILER_TO_HEX","finiteColoredIso_iff_hexIsomorphic"),
 "v23":("experiments/hex_v23_composed_transport","7d170aeafeb4c034ef7b6a9201dc28f267e51b56c91a6fa9736daf5a96516160","VERIFIED_RELATIONAL_ISOMORPHISM_TO_HEX_COMPOSITION","IncidencePairPresentation.sourceIso_iff_hexIsomorphic"),
 "v24":("experiments/hex_v24_numbering_constructor","c6cddb808379b3b13db8f953ed847660a64c7c1ae814879f5525859a033f128b","VERIFIED_INCIDENCE_NUMBERING_CONSTRUCTOR_TO_HEX","IncidenceNumberingPair.sourceIso_iff_hexIsomorphic"),
 "v25":("experiments/hex_v25_relational_decision","37b0cab3ad2f834d44c8046101fa5be98f8d11755732636965fd70010e57abb1","VERIFIED_RELATIONAL_ISOMORPHISM_DECISION_VIA_HEX",None),
}
FORBIDDEN=[
 ("sorry",re.compile(r"\bsorry\b")),
 ("admit",re.compile(r"\badmit\b")),
 ("axiom",re.compile(r"(?m)^\s*axiom\b")),
]
results={}
for name,(rel,sha,verdict,theorem) in EXPECTED.items():
    d=ROOT/rel
    src=d/"Main.lean"
    auth=d/"AUTHORITY.json"
    if not src.exists() or not auth.exists():
        raise SystemExit(f"missing authority files for {name}")
    actual=hashlib.sha256(src.read_bytes()).hexdigest()
    text=src.read_text()
    bad={label: bool(rx.search(text)) for label,rx in FORBIDDEN}
    a=json.loads(auth.read_text())
    ok_sha=actual==sha
    ok_verdict=a.get("verdict")==verdict
    auth_theorem=a.get("theorem")
    ok_theorem=True if theorem is None else auth_theorem==theorem
    no_holes=not any(bad.values())
    results[name]={
      "sha256":actual,"sha_ok":ok_sha,
      "verdict":a.get("verdict"),"verdict_ok":ok_verdict,
      "theorem":auth_theorem,"theorem_ok":ok_theorem,
      "forbidden_tokens":bad,"proof_hygiene_ok":no_holes,
    }
    if not all([ok_sha,ok_verdict,ok_theorem,no_holes]):
        print(json.dumps(results,indent=2,sort_keys=True))
        raise SystemExit(f"authority audit failed at {name}")

out={
 "verdict":"PASS_V20_V25_AUTHORITY_AND_PROOF_HYGIENE",
 "chain":results,
 "gates":{
   "all_exact_hashes":all(v["sha_ok"] for v in results.values()),
   "all_authority_verdicts":all(v["verdict_ok"] for v in results.values()),
   "all_theorem_names":all(v["theorem_ok"] for v in results.values()),
   "no_sorry_admit_axiom":all(v["proof_hygiene_ok"] for v in results.values()),
 }
}
p=pathlib.Path(__file__).resolve().parent/"results"
p.mkdir(exist_ok=True)
(p/"authority_audit.json").write_text(json.dumps(out,indent=2,sort_keys=True)+"\n")
print(json.dumps(out,indent=2,sort_keys=True))
