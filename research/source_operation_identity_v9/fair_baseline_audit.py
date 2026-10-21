#!/usr/bin/env python3
"""Post-exposure fair baseline audit. NOT original prospective scoring."""
import hashlib,importlib.util,json,pathlib,re,urllib.request
ROOT=pathlib.Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location("frozen_v9",ROOT/"test.py")
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
SOURCE_SHA="24cc5fea221e2e81f4773464fab420a01dc5f3d5b068f2ac16fb91d3109361e6"
req=urllib.request.Request(m.URL,headers={"User-Agent":"Metalogic-V9-SourceIdentity/1"})
with urllib.request.urlopen(req,timeout=30) as r: raw=r.read(3_000_001)
assert hashlib.sha256(raw).hexdigest()==SOURCE_SHA,"SOURCE_CHANGED_NO_REPRODUCIBLE_POSTHOC_TEST"
parser=m.DefinitionBlocks();parser.feed(raw.decode("utf-8"))
candidate=m.exact_identity(parser.entries)
matches=[]
for e in parser.entries:
    normalized=re.sub(r"\s+","",e["owner_signature"])
    if "insort_left(" in normalized:
        matches.append(e)
assert candidate["status"]=="SOURCE_OWNER_MATCH" and len(matches)==1
assert candidate["definition"]["owner_signature"]==matches[0]["owner_signature"]
receipt={"status":"POSTEXPOSURE_FAIR_BASELINE_TIE","source_sha256":SOURCE_SHA,
         "candidate_owner":candidate["definition"]["owner_signature"],
         "repaired_baseline_owner":matches[0]["owner_signature"],
         "original_frozen_baseline":"UNKNOWN_FORMATTING_BUG",
         "semantic_entailment":"UNKNOWN_NOT_CHECKED","automatic_native_witness":"NOT_CONSTRUCTED"}
(ROOT/"baseline_audit_result.json").write_text(json.dumps(receipt,indent=2)+"\n")
print(json.dumps(receipt,sort_keys=True))
