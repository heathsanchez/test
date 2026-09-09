"""Post-freeze external theorem qualification over a pinned MiniF2F test split.

The implementation, source capability, parser, selection rule, and verifier are
frozen before the external Test.lean file is fetched. Selection then uses the
platform-assigned workflow run ID, so the exact B/held-out pair is not known at
commit time. This is a bounded external-selection test, not a claim of arbitrary
theorem proving or independently authored adapter synthesis.
"""
from __future__ import annotations

import argparse
from copy import deepcopy
from dataclasses import asdict
from fractions import Fraction as Q
from hashlib import sha256
import json
from pathlib import Path
import re
import tempfile
from typing import Any, Mapping

from .proof import ProofProcedureAdapter, check, half_line_square, norm
from .residual import ResidualEnvelope
from .runtime import (
    CapabilityContract, Developer, Evidence, EvidenceStore, IRContract,
    Obligation, Repair, assessment_claim, canonical, digest,
)

CORPUS_REPOSITORY = "google-deepmind/miniF2F"
CORPUS_COMMIT = "f0a20e14c1eeccd859d51bb4c2b3ee487889c303"
TEST_PATH = "MiniF2F/Test.lean"
TEST_BLOB_SHA1 = "7d3a756cb3da856fc26096c8da440f086653cfc1"

SOURCE_PURPOSE_A = {
    "name": "pre-external-ray-square",
    "polynomial": {"1": "1/2", "2": "-1", "3": "1/2"},
    "domain": ["ray"],
}
UNRELATED_PURPOSE = {
    "name": "pre-external-unrelated-interval",
    "polynomial": {"0": "1", "2": "-1"},
    "domain": ["interval", "0", "1"],
}

THEOREM_RE = re.compile(
    r"(?ms)^theorem\s+([A-Za-z0-9_'.]+)\s+"
    r"\(([A-Za-z_][A-Za-z0-9_']*)\s*:\s*ℝ\)\s*:\s*"
    r"(.*?)\s*:=\s*by\b"
)
TOKEN_RE = re.compile(
    r"\s*(?:(\d+)|([A-Za-z_][A-Za-z0-9_']*)|(\^|\+|-|\*|/|\(|\)))"
)


def _padd(left: Mapping[int, Q], right: Mapping[int, Q]) -> dict[int, Q]:
    out = dict(left)
    for power, coefficient in right.items():
        out[power] = out.get(power, Q(0)) + coefficient
    return {k: v for k, v in out.items() if v}


def _pneg(poly: Mapping[int, Q]) -> dict[int, Q]:
    return {k: -v for k, v in poly.items() if v}


def _pmul(left: Mapping[int, Q], right: Mapping[int, Q]) -> dict[int, Q]:
    out: dict[int, Q] = {}
    for i, x in left.items():
        for j, y in right.items():
            out[i + j] = out.get(i + j, Q(0)) + x * y
    return {k: v for k, v in out.items() if v}


def _ppow(poly: Mapping[int, Q], power: int) -> dict[int, Q]:
    if power < 0 or power > 6:
        raise ValueError("unsupported exponent")
    out = {0: Q(1)}
    for _ in range(power):
        out = _pmul(out, poly)
    return out


class _PolynomialParser:
    def __init__(self, text: str, variable: str):
        self.variable = variable
        self.tokens: list[str] = []
        pos = 0
        while pos < len(text):
            match = TOKEN_RE.match(text, pos)
            if match is None:
                raise ValueError("unsupported token")
            token = match.group(1) or match.group(2) or match.group(3)
            self.tokens.append(token)
            pos = match.end()
        self.index = 0

    def _peek(self) -> str | None:
        return self.tokens[self.index] if self.index < len(self.tokens) else None

    def _take(self, expected: str | None = None) -> str:
        token = self._peek()
        if token is None or (expected is not None and token != expected):
            raise ValueError("malformed expression")
        self.index += 1
        return token

    def parse(self) -> dict[int, Q]:
        out = self._expr()
        if self._peek() is not None:
            raise ValueError("trailing expression")
        return out

    def _expr(self) -> dict[int, Q]:
        left = self._term()
        while self._peek() in {"+", "-"}:
            op = self._take()
            right = self._term()
            left = _padd(left, right if op == "+" else _pneg(right))
        return left

    def _term(self) -> dict[int, Q]:
        left = self._power()
        while self._peek() in {"*", "/"}:
            op = self._take()
            right = self._power()
            if op == "*":
                left = _pmul(left, right)
            else:
                if set(right) - {0} or right.get(0, Q(0)) == 0:
                    raise ValueError("division must be by a nonzero constant")
                divisor = right[0]
                left = {k: v / divisor for k, v in left.items()}
        return {k: v for k, v in left.items() if v}

    def _power(self) -> dict[int, Q]:
        left = self._unary()
        if self._peek() == "^":
            self._take("^")
            raw = self._take()
            if not raw.isdigit():
                raise ValueError("power must be a natural numeral")
            left = _ppow(left, int(raw))
        return left

    def _unary(self) -> dict[int, Q]:
        if self._peek() == "-":
            self._take("-")
            return _pneg(self._unary())
        return self._atom()

    def _atom(self) -> dict[int, Q]:
        token = self._take()
        if token == "(":
            out = self._expr()
            self._take(")")
            return out
        if token.isdigit():
            return {0: Q(int(token))}
        if token == self.variable:
            return {1: Q(1)}
        raise ValueError("unexpected identifier")


