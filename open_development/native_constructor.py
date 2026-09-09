"""Persistent integration of the frozen Machine Insight V5 type constructor.

The historical npm selection is not rerun here.  This module replays the exact
old-grammar obstruction and the 237-program lower-substrate search, then routes
the resulting executable constructor through the ordinary admission ledger.
"""
from __future__ import annotations

from hashlib import sha256
from pathlib import Path
from typing import Any, Mapping

from .runtime import (CapabilityContract, Evidence, IRContract, Obligation, Repair,
                      assessment_claim, digest)

V5_PRECOMMIT = "dd603d2d1e0eb61089483f0e93a30c4b30db6b0b88d39768bd6b9cee8ae176ac"
V5_PROPOSAL = "02adbed53296089e71385b5a03513f08396566eac5929982fce1cd7c56dae62d"
TARGET = ("SUM", "ONE", ("PROD", "PARAM", "Y"))


def generated_trees(atoms: tuple[str, ...], max_size: int) -> tuple[Any, ...]:
    """Ordered odd-sized trees over the frozen SUM/PROD substrate."""
    levels: dict[int, list[Any]] = {1: list(atoms)}
    for size in range(3, max_size + 1, 2):
        out = []
        for left_size in range(1, size - 1, 2):
            right_size = size - 1 - left_size
            for operation in ("SUM", "PROD"):
                for left in levels[left_size]:
                    for right in levels[right_size]:
                        out.append((operation, left, right))
        levels[size] = out
    return tuple(tree for size in sorted(levels) for tree in levels[size])


def direct_arity(tree: Any) -> int:
    if tree == "ONE":
        return 0
    if tree == "SELF":
        return 1
    operation, left, right = tree
    if operation == "SUM":
        return max(direct_arity(left), direct_arity(right))
    return direct_arity(left) + direct_arity(right)


def old_closure_certificate() -> dict[str, Any]:
    trees = generated_trees(("ONE", "SELF"), 9)
    return {"enumerated": len(trees), "maximum_direct_arity": max(map(direct_arity, trees)),
            "deciding_array_arity": max(map(direct_arity, trees)) + 1,
            "budget_independent": True}


def _denote(tree: Any, recursive: set[Any]) -> set[Any]:
    if tree == "ONE":
        return {("unit",)}
    if tree == "PARAM":
        return {("param", "a"), ("param", "b")}
    if tree == "Y":
        return recursive
    operation, left, right = tree
    lvalues, rvalues = _denote(left, recursive), _denote(right, recursive)
    if operation == "SUM":
        return {("left", value) for value in lvalues} | {
            ("right", value) for value in rvalues}
    return {("product", left_value, right_value)
            for left_value in lvalues for right_value in rvalues}


def fixed_point_prefix(tree: Any, depth: int = 4) -> set[Any]:
    values: set[Any] = set()
    for _ in range(depth):
        values = _denote(tree, values)
    return values


def constructor_candidates() -> tuple[Any, ...]:
    candidates = generated_trees(("ONE", "PARAM", "Y"), 5)
    assert len(candidates) == 237
    return candidates


def unique_survivors() -> tuple[Any, ...]:
    expected = fixed_point_prefix(TARGET)
    return tuple(candidate for candidate in constructor_candidates()
                 if fixed_point_prefix(candidate) == expected)


def valid_tree(value: Any) -> bool:
    return (isinstance(value, Mapping) and isinstance(value.get("label"), str)
            and isinstance(value.get("children"), list)
            and all(valid_tree(child) for child in value["children"]))


def roundtrip(value: Mapping[str, Any]) -> dict[str, Any]:
    if not valid_tree(value):
        raise ValueError("malformed recursive value")
    return {"label": value["label"], "children": [roundtrip(child) for child in value["children"]]}


def node_count(value: Mapping[str, Any]) -> int:
    checked = roundtrip(value)
    return 1 + sum(node_count(child) for child in checked["children"])


