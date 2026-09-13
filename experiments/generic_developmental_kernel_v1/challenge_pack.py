#!/usr/bin/env python3
from __future__ import annotations

import copy
import hashlib
import itertools
from collections import Counter
from functools import lru_cache
from typing import Dict

from kernel import Action, Challenge


KERNEL_SHA256 = "5539aba1ef745f8c645fa932997914c32d12572e5befa5b00fed58dd018c30f3"


def aid(label: str) -> str:
    return "a_" + hashlib.sha256((KERNEL_SHA256 + ":" + label).encode()).hexdigest()[:12]


ACTION_LEGEND: Dict[str, str] = {}


def opaque_action(label, fn):
    x = aid(label)
    ACTION_LEGEND[x] = label
    return Action(x, fn)


def partition_mismatch(src, tgt):
    cs = Counter(src)
    ct = Counter(tgt)
    cj = Counter(zip(src, tgt))
    return (
        sum(v * v for v in cs.values())
        + sum(v * v for v in ct.values())
        - 2 * sum(v * v for v in cj.values())
    )


def first_partition_witness(src, tgt):
    by_t = {}
    for i, (s, t) in enumerate(zip(src, tgt)):
        prev = by_t.get(t)
        if prev is not None and src[prev] != s:
            return {"kind": "TARGET_MERGE", "i": prev, "j": i}
        by_t[t] = i
    by_s = {}
    for i, (s, t) in enumerate(zip(src, tgt)):
        prev = by_s.get(s)
        if prev is not None and tgt[prev] != t:
            return {"kind": "TARGET_SPLIT", "i": prev, "j": i}
        by_s[s] = i
    return None


# ---------------------------------------------------------------------------
# C0: already sufficient -> no change
# ---------------------------------------------------------------------------

def c0_eval(state):
    ok = state.get("stable") == 1
    return {
        "accepted": ok,
        "loss": 0 if ok else 1,
        "protected_ok": True,
        "witness": None if ok else {"stable": state.get("stable")},
    }


def c0_flip(state):
    s = copy.deepcopy(state)
    s["stable"] = 0
    return s


def c0_noise(state):
    s = copy.deepcopy(state)
    s["noise"] = int(s.get("noise", 0)) + 1
    return s


C0_ACTIONS = [
    opaque_action("noop.flip_stable_off", c0_flip),
    opaque_action("noop.add_noise", c0_noise),
]


# ---------------------------------------------------------------------------
# C1: compositional directed-graph representation repair
# ---------------------------------------------------------------------------

DG_N = 3
DG_ARCS = [(i, j) for i in range(DG_N) for j in range(DG_N) if i != j]
DG_GRAPHS = [
    frozenset(a for k, a in enumerate(DG_ARCS) if (bits >> k) & 1)
    for bits in range(1 << len(DG_ARCS))
]


def dg_source_sig(E, n=DG_N):
    ps = list(itertools.permutations(range(n)))
    return min(tuple(sorted((p[u], p[v]) for u, v in E)) for p in ps)


DG_SOURCE = [dg_source_sig(E) for E in DG_GRAPHS]


@lru_cache(maxsize=None)
def dg_role_maps(n, roles):
    ps = list(itertools.permutations(range(n)))
    maps = []
    for rps in itertools.product(ps, repeat=roles):
        m = []
        for v in range(n):
            for r in range(roles):
                m.append(roles * rps[r][v] + r)
        maps.append(tuple(m))
    return tuple(maps)


def dg_encode(E, n, roles, couplings):
    idx = lambda v, r: roles * v + r
    out = set()
    for u, v in E:
        out.add(tuple(sorted((idx(u, 0), idx(v, 1)))))
    for a, b in couplings:
        for v in range(n):
            out.add(tuple(sorted((idx(v, a), idx(v, b)))))
    return frozenset(out)


def dg_target_sig(E, n, roles, couplings):
    enc = dg_encode(E, n, roles, couplings)
    vals = []
    for m in dg_role_maps(n, roles):
        vals.append(tuple(sorted(tuple(sorted((m[u], m[v]))) for u, v in enc)))
    return min(vals)


DG_CACHE = {}


