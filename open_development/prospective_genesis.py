"""Prospective continuation genesis from a frozen lower grid substrate.

The external stream is route-neutral and completely fixed before development.
Concrete formation programs are generated only after a complete current-language
obstruction.  The ordinary :class:`Developer` remains the sole admission path.
"""
from __future__ import annotations

import argparse
from collections import Counter
from copy import deepcopy
from dataclasses import asdict
from hashlib import sha256
import json
from itertools import product
from pathlib import Path
import resource
import subprocess
import tempfile
import time
from typing import Any, Iterable, Mapping

from .arc_discrimination import crop, d4, form, grid
from .residual import ResidualEnvelope
from .runtime import (CapabilityContract, Developer, Evidence, EvidenceStore,
                      IRContract, Obligation, Repair, assessment_claim, digest)

V4_SOURCE = "01088c9e67b11cc29342b5150a28050bdef16b29"
V4_SCIENTIFIC_FREEZE = "7505fbf047b9684fbde417705528ef0d6b37895d"
V4_SCIENTIFIC_RUN = 34449939382
V4_AUTHORITY_RUN = 34451224397
V4_AUTHORITY_ARTIFACT = 10141699676
V4_AUTHORITY_ARTIFACT_SHA256 = "7594ac85ef51238f1198c51f73f337a7d0f03218e4e7f724ea8ea4c069b95de6"
V4_AUTHORITY_EVIDENCE_DIGEST = "a3fafeddec722a32c20be4bb9ff6af9e361252d1ac200c366619f2367f71c7f9"
ARC_REPOSITORY = "fchollet/ARC-AGI"
ARC_COMMIT = "399030444e0ab0cc8b4e199870fb20b863846f34"
ARC_PATH = "data/evaluation"
D4 = ("id", "r90", "r180", "r270", "flip-h", "flip-v", "transpose", "anti")
FORM_OPS = ("concat-h", "concat-v", "overlay")
MAX_AST_SIZE = 5
MAX_AST_DEPTH = 3

INTERACTION_PROBES = tuple(
    ((a, b), (c, d))
    for a, b, c, d in product((0, 1), repeat=4)
)
INTERACTION_PROBE_MANIFEST = {
    "schema": "grid-interaction-probes/v1",
    "domain": "all 2x2 binary grids",
    "count": len(INTERACTION_PROBES),
    "digest": digest(INTERACTION_PROBES),
}


def ast_key(ast: Mapping[str, Any]) -> str:
    return json.dumps(ast, sort_keys=True, separators=(",", ":"))


def ast_size(ast: Mapping[str, Any]) -> int:
    op = ast["op"]
    if op == "input":
        return 1
    if op in {"call", "crop"}:
        return 1 + ast_size(ast["arg"])
    return 1 + ast_size(ast["left"]) + ast_size(ast["right"])


def ast_depth(ast: Mapping[str, Any]) -> int:
    op = ast["op"]
    if op == "input":
        return 1
    if op in {"call", "crop"}:
        return 1 + ast_depth(ast["arg"])
    return 1 + max(ast_depth(ast["left"]), ast_depth(ast["right"]))


def ast_dependencies(ast: Mapping[str, Any]) -> tuple[str, ...]:
    out: list[str] = []

    def walk(node: Mapping[str, Any]) -> None:
        if node["op"] == "call":
            if node["callee"] not in out:
                out.append(node["callee"])
            walk(node["arg"])
        elif node["op"] == "crop":
            walk(node["arg"])
        elif node["op"] in FORM_OPS:
            walk(node["left"])
            walk(node["right"])

    walk(ast)
    return tuple(out)


def substrate_manifest() -> dict[str, Any]:
    body = {
        "schema": "grid-lower-substrate/interaction-quotient-v1",
        "nodes": ["input", "call-retained", "crop", *FORM_OPS],
        "typing": {
            "input": "Grid",
            "call-retained": "(Grid->Grid) x Grid -> Grid",
            "crop": "Grid -> Grid",
            "concat-h": "equal-height Grid x Grid -> Grid",
            "concat-v": "equal-width Grid x Grid -> Grid",
            "overlay": "equal-shape Grid x Grid -> Grid",
        },
        "maximum_ast_size": MAX_AST_SIZE,
        "maximum_ast_depth": MAX_AST_DEPTH,
        "enumeration": "increasing size then canonical JSON",
        "normalization": [
            "call retained identity on input -> input",
            "overlay operands canonicalized",
            "duplicate canonical JSON removed",
        ],
        "equivalence": "minimum ASTs are quotiented by a frozen finite interaction profile before authority",
        "interaction_probe_manifest": INTERACTION_PROBE_MANIFEST,
        "interaction_quotient_scope": "bounded exact over the declared 16-probe suite; not global semantic equivalence",
    }
    return {**body, "substrate_id": digest(body)}


SUBSTRATE = substrate_manifest()


def _is_grid_capability(record: Mapping[str, Any]) -> bool:
    contract = record["repair"].get("contract") or {}
    return contract.get("input_type") == "Grid" and contract.get("output_type") == "Grid"


def _identity_ids(state: Mapping[str, Any]) -> set[str]:
    return {rid for rid, rec in state["capabilities"].items()
            if rec["repair"]["payload"].get("body") == {"op": "d4", "name": "id"}}


def generation_terms(state: Mapping[str, Any]) -> tuple[dict[str, Any], ...]:
    base = {"op": "input"}
    values = [base, {"op": "crop", "arg": base}]
    identities = _identity_ids(state)
    for rid, rec in sorted(state["capabilities"].items()):
        if rid not in identities and _is_grid_capability(rec):
            values.append({"op": "call", "callee": rid, "arg": base})
    unique = {ast_key(value): value for value in values}
    return tuple(unique[key] for key in sorted(unique))


def generated_asts(state: Mapping[str, Any]) -> tuple[dict[str, Any], ...]:
    """Complete bounded formation closure; no concrete combination is listed."""
    terms = generation_terms(state)
    values: dict[str, dict[str, Any]] = {}
    for op in FORM_OPS:
        for left in terms:
            for right in terms:
                if op == "overlay" and ast_key(left) > ast_key(right):
                    continue
                ast = {"op": op, "left": left, "right": right}
                if ast_size(ast) <= MAX_AST_SIZE and ast_depth(ast) <= MAX_AST_DEPTH:
                    values[ast_key(ast)] = ast
    return tuple(sorted(values.values(), key=lambda x: (ast_size(x), ast_key(x))))


