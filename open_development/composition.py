"""Bounded construction of reusable proof programs from lower-level primitives."""
from __future__ import annotations

from fractions import Fraction as Q
from hashlib import sha256
from pathlib import Path
from typing import Any, Mapping

from .proof import half_line_square, interval_affine, mul, norm
from .runtime import Evidence, Obligation, Repair, assessment_claim, digest


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


class ProofCompositionAdapter:
    """Develop a product constructor, then use it as retained executable means."""
    name = "proof-composition"
    verifier_id = "exact-proof-program-replay-v1:" + digest({
        "nodes": ["monomial", "square", "affine", "product"], "arity": 2,
        "checker_source": sha256(Path(__file__).read_bytes()).hexdigest()})

    def _problem(self, obligation: Obligation):
        poly = norm(obligation.target["polynomial"])
        raw = obligation.target["domain"]
        return poly, (str(raw[0]), *(Q(x) for x in raw[1:]))

    def _constructor(self, state: Mapping[str, Any]):
        return next((rid for rid, record in state["capabilities"].items()
                     if record["repair"]["scope"] == self.name
                     and record["repair"]["payload"].get("constructor") == "binary_product"
                     and record["evidence"]["verifier"] == self.verifier_id), None)

    def assess(self, state: Mapping[str, Any], obligation: Obligation) -> Evidence:
        claim = assessment_claim(state, obligation)
        constructor = self._constructor(state)
        poly, domain = self._problem(obligation)
        if constructor is None:
            return Evidence("unknown", claim, self.verifier_id, {"closure": "primitive-only"},
                            {"class": "MISSING_COMPOSITION", "operation": "product"}, self.name)
        program = construct_product(poly, domain)
        if program is None:
            return Evidence("unknown", claim, self.verifier_id, {"constructor": constructor},
                            {"class": "BOUNDED_PROGRAM_NOT_FOUND"}, self.name)
        return Evidence("verified", claim, self.verifier_id,
                        {"constructor": constructor, "program": program,
                         "semantics": "replay_program(program, domain) = polynomial"}, scope=self.name)

    def propose(self, state: Mapping[str, Any], obligation: Obligation, residual: Any):
        if residual.get("class") == "MISSING_COMPOSITION":
            yield Repair("capability", "binary-product", {"constructor": "binary_product"}, self.name)

    def verify(self, state: Mapping[str, Any], obligation: Obligation, repair: Repair) -> Evidence:
        poly, domain = self._problem(obligation)
        program = construct_product(poly, domain)
        valid = (repair.kind == "capability" and repair.payload.get("constructor") == "binary_product"
                 and program is not None and check_program(poly, domain, program))
        if not valid:
            return Evidence("refuted", repair.id, self.verifier_id,
                            {"accepted": False}, scope=self.name)
        return Evidence("verified", repair.id, self.verifier_id,
                        {"accepted": True, "witness_program": program,
                         "semantics": "binary product preserves certified nonnegativity"}, scope=self.name)

    def attach(self, state: Mapping[str, Any], repair: Repair, evidence: Evidence):
        if evidence.verdict != "verified" or evidence.claim != repair.id or not evidence.certificate["accepted"]:
            raise ValueError("unverified constructor")
        return {"constructor": "binary_product", "executable": True,
                "semantic_contract": evidence.certificate["semantics"]}
