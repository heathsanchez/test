#!/usr/bin/env python3
"""Post-freeze challenge ladder for V7 proto-semantics basis search."""
from __future__ import annotations

from typing import Any, Dict, Mapping, Sequence, Tuple

from basis import (
    BIT,
    BasisConfig,
    Carrier,
    FunctionalRelation,
)
from kernel import ProtoKernel


def exact_relation_evaluator(required: Sequence[int], label: str):
    req = tuple(int(x) for x in required)

    def evaluate(r: FunctionalRelation) -> Dict[str, Any]:
        ok = tuple(r.outputs) == req
        return {
            "accepted": ok,
            "protected_ok": True,
            "loss": sum(a != b for a, b in zip(r.outputs, req)),
            "witness": {
                "label": label,
                "required_outputs": list(req),
                "actual_outputs": list(r.outputs),
                "rows_checked": len(req),
            },
        }

    return evaluate


def partial_relation_evaluator(prefix: Mapping[int, int], label: str):
    prefix = {int(k): int(v) for k, v in prefix.items()}

    def evaluate(r: FunctionalRelation) -> Dict[str, Any]:
        bad = [
            (i, expected, r.outputs[i])
            for i, expected in prefix.items()
            if r.outputs[i] != expected
        ]
        return {
            "accepted": not bad,
            "protected_ok": True,
            "loss": len(bad),
            "witness": {
                "label": label,
                "constraints": sorted((i, v) for i, v in prefix.items()),
                "actual_outputs": list(r.outputs),
                "violations": bad,
            },
        }

    return evaluate


def slim(result: Dict[str, Any]) -> Dict[str, Any]:
    """JSON-safe evidence summary."""
    out: Dict[str, Any] = {}
    for k, v in result.items():
        if k.startswith("_"):
            continue
        if k in {"carrier", "relation", "recipe", "formed"}:
            if hasattr(v, "data"):
                out[k] = v.data()
            else:
                out[k] = str(v)
            continue
        if k == "frontier":
            rows = []
            for item in v:
                if isinstance(item, dict):
                    row = {}
                    for kk, vv in item.items():
                        if kk == "candidate":
                            row[kk] = {
                                "cost": vv.cost,
                                "route": vv.route,
                                "components": list(vv.components),
                                "relation": vv.relation.data(),
                            }
                        elif hasattr(vv, "data"):
                            row[kk] = vv.data()
                        else:
                            row[kk] = vv
                    rows.append(row)
                else:
                    rows.append(str(item))
            out[k] = rows
            continue
        out[k] = v
    return out


