#!/usr/bin/env python3
"""V124: typed authority contracts for the persistent Collatz ROS controller.

V123 proved source-indexed two-clock composition and exact replay. It still
accepted any true finite witness when tagged with ANY existing live support,
even if that support only proved an unrelated proposition. That is semantic
authority laundering.

This successor rejects unsupported provenance, rechecks record IDs, requires
all composed parent proof records to be live, and permits NEW direct finite
witnesses only under an explicit BOUNDED_EXACT replay authority. The earlier
V123 state remains unchanged; this is a monotone state migration.

V124 is an executable *research controller*. No universal Collatz QED.
"""
from __future__ import annotations

import argparse
import json
from copy import deepcopy
from pathlib import Path

from research.collatz_ros_future_controller_v123 import (
    BASE_RUNS, Controller as BaseController, compose, digest, dump, make_join,
    verify_join,
)

ADMISSION = "COLLATZ_ROS_V124_TYPED_WARRANT_ADMISSION"
REVISION = 2
JOIN_FIELDS = frozenset((
    "source", "earlier", "source_clock", "earlier_clock", "common",
    "support", "origin", "parents", "id"
))
ID_FIELDS = ("source", "earlier", "source_clock", "earlier_clock",
             "support", "origin", "parents")
DIRECT = "DIRECT_CHECKED_FINITE_PROOF"
COMPOSED = "CERTIFIED_RECOMPOSITION"
PROOF_PINS = {
    "v124_exact_replay": {
        "run": None,
        "sha": None,
        "status": "BOUNDED_EXACT",
        "scope": "finite source-indexed two-clock witnesses independently replayed on admission and restart; no Lean-family or universal claim",
    },
    "v123_composition_theorem": {
        "run": 37978857199,
        "sha": "e44442266792ae2a072c4b320316021a5fd8bb3a",
        "status": "WARRANTED_FORMAL",
        "scope": "generic source-indexed two-clock composition only, conditional on both live certified premises; no new base witness",
    },
}
# Named proof THEOREM scope is not enough. These are the only existing
# independently verified V123 leaf assertions that can claim that support.
DECLARED_LEAF_CONTRACTS = {
    "LEAN_FORMAL_SOURCE27_EXACT_FIRST_CLOCK": {
        "support": "v122_exact_first_join_27",
        "quad": (27, 23, 59, 0),
    },
    "EXACT_ASYNCHRONOUS_ORBIT": {
        "support": "v123_bounded_arithmetic",
        "quad": (11, 3, 6, 1),
    },
    "EXACT_SMALLER_SOURCE": {
        "support": "v123_bounded_arithmetic",
        "quad": (3, 2, 4, 0),
    },
}
COMP_SUPPORT = frozenset({"v123_bounded_arithmetic", "v123_composition_theorem"})

