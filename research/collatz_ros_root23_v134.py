#!/usr/bin/env python3
"""V134 persistent ROS successor: the V133 infinite source23 root-family
is FORMAL, and its exact t=0 instance closes two additional source27
class obligations by reusing V122/V123 two-clock certificates.

No origin/clock/parameter can inherit an unrelated theorem's authority.
The V131 conditional generic chart stays separate from its BOUNDED_EXACT
premise instances. The V132 exact state is never overwritten.

Protected live witnesses after bootstrap:
  pre-V134 13 records,
  new source23 -> odd-three-root3 @ (7,1),
  derived 23 ->2 @ (11,1),
  derived 27 ->3 @ (66,1),
  derived 27 ->2 @ (70,1).

This does not prove global Collatz or the entire source27 residue class.
"""
from __future__ import annotations

import argparse,json
from copy import deepcopy
from pathlib import Path

from research.collatz_ros_future_controller_v123 import (
    BASE_RUNS,make_join,digest,dump,verify_join,
)
from research.collatz_ros_future_controller_v124 import PROOF_PINS,TypedController
from research.collatz_ros_relational_root_v130 import EXTRA_PROOF_PINS,FROZEN_LAW
from research.collatz_ros_chart_overlap_v132 import (
    ADMISSION as V132_ADMISSION,
    ADDED_PROOF_PINS, ROOT9_LAW, GENERIC_COMPILER, CHART_ORIGIN,
    GENERIC_ID, CHART_EXACT_ID, ROOT9_ID,
    ChartController,
)

ADMISSION="COLLATZ_ROS_V134_WARRANTED_ROOT23_AND_LATE_SOURCE27_REJOIN"
REVISION=5
ROOT23_SUPPORT="v133_formal_root23_chart_and_27_composition"
ROOT23_ORIGIN="V133_FORMAL_ALL_OFFSET_ROOT23_TO_ODD_THREE_ROOT3"

V133_SCOPE={
    ROOT23_SUPPORT:{
        "run":37988274186,
        "sha":"b734f5c5dbb9b52ec1eea6df84e17dd20a3a97d0",
        "status":"WARRANTED_FORMAL",
        "scope":"only all-offset V133 root23ViaChart t: source 23+384*t, smaller odd three-root 3+54*t, clocks (7,1), exact endpoint 5+81*t; plus separately checked composed numeric source27→root3 at (66,1) and root2 (70,1), no full residue-class closure",
    }
}
ROOT23_LAW={
    "law_id":"V133_SOURCE23_ALL_OFFSET_TO_ODD_THREE_ROOT3",
    "support":ROOT23_SUPPORT,
    "theorem":"CollatzFinal.root23ViaChart",
    "parameter":"t:Nat",
    "source_affine":[23,384],
    "earlier_affine":[3,54],
    "source_clock":7,
    "earlier_clock":1,
    "endpoint_affine":[5,81],
    "guard":"0<3+54*t<23+384*t and earlier source congruent to 3 mod6 for every t",
    "global_coverage":"UNKNOWN",
    "constructor_status":"WARRANTED_FORMAL_ALL_OFFSETS",
}

def source23_root3(t:int)->tuple[int,int,int,int]:
    if type(t) is not int or t<0:
        raise ValueError("V133 theorem parameter must be a natural number")
    return 23+384*t,3+54*t,7,1