def examples(task: Mapping[str, Any]) -> tuple[Mapping[str, Any], ...]:
    return tuple(task["train"])


def _valid_output(value: Any) -> bool:
    return value is not None


class ProspectiveARCAdapter:
    name = "interaction-quotient-controller-v1"
    contract = IRContract(
        "ARCTask", "GeneratedGridAST", "Verified|Unknown",
        "finite exact grid-program interpretation",
        "all available training observations equal execution",
        "GeneratedGridASTReplayCertificate")
    direct_contract = CapabilityContract("Grid", "Grid", "D4 whole-grid transform", "ARCExactGridReplay")
    role_contract = CapabilityContract(
        "NonzeroBoundingObject", "Grid", "crop then retained D4 transform", "ARCExactGridReplay")
    generated_contract = CapabilityContract(
        "Grid", "Grid", "frozen lower-substrate AST interpretation", "GeneratedGridASTReplayCertificate")
    verifier_id = "interaction-quotient-grid-genesis-v1:" + digest({
        "source": sha256(Path(__file__).read_bytes()).hexdigest(),
        "substrate": SUBSTRATE,
        "contract": contract.id,
    })

    def _exec_ast(self, state: Mapping[str, Any], ast: Mapping[str, Any], value: Any,
                  trace: list[str], active: tuple[str, ...]) -> Any:
        op = ast.get("op")
        if op == "input":
            return grid(value)
        if op == "crop":
            child = self._exec_ast(state, ast["arg"], value, trace, active)
            return None if child is None else crop(child)
        if op == "call":
            child = self._exec_ast(state, ast["arg"], value, trace, active)
            return None if child is None else self.execute(state, ast["callee"], child, trace, active)
        if op in FORM_OPS:
            left = self._exec_ast(state, ast["left"], value, trace, active)
            right = self._exec_ast(state, ast["right"], value, trace, active)
            return None if left is None or right is None else form(left, right, op)
        return None

    def execute(self, state: Mapping[str, Any], rid: str, value: Any,
                trace: list[str] | None = None, active: tuple[str, ...] = ()) -> Any:
        trace = [] if trace is None else trace
        if rid in active:
            return None
        rec = state["capabilities"].get(rid)
        if not rec or rec["evidence"]["verifier"] != self.verifier_id:
            return None
        trace.append(rid)
        repair = rec["repair"]
        body = repair["payload"].get("body", {})
        if body.get("op") == "d4" and repair["contract"] == asdict(self.direct_contract):
            return d4(value, body["name"])
        if body.get("op") == "crop-call" and repair["contract"] == asdict(self.role_contract):
            parent = body.get("callee")
            if repair["dependencies"] != [parent]:
                return None
            return self.execute(state, parent, crop(value), trace, (*active, rid))
        if body.get("op") == "generated-ast" and repair["contract"] == asdict(self.generated_contract):
            ast = body.get("ast")
            if body.get("substrate_id") != SUBSTRATE["substrate_id"] or not isinstance(ast, Mapping):
                return None
            if repair["dependencies"] != list(ast_dependencies(ast)):
                return None
            return self._exec_ast(state, ast, value, trace, (*active, rid))
        return None

    def solves(self, state: Mapping[str, Any], rid: str, task: Mapping[str, Any]) -> bool:
        try:
            return all(self.execute(state, rid, e["input"], []) == grid(e["output"])
                       for e in examples(task))
        except (KeyError, TypeError, ValueError, IndexError):
            return False

    def solving_records(self, state: Mapping[str, Any], task: Mapping[str, Any]) -> list[str]:
        return [rid for rid in state["capabilities"] if self.solves(state, rid, task)]

    def role_survivors(self, state: Mapping[str, Any], task: Mapping[str, Any]) -> list[str]:
        seeds = [(rid, rec["repair"]["payload"]["body"]["name"])
                 for rid, rec in state["capabilities"].items()
                 if rec["repair"]["payload"].get("body", {}).get("op") == "d4"]
        out = []
        for rid, name in seeds:
            try:
                if all(d4(crop(e["input"]), name) == grid(e["output"]) for e in examples(task)):
                    out.append(rid)
            except (KeyError, TypeError, ValueError, IndexError):
                pass
        return sorted(out)

    def execute_ast(self, state: Mapping[str, Any], ast: Mapping[str, Any], value: Any) -> Any:
        return self._exec_ast(state, ast, value, [], ())

    def _interaction_profile(self, state: Mapping[str, Any], ast: Mapping[str, Any]) -> tuple[str, tuple[Any, ...]]:
        outputs = tuple(self.execute_ast(state, ast, probe) for probe in INTERACTION_PROBES)
        return digest(outputs), outputs

    def _interaction_classes(self, state: Mapping[str, Any],
                             survivors: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], dict[str, Any] | None]:
        grouped: dict[str, dict[str, Any]] = {}
        for ast in survivors:
            class_id, outputs = self._interaction_profile(state, ast)
            item = grouped.setdefault(class_id, {"class_id": class_id, "outputs": outputs, "members": []})
            item["members"].append(ast)
        classes = []
        for class_id in sorted(grouped):
            item = grouped[class_id]
            members = sorted(item["members"], key=ast_key)
            classes.append({
                "class_id": class_id,
                "size": len(members),
                "representative": members[0],
                "outputs": item["outputs"],
            })

        separator = None
        if len(classes) > 1:
            for index, probe in enumerate(INTERACTION_PROBES):
                outputs = [item["outputs"][index] for item in classes]
                if len({repr(output) for output in outputs}) > 1:
                    separator = {
                        "probe_index": index,
                        "input": probe,
                        "class_output_digests": [digest(output) for output in outputs],
                    }
                    break
        return classes, separator

    def generation_analysis(self, state: Mapping[str, Any], task: Mapping[str, Any]) -> dict[str, Any]:
        candidates = generated_asts(state)
        by_size: dict[int, list[dict[str, Any]]] = {}
        checked: dict[int, int] = {}
        for ast in candidates:
            size = ast_size(ast)
            checked[size] = checked.get(size, 0) + 1
            try:
                ok = all(self.execute_ast(state, ast, e["input"]) == grid(e["output"])
                         for e in examples(task))
            except (KeyError, TypeError, ValueError, IndexError):
                ok = False
            if ok:
                by_size.setdefault(size, []).append(ast)
        minimum = min(by_size) if by_size else None
        survivors = by_size.get(minimum, []) if minimum is not None else []
        classes, separator = self._interaction_classes(state, survivors)
        representatives = [item["representative"] for item in classes]
        class_ids = [item["class_id"] for item in classes]
        return {
            "candidate_count": len(candidates),
            "candidate_count_by_size": {str(k): checked[k] for k in sorted(checked)},
            "complete_through_size": MAX_AST_SIZE,
            "minimum_size": minimum,
            "smaller_survivor_count": sum(len(v) for k, v in by_size.items() if minimum is not None and k < minimum),
            "minimum_survivors": survivors,
            "minimum_survivor_count": len(survivors),
            "minimum_syntactic_survivor_count": len(survivors),
            "minimum_interaction_class_count": len(classes),
            "minimum_interaction_class_sizes": [item["size"] for item in classes],
            "minimum_class_representatives": representatives,
            "interaction_class_ids": class_ids,
            "interaction_probe_manifest": INTERACTION_PROBE_MANIFEST,
            "separator_probe": separator,
            "version_space_id": digest({
                "probe_manifest": INTERACTION_PROBE_MANIFEST,
                "interaction_class_ids": class_ids,
            }),
        }

    def _envelope(self, obligation: Obligation, cls: str, diagnosis: str,
                  witness: Mapping[str, Any], constraint: Mapping[str, Any],
                  strength: str) -> dict[str, Any]:
        return ResidualEnvelope(
            cls, diagnosis, witness,
            digest({"active_language": witness.get("active_capabilities"), "old_roles": D4}),
            digest({"budget": obligation.budget, "task": obligation.target["task_sha256"]}),
            constraint, SUBSTRATE["substrate_id"], strength,
            {"task_sha256": obligation.target["task_sha256"]},
        ).to_mapping()

    def assess(self, state: Mapping[str, Any], obligation: Obligation) -> Evidence:
        claim = assessment_claim(state, obligation)
        target = obligation.target
        if target.get("admin") == "seed":
            name = target["name"]
            existing = [rid for rid, rec in state["capabilities"].items()
                        if rec["repair"]["payload"].get("body") == {"op": "d4", "name": name}]
            if existing:
                return Evidence("verified", claim, self.verifier_id, {"capability": existing[0]}, scope=self.name)
            return Evidence("unknown", claim, self.verifier_id, {"missing_seed": name},
                            {"class": "SEED_REQUIRED", "name": name}, self.name)

        task = target["task"]
        direct = self.solving_records(state, task)
        if direct:
            trace: list[str] = []
            self.execute(state, direct[0], examples(task)[0]["input"], trace)
            return Evidence("verified", claim, self.verifier_id,
                            {"executed": direct[0], "execution_trace": trace,
                             "training_examples": len(examples(task))}, scope=self.name)

        roles = self.role_survivors(state, task)
        active = sorted(state["capabilities"])
        if roles:
            witness = {"active_capabilities": active, "active_checked": len(active),
                       "role_checked": len(D4), "role_survivors": roles}
            constraint = {"change": "role-only", "callee": roles[0],
                          "new_input": "NonzeroBoundingObject"}
            return Evidence("unknown", claim, self.verifier_id, witness,
                            self._envelope(obligation, "ROLE_REQUALIFICATION_REQUIRED",
                                           "capability_failure", witness, constraint,
                                           "finite-exhaustive"), self.name)

        old_witness = {"active_capabilities": active, "active_checked": len(active),
                       "role_checked": len(D4), "active_survivors": [],
                       "role_survivors": [], "old_language_complete": True,
                       "old_language_cardinality": len(active) + len(D4)}
        analysis = self.generation_analysis(state, task)
        witness = {**old_witness, "generator": {k: v for k, v in analysis.items()
                                                 if k not in {"minimum_survivors", "minimum_class_representatives"}}}
        if analysis["minimum_size"] is None:
            constraint = {"remain": "UNKNOWN", "bounded_generator_complete": True}
            cls = "NO_GENERATED_REALIZATION"
            strength = "finite-exhaustive-inconclusive"
        elif analysis["minimum_interaction_class_count"] != 1:
            constraint = {
                "remain": "UNKNOWN",
                "minimum_size": analysis["minimum_size"],
                "version_space_id": analysis["version_space_id"],
                "interaction_class_count": analysis["minimum_interaction_class_count"],
                "next_distinguishing_probe": analysis["separator_probe"],
            }
            cls = "GENERATIVE_VERSION_SPACE_UNRESOLVED"
            strength = "finite-exhaustive-ambiguous-under-frozen-interaction-probes"
        else:
            constraint = {
                "change": "generated-language",
                "substrate_id": SUBSTRATE["substrate_id"],
                "minimum_size": analysis["minimum_size"],
                "version_space_id": analysis["version_space_id"],
                "interaction_class_count": 1,
                "interaction_probe_manifest": INTERACTION_PROBE_MANIFEST,
            }
            cls = "GENERATED_FORMATION_REQUIRED"
            strength = "finite-exhaustive-minimal-interaction-class"
        return Evidence("unknown", claim, self.verifier_id, old_witness,
                        self._envelope(obligation, cls, "language_failure", witness,
                                       constraint, strength), self.name)

    def propose(self, state: Mapping[str, Any], obligation: Obligation,
                residual: Mapping[str, Any]) -> Iterable[Repair]:
        cls = residual.get("class")
        if cls == "SEED_REQUIRED":
            yield Repair("capability", "seed-" + residual["name"],
                         {"body": {"op": "d4", "name": residual["name"]}},
                         self.name, contract=self.direct_contract)
        elif cls == "ROLE_REQUALIFICATION_REQUIRED":
            callee = residual["necessary_constraint"]["callee"]
            yield Repair("capability", "crop-role-" + callee,
                         {"body": {"op": "crop-call", "callee": callee}},
                         self.name, (callee,), self.role_contract)
        elif cls == "GENERATED_FORMATION_REQUIRED":
            analysis = self.generation_analysis(state, obligation.target["task"])
            if analysis["minimum_interaction_class_count"] == 1:
                ast = analysis["minimum_class_representatives"][0]
                yield Repair("capability", "generated-" + digest(ast)[:16],
                             {"body": {"op": "generated-ast", "ast": ast,
                                       "substrate_id": SUBSTRATE["substrate_id"]},
                              "minimum_size": ast_size(ast),
                              "version_space_id": analysis["version_space_id"]},
                             self.name, ast_dependencies(ast), self.generated_contract)

    def verify(self, state: Mapping[str, Any], obligation: Obligation, repair: Repair) -> Evidence:
        body = repair.payload.get("body", {})
        ok = False
        certificate: dict[str, Any] = {"accepted": False, "body": body}
        if obligation.target.get("admin") == "seed":
            ok = (body == {"op": "d4", "name": obligation.target["name"]}
                  and repair.contract == self.direct_contract and not repair.dependencies)
        elif body.get("op") == "crop-call":
            roles = self.role_survivors(state, obligation.target["task"])
            ok = (repair.contract == self.role_contract
                  and repair.dependencies == (body.get("callee"),)
                  and body.get("callee") in roles)
        elif body.get("op") == "generated-ast":
            analysis = self.generation_analysis(state, obligation.target["task"])
            ast = body.get("ast")
            ok = (repair.contract == self.generated_contract
                  and body.get("substrate_id") == SUBSTRATE["substrate_id"]
                  and analysis["minimum_interaction_class_count"] == 1
                  and ast == analysis["minimum_class_representatives"][0]
                  and repair.dependencies == ast_dependencies(ast)
                  and analysis["smaller_survivor_count"] == 0)
            certificate.update({
                "substrate_id": SUBSTRATE["substrate_id"],
                "candidate_count": analysis["candidate_count"],
                "candidate_count_by_size": analysis["candidate_count_by_size"],
                "minimum_size": analysis["minimum_size"],
                "smaller_survivor_count": analysis["smaller_survivor_count"],
                "minimum_survivor_count": analysis["minimum_survivor_count"],
                "minimum_interaction_class_count": analysis["minimum_interaction_class_count"],
                "interaction_probe_manifest": analysis["interaction_probe_manifest"],
                "separator_probe": analysis["separator_probe"],
                "version_space_id": analysis["version_space_id"],
            })
        certificate["accepted"] = ok
        return Evidence("verified" if ok else "refuted", repair.id, self.verifier_id,
                        certificate, scope=self.name)

    def attach(self, state: Mapping[str, Any], repair: Repair,
               evidence: Evidence) -> Mapping[str, Any]:
        if evidence.verdict != "verified" or not evidence.certificate.get("accepted"):
            raise ValueError("unverified prospective capability")
        return {"executable": repair.payload["body"], "semantics": "exact generated grid replay"}


