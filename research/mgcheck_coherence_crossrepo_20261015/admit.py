#!/usr/bin/env python3
"""Conservative source-native matched receipt, not general safe-merge authority."""
from __future__ import annotations
import hashlib, json, os, pathlib, sys, time, zipfile

A_ZIP_SHA="2ab47701fa213e417b528ccd2e46a9233143c9b5191bd2c5aea112a24412d057"
EXPECTED={
 "b":{"base":"1cc59b351e1ff5c7591ab05d4d027638100af82b","head":"5be7c5041f28df68365ec4f3d77b3363ede198be"},
 "c":{"base":"d883c7cf2ae48eae5ba572c1d45bc46fbf8e5cb5","head":"b28b705bd364aa7d7fbc9f6102bca3ceda223dbf"}
}
def dig(p):return hashlib.sha256(pathlib.Path(p).read_bytes()).hexdigest()
def load(path):return json.loads(pathlib.Path(path).read_text())
def comparable(r):
 return {(x["program_index"],x["mode"]):x for x in r["results"]}
def native_projection(r):
 return {(x["program_index"],x["mode"]):
  (x.get("native_status"),x.get("coherence"),x.get("reference_canonical"),
   x.get("own_reparse_equal"),x.get("reference_error"),x.get("native_error"))
   for x in r["results"]}
def main():
 E=pathlib.Path(sys.argv[1]); root=E.parent
 source_cap_path=root/"acquired_capability_A_from_original_archive.json"
 assert dig(source_cap_path)=="2407927cfc0a7b5061aefecce70ae69ddd19a70820883d08439da5fb2aa363d1","UNKNOWN_SOURCE_A_MANIFEST_IDENTITY"
 prev=load(source_cap_path)
 assert prev["selected_channels"]==["coherence"] and prev["source_old_fail_to_head_pass"]==13,"UNKNOWN_A_CAPABILITY"
 source_cap_sha=dig(source_cap_path)
 cap={
   "source":"heathsanchez/test Actions 38639050079 artifact 11929272911",
   "source_archive_sha256":A_ZIP_SHA,
   "source_capability_sha256":source_cap_sha,
   "observation":"coherence",
   "source_learned_qualifier":"WARRANTED_BOUNDED_A",
   "new_transfer_adapter":"human-authored common loads/dumps",
   "source_nonnormative_warning":"author-fix topics known; no prospective bug novelty"
 }
 (E/"acquired_capability.json").write_text(json.dumps(cap,sort_keys=True,indent=2)+"\n")
 family_result={}
 for f in ("b","c"):
  obs={rev:load(E/f"{f}_{rev}.json") for rev in ("base","head","ablated")}
  original=obs["base"];head=obs["head"];ablated=obs["ablated"]
  assert original["source_sha"]==EXPECTED[f]["base"]
  assert head["source_sha"]==EXPECTED[f]["head"]
  assert ablated["source_sha"]==EXPECTED[f]["head"],"ABLATED_HEAD_IDENTIFICATION_BAD"
  assert original["corpus_size"]==head["corpus_size"]==ablated["corpus_size"]==16
  a=comparable(original);b=comparable(head);c=comparable(ablated)
  assert a.keys()==b.keys()==c.keys(),"UNKNOWN_COMPARATOR_MODE_DRIFT"
  repairs=[k for k in a if a[k]["coherence"]=="VIOLATION" and b[k]["coherence"]=="MATCH"]
  preserved=[k for k in a if a[k]["coherence"]=="MATCH" and b[k]["coherence"]=="MATCH"]
  same_problem=[k for k in repairs if c[k]["coherence"]=="VIOLATION" and c[k].get("reference_canonical")==a[k].get("reference_canonical")]
  unexpected=[k for k in a if a[k]["coherence"]=="MATCH" and b[k]["coherence"]=="VIOLATION"]
  # Restricted observer knows that public call returned or failed, but does NOT
  # have the independently derived semantic output. Count any exceptions as known.
  old_unknown=sum(x["coherence"].startswith("UNKNOWN") for x in a.values())
  modes=original["supported_modes"]
  family_result[f]={
   "repo":{"b":"uiri/toml","c":"avakar/pytoml"}[f],
   "original_base_sha":EXPECTED[f]["base"],"original_contributor_head_sha":EXPECTED[f]["head"],
   "module":original["discovered_module"],
   "modes":modes,"sample_count":len(a),
   "old_violations":sum(x["coherence"]=="VIOLATION" for x in a.values()),
   "head_violations":sum(x["coherence"]=="VIOLATION" for x in b.values()),
   "old_unknown":old_unknown,
   "head_unknown":sum(x["coherence"].startswith("UNKNOWN") for x in b.values()),
   "fixed_native_witness_count":len(repairs),
   "first_witness":repr(repairs[0]) if repairs else None,
   "preserved_old_success_count":len(preserved),
   "new_regression_count":len(unexpected),
   "ablated_original_failure_restored_count":len(same_problem),
   "ablated_all_repaired":len(same_problem)==len(repairs),
   "restricted_no_semantic_channel_observer":"UNKNOWN_NO_SEMANTIC_ORACLE",
   "fully_informed_ledger_semantic_equivalence":"PENDING_LEDGER_REPLAY",
   "native_calls_by_arm":{rev:obs[rev]["calls"] for rev in obs},
   "native_elapsed_ns_by_arm":{rev:obs[rev]["elapsed_ns"] for rev in obs},
   "source_ablation_metadata":load(E/f"{f}_ablation_source.json"),
   "raw_native_json_sha256":{rev:dig(E/f"{f}_{rev}.json") for rev in obs}
  }
  if repairs and len(same_problem)!=len(repairs):
   raise AssertionError(f"PHYSICAL_ABLATION_DID_NOT_RESTORE_OLD_WITNESS {f}")
  if unexpected:
   print("PROTECTED_NATIVE_REGRESSION_IN_HEAD",f,unexpected)
 evidence={"source_qualification":"WARRANTED_BOUNDED_A",
  "two_source_distinct_futures":"WARRANTED_BOUNDED" if all(family_result[f]["fixed_native_witness_count"] for f in ("b","c")) else "UNKNOWN_NOT_BOTH_FUTURES",
  "meta_language_genesis":"NOT_TESTED","strong_live_coding_agent":"NOT_RUN",
  "economic_dominance":"UNKNOWN_NO_FULL_ACQUISITION_COST",
  "families":family_result}
 (E/"native_report.json").write_text(json.dumps(evidence,sort_keys=True,indent=2)+"\n")
 print(json.dumps({"claim":evidence["two_source_distinct_futures"],
  "B":{k:v for k,v in family_result["b"].items() if k in ("old_violations","fixed_native_witness_count","new_regression_count","ablated_original_failure_restored_count")},
  "C":{k:v for k,v in family_result["c"].items() if k in ("old_violations","fixed_native_witness_count","new_regression_count","ablated_original_failure_restored_count")}},sort_keys=True))
 if evidence["two_source_distinct_futures"]!="WARRANTED_BOUNDED":
  (E/"FROZEN_SCIENTIFIC_RED.txt").write_text("NATIVE_TWOSOURCE_ADMISSION_RED: B qualified, C unavailable; do not promote 2/2.\n")
  print("NATIVE_TWOSOURCE_ADMISSION_RED_RETAINED")
if __name__=="__main__":main()