def _parse_expr(text: str, variable: str) -> dict[int, Q]:
    return _PolynomialParser(text, variable).parse()


def _serialize_poly(poly: Mapping[int, Q]) -> dict[str, str]:
    return {str(k): str(v) for k, v in sorted(poly.items()) if v}


def _global_certificate(poly: Mapping[Any, Any]) -> dict[str, str] | None:
    """Independent exact global-quadratic verifier/realization."""
    p = norm(poly)
    if max(p, default=-1) != 2:
        return None
    a, b, c = p.get(2, Q(0)), p.get(1, Q(0)), p.get(0, Q(0))
    if a <= 0:
        return None
    root = -b / (2 * a)
    delta = c - b * b / (4 * a)
    if delta < 0:
        return None
    return {"A": str(a), "r": str(root), "D": str(delta)}


def _check_global(poly: Mapping[Any, Any], certificate: Mapping[str, Any]) -> bool:
    try:
        a, root, delta = Q(certificate["A"]), Q(certificate["r"]), Q(certificate["D"])
        if a <= 0 or delta < 0:
            return False
        reconstructed = norm({0: a * root * root + delta, 1: -2 * a * root, 2: a})
        return reconstructed == norm(poly)
    except (KeyError, TypeError, ValueError, ZeroDivisionError):
        return False


def _candidate_from_statement(name: str, variable: str, statement: str):
    if any(marker in statement for marker in (
        "answer", "Real.", "abs", "∀", "∃", "Set.", "{", "}", "∧", "∨", "↔", "→",
    )):
        return None
    if statement.count("≤") + statement.count("≥") != 1:
        return None
    if "≤" in statement:
        left_raw, right_raw = statement.split("≤", 1)
        direction = "le"
    else:
        left_raw, right_raw = statement.split("≥", 1)
        direction = "ge"
    try:
        left = _parse_expr(left_raw, variable)
        right = _parse_expr(right_raw, variable)
    except ValueError:
        return None
    poly = _padd(right, _pneg(left)) if direction == "le" else _padd(left, _pneg(right))
    cert = _global_certificate(poly)
    if cert is None:
        return None
    source_cert = half_line_square(poly, ("ray",))
    if source_cert is None or int(source_cert.get("power", -1)) != 0:
        return None
    if not check(poly, ("ray",), source_cert) or not _check_global(poly, source_cert):
        return None
    normalized = " ".join(statement.split())
    return {
        "name": name,
        "variable": variable,
        "statement": normalized,
        "statement_sha256": sha256(normalized.encode()).hexdigest(),
        "polynomial": _serialize_poly(poly),
        "global_certificate_sha256": sha256(canonical(cert).encode()).hexdigest(),
    }


def extract_candidates(text: str) -> list[dict[str, Any]]:
    out = []
    for match in THEOREM_RE.finditer(text):
        candidate = _candidate_from_statement(match.group(1), match.group(2), match.group(3))
        if candidate is not None:
            out.append(candidate)
    out.sort(key=lambda c: (c["name"], c["statement_sha256"]))
    return out


def _source_fingerprint(record: Mapping[str, Any]) -> str:
    return digest({
        "repair": record["repair"],
        "verifier": record["evidence"]["verifier"],
        "attachment": record["attachment"],
        "status": record["status"],
    })


