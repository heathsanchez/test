#!/usr/bin/env python3
"""Independent finite, archived native JUnit -> Lean data certification.

Mistral (16 masks) and Deer-flow (4 masks) were already independently audited
at source/author-Git level. This tool independently REPARSES the native JUnit
files, verifies recorded hashes and consequences, tests every subset-pair
join relation, and writes a finite Lean theorem. It does not build or run new
repair code and does not certify source-to-external-truth soundness.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import subprocess
import sys
import xml.etree.ElementTree as ET

HERE=Path(__file__).resolve().parents[2]
PROTOCOL="research/unified_consequence_runtime/G2_TWO_SOURCE_FINITE_JOIN_FROZEN_PROTOCOL_V1.json"
FROZEN_COMMIT="eed380b0a50683f1f8a9c6c2160311f17b5d55f1"
SCHEMA="G2_TWO_REAL_SOURCE_NATIVE_FINITE_JOIN_V1"


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def frozen_protocol():
    current=(HERE/PROTOCOL).read_bytes()
    origin=subprocess.check_output(
        ["git","-C",str(HERE),"show",FROZEN_COMMIT+":"+PROTOCOL],
        timeout=35)
    if current!=origin:
        raise ValueError("UNKNOWN_FROZEN_PROTOCOL_DRIFT")
    o=json.loads(current)
    if o.get("schema")!="G2_TWO_REAL_SOURCE_FINITE_JOIN_CERT_V1_FROZEN":
        raise ValueError("UNKNOWN_EXPERIMENT_SCHEMA")
    if {x["name"] for x in o["cases"]}!={"MISTRAL","DEERFLOW"}:
        raise ValueError("UNKNOWN_SOURCE_PAIR")
    return o,sha(current)


def validate_masks(masks,edits,tests):
    """Exact finite join and basis necessity over bit-coded PASS sets.

    Inputs are independently reconstructed actual original native test-case
    outcomes, not similarity scores or hypothesized program semantics.
    """
    if not (type(edits) is int and 1<=edits<=6 and
            type(tests) is int and 1<=tests<=30 and
            isinstance(masks,(list,tuple)) and len(masks)==(1<<edits)):
        raise ValueError("UNKNOWN_FINITE_MASK_DIMENSION")
    full=(1<<tests)-1
    if any(type(x) is not int or x<0 or x>full for x in masks):
        raise ValueError("UNKNOWN_PASS_CASE_VECTOR")
    if masks[0]==full or masks[-1]!=full:
        raise ValueError("UNKNOWN_NATIVE_ORIGINAL_OR_COMPLETE_OUTCOME")
    pair_count=0
    for left in range(1<<edits):
        for right in range(1<<edits):
            if masks[left|right]!=(masks[left]|masks[right]):
                raise ValueError("REJECTED_FINITE_JOIN_RELATION")
            pair_count+=1
    for bit in range(edits):
        if masks[((1<<edits)-1)^(1<<bit)]==full:
            raise ValueError("REJECTED_UNNECESSARY_SOURCE_EDIT")
    return {"original_pass_mask":masks[0],"all_pass_mask":full,
            "necessary_edits":edits,"pairwise_join_pairs":pair_count,
            "source_subset_states":1<<edits}


def parse_cases(raw,style="full"):
    cases=list(ET.fromstring(raw).iter("testcase"))
    if not cases:raise ValueError("UNKNOWN_EMPTY_NATIVE_JUNIT")
    result={}
    for node in cases:
        name=node.get("name")
        if not isinstance(name,str) or not name:
            raise ValueError("UNKNOWN_JUNIT_CASE_ID")
        if style=="mistral_protected":
            identifier=name
        else:
            classname=node.get("classname")
            if not isinstance(classname,str) or not classname:
                raise ValueError("UNKNOWN_JUNIT_CASE_CLASS")
            identifier=classname+"::"+name
        if identifier in result:
            raise ValueError("UNKNOWN_DUPLICATE_JUNIT_CASE")
        children=[x.tag for x in list(node)]
        if "error" in children or "skipped" in children or "xfail" in children:
            raise ValueError("UNKNOWN_NONEXECUTED_NATIVE_OBLIGATION")
        result[identifier]="FAIL" if "failure" in children else "PASS"
    return dict(sorted(result.items()))


def source_directory(root,suffix):
    root=Path(root).resolve(strict=True)
    found=[p.parent for p in root.rglob("RESULT.json") if p.parent.name==suffix]
    if len(found)!=1:
        raise ValueError("UNKNOWN_AMBIGUOUS_ARCHIVED_SOURCE_SCOPE")
    return found[0]


def receipt_vector(folder,file,receipt,expected_case_universe,style,*,is_mistral):
    raw=(folder/file).read_bytes()
    if sha(raw)!=receipt["junit_sha256"]:
        raise ValueError("UNKNOWN_NATIVE_JUNIT_SHA_MISMATCH:"+file)
    vector=parse_cases(raw,style)
    if set(vector)!=set(expected_case_universe):
        raise ValueError("UNKNOWN_NATIVE_CASE_UNIVERSE_CHANGED:"+file)
    fails=sum(v=="FAIL" for v in vector.values())
    counts=receipt["counts"]  # Both original native receipt formats nest actual counts.
    if is_mistral:
        exit_code=receipt["exit"]
    else:
        exit_code=receipt["returncode"]
    if counts.get("tests")!=len(vector) or counts.get("failures")!=fails or (
        counts.get("errors")!=0 or counts.get("skipped")!=0
    ) or exit_code!=(1 if fails else 0):
        raise ValueError("UNKNOWN_NATIVE_RECEIPT_JUNIT_DISAGREEMENT:"+file)
    return vector


def read_native_source(entry,download_root):
    folder=source_directory(download_root,entry["folder_suffix"])
    result=json.loads((folder/"RESULT.json").read_text())
    audit=json.loads((folder/"INDEPENDENT_AUDIT.json").read_text())
    if audit.get("status")!=entry["auditor_warrant"] or audit.get("G2")!="UNKNOWN":
        raise ValueError("UNKNOWN_INDEPENDENT_SOURCE_QUALIFICATION:"+entry["name"])
    if result.get("G2")!="UNKNOWN":
        raise ValueError("UNAUTHORIZED_G2_PROMOTION")
    edits=entry["selected_edit_count"];expected=(1<<edits)
    rows=result.get(entry["native_cases_from"])
    if not isinstance(rows,dict) or set(rows)!={str(i) for i in range(expected)}:
        raise ValueError("UNKNOWN_INCOMPLETE_NATIVE_SUBSET_UNIVERSE")
    original=rows["0"]
    initial=original["verdicts"] if entry["name"]=="MISTRAL" else original["native"]["vector"]
    if len(initial)!=entry["native_case_count"] or not all(
         v in ("FAIL","PASS") for v in initial.values()):
        raise ValueError("UNKNOWN_PROTECTED_TEST_UNIVERSE")
    test_names=sorted(initial)
    style="mistral_protected" if entry["name"]=="MISTRAL" else "deer_protected"
    pass_masks=[]
    source_fingerprints=[]
    for mask in range(expected):
        row=rows[str(mask)]
        if row.get("mask")!=mask:
            raise ValueError("UNKNOWN_SOURCE_EDIT_MASK_ID")
        native=row["receipt"] if entry["name"]=="MISTRAL" else row["native"]
        label=entry["subset_file_pattern"].format(mask=mask)
        vector=receipt_vector(folder,label,native,test_names,style,
                              is_mistral=entry["name"]=="MISTRAL")
        if vector!=(row["verdicts"] if entry["name"]=="MISTRAL" else native["vector"]):
            raise ValueError("UNKNOWN_RESULT_VECTOR_VS_ORIGINAL_JUNIT")
        if entry["name"]=="MISTRAL":
            identity=row["source_sha256"]
        else:
            identity=json.dumps(row["source_sha256"],sort_keys=True)
        source_fingerprints.append(identity)
        pass_masks.append(sum((1<<bit) for bit,test in enumerate(test_names)
                              if vector[test]=="PASS"))
    if len(set(source_fingerprints))!=expected:
        raise ValueError("UNKNOWN_REUSED_EDIT_SOURCE_IDENTITY")
    lawful=validate_masks(pass_masks,edits,len(test_names))

    if entry["name"]=="MISTRAL":
        full_receipt=result["full_author_suite"]
        withdrawal_receipt=result["withdrawal"]
        restoration_receipt=result["restoration"]
        full_counts=full_receipt["counts"]
    else:
        full_receipt=result["full_author"]
        withdrawal_receipt=result["withdrawal"]
        restoration_receipt=result["restoration"]
        full_counts=full_receipt
    full_file=entry["full_file"]
    full_raw=(folder/full_file).read_bytes()
    if sha(full_raw)!=full_receipt["junit_sha256"]:
        raise ValueError("UNKNOWN_FULL_AUTHOR_JUNIT_SHA")
    full_cases=parse_cases(full_raw,"full")
    if (len(full_cases)!=entry["full_author_pass_count"] or
        any(v!="PASS" for v in full_cases.values()) or
        full_counts.get("tests")!=len(full_cases) or
        full_counts.get("failures")!=0 or
        full_counts.get("errors")!=0 or full_counts.get("skipped")!=0):
        raise ValueError("REJECTED_FULL_AUTHOR_NATIVE_SUITE")
    withdrawal=receipt_vector(folder,entry["withdrawal_file"],
          withdrawal_receipt,test_names,style,
          is_mistral=entry["name"]=="MISTRAL")
    restoration=receipt_vector(folder,entry["restoration_file"],
          restoration_receipt,test_names,style,
          is_mistral=entry["name"]=="MISTRAL")
    if withdrawal!=initial or any(v!="PASS" for v in restoration.values()):
        raise ValueError("REJECTED_NATIVE_PHYSICAL_WITHDRAWAL_OR_RESTORATION")
    return {"name":entry["name"],"edits":edits,"cases":len(test_names),
            "case_name_sha256":sha(json.dumps(test_names,sort_keys=True).encode()),
            "pass_masks":pass_masks,"mask_junit_sha256":[
                 (rows[str(i)]["receipt"] if entry["name"]=="MISTRAL"
                  else rows[str(i)]["native"])["junit_sha256"]
                 for i in range(expected)],
            "qualified_source_archive_sha256_inherited":entry["archive_sha256"],
            "qualified_audit_status":audit["status"],
            "full_author_passed":len(full_cases),
            "original_withdrawal_reproduced":True,
            "exact_restoration_passed":True,**lawful}


def render_lean(rows):
    """Finite theorem checker; bind table truth to separately checked JUnit packet."""
    lines=[
        "-- Autogenerated only after independent source-native JUnit SHA and case-universe audit.",
        "-- Proof covers supplied finite tables, NOT arbitrary external source correctness.",
        "import Init",
        "",
        "namespace SourceNativeFiniteJoin",
        ""
    ]
    for name in ("MISTRAL","DEERFLOW"):
        row=rows[name]
        x=row["pass_masks"]
        N=len(x);n=row["edits"];all_pass=(1<<row["cases"])-1
        lines.append("def "+name+"Pass (mask : Nat) : Nat :=")
        lines.append("  match mask with")
        for i,v in enumerate(x):
            lines.append("  | "+str(i)+" => "+str(v))
        lines.append("  | _ => 0")
        lines.append("")
        lines.append("theorem "+name+"JoinAllOrderedPairs :")
        lines.append("    ∀ a : Fin "+str(N)+", ∀ b : Fin "+str(N)+",")
        lines.append("      "+name+"Pass (Nat.lor a.val b.val) =")
        lines.append("        Nat.lor ("+name+"Pass a.val) ("+name+"Pass b.val) := by")
        lines.append("  decide")
        lines.append("")
        lines.append("theorem "+name+"EveryEditNecessary :")
        lines.append("    ∀ i : Fin "+str(n)+",")
        lines.append("      "+name+"Pass ("+str(N-1)+" - 2^i.val) ≠ "+str(all_pass)+" := by")
        lines.append("  decide")
        lines.append("")
        lines.append("theorem "+name+"FullyRepaired :")
        lines.append("    "+name+"Pass "+str(N-1)+" = "+str(all_pass)+" := by")
        lines.append("  decide")
        lines.append("")
    lines.append("end SourceNativeFiniteJoin")
    return "\n".join(lines)+"\n"


def certify(mistral, deer, output):
    output=Path(output).absolute()
    output.mkdir(parents=True,exist_ok=False)
    proto,protocol_sha=frozen_protocol()
    data={}
    for entry in proto["cases"]:
        root=mistral if entry["name"]=="MISTRAL" else deer
        data[entry["name"]]=read_native_source(entry,root)
    result={
       "schema":SCHEMA,"status":"CANDIDATE_INDEPENDENT_NATIVE_TABLE_READY_FOR_LEAN",
       "protocol_commit":FROZEN_COMMIT,"protocol_sha256":protocol_sha,
       "G2":"UNKNOWN","G3":"UNKNOWN","G4":"UNKNOWN","G5":"UNKNOWN","G6":"UNKNOWN",
       "native_original_sources":"PREVIOUSLY_INDEPENDENTLY_AUDITED",
       "Lean":"NOT_YET_EXECUTED","CLC":"NOT_EXECUTED","FLASH":"NOT_EXECUTED",
       "informed_ledger":"DEERFLOW_SAME_MINIMAL_MASK_TIE_NO_EXCLUSIVE_ADVANTAGE",
       "pairwise_relations":sum(x["pairwise_join_pairs"] for x in data.values()),
       "source_count":len(data),"sources":data,
       "claim_limit":"TWO_EXPOSED_PROJECTS; FINITE_AUTHENTIC_NATIVE_RECEIPTS; NOT_NEW_G2"
    }
    lean=render_lean(data)
    (output/"FiniteNativeJoin.lean").write_text(lean)
    result["lean_source_sha256"]=sha(lean.encode())
    (output/"RESULT.json").write_text(json.dumps(result,indent=2,sort_keys=True)+"\n")
    return result


if __name__=="__main__":
    if len(sys.argv)!=4:
        raise SystemExit("usage: g2_two_source_finite_join_v1.py MISTRAL_UNPACKED DEER_UNPACKED FRESH_OUTPUT")
    o=certify(sys.argv[1],sys.argv[2],sys.argv[3])
    print(json.dumps({k:o[k] for k in ("status","source_count","pairwise_relations","G2","Lean")},sort_keys=True))
