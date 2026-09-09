"""Exact rational-polynomial proof-procedure adapter.

Procedures emit inert certificate data. An independent replay checker
reconstructs the polynomial and checks every domain side condition. The finite
builder menu is a declared search boundary, not a completeness claim.
"""
from __future__ import annotations

from fractions import Fraction as Q
from hashlib import sha256
from math import isqrt
from pathlib import Path
from typing import Any, Mapping

from .runtime import (CapabilityContract, Evidence, IRContract, Obligation, Repair,
                      assessment_claim, digest)


def norm(poly: Mapping[Any, Any]) -> dict[int, Q]:
    return {int(k): Q(v) for k, v in poly.items() if Q(v)}


def mul(left: Mapping[Any, Any], right: Mapping[Any, Any]) -> dict[int, Q]:
    out: dict[int, Q] = {}
    for i, x in norm(left).items():
        for j, y in norm(right).items():
            out[i + j] = out.get(i + j, Q(0)) + x * y
    return norm(out)


def replay(certificate: Mapping[str, Any], domain: tuple[Any, ...]) -> dict[int, Q]:
    kind = certificate["kind"]
    if kind == "coeff":
        poly = norm(certificate["polynomial"])
        if any(k < 0 or v < 0 for k, v in poly.items()):
            raise ValueError("negative coefficient")
        if domain[0] == "interval" and Q(domain[1]) < 0:
            raise ValueError("negative interval unsupported")
        return poly
    if kind == "square":
        power = int(certificate["power"])
        a, root, delta = Q(certificate["A"]), Q(certificate["r"]), Q(certificate["D"])
        if domain[0] != "ray" or power < 0 or a < 0 or delta < 0:
            raise ValueError("invalid half-line square")
        return norm({power: a * root * root + delta,
                     power + 1: -2 * a * root, power + 2: a})
    if kind == "affine":
        if domain[0] != "interval":
            raise ValueError("affine requires interval")
        lower, upper = Q(domain[1]), Q(domain[2])
        a, b = Q(certificate["a"]), Q(certificate["b"])
        if lower > upper or a * lower + b < 0 or a * upper + b < 0:
            raise ValueError("affine endpoint condition")
        return norm({0: b, 1: a})
    if kind == "product":
        children = certificate["children"]
        if not children:
            raise ValueError("empty product")
        result = {0: Q(1)}
        for child in children:
            result = mul(result, replay(child, domain))
        return result
    raise ValueError("unknown constructor")


def check(poly: Mapping[Any, Any], domain: tuple[Any, ...], certificate: Mapping[str, Any]) -> bool:
    try:
        return replay(certificate, domain) == norm(poly)
    except (KeyError, TypeError, ValueError, ZeroDivisionError, OverflowError):
        return False


def coefficientwise(poly: Mapping[Any, Any], _domain: tuple[Any, ...]):
    p = norm(poly)
    if any(k < 0 or v < 0 for k, v in p.items()):
        return None
    return {"kind": "coeff", "polynomial": {str(k): str(v) for k, v in p.items()}}


def half_line_square(poly: Mapping[Any, Any], domain: tuple[Any, ...]):
    if domain[0] != "ray":
        return None
    p = norm(poly)
    if not p:
        return coefficientwise(p, domain)
    power = min(p)
    shifted = {k - power: v for k, v in p.items()}
    if any(k not in (0, 1, 2) for k in shifted):
        return None
    a, b, c = shifted.get(2, Q(0)), shifted.get(1, Q(0)), shifted.get(0, Q(0))
    if a <= 0:
        return None
    root, delta = -b / (2 * a), c - b * b / (4 * a)
    if delta < 0:
        return None
    return {"kind": "square", "power": power, "A": str(a), "r": str(root), "D": str(delta)}


def interval_affine(poly: Mapping[Any, Any], domain: tuple[Any, ...]):
    if domain[0] != "interval":
        return None
    p = norm(poly)
    if not p or max(p) != 2:
        return None
    lower, upper = Q(domain[1]), Q(domain[2])
    a, b, c = p[2], p.get(1, Q(0)), p.get(0, Q(0))
    discriminant = b * b - 4 * a * c
    if discriminant < 0:
        return None
    numerator, denominator = isqrt(discriminant.numerator), isqrt(discriminant.denominator)
    if numerator * numerator != discriminant.numerator or denominator * denominator != discriminant.denominator:
        return None
    root = Q(numerator, denominator)
    r1, r2 = (-b + root) / (2 * a), (-b - root) / (2 * a)
    variants = (({0: -a*r1, 1: a}, {0: -r2, 1: Q(1)}),
                ({0: -a*r2, 1: a}, {0: -r1, 1: Q(1)}),
                ({0: a*r1, 1: -a}, {0: r2, 1: Q(-1)}),
                ({0: a*r2, 1: -a}, {0: r1, 1: Q(-1)}))
    for first, second in variants:
        if mul(first, second) != p:
            continue
        children = [{"kind": "affine", "a": str(f[1]), "b": str(f[0])}
                    for f in (first, second)]
        cert = {"kind": "product", "children": children}
        if all(Q(f["a"])*lower + Q(f["b"]) >= 0 and Q(f["a"])*upper + Q(f["b"]) >= 0
               for f in children):
            return cert
    return None


