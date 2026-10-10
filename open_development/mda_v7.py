"""MDA v7: one proof-gated minimal-continuation transition over the existing core.

Experimental implementation, not a new constitutional controller or a claim
of global minimality. The old Developer, Adapter, Repair, EvidenceStore and
certificates are the only admission machinery. Candidate plans are explored
on disposable, exact virtual states and admitted ONLY after independent replay.

A failure to find a plan is UNKNOWN_SEARCH, never a proof of expressivity
obstruction. If incomparable adequate plans survive, the decision is
UNKNOWN_CHOICE and none is arbitrarily admitted. Requalification may use a
new role with an existing certified executable ancestor.
"""
from __future__ import annotations

from collections import deque
from copy import deepcopy
from dataclasses import asdict, dataclass
from itertools import islice
from typing import Any, Mapping, Sequence

from .runtime import (Developer, Evidence, EvidenceStore, Obligation, Repair,
                      admission_id, assessment_claim, canonical, digest)


@dataclass(frozen=True)
class ContinuationDecision:
    outcome: str     # IDENTITY | COMMIT | UNKNOWN_SEARCH | UNKNOWN_CHOICE | REFUTED | OBSTRUCTION | UNKNOWN_AUTHORITY
    verdict: str     # verified | unknown | refuted | obstruction
    state_id: str
    retained: tuple[str, ...] = ()
    frontier: tuple[tuple[str, ...], ...] = ()
    proposal_checks: int = 0
    verifier_checks: int = 0
    replay_checks: int = 0
    protected_checks: int = 0
    final_execution_checks: int = 0
    source_residual: Any = None
    no_global_minimality_claim: bool = True


@dataclass
class _Node:
    state: dict[str, Any]
    path: tuple[tuple[Repair, Evidence], ...]
    witnesses: tuple[str, ...]


def _project(state: Mapping[str, Any], repair: Repair, proof: Evidence,
             adapter: Any) -> dict[str, Any]:
    """Virtual, proof-bound projection. Not an admission to a persistent ledger."""
    if proof.verdict != "verified" or proof.claim != repair.id or proof.verifier != adapter.verifier_id:
        raise ValueError("unbound virtual proof")
    if proof.certificate is None or proof.scope != adapter.name:
        raise ValueError("missing exact proof authority/scope")
    if repair.scope != adapter.name:
        raise ValueError("repair outside adapter scope")
    for parent in repair.dependencies:
        if parent not in state["capabilities"]:
            raise ValueError("missing executable dependency")
    attachment = dict(adapter.attach(state, repair, proof))
    canonical(attachment)
    projected = deepcopy(state)
    rid = admission_id(repair, proof.verifier)
    if rid in projected["capabilities"]:
        raise ValueError("duplicate projected admission")
    projected["capabilities"][rid] = {
        "id": rid, "repair": asdict(repair), "evidence": asdict(proof),
        "attachment": attachment, "status": "verified", "level": "K1"}
    if repair.kind == "observation":
        projected["observations"] = sorted(set(projected["observations"]) | {rid})
    if repair.kind == "policy":
        projected["policies"][repair.scope] = rid
    return projected


def _cost(path: tuple[tuple[Repair, Evidence], ...]) -> tuple[int, int, int]:
    """Declared bounded resource preorder: admission count, bytes, verifier replays."""
    return (len(path),
            sum(len(canonical(asdict(repair)).encode("utf-8")) for repair, _ in path),
            2 * len(path))


def _dominates(a: tuple[int, ...], b: tuple[int, ...]) -> bool:
    return all(x <= y for x, y in zip(a, b)) and any(x < y for x, y in zip(a, b))