def freeze_source(state_path: Path, freeze_sha: str) -> dict[str, Any]:
    if re.fullmatch(r"[0-9a-f]{40}", freeze_sha) is None:
        raise ValueError("freeze SHA must be a full lowercase Git SHA")
    if state_path.exists():
        state_path.unlink()
    store = EvidenceStore(state_path)
    adapter = ProofProcedureAdapter()
    source = Developer(store, adapter).run(Obligation(adapter.name, SOURCE_PURPOSE_A, 1, "method"))
    if source.verdict != "verified" or len(source.retained) != 1:
        raise RuntimeError("failed to acquire source K_A before external workload")
    source_id = source.retained[0]
    unrelated = Developer(store, adapter).run(Obligation(adapter.name, UNRELATED_PURPOSE, 1, "method"))
    if unrelated.verdict != "verified" or len(unrelated.retained) != 1:
        raise RuntimeError("failed to acquire pre-frozen unrelated control capability")
    unrelated_id = unrelated.retained[0]
    state = store.state()
    record = deepcopy(state["capabilities"][source_id])
    if record["repair"]["payload"].get("procedure") != "half_line_square":
        raise RuntimeError("unexpected K_A procedure")
    manifest = {
        "schema": "external-minif2f-source-freeze/v1",
        "freeze_commit": freeze_sha,
        "source_A_purpose": SOURCE_PURPOSE_A,
        "source_A_purpose_digest": digest(SOURCE_PURPOSE_A),
        "K_A": source_id,
        "K_A_fingerprint": _source_fingerprint(record),
        "K_A_scope": record["repair"]["scope"],
        "K_A_contract": record["repair"]["contract"],
        "K_A_verifier": record["evidence"]["verifier"],
        "unrelated_capability": unrelated_id,
        "state_id": digest(state),
        "ledger_digest": digest(store.events()),
        "external_test_bytes_seen": False,
    }
    store.close()
    return {**manifest, "freeze_digest": digest(manifest)}