BUILDERS = {"coefficientwise": coefficientwise,
            "half_line_square": half_line_square,
            "interval_affine": interval_affine}


class ProofProcedureAdapter:
    name = "proof-procedure"
    contract = IRContract(
        "PolynomialNonnegativityObligation", "CertificateProcedure",
        "VerifiedNonnegativity|Unknown", "exact rational polynomial replay",
        "replayed polynomial equals obligation polynomial", "RationalCertificate")
    procedure_contract = CapabilityContract(
        "Polynomial×Domain", "Certificate", "exact certificate replay preserves polynomial",
        "RationalCertificate")

    def __init__(self, candidates: tuple[str, ...] = tuple(BUILDERS)):
        if not candidates or any(name not in BUILDERS for name in candidates):
            raise ValueError("unknown procedure candidate")
        self.candidates = candidates
        source = sha256(Path(__file__).read_bytes()).hexdigest()
        self.verifier_id = "exact-rational-certificate-v1:" + digest(
            {"checker_source": source, "candidates": candidates,
             "ir_contract": self.contract.id})

    def _problem(self, obligation: Obligation):
        poly = norm(obligation.target["polynomial"])
        raw = obligation.target["domain"]
        domain = (str(raw[0]), *(Q(x) for x in raw[1:]))
        if domain[0] not in {"ray", "interval"} or (domain[0] == "interval" and len(domain) != 3):
            raise ValueError("invalid proof domain")
        return poly, domain

    def _active(self, state: Mapping[str, Any]):
        names = ["coefficientwise"]
        for record in state["capabilities"].values():
            repair, evidence = record["repair"], record["evidence"]
            if (repair["scope"] == self.name and repair["kind"] == "capability" and
                    evidence["verifier"] == self.verifier_id):
                names.append(repair["payload"]["procedure"])
        return tuple(dict.fromkeys(names))

    def assess(self, state: Mapping[str, Any], obligation: Obligation) -> Evidence:
        claim = assessment_claim(state, obligation)
        poly, domain = self._problem(obligation)
        failures = []
        for name in self._active(state):
            certificate = BUILDERS[name](poly, domain)
            if certificate is not None and check(poly, domain, certificate):
                return Evidence("verified", claim, self.verifier_id,
                                {"procedure": name, "certificate": certificate,
                                 "polynomial": {str(k): str(v) for k, v in poly.items()},
                                 "domain": [str(x) for x in domain]}, scope=self.name)
            failures.append(name)
        return Evidence("unknown", claim, self.verifier_id, {"checked": failures},
                        {"class": "PROCEDURE_GRAMMAR_INSUFFICIENT", "failed": failures}, self.name)

    def propose(self, state: Mapping[str, Any], obligation: Obligation, residual: Any):
        if residual.get("class") != "PROCEDURE_GRAMMAR_INSUFFICIENT":
            return
        active = set(self._active(state))
        for name in self.candidates:
            if name not in active:
                yield Repair("capability", name, {"procedure": name}, self.name,
                             contract=self.procedure_contract)

    def verify(self, state: Mapping[str, Any], obligation: Obligation, repair: Repair) -> Evidence:
        if (repair.kind != "capability" or repair.payload.get("procedure") not in BUILDERS
                or repair.contract != self.procedure_contract):
            return Evidence("unknown", repair.id, self.verifier_id)
        poly, domain = self._problem(obligation)
        certificate = BUILDERS[repair.payload["procedure"]](poly, domain)
        if certificate is None or not check(poly, domain, certificate):
            return Evidence("refuted", repair.id, self.verifier_id,
                            {"checked": True, "accepted": False}, scope=self.name)
        return Evidence("verified", repair.id, self.verifier_id,
                        {"checked": True, "accepted": True, "certificate": certificate,
                         "semantics": "replay(certificate, domain) = polynomial"}, scope=self.name)

    def attach(self, state: Mapping[str, Any], repair: Repair, evidence: Evidence):
        if evidence.verdict != "verified" or evidence.claim != repair.id or not evidence.certificate.get("accepted"):
            raise ValueError("unverified proof procedure")
        return {"procedure": repair.payload["procedure"], "executable": True,
                "semantic_contract": evidence.certificate["semantics"]}
