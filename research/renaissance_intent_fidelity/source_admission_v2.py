#!/usr/bin/env python3
"""Admission verifier: source-identity + deterministic docstring-adjacent declaration census.
This is NOT a semantic-fidelity classifier or independent mathematical adjudicator.
"""
import hashlib, pathlib, re, subprocess, sys
EXPECTED_BLOB = "04fc6ed3e31ef9cd594f3db95e8edf87bf593bf3"
EXPECTED_NAMES = [
 "le_prod_nonempty_of_submultiplicative_on_pred",
 "le_prod_nonempty_of_submultiplicative",
 "le_prod_of_submultiplicative_on_pred",
 "le_prod_of_submultiplicative",
 "prod_le_prod",
 "_root_.Monotone.finsetProd'",
 "_root_.MonotoneOn.finsetProd'",
 "_root_.Antitone.finsetProd'",
]
def candidates(text):
    found=[]
    for match in re.finditer(r"/--[\\s\\S]*?-/", text):
        rest=text[match.end():]
        m=re.match(r"\\s*(?:@\\[[^\\n]*\\]\\s*)*(?:theorem|lemma)\\s+([^\\s(:]+)",rest)
        if m: found.append(m.group(1))
    return found
def audit(data):
    blob=subprocess.run(["git","hash-object","--stdin"],input=data,stdout=subprocess.PIPE,check=True).stdout.decode().strip()
    if blob != EXPECTED_BLOB: raise ValueError(f"SOURCE_BLOB_MISMATCH: {blob}")
    found=candidates(data.decode())
    if len(found)<8: raise ValueError(f"INSUFFICIENT_SOURCE: {len(found)}")
    if found[:8]!=EXPECTED_NAMES: raise ValueError(f"SELECTION_MISMATCH: {found[:8]}")
    return found
if __name__=="__main__":
    raw=pathlib.Path(sys.argv[1]).read_bytes()
    selected=audit(raw)
    # negative control: modified source must be refused
    try: audit(raw+b"\\n-- tamper\\n")
    except ValueError as e:
        assert str(e).startswith("SOURCE_BLOB_MISMATCH")
    else: raise AssertionError("tamper was accepted")
    print(f"ADMISSION_PASS: {len(selected)} documented theorem declarations; first eight fixed; tamper refused; blob {EXPECTED_BLOB}")
