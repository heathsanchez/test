#!/usr/bin/env python3
"""Post-freeze V8 ladder: can RELATION + COMPOSE regenerate V7?"""
from __future__ import annotations

from typing import Any, Dict, Mapping, Sequence, Tuple

from basis import (
    BIT,
    BasisConfig,
    Relation,
    equivalence_classes,
    is_equivalence_relation,
)
from kernel import ProtoKernel


def exact_function(outputs: Sequence[int], label: str):
    target = tuple(int(x) for x in outputs)

    def evaluate(r: Relation) -> Dict[str, Any]:
        if not r.is_function():
            return {
                "accepted": False,
                "protected_ok": True,
                "loss": len(target) + 1,
                "witness": {"label": label, "reason": "not_function"},
            }
        got = r.function_outputs()
        return {
            "accepted": got == target,
            "protected_ok": True,
            "loss": sum(a != b for a, b in zip(got, target)),
            "witness": {
                "label": label,
                "required_outputs": list(target),
                "actual_outputs": list(got),
                "rows_checked": len(target),
            },
        }

    return evaluate


def partial_function(constraints: Mapping[int, int], label: str):
    constraints = {int(k): int(v) for k, v in constraints.items()}

    def evaluate(r: Relation) -> Dict[str, Any]:
        if not r.is_function():
            return {
                "accepted": False,
                "protected_ok": True,
                "loss": len(constraints) + 1,
                "witness": {"label": label, "reason": "not_function"},
            }
        out = r.function_outputs()
        bad = [
            (i, expected, out[i])
            for i, expected in constraints.items()
            if out[i] != expected
        ]
        return {
            "accepted": not bad,
            "protected_ok": True,
            "loss": len(bad),
            "witness": {
                "label": label,
                "constraints": sorted((i, v) for i, v in constraints.items()),
                "actual_outputs": list(out),
                "violations": bad,
            },
        }

    return evaluate


def total_relation_evaluator(label: str):
    def evaluate(r: Relation) -> Dict[str, Any]:
        ok = r.is_total_relation()
        return {
            "accepted": ok,
            "protected_ok": True,
            "loss": r.domain.size * r.codomain.size - len(r.edges),
            "witness": {
                "label": label,
                "expected_edge_count": r.domain.size * r.codomain.size,
                "actual_edge_count": len(r.edges),
            },
        }
    return evaluate


def equivalence_with_classes(k: int, label: str):
    k = int(k)

    def evaluate(r: Relation) -> Dict[str, Any]:
        if not is_equivalence_relation(r):
            return {
                "accepted": False,
                "protected_ok": True,
                "loss": 1,
                "witness": {"label": label, "reason": "not_equivalence"},
            }
        classes = equivalence_classes(r)
        return {
            "accepted": len(classes) == k,
            "protected_ok": True,
            "loss": abs(len(classes) - k),
            "witness": {
                "label": label,
                "class_count": len(classes),
                "classes": [list(c) for c in classes],
            },
        }

    return evaluate


def slim(result: Dict[str, Any]) -> Dict[str, Any]:
    out: Dict[str, Any] = {}
    for k, v in result.items():
        if k.startswith("_"):
            continue
        if hasattr(v, "data"):
            out[k] = v.data()
        elif isinstance(v, list):
            rows = []
            for item in v:
                if isinstance(item, dict):
                    row = {}
                    for kk, vv in item.items():
                        row[kk] = vv.data() if hasattr(vv, "data") else vv
                    rows.append(row)
                else:
                    rows.append(item.data() if hasattr(item, "data") else item)
            out[k] = rows
        else:
            out[k] = v
    return out


def active_relation_from_frontier(result: Dict[str, Any]) -> Relation | None:
    rows = result.get("_frontier_objects", [])
    if not rows:
        return result.get("relation")
    # Active execution may choose one lawful frontier member without deleting
    # the other warranted alternatives.
    return rows[0][0].relation


def build_c4_from_bit(
    k: ProtoKernel,
    label: str,
) -> Tuple[Dict[str, Any], Any]:
    total = k.synthesize_relation(
        label + "_total_bit_relation",
        BIT,
        BIT,
        total_relation_evaluator(label + "_total"),
        max_cost=5,
        search_complete=True,
        functional_only=False,
    )
    if total.get("status") != "VERIFIED":
        return total, None
    rel = active_relation_from_frontier(total)
    c4 = k.reify_edges(
        rel,
        verified=True,
        warrant=total.get("evaluation") or {"frontier": True},
    )
    k.retain_carrier(c4)
    return total, c4