def validate_task_schema(task: Any) -> bool:
    """Route-neutral eligibility: inspect declared JSON fields and resource bounds only."""
    if not isinstance(task, Mapping) or not {"train", "test"} <= set(task):
        return False
    if not isinstance(task["train"], list) or not isinstance(task["test"], list):
        return False
    if not task["train"] or not task["test"] or len(task["train"]) > 10 or len(task["test"]) > 10:
        return False
    for part in ("train", "test"):
        for example in task[part]:
            if not isinstance(example, Mapping) or not {"input", "output"} <= set(example):
                return False
            for field in ("input", "output"):
                value = example[field]
                if (not isinstance(value, list) or not value or len(value) > 30
                        or any(not isinstance(row, list) or not row or len(row) > 30 for row in value)
                        or len({len(row) for row in value}) != 1
                        or any(not isinstance(x, int) or x < 0 or x > 9 for row in value for x in row)):
                    return False
    return True


def select_stream(root: Path, nonce: str) -> dict[str, Any]:
    rows = []
    for path in sorted((root / ARC_PATH).glob("*.json")):
        raw = path.read_bytes()
        task = json.loads(raw)
        if validate_task_schema(task):
            public = {"train": task["train"],
                      "test": [{"input": example["input"]} for example in task["test"]]}
            rows.append({"task_id": path.stem, "task_sha256": sha256(raw).hexdigest(),
                         "task": public})
    rows.sort(key=lambda row: digest({"nonce": nonce, "task_sha256": row["task_sha256"]}))
    body = {"schema": "prospective-route-neutral-stream/v1",
            "external_repository": ARC_REPOSITORY, "external_commit": ARC_COMMIT,
            "external_path": ARC_PATH, "selection_nonce": nonce,
            "eligibility": "ARC JSON schema, grid/color/resource bounds only",
            "selection": "complete eligible pool in nonce-hash order",
            "route_labels_present": False, "tasks": rows}
    return {**body, "stream_digest": digest(body)}


