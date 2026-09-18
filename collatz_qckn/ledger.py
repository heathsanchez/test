"""Immutable causal promotion/revocation ledger for Collatz QCKN."""
from __future__ import annotations

from typing import Dict, Iterable, Tuple

from .types import Capability, LedgerEvent, VerificationEvidence


class PromotionRejected(ValueError):
    pass


class LedgerConflict(ValueError):
    pass


class CausalLedger:
    def __init__(self):
        self._events:Dict[str,LedgerEvent]={}
        self._caps:Dict[str,Dict[str,Capability]]={}
        self._promotion_events:Dict[str,Dict[str,str]]={}
        self._revoked_events:set[str]=set()

    def events(self)->Tuple[LedgerEvent,...]:
        return tuple(sorted(self._events.values(),key=lambda e:e.event_id))

    def _heads(self):
        # Sequential reference implementation: every new event observes current events.
        return tuple(sorted(self._events))

    def promote(self,cap:Capability,evidence:VerificationEvidence)->LedgerEvent:
        if not evidence.valid:
            raise PromotionRejected("authority evidence is not valid")
        if evidence.capability_id!=cap.semantic_id or evidence.payload_digest!=cap.payload_digest:
            raise PromotionRejected("evidence does not bind proposed capability")
        variants=self._caps.get(cap.semantic_id,{})
        active_variants=[
            d for d,eid in self._promotion_events.get(cap.semantic_id,{}).items()
            if eid not in self._revoked_events
        ]
        if active_variants and cap.payload_digest not in active_variants:
            raise LedgerConflict("same identity has conflicting active payload")
        body={
            "capability":cap.to_canonical(),
            "authority_digest":evidence.authority_digest,
            "verification":evidence.to_canonical(),
        }
        ev=LedgerEvent("PROMOTE",cap.semantic_id,cap.payload_digest,
                       parents=self._heads(),body=body)
        eid=ev.event_id
        self._events[eid]=ev
        self._caps.setdefault(cap.semantic_id,{})[cap.payload_digest]=cap
        self._promotion_events.setdefault(cap.semantic_id,{})[cap.payload_digest]=eid
        return ev

    def revoke(self,capability_id:str,reason:str)->LedgerEvent:
        observed=tuple(sorted(
            eid for eid in self._promotion_events.get(capability_id,{}).values()
            if eid not in self._revoked_events
        ))
        ev=LedgerEvent("REVOKE",capability_id,"",
                       parents=self._heads(),observed=observed,
                       body={"reason":reason})
        self._events[ev.event_id]=ev
        self._revoked_events.update(observed)
        return ev

    def active_capabilities(self)->Tuple[Capability,...]:
        active:Dict[str,Capability]={}
        for cid,variants in self._promotion_events.items():
            live=[(digest,eid) for digest,eid in variants.items() if eid not in self._revoked_events]
            if len(live)>1:
                raise LedgerConflict("same identity has multiple active payloads")
            if live:
                digest,_=live[0]
                active[cid]=self._caps[cid][digest]
        # Dependency fixed point: only capabilities whose dependencies are active survive.
        changed=True
        while changed:
            changed=False
            for cid,cap in list(active.items()):
                if any(dep not in active for dep in cap.dependencies):
                    del active[cid]; changed=True
        return tuple(active[cid] for cid in sorted(active))