class MinimalContinuation(Developer):
    """Single bounded MDA transition reusing the existing verifier and ledger.

    Full prospective semantic value is NOT reducible to the provisional cost
    order here. We explicitly preserve all undominated alternatives.
    """

    def __init__(self, store: EvidenceStore, adapter: Any):
        super().__init__(store, adapter)

    def _assess(self, state: Mapping[str, Any],
                obligation: Obligation) -> Evidence | None:
        claim = assessment_claim(state, obligation)
        r = self.adapter.assess(state, obligation)
        return r if self._bound(r, claim) else None

    def run_minimal(self, obligation: Obligation, *,
                    protected: Sequence[Obligation] = (),
                    max_depth: int = 4,
                    max_nodes: int = 64) -> ContinuationDecision:
        if obligation.domain != self.adapter.name:
            raise ValueError("domain mismatch")
        if obligation.budget < 0 or max_depth < 0 or max_nodes < 1:
            raise ValueError("invalid declared exploration boundary")
        original = self.store.state()
        before = self._assess(original, obligation)
        initial_id = digest(original)
        if before is None:
            return ContinuationDecision("UNKNOWN_AUTHORITY", "unknown", initial_id)
        self.store.append({"type": "mda_assess", "state_id": initial_id,
                           "obligation": asdict(obligation),
                           "evidence": asdict(before)})
        if before.verdict in ("verified", "refuted", "obstruction"):
            outcome = {"verified": "IDENTITY", "refuted": "REFUTED",
                       "obstruction": "OBSTRUCTION"}[before.verdict]
            return ContinuationDecision(outcome, before.verdict, initial_id,
                                        final_execution_checks=1,
                                        source_residual=before.residual)
        if before.verdict != "unknown" or before.residual is None or obligation.budget == 0:
            return ContinuationDecision("UNKNOWN_SEARCH", "unknown", initial_id,
                                        final_execution_checks=1,
                                        source_residual=before.residual)

        # Protect only independently warranted prior consequences. Failure to
        # bind a protection to current authority fails the entire transition.
        checks = 0
        protect_baseline = []
        for old in protected:
            if old.domain != obligation.domain:
                raise ValueError("protected obligation from another domain")
            observation = self._assess(original, old)
            checks += 1
            if observation is None:
                return ContinuationDecision("UNKNOWN_AUTHORITY", "unknown", initial_id,
                                            protected_checks=checks,
                                            source_residual=before.residual)
            if observation.verdict == "verified":
                protect_baseline.append(old)
        frontier = deque([_Node(deepcopy(original), (), ())])
        successes: list[_Node] = []
        proposal_checks = verifier_checks = replay_checks = 0
        assess_checks = 1
        exhausted = False
        expanded_nodes = 0
        known = {initial_id}

        while frontier:
            if expanded_nodes >= max_nodes:
                exhausted = True
                break
            node = frontier.popleft()
            expanded_nodes += 1
            if node.path:
                current = self._assess(node.state, obligation)
                assess_checks += 1
                if current is None:
                    exhausted = True
                    continue
            else:
                current = before
            if current.verdict == "verified":
                successes.append(node)
                continue
            if current.verdict != "unknown" or current.residual is None:
                continue
            if len(node.path) >= max_depth:
                exhausted = True
                continue
            # A common finite proof budget; reaching its limit cannot certify
            # exhaustiveness of a larger class or justify language expansion.
            remaining = obligation.budget - proposal_checks
            if remaining <= 0:
                exhausted = True
                break
            proposals = list(islice(self.adapter.propose(
                node.state, obligation, current.residual), remaining + 1))
            if len(proposals) > remaining:
                exhausted = True
            for repair in proposals[:remaining]:
                proposal_checks += 1
                rid = admission_id(repair, self.adapter.verifier_id)
                if (repair.scope != obligation.domain or
                        rid in node.state["capabilities"] or
                        any(repair.id == prev.id for prev, _ in node.path) or
                        any(dep not in node.state["capabilities"]
                            for dep in repair.dependencies)):
                    continue
                first = self.adapter.verify(node.state, obligation, repair)
                verifier_checks += 1
                if not self._check(first, repair.id):
                    continue
                second = self.adapter.verify(node.state, obligation, repair)
                verifier_checks += 1
                replay_checks += 1
                if not self._check(second, repair.id) or first.certificate != second.certificate:
                    continue
                try:
                    changed = _project(node.state, repair, second, self.adapter)
                except (ValueError, KeyError, TypeError):
                    continue
                okay = True
                for old in protect_baseline:
                    trial = self._assess(changed, old)
                    checks += 1
                    if trial is None or trial.verdict != "verified":
                        okay = False
                        break
                if not okay:
                    continue
                fingerprint = digest(changed)
                if fingerprint in known:
                    continue
                known.add(fingerprint)
                frontier.append(_Node(changed, node.path + ((repair, second),),
                                      node.witnesses + (rid,)))

        # No successes, or incomplete rival exploration: don't turn an
        # underpowered search into certified inadequacy/minimality.
        if not successes:
            return ContinuationDecision("UNKNOWN_SEARCH", "unknown", initial_id,
                                        proposal_checks=proposal_checks,
                                        verifier_checks=verifier_checks,
                                        replay_checks=replay_checks,
                                        protected_checks=checks,
                                        final_execution_checks=assess_checks,
                                        source_residual=before.residual)

        unique: dict[tuple[str, ...], _Node] = {}
        for node in successes:
            unique[node.witnesses] = node
        nodes = list(unique.values())
        least = [x for x in nodes if not any(
            _dominates(_cost(y.path), _cost(x.path)) for y in nodes if y is not x)]
        possible = tuple(sorted(x.witnesses for x in least))

        # If another feasible plan remains unexplored, report that uncertainty
        # instead of claiming a minimum of the whole declared search class.
        if exhausted:
            return ContinuationDecision("UNKNOWN_SEARCH", "unknown", initial_id,
                                        frontier=possible,
                                        proposal_checks=proposal_checks,
                                        verifier_checks=verifier_checks,
                                        replay_checks=replay_checks,
                                        protected_checks=checks,
                                        final_execution_checks=assess_checks,
                                        source_residual=before.residual)
        if len(least) != 1:
            return ContinuationDecision("UNKNOWN_CHOICE", "unknown", initial_id,
                                        frontier=possible,
                                        proposal_checks=proposal_checks,
                                        verifier_checks=verifier_checks,
                                        replay_checks=replay_checks,
                                        protected_checks=checks,
                                        final_execution_checks=assess_checks,
                                        source_residual=before.residual)

        chosen = least[0]
        # Final persistent admission is performed by the SAME Developer._admit
        # used throughout Open Development Core, not by a duplicate ledger.
        retained = []
        for repair, evidence in chosen.path:
            rid = self._admit(repair, evidence)
            assert rid == admission_id(repair, evidence.verifier)
            retained.append(rid)
        actual = self.store.state()
        final = self._assess(actual, obligation)
        assess_checks += 1
        okay = final is not None and final.verdict == "verified"
        for old in protect_baseline:
            trial = self._assess(actual, old)
            checks += 1
            if trial is None or trial.verdict != "verified":
                okay = False
        if not okay:
            # Preserve evidence; revoke ONLY this intervention's causal chain.
            for rid in retained:
                if rid in self.store.state()["capabilities"]:
                    self.store.revoke(rid, "MDA V7 post-admission replay failed")
            return ContinuationDecision("UNKNOWN_AUTHORITY", "unknown",
                                        digest(self.store.state()),
                                        proposal_checks=proposal_checks,
                                        verifier_checks=verifier_checks,
                                        replay_checks=replay_checks,
                                        protected_checks=checks,
                                        final_execution_checks=assess_checks,
                                        source_residual=before.residual)
        self.store.append({"type": "mda_warranted_continuation",
                           "before_state": initial_id,
                           "after_state": digest(actual),
                           "retained": retained,
                           "frontier_checked": list(possible),
                           "cost": _cost(chosen.path),
                           "source_residual": before.residual,
                           "relative_to": {"candidate_budget": obligation.budget,
                                           "max_depth": max_depth,
                                           "max_nodes": max_nodes}})
        return ContinuationDecision("COMMIT", "verified", digest(actual),
                                    tuple(retained), possible, proposal_checks,
                                    verifier_checks, replay_checks, checks,
                                    assess_checks, before.residual)
