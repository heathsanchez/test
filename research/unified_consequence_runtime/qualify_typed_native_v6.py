"""Exposed-source V6 diagnostic on pinned original wcwidth history, NEVER G2.

Only a source-distinct, newly frozen future can qualify autonomous learning.
This script exercises a scoped original author-authored pytest file twice with
typed Git transport, opaque gitlinks and independent source rechecks.
"""
from __future__ import annotations
import json
import os
from pathlib import Path
import sys

from . import typed_native_authority_v6 as typed

SOURCE = "784d08c6cf6b67e19f34ae5ddb9bb8b4aa4f17fe"
REQUIRED = ("tests/test_width.py::test_width_basic",)
SCOPE = ("tests/test_width.py",)


def main():
    source = Path(os.environ["UDM_V6_ORIGINAL_SOURCE"]).absolute()
    stage = Path(os.environ["UDM_V6_NATIVE_STAGE"]).absolute()
    prepared = typed.stage(source, SOURCE, stage)
    first = typed.run_protected(source, SOURCE, stage, required=REQUIRED,
                                paths=SCOPE,interpreter=sys.executable,timeout=180)
    second = typed.run_protected(source, SOURCE, stage, required=REQUIRED,
                                 paths=SCOPE,interpreter=sys.executable,timeout=180)
    after = typed.verify_stage(source, SOURCE, stage)
    result={"schema":"UDM_V6_EXPOSED_WCWIDTH_NATIVE_DIAGNOSTIC",
            "type":"EXPOSED_SOURCE_DIAGNOSTIC_ONLY","repository":"jquast/wcwidth",
            "source_commit":SOURCE,"stage":prepared,"after":after,
            "first":first,"second":second,
            "G2":"UNKNOWN","G3":"UNKNOWN","G4":"UNKNOWN","G5":"UNKNOWN","G6":"UNKNOWN",
            "not_an_original_full_suite_claim":True,
            "not_a_scientific_new_frontier":True}
    print(json.dumps(result,sort_keys=True))


if __name__=="__main__":
    main()
