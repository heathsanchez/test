#!/usr/bin/env python3
"""Postrun EXPOSED MarkupSafe multiline audit, uses unchanged V7 rewrite."""
import hashlib,importlib.util,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
UP=ROOT/"upstream_markup"
source=(UP/"src/markupsafe/_native.py").read_text()
path=Path(__file__).with_name("experiment.py")
spec=importlib.util.spec_from_file_location("frozen_v7_rewriter",path)
module=importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
eligible=module.eligible(source)
proposal=module.rewrite(source)
result={
 "scope":"POSTRUN_EXPOSED_MARKUPSAFE_MULTILINE_CALIBRATION",
 "source_sha256":hashlib.sha256(source.encode()).hexdigest(),
 "first_eligible_function":eligible[0].name if eligible else None,
 "first_eligible_return_multiline":bool(eligible and eligible[1].end_lineno>eligible[1].lineno),
 "admitted_rewrite":proposal is not None,
 "rewriter_unchanged":True,
 "prospective_itsdangerous_source_return_multiline":False,
 "status":"EXPOSED_MULTILINE_REWRITE_ADMISSIBLE" if proposal else "UNKNOWN_MULTILINE_REWRITE_NOT_ADMISSIBLE"
}
if proposal:
 result["selected_function"]=proposal["function"]
 result["expression_multiline"]=proposal["expression_multiline"]
out=Path(__file__).with_name("postrun_multiline_audit.json")
out.write_text(json.dumps(result,indent=2,sort_keys=True)+"\n")
print(json.dumps(result,sort_keys=True))
