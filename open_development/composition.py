"""Bounded construction of reusable proof programs from lower-level primitives."""
from __future__ import annotations

from fractions import Fraction as Q
from hashlib import sha256
from pathlib import Path
from typing import Any, Mapping

from .proof import half_line_square, interval_affine, mul, norm
from .runtime import (CapabilityContract, Evidence, IRContract, Obligation, Repair,
                      assessment_claim, digest)


def replay_program(program: Mapping[str, Any], domain: tuple[Any, ...]) -> dict[int, Q]:
    kind = program["kind"]
    if kind == "monomial":
        power, coefficient = int(program["power"]), Q(program["coefficient"])
        if power < 0 or coefficient < 0 or (domain[0] == "interval" and Q(domain[1]) < 0):
            raise ValueError("invalid monomial")
        return norm({power: coefficient})
    if kind == "square":
        root = Q(program["root"])
        return norm({0: root * root, 1: -2 * root, 2: Q(1)})
    if kind == "affine":
        if domain[0] != "interval":
            raise ValueError("affine requires interval")
        lower, upper = Q(domain[1]), Q(domain[2])
        a, b = Q(program["a"]), Q(program["b"])
        if lower > upper or a * lower + b < 0 or a * upper + b < 0:
            raise ValueError("affine endpoint condition")
        return norm({0: b, 1: a})
    if kind == "product":
        children = program["children"]
        if len(children) != 2:
            raise ValueError("binary product required")
        return mul(replay_program(children[0], domain), replay_program(children[1], domain))
    raise ValueError("unknown program node")


def check_program(poly: Mapping[Any, Any], domain: tuple[Any, ...], program: Mapping[str, Any]) -> bool:
    try:
        return replay_program(program, domain) == norm(poly)
    except (KeyError, TypeError, ValueError, ZeroDivisionError, OverflowError):
        return False


def construct_product(poly: Mapping[Any, Any], domain: tuple[Any, ...]):
    """Fit one binary product from the supplied primitive language."""
    if domain[0] == "ray":
        square = half_line_square(poly, domain)
        if square is None or Q(square["D"]) != 0:
            return None
        program = {"kind": "product", "children": [
            {"kind": "monomial", "power": square["power"], "coefficient": square["A"]},
            {"kind": "square", "root": square["r"]}]}
    else:
        factors = interval_affine(poly, domain)
        if factors is None:
            return None
        program = factors
    return program if check_program(poly, domain, program) else None


def construct_nested_product(poly: Mapping[Any, Any], domain: tuple[Any, ...]):
    """Extend a retained affine-product program by a nonnegative monomial.

    This is deliberately generic over the coefficients: divisibility by x is
    detected from the obligation, and the remaining quadratic is replayed
    through the existing interval-affine constructor.
    """
    p = norm(poly)
    if domain[0] != "interval" or p.get(0, Q(0)) != 0 or not p:
        return None
    quotient = norm({power - 1: coefficient for power, coefficient in p.items()
                     if power > 0})
    factors = interval_affine(quotient, domain)
    if factors is None:
        return None
    program = {"kind": "product", "children": [
        {"kind": "monomial", "power": 1, "coefficient": "1"}, factors]}
    return program if check_program(poly, domain, program) else None


def program_shape(program: Mapping[str, Any]) -> str:
    kind = program["kind"]
    if kind != "product":
        return kind
    children = program.get("children", ())
    if len(children) != 2:
        raise ValueError("binary product required")
    return "product(" + ",".join(program_shape(child) for child in children) + ")"