def freeze_state(path: Path) -> dict[str, Any]:
    if path.exists():
        path.unlink()
    store = EvidenceStore(path)
    adapter = ProspectiveARCAdapter()
    ids = []
    for name in D4:
        result = Developer(store, adapter).run(
            Obligation(adapter.name, {"admin": "seed", "name": name}, 1, "method"))
        if result.verdict != "verified" or len(result.retained) != 1:
            raise RuntimeError("seed admission failed")
        ids.extend(result.retained)
    body = {"schema": "prospective-initial-state/v1", "seed_ids": ids,
            "state_id": digest(store.state()), "ledger_digest": digest(store.events()),
            "substrate": SUBSTRATE}
    store.close()
    return {**body, "digest": digest(body)}


def task_trace(state: Mapping[str, Any], task: Mapping[str, Any],
               adapter: ProspectiveARCAdapter) -> dict[str, Any]:
    ids = adapter.solving_records(state, task)
    if not ids:
        return {"capability": None, "outputs": [], "execution_traces": []}
    rid = ids[0]
    outputs, traces = [], []
    for example in task.get("test", []):
        trace: list[str] = []
        outputs.append(adapter.execute(state, rid, example["input"], trace))
        traces.append(trace)
    return {"capability": rid, "outputs": outputs, "execution_traces": traces}