def dg_eval(state):
    roles = int(state["roles"])
    couplings = tuple(tuple(x) for x in sorted(state.get("couplings", [])))
    key = (roles, couplings)
    if key not in DG_CACHE:
        tgt = [dg_target_sig(E, DG_N, roles, couplings) for E in DG_GRAPHS]
        mm = partition_mismatch(DG_SOURCE, tgt)
        DG_CACHE[key] = (mm, first_partition_witness(DG_SOURCE, tgt))
    mm, witness = DG_CACHE[key]
    return {
        "accepted": mm == 0,
        "loss": mm,
        "protected_ok": True,
        "witness": witness,
        "world": {"objects": 64, "ordered_pairs": 4096},
    }


def dg_add_fresh(state):
    if state["roles"] != 2:
        return None
    s = copy.deepcopy(state)
    s["roles"] = 3
    return s


def _dg_add_pair(pair):
    def f(state):
        if state["roles"] != 3:
            return None
        s = copy.deepcopy(state)
        cs = [tuple(x) for x in s.get("couplings", [])]
        p = tuple(sorted(pair))
        if p in cs:
            return None
        cs.append(p)
        s["couplings"] = [list(x) for x in sorted(cs)]
        return s
    return f


DG_ACTIONS = [
    opaque_action("digraph.add_fresh_role", dg_add_fresh),
    opaque_action("digraph.couple_old0_fresh", _dg_add_pair((0, 2))),
    opaque_action("digraph.couple_old1_fresh", _dg_add_pair((1, 2))),
    opaque_action("digraph.distractor_couple_old0_old1", _dg_add_pair((0, 1))),
]


def dg_iso(E, F, n):
    return dg_source_sig(E, n) == dg_source_sig(F, n)


def dg_holdout(state):
    n = 4
    a = frozenset({(0, 1), (1, 2), (2, 3)})
    p = (2, 0, 3, 1)
    b = frozenset((p[u], p[v]) for u, v in a)
    c = frozenset({(0, 1), (2, 1), (2, 3)})
    roles = int(state["roles"])
    couplings = tuple(tuple(x) for x in sorted(state.get("couplings", [])))
    pos_src = dg_iso(a, b, n)
    neg_src = not dg_iso(a, c, n)
    pos_tgt = dg_target_sig(a, n, roles, couplings) == dg_target_sig(b, n, roles, couplings)
    neg_tgt = dg_target_sig(a, n, roles, couplings) != dg_target_sig(c, n, roles, couplings)
    ok = pos_src and neg_src and pos_tgt and neg_tgt
    return {
        "accepted": ok,
        "protected_ok": True,
        "loss": 0 if ok else 1,
        "witness": None if ok else {
            "positive_source": pos_src,
            "negative_source": neg_src,
            "positive_target": pos_tgt,
            "negative_target": neg_tgt,
        },
        "heldout_n": 4,
    }


# ---------------------------------------------------------------------------
# C2: ternary coherence representation growth, exact V16 finite world
# ---------------------------------------------------------------------------

TR_N = 3
TR_ARITY = 3
TR_TUPLES = list(itertools.product(range(TR_N), repeat=TR_ARITY))
TR_RELATIONS = list(itertools.combinations(TR_TUPLES, 4))


def tr_source_sig(R, n=TR_N):
    ps = list(itertools.permutations(range(n)))
    return min(tuple(sorted(tuple(p[x] for x in t) for t in R)) for p in ps)


TR_SOURCE = [tr_source_sig(R) for R in TR_RELATIONS]


def tr_pairwise_sig(R, n=TR_N):
    ps = list(itertools.permutations(range(n)))
    vals = []
    for p in ps:
        proj = []
        for i, j in ((0, 1), (0, 2), (1, 2)):
            proj.append(tuple(sorted((p[t[i]], p[t[j]]) for t in R)))
        vals.append(tuple(proj))
    return min(vals)


def tr_occ_sig(R, links, n=TR_N):
    ps = list(itertools.permutations(range(n)))
    links = tuple(sorted(links))
    vals = []
    for p in ps:
        vals.append(tuple(sorted(tuple(p[t[i]] for i in links) for t in R)))
    return min(vals)


TR_PAIRWISE = [tr_pairwise_sig(R) for R in TR_RELATIONS]
TR_OCC_CACHE = {}


