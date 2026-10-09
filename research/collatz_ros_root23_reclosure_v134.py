#!/usr/bin/env python3
"""V134 — source-indexed root23 family and genuine late-join consequence reuse.

The actual first smaller-source merger of 27 occurs at source-clock 59
with earlier source 23 (V122). V133 proves an independently scoped
all-offset source23→odd-three-root3 family:
    T^7(23 + 384*t) = T(3 + 54*t) = 5+81*t.
This file types the V133 FORMAL source authority and admits the single
needed instance t=0; the existing V123 compositor then derives
    27→3 at clocks (66,1)
    23→2 at clocks (11,1)
    27→2 at clocks (70,1).
The earliest certified source27 clock stays 59; source27→3 is NOT
claimed optimal and the source27 all-offset cylinder is NOT claimed.

V132 generic chart soundness, two unconditional formal families, one
executable chart premise, earlier proof pins, negative controls and exact
large naturals are retained without loss. Global Collatz UNKNOWN.
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
    PROOF_PINS, TypedController
)
from research.collatz_ros_relational_root_v130 import (
    EXTRA_PROOF_PINS, FROZEN_LAW
)
from research.collatz_ros_chart_overlap_v132 import (
    ADMISSION as V132_ADMISSION,
    ADDED_PROOF_PINS, ROOT9_LAW, GENERIC_COMPILER,
    ChartController, GENERIC_ID, CHART_EXACT_ID, ROOT9_ID,
    ROOT9_ORIGIN, CHART_ORIGIN, chart_hypotheses
)

ADMISSION = "COLLATZ_ROS_V134_LATE_ROOT_REUSE_AUTHORITY"
REVISION = 5
ROOT23_ID = "v133_root23_formal_family"
ROOT23_ORIGIN = "V133_ROOT23_FORMAL_ALL_OFFSET_JOIN"

ROOT23_PROOF_PIN = {
    ROOT23_ID:{
        "run":37988274186,
        "sha":"b734f5c5dbb9b52ec1eea6df84e17dd20a3a97d0",
        "status":"WARRANTED_FORMAL",
        "scope":"ONLY V133 root23ViaChart: 23+384*t→3+54*t, source-clock7, earlier-clock1, endpoint5+81*t for all t Nat; Lean also qualified 27→3 and 27→2 at clocks (66,1) and (70,1) by separate V122 source27 premise",
    }
}

ROOT23_LAW = {
    "law_id":"V133_ROOT23_ODD_THREE_ROOT_ALL_OFFSET",
    "support":ROOT23_ID,
    "theorem":"CollatzFinal.root23ViaChart",
    "parameter":"t:Nat",
    "source_affine":[23,384],
    "earlier_affine":[3,54],
    "source_clock":7,
    "earlier_clock":1,
    "endpoint_affine":[5,81],
    "guard":"0<3+54*t<23+384*t, source and earlier positive, earlier root=3 mod6",
    "global_coverage":"UNKNOWN",
    "constructor_status":"WARRANTED_FORMAL_ALL_OFFSETS",
}

def root23_family(t:int)->tuple[int,int,int,int]:
    if type(t) is not int or t<0:
        raise ValueError("V133 all-offset theorem parameter must be a nonnegative natural")
    return 23+384*t,3+54*t,7,1

class LateRootController(ChartController):
    def _check_support_table(self)->None:
        expected=dict(BASE_RUNS,**PROOF_PINS,**EXTRA_PROOF_PINS,
                      **ADDED_PROOF_PINS,**ROOT23_PROOF_PIN)
        state=self.state
        if state.get("admission_schema") != ADMISSION or state.get("controller_revision") != REVISION:
            raise ValueError("V134 protected proof-admission revision mismatch")
        if set(state["support"])!=set(expected):
            raise ValueError("missing or unexpected theorem authority")
        for name,pin in expected.items():
            current=state["support"][name]
            want=({**pin,"status":"REVOKED"} if current.get("status")=="REVOKED" else pin)
            if current!=want:
                raise ValueError("proof pin or exact theorem scope was modified: "+name)

    def _check_claim(self,w:dict,known:dict,active_ids:set[str],
                     is_active:bool)->None:
        if w.get("origin")!=ROOT23_ORIGIN:
            return super()._check_claim(w,known,active_ids,is_active)
        self._validate_record_id(w)
        verify_join(w)
        if w["support"]!=ROOT23_ID or w["parents"]:
            raise ValueError("root23 leaf must carry only exact V133 formal authority")
        n,p,i,j=(w[x] for x in ("source","earlier","source_clock","earlier_clock"))
        if n<23 or (n-23)%384!=0:
            raise ValueError("unrelated source cannot cite V133 root23 theorem")
        t=(n-23)//384
        if (n,p,i,j)!=root23_family(t) or w["common"]!=5+81*t:
            raise ValueError("V133 earlier-root, clock, slope or endpoint was altered")
        if is_active and self.state["support"][ROOT23_ID]["status"]!="WARRANTED_FORMAL":
            raise ValueError("cannot use revoked V133 parametric theorem")

    def audit(self)->None:
        # ChartController.audit has the prior specific V132 frozen-list
        # assertion; preserve all V132 checks while extending ONLY
        # that one exact law list and revision.
        TypedController.audit(self)
        s=self.state
        if s.get("parametric_laws")!=[FROZEN_LAW,ROOT9_LAW,ROOT23_LAW]:
            raise ValueError("unwarranted parametric law edit")
        if s.get("conditional_compilers")!=[GENERIC_COMPILER]:
            raise ValueError("generic V131 chart compiler changed or widened")
        if s["grammar"].get("revision")!=4:
            raise ValueError("source23 grammar revision mismatch")
        for constructor in ("RELATIONAL_ODD_THREE_ROOT_JOIN",
                            "FORMAL_ROOT9_TWO_CLOCK_JOIN",
                            "TWO_CLOCK_CHART_OVERLAP_CONDITIONAL",
                            "FORMAL_ROOT23_TO_ODD_THREE_ROOT_JOIN"):
            if constructor not in s["grammar"]["constructors"]:
                raise ValueError("missing formally justified constructor: "+constructor)
        if "PREFERRED_ROOT_SELECTOR" not in s["grammar"]["rejected_as_complete"]:
            raise ValueError("V128 negative selector proof disappeared")
        full=s["joins"]+s["archived_joins"]
        expected_ids={w["id"] for w in full if w["origin"]==CHART_ORIGIN}
        if set(s.get("chart_instances",{}))!=expected_ids:
            raise ValueError("all active and archived generic chart instances need exact premises")
        if s["global_collatz"]!="UNKNOWN" or s["qed"] is not False or s["universal_event_producer_proved"] is not False:
            raise ValueError("source23 consequence reuse is NOT global Collatz QED")

    def admit_root23(self,t:int)->bool:
        if self.state["support"][ROOT23_ID]["status"]!="WARRANTED_FORMAL":
            raise ValueError("root23 all-offset theorem no longer qualifies new leaves")
        n,p,i,j=root23_family(t)
        return self.add(make_join(n,p,i,j,ROOT23_ID,ROOT23_ORIGIN))

def migrate(state:dict)->LateRootController:
    source=deepcopy(state)
    if source.get("admission_schema")==ADMISSION:
        return LateRootController(source)
    if source.get("admission_schema")!=V132_ADMISSION:
        raise ValueError("migration must start at the verified exact V132 checkpoint")
    ChartController(source).audit()
    s=deepcopy(source)
    s["controller_revision"]=REVISION
    s["admission_schema"]=ADMISSION
    s["support"].update(deepcopy(ROOT23_PROOF_PIN))
    s["parametric_laws"].append(deepcopy(ROOT23_LAW))
    s["grammar"]["revision"]=4
    s["grammar"]["constructors"].append("FORMAL_ROOT23_TO_ODD_THREE_ROOT_JOIN")
    s["history"].append({
        "op":"REFINE_FROM_V122_27_FIRST_LOWER_SOURCE_SEAM",
        "previous_exact_source":27,
        "old_qualified_predecessor":23,
        "source27_to23_clocks":[59,0],
        "new_formal_root23_typed_family":"23+384*t→3+54*t, clocks(7,1)",
        "qualified_v133_run":37988274186,
        "preserved_v131_chart_compiler_run":37986167263,
        "derive_source27_to3_by_parent_DAG":True,
        "derive_source27_to2_without_new_trajectory":True,
        "no_all_offset_source27_claim":True,
        "universal_event_producer":"UNKNOWN",
        "global_collatz":"UNKNOWN",
    })
    return LateRootController(s)

def bootstrap(path:Path=Path("research/collatz_ros_state_v132.json"))->LateRootController:
    controller=migrate(json.loads(path.read_text()))
    assert controller.admit_root23(0)
    num=controller.reclose()
    assert num==3,("unexpected consequence count",num)
    bypair={(x["source"],x["earlier"]):x for x in controller.state["joins"]}
    assert len(bypair)==17
    assert (bypair[23,3]["source_clock"],bypair[23,3]["earlier_clock"])==(7,1)
    assert (bypair[27,3]["source_clock"],bypair[27,3]["earlier_clock"])==(66,1)
    assert (bypair[23,2]["source_clock"],bypair[23,2]["earlier_clock"])==(11,1)
    assert (bypair[27,2]["source_clock"],bypair[27,2]["earlier_clock"])==(70,1)
    assert controller.status(27)["earlier"]==23
    assert controller.status(27)["source_clock"]==59
    controller.audit()
    return controller

def open_state(path:Path)->LateRootController:
    return migrate(json.loads(path.read_text()))

def main()->None:
    cli=argparse.ArgumentParser()
    cli.add_argument("--input",type=Path,default=Path("research/collatz_ros_state_v132.json"))
    cli.add_argument("--bootstrap",action="store_true")
    cli.add_argument("--output",type=Path)
    cli.add_argument("--revoke-support")
    args=cli.parse_args()
    controller=bootstrap(args.input) if args.bootstrap else open_state(args.input)
    revoked=controller.revoke(args.revoke_support) if args.revoke_support else 0
    checksum=dump(controller,args.output) if args.output else digest(controller.state)
    bypair={(w["source"],w["earlier"]):w for w in controller.state["joins"]}
    print(json.dumps({
        "schema":ADMISSION,
        "controller_revision":REVISION,
        "state_sha256":checksum,
        "live_two_clock_joins":len(controller.state["joins"]),
        "formal_parametric_root_laws":len(controller.state["parametric_laws"]),
        "formally_sound_conditional_chart_compilers":len(controller.state["conditional_compilers"]),
        "executable_generic_chart_instances":len(controller.state["chart_instances"]),
        "source27_earliest_lower_source_clock":controller.status(27).get("source_clock"),
        "source27_to3_clocks":[bypair[27,3]["source_clock"],bypair[27,3]["earlier_clock"]] if (27,3) in bypair else None,
        "source27_to2_clocks":[bypair[27,2]["source_clock"],bypair[27,2]["earlier_clock"]] if (27,2) in bypair else None,
        "archived_by_requested_revocation":revoked,
        "universal_event_producer_proved":False,
        "global_collatz":"UNKNOWN","qed":False,
    },sort_keys=True))

if __name__=="__main__":
    main()
