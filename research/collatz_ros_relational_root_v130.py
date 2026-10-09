#!/usr/bin/env python3
"""Collatz ROS V130: proof-typed RELATIONAL odd-three-root law, statefully.

Migrate the exact V124 restartable controller without deleting or weakening
its four V123 + three V124 lower-source certificates.

V128's kernel-checked source21 separator REJECTED completeness of a single
preferred root. V129 proved an all-offset relational replacement:
  n(t)=21+72*t, p(t)=3+12*t, T^3(n)=T^2(p)=8+27*t.

The preferred-root selector is a CLASS-IDENTITY search tool, not descent.
The new capability is ONE typed symbolic law; only necessary local
instantiations become concrete leaf witnesses. Reclose their downstream
verified consequences with the existing two-clock compose theorem.

This does not prove every odd 3-root has a lower coalescent.
GLOBAL COLLATZ remains UNKNOWN.
"""
from __future__ import annotations

import argparse
import json
from copy import deepcopy
from pathlib import Path

from research.collatz_ros_future_controller_v123 import (
    BASE_RUNS, make_join, verify_join, digest, dump
)
from research.collatz_ros_future_controller_v124 import (
    ADMISSION as V124_ADMISSION, DIRECT, COMPOSED, PROOF_PINS,
    TypedController
)

ADMISSION = "COLLATZ_ROS_V130_RELATIONAL_ODD_ROOT_AUTHORITY"
REVISION = 3
RELATIONAL_ORIGIN = "V129_FORMAL_ODD_THREE_ROOT_PARAMETRIC_JOIN"
RELATIONAL_SUPPORT = "v129_odd_three_root_family"
EXTRA_PROOF_PINS = {
    "v128_preferred_root_incomplete": {
        "run":37983621550,
        "sha":"2bda4439b015f4ac6e3aa901b84a6097776881a9",
        "status":"WARRANTED_FORMAL",
        "scope":"source21 chosen 3-root selector remains 21 on EVERY future step, but source3 joins at clocks 3,2; negative grammar separator only",
    },
    RELATIONAL_SUPPORT: {
        "run":37984356667,
        "sha":"f07db1c38e877a85d6116e876bebad8310b26bab",
        "status":"WARRANTED_FORMAL",
        "scope":"ONLY the all-offset odd three-root family 21+72*t -> 3+12*t at source clock3, earlier clock2, endpoint 8+27*t, theorem root21_family_join",
    }
}
FROZEN_LAW = {
    "law_id":"V129_ODD_THREE_ROOT_RELATIONAL_JOIN",
    "support":RELATIONAL_SUPPORT,
    "theorem":"CollatzFinal.root21_family_join",
    "parameter":"t:Nat",
    "source_affine":[21,72],
    "earlier_affine":[3,12],
    "source_clock":3,
    "earlier_clock":2,
    "endpoint_affine":[8,27],
    "guard":"0 < earlier < original source; both source and earlier congruent 3 modulo 6",
    "global_coverage":"UNKNOWN",
    "constructor_status":"WARRANTED_FORMAL_ALL_OFFSETS",
}

def rooted_family(t:int) -> tuple[int,int,int,int]:
    if type(t) is not int or t < 0:
        raise ValueError("V129 theorem parameter must be a natural number")
    return (21+72*t,3+12*t,3,2)

