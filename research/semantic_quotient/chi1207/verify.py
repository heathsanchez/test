#!/usr/bin/env python3
"""Independently compare source-pinned Go logs; no source or expected witness encoded."""
from pathlib import Path
import json
import re
import sys

if len(sys.argv) != 5:
    raise SystemExit("REQUIRE_OLD_NEW_ABLATED_MODEL_LOGS")
old_path, new_path, ablated_path, model_path = map(Path,sys.argv[1:])
model_log=model_path.read_text()
m=re.search(r"MATHGRAPH_QUOTIENT_MODEL (\{[^\n]+\})",model_log)
assert m, "MODEL_REPORT_ABSENT"
model=json.loads(m.group(1))
assert model["equivalence_classes"] == 9
assert model["separated_pairs"] == model["distinct_pairs"]
assert model["histories"] == 121

def parse(path):
    text=path.read_text()
    assert "--- FAIL" not in text and "\nFAIL" not in text, "NATIVE_TEST_FAILED_"+path.stem
    key=re.search(r"MATHGRAPH_NATIVE_KEY_QUOTIENT cases=(\d+) alphabet=(\d+) maxKeys=(\d+) mismatch=(\d+)",text)
    state=re.search(r'MATHGRAPH_NATIVE_RECOVERY cases=(\d+) dirty=(\d+) clean=(\d+) minDirtyKeys=(\d+) minDirtyPattern="([^"]*)"',text)
    live=re.search(r"MATHGRAPH_NATIVE_LIVENESS tested=(\d+) firstNotReturnedWithin150ms=(\d+)",text)
    assert key and state and live, "MISSING_NATIVE_RECIEPT_"+path.stem
    assert [int(x) for x in key.groups()]==[121,3,4,0]
    count,dirty,clean,minimum=[int(x) for x in state.groups()[:4]]
    assert count>0 and dirty+clean==count
    return {"file":path.name,"nativeKeyCases":int(key.group(1)),
            "recoveredInvalidCases":count,"dirty":dirty,"clean":clean,
            "minimalDirtyKeyCount":minimum,"minimalDirtyPattern":state.group(5),
            "livenessCases":int(live.group(1)),
            "firstNotReturnedWithin150ms":int(live.group(2))}
old,new,ablated=map(parse,(old_path,new_path,ablated_path))
assert old["recoveredInvalidCases"]==new["recoveredInvalidCases"]==ablated["recoveredInvalidCases"]
assert old["dirty"]>0, "NO_OLD_STATE_MUTATION_DISCOVERED"
assert new["dirty"]==0, "CURRENT_PR_STILL_MUTATES_FRESH_TREE"
assert ablated["dirty"]==old["dirty"],"REMOVAL_DOES_NOT_RESTORE_PRIOR_FAILURE"
assert old["minimalDirtyPattern"]==ablated["minimalDirtyPattern"],"ABLATED_WITNESS_CHANGED"
assert old["minimalDirtyKeyCount"]==2, "MINIMAL_TWO_NAME_BOUNDARY_MISSING"
assert new["minimalDirtyKeyCount"]==0
report={"schema":"metalogic.jpl-quotient-router.v1",
 "status":"WARRANTED_BOUNDED_SOURCE_NATIVE",
 "source":{"repository":"go-chi/chi","pr":1207,
 "base":"167e1e3bd039d060696b99c8da4e876ae04f42c1",
 "head":"5a84f0500b8f8f307d615969c1ba4f7cd9126978"},
 "model":model,"old":old,"prHead":new,"oneChangeRemoval":ablated,
 "claim":"A minimal duplicate-key state quotient predicts native admission; two duplicate keys expose a discarded-write/validate ordering distinction on a fresh router, and removing only the early validation reproduces the previous mutation.",
 "nonClaims":["Already described by contributor; no blind bug discovery",
 "Full arbitrary Go code-to-semantics transformation unknown",
 "Tree mutation is local state, not general observable nontermination",
 "A timeout is bounded observation, not nontermination proof",
 "No measured advantage over competent review",
 "No upstream writes"] }
print(json.dumps(report,sort_keys=True,indent=2))