class ExternalMiniF2FAdapter:
    """Requalify one frozen ray-square procedure for all-real quadratics."""
    name = "external-minif2f-global-quadratic-v1"
    contract = IRContract(
        "ExternalLeanGlobalQuadratic", "RequalifiedProofProgram",
        "VerifiedNonnegativity|Unknown", "exact rational all-real square completion",
        "external statement normalizes to replayed nonnegative quadratic",
        "ExternalMiniF2FQuadraticCertificate")
    role_contract = CapabilityContract(
        "QuadraticPolynomial", "GlobalSquareCertificate",
        "source square decomposition reverified on all reals",
        "ExternalGlobalSquareCertificate")
    program_contract = CapabilityContract(
        "QuadraticPolynomial", "GlobalQuadraticProgram",
        "delegates to a verified global-square role",
        "ExternalMiniF2FQuadraticCertificate")

    def __init__(self, source_id: str, source_fingerprint: str, *, allow_requalification: bool = True):
        self.source_id = source_id
        self.source_fingerprint = source_fingerprint
        self.allow_requalification = allow_requalification
        self.verifier_id = "external-minif2f-global-quadratic-v1:" + digest({
            "source_id": source_id,
            "source_fingerprint": source_fingerprint,
            "allow_requalification": allow_requalification,
            "contract": self.contract.id,
        })

    def _problem(self, obligation: Obligation):
        return norm(obligation.target["polynomial"])

    def _source_square(self, state: Mapping[str, Any], poly, trace: list[str]):
        record = state["capabilities"].get(self.source_id)
        if record is None or _source_fingerprint(record) != self.source_fingerprint:
            return None
        repair = record["repair"]
        if repair["scope"] != "proof-procedure" or repair["payload"].get("procedure") != "half_line_square":
            return None
        trace.append(self.source_id)
        certificate = half_line_square(poly, ("ray",))
        if (certificate is None or int(certificate.get("power", -1)) != 0
                or not check(poly, ("ray",), certificate) or not _check_global(poly, certificate)):
            return None
        return {"A": certificate["A"], "r": certificate["r"], "D": certificate["D"]}

    def _role_id(self, state: Mapping[str, Any]) -> str | None:
        for rid, record in state["capabilities"].items():
            repair = record["repair"]
            if (repair["scope"] == self.name
                    and repair["payload"].get("role") == "global-square-requalification"
                    and repair["dependencies"] == [self.source_id]
                    and record["evidence"]["verifier"] == self.verifier_id):
                return rid
        return None

    def _program_id(self, state: Mapping[str, Any]) -> str | None:
        for rid, record in state["capabilities"].items():
            repair = record["repair"]
            if (repair["scope"] == self.name
                    and repair["payload"].get("program") == "external-global-quadratic"
                    and record["evidence"]["verifier"] == self.verifier_id):
                return rid
        return None

    def execute_role(self, state, rid, poly, trace=None, active=()):
        trace = [] if trace is None else trace
        record = state["capabilities"].get(rid)
        if record is None or rid in active:
            return None
        repair = record["repair"]
        body = repair["payload"].get("body", {})
        if (repair["scope"] != self.name or repair["dependencies"] != [self.source_id]
                or body.get("op") != "globalize-square" or body.get("callee") != self.source_id
                or body.get("source_fingerprint") != self.source_fingerprint
                or record["evidence"]["verifier"] != self.verifier_id):
            return None
        trace.append(rid)
        return self._source_square(state, poly, trace)

    def execute_program(self, state, rid, poly, trace=None, active=()):
        trace = [] if trace is None else trace
        record = state["capabilities"].get(rid)
        if record is None or rid in active:
            return None
        repair = record["repair"]
        body = repair["payload"].get("body", {})
        role = body.get("callee")
        if (repair["scope"] != self.name or repair["dependencies"] != [role]
                or repair["payload"].get("program") != "external-global-quadratic"
                or body.get("op") != "call-global-role"
                or record["evidence"]["verifier"] != self.verifier_id):
            return None
        trace.append(rid)
        return self.execute_role(state, role, poly, trace, (*active, rid))

    def _envelope(self, *, residual_class: str, diagnosis: str, witness: Any,
                  obligation: Obligation, state: Mapping[str, Any], constraint: Any,
                  version_space: Any) -> dict[str, Any]:
        return ResidualEnvelope(
            residual_class=residual_class,
            diagnosis=diagnosis,
            verifier_certified_witness=deepcopy(witness),
            closure_id=digest({"scope": self.name, "active": sorted(state["capabilities"])}),
            budget_id=digest({"budget": obligation.budget, "target": obligation.target["statement_sha256"]}),
            necessary_constraint=deepcopy(constraint),
            version_space_id=digest(version_space),
            evidence_strength="exact-replay-certified",
            domain_payload={
                "external_repository": CORPUS_REPOSITORY,
                "external_commit": CORPUS_COMMIT,
                "statement_sha256": obligation.target["statement_sha256"],
            },
            source=self.source_id,
            source_fingerprint=self.source_fingerprint,
            constraint=deepcopy(constraint),
        ).to_mapping()

    def assess(self, state: Mapping[str, Any], obligation: Obligation) -> Evidence:
        claim = assessment_claim(state, obligation)
        poly = self._problem(obligation)
        program = self._program_id(state)
        if program is not None:
            trace: list[str] = []
            certificate = self.execute_program(state, program, poly, trace)
            if certificate is not None and _check_global(poly, certificate):
                return Evidence("verified", claim, self.verifier_id,
                                {"program": program, "certificate": certificate,
                                 "execution_trace": trace,
                                 "statement_sha256": obligation.target["statement_sha256"],
                                 "semantics": "A*(x-r)^2+D = polynomial with A>0 and D>=0"},
                                scope=self.name)

        source_record = state["capabilities"].get(self.source_id)
        if source_record is None or _source_fingerprint(source_record) != self.source_fingerprint:
            witness = {"source_active": False, "K_A": self.source_id}
            return Evidence("unknown", claim, self.verifier_id, witness,
                            self._envelope(residual_class="SOURCE_NOT_ACTIVE",
                                           diagnosis="capability_failure", witness=witness,
                                           obligation=obligation, state=state,
                                           constraint={"requires_active_source": self.source_id},
                                           version_space={"candidates": []}), self.name)

        role = self._role_id(state)
        if role is None:
            trace: list[str] = []
            source_certificate = self._source_square(state, poly, trace)
            witness = {"source_active": True, "K_A": self.source_id,
                       "source_scope": source_record["repair"]["scope"],
                       "source_contract": source_record["repair"]["contract"],
                       "source_can_expose_power0_square": source_certificate is not None,
                       "source_execution_trace": trace}
            constraint = {"new_scope": self.name, "must_depend_on": self.source_id,
                          "must_preserve_source_fingerprint": self.source_fingerprint,
                          "must_reverify_power0_square_on_all_reals": True}
            return Evidence("unknown", claim, self.verifier_id, witness,
                            self._envelope(residual_class="GLOBAL_ROLE_REQUALIFICATION_REQUIRED",
                                           diagnosis="capability_failure", witness=witness,
                                           obligation=obligation, state=state, constraint=constraint,
                                           version_space={"candidate_roles": ["global-square-requalification"]}),
                            self.name)

        trace = []
        role_certificate = self.execute_role(state, role, poly, trace)
        if role_certificate is None or not _check_global(poly, role_certificate):
            witness = {"role": role, "role_execution_failed": True}
            return Evidence("unknown", claim, self.verifier_id, witness,
                            self._envelope(residual_class="REQUALIFIED_ROLE_INADEQUATE",
                                           diagnosis="capability_failure", witness=witness,
                                           obligation=obligation, state=state,
                                           constraint={"requires_global_certificate": True},
                                           version_space={"active_role": role}), self.name)

        witness = {"role": role, "role_certificate": role_certificate, "execution_trace": trace}
        return Evidence("unknown", claim, self.verifier_id, witness,
                        self._envelope(residual_class="EXTERNAL_PROGRAM_REQUIRED",
                                       diagnosis="capability_failure", witness=witness,
                                       obligation=obligation, state=state,
                                       constraint={"program_must_delegate_to": role},
                                       version_space={"candidate_programs": ["external-global-quadratic"]}),
                        self.name)

    def propose(self, state: Mapping[str, Any], obligation: Obligation, residual: Any):
        residual_class = residual.get("class") if isinstance(residual, Mapping) else None
        if residual_class == "GLOBAL_ROLE_REQUALIFICATION_REQUIRED":
            if not self.allow_requalification:
                return
            yield Repair("capability", "global-square-requalification",
                         {"role": "global-square-requalification",
                          "body": {"op": "globalize-square", "callee": self.source_id,
                                   "source_fingerprint": self.source_fingerprint}},
                         self.name, (self.source_id,), self.role_contract)
        elif residual_class == "EXTERNAL_PROGRAM_REQUIRED":
            role = self._role_id(state)
            if role is not None:
                yield Repair("capability", "external-global-quadratic",
                             {"program": "external-global-quadratic",
                              "body": {"op": "call-global-role", "callee": role}},
                             self.name, (role,), self.program_contract)

    def verify(self, state: Mapping[str, Any], obligation: Obligation, repair: Repair) -> Evidence:
        poly = self._problem(obligation)
        expected_role_payload = {"role": "global-square-requalification",
                                 "body": {"op": "globalize-square", "callee": self.source_id,
                                          "source_fingerprint": self.source_fingerprint}}
        role_ok = (repair.kind == "capability" and repair.scope == self.name
                   and repair.payload == expected_role_payload
                   and repair.dependencies == (self.source_id,) and repair.contract == self.role_contract)
        role = self._role_id(state)
        expected_program_payload = {"program": "external-global-quadratic",
                                    "body": {"op": "call-global-role", "callee": role}}
        program_ok = (role is not None and repair.kind == "capability" and repair.scope == self.name
                      and repair.payload == expected_program_payload and repair.dependencies == (role,)
                      and repair.contract == self.program_contract)
        trace: list[str] = []
        if role_ok:
            certificate = self._source_square(state, poly, trace)
            valid = certificate is not None and _check_global(poly, certificate)
            kind = "role"
        elif program_ok:
            certificate = self.execute_role(state, role, poly, trace)
            valid = certificate is not None and _check_global(poly, certificate)
            kind = "program"
        else:
            certificate, valid, kind = None, False, "invalid"
        return Evidence("verified" if valid else "refuted", repair.id, self.verifier_id,
                        {"accepted": valid, "object": kind, "certificate": certificate,
                         "execution_trace": trace,
                         "statement_sha256": obligation.target["statement_sha256"]}, scope=self.name)

    def attach(self, state: Mapping[str, Any], repair: Repair, evidence: Evidence):
        if evidence.verdict != "verified" or evidence.claim != repair.id or not evidence.certificate.get("accepted"):
            raise ValueError("unverified external capability")
        return {"executable": True, "semantic_contract": "exact all-real square completion",
                "external_corpus": f"{CORPUS_REPOSITORY}@{CORPUS_COMMIT}"}


