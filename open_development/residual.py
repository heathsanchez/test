"""Shared typed residual contract for developmental adapters.

Adapters may keep domain-specific residual payloads, but consequential failures
that license development should be representable by this fail-closed envelope.
The envelope is data, not authority: its witness still comes from the adapter's
external verifier and must remain bound to the exact assessment claim.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any, Mapping

from .runtime import canonical


@dataclass(frozen=True)
class ResidualEnvelope:
    """Portable description of a verifier-certified developmental residual."""

    residual_class: str
    diagnosis: str
    verifier_certified_witness: Any
    closure_id: str
    budget_id: str
    necessary_constraint: Any
    version_space_id: str
    evidence_strength: str
    domain_payload: Mapping[str, Any] = field(default_factory=dict)
    source: Any = None
    source_fingerprint: str | None = None
    constraint: Any = None
    schema: str = "ResidualEnvelope/v1"

    def __post_init__(self) -> None:
        required = {
            "schema": self.schema,
            "residual_class": self.residual_class,
            "diagnosis": self.diagnosis,
            "closure_id": self.closure_id,
            "budget_id": self.budget_id,
            "version_space_id": self.version_space_id,
            "evidence_strength": self.evidence_strength,
        }
        if any(not isinstance(value, str) or not value.strip()
               for value in required.values()):
            raise ValueError("residual envelope identities must be nonempty strings")
        if self.schema != "ResidualEnvelope/v1":
            raise ValueError("unknown residual envelope schema")
        if self.diagnosis not in {
            "search_failure", "selection_failure", "capability_failure",
            "representation_failure", "language_failure",
            "constitutional_failure", "infrastructure_failure", "unknown",
        }:
            raise ValueError("unknown residual diagnosis")
        if self.verifier_certified_witness is None:
            raise ValueError("residual envelope requires a verifier-certified witness")
        if self.necessary_constraint is None:
            raise ValueError("residual envelope requires a necessary constraint")
        canonical(self.to_mapping())

    def to_mapping(self) -> dict[str, Any]:
        data = asdict(self)
        data["type"] = data.pop("schema")
        data["class"] = data.pop("residual_class")
        return data

    @classmethod
    def from_mapping(cls, value: Mapping[str, Any]) -> "ResidualEnvelope":
        if value.get("type") != "ResidualEnvelope/v1":
            raise ValueError("unknown residual envelope schema")
        return cls(
            residual_class=value["class"],
            diagnosis=value["diagnosis"],
            verifier_certified_witness=value["verifier_certified_witness"],
            closure_id=value["closure_id"],
            budget_id=value["budget_id"],
            necessary_constraint=value["necessary_constraint"],
            version_space_id=value["version_space_id"],
            evidence_strength=value["evidence_strength"],
            domain_payload=value.get("domain_payload", {}),
            source=value.get("source"),
            source_fingerprint=value.get("source_fingerprint"),
            constraint=value.get("constraint"),
        )