def run_ladder(config: BasisConfig, detailed: bool = False) -> Dict[str, Any]:
    k = ProtoKernel(config)
    gates: Dict[str, bool] = {}
    results: Dict[str, Any] = {}

    # --------------------------------------------------------------
    # L0: proto-logic -- nontrivial predicate over BIT x BIT.
    # --------------------------------------------------------------
    c4r = k.construct_carrier(
        4, max_cost=3, search_complete=True,
        allow_retained=True, retain_verified=True,
    )
    results["L0_carrier4"] = slim(c4r)
    c4 = c4r.get("carrier") if c4r.get("status") == "VERIFIED" else None

    l0 = None
    if c4 is not None:
        l0 = k.synthesize_relation(
            "L0_predicate",
            c4,
            BIT,
            exact_relation_evaluator((0, 1, 1, 0), "binary_predicate"),
            max_cost=5,
            search_complete=True,
        )
        results["L0_predicate"] = slim(l0)
    gates["L0_proto_logic"] = bool(
        l0
        and l0.get("status") == "VERIFIED"
        and l0.get("frontier_size") == 1
        and tuple(l0.get("relation").outputs) == (0, 1, 1, 0)
    )

    # --------------------------------------------------------------
    # L1: mathematical structure -- 3-state quotient from binary seed.
    # --------------------------------------------------------------
    c3r = k.construct_carrier(
        3, max_cost=4, search_complete=True,
        allow_retained=True, retain_verified=True,
    )
    results["L1_carrier3"] = slim(c3r)
    c3 = c3r.get("carrier") if c3r.get("status") == "VERIFIED" else None

    qwit = c3r.get("construction_witness") or {}
    class_of = qwit.get("class_of", []) if isinstance(qwit, dict) else []
    gates["L1_three_state_quotient"] = bool(
        c3 is not None
        and c3r.get("route") == "QUOTIENT"
        and c3.size == 3
        and sorted(set(class_of)) == [0, 1, 2]
    )

    # --------------------------------------------------------------
    # L2 + L4: computation and vocabulary compilation/reuse.
    # --------------------------------------------------------------
    l2 = l4repeat = l4reuse = None
    f_atom = None
    if c3 is not None:
        f_eval = exact_relation_evaluator((0, 1, 1), "finite_computation")
        l2 = k.synthesize_relation(
            "L2_compute", c3, BIT, f_eval,
            max_cost=4, search_complete=True,
        )
        results["L2_compute"] = slim(l2)

        l4repeat = k.synthesize_relation(
            "L4_repeat", c3, BIT, f_eval,
            max_cost=4, search_complete=True,
        )
        results["L4_repeat"] = slim(l4repeat)
        f_atom = l4repeat.get("promoted_atom_id")

        l4reuse = k.synthesize_relation(
            "L4_reuse", c3, BIT, f_eval,
            max_cost=1, search_complete=True,
            allow_direct=False,
        )
        results["L4_reuse"] = slim(l4reuse)

    gates["L2_computation"] = bool(
        l2
        and l2.get("status") == "VERIFIED"
        and tuple(l2.get("relation").outputs) == (0, 1, 1)
        and all(
            l2.get("relation").run(x)
            == BIT.elements[(0, 1, 1)[i]]
            for i, x in enumerate(c3.elements)
        )
    ) if c3 is not None else False

    gates["L4_vocabulary_compile_reuse"] = bool(
        f_atom
        and l4reuse
        and l4reuse.get("status") == "VERIFIED"
        and l4reuse.get("route") == "ATOM"
        and l4reuse.get("minimum_cost") == 1
    )

    # --------------------------------------------------------------
    # L3: modular composition. Compile a second relation, then require
    # their composition under a bound below direct table construction.
    # --------------------------------------------------------------
    g1 = g2 = modular = cold_tight = cold_deep = None
    g_atom = None
    if c3 is not None:
        g_eval = exact_relation_evaluator((1, 0), "bit_transform")
        g1 = k.synthesize_relation(
            "L3_g1", BIT, BIT, g_eval,
            max_cost=3, search_complete=True,
        )
        g2 = k.synthesize_relation(
            "L3_g2", BIT, BIT, g_eval,
            max_cost=3, search_complete=True,
        )
        g_atom = g2.get("promoted_atom_id")
        results["L3_g2"] = slim(g2)

        modular_eval = exact_relation_evaluator((1, 0, 0), "composed_transfer")
        modular = k.synthesize_relation(
            "L3_modular", c3, BIT, modular_eval,
            max_cost=3, search_complete=True,
            allow_direct=True,
        )
        results["L3_modular"] = slim(modular)

        cold = ProtoKernel(config)
        cold_tight = cold.synthesize_relation(
            "L3_cold_tight", c3, BIT, modular_eval,
            max_cost=3, search_complete=True,
            allow_direct=True,
        )
        cold_deep = cold.synthesize_relation(
            "L3_cold_deep", c3, BIT, modular_eval,
            max_cost=4, search_complete=True,
            allow_direct=True,
        )
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
        and cold_deep.get("minimum_cost") == 4
    )

    # --------------------------------------------------------------
    # L5: recurring carrier formation -> parametric grammar atom.
    # Need C3 and C6 as distinct bases, then transfer to unseen C4.
    # --------------------------------------------------------------
    c6r = None
    c6 = None
    if c3 is not None:
        c6r = k.construct_carrier(
            6, max_cost=3, search_complete=True,
            allow_retained=True, retain_verified=True,
        )
        results["L5_carrier6"] = slim(c6r)
        c6 = c6r.get("carrier") if c6r.get("status") == "VERIFIED" else None

    f1 = f2 = ftransfer = fcold = fdeep = None
    recipe_atom = None
    if c3 is not None and c6 is not None and c4 is not None:
        f1 = k.synthesize_formation(
            "L5_form1", c3, 9, max_cost=3, search_complete=True
        )
        f2 = k.synthesize_formation(
            "L5_form2", c6, 36, max_cost=3, search_complete=True
        )
        recipe_atom = f2.get("promoted_recipe_atom_id")
        ftransfer = k.synthesize_formation(
            "L5_transfer", c4, 16, max_cost=1, search_complete=True
        )

        cold_form = ProtoKernel(config)
        fcold = cold_form.synthesize_formation(
            "L5_cold_tight", c4, 16, max_cost=1, search_complete=True
        )
        fdeep = cold_form.synthesize_formation(
            "L5_cold_deep", c4, 16, max_cost=3, search_complete=True
        )
        results["L5_form1"] = slim(f1)
        results["L5_form2"] = slim(f2)
        results["L5_transfer"] = slim(ftransfer)
        results["L5_cold_tight"] = slim(fcold)
        results["L5_cold_deep"] = slim(fdeep)

    gates["L5_grammar_type_formation"] = bool(
        recipe_atom
        and f1 and f1.get("status") == "VERIFIED"
        and f1.get("minimum_cost") == 3
        and f2 and f2.get("status") == "VERIFIED"
        and f2.get("minimum_cost") == 3
        and ftransfer
        and ftransfer.get("status") == "VERIFIED"
        and ftransfer.get("route") == "RECIPE_ATOM"
        and ftransfer.get("minimum_cost") == 1
        and fcold
        and fcold.get("status")
            == "CERTIFIED_NO_FORMATION_IN_DECLARED_CLASS"
        and fdeep
        and fdeep.get("status") == "VERIFIED"
        and fdeep.get("minimum_cost") == 3
    )

    # --------------------------------------------------------------
    # L6: semantic basis growth from quotient-derived carrier.
    # Dedicated kernel avoids retaining C6 across the ablation.
    # --------------------------------------------------------------
    sg = ProtoKernel(config)
    sg3 = sg.construct_carrier(
        3, max_cost=4, search_complete=True,
        allow_retained=True, retain_verified=True,
    )
    sgc3 = sg3.get("carrier") if sg3.get("status") == "VERIFIED" else None
    sg6 = None
    after_ablation = None
    ablated = False
    if sgc3 is not None:
        sg6 = sg.construct_carrier(
            6, max_cost=3, search_complete=True,
            allow_retained=True, retain_verified=False,
        )
        ablated = sg.ablate_carrier(sgc3.carrier_id)
        after_ablation = sg.construct_carrier(
            6, max_cost=3, search_complete=True,
            allow_retained=True, retain_verified=False,
        )

    product_only = BasisConfig(
        product=config.product,
        quotient=False,
        relation=config.relation,
        compose=config.compose,
    )
    po = ProtoKernel(product_only)
    po3 = po.construct_carrier(
        3, max_cost=9, search_complete=True,
        allow_retained=True, retain_verified=False,
    )
    po6 = po.construct_carrier(
        6, max_cost=9, search_complete=True,
        allow_retained=True, retain_verified=False,
    )
    results["L6_genesis3"] = slim(sg3)
    if sg6:
        results["L6_transfer6"] = slim(sg6)
    if after_ablation:
        results["L6_after_ablation"] = slim(after_ablation)
    results["L6_product_only_3"] = slim(po3)
    results["L6_product_only_6"] = slim(po6)

    gates["L6_semantic_basis_growth"] = bool(
        sgc3
        and sg3.get("route") == "QUOTIENT"
        and sg6
        and sg6.get("status") == "VERIFIED"
        and sg6.get("cost") == 3
        and "PRODUCT" == sg6.get("route")
        and ablated
        and after_ablation
        and after_ablation.get("status")
            == "CERTIFIED_NO_CARRIER_IN_DECLARED_CLASS"
        and po3.get("status") == "CERTIFIED_NO_CARRIER_IN_DECLARED_CLASS"
        and po6.get("status") == "CERTIFIED_NO_CARRIER_IN_DECLARED_CLASS"
    )

    # --------------------------------------------------------------
    # L7: meta-rule represented by the same finite relation machinery.
    # Partial evidence leaves a lawful frontier; future consequence selects.
    # --------------------------------------------------------------
    meta0 = meta1 = metareuse = None
    meta_atom = None
    if c3 is not None:
        meta0 = k.synthesize_relation(
            "L7_partial",
            c3,
            c3,
            partial_relation_evaluator({0: 1, 1: 2}, "meta_partial"),
            max_cost=4,
            search_complete=True,
        )
        results["L7_partial"] = slim(meta0)

        frontier = meta0.get("_frontier_objects", []) if meta0 else []
        if frontier:
            meta1 = k.select_relation_frontier(
                "L7_future",
                frontier,
                exact_relation_evaluator((1, 2, 0), "meta_future"),
            )
            results["L7_future"] = slim(meta1)
            meta_atom = meta1.get("promoted_atom_id")

        metareuse = k.synthesize_relation(
            "L7_reuse",
            c3,
            c3,
            exact_relation_evaluator((1, 2, 0), "meta_reuse"),
            max_cost=1,
            search_complete=True,
            allow_direct=False,
        )
        results["L7_reuse"] = slim(metareuse)

    gates["L7_meta_rule_same_substrate"] = bool(
        meta0
        and meta0.get("status") == "VERIFIED"
        and meta0.get("route") == "FRONTIER"
        and meta0.get("frontier_size") == 3
        and meta1
        and meta1.get("status") == "VERIFIED"
        and meta1.get("route") == "FUTURE_SELECT"
        and meta_atom
        and metareuse
        and metareuse.get("status") == "VERIFIED"
        and metareuse.get("route") == "ATOM"
        and metareuse.get("minimum_cost") == 1
    )

    # --------------------------------------------------------------
    # Constitution / conservative-stop sanity.
    # --------------------------------------------------------------
    unknown = ProtoKernel(config).construct_carrier(
        3, max_cost=1, search_complete=False,
        allow_retained=True, retain_verified=False,
    )
    results["UNKNOWN_control"] = slim(unknown)
    gates["UNKNOWN_conservative"] = unknown.get("status") == "UNKNOWN_SEARCH"

    return {
        "basis": config.data(),
        "gates": gates,
        "full_pass": all(gates.values()),
        "results": results if detailed else {},
    }
