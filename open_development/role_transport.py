"""Bounded role transport: a retained verified lift becomes a reusable developer action.

This is not a new arithmetic axiom or unrestricted operator invention. The
existing interpreter already understands arbitrary nested product certificates.
The *old acquisition policy* searched only one named parent shape. The typed
search residual and an already admitted executable 'lift-x' role motivate a
minimum conservative repair: consider that same role against other retained
verified parents, and check each constructed program with exact replay.

Historical source records retain their source verifier identity. This adapter
uses a distinct verifier bound to this exact source and grants only a bounded
bridge from live, correctly hashed original records. No forged source authority,
stale dependency, or identity-only capability is trusted.
"""
from __future__ import annotations

from dataclasses import asdict
from fractions import Fraction as Q
from hashlib import sha256
from pathlib import Path
from typing import Any, Mapping

from .composition import (ProofCompositionAdapter, construct_product,
                          construct_nested_product, replay_program,
                          program_shape, check_program)
from .proof import half_line_square, interval_affine, norm
from .runtime import (Repair, CapabilityContract, admission_id,
                      canonical, digest)

ORIGINAL_VERIFIER = ProofCompositionAdapter.verifier_id


class QualifiedRoleLiftAdapter(ProofCompositionAdapter):
    """A different verifier: preserves old proof meaning and qualifies new role."""
    verifier_id = "bounded-requalified-lift-v1:" + digest({
        "original_verifier": ORIGINAL_VERIFIER,
        "policy_source_sha256": sha256(Path(__file__).read_bytes()).hexdigest(),
        "role": "transport-certified-lift-x-across-parent-shapes",
        "replay_checker": "same exact check_program and replay_program"})

    def _source_checked(self, rid: str, rec: Mapping[str, Any],
                        state: Mapping[str, Any]) -> bool:
        try:
            if rec["id"] != rid or rec["status"] != "verified":
                return False
            rd = rec["repair"]
            ev = rec["evidence"]
            if rd["kind"] != "capability" or rd["scope"] != self.name:
                return False
            if ev["verifier"] not in (ORIGINAL_VERIFIER,self.verifier_id):
                return False
            if ev["verdict"] != "verified" or ev["scope"] != self.name:
                return False
            if ev["certificate"].get("accepted") is not True:
                return False
            if not rec["attachment"].get("executable"):
                return False
            contract = CapabilityContract(**rd["contract"])
            if contract not in (self.program_contract,self.constructor_contract):
                return False
            rebuild = Repair(rd["kind"], rd["name"], rd["payload"],rd["scope"],
                             tuple(rd["dependencies"]),contract)
            if rebuild.id != ev["claim"]:
                return False
            if admission_id(rebuild,ev["verifier"]) != rid:
                return False
            if any(x not in state["capabilities"] for x in rd["dependencies"]):
                return False
            if rd["payload"].get("constructor") == "binary_product":
                return contract == self.constructor_contract and not rd["dependencies"]
            if contract != self.program_contract:
                return False
            op = rd["payload"].get("body",{}).get("op")
            if op not in {"fit-square","fit-affine","lift-x"}:
                return False
            if op == "lift-x" and rd["dependencies"] != [rd["payload"]["body"].get("callee")]:
                return False
            return rd["payload"].get("program_shape") is not None
        except (ValueError,KeyError,TypeError,AttributeError):
            return False

    def _constructor(self,state):
        return next((rid for rid,rec in state["capabilities"].items()
                     if self._source_checked(rid,rec,state)
                     and rec["repair"]["payload"].get("constructor")=="binary_product"),None)

    def _programs(self,state):
        return {rec["repair"]["payload"]["program_shape"]:rid
                for rid,rec in state["capabilities"].items()
                if self._source_checked(rid,rec,state)
                and "program_shape" in rec["repair"]["payload"]}

    def execute(self,state,rid,poly,domain,trace=None,active=()):
        """Exact certificate replay, with a checked bridge to source authority."""
        trace=[] if trace is None else trace
        rec=state["capabilities"].get(rid)
        if rec is None or rid in active or not self._source_checked(rid,rec,state):
            return None
        repair=rec["repair"]
        body=repair["payload"].get("body",{})
        trace.append(rid)
        try:
            if body.get("op")=="fit-affine":
                program=interval_affine(poly,domain) if domain[0]=="interval" else None
            elif body.get("op")=="fit-square":
                program=construct_product(poly,domain) if domain[0]=="ray" else None
            elif body.get("op")=="lift-x":
                parent=body.get("callee")
                if repair["dependencies"] != [parent]:
                    return None
                program=construct_nested_product(
                    poly,domain,
                    lambda q,d:self.execute(state,parent,q,d,trace,(*active,rid)))
            else:
                return None
            if (program is None or
                program_shape(program)!=repair["payload"].get("program_shape") or
                not check_program(poly,domain,program)):
                return None
            return program
        except (TypeError,KeyError,ValueError,ZeroDivisionError,OverflowError):
            return None

    def _source_role(self,state) -> bool:
        """Verified developmental history enables role reinterpretation."""
        for rid,rec in state["capabilities"].items():
            if not self._source_checked(rid,rec,state):
                continue
            rd=rec["repair"]
            if (rec["evidence"]["verifier"]==ORIGINAL_VERIFIER
                and rd["payload"].get("body",{}).get("op")=="lift-x"
                and rd["dependencies"]):
                return True
        return False

    def _candidate(self,state,poly,domain):
        # Reuse all *old* acquisition routes before proposing a change.
        old,dependency,body,trace=super()._candidate(state,poly,domain)
        if old is not None:
            return old,dependency,body,trace
        # A role change is admissible only after the predecessor's independently
        # qualified executable lift-x exists under the original verifier.
        if not self._source_role(state) or domain[0]!="interval":
            return None,None,None,[]
        p=norm(poly)
        if p.get(0,Q(0))!=0 or not p:
            return None,None,None,[]
        options=[]
        for parent in self._programs(state).values():
            trace=[]
            program=construct_nested_product(
                poly,domain,lambda q,d,rid=parent,ts=trace:
                    self.execute(state,rid,q,d,ts))
            if program is not None and check_program(poly,domain,program):
                options.append((program,parent,{"op":"lift-x","callee":parent},trace))
        # Do not turn enumeration order among genuinely distinct lawful
        # requalifications into fictitious semantic uniqueness.
        keys={(digest(prog),rid) for prog,rid,_,_ in options}
        if len(keys)!=1:
            return None,None,None,[]
        return options[0]
