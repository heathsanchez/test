"""Independent authority for Collatz QCKN capability promotion."""
from __future__ import annotations

from dataclasses import dataclass

from .adapter import CollatzAdapter, fragment_certificate, replay_fragment
from .types import Capability, VerificationEvidence, digest_payload


@dataclass(frozen=True)
class AuthoritySnapshot:
    contract_digest:str
    verifier:str

    @property
    def digest(self):
        return digest_payload({"contract_digest":self.contract_digest,"verifier":self.verifier})


class Authority:
    def __init__(self,contract_digest:str,verifier:str):
        self.snapshot=AuthoritySnapshot(contract_digest,verifier)

    @property
    def digest(self):
        return self.snapshot.digest

    def verify(self,cap:Capability,witness:dict)->VerificationEvidence:
        def result(valid,reason,evidence=None):
            return VerificationEvidence(
                capability_id=cap.semantic_id,
                payload_digest=cap.payload_digest,
                valid=valid,
                authority_digest=self.digest,
                contract_digest=self.snapshot.contract_digest,
                verifier=self.snapshot.verifier,
                reason=reason,
                evidence=evidence or {},
            )
        if cap.contract_digest!=self.snapshot.contract_digest:
            return result(False,"contract mismatch")
        try:
            cert=fragment_certificate(cap.payload["word"])
        except Exception as exc:
            return result(False,f"invalid payload: {exc}")
        expected=(cap.start_anchor,cap.end_anchor,cap.affine_a,cap.affine_b,cap.affine_d)
        actual=(cert["r0"],cert["r1"],cert["A"],cert["B"],cert["D"])
        if actual!=expected:
            return result(False,"payload/affine mismatch")
        guard={"word":[list(z) for z in cert["word"]],
               "start_anchor":cert["r0"],"end_anchor":cert["r1"]}
        if digest_payload(guard)!=cap.guard_digest:
            return result(False,"guard mismatch")
        try:
            source=int(witness["source"])
            start_m=int(witness["start_m"])
            replay=replay_fragment(cert,start_m)
        except Exception as exc:
            return result(False,f"replay failed: {exc}")
        if replay["path_min"]>=source:
            return result(False,"protected consequence not established",replay)
        # Recompute rather than trust proposal witness fields.
        return result(True,"verified",{
            "source":source,"start_m":start_m,
            "end_m":replay["end_m"],"path_min":replay["path_min"],
            "argmin":replay["argmin"],"steps":replay["steps"],
        })
