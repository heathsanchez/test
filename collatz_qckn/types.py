"""Immutable typed records for the Collatz QCKN V1 adapter."""
from __future__ import annotations

from dataclasses import dataclass, field, fields
from enum import Enum
import hashlib
import json
from typing import Any, Mapping, Tuple


class Outcome(str,Enum):
    CERTIFIED_LOWER_MERGE="CERTIFIED_LOWER_MERGE"
    CERTIFIED_DESCENT="CERTIFIED_DESCENT"
    TAIL_CLOSED="TAIL_CLOSED"
    RIGID_RESIDUAL="RIGID_RESIDUAL"
    UNKNOWN_SEARCH="UNKNOWN_SEARCH"
    UNKNOWN_CHOICE="UNKNOWN_CHOICE"
    UNKNOWN_EXPRESSIVITY="UNKNOWN_EXPRESSIVITY"
    CERTIFICATE_INVALID="CERTIFICATE_INVALID"
    IMPLEMENTATION_MISMATCH="IMPLEMENTATION_MISMATCH"
    OUT_OF_SCOPE="OUT_OF_SCOPE"


class Intervention(str,Enum):
    SPLIT="SPLIT"; MERGE="MERGE"; EXPAND="EXPAND"; REVOKE="REVOKE"
    CONSTRUCT="CONSTRUCT"; VERIFY="VERIFY"; RESTRUCTURE="RESTRUCTURE"; COMPILE="COMPILE"


class CapabilityKind(str,Enum):
    DIRECT_DESCENT="DIRECT_DESCENT"
    INVERSE_ODD="INVERSE_ODD"
    REVERSE_SCHEMA="REVERSE_SCHEMA"
    RIGID_FRAGMENT="RIGID_FRAGMENT"
    FORWARD_DESCENT_MACRO="FORWARD_DESCENT_MACRO"


def _plain(value: Any) -> Any:
    if isinstance(value,Enum):
        return value.value
    if hasattr(value,"to_canonical"):
        return value.to_canonical()
    if isinstance(value,Mapping):
        return {str(k):_plain(v) for k,v in value.items()}
    if isinstance(value,(tuple,list)):
        return [_plain(v) for v in value]
    return value


def canonical_json(value: Any) -> str:
    return json.dumps(_plain(value),sort_keys=True,separators=(",",":"),ensure_ascii=False)


def digest_payload(value: Any) -> str:
    return hashlib.sha256(canonical_json(value).encode()).hexdigest()


@dataclass(frozen=True)
class CostRecord:
    search_expansions:int=0
    constructions:int=0
    verifications:int=0
    wall_ms:int=0

    def to_canonical(self):
        return {f.name:getattr(self,f.name) for f in fields(self)}


@dataclass(frozen=True)
class Obligation:
    source:int
    contract_digest:str
    obligation_id:str=""
    metadata:Mapping[str,Any]=field(default_factory=dict)

    def to_canonical(self):
        return {"source":self.source,"contract_digest":self.contract_digest,
                "obligation_id":self.obligation_id,"metadata":_plain(self.metadata)}


@dataclass(frozen=True)
class Capability:
    kind:CapabilityKind
    start_anchor:int
    end_anchor:int
    affine_a:int
    affine_b:int
    affine_d:int
    guard_digest:str
    contract_digest:str
    payload:Mapping[str,Any]
    dependencies:Tuple[str,...]=()
    provenance:str=""
    cost:CostRecord=field(default_factory=CostRecord)

    @property
    def semantic_id(self)->str:
        return digest_payload({
            "kind":self.kind.value,
            "start_anchor":self.start_anchor,
            "end_anchor":self.end_anchor,
            "affine_a":self.affine_a,
            "affine_b":self.affine_b,
            "affine_d":self.affine_d,
            "guard_digest":self.guard_digest,
            "contract_digest":self.contract_digest,
        })

    def active_canonical(self):
        return {
            "semantic_id":self.semantic_id,
            "kind":self.kind.value,
            "start_anchor":self.start_anchor,
            "end_anchor":self.end_anchor,
            "affine_a":self.affine_a,
            "affine_b":self.affine_b,
            "affine_d":self.affine_d,
            "guard_digest":self.guard_digest,
            "contract_digest":self.contract_digest,
            "payload":_plain(self.payload),
            "dependencies":list(self.dependencies),
        }

    @property
    def payload_digest(self)->str:
        return digest_payload(self.active_canonical())

    def as_dict(self):
        return {f.name:getattr(self,f.name) for f in fields(self)}

    def to_canonical(self):
        return {
            "semantic_id":self.semantic_id,
            "kind":self.kind.value,
            "start_anchor":self.start_anchor,
            "end_anchor":self.end_anchor,
            "affine_a":self.affine_a,
            "affine_b":self.affine_b,
            "affine_d":self.affine_d,
            "guard_digest":self.guard_digest,
            "contract_digest":self.contract_digest,
            "payload":_plain(self.payload),
            "dependencies":list(self.dependencies),
            "provenance":self.provenance,
            "cost":self.cost.to_canonical(),
        }


@dataclass(frozen=True)
class VerificationEvidence:
    capability_id:str
    payload_digest:str
    valid:bool
    authority_digest:str
    contract_digest:str
    verifier:str
    reason:str=""
    evidence:Mapping[str,Any]=field(default_factory=dict)

    def to_canonical(self):
        return {f.name:_plain(getattr(self,f.name)) for f in fields(self)}


@dataclass(frozen=True)
class LedgerEvent:
    event_type:str
    capability_id:str
    payload_digest:str
    parents:Tuple[str,...]=()
    observed:Tuple[str,...]=()
    body:Mapping[str,Any]=field(default_factory=dict)

    @property
    def event_id(self):
        return digest_payload(self.to_canonical())

    def to_canonical(self):
        return {
            "event_type":self.event_type,
            "capability_id":self.capability_id,
            "payload_digest":self.payload_digest,
            "parents":list(self.parents),
            "observed":list(self.observed),
            "body":_plain(self.body),
        }
