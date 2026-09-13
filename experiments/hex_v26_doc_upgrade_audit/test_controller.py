#!/usr/bin/env python3
import json, pathlib
from controller import Encounter, Decision, resolve

cases=[
 ("verified_witness_settles",Encounter(verified_witness=True),Decision.EXECUTE_SETTLED),
 ("retained_capability_reused",Encounter(retained_capability_applicable=True),Decision.EXECUTE_REUSE),
 ("incomplete_failure_unknown",Encounter(search_complete=False,certified_inadequate=False),Decision.UNKNOWN),
 ("complete_but_no_obstruction_unknown",Encounter(search_complete=True,certified_inadequate=False),Decision.UNKNOWN),
 ("certified_exhaustion_develops",Encounter(search_complete=True,certified_inadequate=True,minimal_verified_repairs=0),Decision.DEVELOP),
 ("noncanonical_repairs_wait",Encounter(certified_inadequate=True,minimal_verified_repairs=3),Decision.WAIT_FUTURE),
 ("future_selects_promote",Encounter(certified_inadequate=True,minimal_verified_repairs=3,future_unique_survivor=True),Decision.PROMOTE),
 ("unique_minimum_promotes",Encounter(certified_inadequate=True,minimal_verified_repairs=1),Decision.PROMOTE),
 ("replay_failure_rejects",Encounter(certified_inadequate=True,minimal_verified_repairs=1,protected_replay_ok=False),Decision.REJECT_CHANGE),
 ("redundancy_contracts",Encounter(redundancy_proven=True,protected_replay_ok=True),Decision.CONTRACT),
 ("bad_contraction_rejected",Encounter(redundancy_proven=True,protected_replay_ok=False),Decision.REJECT_CHANGE),
 ("reuse_beats_spurious_obstruction",Encounter(retained_capability_applicable=True,certified_inadequate=True,minimal_verified_repairs=2),Decision.EXECUTE_REUSE),
]
rows=[]
for name,e,want in cases:
    got=resolve(e)
    rows.append({"case":name,"got":got.name,"want":want.name,"pass":got is want})
    assert got is want,(name,got,want)

# Mutation controls: these are the four constitutional errors the document must forbid.
assert resolve(Encounter(search_complete=False,certified_inadequate=False)) is not Decision.DEVELOP
assert resolve(Encounter(certified_inadequate=True,minimal_verified_repairs=2)) is not Decision.PROMOTE
assert resolve(Encounter(certified_inadequate=True,minimal_verified_repairs=1,protected_replay_ok=False)) is not Decision.PROMOTE
assert resolve(Encounter(retained_capability_applicable=True)) is not Decision.DEVELOP

out={
 "verdict":"PASS_FROZEN_EXECUTE_DEVELOP_PROMOTE_CONTROLLER",
 "cases":rows,
 "constitutional_controls":{
  "no_growth_from_search_failure":True,
  "no_guess_under_noncanonicity":True,
  "no_admission_when_replay_breaks":True,
  "reuse_precedes_rediscovery":True
 }
}
p=pathlib.Path(__file__).resolve().parent/"results"
p.mkdir(exist_ok=True)
(p/"controller_audit.json").write_text(json.dumps(out,indent=2,sort_keys=True)+"\n")
print(json.dumps(out,indent=2,sort_keys=True))