def _protected_replay(state: Mapping[str, Any], protected: list[Mapping[str, Any]],
                      adapter: ProspectiveARCAdapter) -> dict[str, Any]:
    rows = []
    for row in protected:
        survivors = adapter.solving_records(state, row["task"])
        rows.append({"task_id": row["task_id"], "verified": bool(survivors),
                     "capability": survivors[0] if survivors else None})
    return {"count": len(rows), "all_preserved": all(x["verified"] for x in rows),
            "digest": digest(rows)}


def develop_stream(stream: Mapping[str, Any], state_path: Path) -> dict[str, Any]:
    raw_stream = json.dumps(stream, sort_keys=True)
    if any(label in raw_stream for label in ('"predicted_route"', '"ground_truth_route"', '"chain"')):
        raise ValueError("administration leakage")
    adapter = ProspectiveARCAdapter()
    results: list[dict[str, Any]] = []
    protected: list[Mapping[str, Any]] = []
    for index, row in enumerate(stream["tasks"]):
        store = EvidenceStore(state_path)
        before = deepcopy(store.state())
        events_before = len(store.events())
        t0, c0 = time.perf_counter(), time.process_time()
        obligation = Obligation(adapter.name, row, 1, "method")
        cold = adapter.assess(before, obligation)
        result = Developer(store, adapter).run(obligation)
        after = deepcopy(store.state())
        trace = task_trace(after, row["task"], adapter)
        generated = [rid for rid in result.retained
                     if after["capabilities"][rid]["repair"]["payload"].get("body", {}).get("op") == "generated-ast"]
        preservation = _protected_replay(after, protected, adapter)
        if result.verdict == "verified":
            protected.append(row)
        events_after = len(store.events())
        store.close()

        restart = EvidenceStore(state_path)
        restarted = Developer(restart, adapter).run(Obligation(adapter.name, row, 0, "method"))
        restart_trace = task_trace(restart.state(), row["task"], adapter)
        restart.close()
        route = ("REUSE" if result.verdict == "verified" and not result.retained else
                 "EXAPTATION" if result.retained and not generated else
                 "EXPANSION" if generated else "UNKNOWN")
        generator = ((cold.residual or {}).get("verifier_certified_witness", {})
                     .get("generator", {})) if cold.residual else {}
        results.append({
            "stream_index": index, "task_id": row["task_id"], "task_sha256": row["task_sha256"],
            "decision_sequence": index, "pre_state_id": digest(before), "post_state_id": digest(after),
            "events_before": events_before, "events_after": events_after,
            "cold_verdict": cold.verdict, "residual": cold.residual,
            "predicted_route": route, "warm_verdict": result.verdict,
            "admissions": list(result.retained), "generated_admissions": generated,
            "admitted_records": {rid: after["capabilities"][rid] for rid in result.retained},
            "execution": trace, "restart_verdict": restarted.verdict,
            "restart_execution": restart_trace, "preservation": preservation,
            "verifier_identity": adapter.verifier_id, "substrate_id": SUBSTRATE["substrate_id"],
            "cost": {"C_construction": len(result.retained),
                     "C_verification": 2 * len(result.retained) + 1,
                     "C_activation": len(result.retained),
                     "C_execution": len(examples(row["task"])) * max(1, len(after["capabilities"])),
                     "C_memory": len(json.dumps(after, separators=(",", ":"))),
                     "C_recovery": 1, "C_external_interaction": len(examples(row["task"])),
                     "candidate_evaluations": generator.get("candidate_count", 0),
                     "verifier_calls": 2 * len(result.retained) + 1,
                     "wall_seconds": time.perf_counter() - t0,
                     "cpu_seconds": time.process_time() - c0,
                     "peak_rss_kb": resource.getrusage(resource.RUSAGE_SELF).ru_maxrss},
        })
    final = EvidenceStore(state_path)
    final_events, final_state = final.events(), final.state()
    final.close()
    body = {"schema": "prospective-development-decisions/v1",
            "stream_digest": stream["stream_digest"], "labels_seen": False,
            "hidden_outputs_seen": False, "results": results,
            "final_state_id": digest(final_state), "final_events": final_events}
    return {**body, "decisions_digest": digest(body)}


def validate_external(root: Path) -> dict[str, Any]:
    commit = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=root, text=True).strip()
    if commit != ARC_COMMIT:
        raise ValueError("wrong ARC commit")
    identities = {path.stem: sha256(path.read_bytes()).hexdigest()
                  for path in sorted((root / ARC_PATH).glob("*.json"))}
    if len(identities) != 400:
        raise ValueError("unexpected ARC evaluation corpus size")
    return {"repository": ARC_REPOSITORY, "commit": commit, "path": ARC_PATH,
            "file_count": len(identities), "corpus_digest": digest(identities), "files": identities}


def _store_from_events(path: Path, events: Iterable[Mapping[str, Any]]) -> EvidenceStore:
    store = EvidenceStore(path)
    for event in events:
        store.append(event)
    return store


def _ancestors(state: Mapping[str, Any], rid: str) -> set[str]:
    out: set[str] = set()
    stack = [rid]
    while stack:
        current = stack.pop()
        for parent in state["capabilities"][current]["repair"]["dependencies"]:
            if parent not in out:
                out.add(parent)
                stack.append(parent)
    return out


def _hidden_execution(state: Mapping[str, Any], rid: str, task: Mapping[str, Any], oracle: Any) -> dict[str, Any]:
    outputs, traces = [], []
    for example in task["test"]:
        trace: list[str] = []
        outputs.append(oracle.execute(state, rid, example["input"], trace))
        traces.append(trace)
    expected = [grid(example["output"]) for example in task["test"]]
    return {"outputs": outputs, "expected": expected, "traces": traces,
            "verified": outputs == expected}


