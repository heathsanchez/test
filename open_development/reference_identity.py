"""Persistent integration of Machine Insight V6 reference-identity genesis.

The historical deepcopy/cloudpickle/NetworkX corpora are evidence identities,
not rerun claims.  This adapter prospectively freezes new stdlib object-graph
obligations, enumerates a small low-level allocation grammar, and admits only
the implementation that preserves both sharing and cycles.
"""
from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass
from hashlib import sha256
from pathlib import Path
import pickle
from typing import Any, Mapping

from .runtime import (CapabilityContract, Evidence, IRContract, Obligation, Repair,
                      assessment_claim, digest)

HISTORICAL_SOURCE_CASES = 3000
HISTORICAL_TRANSFER_CASES = 3000
HISTORICAL_DESCENDANT_CASES = 5000
HISTORICAL_TREE_FAILURES = (939, 1000)
PRIMITIVE = "REFERENCE_REUSE_BY_IDENTITY"
TARGET = ("identity", "preorder", True)


@dataclass(eq=False)
class RefNode:
    label: str
    children: list["RefNode"]


def decode_graph(spec: Mapping[str, Any]) -> RefNode:
    labels, edges = spec.get("labels"), spec.get("edges")
    if (not isinstance(labels, list) or not labels
            or not all(isinstance(label, str) for label in labels)
            or not isinstance(edges, list) or len(edges) != len(labels)):
        raise ValueError("malformed reference graph")
    if not all(isinstance(row, list) and all(isinstance(i, int) and 0 <= i < len(labels)
                                             for i in row) for row in edges):
        raise ValueError("malformed reference edges")
    root = spec.get("root", 0)
    if not isinstance(root, int) or not 0 <= root < len(labels):
        raise ValueError("malformed reference root")
    nodes = [RefNode(label, []) for label in labels]
    for node, row in zip(nodes, edges):
        node.children.extend(nodes[i] for i in row)
    return nodes[root]


def graph_observation(root: RefNode) -> dict[str, Any]:
    """Canonical reachable graph, including alias and cycle identity."""
    order, positions, queue = [], {}, [root]
    while queue:
        node = queue.pop(0)
        if id(node) in positions:
            continue
        positions[id(node)] = len(order)
        order.append(node)
        queue.extend(node.children)
    return {"labels": [node.label for node in order],
            "edges": [[positions[id(child)] for child in node.children] for node in order],
            "root": 0}


def clone_candidate(root: RefNode, candidate: tuple[str, str, bool]) -> RefNode:
    key_mode, store_phase, reuse = candidate
    table: dict[Any, RefNode] = {}
    active: set[int] = set()

    def visit(source: RefNode) -> RefNode:
        token = id(source) if key_mode == "identity" else source.label
        if reuse and token in table:
            return table[token]
        if id(source) in active:
            raise ValueError("cycle entered before reference was stored")
        active.add(id(source))
        output = RefNode(source.label, [])
        if reuse and store_phase == "preorder":
            table[token] = output
        output.children.extend(visit(child) for child in source.children)
        if reuse and store_phase == "postorder":
            table[token] = output
        active.remove(id(source))
        return output

    return visit(root)


def candidates() -> tuple[tuple[str, str, bool], ...]:
    return tuple((key, phase, reuse)
                 for key in ("tag", "identity")
                 for phase in ("none", "postorder", "preorder")
                 for reuse in (False, True))


def frozen_witnesses() -> tuple[Mapping[str, Any], ...]:
    return (
        # One child is reached twice: allocation without reuse unfolds it.
        {"labels": ["root", "shared"], "edges": [[1, 1], []], "root": 0},
        # Equal visible tags remain two distinct source identities.
        {"labels": ["root", "same", "same"], "edges": [[1, 2], [], []], "root": 0},
        # Allocation must be stored before recursion reaches the root again.
        {"labels": ["a", "b"], "edges": [[1], [0]], "root": 0},
    )


def candidate_passes(candidate: tuple[str, str, bool]) -> bool:
    for spec in frozen_witnesses():
        source = decode_graph(spec)
        try:
            output = clone_candidate(source, candidate)
        except (RecursionError, ValueError):
            return False
        if graph_observation(output) != graph_observation(source):
            return False
    return True


def unique_survivors() -> tuple[tuple[str, str, bool], ...]:
    return tuple(candidate for candidate in candidates() if candidate_passes(candidate))