def _select_pair(candidates: list[dict[str, Any]], freeze_sha: str, nonce: str):
    if len(candidates) < 2:
        raise ValueError("external corpus has fewer than two admissible candidates")
    pool_identity = [{"name": c["name"], "statement_sha256": c["statement_sha256"],
                      "polynomial": c["polynomial"]} for c in candidates]
    pool_digest = digest(pool_identity)
    seed = sha256(f"{freeze_sha}:{nonce}:{CORPUS_COMMIT}:{TEST_BLOB_SHA1}:{pool_digest}".encode()).hexdigest()
    first = int(seed, 16) % len(candidates)
    second_seed = sha256((seed + ":heldout").encode()).hexdigest()
    second = (first + 1 + int(second_seed, 16) % (len(candidates) - 1)) % len(candidates)
    return candidates[first], candidates[second], first, second, pool_digest, seed


def _direct_equivalence(poly, source_certificate):
    direct = _global_certificate(poly)
    return (direct is not None and _check_global(poly, direct) and _check_global(poly, source_certificate),
            digest({"implementation": "direct-discriminant-global-square", "source": "external_minif2f.py"}))


def _matched_fixed_policy(source_manifest, train):
    with tempfile.TemporaryDirectory() as tmp:
        state_path = Path(tmp) / "fixed.sqlite"
        frozen = freeze_source(state_path, source_manifest["freeze_commit"])
        adapter = ExternalMiniF2FAdapter(frozen["K_A"], frozen["K_A_fingerprint"], allow_requalification=False)
        store = EvidenceStore(state_path)
        result = Developer(store, adapter).run(Obligation(adapter.name, train, 2, "method"))
        store.close()
        return {"B_acquisition_budget": 2, "verdict": result.verdict,
                "policy": "requalification-disabled"}


