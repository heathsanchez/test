"""Canonical active Collatz QCKN memory and exact restart."""
from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
from typing import Tuple

from .ledger import CausalLedger
from .types import Capability, CapabilityKind, CostRecord, canonical_json, digest_payload


class CompiledPresentError(ValueError):
    pass


def _cap_from_active(d:dict)->Capability:
    try:
        cap=Capability(
            kind=CapabilityKind(d["kind"]),
            start_anchor=int(d["start_anchor"]),end_anchor=int(d["end_anchor"]),
            affine_a=int(d["affine_a"]),affine_b=int(d["affine_b"]),affine_d=int(d["affine_d"]),
            guard_digest=str(d["guard_digest"]),contract_digest=str(d["contract_digest"]),
            payload=d["payload"],dependencies=tuple(d.get("dependencies",())),
            provenance="",cost=CostRecord(),
        )
    except Exception as exc:
        raise CompiledPresentError(f"invalid capability: {exc}") from exc
    if cap.semantic_id!=d.get("semantic_id"):
        raise CompiledPresentError("capability semantic identity mismatch")
    return cap


@dataclass(frozen=True)
class CompiledPresent:
    capabilities:Tuple[Capability,...]
    contract_digest:str
    authority_digests:Tuple[str,...]
    schema:str="COLLATZ_QCKN_COMPILED_PRESENT_V1"

    @classmethod
    def compile(cls,ledger:CausalLedger):
        caps=ledger.active_capabilities()
        contracts={c.contract_digest for c in caps}
        if len(contracts)>1:
            raise CompiledPresentError("mixed active contracts")
        contract=next(iter(contracts),"")
        active_keys={(c.semantic_id,c.payload_digest) for c in caps}
        auth=set()
        for ev in ledger.events():
            if ev.event_type=="PROMOTE" and (ev.capability_id,ev.payload_digest) in active_keys:
                d=ev.body.get("authority_digest")
                if d:auth.add(str(d))
        return cls(tuple(sorted(caps,key=lambda c:c.semantic_id)),contract,tuple(sorted(auth)))

    def _body(self):
        return {
            "schema":self.schema,
            "contract_digest":self.contract_digest,
            "authority_digests":list(self.authority_digests),
            "capabilities":[
                {"payload_digest":c.payload_digest,"capability":c.active_canonical()}
                for c in sorted(self.capabilities,key=lambda x:x.semantic_id)
            ],
        }

    def to_text(self)->str:
        return canonical_json(self._body())

    @property
    def digest(self)->str:
        return hashlib.sha256(self.to_text().encode()).hexdigest()

    @classmethod
    def from_text(cls,text:str):
        try:
            d=json.loads(text)
        except Exception as exc:
            raise CompiledPresentError(f"invalid JSON: {exc}") from exc
        if d.get("schema")!="COLLATZ_QCKN_COMPILED_PRESENT_V1":
            raise CompiledPresentError("schema mismatch")
        caps=[]
        seen={}
        for row in d.get("capabilities",[]):
            cap=_cap_from_active(row["capability"])
            if cap.payload_digest!=row.get("payload_digest"):
                raise CompiledPresentError("capability payload digest mismatch")
            if cap.semantic_id in seen and seen[cap.semantic_id]!=cap.payload_digest:
                raise CompiledPresentError("same identity conflicting payload")
            seen[cap.semantic_id]=cap.payload_digest
            caps.append(cap)
        ids={c.semantic_id for c in caps}
        for cap in caps:
            if any(dep not in ids for dep in cap.dependencies):
                raise CompiledPresentError("missing active dependency")
        contracts={c.contract_digest for c in caps}
        contract=str(d.get("contract_digest",""))
        if contracts and contracts!={contract}:
            raise CompiledPresentError("contract mismatch")
        obj=cls(tuple(sorted(caps,key=lambda c:c.semantic_id)),contract,
                tuple(sorted(str(x) for x in d.get("authority_digests",[]))))
        if obj.to_text()!=canonical_json(d):
            raise CompiledPresentError("non-canonical or unsupported active payload")
        return obj