def oracle_roundtrip(root: RefNode, oracle: str) -> RefNode:
    if oracle == "pickle-protocol-5":
        return pickle.loads(pickle.dumps(root, protocol=5))
    if oracle == "deepcopy":
        return deepcopy(root)
    raise ValueError("unknown reference oracle")


def scc_sizes(root: RefNode) -> list[int]:
    nodes, positions, queue = [], {}, [root]
    while queue:
        node = queue.pop(0)
        if id(node) in positions:
            continue
        positions[id(node)] = len(nodes)
        nodes.append(node)
        queue.extend(node.children)
    edges = [[positions[id(child)] for child in node.children] for node in nodes]
    index = 0
    stack: list[int] = []
    on_stack: set[int] = set()
    indices: dict[int, int] = {}
    low: dict[int, int] = {}
    sizes: list[int] = []

    def visit(v: int) -> None:
        nonlocal index
        indices[v] = low[v] = index
        index += 1
        stack.append(v)
        on_stack.add(v)
        for w in edges[v]:
            if w not in indices:
                visit(w)
                low[v] = min(low[v], low[w])
            elif w in on_stack:
                low[v] = min(low[v], indices[w])
        if low[v] == indices[v]:
            size = 0
            while True:
                w = stack.pop()
                on_stack.remove(w)
                size += 1
                if w == v:
                    break
            sizes.append(size)

    for vertex in range(len(nodes)):
        if vertex not in indices:
            visit(vertex)
    return sorted(sizes)


