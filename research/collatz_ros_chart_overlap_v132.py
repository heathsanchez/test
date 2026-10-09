#!/usr/bin/env python3
"""V132: persist a theorem-scoped GENERAL two-clock chart-overlap capability.

V131's Lean theorem is universally CONDITIONAL on equal endpoint
intercepts and slopes, plus strict source-guard hypotheses. That theorem
does NOT license an arbitrary claimed chart. The controller therefore
distinguishes:
  1. the formally checked generic *conditional* compiler,
  2. the separately Lean-qualified unconditional all-offset root9 family,
  3. concrete symbolic chart hypotheses verified by an executable exact
     integer checker (BOUNDED_EXACT, not individually formalised).

It retains exact V130 proof state, the V129 source21 family, both clock
coordinates, all negative controls, stable support pins and revocation
closure. It never concludes global Collatz convergence.
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
    ADMISSION as V130_ADMISSION, EXTRA_PROOF_PINS, FROZEN_LAW,
    RelationalController
)

ADMISSION="COLLATZ_ROS_V132_SOURCE_CHART_CONSEQUENCE_AUTHORITY"
REVISION=4
GENERIC_ID="v131_chart_overlap_generic"
ROOT9_ID="v131_root9_formal_family"
CHART_EXACT_ID="v132_exact_affine_chart_hypotheses"
ROOT9_ORIGIN="V131_ROOT9_FORMALLY_CHECKED_PARAMETRIC_JOIN"
CHART_ORIGIN="V131_CONDITIONAL_CHART_WITH_BOUNDED_EXACT_PREMISES"

ADDED_PROOF_PINS={
    GENERIC_ID:{
        "run":37986167263,
        "sha":"9bd21704ef5fe22cbd2e74b04de65969922b28d3",
        "status":"WARRANTED_FORMAL",
        "scope":"ONLY generic chartOverlapJoin conditional soundness: each chart needs its exact proven positive source, both clocks, base endpoint equality, endpoint coefficient equality and nonexpanding predecessor slope; NO universal existence",
    },
    ROOT9_ID:{
        "run":37986167263,
        "sha":"9bd21704ef5fe22cbd2e74b04de65969922b28d3",
        "status":"WARRANTED_FORMAL",
        "scope":"ONLY root9ViaChart source 9+1536*t -> positive smaller 3+486*t, clocks (9,1), endpoint 5+729*t, for every t natural; scope specifically checked in Lean",
    },
    CHART_EXACT_ID:{
        "run":None,"sha":None,
        "status":"BOUNDED_EXACT",
        "scope":"Only executable exact symbolic all-offset parity chart hypotheses; generic V131 Lean theorem supplies conditional soundness, but these arbitrary numerical premises are NOT separately kernel-checked",
    },
}
ROOT9_LAW={
    "law_id":"V131_ODD_THREE_ROOT9_FORMALLY_CHECKED_FAMILY",
    "support":ROOT9_ID,
    "theorem":"CollatzFinal.root9ViaChart",
    "parameter":"t:Nat",
    "source_affine":[9,1536],
    "earlier_affine":[3,486],
    "source_clock":9,
    "earlier_clock":1,
    "endpoint_affine":[5,729],
    "guard":"positive earlier source, 0<earlier<original source; both sources congruent to 3 mod 6",
    "global_coverage":"UNKNOWN",
    "constructor_status":"WARRANTED_FORMAL_ALL_OFFSETS",
}
GENERIC_COMPILER={
    "compiler_id":"V131_GENERIC_TWO_CLOCK_AFFINE_PARITY_CHART_OVERLAP",
    "support":GENERIC_ID,
    "theorem":"CollatzFinal.chartOverlapJoin",
    "status":"WARRANTED_FORMAL_CONDITIONAL_SOUNDNESS",
    "input":"a,p,i,j,u,v : Nat; t : Nat",
    "premises":[
        "0<p<a",
        "2^j*v <= 2^i*u",
        "T^i(a)=T^j(p)",
        "3^oddCount(a,i)*u=3^oddCount(p,j)*v",
    ],
    "conclusion":"LawfulFutureJoin(a+2^i*u*t,p+2^j*v*t,i,j)",
    "universally_available_applicable_charts":"UNKNOWN",
    "evidence_boundary":"new chart hypotheses are exact-symbolic-executable until separately Lean reified",
}

def root9_family(t:int)->tuple[int,int,int,int]:
    if type(t) is not int or t<0:
        raise ValueError("root9 law parameter must be a natural number")
    return (9+1536*t,3+486*t,9,1)

def chart_hypotheses(a:int,p:int,i:int,j:int,u:int,v:int,t:int)->dict:
    args=(a,p,i,j,u,v,t)
    if any(type(x) is not int for x in args):
        raise ValueError("all chart coordinates must be exact natural integers")
    if not (0<p<a and 0<u and 0<v and 0<=i<=512 and 0<=j<=512 and 0<=t):
        raise ValueError("invalid positive chart guards or bounded exact-check horizon")
    if any(x.bit_length()>8192 for x in args):
        raise ValueError("executable chart arithmetic exceeded declared resource boundary")

    def step(b:int,s:int)->tuple[int,int]:
        if s%2:
            raise ValueError("affine chart parity changes across offsets")
        return ((b//2,s//2) if b%2==0
                else ((3*b+1)//2,3*s//2))

    def trace(base:int,clock:int,offset_factor:int)->dict:
        source_slope=(1<<clock)*offset_factor
        b,s=base,source_slope
        odds=0
        for _ in range(clock):
            odds+=b%2
            b,s=step(b,s)
        assert s==3**odds*offset_factor
        return dict(base=base,clock=clock,u=offset_factor,
            source_slope=source_slope,endpoint=b,odd_count=odds,
            endpoint_slope=s)

    first=trace(a,i,u)
    second=trace(p,j,v)
    if second["source_slope"]>first["source_slope"]:
        raise ValueError("earlier-source slope exceeds the original source slope")
    if first["endpoint"]!=second["endpoint"]:
        raise ValueError("two actual chart base endpoints do not match")
    if first["endpoint_slope"]!=second["endpoint_slope"]:
        raise ValueError("two actual chart endpoint slopes do not match for ALL offsets")

    n=a+first["source_slope"]*t
    q=p+second["source_slope"]*t
    endpoint=first["endpoint"]+first["endpoint_slope"]*t
    if not 0<q<n:
        raise ValueError("derived parameter violates strict original-source guard")
    return {
        "schema":"COLLATZ_V132_CHART_PREMISE_CERTIFICATE",
        "theorem_support":GENERIC_ID,
        "premise_authority":CHART_EXACT_ID,
        "parameters":{"a":a,"p":p,"i":i,"j":j,"u":u,"v":v,"t":t},
        "source_chart":first,
        "earlier_chart":second,
        "derived_source":n,
        "derived_earlier":q,
        "derived_endpoint":endpoint,
        "all_offset_symbolic_equality":True,
        "concrete_premises_individually_Lean_reified":False,
        "global_collatz":"UNKNOWN",
    }

class ChartController(RelationalController):
    def _check_support_table(self)->None:
        table=dict(BASE_RUNS,**PROOF_PINS,**EXTRA_PROOF_PINS,**ADDED_PROOF_PINS)
        s=self.state
        if s.get("admission_schema")!=ADMISSION or s.get("controller_revision")!=REVISION:
            raise ValueError("wrong source-chart proof-admission schema or revision")
        if set(s["support"])!=set(table):
            raise ValueError("unregistered exact/formal support in source-chart controller")
        for name,pin in table.items():
            actual=s["support"][name]
            expected=({**pin,"status":"REVOKED"} if actual.get("status")=="REVOKED" else pin)
            if actual!=expected:
                raise ValueError("modified chart theorem pin or unqualified support scope: "+name)

    def _check_claim(self,w:dict,known:dict,live_ids:set[str],
                     is_active:bool)->None:
        kind=w.get("origin")
        if kind not in (ROOT9_ORIGIN,CHART_ORIGIN):
            return super()._check_claim(w,known,live_ids,is_active)
        self._validate_record_id(w)
        verify_join(w)
        if w["parents"]:
            raise ValueError("chart-derived direct source witness cannot borrow parent proof IDs")
        n,p,a,b=(w[k] for k in
                 ("source","earlier","source_clock","earlier_clock"))
        if kind==ROOT9_ORIGIN:
            if w["support"]!=ROOT9_ID:
                raise ValueError("root9 formally verified theorem substitution")
            if n<9 or (n-9)%1536:
                raise ValueError("not in the exact formal root9 all-offset source family")
            t=(n-9)//1536
            if (n,p,a,b)!=root9_family(t) or w["common"]!=5+729*t:
                raise ValueError("false root9 formal parameter, earlier root or clocks")
            if is_active and self.state["support"][ROOT9_ID]["status"]!="WARRANTED_FORMAL":
                raise ValueError("root9 formal source revoked")
            return

        if w["support"]!=CHART_EXACT_ID:
            raise ValueError("generic chart arithmetic needs its exact bounded source authority")
        evidence=self.state.get("chart_instances",{}).get(w["id"])
        if evidence is None:
            raise ValueError("a source-specific generic chart lacks its actual premise record")
        params=evidence.get("parameters",{})
        if set(params)!=set(("a","p","i","j","u","v","t")):
            raise ValueError("incomplete generic chart coordinate")
        qualified=chart_hypotheses(*(params[k] for k in ("a","p","i","j","u","v","t")))
        if evidence!=qualified:
            raise ValueError("cached generic chart premises differ from exact replay")
        if (n,p,a,b,w["common"])!=(
            qualified["derived_source"],qualified["derived_earlier"],
            params["i"],params["j"],qualified["derived_endpoint"]):
            raise ValueError("generic chart witness is NOT entailed by recorded parameters")
        if is_active and any(self.state["support"][k]["status"]=="REVOKED"
              for k in (GENERIC_ID,CHART_EXACT_ID)):
            raise ValueError("active chart join depends on revoked formal compiler or exact premises")

    def audit(self)->None:
        # TypedController's runtime checks source-relative actual equality,
        # parent DAGs and PROOF CONTRACTS; skip V130's now-superseded
        # fixed single-parametric-law/revision comparison only.
        TypedController.audit(self)
        s=self.state
        if s.get("parametric_laws")!=[FROZEN_LAW,ROOT9_LAW]:
            raise ValueError("unqualified unconditional all-offset law was promoted")
        if s.get("conditional_compilers")!=[GENERIC_COMPILER]:
            raise ValueError("theorem obligations and conclusion were mutated")
        if s["grammar"]["revision"]!=3:
            raise ValueError("unqualified root-chart grammar revision")
        if any(x not in s["grammar"]["constructors"] for x in
               ("RELATIONAL_ODD_THREE_ROOT_JOIN",
                "FORMAL_ROOT9_TWO_CLOCK_JOIN",
                "TWO_CLOCK_CHART_OVERLAP_CONDITIONAL")):
            raise ValueError("incomplete chart grammar")
        if "PREFERRED_ROOT_SELECTOR" not in s["grammar"]["rejected_as_complete"]:
            raise ValueError("V128 falsifier lost in grammar migration")
        joins=s["joins"]+s["archived_joins"]
        expected={w["id"] for w in joins if w["origin"]==CHART_ORIGIN}
        if set(s.get("chart_instances",{}))!=expected:
            raise ValueError("orphan/missing generic premise evidence across active and archive")
        if s["global_collatz"]!="UNKNOWN" or s["qed"] is not False or s["universal_event_producer_proved"]:
            raise ValueError("the conditional chart compiler cannot assert Collatz QED")

    def admit_root9(self,t:int)->bool:
        if self.state["support"][ROOT9_ID]["status"]!="WARRANTED_FORMAL":
            raise ValueError("formal root9 theorem not live")
        n,p,i,j=root9_family(t)
        return self.add(make_join(n,p,i,j,ROOT9_ID,ROOT9_ORIGIN))

    def admit_chart(self,a:int,p:int,i:int,j:int,u:int,v:int,t:int)->bool:
        if any(self.state["support"][key]["status"]=="REVOKED"
               for key in (GENERIC_ID,CHART_EXACT_ID)):
            raise ValueError("generic chart compiler or premise authority revoked")
        proof=chart_hypotheses(a,p,i,j,u,v,t)
        witness=make_join(proof["derived_source"],proof["derived_earlier"],
                          i,j,CHART_EXACT_ID,CHART_ORIGIN)
        if witness["id"] in {w["id"] for w in self.state["joins"]+self.state["archived_joins"]}:
            return False
        self.state["chart_instances"][witness["id"]]=proof
        try:
            return self.add(witness)
        except Exception:
            self.state["chart_instances"].pop(witness["id"],None)
            self.audit()
            raise

    def reclose(self)->int:
        return super().reclose()

    def revoke(self,support_id:str)->int:
        if support_id==GENERIC_ID:
            removed=0
            if self.state["support"][CHART_EXACT_ID]["status"]!="REVOKED":
                removed+=super().revoke(CHART_EXACT_ID)
            if self.state["support"][ROOT9_ID]["status"]!="REVOKED":
                removed+=super().revoke(ROOT9_ID)
            removed+=super().revoke(GENERIC_ID)
            return removed
        return super().revoke(support_id)

def migrate(original:dict)->ChartController:
    s=deepcopy(original)
    if s.get("admission_schema")==ADMISSION:
        return ChartController(s)
    if s.get("admission_schema")!=V130_ADMISSION:
        raise ValueError("only V130 formally qualified state can be migrated")
    RelationalController(s).audit()
    s["controller_revision"]=REVISION
    s["admission_schema"]=ADMISSION
    s["support"].update(deepcopy(ADDED_PROOF_PINS))
    s["parametric_laws"].append(deepcopy(ROOT9_LAW))
    s["conditional_compilers"]=[deepcopy(GENERIC_COMPILER)]
    s["chart_instances"]={}
    s["grammar"]["revision"]=3
    s["grammar"]["constructors"].extend(
        ["FORMAL_ROOT9_TWO_CLOCK_JOIN","TWO_CLOCK_CHART_OVERLAP_CONDITIONAL"])
    s["history"].append({
        "op":"ADMIT_FORMAL_CONDITIONAL_CHART_COMPILER_AND_EXACT_ROOT9_SCOPE",
        "generic_theorem_run":37986167263,
        "generic_theorem_blob":"c35bde45d11aad51f46e6e8beced5322acd43e9b",
        "formal_root9_theorem":"CollatzFinal.root9ViaChart",
        "separate_exact_chart_premise_authority":True,
        "protect_two_independent_clocks":True,
        "universal_source_event_production":"UNKNOWN",
        "global_collatz":"UNKNOWN",
    })
    return ChartController(s)

def bootstrap(path:Path=Path("research/collatz_ros_state_v130.json"))->ChartController:
    c=migrate(json.loads(path.read_text()))
    assert c.admit_root9(0)
    assert c.admit_chart(15,3,8,1,3,81,0)
    assert c.reclose()==2
    assert c.status(9)["earlier"]==3
    assert c.status(15)["earlier"]==3
    assert c.state["qed"] is False
    c.audit()
    return c

def open_state(path:Path)->ChartController:
    return migrate(json.loads(path.read_text()))

def main()->None:
    cli=argparse.ArgumentParser()
    cli.add_argument("--input",type=Path,default=Path("research/collatz_ros_state_v130.json"))
    cli.add_argument("--bootstrap",action="store_true")
    cli.add_argument("--output",type=Path)
    cli.add_argument("--revoke-support")
    args=cli.parse_args()
    controller=bootstrap(args.input) if args.bootstrap else open_state(args.input)
    archived=controller.revoke(args.revoke_support) if args.revoke_support else 0
    key=dump(controller,args.output) if args.output else digest(controller.state)
    print(json.dumps({
        "schema":ADMISSION,"state_sha256":key,
        "live_joins":len(controller.state["joins"]),
        "formal_parametric_laws":len(controller.state["parametric_laws"]),
        "conditional_compilers":len(controller.state["conditional_compilers"]),
        "exact_chart_instances":len(controller.state["chart_instances"]),
        "source9":controller.status(9),"source15":controller.status(15),
        "source27":controller.status(27),
        "archived":archived,
        "global_collatz":controller.state["global_collatz"],
        "universal_event_producer_proved":controller.state["universal_event_producer_proved"],
        "qed":False,
    },sort_keys=True))

if __name__=="__main__":
    main()
