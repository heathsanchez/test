"""Prospective bounded exaptation / adjacent-possible qualification.

A proof-composition capability learned for nonnegativity is frozen first.  A
separate later workload is then loaded.  The new adapter may only use the
source capability after an explicit, verifier-checked role requalification;
that role can then support a dependent executable program.  The experiment is
internally administered and finite.  It does not claim unrestricted novelty or
settle whether the newly reachable use was metaphysically discovered or made.
"""
from __future__ import annotations

from copy import deepcopy
from fractions import Fraction as Q
from hashlib import sha256
from math import isqrt
from pathlib import Path
from typing import Any, Mapping
import json
import tempfile

from .composition import ProofCompositionAdapter, check_program, program_shape
from .proof import mul, norm
from .runtime import (CapabilityContract, Developer, Evidence, EvidenceStore,
                      IRContract, Obligation, Repair, assessment_claim, digest)


def _json_poly(poly: Mapping[Any, Any]) -> dict[str, str]:
    return {str(k): str(v) for k, v in sorted(norm(poly).items())}


def _problem(target: Mapping[str, Any]):
    poly = norm(target["polynomial"])
    raw = target["domain"]
    domain = (str(raw[0]), *(Q(x) for x in raw[1:]))
    if domain[0] != "interval" or len(domain) != 3:
        raise ValueError("exaptation workload requires a closed rational interval")
    return poly, domain


def _quotient_x(poly: Mapping[Any, Any]):
    p = norm(poly)
    if not p or p.get(0, Q(0)) != 0:
        return None
    return norm({power - 1: coefficient for power, coefficient in p.items() if power > 0})


def _affine_factor_observation(program: Mapping[str, Any], poly, domain):
    if program.get("kind") != "product" or len(program.get("children", ())) != 2:
        return None
    children = program["children"]
    if any(child.get("kind") != "affine" for child in children):
        return None
    lower, upper = Q(domain[1]), Q(domain[2])
    endpoint_safe = all(
        Q(child["a"]) * lower + Q(child["b"]) >= 0
        and Q(child["a"]) * upper + Q(child["b"]) >= 0
        for child in children)
    if not endpoint_safe or not check_program(poly, domain, program):
        return None
    return {
        "replay": _json_poly(poly),
        "shape": "product(affine,affine)",
        "factor_count": 2,
        "endpoint_safe": True,
    }


def direct_vieta_factor_program(poly: Mapping[Any, Any], domain):
    """Source-distinct control realization; never offered to the developer."""
    p = norm(poly)
    if domain[0] != "interval" or not p or max(p) != 2:
        return None
    a, b, c = p.get(2, Q(0)), p.get(1, Q(0)), p.get(0, Q(0))
    if a == 0:
        return None
    discriminant = b * b - 4 * a * c
    if discriminant < 0:
        return None
    n, d = isqrt(discriminant.numerator), isqrt(discriminant.denominator)
    if n * n != discriminant.numerator or d * d != discriminant.denominator:
        return None
    root = Q(n, d)
    roots = [(-b + root) / (2 * a), (-b - root) / (2 * a)]
    lower, upper = Q(domain[1]), Q(domain[2])
    for r1, r2 in (roots, list(reversed(roots))):
        first = {1: Q(1), 0: -r1}
        second = {1: a, 0: -a * r2}
        for sign in (Q(1), Q(-1)):
            pair = [{k: sign * v for k, v in factor.items()}
                    for factor in (first, second)]
            if mul(pair[0], pair[1]) != p:
                continue
            children = [{"kind": "affine", "a": str(f[1]), "b": str(f[0])}
                        for f in pair]
            if all(Q(f["a"]) * lower + Q(f["b"]) >= 0
                   and Q(f["a"]) * upper + Q(f["b"]) >= 0 for f in children):
                program = {"kind": "product", "children": children}
                return program if check_program(p, domain, program) else None
    return None


def _source_fingerprint(record: Mapping[str, Any]) -> str:
    return digest({
        "id": record["id"],
        "repair": record["repair"],
        "verifier": record["evidence"]["verifier"],
        "attachment": record["attachment"],
        "status": record["status"],
    })