class ProofCompositionAdapter:
    """Develop a product constructor, then use it as retained executable means."""
    name = "proof-composition"
    contract = IRContract(
        "PolynomialNonnegativityObligation", "CertificateProgramTemplate",
        "VerifiedNonnegativity|Unknown", "typed certificate-program interpretation",
        "program replay equals obligation polynomial", "ProofProgramReplayCertificate")
    constructor_contract = CapabilityContract(
        "PrimitiveCertificate×PrimitiveCertificate", "ProductCertificateProgram",
        "product of certified nonnegative programs is nonnegative", "ProductReplayCertificate")
    program_contract = CapabilityContract(
        "Polynomial×Domain", "CertificateProgram", "template instantiation preserves shape and replay",
        "ProofProgramReplayCertificate")
    verifier_id = "exact-proof-program-replay-v1:" + digest({
        "nodes": ["monomial", "square", "affine", "product"], "arity": 2,
        "checker_source": sha256(Path(__file__).read_bytes()).hexdigest(),
        "ir_contract": contract.id})

    def _problem(self, obligation: Obligation):
        poly = norm(obligation.target["polynomial"])
        raw = obligation.target["domain"]
        return poly, (str(raw[0]), *(Q(x) for x in raw[1:]))

    def _constructor(self, state: Mapping[str, Any]):
        return next((rid for rid, record in state["capabilities"].items()
                     if record["repair"]["scope"] == self.name
                     and record["repair"]["payload"].get("constructor") == "binary_product"
                     and record["evidence"]["verifier"] == self.verifier_id), None)

    def _programs(self, state: Mapping[str, Any]):
        return {record["repair"]["payload"]["program_shape"]: rid
                for rid, record in state["capabilities"].items()
                if record["repair"]["scope"] == self.name
                and "program_shape" in record["repair"]["payload"]
                and record["evidence"]["verifier"] == self.verifier_id}

    def assess(self, state: Mapping[str, Any], obligation: Obligation) -> Evidence:
        claim = assessment_claim(state, obligation)
        constructor = self._constructor(state)
        poly, domain = self._problem(obligation)
        if constructor is None:
            return Evidence("unknown", claim, self.verifier_id, {"closure": "primitive-only"},
                            {"class": "MISSING_COMPOSITION", "operation": "product"}, self.name)
        programs = self._programs(state)
        program = construct_product(poly, domain)
        dependency = constructor
        if program is None:
            parent_shape = "product(affine,affine)"
            dependency = programs.get(parent_shape)
            if dependency is not None:
                program = construct_nested_product(poly, domain)
        if program is None:
            return Evidence("unknown", claim, self.verifier_id, {"constructor": constructor},
                            {"class": "BOUNDED_PROGRAM_NOT_FOUND"}, self.name)
        shape = program_shape(program)
        retained = programs.get(shape)
        if retained is None:
            return Evidence("unknown", claim, self.verifier_id,
                            {"constructor": constructor, "candidate_program": program},
                            {"class": "PROGRAM_CONSTRUCTED", "program_shape": shape,
                             "dependency": dependency}, self.name)
        return Evidence("verified", claim, self.verifier_id,
                        {"constructor": constructor, "retained_program": retained,
                         "program": program, "program_shape": shape,
                         "semantics": "replay_program(program, domain) = polynomial"}, scope=self.name)

    def propose(self, state: Mapping[str, Any], obligation: Obligation, residual: Any):
        if residual.get("class") == "MISSING_COMPOSITION":
            yield Repair("capability", "binary-product", {"constructor": "binary_product"}, self.name,
                         contract=self.constructor_contract)
        elif residual.get("class") == "PROGRAM_CONSTRUCTED":
            yield Repair("capability", residual["program_shape"],
                         {"program_shape": residual["program_shape"]}, self.name,
                         (residual["dependency"],), self.program_contract)

    def verify(self, state: Mapping[str, Any], obligation: Obligation, repair: Repair) -> Evidence:
        poly, domain = self._problem(obligation)
        program = construct_product(poly, domain)
        constructor = self._constructor(state)
        is_constructor = (repair.payload.get("constructor") == "binary_product"
                          and not repair.dependencies
                          and repair.contract == self.constructor_contract)
        expected_dependency = constructor
        if program is None:
            parent = self._programs(state).get("product(affine,affine)")
            if parent is not None:
                program = construct_nested_product(poly, domain)
                expected_dependency = parent
        is_program = (program is not None and repair.payload.get("program_shape") == program_shape(program)
                      and expected_dependency is not None
                      and repair.dependencies == (expected_dependency,)
                      and repair.contract == self.program_contract)
        valid = (repair.kind == "capability" and (is_constructor or is_program)
                 and program is not None and check_program(poly, domain, program))
        if not valid:
            return Evidence("refuted", repair.id, self.verifier_id,
                            {"accepted": False}, scope=self.name)
        return Evidence("verified", repair.id, self.verifier_id,
                        {"accepted": True, "witness_program": program,
                         "object": "constructor" if is_constructor else "program",
                         "semantics": "binary product preserves certified nonnegativity"}, scope=self.name)

    def attach(self, state: Mapping[str, Any], repair: Repair, evidence: Evidence):
        if evidence.verdict != "verified" or evidence.claim != repair.id or not evidence.certificate["accepted"]:
            raise ValueError("unverified constructor")
        if repair.payload.get("constructor") == "binary_product":
            return {"constructor": "binary_product", "executable": True,
                    "semantic_contract": evidence.certificate["semantics"]}
        return {"program_shape": repair.payload["program_shape"], "executable": True,
                "semantic_contract": evidence.certificate["semantics"]}