def evaluate(stream: Mapping[str, Any], decisions: Mapping[str, Any], freeze: Mapping[str, Any],
             external_root: Path, work: Path) -> dict[str, Any]:
    from . import prospective_oracle as oracle

    if decisions["stream_digest"] != stream["stream_digest"]:
        raise ValueError("stream mismatch")
    if len(stream["tasks"]) != len(decisions["results"]):
        raise ValueError("decision count mismatch")
    external: dict[str, tuple[str, Any]] = {}
    for path in (external_root / ARC_PATH).glob("*.json"):
        external[path.stem] = (sha256(path.read_bytes()).hexdigest(), json.loads(path.read_text()))

    expected_state = freeze["state"]["state_id"]
    checked: list[dict[str, Any]] = []
    generated_events: list[tuple[int, str]] = []
    for index, (source, decision) in enumerate(zip(stream["tasks"], decisions["results"])):
        if decision["decision_sequence"] != index or source["task_sha256"] != decision["task_sha256"]:
            raise ValueError("decision chronology mismatch")
        if decision["pre_state_id"] != expected_state:
            raise ValueError("state chain mismatch")
        file_hash, full = external[source["task_id"]]
        if file_hash != source["task_sha256"]:
            raise ValueError("external task identity mismatch")
        public_expected = {"train": full["train"], "test": [{"input": x["input"]} for x in full["test"]]}
        if public_expected != source["task"]:
            raise ValueError("hidden output or source mismatch")
        admission_checks = []
        for rid in decision["generated_admissions"]:
            record = decision["admitted_records"][rid]
            pre_state = oracle.state_at(decisions["final_events"], decision["events_before"])
            analysis = oracle.analyze(pre_state, full)
            ast = record["repair"]["payload"]["body"]["ast"]
            valid = (analysis["minimum_survivor_count"] == 1
                     and analysis["minimum_survivors"][0] == ast
                     and analysis["smaller_survivor_count"] == 0
                     and record["repair"]["dependencies"] == list(oracle.dependencies(ast)))
            admission_checks.append({"capability": rid, "valid": valid, "analysis": analysis,
                                     "ast": ast, "dependencies": record["repair"]["dependencies"]})
            generated_events.append((index, rid))
        state = oracle.state_at(decisions["final_events"], decision["events_after"])
        rid = decision["execution"]["capability"]
        hidden = (_hidden_execution(state, rid, full, oracle) if rid else
                  {"outputs": [], "expected": [grid(x["output"]) for x in full["test"]],
                   "traces": [], "verified": False})
        checked.append({"stream_index": index, "task_id": source["task_id"],
                        "route": decision["predicted_route"], "warm_verdict": decision["warm_verdict"],
                        "hidden": hidden, "generated": admission_checks,
                        "preservation_training": decision["preservation"]})
        expected_state = decision["post_state_id"]

    chains = []
    for a_index, g1 in generated_events:
        for b_index, g2 in generated_events:
            if b_index <= a_index:
                continue
            b_state = oracle.state_at(decisions["final_events"], decisions["results"][b_index]["events_after"])
            if g1 not in _ancestors(b_state, g2):
                continue
            for c_index in range(b_index + 1, len(stream["tasks"])):
                c_dec = decisions["results"][c_index]
                if c_dec["admissions"] or c_dec["warm_verdict"] != "verified":
                    continue
                traces = c_dec["restart_execution"]["execution_traces"]
                if not traces or not all(g2 in trace and g1 in trace and trace.index(g2) < trace.index(g1)
                                         for trace in traces):
                    continue
                control = evaluate_chain(stream, decisions, external, a_index, g1, b_index, g2,
                                         c_index, work, oracle)
                chains.append(control)
                if control["passes"]:
                    break
            if any(chain["passes"] for chain in chains):
                break
        if any(chain["passes"] for chain in chains):
            break

    qualifying = next((chain for chain in chains if chain["passes"]), None)
    if qualifying:
        outcome = "PROSPECTIVE_CONTINUATION_GENESIS_V1_PASS"
    elif not generated_events:
        outcome = "UNKNOWN_PROSPECTIVE_CONTINUATION_COVERAGE"
    elif any(not item["valid"] for row in checked for item in row["generated"]):
        outcome = "UNKNOWN_GENERATION_BOUNDARY"
    else:
        outcome = "UNKNOWN_PROSPECTIVE_CONTINUATION_COVERAGE"
    body = {"schema": "prospective-continuation-evaluation/v1", "outcome": outcome,
            "external_identity": validate_external(external_root),
            "stream_digest": stream["stream_digest"], "decisions_digest": decisions["decisions_digest"],
            "task_count": len(checked), "generated_count": len(generated_events),
            "checked_tasks": checked, "candidate_chains": chains,
            "qualifying_chain": qualifying,
            "limitations": ["finite supplied AST substrate", "ARC training examples guide generation",
                            "Python operational qualification", "no human blinding",
                            "no unrestricted grammar invention"]}
    return {**body, "evidence_digest": digest(body)}