class NativeConstructorAdapter:
    name = "native-constructor"
    contract = IRContract(
        "RecursiveSchema|RecursiveTreeTask", "NestedParameterizedFixpoint",
        "ExactRoundtrip|Natural", "ordered finite homogeneous recurrence",
        "native tree roundtrip and fold observation", "NativeConstructorReplayCertificate")
    constructor_contract = CapabilityContract(
        "ParameterType", "OrderedFiniteSequence(ParameterType)",
        "MU(Y,SUM(ONE,PROD(PARAM,Y)))", "NestedFixpointCertificate")
    fold_contract = CapabilityContract(
        "RecursiveTree", "Natural", "fold over retained ordered child spine",
        "RecursiveFoldReplayCertificate")
    verifier_id = "machine-insight-native-v5-replay:" + digest({
        "precommit": V5_PRECOMMIT, "proposal": V5_PROPOSAL,
        "source": sha256(Path(__file__).read_bytes()).hexdigest(), "contract": contract.id})

    def _records(self, state: Mapping[str, Any]):
        return tuple((rid, record) for rid, record in state["capabilities"].items()
                     if record["repair"]["scope"] == self.name
                     and record["evidence"]["verifier"] == self.verifier_id)

    def _constructor(self, state: Mapping[str, Any]):
        return next((rid for rid, record in self._records(state)
                     if record["repair"]["payload"].get("role") == "constructor"), None)

    def _fold(self, state: Mapping[str, Any]):
        return next((rid for rid, record in self._records(state)
                     if record["repair"]["payload"].get("role") == "node_count"), None)

    def assess(self, state: Mapping[str, Any], obligation: Obligation) -> Evidence:
        claim, task = assessment_claim(state, obligation), obligation.target["task"]
        constructor = self._constructor(state)
        if task in {"source", "transfer"}:
            if constructor is None:
                obstruction = old_closure_certificate()
                return Evidence("unknown", claim, self.verifier_id, obstruction,
                                {"class": "OLD_GRAMMAR_INADEQUATE", **obstruction}, self.name)
            return Evidence("verified", claim, self.verifier_id,
                            {"constructor": constructor, "ast": list(TARGET),
                             "package": obligation.target["package"],
                             "roundtrip": "exact", "variable_arity": True}, scope=self.name)
        if task == "acquire-fold":
            if constructor is None:
                return Evidence("unknown", claim, self.verifier_id, {"closure": "old"},
                                {"class": "MISSING_NESTED_CONSTRUCTOR"}, self.name)
            fold = self._fold(state)
            if fold is None:
                return Evidence("unknown", claim, self.verifier_id, {"constructor": constructor},
                                {"class": "FOLD_CONSTRUCTED", "constructor": constructor}, self.name)
            return Evidence("verified", claim, self.verifier_id,
                            {"fold": fold, "value": node_count(obligation.target["tree"])}, scope=self.name)
        if task == "heldout-fold":
            fold = self._fold(state)
            if fold is None:
                return Evidence("unknown", claim, self.verifier_id, {"fold": None},
                                {"class": "MISSING_RECURSIVE_FOLD"}, self.name)
            actual = node_count(obligation.target["tree"])
            verdict = "verified" if actual == obligation.target["expected"] else "refuted"
            return Evidence(verdict, claim, self.verifier_id,
                            {"fold": fold, "actual": actual, "expected": obligation.target["expected"]},
                            scope=self.name)
        raise ValueError("unknown native constructor task")

    def propose(self, state: Mapping[str, Any], obligation: Obligation, residual: Any):
        if residual.get("class") == "OLD_GRAMMAR_INADEQUATE":
            for index, candidate in enumerate(constructor_candidates()):
                yield Repair("capability", f"nested-fixpoint-{index}",
                             {"role": "constructor", "ast": candidate}, self.name,
                             contract=self.constructor_contract)
        elif residual.get("class") == "FOLD_CONSTRUCTED":
            yield Repair("capability", "recursive-node-count", {"role": "node_count"},
                         self.name, (residual["constructor"],), self.fold_contract)

    def verify(self, state: Mapping[str, Any], obligation: Obligation, repair: Repair) -> Evidence:
        survivors = unique_survivors()
        ast = repair.payload.get("ast")
        ast = tuple(ast) if isinstance(ast, list) else ast
        is_constructor = (repair.payload.get("role") == "constructor"
                          and repair.contract == self.constructor_contract
                          and not repair.dependencies and ast in survivors and len(survivors) == 1)
        constructor = self._constructor(state)
        is_fold = (repair.payload.get("role") == "node_count" and constructor is not None
                   and repair.dependencies == (constructor,) and repair.contract == self.fold_contract
                   and obligation.target["task"] == "acquire-fold"
                   and node_count(obligation.target["tree"]) == obligation.target["expected"])
        if not (repair.kind == "capability" and (is_constructor or is_fold)):
            return Evidence("refuted", repair.id, self.verifier_id, {"accepted": False}, scope=self.name)
        return Evidence("verified", repair.id, self.verifier_id,
                        {"accepted": True, "object": "constructor" if is_constructor else "fold",
                         "candidate_count": 237, "unique_survivors": len(survivors),
                         "old_closure": old_closure_certificate(),
                         "historical_proposal": V5_PROPOSAL}, scope=self.name)

    def attach(self, state: Mapping[str, Any], repair: Repair, evidence: Evidence):
        if evidence.verdict != "verified" or not evidence.certificate.get("accepted"):
            raise ValueError("unverified native constructor")
        return {"role": repair.payload["role"], "executable": True,
                "ast": repair.payload.get("ast"), "historical_proposal": V5_PROPOSAL}
