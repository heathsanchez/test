"""Typed MDA routing for the Collatz QCKN V1 adapter."""
from __future__ import annotations

from typing import Mapping

from .types import Intervention, Outcome


_BASE={
    Outcome.CERTIFIED_LOWER_MERGE:(Intervention.COMPILE,),
    Outcome.CERTIFIED_DESCENT:(Intervention.COMPILE,),
    Outcome.TAIL_CLOSED:(Intervention.COMPILE,),
    Outcome.RIGID_RESIDUAL:(Intervention.CONSTRUCT,Intervention.VERIFY,Intervention.RESTRUCTURE),
    Outcome.UNKNOWN_SEARCH:(Intervention.VERIFY,Intervention.CONSTRUCT),
    Outcome.UNKNOWN_CHOICE:(Intervention.VERIFY,Intervention.CONSTRUCT),
    Outcome.UNKNOWN_EXPRESSIVITY:(Intervention.VERIFY,Intervention.CONSTRUCT),
    Outcome.CERTIFICATE_INVALID:(Intervention.REVOKE,Intervention.VERIFY),
    Outcome.IMPLEMENTATION_MISMATCH:(Intervention.RESTRUCTURE,Intervention.VERIFY,Intervention.REVOKE),
    Outcome.OUT_OF_SCOPE:(Intervention.EXPAND,Intervention.CONSTRUCT),
}


def licensed_interventions(outcome:Outcome,completeness_certificate=None,obligation_id=None):
    base=list(_BASE[outcome])
    if outcome==Outcome.UNKNOWN_EXPRESSIVITY and completeness_certificate:
        cert=completeness_certificate
        if (cert.get("complete") is True and cert.get("no_resolution") is True
                and cert.get("obligation_id")==obligation_id):
            base.append(Intervention.EXPAND)
    return tuple(base)


def select_intervention(outcome:Outcome,candidate_costs:Mapping[Intervention,int],
                        completeness_certificate=None,obligation_id=None):
    allowed=set(licensed_interventions(outcome,completeness_certificate,obligation_id))
    candidates=[(cost,intervention.value,intervention)
                for intervention,cost in candidate_costs.items() if intervention in allowed]
    if not candidates:
        return None
    return min(candidates)[2]