def qualify_external(*, state_path: Path, source_manifest_path: Path,
                     test_path: Path, freeze_sha: str, selection_nonce: str,
                     corpus_commit: str, test_blob_sha1: str) -> dict[str, Any]:
    source_manifest = json.loads(source_manifest_path.read_text())
    if source_manifest.get("schema") != "external-minif2f-source-freeze/v1":
        raise ValueError("invalid source freeze manifest")
    supplied_freeze_digest = source_manifest.get("freeze_digest")
    freeze_body = {k: v for k, v in source_manifest.items() if k != "freeze_digest"}
    if supplied_freeze_digest != digest(freeze_body):
        raise ValueError("source freeze manifest is stale")
    if source_manifest["freeze_commit"] != freeze_sha:
        raise ValueError("source was not frozen at this commit")
    if corpus_commit != CORPUS_COMMIT or test_blob_sha1 != TEST_BLOB_SHA1:
        raise ValueError("external corpus identity changed")

    store = EvidenceStore(state_path)
    initial_state = store.state()
    if digest(initial_state) != source_manifest["state_id"] or digest(store.events()) != source_manifest["ledger_digest"]:
        raise ValueError("active source state changed before external workload")
    source_id = source_manifest["K_A"]
    source_record = initial_state["capabilities"].get(source_id)
    if source_record is None or _source_fingerprint(source_record) != source_manifest["K_A_fingerprint"]:
        raise ValueError("frozen K_A does not match source manifest")

    test_bytes = test_path.read_bytes()
    test_sha256 = sha256(test_bytes).hexdigest()
    candidates = extract_candidates(test_bytes.decode("utf-8"))
    if len(candidates) < 2:
        result = {"outcome": "UNKNOWN_EXTERNAL_CORPUS_INSUFFICIENT", "freeze_commit": freeze_sha,
                  "selection_nonce": selection_nonce, "source_freeze_digest": supplied_freeze_digest,
                  "external_repository": CORPUS_REPOSITORY, "external_commit": CORPUS_COMMIT,
                  "external_test_blob_sha1": TEST_BLOB_SHA1, "external_test_sha256": test_sha256,
                  "candidate_count": len(candidates),
                  "obstruction": "fewer than two test-split theorems match the pre-frozen one-variable global-quadratic grammar"}
        store.close()
        return result

    train, heldout, train_index, heldout_index, pool_digest, seed = _select_pair(candidates, freeze_sha, selection_nonce)
    adapter = ExternalMiniF2FAdapter(source_id, source_manifest["K_A_fingerprint"])
    obligation = lambda target, budget: Obligation(adapter.name, target, budget, "method")

    cold = Developer(store, adapter).run(obligation(train, 0))
    if cold.verdict != "unknown":
        raise RuntimeError("cold external B unexpectedly bypassed development")
    cold_residual = ResidualEnvelope.from_mapping(cold.evidence.residual)
    if cold_residual.residual_class != "GLOBAL_ROLE_REQUALIFICATION_REQUIRED":
        raise RuntimeError("external B did not expose the expected role boundary")

    real_role = next(adapter.propose(store.state(), obligation(train, 2), cold.evidence.residual))
    sham_payload = deepcopy(real_role.payload)
    sham_payload["body"]["op"] = "globalize-squarE"
    sham = Repair(real_role.kind, real_role.name, sham_payload, real_role.scope,
                  real_role.dependencies, real_role.contract)
    if len(canonical(asdict(real_role))) != len(canonical(asdict(sham))):
        raise RuntimeError("same-size sham construction failed")
    sham_evidence = adapter.verify(store.state(), obligation(train, 2), sham)
    wrong_payload = deepcopy(real_role.payload)
    wrong_payload["body"]["op"] = "localize-square"
    wrong = Repair(real_role.kind, "wrong-direction-global-role", wrong_payload,
                   real_role.scope, real_role.dependencies, real_role.contract)
    wrong_evidence = adapter.verify(store.state(), obligation(train, 2), wrong)

    developed = Developer(store, adapter).run(obligation(train, 2))
    if developed.verdict != "verified" or len(developed.retained) != 2:
        result = {"outcome": "UNKNOWN_EXTERNAL_DEVELOPMENT", "freeze_commit": freeze_sha,
                  "selection_nonce": selection_nonce, "source_freeze_digest": supplied_freeze_digest,
                  "candidate_count": len(candidates), "candidate_pool_digest": pool_digest,
                  "selection_seed": seed, "B": train, "heldout": heldout,
                  "cold_residual": cold.evidence.residual, "development_verdict": developed.verdict,
                  "retained": list(developed.retained)}
        store.close()
        return result

    role, child = developed.retained
    pre_restart_state = store.state()
    if pre_restart_state["capabilities"][role]["repair"]["dependencies"] != [source_id]:
        raise RuntimeError("K_B does not depend exactly on K_A")
    if pre_restart_state["capabilities"][child]["repair"]["dependencies"] != [role]:
        raise RuntimeError("K_C does not depend exactly on K_B")

    store.close()
    store = EvidenceStore(state_path)
    adapter = ExternalMiniF2FAdapter(source_id, source_manifest["K_A_fingerprint"])
    heldout_result = Developer(store, adapter).run(obligation(heldout, 0))
    if heldout_result.verdict != "verified" or heldout_result.retained:
        raise RuntimeError("external held-out zero-acquisition reuse failed")
    trace = heldout_result.evidence.certificate["execution_trace"]
    if trace != [child, role, source_id]:
        raise RuntimeError("held-out execution did not traverse K_C -> K_B -> K_A")

    train_trace: list[str] = []
    train_cert = adapter.execute_program(store.state(), child, norm(train["polynomial"]), train_trace)
    heldout_trace: list[str] = []
    heldout_cert = adapter.execute_program(store.state(), child, norm(heldout["polynomial"]), heldout_trace)
    train_equiv, direct_hash = _direct_equivalence(norm(train["polynomial"]), train_cert)
    heldout_equiv, _ = _direct_equivalence(norm(heldout["polynomial"]), heldout_cert)
    if not (train_equiv and heldout_equiv):
        raise RuntimeError("source-distinct behavioral check failed")

    live = store.state()
    missing_source = deepcopy(live)
    del missing_source["capabilities"][source_id]["repair"]["payload"]["procedure"]
    missing = adapter.assess(missing_source, obligation(heldout, 0))

    unrelated = deepcopy(live)
    unrelated_id = source_manifest["unrelated_capability"]
    del unrelated["capabilities"][unrelated_id]
    unrelated_result = adapter.assess(unrelated, obligation(heldout, 0))

    removed = set(store.revoke(source_id, "external MiniF2F ancestor ablation"))
    after_revoke = Developer(store, adapter).run(obligation(heldout, 0))
    raw_history = Developer(store, adapter).run(obligation(train, 2))
    history_preserved = any(event["type"] == "admit" and event["record"]["id"] == source_id
                            for event in store.events())

    proof_adapter = ProofProcedureAdapter()
    restored_source = Developer(store, proof_adapter).run(Obligation(proof_adapter.name, SOURCE_PURPOSE_A, 1, "method"))
    restored_development = Developer(store, adapter).run(obligation(train, 2))
    restored_heldout = Developer(store, adapter).run(obligation(heldout, 0))
    fixed = _matched_fixed_policy(source_manifest, train)

    result = {
        "outcome": "VERIFIED_EXTERNALLY_SELECTED_EXAPTATION",
        "claim_boundary": "external B/held-out selected after source/controller freeze from a pinned independent MiniF2F test split within a precommitted one-variable global-quadratic grammar",
        "freeze_commit": freeze_sha, "selection_nonce": selection_nonce,
        "source_freeze_digest": supplied_freeze_digest, "source_state_id": source_manifest["state_id"],
        "source_external_bytes_seen_at_freeze": source_manifest["external_test_bytes_seen"],
        "external_repository": CORPUS_REPOSITORY, "external_commit": CORPUS_COMMIT,
        "external_test_path": TEST_PATH, "external_test_blob_sha1": TEST_BLOB_SHA1,
        "external_test_sha256": test_sha256, "candidate_count": len(candidates),
        "candidate_pool_digest": pool_digest,
        "selection_rule": "sha256(freeze_sha:workflow_run_id:corpus_commit:test_blob:pool_digest)",
        "selection_seed": seed, "B_index": train_index, "heldout_index": heldout_index,
        "B": train, "heldout": heldout,
        "classification": {"reuse": False, "exaptation": True, "expansion": False},
        "K_A": source_id, "K_A_fingerprint": source_manifest["K_A_fingerprint"],
        "K_B": role, "K_B_dependency": source_id, "K_C": child, "K_C_dependency": role,
        "cold": cold.verdict, "typed_residual": cold.evidence.residual,
        "B_acquisition_budget": 2, "warm": developed.verdict, "restart": True,
        "heldout_acquisition_budget": 0, "heldout_verdict": heldout_result.verdict,
        "heldout_execution_trace": trace,
        "behavioral_identity": {"source_distinct_implementation": "direct-discriminant-global-square",
                                "source_distinct_implementation_hash": direct_hash,
                                "same_behavioral_class_on_B_and_heldout": True,
                                "not_available_to_developer": True},
        "controls": {"same_size_sham_K_B": sham_evidence.verdict,
                     "same_size_serialized_bytes": len(canonical(asdict(real_role))),
                     "wrong_direction_adapter": wrong_evidence.verdict,
                     "missing_K_A_executable_identity": missing.verdict,
                     "unrelated_removal": unrelated_result.verdict,
                     "ancestor_revocation_heldout": after_revoke.verdict,
                     "raw_history_reconstruction_same_B_budget": raw_history.verdict,
                     "matched_fixed_policy": fixed,
                     "restored_source_same_identity": restored_source.retained == (source_id,),
                     "restored_development": restored_development.verdict,
                     "restored_heldout": restored_heldout.verdict,
                     "history_preserved": history_preserved,
                     "revoked_lineage_contains": sorted({source_id, role, child} & removed)},
        "limits": [
            "external theorem pair is selected from a predeclared parseable family, not arbitrary MiniF2F",
            "adapter/parser and requalification operation are supplied before selection",
            "test split is independently maintained, but this protocol does not prove no human ever saw its contents",
            "selection uses a platform run ID after commit freeze; re-running the same commit can select a different pair",
            "exact rational quadratic verifier is Python, not Lean-verified",
            "result does not establish unrestricted grammar invention or universal theorem proving",
        ],
    }
    store.close()
    return result