def tr_eval(state):
    if state.get("mode") == "pairwise":
        tgt = TR_PAIRWISE
        key = ("pairwise",)
    else:
        links = tuple(sorted(int(x) for x in state.get("links", [])))
        key = ("occurrence", links)
        if key not in TR_OCC_CACHE:
            TR_OCC_CACHE[key] = [tr_occ_sig(R, links) for R in TR_RELATIONS]
        tgt = TR_OCC_CACHE[key]
    mm = partition_mismatch(TR_SOURCE, tgt)
    return {
        "accepted": mm == 0,
        "loss": mm,
        "protected_ok": True,
        "witness": first_partition_witness(TR_SOURCE, tgt),
        "world": {
            "carrier_size": 3,
            "arity": 3,
            "relation_size": 4,
            "objects": len(TR_RELATIONS),
            "ordered_pairs": len(TR_RELATIONS) ** 2,
        },
        "representation": key,
    }


def tr_enable_occ(state):
    if state.get("mode") != "pairwise":
        return None
    return {"mode": "occurrence", "links": []}


def _tr_link(i):
    def f(state):
        if state.get("mode") != "occurrence":
            return None
        links = list(state.get("links", []))
        if i in links:
            return None
        links.append(i)
        s = copy.deepcopy(state)
        s["links"] = sorted(links)
        return s
    return f


def tr_reset(state):
    if state.get("mode") != "occurrence":
        return None
    return {"mode": "pairwise", "links": []}


TR_ACTIONS = [
    opaque_action("ternary.enable_occurrence_object", tr_enable_occ),
    opaque_action("ternary.connect_position_0", _tr_link(0)),
    opaque_action("ternary.connect_position_1", _tr_link(1)),
    opaque_action("ternary.connect_position_2", _tr_link(2)),
    opaque_action("ternary.distractor_reset_pairwise", tr_reset),
]


def tr_holdout(state):
    n = 4
    a = frozenset({(0, 0, 1), (1, 2, 3), (2, 3, 0), (3, 1, 2)})
    p = (2, 0, 3, 1)
    b = frozenset(tuple(p[x] for x in t) for t in a)
    all_t = list(itertools.product(range(n), repeat=3))
    c = None
    for old in sorted(a):
        for new in all_t:
            cand = frozenset((set(a) - {old}) | {new})
            if len(cand) != len(a):
                continue
            if tr_source_sig(tuple(a), n) != tr_source_sig(tuple(cand), n):
                c = cand
                break
        if c is not None:
            break
    if c is None:
        raise RuntimeError("failed to construct ternary negative holdout")

    if state.get("mode") == "pairwise":
        sig = lambda R: tr_pairwise_sig(tuple(R), n)
    else:
        links = tuple(sorted(int(x) for x in state.get("links", [])))
        sig = lambda R: tr_occ_sig(tuple(R), links, n)

    pos = sig(a) == sig(b)
    neg = sig(a) != sig(c)
    src_pos = tr_source_sig(tuple(a), n) == tr_source_sig(tuple(b), n)
    src_neg = tr_source_sig(tuple(a), n) != tr_source_sig(tuple(c), n)
    ok = pos and neg and src_pos and src_neg
    return {
        "accepted": ok,
        "protected_ok": True,
        "loss": 0 if ok else 1,
        "witness": None if ok else {
            "source_positive": src_pos,
            "source_negative": src_neg,
            "target_positive": pos,
            "target_negative": neg,
        },
        "heldout": {"carrier_size": 4, "arity": 3, "relation_size": 4},
    }


# ---------------------------------------------------------------------------
# C3: non-canonical minimum repairs; future consequence must select
# ---------------------------------------------------------------------------

SEL_CACHE = {}


def selector_subset(selector, m):
    if selector == "ALL":
        return list(range(m))
    if selector == "FIRST":
        return [0]
    if selector == "LAST":
        return [m - 1]
    if selector == "BOUNDARY":
        return sorted({0, m - 1})
    return []


def sel_source_sig(bits):
    comp = tuple(1 - x for x in bits)
    return min(tuple(bits), comp)


def sel_encode(bits, selected):
    m = len(bits)
    roles = 2 * m + 1
    fresh = 2 * m
    edges = set()
    for rel, orientation in enumerate(bits):
        u, v = ((0, 1) if orientation == 0 else (1, 0))
        edges.add(tuple(sorted((roles * u + 2 * rel, roles * v + 2 * rel + 1))))
    for rel in selected:
        for role in (2 * rel, 2 * rel + 1):
            edges.add(tuple(sorted((role, fresh))))
            edges.add(tuple(sorted((roles + role, roles + fresh))))
    return frozenset(edges)


def sel_map_vertex(x, mask, roles):
    v, role = divmod(x, roles)
    if (mask >> role) & 1:
        v = 1 - v
    return roles * v + role