class ExaptationAdapter:
    """Requalify a learned proof program for a new factor-interface role."""
    name = "proof-exaptation"
    contract = IRContract(
        "CubicPolynomialNonnegativityObligation", "RequalifiedFactorProgram",
        "VerifiedNonnegativity|Unknown", "typed requalification plus exact replay",
        "replayed nested program equals obligation polynomial",
        "ExaptationReplayCertificate")
    role_contract = CapabilityContract(
        "QuadraticPolynomial×Interval", "AffineFactorPair",
        "source execution yields two endpoint-safe affine factors whose product is the input",
        "FactorRoleCertificate")
    lift_contract = CapabilityContract(
        "PolynomialDivisibleByX×Interval", "CertificateProgram",
        "multiply x by a requalified affine-factor program and replay exactly",
        "ExaptationReplayCertificate")

    def __init__(self):
        self.source_adapter = ProofCompositionAdapter()
        self.verifier_id = "prospective-exaptation-v1:" + digest({
            "checker_source": sha256(Path(__file__).read_bytes()).hexdigest(),
            "source_verifier": self.source_adapter.verifier_id,
            "ir_contract": self.contract.id})
        self.metrics = {"construction": 0, "verification": 0,
                        "activation": 0, "execution": 0}

    def _source(self, state: Mapping[str, Any]):
        matches = []
        for rid, record in state["capabilities"].items():
            repair = record["repair"]
            if (repair["scope"] == self.source_adapter.name
                    and repair["kind"] == "capability"
                    and repair["payload"].get("body", {}).get("op") == "fit-affine"
                    and repair["payload"].get("program_shape") == "product(affine,affine)"
                    and record["evidence"]["verifier"] == self.source_adapter.verifier_id):
                matches.append(rid)
        return sorted(matches)[0] if matches else None

    def _role(self, state: Mapping[str, Any], source: str):
        for rid, record in state["capabilities"].items():
            repair = record["repair"]
            if (repair["scope"] == self.name
                    and repair["payload"].get("role") == "affine-factor-pair"
                    and repair["dependencies"] == [source]
                    and record["evidence"]["verifier"] == self.verifier_id):
                return rid
        return None

    def _programs(self, state: Mapping[str, Any]):
        return {record["repair"]["payload"]["program_shape"]: rid
                for rid, record in state["capabilities"].items()
                if record["repair"]["scope"] == self.name
                and record["repair"]["payload"].get("body", {}).get("op") == "lift-x-factor-role"
                and "program_shape" in record["repair"]["payload"]
                and record["evidence"]["verifier"] == self.verifier_id}

    def _problem(self, obligation: Obligation):
        return _problem(obligation.target)

    def _source_program(self, state, source, poly, domain, trace):
        record = state["capabilities"].get(source)
        if record is None:
            return None
        self.metrics["execution"] += 1
        program = self.source_adapter.execute(state, source, poly, domain, trace)
        if program is None or _affine_factor_observation(program, poly, domain) is None:
            return None
        return program

    def execute_role(self, state, rid, poly, domain, trace=None):
        trace = [] if trace is None else trace
        record = state["capabilities"].get(rid)
        if record is None or record["evidence"]["verifier"] != self.verifier_id:
            return None
        repair = record["repair"]
        body = repair["payload"].get("body", {})
        source = body.get("callee")
        if (body.get("op") != "requalify-affine-factors"
                or repair["dependencies"] != [source]
                or source not in state["capabilities"]
                or repair["payload"].get("source_fingerprint")
                   != _source_fingerprint(state["capabilities"][source])):
            return None
        self.metrics["execution"] += 1
        trace.append(rid)
        program = self._source_program(state, source, poly, domain, trace)
        return None if program is None else program["children"]

    def execute_program(self, state, rid, poly, domain, trace=None):
        trace = [] if trace is None else trace
        record = state["capabilities"].get(rid)
        if record is None or record["evidence"]["verifier"] != self.verifier_id:
            return None
        repair = record["repair"]
        body = repair["payload"].get("body", {})
        role = body.get("callee")
        if body.get("op") != "lift-x-factor-role" or repair["dependencies"] != [role]:
            return None
        quotient = _quotient_x(poly)
        if quotient is None:
            return None
        self.metrics["execution"] += 1
        trace.append(rid)
        factors = self.execute_role(state, role, quotient, domain, trace)
        if factors is None:
            return None
        factor_program = {"kind": "product", "children": factors}
        program = {"kind": "product", "children": [
            {"kind": "monomial", "power": 1, "coefficient": "1"}, factor_program]}
        if (program_shape(program) != repair["payload"].get("program_shape")
                or not check_program(poly, domain, program)):
            return None
        return program

    def _candidate_program(self, state, role, poly, domain):
        quotient = _quotient_x(poly)
        if quotient is None:
            return None, []
        trace = []
        factors = self.execute_role(state, role, quotient, domain, trace)
        if factors is None:
            return None, trace
        program = {"kind": "product", "children": [
            {"kind": "monomial", "power": 1, "coefficient": "1"},
            {"kind": "product", "children": factors}]}
        return (program, trace) if check_program(poly, domain, program) else (None, trace)

    def assess(self, state: Mapping[str, Any], obligation: Obligation) -> Evidence:
        claim = assessment_claim(state, obligation)
        poly, domain = self._problem(obligation)
        source = self._source(state)
        if source is None:
            return Evidence("unknown", claim, self.verifier_id,
                            {"active_source": False, "history_is_not_execution": True},
                            {"class": "MISSING_ACTIVE_SOURCE"}, self.name)
        role = self._role(state, source)
        if role is None:
            record = state["capabilities"][source]
            constraint = {
                "input": "QuadraticPolynomial×Interval",
                "output": "AffineFactorPair",
                "must": ["execute the retained source body",
                         "return exactly two affine factors",
                         "factor product replays the quotient exactly",
                         "both factors are nonnegative at interval endpoints"],
            }
            return Evidence("unknown", claim, self.verifier_id,
                            {"source": source, "source_fingerprint": _source_fingerprint(record),
                             "source_original_scope": record["repair"]["scope"]},
                            {"class": "ROLE_REQUALIFICATION_REQUIRED", "source": source,
                             "source_fingerprint": _source_fingerprint(record),
                             "constraint": constraint}, self.name)
        programs = self._programs(state)
        for shape, rid in programs.items():
            trace = []
            program = self.execute_program(state, rid, poly, domain, trace)
            if program is not None:
                return Evidence("verified", claim, self.verifier_id,
                                {"source": source, "role": role, "program": program,
                                 "program_shape": shape, "execution_trace": trace,
                                 "semantics": "nested replay equals obligation polynomial"},
                                scope=self.name)
        program, trace = self._candidate_program(state, role, poly, domain)
        if program is None:
            return Evidence("unknown", claim, self.verifier_id,
                            {"source": source, "role": role, "execution_trace": trace},
                            {"class": "CURRENT_REQUALIFIED_ROLE_INADEQUATE"}, self.name)
        shape = program_shape(program)
        return Evidence("unknown", claim, self.verifier_id,
                        {"source": source, "role": role, "candidate_program": program,
                         "execution_trace": trace},
                        {"class": "EXAPTATION_PROGRAM_CONSTRUCTED", "role": role,
                         "program_shape": shape,
                         "body": {"op": "lift-x-factor-role", "callee": role}}, self.name)

    def propose(self, state: Mapping[str, Any], obligation: Obligation, residual: Any):
        if residual.get("class") == "ROLE_REQUALIFICATION_REQUIRED":
            self.metrics["construction"] += 1
            source = residual["source"]
            yield Repair(
                "capability", "affine-factor-role",
                {"role": "affine-factor-pair",
                 "source_fingerprint": residual["source_fingerprint"],
                 "body": {"op": "requalify-affine-factors", "callee": source}},
                self.name, (source,), self.role_contract)
        elif residual.get("class") == "EXAPTATION_PROGRAM_CONSTRUCTED":
            self.metrics["construction"] += 1
            role = residual["role"]
            yield Repair(
                "capability", residual["program_shape"],
                {"program_shape": residual["program_shape"], "body": residual["body"]},
                self.name, (role,), self.lift_contract)

    def verify(self, state: Mapping[str, Any], obligation: Obligation, repair: Repair) -> Evidence:
        self.metrics["verification"] += 1
        poly, domain = self._problem(obligation)
        source = self._source(state)
        if source is None:
            return Evidence("refuted", repair.id, self.verifier_id,
                            {"accepted": False, "reason": "missing source"}, scope=self.name)
        body = repair.payload.get("body", {}) if isinstance(repair.payload, Mapping) else {}
        if repair.payload.get("role") == "affine-factor-pair":
            quotient = _quotient_x(poly)
            expected_fingerprint = _source_fingerprint(state["capabilities"][source])
            trace = []
            source_program = None if quotient is None else self._source_program(
                state, source, quotient, domain, trace)
            valid = (repair.kind == "capability" and repair.contract == self.role_contract
                     and repair.dependencies == (source,)
                     and repair.payload.get("source_fingerprint") == expected_fingerprint
                     and body == {"op": "requalify-affine-factors", "callee": source}
                     and source_program is not None
                     and _affine_factor_observation(source_program, quotient, domain) is not None)
            if not valid:
                return Evidence("refuted", repair.id, self.verifier_id,
                                {"accepted": False, "execution_trace": trace}, scope=self.name)
            return Evidence("verified", repair.id, self.verifier_id,
                            {"accepted": True, "execution_trace": trace,
                             "source_fingerprint": expected_fingerprint,
                             "semantics": "source body realizes endpoint-safe affine factor interface"},
                            scope=self.name)
        if "program_shape" in repair.payload:
            role = self._role(state, source)
            program, trace = (None, []) if role is None else self._candidate_program(
                state, role, poly, domain)
            expected_body = {"op": "lift-x-factor-role", "callee": role}
            valid = (repair.kind == "capability" and repair.contract == self.lift_contract
                     and role is not None and repair.dependencies == (role,)
                     and body == expected_body and program is not None
                     and repair.payload.get("program_shape") == program_shape(program))
            if not valid:
                return Evidence("refuted", repair.id, self.verifier_id,
                                {"accepted": False, "execution_trace": trace}, scope=self.name)
            return Evidence("verified", repair.id, self.verifier_id,
                            {"accepted": True, "execution_trace": trace,
                             "witness_program": program,
                             "semantics": "x times requalified factor program replays exactly"},
                            scope=self.name)
        return Evidence("refuted", repair.id, self.verifier_id,
                        {"accepted": False, "reason": "unknown repair"}, scope=self.name)

    def attach(self, state: Mapping[str, Any], repair: Repair, evidence: Evidence):
        if (evidence.verdict != "verified" or evidence.claim != repair.id
                or not evidence.certificate.get("accepted")):
            raise ValueError("unverified exaptation repair")
        self.metrics["activation"] += 1
        if repair.payload.get("role") == "affine-factor-pair":
            return {"role": "affine-factor-pair", "executable": True,
                    "source": repair.dependencies[0],
                    "semantic_contract": evidence.certificate["semantics"]}
        return {"program_shape": repair.payload["program_shape"], "executable": True,
                "semantic_contract": evidence.certificate["semantics"]}