def evaluate_chain(stream: Mapping[str, Any], decisions: Mapping[str, Any],
                   external: Mapping[str, tuple[str, Any]], a_index: int, g1: str,
                   b_index: int, g2: str, c_index: int, work: Path, oracle: Any) -> dict[str, Any]:
    rows = stream["tasks"]
    events = decisions["final_events"]
    a_dec, b_dec, c_dec = (decisions["results"][i] for i in (a_index, b_index, c_index))
    state_c = oracle.state_at(events, c_dec["events_after"])
    q_a, q_b, q_c = (external[rows[i]["task_id"]][1] for i in (a_index, b_index, c_index))
    actual = _hidden_execution(state_c, g2, q_c, oracle)
    ancestors = _ancestors(state_c, g2)
    seed_ancestors = [rid for rid in ancestors if state_c["capabilities"][rid]["repair"]["payload"].get("body", {}).get("op") == "d4"]
    unrelated = next((rid for rid, rec in state_c["capabilities"].items()
                      if rec["repair"]["payload"].get("body", {}).get("op") == "d4"
                      and rid not in ancestors), None)

    def store_at(label: str, count: int) -> EvidenceStore:
        path = work / f"{label}-{a_index}-{b_index}-{c_index}.sqlite"
        if path.exists():
            path.unlink()
        return _store_from_events(path, events[:count])

    removed_store = store_at("remove", c_dec["events_after"])
    removed_ids = removed_store.revoke(g1, "prospective ancestor ablation")
    removed_result = Developer(removed_store, ProspectiveARCAdapter()).run(
        Obligation(ProspectiveARCAdapter.name, rows[c_index], 0, "method"))
    removed_state = removed_store.state()
    removed_store.close()

    restored_store = store_at("restore", c_dec["events_after"])
    restored_ids = restored_store.revoke(g1, "restoration control")
    admit_by_id = {event["record"]["id"]: event for event in events[:c_dec["events_after"]]
                   if event["type"] == "admit"}
    for rid in restored_ids:
        if rid in admit_by_id:
            restored_store.append(admit_by_id[rid])
    restored = Developer(restored_store, ProspectiveARCAdapter()).run(
        Obligation(ProspectiveARCAdapter.name, rows[c_index], 0, "method"))
    restored_state = restored_store.state()
    restored_store.close()

    ancestor_result = None
    if seed_ancestors:
        ancestor_store = store_at("ancestor", c_dec["events_after"])
        ancestor_removed = ancestor_store.revoke(seed_ancestors[0], "necessary ancestor control")
        ancestor_result = Developer(ancestor_store, ProspectiveARCAdapter()).run(
            Obligation(ProspectiveARCAdapter.name, rows[c_index], 0, "method"))
        ancestor_store.close()
    else:
        ancestor_removed = ()

    unrelated_result = None
    if unrelated:
        unrelated_store = store_at("unrelated", c_dec["events_after"])
        unrelated_removed = unrelated_store.revoke(unrelated, "unrelated control")
        unrelated_result = Developer(unrelated_store, ProspectiveARCAdapter()).run(
            Obligation(ProspectiveARCAdapter.name, rows[c_index], 0, "method"))
        unrelated_store.close()
    else:
        unrelated_removed = ()

    # Same-size and wrong-operation controls alter only the executable body in a
    # copied observation state; no altered record is admitted to the ledger.
    sham_state = deepcopy(state_c)
    g1_ast = sham_state["capabilities"][g1]["repair"]["payload"]["body"]["ast"]
    alternatives = [ast for ast in oracle.enumerate_asts(oracle.state_at(events, a_dec["events_before"]))
                    if oracle.size(ast) == oracle.size(g1_ast) and ast != g1_ast]
    sham_ast = alternatives[0] if alternatives else {"op": "input"}
    sham_state["capabilities"][g1]["repair"]["payload"]["body"]["ast"] = sham_ast
    sham_state["capabilities"][g1]["repair"]["dependencies"] = list(oracle.dependencies(sham_ast))
    sham = _hidden_execution(sham_state, g2, q_c, oracle)
    wrong_state = deepcopy(state_c)
    wrong_ast = deepcopy(g1_ast)
    wrong_ast["op"] = next(op for op in FORM_OPS if op != g1_ast["op"])
    wrong_state["capabilities"][g1]["repair"]["payload"]["body"]["ast"] = wrong_ast
    wrong = _hidden_execution(wrong_state, g2, q_c, oracle)

    # Exact matched cold replay starts from the pre-qA ledger and sees the same
    # already-fixed suffix in the same order, with qA itself omitted.
    cold_store = store_at("cold", a_dec["events_before"])
    cold_rows = []
    cold_adapter = ProspectiveARCAdapter()
    for index in range(b_index, c_index + 1):
        result = Developer(cold_store, cold_adapter).run(
            Obligation(cold_adapter.name, rows[index], 1, "method"))
        cold_rows.append({"stream_index": index, "verdict": result.verdict,
                          "admissions": list(result.retained),
                          "execution": task_trace(cold_store.state(), rows[index]["task"], cold_adapter)})
        cold_store.close()
        cold_store = EvidenceStore(cold_store.path)
    cold_c = cold_rows[-1]
    cold_store.close()

    final_state = oracle.state_at(events, c_dec["events_after"])
    protected = []
    for index in range(a_index):
        if decisions["results"][index]["warm_verdict"] == "verified":
            task = external[rows[index]["task_id"]][1]
            protected.append({"task_id": rows[index]["task_id"],
                              "verified": oracle.any_solves(final_state, task)})
    preservation = {"count": len(protected), "all_preserved": all(x["verified"] for x in protected),
                    "digest": digest(protected)}

    b_record = state_c["capabilities"][g2]
    actual_vs_cold = (cold_rows[0]["admissions"] != b_dec["admissions"]
                      or cold_c["verdict"] != c_dec["restart_verdict"]
                      or cold_c["execution"]["capability"] != c_dec["restart_execution"]["capability"])
    controls = {
        "restart": c_dec["restart_verdict"] == "verified",
        "exact_g1_removal": removed_result.verdict != "verified" and g2 in removed_ids,
        "recursive_removed_ids": list(removed_ids),
        "restoration": restored.verdict == "verified" and g1 in restored_state["capabilities"] and g2 in restored_state["capabilities"],
        "necessary_ancestor_removal": bool(seed_ancestors and ancestor_result and ancestor_result.verdict != "verified" and g2 in ancestor_removed),
        "unrelated_removal": bool(unrelated_result and unrelated_result.verdict == "verified" and g2 not in unrelated_removed),
        "same_size_sham": not sham["verified"], "wrong_operation": not wrong["verified"],
        "fixed_policy": cold_rows[0]["admissions"] != b_dec["admissions"],
        "raw_history_without_admission": g2 not in oracle.state_at(events, a_dec["events_before"])["capabilities"],
        "matched_cold_difference": actual_vs_cold,
        "preservation": preservation["all_preserved"],
    }
    passes = (actual["verified"] and b_record["repair"]["dependencies"]
              and g1 in _ancestors(state_c, g2) and seed_ancestors
              and all(controls.values()) and b_dec["generated_admissions"] == [g2]
              and not c_dec["admissions"] and c_dec["restart_verdict"] == "verified")
    return {
        "stage_a": {"index": a_index, "task_id": rows[a_index]["task_id"], "G1": g1,
                    "ast": state_c["capabilities"][g1]["repair"]["payload"]["body"]["ast"],
                    "dependencies": state_c["capabilities"][g1]["repair"]["dependencies"],
                    "hidden_verified": _hidden_execution(state_c, g1, q_a, oracle)["verified"]},
        "stage_b": {"index": b_index, "task_id": rows[b_index]["task_id"], "G2": g2,
                    "ast": b_record["repair"]["payload"]["body"]["ast"],
                    "dependencies": b_record["repair"]["dependencies"],
                    "hidden_verified": _hidden_execution(state_c, g2, q_b, oracle)["verified"]},
        "stage_c": {"index": c_index, "task_id": rows[c_index]["task_id"],
                    "capability": c_dec["restart_execution"]["capability"],
                    "execution_traces": actual["traces"], "hidden_verified": actual["verified"],
                    "zero_new_acquisition": not c_dec["admissions"]},
        "frozen_suffix": {"start": b_index, "end": c_index,
                          "task_ids": [rows[i]["task_id"] for i in range(b_index, c_index + 1)]},
        "actual_future": {"qB_admissions": b_dec["admissions"], "qC_verdict": c_dec["restart_verdict"],
                          "qC_capability": c_dec["restart_execution"]["capability"]},
        "cold_counterfactual": {"rows": cold_rows},
        "controls": controls, "preservation": preservation,
        "sham_ast": sham_ast, "wrong_ast": wrong_ast, "passes": passes,
    }