def build_c3_from_c4(
    k: ProtoKernel,
    c4,
    label: str,
) -> Tuple[Dict[str, Any], Any]:
    eq = k.synthesize_relation(
        label + "_equivalence",
        c4,
        c4,
        equivalence_with_classes(3, label + "_three_classes"),
        max_cost=17,
        search_complete=True,
        functional_only=False,
    )
    if eq.get("status") != "VERIFIED":
        return eq, None
    rel = active_relation_from_frontier(eq)
    c3 = k.reify_classes(
        rel,
        verified=True,
        warrant={
            "authority": label,
            "frontier_size": eq.get("frontier_size"),
            "selected_for_active_execution_only": True,
        },
    )
    k.retain_carrier(c3)
    return eq, c3


def run_ladder(config: BasisConfig, detailed: bool = False) -> Dict[str, Any]:
    k = ProtoKernel(config)
    results: Dict[str, Any] = {}
    gates: Dict[str, bool] = {}

    # --------------------------------------------------------------
    # Bootstrap a four-edge distinction space from a verified total relation.
    # --------------------------------------------------------------
    total4, c4 = build_c4_from_bit(k, "bootstrap4")
    results["bootstrap_total_relation"] = slim(total4)
    if c4 is not None:
        results["bootstrap_edge_reified_carrier"] = c4.data()

    # --------------------------------------------------------------
    # L0 proto-logic: predicate on relationally reified four-state carrier.
    # --------------------------------------------------------------
    l0 = None
    if c4 is not None:
        l0 = k.synthesize_relation(
            "L0_predicate",
            c4,
            BIT,
            exact_function((0, 1, 1, 0), "predicate_xor_shape"),
            max_cost=9,
            search_complete=True,
            functional_only=True,
        )
        results["L0_predicate"] = slim(l0)

    gates["L0_proto_logic"] = bool(
        l0
        and l0.get("status") == "VERIFIED"
        and l0.get("frontier_size") == 1
        and l0.get("relation").function_outputs() == (0, 1, 1, 0)
    )

    # --------------------------------------------------------------
    # L1 finite math: 3 classes from a verified equivalence relation.
    # --------------------------------------------------------------
    eq3 = None
    c3 = None
    if c4 is not None:
        eq3, c3 = build_c3_from_c4(k, c4, "L1")
        results["L1_equivalence"] = slim(eq3)
        if c3 is not None:
            results["L1_class_reified_carrier"] = c3.data()

    gates["L1_three_state_class_reification"] = bool(
        eq3
        and eq3.get("status") == "VERIFIED"
        and eq3.get("frontier_size") == 6
        and c3 is not None
        and c3.size == 3
        and c3.provenance[0] == "CLASS_REIFY"
    )

    # --------------------------------------------------------------
    # L2 + L4 computation and compiled vocabulary.
    # --------------------------------------------------------------
    l2 = repeat = reuse = None
    f_atom = None
    if c3 is not None:
        f_eval = exact_function((0, 1, 1), "finite_computation")
        l2 = k.synthesize_relation(
            "L2_compute",
            c3,
            BIT,
            f_eval,
            max_cost=7,
            search_complete=True,
            functional_only=True,
        )
        repeat = k.synthesize_relation(
            "L4_repeat",
            c3,
            BIT,
            f_eval,
            max_cost=7,
            search_complete=True,
            functional_only=True,
        )
        f_atom = repeat.get("promoted_atom_id")
        reuse = k.synthesize_relation(
            "L4_reuse",
            c3,
            BIT,
            f_eval,
            max_cost=1,
            search_complete=True,
            functional_only=True,
            allow_direct=False,
        )
        results["L2_compute"] = slim(l2)
        results["L4_repeat"] = slim(repeat)
        results["L4_reuse"] = slim(reuse)

    gates["L2_computation"] = bool(
        c3 is not None
        and l2
        and l2.get("status") == "VERIFIED"
        and l2.get("relation").is_function()
        and l2.get("relation").function_outputs() == (0, 1, 1)
        and all(
            l2.get("relation").run(x) == BIT.elements[(0, 1, 1)[i]]
            for i, x in enumerate(c3.elements)
        )
    )

    gates["L4_vocabulary_compile_reuse"] = bool(
        f_atom
        and reuse
        and reuse.get("status") == "VERIFIED"
        and reuse.get("route") == "ATOM"
        and reuse.get("minimum_cost") == 1
    )

    # --------------------------------------------------------------
    # L3 modular computation through relational composition.
    # --------------------------------------------------------------
    g1 = g2 = modular = cold_tight = cold_deep = None
    g_atom = None
    if c3 is not None:
        g_eval = exact_function((1, 0), "bit_flip")
        g1 = k.synthesize_relation(
            "L3_g1",
            BIT,
            BIT,
            g_eval,
            max_cost=5,
            search_complete=True,
            functional_only=True,
        )
        g2 = k.synthesize_relation(
            "L3_g2",
            BIT,
            BIT,
            g_eval,
            max_cost=5,
            search_complete=True,
            functional_only=True,
        )
        g_atom = g2.get("promoted_atom_id")

        composed_eval = exact_function((1, 0, 0), "composed_transfer")
        modular = k.synthesize_relation(
            "L3_modular",
            c3,
            BIT,
            composed_eval,
            max_cost=3,
            search_complete=True,
            functional_only=True,
        )

        cold = ProtoKernel(config)
        cold_tight = cold.synthesize_relation(
            "L3_cold_tight",
            c3,
            BIT,
            composed_eval,
            max_cost=3,
            search_complete=True,
            functional_only=True,
        )
        cold_deep = cold.synthesize_relation(
            "L3_cold_deep",
            c3,
            BIT,
            composed_eval,
            max_cost=7,
            search_complete=True,
            functional_only=True,
        )

        results["L3_g2"] = slim(g2)
        results["L3_modular"] = slim(modular)
        results["L3_cold_tight"] = slim(cold_tight)
        results["L3_cold_deep"] = slim(cold_deep)

    gates["L3_modular_composition"] = bool(
        f_atom
        and g_atom
        and modular
        and modular.get("status") == "VERIFIED"
        and modular.get("route") == "COMPOSE"
        and modular.get("minimum_cost") == 3
        and cold_tight
        and cold_tight.get("status")
            == "CERTIFIED_NO_RELATION_IN_DECLARED_CLASS"
        and cold_deep
        and cold_deep.get("status") == "VERIFIED"
        and cold_deep.get("route") == "RELATION"
        and cold_deep.get("minimum_cost") == 7
    )

    # --------------------------------------------------------------
    # L5 repeated relation-reification formation -> grammar atom.
    # --------------------------------------------------------------
    form1 = form2 = form_transfer = form_cold = form_deep = None
    formation_atom = None
    if c3 is not None and c4 is not None:
        form1 = k.construct_total_edge_self(
            "L5_form1",
            c3,
            max_cost=11,
            search_complete=True,
        )
        form2 = k.construct_total_edge_self(
            "L5_form2",
            c4,
            max_cost=18,
            search_complete=True,
        )
        formation_atom = form2.get("promoted_formation_atom_id")
        form_transfer = k.construct_total_edge_self(
            "L5_transfer",
            BIT,
            max_cost=1,
            search_complete=True,
        )

        cold_form = ProtoKernel(config)
        form_cold = cold_form.construct_total_edge_self(
            "L5_cold_tight",
            BIT,
            max_cost=1,
            search_complete=True,
        )
        form_deep = cold_form.construct_total_edge_self(
            "L5_cold_deep",
            BIT,
            max_cost=6,
            search_complete=True,
        )

        results["L5_form1"] = slim(form1)
        results["L5_form2"] = slim(form2)
        results["L5_transfer"] = slim(form_transfer)
        results["L5_cold_tight"] = slim(form_cold)
        results["L5_cold_deep"] = slim(form_deep)

    gates["L5_grammar_type_formation"] = bool(
        formation_atom
        and form1 and form1.get("status") == "VERIFIED"
        and form1.get("cost") == 11
        and form2 and form2.get("status") == "VERIFIED"
        and form2.get("cost") == 18
        and form_transfer
        and form_transfer.get("status") == "VERIFIED"
        and form_transfer.get("route") == "FORMATION_ATOM"
        and form_transfer.get("cost") == 1
        and form_cold
        and form_cold.get("status")
            == "CERTIFIED_NO_FORMATION_IN_DECLARED_CLASS"
        and form_deep
        and form_deep.get("status") == "VERIFIED"
        and form_deep.get("cost") == 6
    )

    # --------------------------------------------------------------
    # L6 semantic basis growth: verified class-reified C3 creates C6 reach.
    # --------------------------------------------------------------
    sg = ProtoKernel(config)
    sg_total4, sg_c4 = build_c4_from_bit(sg, "L6_bootstrap")
    sg_eq = None
    sg_c3 = None
    if sg_c4 is not None:
        sg_eq, sg_c3 = build_c3_from_c4(sg, sg_c4, "L6")
    warm6 = None
    if sg_c3 is not None:
        warm6 = sg.construct_total_edge_between(
            "L6_warm6",
            sg_c3,
            BIT,
            max_cost=8,
            search_complete=True,
        )

    before_sizes = ProtoKernel(config).reachable_sizes(
        max_cost=8,
        size_cap=6,
    )
    warm_sizes = sg.reachable_sizes(
        max_cost=8,
        size_cap=6,
    )

    ablated = False
    after_sizes = {}
    if sg_c3 is not None:
        ablated = sg.ablate_carrier(sg_c3.carrier_id)
        after_sizes = sg.reachable_sizes(
            max_cost=8,
            size_cap=6,
        )

    results["L6_bootstrap_total"] = slim(sg_total4)
    if sg_eq:
        results["L6_equivalence"] = slim(sg_eq)
    if sg_c3:
        results["L6_carrier3"] = sg_c3.data()
    if warm6:
        results["L6_warm6"] = slim(warm6)
    results["L6_reachable_before"] = before_sizes
    results["L6_reachable_warm"] = warm_sizes
    results["L6_reachable_after_ablation"] = after_sizes

    gates["L6_semantic_basis_growth"] = bool(
        sg_c3 is not None
        and sg_c3.size == 3
        and warm6
        and warm6.get("status") == "VERIFIED"
        and warm6.get("carrier").size == 6
        and 3 not in before_sizes
        and 6 not in before_sizes
        and 3 in warm_sizes
        and 6 in warm_sizes
        and warm_sizes[6] <= 8
        and ablated
        and 3 not in after_sizes
        and 6 not in after_sizes
    )

    # --------------------------------------------------------------
    # L7 meta-rule is again just a relation with partial consequence.
    # --------------------------------------------------------------
    partial = future = meta_reuse = None
    meta_atom = None
    if c3 is not None:
        partial = k.synthesize_relation(
            "L7_partial",
            c3,
            c3,
            partial_function({0: 1, 1: 2}, "meta_partial"),
            max_cost=10,
            search_complete=True,
            functional_only=True,
        )
        frontier = partial.get("_frontier_objects", [])
        if frontier:
            future = k.select_relation_frontier(
                "L7_future",
                frontier,
                exact_function((1, 2, 0), "meta_future"),
            )
            meta_atom = future.get("promoted_atom_id")

        meta_reuse = k.synthesize_relation(
            "L7_reuse",
            c3,
            c3,
            exact_function((1, 2, 0), "meta_reuse"),
            max_cost=1,
            search_complete=True,
            functional_only=True,
            allow_direct=False,
        )
        results["L7_partial"] = slim(partial)
        if future:
            results["L7_future"] = slim(future)
        results["L7_reuse"] = slim(meta_reuse)

    gates["L7_meta_rule_same_substrate"] = bool(
        partial
        and partial.get("status") == "VERIFIED"
        and partial.get("route") == "FRONTIER"
        and partial.get("frontier_size") == 3
        and future
        and future.get("status") == "VERIFIED"
        and future.get("route") == "FUTURE_SELECT"
        and meta_atom
        and meta_reuse
        and meta_reuse.get("status") == "VERIFIED"
        and meta_reuse.get("route") == "ATOM"
        and meta_reuse.get("minimum_cost") == 1
    )

    # --------------------------------------------------------------
    # UNKNOWN control.
    # --------------------------------------------------------------
    uk = ProtoKernel(config)
    unknown = uk.synthesize_relation(
        "UNKNOWN_control",
        BIT,
        BIT,
        total_relation_evaluator("unknown_total"),
        max_cost=4,
        search_complete=False,
        functional_only=False,
    )
    results["UNKNOWN_control"] = slim(unknown)
    gates["UNKNOWN_conservative"] = (
        unknown.get("status") == "UNKNOWN_SEARCH"
    )

    return {
        "basis": config.data(),
        "gates": gates,
        "full_pass": all(gates.values()),
        "results": results if detailed else {},
    }