def main() -> None:
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="command", required=True)
    freeze = sub.add_parser("freeze-source")
    freeze.add_argument("--state", type=Path, required=True)
    freeze.add_argument("--freeze-sha", required=True)
    freeze.add_argument("--output", type=Path, required=True)
    qualify = sub.add_parser("qualify")
    qualify.add_argument("--state", type=Path, required=True)
    qualify.add_argument("--source-manifest", type=Path, required=True)
    qualify.add_argument("--test", type=Path, required=True)
    qualify.add_argument("--freeze-sha", required=True)
    qualify.add_argument("--selection-nonce", required=True)
    qualify.add_argument("--corpus-commit", required=True)
    qualify.add_argument("--test-blob-sha1", required=True)
    qualify.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if args.command == "freeze-source":
        result = freeze_source(args.state, args.freeze_sha)
    else:
        result = qualify_external(state_path=args.state, source_manifest_path=args.source_manifest,
                                  test_path=args.test, freeze_sha=args.freeze_sha,
                                  selection_nonce=args.selection_nonce, corpus_commit=args.corpus_commit,
                                  test_blob_sha1=args.test_blob_sha1)
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(result["outcome"] if "outcome" in result else "SOURCE_FREEZE_PASS",
          result.get("freeze_digest", result.get("candidate_pool_digest", "")))


if __name__ == "__main__":
    main()