class RelationalController(TypedController):
    def _check_support_table(self) -> None:
        s=self.state
        if s.get("admission_schema") != ADMISSION or s.get("controller_revision") != REVISION:
            raise ValueError("unexpected or unsupported active law-admission policy")
        required=dict(BASE_RUNS, **PROOF_PINS, **EXTRA_PROOF_PINS)
        if set(s["support"]) != set(required):
            raise ValueError("undeclared theorem-support pin or missing authority")
        for name,pin in required.items():
            cur=s["support"][name]
            expected=({**pin,"status":"REVOKED"} if cur.get("status")=="REVOKED" else pin)
            if cur!=expected:
                raise ValueError("theorem support scope or exact proof head was modified: "+name)

    def _check_claim(self, w:dict, known:dict, live_ids:set[str],
                     is_active:bool) -> None:
        if w.get("origin") != RELATIONAL_ORIGIN:
            return super()._check_claim(w,known,live_ids,is_active)
        self._validate_record_id(w)
        verify_join(w)
        if w["support"] != RELATIONAL_SUPPORT or w["parents"]:
            raise ValueError("relational law requires its EXACT formal source and no parent")
        n,p,a,b=(w[k] for k in
                 ("source","earlier","source_clock","earlier_clock"))
        if n<21 or (n-21)%72 !=0:
            raise ValueError("source outside V129 formal source family")
        t=(n-21)//72
        if (n,p,a,b)!=rooted_family(t):
            raise ValueError("formal family slope, earlier root or clock was substituted")
        if w["common"]!=8+27*t or n%6 != 3 or p%6 != 3:
            raise ValueError("family semantic consequence does not match theorem")
        if is_active and self.state["support"][RELATIONAL_SUPPORT]["status"]!="WARRANTED_FORMAL":
            raise ValueError("v129 theorem no longer live")

    def audit(self) -> None:
        super().audit()
        if self.state.get("parametric_laws") != [FROZEN_LAW]:
            raise ValueError("parametric law was mutated or unqualified law added")
        if "RELATIONAL_ODD_THREE_ROOT_JOIN" not in self.state["grammar"]["constructors"]:
            raise ValueError("V128-forced relational constructor not installed")
        if "PREFERRED_ROOT_SELECTOR" not in self.state["grammar"]["rejected_as_complete"]:
            raise ValueError("source21 all-clock counterexample was lost")
        if self.state["grammar"]["revision"] != 2:
            raise ValueError("unqualified grammar revision")
        if self.state["global_collatz"]!="UNKNOWN" or self.state["qed"] is not False:
            raise ValueError("no global Collatz theorem exists")

    def admit_odd_root_family(self, t:int) -> bool:
        if self.state["support"][RELATIONAL_SUPPORT]["status"] != "WARRANTED_FORMAL":
            raise ValueError("cannot use revoked formal family")
        n,p,a,b=rooted_family(t)
        witness=make_join(n,p,a,b,RELATIONAL_SUPPORT,RELATIONAL_ORIGIN)
        return self.add(witness)

    def reclose(self)->int:
        return super().reclose()

def migrate(state:dict)->RelationalController:
    prior=deepcopy(state)
    if prior.get("admission_schema")==ADMISSION:
        return RelationalController(prior)
    if prior.get("admission_schema")!=V124_ADMISSION:
        raise ValueError("only qualified V124 persisted research state may be migrated")
    # Verify ALL original proof-bound witnesses before revising its grammar.
    TypedController(prior).audit()
    s=deepcopy(prior)
    s["support"].update(deepcopy(EXTRA_PROOF_PINS))
    s["admission_schema"]=ADMISSION
    s["controller_revision"]=REVISION
    s["parametric_laws"]=[deepcopy(FROZEN_LAW)]
    s["grammar"]["revision"]=2
    s["grammar"]["constructors"].append("RELATIONAL_ODD_THREE_ROOT_JOIN")
    s["grammar"]["rejected_as_complete"].append("PREFERRED_ROOT_SELECTOR")
    s["retired_hypotheses"].append("a_single_preferred_three_root_is_a_complete_lower_source_detector")
    s["history"].append({
        "op":"REFINE_GRAMMAR_FROM_FORMAL_ALL_CLOCK_SEPARATOR",
        "separator":"V128_SOURCE21_CHOSEN_ROOT_STUTTERS_FOR_EVERY_CLOCK",
        "proof_run":37983621550,
        "new_constructor":"V129_ODD_THREE_ROOT_RELATIONAL_JOIN",
        "law_run":37984356667,
        "law_scope":"all natural t in source 21+72*t ONLY",
        "original_source_preserved":True,
        "both_clocks_preserved":True,
        "global_collatz":"UNKNOWN",
    })
    return RelationalController(s)

def bootstrap(path:Path=Path("research/collatz_ros_state_v124.json"))->RelationalController:
    c=migrate(json.loads(path.read_text()))
    assert c.admit_odd_root_family(0)
    new=c.reclose()
    assert new==1, new
    assert c.status(21)["earlier"]==3
    assert c.state["global_collatz"]=="UNKNOWN"
    c.audit()
    return c

def open_state(path:Path)->RelationalController:
    return migrate(json.loads(path.read_text()))

def main()->None:
    parser=argparse.ArgumentParser()
    parser.add_argument("--input",type=Path,
       default=Path("research/collatz_ros_state_v124.json"))
    parser.add_argument("--bootstrap",action="store_true")
    parser.add_argument("--output",type=Path)
    parser.add_argument("--revoke-support")
    args=parser.parse_args()
    c=(bootstrap(args.input) if args.bootstrap else open_state(args.input))
    archived=c.revoke(args.revoke_support) if args.revoke_support else 0
    checksum=dump(c,args.output) if args.output else digest(c.state)
    print(json.dumps({
       "schema":ADMISSION,
       "active_witnesses":len(c.state["joins"]),
       "parametric_laws":len(c.state["parametric_laws"]),
       "source21":c.status(21),
       "source27":c.status(27),
       "archived":archived,
       "state_sha256":checksum,
       "universal_event_producer_proved":False,
       "global_collatz":c.state["global_collatz"],
       "qed":False,
    },sort_keys=True))

if __name__=="__main__":
    main()