def sel_target_sig(bits, selected):
    m = len(bits)
    roles = 2 * m + 1
    E = sel_encode(bits, selected)
    vals = []
    for mask in range(1 << roles):
        vals.append(tuple(sorted(
            tuple(sorted((sel_map_vertex(u, mask, roles), sel_map_vertex(v, mask, roles))))
            for u, v in E
        )))
    return min(vals)


def selector_mismatch(selector, m):
    key = (selector, m)
    if key in SEL_CACHE:
        return SEL_CACHE[key]
    objs = [tuple((bits >> i) & 1 for i in range(m)) for bits in range(1 << m)]
    src = [sel_source_sig(x) for x in objs]
    selected = selector_subset(selector, m)
    tgt = [sel_target_sig(x, selected) for x in objs]
    mm = partition_mismatch(src, tgt)
    SEL_CACHE[key] = (mm, first_partition_witness(src, tgt))
    return SEL_CACHE[key]


def sel_eval_m(m):
    def f(state):
        selector = state.get("selector", "NONE")
        mm, witness = selector_mismatch(selector, m)
        return {
            "accepted": mm == 0,
            "loss": mm,
            "protected_ok": True,
            "witness": witness,
            "relation_count": m,
            "selected_relations": selector_subset(selector, m),
        }
    return f


def _sel_set(name):
    def f(state):
        if state.get("selector") == name:
            return None
        return {"selector": name}
    return f


SEL_ACTIONS = [
    opaque_action("selector.set_all", _sel_set("ALL")),
    opaque_action("selector.set_first", _sel_set("FIRST")),
    opaque_action("selector.set_last", _sel_set("LAST")),
    opaque_action("selector.set_boundary", _sel_set("BOUNDARY")),
]


# ---------------------------------------------------------------------------
# C4-C8: scope growth, persistence, no-change, and retained-program reuse
# ---------------------------------------------------------------------------

SCOPE_OBSERVED_BATCHES = {1, 2}
SCOPE_PROTECTED = [[0], [0, 1]]


def scope_applicable(active, keys):
    failures = []
    if "K" in active:
        if not all(isinstance(k, int) and not isinstance(k, bool) for k in keys):
            failures.append("K")
    if "B" in active:
        if len(keys) not in SCOPE_OBSERVED_BATCHES:
            failures.append("B")
    return not failures, failures


def scope_eval(required):
    def f(state):
        active = set(state.get("active", []))
        current_ok, failures = scope_applicable(active, required)
        protected = [scope_applicable(active, r)[0] for r in SCOPE_PROTECTED]
        protected_ok = all(protected)
        return {
            "accepted": current_ok and protected_ok,
            "loss": len(failures) + (0 if protected_ok else 100),
            "protected_ok": protected_ok,
            "witness": None if current_ok else {"failed_predicates": failures},
            "active_predicates": sorted(active),
            "required_key_count": len(required),
        }
    return f


def _scope_drop(p):
    def f(state):
        active = list(state.get("active", []))
        if p not in active:
            return None
        s = copy.deepcopy(state)
        s["active"] = sorted(x for x in active if x != p)
        return s
    return f


def scope_add_z(state):
    active = list(state.get("active", []))
    if "Z" in active:
        return None
    s = copy.deepcopy(state)
    s["active"] = sorted(active + ["Z"])
    return s


SCOPE_ACTIONS = [
    opaque_action("scope.drop_key_type_restriction", _scope_drop("K")),
    opaque_action("scope.drop_batch_size_restriction", _scope_drop("B")),
    opaque_action("scope.distractor_add_inert_predicate", scope_add_z),
]


# ---------------------------------------------------------------------------
# C9-C10: conservative stopping
# ---------------------------------------------------------------------------

def inc_action(state):
    s = copy.deepcopy(state)
    s["x"] = int(s.get("x", 0)) + 1
    return s


def set1_action(state):
    if state.get("x") == 1:
        return None
    s = copy.deepcopy(state)
    s["x"] = 1
    return s


INC_ACTION = opaque_action("unknown.increment_once_per_step", inc_action)
SET1_ACTION = opaque_action("obstruction.set_one", set1_action)


def x_eval(state):
    x = int(state.get("x", 0))
    return {
        "accepted": x >= 2,
        "loss": max(0, 2 - x),
        "protected_ok": True,
        "witness": None if x >= 2 else {"x": x, "required": 2},
    }