class Root23Controller(ChartController):
    def _check_support_table(self)->None:
        s=self.state
        pins=dict(BASE_RUNS,**PROOF_PINS,**EXTRA_PROOF_PINS,
                  **ADDED_PROOF_PINS,**V133_SCOPE)
        if s.get("controller_revision")!=REVISION or s.get("admission_schema")!=ADMISSION:
            raise ValueError("V134 proof-admission schema/revision mismatch")
        if set(s["support"])!=set(pins):
            raise ValueError("unrecognized V134 theorem support table")
        for name,pin in pins.items():
            actual=s["support"][name]
            expected=({**pin,"status":"REVOKED"} if actual.get("status")=="REVOKED" else pin)
            if actual!=expected:
                raise ValueError("modified proof-source scope or pin: "+name)

    def _check_claim(self,w:dict,known:dict,live_ids:set[str],is_active:bool)->None:
        if w.get("origin")!=ROOT23_ORIGIN:
            return super()._check_claim(w,known,live_ids,is_active)
        self._validate_record_id(w)
        verify_join(w)
        if w["support"]!=ROOT23_SUPPORT or w["parents"]:
            raise ValueError("root23 theorem cannot borrow an unrelated support/parent")
        n,p,a,b=(w[k] for k in
                 ("source","earlier","source_clock","earlier_clock"))
        if n<23 or (n-23)%384:
            raise ValueError("source outside V133 all-offset family")
        t=(n-23)//384
        if (n,p,a,b)!=source23_root3(t) or w["common"]!=5+81*t:
            raise ValueError("root23 formal theorem exact earlier source or clocks falsified")
        if is_active and self.state["support"][ROOT23_SUPPORT]["status"]!="WARRANTED_FORMAL":
            raise ValueError("root23 theorem revoked")

    def audit(self)->None:
        # Bypass V132's *old* fixed list of two unconditional parametric
        # laws while retaining every independent TypedController audit:
        # arithmetic replay, ID integrity, live proof DAG and strict p<n.
        TypedController.audit(self)
        s=self.state
        if s.get("parametric_laws")!=[FROZEN_LAW,ROOT9_LAW,ROOT23_LAW]:
            raise ValueError("new parametric root law omitted or forged")
        if s.get("conditional_compilers")!=[GENERIC_COMPILER]:
            raise ValueError("V131 formal conditional theorem contract changed")
        if s["grammar"]["revision"]!=4:
            raise ValueError("unexpected grammar revision")
        for k in ("RELATIONAL_ODD_THREE_ROOT_JOIN",
                  "FORMAL_ROOT9_TWO_CLOCK_JOIN",
                  "TWO_CLOCK_CHART_OVERLAP_CONDITIONAL",
                  "FORMAL_ROOT23_TO_ODD_THREE_ROOT3"):
            if k not in s["grammar"]["constructors"]:
                raise ValueError("missing permitted proof constructor: "+k)
        if "PREFERRED_ROOT_SELECTOR" not in s["grammar"]["rejected_as_complete"]:
            raise ValueError("V128 all-clock canonical-root counterexample lost")
        expected={w["id"] for w in s["joins"]+s["archived_joins"]
                  if w.get("origin")==CHART_ORIGIN}
        if set(s["chart_instances"])!=expected:
            raise ValueError("generic exact source-chart evidence was lost/replaced")
        if s["global_collatz"]!="UNKNOWN" or s["qed"] is not False or s["universal_event_producer_proved"]:
            raise ValueError("finite source27 consequence is not global Collatz")

    def admit_source23_family(self,t:int)->bool:
        if self.state["support"][ROOT23_SUPPORT]["status"]!="WARRANTED_FORMAL":
            raise ValueError("cannot admit new instance from revoked source23 theorem")
        n,p,a,b=source23_root3(t)
        return self.add(make_join(n,p,a,b,ROOT23_SUPPORT,ROOT23_ORIGIN))

    def reclose(self)->int:
        return super().reclose()

    def revoke(self,support_id:str)->int:
        # The V133 formal root23 specialization is defined using the
        # V131 conditional chart theorem. Revocation propagates across
        # this THEOREM dependency, not only across witness parent IDs.
        if support_id==GENERIC_ID:
            count=0
            if self.state["support"][ROOT23_SUPPORT]["status"]!="REVOKED":
                count+=super().revoke(ROOT23_SUPPORT)
            count+=super().revoke(GENERIC_ID)
            return count
        return super().revoke(support_id)

def migrate(prior:dict)->Root23Controller:
    s=deepcopy(prior)
    if s.get("admission_schema")==ADMISSION:
        return Root23Controller(s)
    if s.get("admission_schema")!=V132_ADMISSION:
        raise ValueError("only the V132 formally qualified exact state can be migrated")
    ChartController(s).audit()
    s["support"].update(deepcopy(V133_SCOPE))
    s["controller_revision"]=REVISION
    s["admission_schema"]=ADMISSION
    s["parametric_laws"].append(deepcopy(ROOT23_LAW))
    s["grammar"]["revision"]=4
    s["grammar"]["constructors"].append("FORMAL_ROOT23_TO_ODD_THREE_ROOT3")
    s["history"].append({
        "op":"ADMIT_V133_SOURCE23_FORMAL_ALL_OFFSET_AND_RECLOSE",
        "source_theorem_run":37988274186,
        "root23_to_root3_law":"23+384*t -> 3+54*t, clocks (7,1)",
        "verified_original27_to23":"V122 source27 clocks (59,0)",
        "qualified_composition_rule":"V123 LawfulFutureJoin.compose",
        "expected_source27_to_root3_clocks":[66,1],
        "expected_source27_to_root2_clocks":[70,1],
        "no_claim_for_all_27_CRT_lifts":True,
        "global_collatz":"UNKNOWN",
    })
    return Root23Controller(s)

def bootstrap(path:Path=Path("research/collatz_ros_state_v132.json"))->Root23Controller:
    c=migrate(json.loads(path.read_text()))
    assert c.admit_source23_family(0)
    assert c.reclose()==3
    assert c.status(23)["earlier"]==3
    assert c.status(27)["earlier"]==23
    assert c.status(27)["source_clock"]==59
    assert len(c.state["joins"])==17
    c.audit()
    return c

def open_state(path:Path)->Root23Controller:
    return migrate(json.loads(path.read_text()))

def main()->None:
    p=argparse.ArgumentParser()
    p.add_argument("--input",type=Path,
                   default=Path("research/collatz_ros_state_v132.json"))
    p.add_argument("--bootstrap",action="store_true")
    p.add_argument("--output",type=Path)
    p.add_argument("--revoke-support")
    args=p.parse_args()
    controller=bootstrap(args.input) if args.bootstrap else open_state(args.input)
    archived=controller.revoke(args.revoke_support) if args.revoke_support else 0
    seal=dump(controller,args.output) if args.output else digest(controller.state)
    print(json.dumps({
        "schema":ADMISSION,
        "state_sha256":seal,
        "live_joins":len(controller.state["joins"]),
        "parametric_laws":len(controller.state["parametric_laws"]),
        "conditional_compilers":len(controller.state["conditional_compilers"]),
        "source23":controller.status(23),
        "source27":controller.status(27),
        "archived":archived,
        "global_collatz":controller.state["global_collatz"],
        "qed":False
    },sort_keys=True))

if __name__=="__main__":
    main()