class ReferenceIdentityAdapter:
    name = "reference-identity"
    contract = IRContract(
        "ReferenceGraph|ReferenceGraphTask", "IdentityMemoConstructor|SCCProcedure",
        "ReferenceGraph|List(Natural)", "finite reachable directed object graphs",
        "labelled edge quotient preserving source identity", "ReferenceIdentityReplayCertificate")
    constructor_contract = CapabilityContract(
        "ReferenceGraph", "ReferenceGraph", PRIMITIVE, "ReferenceIdentityConstructorCertificate")
    scc_contract = CapabilityContract(
        "ReferenceGraph", "List(Natural)", "Tarjan SCC over retained identity graph",
        "ReferenceSCCReplayCertificate")
    verifier_id = "machine-insight-v6-persistent-v1:" + digest({
        "source": sha256(Path(__file__).read_bytes()).hexdigest(),
        "primitive": PRIMITIVE, "contract": contract.id,
        "historical_counts": [HISTORICAL_SOURCE_CASES, HISTORICAL_TRANSFER_CASES,
                              HISTORICAL_DESCENDANT_CASES, *HISTORICAL_TREE_FAILURES]})

    def _records(self, state: Mapping[str, Any]):
        return tuple((rid, record) for rid, record in state["capabilities"].items()
                     if record["repair"]["scope"] == self.name
                     and record["evidence"]["verifier"] == self.verifier_id)

    def _constructor(self, state: Mapping[str, Any]):
        return next((rid for rid, record in self._records(state)
                     if record["repair"]["payload"].get("role") == "constructor"), None)

    def _scc(self, state: Mapping[str, Any]):
        return next((rid for rid, record in self._records(state)
                     if record["repair"]["payload"].get("role") == "scc"), None)

    def assess(self, state: Mapping[str, Any], obligation: Obligation) -> Evidence:
        claim, task = assessment_claim(state, obligation), obligation.target["task"]
        constructor = self._constructor(state)
        if task in {"source", "transfer"}:
            if constructor is None:
                return Evidence("unknown", claim, self.verifier_id,
                                {"tree_only": True, "witnesses": len(frozen_witnesses())},
                                {"class": "REFERENCE_FORM_MISSING",
                                 "failures": ["duplicated_allocation", "tag_collision",
                                              "postorder_cycle"]}, self.name)
            source = decode_graph(obligation.target["graph"])
            oracle = oracle_roundtrip(source, obligation.target["oracle"])
            actual = clone_candidate(source, TARGET)
            certificate = {"constructor": constructor, "primitive": PRIMITIVE,
                           "actual": graph_observation(actual),
                           "oracle": graph_observation(oracle)}
            return Evidence("verified" if certificate["actual"] == certificate["oracle"] else "refuted",
                            claim, self.verifier_id, certificate, scope=self.name)
        if task == "acquire-scc":
            if constructor is None:
                return Evidence("unknown", claim, self.verifier_id, {"constructor": None},
                                {"class": "MISSING_REFERENCE_CONSTRUCTOR"}, self.name)
            procedure = self._scc(state)
            actual = scc_sizes(clone_candidate(decode_graph(obligation.target["graph"]), TARGET))
            if procedure is None:
                return Evidence("unknown", claim, self.verifier_id,
                                {"constructor": constructor, "actual": actual},
                                {"class": "SCC_PROCEDURE_CONSTRUCTED",
                                 "constructor": constructor}, self.name)
            return Evidence("verified" if actual == obligation.target["expected"] else "refuted",
                            claim, self.verifier_id,
                            {"procedure": procedure, "actual": actual,
                             "expected": obligation.target["expected"]}, scope=self.name)
        if task == "heldout-scc":
            procedure = self._scc(state)
            if procedure is None:
                return Evidence("unknown", claim, self.verifier_id, {"procedure": None},
                                {"class": "MISSING_SCC_PROCEDURE"}, self.name)
            actual = scc_sizes(clone_candidate(decode_graph(obligation.target["graph"]), TARGET))
            return Evidence("verified" if actual == obligation.target["expected"] else "refuted",
                            claim, self.verifier_id,
                            {"procedure": procedure, "actual": actual,
                             "expected": obligation.target["expected"]}, scope=self.name)
        raise ValueError("unknown reference identity task")

    def propose(self, state: Mapping[str, Any], obligation: Obligation, residual: Any):
        if residual.get("class") == "REFERENCE_FORM_MISSING":
            for index, candidate in enumerate(candidates()):
                yield Repair("capability", f"reference-candidate-{index}",
                             {"role": "constructor", "candidate": candidate}, self.name,
                             contract=self.constructor_contract)
        elif residual.get("class") == "SCC_PROCEDURE_CONSTRUCTED":
            yield Repair("capability", "identity-aware-scc", {"role": "scc"}, self.name,
                         (residual["constructor"],), self.scc_contract)

    def verify(self, state: Mapping[str, Any], obligation: Obligation, repair: Repair) -> Evidence:
        survivors = unique_survivors()
        candidate = repair.payload.get("candidate")
        candidate = tuple(candidate) if isinstance(candidate, list) else candidate
        is_constructor = (repair.kind == "capability"
                          and repair.payload.get("role") == "constructor"
                          and repair.contract == self.constructor_contract
                          and not repair.dependencies and candidate in survivors
                          and survivors == (TARGET,))
        constructor = self._constructor(state)
        actual = None
        if repair.payload.get("role") == "scc" and obligation.target["task"] == "acquire-scc":
            actual = scc_sizes(clone_candidate(decode_graph(obligation.target["graph"]), TARGET))
        is_scc = (repair.kind == "capability" and repair.payload.get("role") == "scc"
                  and repair.contract == self.scc_contract and constructor is not None
                  and repair.dependencies == (constructor,)
                  and actual == obligation.target["expected"])
        if not (is_constructor or is_scc):
            return Evidence("refuted", repair.id, self.verifier_id,
                            {"accepted": False}, scope=self.name)
        return Evidence("verified", repair.id, self.verifier_id,
                        {"accepted": True, "object": "constructor" if is_constructor else "scc",
                         "candidate_count": len(candidates()),
                         "unique_survivors": len(survivors),
                         "residual_controls": {
                             "no_memo": False, "tag_key": False, "postorder": False},
                         "historical_replay_identity": {
                             "deepcopy": HISTORICAL_SOURCE_CASES,
                             "cloudpickle": HISTORICAL_TRANSFER_CASES,
                             "networkx_scc": HISTORICAL_DESCENDANT_CASES,
                             "tree_only_failures": list(HISTORICAL_TREE_FAILURES)}},
                        scope=self.name)

    def attach(self, state: Mapping[str, Any], repair: Repair, evidence: Evidence):
        if evidence.verdict != "verified" or not evidence.certificate.get("accepted"):
            raise ValueError("unverified reference capability")
        return {"role": repair.payload["role"], "executable": True,
                "primitive": PRIMITIVE if repair.payload["role"] == "constructor" else None,
                "candidate": repair.payload.get("candidate")}