CHALLENGES = [
    Challenge(
        "C0_ALREADY_SUFFICIENT",
        {"stable": 1},
        C0_ACTIONS,
        c0_eval,
        max_depth=2,
        holdout=c0_eval,
    ),
    Challenge(
        "C1_COMPOSITIONAL_IDENTITY_REPAIR",
        {"roles": 2, "couplings": []},
        DG_ACTIONS,
        dg_eval,
        max_depth=3,
        holdout=dg_holdout,
    ),
    Challenge(
        "C2_TERNARY_COHERENCE_GROWTH",
        {"mode": "pairwise", "links": []},
        TR_ACTIONS,
        tr_eval,
        max_depth=4,
        holdout=tr_holdout,
    ),
    Challenge(
        "C3_FUTURE_CONSEQUENCE_SELECTION",
        {"selector": "NONE"},
        SEL_ACTIONS,
        sel_eval_m(1),
        max_depth=1,
        future=(sel_eval_m(2), sel_eval_m(3)),
        holdout=sel_eval_m(4),
    ),
    Challenge(
        "C4_SCOPE_KEY_GROWTH",
        {"active": ["B", "K"]},
        SCOPE_ACTIONS,
        scope_eval(["LEFT"]),
        max_depth=1,
        context_id="scope_context",
        use_context=False,
    ),
    Challenge(
        "C5_SCOPE_BATCH_GROWTH",
        {"active": ["B", "K"]},
        SCOPE_ACTIONS,
        scope_eval([0, 1, 2]),
        max_depth=1,
        context_id="scope_context",
        use_context=True,
    ),
    Challenge(
        "C6_SCOPE_POST_GROWTH_NOOP",
        {"active": ["B", "K"]},
        SCOPE_ACTIONS,
        scope_eval([("P", 0), ("P", 1), ("P", 2), ("P", 3)]),
        max_depth=1,
        context_id="scope_context",
        use_context=True,
    ),
    Challenge(
        "C7_REUSE_KEY_REPAIR_ON_RESET",
        {"active": ["B", "K"]},
        SCOPE_ACTIONS,
        scope_eval(["CATEGORY"]),
        max_depth=1,
        context_id="scope_reset_key",
        use_context=False,
    ),
    Challenge(
        "C8_REUSE_BATCH_REPAIR_ON_RESET",
        {"active": ["B", "K"]},
        SCOPE_ACTIONS,
        scope_eval([10, 11, 12]),
        max_depth=1,
        context_id="scope_reset_batch",
        use_context=False,
    ),
    Challenge(
        "C9_UNCERTIFIED_SEARCH_STOPS_UNKNOWN",
        {"x": 0},
        [INC_ACTION],
        x_eval,
        max_depth=1,
        completeness_certified=False,
        retain_program=False,
    ),
    Challenge(
        "C10_CERTIFIED_CLASS_OBSTRUCTION",
        {"x": 0},
        [SET1_ACTION],
        x_eval,
        max_depth=1,
        completeness_certified=True,
        retain_program=False,
    ),
]


EXPECTED = {
    "C0_ALREADY_SUFFICIENT": {"status": "RESOLVED", "route": "NO_CHANGE"},
    "C1_COMPOSITIONAL_IDENTITY_REPAIR": {"status": "RESOLVED", "route": "SEARCH_SELECTED"},
    "C2_TERNARY_COHERENCE_GROWTH": {"status": "RESOLVED", "route": "SEARCH_SELECTED"},
    "C3_FUTURE_CONSEQUENCE_SELECTION": {"status": "RESOLVED", "route": "FUTURE_SELECTED"},
    "C4_SCOPE_KEY_GROWTH": {"status": "RESOLVED", "route": "SEARCH_SELECTED"},
    "C5_SCOPE_BATCH_GROWTH": {"status": "RESOLVED", "route": "SEARCH_SELECTED"},
    "C6_SCOPE_POST_GROWTH_NOOP": {"status": "RESOLVED", "route": "NO_CHANGE"},
    "C7_REUSE_KEY_REPAIR_ON_RESET": {"status": "RESOLVED", "route": "REUSE"},
    "C8_REUSE_BATCH_REPAIR_ON_RESET": {"status": "RESOLVED", "route": "REUSE"},
    "C9_UNCERTIFIED_SEARCH_STOPS_UNKNOWN": {"status": "UNKNOWN_SEARCH", "route": "STOP"},
    "C10_CERTIFIED_CLASS_OBSTRUCTION": {"status": "CERTIFIED_NO_REPAIR_IN_CLASS", "route": "STOP"},
}