def _assert_workload_has_no_answer(value: Any):
    forbidden = {"answer", "expected", "certificate", "solution", "program"}
    if isinstance(value, Mapping):
        if forbidden & set(value):
            raise ValueError("later workload must not encode its protected answer")
        for child in value.values():
            _assert_workload_has_no_answer(child)
    elif isinstance(value, list):
        for child in value:
            _assert_workload_has_no_answer(child)


def _direct_equivalence(adapter: ExaptationAdapter, state, source, targets):
    observations = []
    source_code = sha256(direct_vieta_factor_program.__code__.co_code).hexdigest()
    for target in targets:
        poly, domain = _problem(target)
        quotient = _quotient_x(poly)
        trace = []
        source_program = adapter._source_program(state, source, quotient, domain, trace)
        direct_program = direct_vieta_factor_program(quotient, domain)
        source_obs = None if source_program is None else _affine_factor_observation(
            source_program, quotient, domain)
        direct_obs = None if direct_program is None else _affine_factor_observation(
            direct_program, quotient, domain)
        if source_obs is None or direct_obs is None or source_obs != direct_obs:
            return False, observations, source_code
        observations.append(source_obs)
    return True, observations, source_code


def qualify():
    proof_stages = json.loads((Path(__file__).parent / "examples/proof.json").read_text())["stages"]
    source_adapter = ProofCompositionAdapter()
    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / "exaptation.sqlite"
        store = EvidenceStore(path)
        source_dev = Developer(store, source_adapter)
        source_first = source_dev.run(Obligation("proof-composition", proof_stages[0], 2, "method"))
        source_second = source_dev.run(Obligation("proof-composition", proof_stages[1], 1, "method"))
        assert source_first.verdict == source_second.verdict == "verified"
        assert len(source_second.retained) == 1
        source = source_second.retained[0]
        source_record = deepcopy(store.state()["capabilities"][source])
        frozen_source = {
            "id": source,
            "fingerprint": _source_fingerprint(source_record),
            "scope": source_record["repair"]["scope"],
            "contract": source_record["repair"]["contract"],
            "verifier": source_record["evidence"]["verifier"],
            "body": source_record["repair"]["payload"]["body"],
        }
        source_freeze_digest = digest(frozen_source)

        # The later workload is loaded only after K_A is acquired and frozen.
        workload_path = Path(__file__).parent / "examples/exaptation_workload.json"
        workload_bytes = workload_path.read_bytes()
        workload = json.loads(workload_bytes)
        _assert_workload_has_no_answer(workload)
        train, heldout = workload["train"], workload["heldout"]
        workload_digest = sha256(workload_bytes).hexdigest()

        adapter = ExaptationAdapter()
        obligation = lambda target, budget: Obligation(adapter.name, target, budget, "method")

        # Cold boundary: all A artifacts are retained, but no B role exists.
        indiscriminate_active_count = len(store.state()["capabilities"])
        cold = Developer(store, adapter).run(obligation(train, 0))
        assert cold.verdict == "unknown"
        assert cold.evidence.residual["class"] == "ROLE_REQUALIFICATION_REQUIRED"
        constraint = cold.evidence.residual["constraint"]
        assert cold.evidence.certificate["source_fingerprint"] == frozen_source["fingerprint"]

        # Same-size sham source and wrong-direction role both fail closed.
        cold_state = store.state()
        sham_state = deepcopy(cold_state)
        sham_state["capabilities"][source]["repair"]["payload"]["body"] = {"op": "fit-square"}
        train_poly, train_domain = _problem(train)
        train_q = _quotient_x(train_poly)
        assert adapter._source_program(sham_state, source, train_q, train_domain, []) is None
        wrong = Repair(
            "capability", "wrong-direction-role",
            {"role": "affine-factor-pair", "source_fingerprint": frozen_source["fingerprint"],
             "body": {"op": "reverse-call", "callee": source}},
            adapter.name, (source,), adapter.role_contract)
        wrong_evidence = adapter.verify(cold_state, obligation(train, 2), wrong)
        assert wrong_evidence.verdict == "refuted"

        before_main = dict(adapter.metrics)
        developed = Developer(store, adapter).run(obligation(train, 2))
        assert developed.verdict == "verified" and len(developed.retained) == 2
        role, child = developed.retained
        active = store.state()["capabilities"]
        assert active[role]["repair"]["dependencies"] == [source]
        assert active[child]["repair"]["dependencies"] == [role]
        assert active[source]["repair"]["scope"] == frozen_source["scope"]
        main_cost = {k: adapter.metrics[k] - before_main[k] for k in before_main}
        main_cost["memory"] = 2
        main_cost["recovery"] = 0
        main_cost["total"] = sum(main_cost.values())
        main_cost["unit"] = "counted prospective-B operations/capability records, not wall-clock time"

        # Restart and require held-out zero-acquisition execution through K_C -> K_B -> K_A.
        store.close()
        store = EvidenceStore(path)
        heldout_result = Developer(store, adapter).run(obligation(heldout, 0))
        assert heldout_result.verdict == "verified" and not heldout_result.retained
        trace = heldout_result.evidence.certificate["execution_trace"]
        assert trace == [child, role, source]

        # A second implementation is classified only by protected behavior and is never a proposal.
        same_class, observations, direct_source_hash = _direct_equivalence(
            adapter, store.state(), source, [train, heldout])
        assert same_class

        # Causal execution control: preserve identities/dependencies but remove K_A's executable body.
        state = store.state()
        missing_body = deepcopy(state)
        del missing_body["capabilities"][source]["repair"]["payload"]["body"]
        heldout_poly, heldout_domain = _problem(heldout)
        assert adapter.execute_program(missing_body, child, heldout_poly, heldout_domain, []) is None
        missing_assessment = adapter.assess(missing_body, obligation(heldout, 0))
        assert missing_assessment.verdict == "unknown"

        unrelated = deepcopy(state)
        unrelated_id = source_first.retained[1]
        assert unrelated_id not in {source, role, child}
        del unrelated["capabilities"][unrelated_id]
        assert adapter.execute_program(unrelated, child, heldout_poly, heldout_domain, []) is not None
        assert adapter.execute_program(state, child, heldout_poly, heldout_domain, []) is not None

        # History-only and same-budget controls: revocation leaves immutable evidence but not execution.
        removed = store.revoke(source, "prospective exaptation source ablation")
        assert set(removed) == {source, role, child}
        assert any(e["type"] == "admit" and e["record"]["id"] == source for e in store.events())
        history_only = Developer(store, adapter).run(obligation(train, 2))
        assert history_only.verdict == "unknown"
        assert history_only.evidence.residual["class"] == "MISSING_ACTIVE_SOURCE"

        # Requalify from the same authority/history, then reacquire the exact role lineage.
        before_recovery = dict(adapter.metrics)
        restored_source = Developer(store, source_adapter).run(
            Obligation("proof-composition", proof_stages[1], 1, "method"))
        assert restored_source.verdict == "verified" and restored_source.retained == (source,)
        restored = Developer(store, adapter).run(obligation(train, 2))
        assert restored.verdict == "verified" and restored.retained == (role, child)
        restored_heldout = Developer(store, adapter).run(obligation(heldout, 0))
        assert restored_heldout.verdict == "verified"
        recovery_delta = {k: adapter.metrics[k] - before_recovery[k] for k in before_recovery}
        recovery_delta["recovery_admissions"] = 3

        source_after = store.state()["capabilities"][source]
        assert _source_fingerprint(source_after) == frozen_source["fingerprint"]
        assert digest({
            "id": source, "fingerprint": _source_fingerprint(source_after),
            "scope": source_after["repair"]["scope"],
            "contract": source_after["repair"]["contract"],
            "verifier": source_after["evidence"]["verifier"],
            "body": source_after["repair"]["payload"]["body"],
        }) == source_freeze_digest
        store.close()

        return {
            "outcome": "VERIFIED_EXAPTATION",
            "claim": "a learned proof capability was requalified for a previously unassigned factor-interface role and causally opened a dependent future capability",
            "source_A": frozen_source,
            "source_freeze_digest": source_freeze_digest,
            "later_workload_sha256": workload_digest,
            "later_workload_loaded_after_source_freeze": True,
            "later_workload_contains_no_encoded_answer": True,
            "cold_boundary": cold.verdict,
            "cold_residual": cold.evidence.residual["class"],
            "derived_constraint": constraint,
            "classification": {"reuse": False, "exaptation": True, "expansion": False},
            "K_B": role,
            "K_B_dependency": source,
            "K_C": child,
            "K_C_dependency": role,
            "heldout_zero_acquisition_budget": heldout_result.verdict,
            "heldout_execution_trace": trace,
            "source_distinct_realization": {
                "implementation": "direct-vieta-factor-program",
                "source_hash": direct_source_hash,
                "same_behavioral_class": same_class,
                "protected_observations": observations,
                "not_available_to_developer": True,
            },
            "controls": {
                "fixed_policy_zero_budget": cold.verdict,
                "indiscriminate_A_retention_without_requalification": cold.verdict,
                "indiscriminate_active_capabilities": indiscriminate_active_count,
                "same_size_sham_source": "unknown",
                "wrong_direction_role": wrong_evidence.verdict,
                "missing_source_body": missing_assessment.verdict,
                "unrelated_capability_removal": "verified",
                "raw_history_only_same_budget": history_only.verdict,
                "same_budget": 2,
                "restored_requalified_lineage": restored_heldout.verdict,
            },
            "causal_ablation_removed_lineage": sorted(removed),
            "history_preserved": True,
            "developmental_cost": main_cost,
            "recovery_cost": recovery_delta,
            "limits": [
                "internally authored frozen later workload, not externally blind administration",
                "finite supplied proof-program language and exact rational polynomial tasks",
                "requalification is verifier-checked but the Python interpreter is not Lean-verified",
                "source-distinct realization is a protected-behavior control, not an offered proposal",
                "zero acquisition budget is not zero execution cost",
                "does not decide whether the newly reachable use pre-existed or was created",
            ],
        }


if __name__ == "__main__":
    print(json.dumps(qualify(), indent=2))