class TypedController(BaseController):
    def _check_support_table(self) -> None:
        s = self.state
        if s.get("admission_schema") != ADMISSION or s.get("controller_revision") != REVISION:
            raise ValueError("unsupported or unqualified admission policy")
        wanted = dict(BASE_RUNS, **PROOF_PINS)
        if set(s["support"]) != set(wanted):
            raise ValueError("unknown support cannot authorize a certificate")
        for name, pin in wanted.items():
            current = s["support"][name]
            # Revocation is the only permitted change to frozen authority.
            expected = {**pin, "status": current.get("status")} if current.get("status") == "REVOKED" else pin
            if current != expected:
                raise ValueError("proof source scope or pin has been altered: " + name)

    @staticmethod
    def _validate_record_id(w: dict) -> None:
        if set(w) != JOIN_FIELDS:
            raise ValueError("extra, missing, or untyped join fields")
        if not isinstance(w["parents"], list) or any(not isinstance(p, str) for p in w["parents"]):
            raise ValueError("untyped dependency parent list")
        expected = digest({k: w[k] for k in ID_FIELDS})[:20]
        if w.get("id") != expected:
            raise ValueError("witness content changed without recomputed certificate ID")

    def _check_claim(self, w: dict, known: dict, active: set[str],
                     is_active: bool) -> None:
        self._validate_record_id(w)
        verify_join(w)
        origin = w["origin"]
        quad = tuple(w[k] for k in ("source", "earlier", "source_clock", "earlier_clock"))
        if origin in DECLARED_LEAF_CONTRACTS:
            spec = DECLARED_LEAF_CONTRACTS[origin]
            if w["support"] != spec["support"] or quad != spec["quad"] or w["parents"]:
                raise ValueError("unrelated formal theorem used as support for a different witness")
            return
        if origin == DIRECT:
            if w["support"] != "v124_exact_replay" or w["parents"]:
                raise ValueError("new direct witness must have bounded-exact evidence provenance")
            return
        if origin != COMPOSED or w["support"] not in COMP_SUPPORT:
            raise ValueError("unlicensed consequence constructor or proof-source substitution")
        if len(w["parents"]) != 2 or len(set(w["parents"])) != 2:
            raise ValueError("a composed warrant needs exactly two DISTINCT parents")
        if any(p not in known for p in w["parents"]):
            raise ValueError("compiled proof refers to an absent parent")
        if is_active and any(p not in active for p in w["parents"]):
            raise ValueError("a live claim cannot depend on a revoked parent")
        x, y = (known[p] for p in w["parents"])
        if x["earlier"] != y["source"]:
            raise ValueError("composed source/target interface does not connect")
        expected_quad = (
            x["source"], y["earlier"],
            x["source_clock"] + y["source_clock"],
            y["earlier_clock"] + x["earlier_clock"],
        )
        if quad != expected_quad:
            raise ValueError("true equality is insufficient: it was NOT entailed by these parents")

    def audit(self) -> None:
        super().audit()
        self._check_support_table()
        live = self.state["joins"]
        archive = self.state["archived_joins"]
        known = {w["id"]: w for w in (live + archive)}
        active_ids = {w["id"] for w in live}
        if len(known) != len(live) + len(archive):
            raise ValueError("certificate IDs are not globally unique")
        for w in live:
            self._check_claim(w, known, active_ids, True)
        for w in archive:
            self._check_claim(w, known, active_ids, False)
        if self.state["global_collatz"] != "UNKNOWN" or self.state["qed"] is not False:
            raise ValueError("this admission calculus has NOT solved universal Collatz")

    def add(self, join: dict) -> bool:
        known = {j["id"]: j for j in self.state["joins"] + self.state["archived_joins"]}
        self._check_claim(join, known,
            {j["id"] for j in self.state["joins"]}, True)
        return super().add(join)

    def admit_direct(self, n: int, p: int, a: int, b: int) -> bool:
        """External finite trajectory is exact-replayed, but never labeled
        as an independently qualified parametric/formal proof."""
        join = make_join(n, p, a, b, "v124_exact_replay", DIRECT)
        return self.add(join)

    def reclose(self) -> int:
        if self.state["grammar"]["active"] != "SOURCE_INDEXED_TWO_CLOCK":
            return 0
        count = 0
        while True:
            found = False
            for x in list(self.state["joins"]):
                for y in list(self.state["joins"]):
                    if x["earlier"] != y["source"]:
                        continue
                    w = compose(x, y, "v123_composition_theorem")
                    if any(t["source"] == w["source"] and t["earlier"] == w["earlier"]
                           for t in self.state["joins"]):
                        continue
                    if self.add(w):
                        count += 1
                        found = True
                        break
                if found:
                    break
            if not found:
                return count


def migrate(base: dict) -> TypedController:
    s = deepcopy(base)
    if s.get("admission_schema") == ADMISSION:
        return TypedController(s)
    if s.get("schema") != "COLLATZ_ROS_LAWFUL_FUTURE_V123":
        raise ValueError("only V123 verified durable state may be migrated")
    if set(s["support"]) != set(BASE_RUNS):
        raise ValueError("unexpected old support table")
    s["controller_revision"] = REVISION
    s["admission_schema"] = ADMISSION
    s["support"].update(deepcopy(PROOF_PINS))
    s["history"].append({
        "op": "MIGRATE_PROTECTED_PROVENANCE_ADMISSION",
        "from_revision": 1,
        "to_revision": REVISION,
        "trigger": "V123 true but unrelated theorem can be falsely attached to a witness",
        "prior_qualified_head": "e44442266792ae2a072c4b320316021a5fd8bb3a",
        "universal_collatz": "UNKNOWN",
    })
    return TypedController(s)


def bootstrap(path: Path = Path("research/collatz_ros_state_v123.json")) -> TypedController:
    controller = migrate(json.loads(path.read_text()))
    assert controller.admit_direct(7, 5, 7, 0)
    assert controller.admit_direct(5, 4, 2, 0)
    assert controller.reclose() == 1
    assert controller.status(7)["earlier"] == 5
    assert controller.state["qed"] is False
    controller.audit()
    return controller


def open_state(path: Path) -> TypedController:
    return migrate(json.loads(path.read_text()))


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--input", type=Path, default=Path("research/collatz_ros_state_v123.json"))
    ap.add_argument("--bootstrap", action="store_true")
    ap.add_argument("--output", type=Path)
    ap.add_argument("--revoke-support")
    args = ap.parse_args()
    if args.bootstrap:
        c = bootstrap(args.input)
    else:
        c = open_state(args.input)
    archived = c.revoke(args.revoke_support) if args.revoke_support else 0
    checkpoint = dump(c, args.output) if args.output else digest(c.state)
    print(json.dumps({
        "schema": ADMISSION,
        "status": "BOUNDED_EXACT_TYPED_AUTHORITY",
        "state_sha256": checkpoint,
        "active_joins": len(c.state["joins"]),
        "archived": archived,
        "source27": c.status(27),
        "source7": c.status(7),
        "collatz": c.state["global_collatz"],
        "qed": False,
    }, sort_keys=True))


if __name__ == "__main__":
    main()
