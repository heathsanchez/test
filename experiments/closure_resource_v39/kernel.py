from __future__ import annotations
from typing import Any, Callable

from basis import PartialGraph, Signature

Verifier = Callable[[Signature, int, Signature], bool]


class Kernel:
    @staticmethod
    def _validate(graph: PartialGraph) -> dict[str, Any] | None:
        states = tuple(tuple(s) for s in graph.states)
        if not states or len(set(states)) != len(states):
            return {"status": "INVALID_STATE_SET"}
        if tuple(graph.initial) not in set(states):
            return {"status": "INVALID_INITIAL_STATE"}
        try:
            edge_map = graph.edge_map()
        except ValueError:
            return {"status": "INVALID_WARRANTED_EDGE_SET"}
        state_set = set(states)
        for (src, sym), dst in edge_map.items():
            if src not in state_set or dst not in state_set or sym not in (0,1):
                return {"status": "INVALID_WARRANTED_EDGE_SET"}
        return None

    @staticmethod
    def _uniform_spanning_cycle(graph: PartialGraph) -> dict[str, Any] | None:
        edge_map = graph.edge_map()
        states = set(tuple(s) for s in graph.states)
        n = len(states)
        found = []

        for symbol in (0,1):
            q = tuple(graph.initial)
            order = []
            seen = set()
            ok = True
            for _ in range(n):
                if q in seen:
                    ok = False
                    break
                seen.add(q)
                order.append(q)
                nxt = edge_map.get((q, symbol))
                if nxt is None:
                    ok = False
                    break
                q = tuple(nxt)
            if ok and q == tuple(graph.initial) and seen == states:
                found.append((symbol, tuple(order)))

        if len(found) != 1:
            return None

        symbol, order = found[0]
        position = {q:i for i,q in enumerate(order)}
        return {
            "cycle_symbol": int(symbol),
            "alternate_symbol": int(1-symbol),
            "cycle_order": order,
            "position": position,
        }

    @staticmethod
    def inspect(graph: PartialGraph) -> dict[str, Any]:
        invalid = Kernel._validate(graph)
        if invalid:
            return invalid

        cycle = Kernel._uniform_spanning_cycle(graph)
        if cycle is None:
            return {
                "status": "VERIFIED_PARTIAL_NO_CLOSURE",
                "spanning_cycle": False,
                "compiled_rule": False,
                "compiled_displacement": None,
                "seed_edge_count": 0,
            }

        edge_map = graph.edge_map()
        order = cycle["cycle_order"]
        position = cycle["position"]
        alt = cycle["alternate_symbol"]
        n = len(order)

        displacements = []
        seed_sources = []
        for src in order:
            dst = edge_map.get((src, alt))
            if dst is None:
                continue
            delta = (position[tuple(dst)] - position[src]) % n
            displacements.append(int(delta))
            seed_sources.append(src)

        compiled = (
            len(set(seed_sources)) >= 2 and
            len(set(displacements)) == 1
        )
        return {
            "status": "VERIFIED_CLOSURE_FRAME",
            "spanning_cycle": True,
            "cycle_symbol": cycle["cycle_symbol"],
            "alternate_symbol": alt,
            "cycle_order": [list(q) for q in order],
            "cycle_size": n,
            "seed_edge_count": len(seed_sources),
            "seed_displacements": displacements,
            "compiled_rule": compiled,
            "compiled_displacement": (
                int(displacements[0]) if compiled else None
            ),
        }

    @staticmethod
    def _baseline_complete_with_frame(
        graph: PartialGraph,
        verifier: Verifier,
        cycle: dict[str, Any],
    ) -> dict[str, Any]:
        edge_map = dict(graph.edge_map())
        order = cycle["cycle_order"]
        position = cycle["position"]
        alt = cycle["alternate_symbol"]
        n = len(order)
        calls = 0
        accepted = []

        for src in order:
            key = (src, alt)
            if key in edge_map:
                continue
            src_pos = position[src]
            found = None
            for delta in range(n):
                dst = order[(src_pos + delta) % n]
                calls += 1
                if bool(verifier(src, alt, dst)):
                    found = dst
                    accepted.append((src, alt, dst))
                    break
            if found is None:
                return {
                    "status": "VERIFIER_INCONSISTENT",
                    "verifier_calls": calls,
                    "final_edge_map": edge_map,
                }
            edge_map[key] = found

        return {
            "status": "VERIFIED_COMPLETE",
            "verifier_calls": calls,
            "accepted_edges": accepted,
            "final_edge_map": edge_map,
        }

    @staticmethod
    def _baseline_complete_without_frame(
        graph: PartialGraph,
        verifier: Verifier,
    ) -> dict[str, Any]:
        edge_map = dict(graph.edge_map())
        states = tuple(sorted((tuple(s) for s in graph.states), key=repr))
        calls = 0
        accepted = []

        for src in states:
            for sym in (0,1):
                key = (src,sym)
                if key in edge_map:
                    continue
                found = None
                for dst in states:
                    calls += 1
                    if bool(verifier(src,sym,dst)):
                        found = dst
                        accepted.append((src,sym,dst))
                        break
                if found is None:
                    return {
                        "status": "VERIFIER_INCONSISTENT",
                        "verifier_calls": calls,
                        "final_edge_map": edge_map,
                    }
                edge_map[key] = found

        return {
            "status": "VERIFIED_COMPLETE",
            "verifier_calls": calls,
            "accepted_edges": accepted,
            "final_edge_map": edge_map,
        }

    def complete(
        self,
        graph: PartialGraph,
        verifier: Verifier,
        *,
        closure_enabled: bool = True,
    ) -> dict[str, Any]:
        invalid = self._validate(graph)
        if invalid:
            return invalid

        cycle = self._uniform_spanning_cycle(graph)
        inspection = self.inspect(graph)

        if cycle is None:
            baseline = self._baseline_complete_without_frame(graph, verifier)
            return {
                **baseline,
                "spanning_cycle": False,
                "compiled_rule": False,
                "compiled_displacement": None,
                "rule_revoked": False,
                "prediction_attempts": 0,
                "prediction_accepts": 0,
                "prediction_rejections": 0,
                "used_closure_resource": False,
            }

        if not closure_enabled or not inspection.get("compiled_rule"):
            baseline = self._baseline_complete_with_frame(graph, verifier, cycle)
            return {
                **baseline,
                "spanning_cycle": True,
                "compiled_rule": bool(inspection.get("compiled_rule")),
                "compiled_displacement": inspection.get("compiled_displacement"),
                "rule_revoked": False,
                "prediction_attempts": 0,
                "prediction_accepts": 0,
                "prediction_rejections": 0,
                "used_closure_resource": False,
            }

        edge_map = dict(graph.edge_map())
        order = cycle["cycle_order"]
        position = cycle["position"]
        alt = cycle["alternate_symbol"]
        n = len(order)
        delta = int(inspection["compiled_displacement"])

        calls = 0
        prediction_attempts = 0
        prediction_accepts = 0
        prediction_rejections = 0
        rejected_edges = []
        accepted_edges = []
        rule_active = True
        rule_revoked = False

        for src in order:
            key = (src,alt)
            if key in edge_map:
                continue

            src_pos = position[src]
            tested = set()
            found = None

            if rule_active:
                predicted = order[(src_pos + delta) % n]
                tested.add(predicted)
                calls += 1
                prediction_attempts += 1
                if bool(verifier(src,alt,predicted)):
                    found = predicted
                    prediction_accepts += 1
                    accepted_edges.append((src,alt,predicted))
                else:
                    prediction_rejections += 1
                    rejected_edges.append((src,alt,predicted))
                    rule_active = False
                    rule_revoked = True

            if found is None:
                for local_delta in range(n):
                    dst = order[(src_pos + local_delta) % n]
                    if dst in tested:
                        continue
                    calls += 1
                    if bool(verifier(src,alt,dst)):
                        found = dst
                        accepted_edges.append((src,alt,dst))
                        break

            if found is None:
                return {
                    "status": "VERIFIER_INCONSISTENT",
                    "verifier_calls": calls,
                    "spanning_cycle": True,
                    "compiled_rule": True,
                    "compiled_displacement": delta,
                    "rule_revoked": rule_revoked,
                    "prediction_attempts": prediction_attempts,
                    "prediction_accepts": prediction_accepts,
                    "prediction_rejections": prediction_rejections,
                    "rejected_edges": rejected_edges,
                    "final_edge_map": edge_map,
                    "used_closure_resource": True,
                }

            edge_map[key] = found

        return {
            "status": "VERIFIED_COMPLETE",
            "verifier_calls": calls,
            "spanning_cycle": True,
            "compiled_rule": True,
            "compiled_displacement": delta,
            "rule_revoked": rule_revoked,
            "retained_compiled_rule": not rule_revoked,
            "prediction_attempts": prediction_attempts,
            "prediction_accepts": prediction_accepts,
            "prediction_rejections": prediction_rejections,
            "rejected_edges": rejected_edges,
            "accepted_edges": accepted_edges,
            "final_edge_map": edge_map,
            "used_closure_resource": True,
        }