def freeze_manifest(root: Path, external: Path, state: Path,
                    source_commit: str, nonce: str) -> dict[str, Any]:
    if external.exists():
        raise ValueError("external path present before freeze")
    actual = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=root, text=True).strip()
    if actual != source_commit:
        raise ValueError("wrong source commit")
    subprocess.run(["git", "merge-base", "--is-ancestor", V4_SOURCE, source_commit], cwd=root, check=True)
    frozen = freeze_state(state)
    files = {str(path.relative_to(root)): sha256(path.read_bytes()).hexdigest()
             for path in sorted((root / "open_development").rglob("*.py"))}
    workflow = root / ".github/workflows/prospective-continuation-genesis-v1.yml"
    files[str(workflow.relative_to(root))] = sha256(workflow.read_bytes()).hexdigest()
    body = {"schema": "prospective-continuation-freeze/v1", "v4_source": V4_SOURCE,
            "v4_scientific_freeze": V4_SCIENTIFIC_FREEZE,
            "v4_scientific_run": V4_SCIENTIFIC_RUN,
            "v4_authority_run": V4_AUTHORITY_RUN,
            "v4_authority_artifact": V4_AUTHORITY_ARTIFACT,
            "v4_authority_artifact_sha256": V4_AUTHORITY_ARTIFACT_SHA256,
            "v4_authority_evidence_digest": V4_AUTHORITY_EVIDENCE_DIGEST,
            "source_commit": source_commit,
            "nonce": nonce, "external_absent": True, "files": files,
            "substrate": SUBSTRATE, "state": frozen}
    return {**body, "freeze_digest": digest(body)}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("stage", choices=("freeze", "admin", "develop", "evaluate"))
    parser.add_argument("--source-commit", required=True)
    parser.add_argument("--nonce", required=True)
    parser.add_argument("--root", type=Path, default=Path.cwd())
    parser.add_argument("--external", type=Path, default=Path("external"))
    parser.add_argument("--state", type=Path, default=Path("prospective-state.sqlite"))
    parser.add_argument("--freeze", type=Path, default=Path("prospective-freeze.json"))
    parser.add_argument("--stream", type=Path, default=Path("prospective-stream.json"))
    parser.add_argument("--decisions", type=Path, default=Path("prospective-decisions.json"))
    parser.add_argument("--evaluation", type=Path, default=Path("prospective-evaluation.json"))
    args = parser.parse_args()
    if args.stage == "freeze":
        out = freeze_manifest(args.root, args.external, args.state, args.source_commit, args.nonce)
        args.freeze.write_text(json.dumps(out, indent=2) + "\n")
        print("PROSPECTIVE_CONTINUATION_FREEZE", out["freeze_digest"])
        return
    frozen = json.loads(args.freeze.read_text())
    if (frozen["source_commit"] != args.source_commit or frozen["nonce"] != args.nonce
            or frozen["v4_source"] != V4_SOURCE):
        raise ValueError("freeze identity mismatch")
    if frozen["freeze_digest"] != digest({k: v for k, v in frozen.items() if k != "freeze_digest"}):
        raise ValueError("tampered freeze")
    if args.stage == "admin":
        identity = validate_external(args.external)
        out = select_stream(args.external, args.nonce)
        out["corpus_identity"] = identity
        out["stream_digest"] = digest({k: v for k, v in out.items() if k != "stream_digest"})
        args.stream.write_text(json.dumps(out, indent=2) + "\n")
        print("PROSPECTIVE_ROUTE_NEUTRAL_STREAM", len(out["tasks"]), out["stream_digest"])
        return
    stream = json.loads(args.stream.read_text())
    if (stream["stream_digest"] != digest({k: v for k, v in stream.items() if k != "stream_digest"})
            or stream["selection_nonce"] != args.nonce):
        raise ValueError("tampered stream")
    if args.stage == "develop":
        out = develop_stream(stream, args.state)
        args.decisions.write_text(json.dumps(out, indent=2) + "\n")
        print("PROSPECTIVE_DEVELOPER_DECISIONS", len(out["results"]), out["decisions_digest"])
        return
    identity = validate_external(args.external)
    if identity != stream.get("corpus_identity"):
        raise ValueError("evaluator corpus mismatch")
    decisions = json.loads(args.decisions.read_text())
    if decisions["decisions_digest"] != digest({k: v for k, v in decisions.items() if k != "decisions_digest"}):
        raise ValueError("tampered decisions")
    with tempfile.TemporaryDirectory() as tmp:
        out = evaluate(stream, decisions, frozen, args.external, Path(tmp))
    args.evaluation.write_text(json.dumps(out, indent=2) + "\n")
    print(out["outcome"], out["task_count"], out["generated_count"], out["evidence_digest"])


if __name__ == "__main__":
    main()
