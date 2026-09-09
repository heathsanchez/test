"""Persistent, verifier-gated development. No model or domain is trusted by default.

The mathematical refinement kernel lives in lean/Core.lean. This module owns
external effects, evidence provenance and the one bounded developmental loop.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass, field
from hashlib import sha256
from itertools import islice
import json
from pathlib import Path
import sqlite3
from typing import Any, Iterable, Mapping, Protocol


def canonical(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False)


def digest(value: Any) -> str:
    return sha256(canonical(value).encode()).hexdigest()


@dataclass(frozen=True)
class Obligation:
    domain: str
    target: Any
    budget: int = 32
    kind: str = "object"


@dataclass(frozen=True)
class Repair:
    kind: str  # observation, capability, policy
    name: str
    payload: Any
    scope: str
    dependencies: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if self.kind not in {"observation", "capability", "policy"}:
            raise ValueError("unknown repair kind")
        if not self.name or not self.scope or len(set(self.dependencies)) != len(self.dependencies):
            raise ValueError("invalid repair identity or dependencies")
        canonical(asdict(self))

    @property
    def id(self) -> str:
        return digest(asdict(self))


@dataclass(frozen=True)
class Evidence:
    verdict: str  # verified, refuted, unknown, obstruction
    claim: str
    verifier: str
    certificate: Any = None
    residual: Any = None
    scope: str = ""
    cost: Mapping[str, float] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if self.verdict not in {"verified", "refuted", "unknown", "obstruction"}:
            raise ValueError("unknown evidence verdict")
        canonical(asdict(self))


@dataclass(frozen=True)
class Result:
    verdict: str
    evidence: Evidence
    state_id: str
    retained: tuple[str, ...] = ()


def assessment_claim(state: Mapping[str, Any], obligation: Obligation) -> str:
    return digest({"state": state, "obligation": asdict(obligation)})


def admission_id(repair: Repair, verifier: str) -> str:
    """Identity of an admitted repair under one exact authority.

    Proposal identity remains ``repair.id`` for certificate claims. Admission
    identity additionally binds the verifier so a stale capability is never
    silently reused, while the same repair can be explicitly requalified.
    """
    return digest({"repair": repair.id, "verifier": verifier})


class Adapter(Protocol):
    """Domain authority. A proposed repair is not a certificate."""
    name: str
    verifier_id: str

    def assess(self, state: Mapping[str, Any], obligation: Obligation) -> Evidence: ...
    def propose(self, state: Mapping[str, Any], obligation: Obligation,
                residual: Any) -> Iterable[Repair]: ...
    def verify(self, state: Mapping[str, Any], obligation: Obligation,
               repair: Repair) -> Evidence: ...
    def attach(self, state: Mapping[str, Any], repair: Repair,
               evidence: Evidence) -> Mapping[str, Any]: ...


class EvidenceStore:
    """Append-only, hash-chained SQLite ledger; the active crystal is a projection.

    Hashes detect accidental alteration, not a malicious rewrite of the whole DB.
    External attestation is required for a tamper-evident authority boundary.
    """
    def __init__(self, path: str | Path):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.db = sqlite3.connect(self.path)
        self.db.execute("PRAGMA busy_timeout=5000")
        self.db.execute("CREATE TABLE IF NOT EXISTS events (seq INTEGER PRIMARY KEY, prev TEXT NOT NULL, digest TEXT NOT NULL, payload TEXT NOT NULL)")
        self.db.commit()
        self.events()  # fail closed on a damaged history

    def events(self) -> list[dict[str, Any]]:
        previous = "0" * 64
        out = []
        for seq, prev, h, raw in self.db.execute("SELECT seq, prev, digest, payload FROM events ORDER BY seq"):
            event = json.loads(raw)
            if prev != previous or h != digest({"prev": prev, "event": event}):
                raise ValueError(f"evidence ledger corrupted at event {seq}")
            out.append(event)
            previous = h
        return out

    def append(self, event: Mapping[str, Any]) -> str:
        # Validate the entire chain before extending it; never repair it silently.
        self.events()
        raw = canonical(dict(event))
        with self.db:
            row = self.db.execute("SELECT digest FROM events ORDER BY seq DESC LIMIT 1").fetchone()
            previous = row[0] if row else "0" * 64
            h = digest({"prev": previous, "event": json.loads(raw)})
            self.db.execute("INSERT INTO events(prev,digest,payload) VALUES(?,?,?)", (previous, h, raw))
        return h

    def state(self) -> dict[str, Any]:
        active: dict[str, dict[str, Any]] = {}
        for event in self.events():
            if event["type"] == "admit":
                record = event["record"]
                active[record["id"]] = record
            elif event["type"] == "revoke":
                for rid in event["ids"]:
                    active.pop(rid, None)
        observations = sorted(rid for rid, rec in active.items()
                              if rec["repair"]["kind"] == "observation")
        policies: dict[str, str] = {}
        for rid, rec in active.items():
            if rec["repair"]["kind"] == "policy":
                policies[rec["repair"]["scope"]] = rid
        return {"capabilities": active, "observations": observations, "policies": policies}

    def revoke(self, rid: str, reason: str) -> tuple[str, ...]:
        active = self.state()["capabilities"]
        if rid not in active:
            raise KeyError(rid)
        removed = {rid}
        while True:
            new = {key for key, rec in active.items()
                   if set(rec["repair"]["dependencies"]) & removed}
            if new <= removed:
                break
            removed |= new
        self.append({"type": "revoke", "ids": sorted(removed), "reason": reason})
        return tuple(sorted(removed))

    def close(self) -> None:
        self.db.close()


class Developer:
    """One transition for object, constructor and policy obligations."""
    def __init__(self, store: EvidenceStore, adapter: Adapter):
        self.store, self.adapter = store, adapter

    def _bound(self, evidence: Evidence, claim: str) -> bool:
        return (evidence.claim == claim and evidence.verifier == self.adapter.verifier_id
                and evidence.scope == self.adapter.name and evidence.certificate is not None)

    def _check(self, evidence: Evidence, claim: str) -> bool:
        return evidence.verdict == "verified" and self._bound(evidence, claim)

    def _admit(self, repair: Repair, evidence: Evidence) -> str:
        state = self.store.state()
        missing = set(repair.dependencies) - set(state["capabilities"])
        if missing:
            raise ValueError(f"missing dependencies: {sorted(missing)}")
        # The adapter must preserve its declared semantics. Only the checked
        # record is admitted; arbitrary proposals never become executable.
        attachment = dict(self.adapter.attach(state, repair, evidence))
        canonical(attachment)
        rid = admission_id(repair, evidence.verifier)
        existing = state["capabilities"].get(rid)
        if existing is not None:
            return rid
        self.store.append({"type": "admit", "record": {
            "id": rid, "repair": asdict(repair), "evidence": asdict(evidence),
            "attachment": attachment, "status": "verified", "level": "K1"}})
        return rid

    def run(self, obligation: Obligation) -> Result:
        if obligation.domain != self.adapter.name:
            raise ValueError("domain mismatch")
        if obligation.budget < 0:
            raise ValueError("negative budget")
        retained: list[str] = []
        attempted: set[str] = set()
        remaining = obligation.budget
        last = Evidence("unknown", "not attempted", self.adapter.verifier_id)
        while True:
            state = self.store.state()
            claim = assessment_claim(state, obligation)
            last = self.adapter.assess(state, obligation)
            self.store.append({"type": "assessment", "obligation": asdict(obligation),
                               "state_id": digest(state), "evidence": asdict(last)})
            if not self._bound(last, claim):
                # A bare failure, unbound certificate, or wrong verifier is not evidence.
                return Result("unknown", Evidence("unknown", claim, self.adapter.verifier_id),
                              digest(state), tuple(retained))
            if last.verdict in ("verified", "refuted", "obstruction"):
                return Result(last.verdict, last, digest(state), tuple(retained))
            if last.verdict != "unknown" or last.residual is None or remaining == 0:
                break
            progressed = False
            for repair in islice(self.adapter.propose(state, obligation, last.residual), remaining):
                remaining -= 1
                rid = admission_id(repair, self.adapter.verifier_id)
                if repair.id in attempted or rid in state["capabilities"]:
                    continue
                attempted.add(repair.id)
                if repair.scope != obligation.domain:
                    continue
                if set(repair.dependencies) - set(state["capabilities"]):
                    continue
                first = self.adapter.verify(state, obligation, repair)
                self.store.append({"type": "candidate", "repair": asdict(repair),
                                   "evidence": asdict(first)})
                if not self._check(first, repair.id):
                    continue
                second = self.adapter.verify(state, obligation, repair)
                self.store.append({"type": "replay", "repair_id": repair.id,
                                   "evidence": asdict(second)})
                if not self._check(second, repair.id) or second.certificate != first.certificate:
                    continue
                rid = self._admit(repair, second)
                retained.append(rid)
                progressed = True
                break
            if not progressed:
                break
        return Result("unknown", last, digest(self.store.state()), tuple(retained))
