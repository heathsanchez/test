#!/usr/bin/env python3
"""C126: original-source N7 function-head budget discriminator on C105 lineage.

Read-only diagnostic research, not a kernel rule, C124 replay, or ACCEPT claim.
"""

import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess


SOURCE_SHA256 = "abce636f6a7dd529c0dc6bbad8e7c8e2eaecfdda0d04c191d7f868e3a4468d35"
PREFIX = "NUCLEUS_C126_N7_HEAD:"
BUDGETS = (65_536, 14_155_776)
KEYS = {"application", "function", "argument", "before", "after", "context",
        "pi_head", "type_proven"}
EDGE_PREFIX = "NUCLEUS_C129_APP_EDGE:"
ARG_PREFIX = "NUCLEUS_C130_APP_ARG:"
CONVERSION_INFER_PREFIX = "NUCLEUS_C131_ARG_INFER:"
CONVERSION_RELATION_PREFIX = "NUCLEUS_C131_ARG_CONVERT:"
INNER_ARG_PREFIX = "NUCLEUS_C132_APP_ARG:"
INNER_INFER_PREFIX = "NUCLEUS_C133_ARG_INFER:"
INNER_CONVERSION_PREFIX = "NUCLEUS_C133_ARG_CONVERT:"
C134_OWNER_PREFIX = "NUCLEUS_C134_OWNER:"
C134_RECURSOR_PREFIX = "NUCLEUS_C134_RECURSOR:"
C135_TRIAL_PREFIX = "NUCLEUS_C135_RECURSOR_TRIAL:"
C136_ROUTE_PREFIX = "NUCLEUS_C136_ROUTE:"
C137_WORK_PREFIX = "NUCLEUS_C137_WORK:"
C138_DEFERRED_PREFIX = "NUCLEUS_C138_DEFERRED:"
C139_COMPARE_PREFIX = "NUCLEUS_C139_COMPARE:"
C140_RHS_PREFIX = "NUCLEUS_C140_RHS:"
C141_CACHE_PREFIX = "NUCLEUS_C141_CACHE:"
C142_MISS_PREFIX = "NUCLEUS_C142_MISS:"
C143_HEAD_PREFIX = "NUCLEUS_C143_HEADS:"
C145_ACTION_PREFIX = "NUCLEUS_C145_ACTIONS:"
C146_BINDING_PREFIX = "NUCLEUS_C146_BINDING:"
C147_UPPER_PREFIX = "NUCLEUS_C147_UPPER:"
C148_GROUP_PREFIX = "NUCLEUS_C148_GROUP:"


def parse_traces(stderr: bytes):
    rows = []
    for line in stderr.decode(errors="replace").splitlines():
        if not line.startswith(PREFIX):
            continue
        head, value = line[len(PREFIX):].split(":type=", 1)
        fields = dict(piece.split("=", 1) for piece in head.split(":"))
        assert KEYS <= fields.keys(), line
        assert (int(fields["application"]), int(fields["function"]),
                int(fields["argument"])) == (8835, 8805, 8834), line
        before, after = int(fields["before"]), int(fields["after"])
        assert 0 <= after <= before, (before, after)
        assert fields["pi_head"] in ("true", "false")
        assert fields["type_proven"] in ("true", "false")
        rows.append({"context": int(fields["context"]),
                     "before": before, "after": after,
                     "charged": before - after,
                     "pi_head": fields["pi_head"] == "true",
                     "type_proven": fields["type_proven"] == "true",
                     "type_preview": value[:800]})
    return rows


def source_app_edges(source: bytes):
    """The exact exported AST, not guessed function-spine associations."""
    return {row["ie"]: row["app"] for line in source.splitlines()
            if (row := json.loads(line)).get("ie") is not None
            and isinstance(row.get("app"), dict)}


def parse_app_edges(stderr: bytes, source_edges):
    rows = []
    for line in stderr.decode(errors="replace").splitlines():
        if not line.startswith(EDGE_PREFIX):
            continue
        fields = dict(item.split("=", 1) for item in line[len(EDGE_PREFIX):].split(":"))
        app, fun, arg = (int(fields[key]) for key in ("app", "fun", "arg"))
        assert source_edges.get(app) == {"fn": fun, "arg": arg}, line
        before, after = int(fields["before"]), int(fields["after"])
        assert before >= after >= 0, line
        assert fields["pi_head"] in ("true", "false"), line
        assert fields["type_proven"] in ("true", "false"), line
        rows.append({"app": app, "fun": fun, "arg": arg, "context": int(fields["context"]),
                     "charged": before - after, "before": before, "after": after,
                     "pi_head": fields["pi_head"] == "true",
                     "type_proven": fields["type_proven"] == "true"})
    return rows


def parse_arg_obligations(stderr: bytes, source_edges):
    rows = []
    for line in stderr.decode(errors="replace").splitlines():
        if not line.startswith(ARG_PREFIX):
            continue
        record, judgment = line[len(ARG_PREFIX):].split(":judgment=", 1)
        fields = dict(item.split("=", 1) for item in record.split(":"))
        app, fun, arg = (int(fields[key]) for key in ("app", "fun", "arg"))
        assert (app, fun, arg) == (8805, 8753, 8804), line
        assert source_edges.get(app) == {"fn": fun, "arg": arg}, line
        before, after = int(fields["before"]), int(fields["after"])
        assert before >= after >= 0, line
        state = fields["state"]
        assert state in ("PROVEN", "UNKNOWN", "REFUTED"), line
        assert judgment.startswith(state.title()), line
        rows.append({"app": app, "fun": fun, "arg": arg, "context": int(fields["context"]),
                     "before": before, "after": after, "charged": before - after,
                     "state": state, "judgment_preview": judgment[:500]})
    return rows


def parse_conversion_stages(stderr: bytes, source_edges):
    """C131 stage receipts; source identity and stage status are not verdicts."""
    assert source_edges.get(8805) == {"fn": 8753, "arg": 8804}
    rows = []
    for line in stderr.decode(errors="replace").splitlines():
        if line.startswith(CONVERSION_INFER_PREFIX):
            record, descriptions = line[len(CONVERSION_INFER_PREFIX):].split(":inferred=", 1)
            inferred, expected = descriptions.split(":expected=", 1)
            fields = dict(item.split("=", 1) for item in record.split(":"))
            assert int(fields["expr"]) == 8804 and int(fields["context"]) == 0, line
            assert fields["state"] in ("PROVEN", "UNKNOWN", "REFUTED"), line
            assert inferred.startswith(fields["state"].title()), line
            before, after = int(fields["before"]), int(fields["after"])
            assert before >= after >= 0, line
            rows.append({"stage": "infer", "state": fields["state"],
                         "frame": int(fields["frame"]), "before": before,
                         "after": after, "charged": before - after,
                         "inferred_preview": inferred[:700], "expected_preview": expected[:700]})
        elif line.startswith(CONVERSION_RELATION_PREFIX):
            record, judgment = line[len(CONVERSION_RELATION_PREFIX):].split(":judgment=", 1)
            fields = dict(item.split("=", 1) for item in record.split(":"))
            assert int(fields["expr"]) == 8804 and int(fields["context"]) == 0, line
            assert fields["state"] in ("PROVEN", "UNKNOWN", "REFUTED"), line
            assert judgment.startswith(fields["state"].title()), line
            rows.append({"stage": "convert", "state": fields["state"],
                         "frame": int(fields["frame"]), "fuel": int(fields["fuel"]),
                         "judgment_preview": judgment[:700]})
    return rows


def parse_inner_arg_edges(stderr: bytes, source_edges):
    """Only accept real AST application edges and actual argument judgments."""
    rows = []
    for line in stderr.decode(errors="replace").splitlines():
        if not line.startswith(INNER_ARG_PREFIX):
            continue
        record, judgment = line[len(INNER_ARG_PREFIX):].split(":judgment=", 1)
        fields = dict(item.split("=", 1) for item in record.split(":"))
        app, fun, arg = (int(fields[k]) for k in ("app", "fun", "arg"))
        assert 8700 <= app <= 8804, line
        assert source_edges.get(app) == {"fn": fun, "arg": arg}, line
        state = fields["state"]
        assert state in ("PROVEN", "UNKNOWN", "REFUTED") and judgment.startswith(state.title()), line
        before, after = int(fields["before"]), int(fields["after"])
        assert before >= after >= 0, line
        rows.append({"app": app, "fun": fun, "arg": arg,
                     "context": int(fields["context"]), "state": state,
                     "before": before, "after": after, "charged": before - after,
                     "judgment_preview": judgment[:300]})
    return rows


def parse_c133_stages(stderr: bytes, source_edges):
    """The exact 8803→1477 source argument, without assuming conversion ran."""
    assert source_edges.get(8803) == {"fn": 8802, "arg": 1477}
    rows = []
    for line in stderr.decode(errors="replace").splitlines():
        if line.startswith(INNER_INFER_PREFIX):
            record, desc = line[len(INNER_INFER_PREFIX):].split(":inferred=", 1)
            inferred, expected = desc.split(":expected=", 1)
            stage = "infer"
        elif line.startswith(INNER_CONVERSION_PREFIX):
            record, judgment = line[len(INNER_CONVERSION_PREFIX):].split(":judgment=", 1)
            stage = "convert"
        else:
            continue
        fields = dict(piece.split("=", 1) for piece in record.split(":"))
        assert int(fields["expr"]) == 1477 and int(fields["context"]) == 0, line
        state = fields["state"]
        assert state in ("PROVEN", "UNKNOWN", "REFUTED"), line
        row = {"stage": stage, "state": state, "frame": int(fields["frame"])}
        if stage == "infer":
            assert inferred.startswith(state.title()), line
            before, after = int(fields["before"]), int(fields["after"])
            assert before >= after >= 0, line
            row.update(before=before, after=after, charged=before-after,
                       inferred_preview=inferred[:800], expected_preview=expected[:800])
        else:
            assert judgment.startswith(state.title()), line
            row.update(fuel=int(fields["fuel"]), judgment_preview=judgment[:800])
        rows.append(row)
    return rows


def parse_c134_owner_traces(stderr: bytes):
    """C134 never transports a receipt across a different captured pair."""
    owner, recursor = [], []
    for line in stderr.decode(errors="replace").splitlines():
        if line.startswith(C134_OWNER_PREFIX):
            fields = dict(p.split("=", 1) for p in line[len(C134_OWNER_PREFIX):].split(":"))
            assert tuple(int(fields[k]) for k in
                         ("actual", "actual_env", "expected", "expected_env")) == (
                             110, 66182, 1, 66180), line
            assert fields["outcome"] in ("PROVEN", "UNKNOWN", "REFUTED"), line
            owner.append({"budget": int(fields["budget"]),
                          "outcome": fields["outcome"]})
        elif line.startswith(C134_RECURSOR_PREFIX):
            record, heads = line[len(C134_RECURSOR_PREFIX):].split(":left=", 1)
            left, right = heads.split(":right=", 1)
            fields = dict(p.split("=", 1) for p in record.split(":"))
            recursor.append({"budget": int(fields["budget"]),
                             "depth": int(fields["depth"]),
                             "left_spine": int(fields["left_spine"]),
                             "right_spine": int(fields["right_spine"]),
                             "left_head_preview": left[:550],
                             "right_head_preview": right[:550]})
    return {"owner": owner, "recursor": recursor}


def parse_c135_trials(stderr: bytes):
    """Evidence only for the checked one-step trial of source recursor NameId147."""
    rows = []
    for line in stderr.decode(errors="replace").splitlines():
        if not line.startswith(C135_TRIAL_PREFIX):
            continue
        record, obstruction = line[len(C135_TRIAL_PREFIX):].split(":obstruction=", 1)
        fields = dict(piece.split("=", 1) for piece in record.split(":"))
        assert fields["side"] == "right", line
        assert fields["outcome"] in ("PROVEN", "UNKNOWN", "REFUTED"), line
        assert fields["outcome"] == "PROVEN" or obstruction, line
        probe, remainder = (int(fields[key]) for key in
                            ("probe", "remaining_after_reservation"))
        assert probe >= 64 and remainder >= 0, line
        rows.append({"side": fields["side"], "probe": probe,
                     "remaining_after_reservation": remainder,
                     "outcome": fields["outcome"],
                     "obstruction_preview": obstruction[:400]})
    return rows


def parse_c136_routes(stderr: bytes):
    """Which existing positive rule acts at the exact second capture only."""
    allowed = {"pop", "same-value", "exact-source-capture", "left-eta", "right-eta",
               "checked-same-proposition", "checked-proof-local", "unit-like-free",
               "proof-free", "fixed-proof-function", "opaque-congruence",
               "rigid-application-congruence", "lazy-delta-conversion",
               "cheap-exposure-attempted", "cheap-exposure-unknown",
               "cheap-comparison-proven", "full-comparison-proven"}
    rows = []
    for line in stderr.decode(errors="replace").splitlines():
        if not line.startswith(C136_ROUTE_PREFIX):
            continue
        fields = dict(piece.split("=", 1) for piece in
                      line[len(C136_ROUTE_PREFIX):].split(":"))
        assert fields["event"] in allowed, line
        assert int(fields["remaining"]) >= 0, line
        rows.append({"event": fields["event"], "remaining": int(fields["remaining"])})
    return rows


def parse_c137_worklist(stderr: bytes):
    """Only exact-owner worklist entries; do not quotient captured environments."""
    rows = []
    for line in stderr.decode(errors="replace").splitlines():
        if not line.startswith(C137_WORK_PREFIX):
            continue
        record, pair = line[len(C137_WORK_PREFIX):].split(":left=", 1)
        left, right = pair.split(":right=", 1)
        fields = dict(item.split("=", 1) for item in record.split(":"))
        pop, remaining, depth, pending = (int(fields[k]) for k in
                                          ("pop", "remaining", "depth", "pending"))
        assert pop == len(rows), line
        assert remaining >= 0 and depth >= 0 and pending >= 0, line
        assert left and right, line
        rows.append({"pop": pop, "remaining": remaining,
                     "depth": depth, "pending": pending,
                     "left": left[:450], "right": right[:450]})
    if rows:
        assert rows[0]["left"].startswith("Expr110@Env66182@Levels"), rows[0]
        assert rows[0]["right"].startswith("Expr1@Env66180@Levels"), rows[0]
    return rows


def parse_c138_deferred_route(stderr: bytes):
    """Rule stages for only the second deferred pair of the C137 source owner."""
    valid = {"pop", "same-value", "exact-source-capture", "left-eta", "right-eta",
             "checked-same-proposition", "checked-proof-local", "unit-like-free",
             "proof-free", "fixed-proof-function", "opaque-congruence",
             "rigid-application-congruence", "lazy-delta-conversion",
             "cheap-exposure-attempted", "cheap-exposure-status",
             "cheap-exposure-unknown", "cheap-comparison-proven",
             "cheap-comparison-unknown", "full-comparison-proven",
             "full-exposure-unknown", "full-comparison-unknown"}
    route = []
    for line in stderr.decode(errors="replace").splitlines():
        if not line.startswith(C138_DEFERRED_PREFIX):
            continue
        fields = dict(part.split("=", 1) for part in
                      line[len(C138_DEFERRED_PREFIX):].split(":"))
        assert fields.get("event") in valid, line
        row = {"event": fields["event"], "remaining": int(fields["remaining"])}
        assert row["remaining"] >= 0, line
        if row["event"] == "cheap-exposure-status":
            assert fields.get("left") in {"PROVEN", "UNKNOWN"}, line
            assert fields.get("right") in {"PROVEN", "UNKNOWN"}, line
            row.update(left=fields["left"], right=fields["right"])
        route.append(row)
    if route:
        assert route[0]["event"] == "pop", route
        assert len([r for r in route if r["event"] == "pop"]) == 1, route
    return route


def parse_c139_value_comparison(stderr: bytes):
    """Record, but never equate, value heads under one exact C138 call."""
    stages = {"enter", "neutral-head-PROVEN", "neutral-head-UNKNOWN",
              "neutral-head-REFUTED", "recursor-trial-PROVEN",
              "recursor-trial-UNKNOWN", "recursor-trial-REFUTED",
              "neutral-spine-work", "certified-relevance-PROVEN",
              "proof-irrelevance-PROVEN", "structure-eta-PROVEN",
              "recursor-reduced", "return-head-UNKNOWN",
              "return-head-REFUTED"}
    rows = []
    for line in stderr.decode(errors="replace").splitlines():
        if not line.startswith(C139_COMPARE_PREFIX):
            continue
        fields = dict(part.split("=", 1) for part in
                      line[len(C139_COMPARE_PREFIX):].split(":"))
        assert fields.get("stage") in stages, line
        assert int(fields["budget"]) > 0 and int(fields["depth"]) >= 0, line
        assert fields["left"] and fields["right"], line
        rows.append({"stage": fields["stage"], "budget": int(fields["budget"]),
                     "depth": int(fields["depth"]), "left": fields["left"],
                     "right": fields["right"]})
        assert len(rows) <= 128, "source-qualified log capped at 128 entries"
    if rows:
        assert rows[0]["stage"] == "enter", rows
    return rows


def parse_c140_rhs_exposure(stderr: bytes):
    """One exact right-hand exposure; no positive-value equality assumed."""
    rows = []
    for line in stderr.decode(errors="replace").splitlines():
        if not line.startswith(C140_RHS_PREFIX):
            continue
        fields = dict(part.split("=", 1) for part in
                      line[len(C140_RHS_PREFIX):].split(":"))
        assert fields["source"] == "8799" and fields["env"] == "0", line
        assert fields["outcome"] in {"PROVEN", "UNKNOWN", "REFUTED"}, line
        assert fields["head"].startswith(("Const", "Other")), line
        row = {"source": 8799, "env": 0,
               "budget": int(fields["budget"]), "outcome": fields["outcome"],
               "head": fields["head"]}
        for key in ("arity", "steps", "recursor_calls", "key_work"):
            row[key] = int(fields[key])
            assert row[key] >= 0, line
        assert row["budget"] > 0, line
        rows.append(row)
    assert len(rows) <= 1, "more than one exact C140 right-hand owner"
    return rows


def parse_c141_cache_provenance(stderr: bytes):
    """Exact exposure-cache provenance, not a proof of value equivalence."""
    allowed_events = {"lookup-hit", "lookup-miss", "uncached-proven",
                      "uncached-unknown", "uncached-refuted", "publication",
                      "publication-skipped"}
    rows = []
    for line in stderr.decode(errors="replace").splitlines():
        if not line.startswith(C141_CACHE_PREFIX):
            continue
        fields = dict(part.split("=", 1) for part in
                      line[len(C141_CACHE_PREFIX):].split(":"))
        assert fields["event"] in allowed_events, line
        assert (int(fields["source"]), int(fields["env"]),
                int(fields["levels"]), int(fields["pending"])) == (8799, 0, 0, 0), line
        assert fields["transparency"] in {"Full", "Reducible"}, line
        assert fields["preserve"] == "true", line
        assert fields["scope"] in {"true", "false"}, line
        assert fields["published"] in {"true", "false"}, line
        assert fields["head"].startswith(("Const", "Other", "None")), line
        assert int(fields["authority"]) >= 0 and int(fields["digest"]) >= 0, line
        assert int(fields["budget"]) > 0, line
        rows.append({"event": fields["event"], "source": 8799, "env": 0,
                     "levels": 0, "authority": int(fields["authority"]),
                     "transparency": fields["transparency"], "pending": 0,
                     "preserve": True, "digest": int(fields["digest"]),
                     "scope": fields["scope"] == "true",
                     "published": fields["published"] == "true",
                     "budget": int(fields["budget"]), "head": fields["head"]})
        assert len(rows) <= 4096, "unexpectedly broad cache trace"
    return rows


def parse_c142_exact_miss_cost(stderr: bytes):
    """Read-only work per exact cache miss; no claim of resumability."""
    rows = []
    for line in stderr.decode(errors="replace").splitlines():
        if not line.startswith(C142_MISS_PREFIX):
            continue
        fields = dict(part.split("=", 1) for part in
                      line[len(C142_MISS_PREFIX):].split(":"))
        assert (int(fields["source"]), int(fields["env"]),
                int(fields["levels"]), int(fields["pending"])) == (8799, 0, 0, 0), line
        assert fields["preserve"] == "true", line
        assert fields["transparency"] in ("Full", "Reducible"), line
        assert fields["scope"] in ("true", "false"), line
        assert fields["outcome"] in ("PROVEN", "UNKNOWN", "REFUTED"), line
        assert fields["head"].startswith(("Const", "Other", "None")), line
        budget = int(fields["budget"])
        steps, recursor_calls, key_work = (int(fields[k]) for k in
                                            ("steps", "recursor_calls", "key_work"))
        assert budget > 0 and steps >= 0 and recursor_calls >= 0 and key_work >= 0, line
        before, after = fields["fuel_before"], fields["fuel_after"]
        assert before == "none" or before.isdigit(), line
        assert after == "none" or after.isdigit(), line
        charged_fuel = None
        if before != "none" and after != "none":
            assert int(before) >= int(after), line
            charged_fuel = int(before) - int(after)
        rows.append({"source": 8799, "env": 0, "authority": int(fields["authority"]),
                     "transparency": fields["transparency"], "scope": fields["scope"] == "true",
                     "outcome": fields["outcome"], "head": fields["head"],
                     "budget": budget, "steps": steps,
                     "recursor_calls": recursor_calls, "key_work": key_work,
                     "fuel_before": before, "fuel_after": after,
                     "charged_fuel": charged_fuel})
        assert len(rows) <= 1024, "unexpectedly broad exact miss trace"
    return rows


def parse_c143_head_reuse_sample(stderr: bytes):
    """Sampled exact closures and full ExprId counts; neither implies convertibility."""
    rows = []
    for line in stderr.decode(errors="replace").splitlines():
        if not line.startswith(C143_HEAD_PREFIX):
            continue
        fields = dict(part.split("=", 1) for part in
                      line[len(C143_HEAD_PREFIX):].split(":"))
        assert int(fields["source"]) == 8799 and int(fields["env"]) == 0, line
        assert int(fields["authority"]) >= 0 and fields["scope"] in {"true", "false"}, line
        total = int(fields["total"])
        sampled = int(fields["sample_steps"])
        unique, repeats, overflow = (int(fields[k]) for k in
                                      ("sample_unique", "sample_repeats", "sample_overflow"))
        assert total >= sampled >= 0 and unique >= 0 and repeats >= 0 and overflow >= 0, line
        assert sampled == unique + repeats + overflow, line
        top = []
        for entry in fields["top"].split(","):
            if not entry:
                continue
            match = re.fullmatch(r"Expr(\d+)@(\d+)", entry)
            assert match, line
            top.append({"expr": int(match.group(1)), "count": int(match.group(2))})
        assert len(top) <= 8 and all(item["count"] > 0 for item in top), line
        assert sum(item["count"] for item in top) <= total, line
        rows.append({"source": 8799, "env": 0, "authority": int(fields["authority"]),
                     "scope": fields["scope"] == "true", "budget": int(fields["budget"]),
                     "total": total, "sample_steps": sampled, "sample_unique": unique,
                     "sample_repeats": repeats, "sample_overflow": overflow,
                     "top": top})
        assert rows[-1]["budget"] > 0 and len(rows) <= 8, line
    return rows


def parse_c145_action_mix(stderr: bytes):
    """Count real evaluator head actions; never promote counts to equality."""
    rows = []
    constructors = ("bvar", "app", "lam", "let", "proj", "const", "natlit", "other")
    bindings = ("bvar_closure", "bvar_free", "bvar_nat", "bvar_neutral", "bvar_unbound")
    for line in stderr.decode(errors="replace").splitlines():
        if not line.startswith(C145_ACTION_PREFIX):
            continue
        fields = dict(part.split("=", 1) for part in
                      line[len(C145_ACTION_PREFIX):].split(":"))
        assert (int(fields["source"]), int(fields["env"])) == (8799, 0), line
        assert fields["scope"] in ("true", "false"), line
        assert int(fields["authority"]) >= 0 and int(fields["budget"]) > 0, line
        counts = {name: int(fields[name]) for name in constructors + bindings +
                  ("total", "lam_beta", "lam_rigid")}
        assert all(n >= 0 for n in counts.values()), line
        assert sum(counts[k] for k in constructors) == counts["total"], line
        assert sum(counts[k] for k in bindings) == counts["bvar"], line
        assert counts["lam_beta"] + counts["lam_rigid"] == counts["lam"], line
        rows.append({"source": 8799, "env": 0, "authority": int(fields["authority"]),
                     "scope": fields["scope"] == "true", "budget": int(fields["budget"]),
                     **counts})
        assert len(rows) <= 8, "unexpectedly broad C145 source census"
    return rows


def parse_c146_binding_projection(stderr: bytes):
    """A sampled workload quotient, never a certificate to reuse a value."""
    rows = []
    keys = ("head_total", "bvar_total", "target_total", "sampled",
            "sample_missing", "sample_overflow", "pending_nonempty",
            "full_unique", "projected_unique", "full_repeats",
            "projected_repeats")
    for line in stderr.decode(errors="replace").splitlines():
        if not line.startswith(C146_BINDING_PREFIX):
            continue
        fields = dict(part.split("=", 1) for part in
                      line[len(C146_BINDING_PREFIX):].split(":"))
        assert (int(fields["source"]), int(fields["env"])) == (8799, 0), line
        assert fields["scope"] in ("true", "false"), line
        assert int(fields["authority"]) >= 0 and int(fields["budget"]) > 0, line
        counts = {key: int(fields[key]) for key in keys}
        assert all(n >= 0 for n in counts.values()), line
        total = counts["sampled"]
        eligible = total - counts["sample_missing"] - counts["sample_overflow"]
        assert (0 <= counts["target_total"] <= counts["bvar_total"]
                <= counts["head_total"]), line
        assert 0 <= counts["pending_nonempty"] <= total <= counts["target_total"], line
        assert 0 <= eligible <= total, line
        assert counts["full_unique"] + counts["full_repeats"] == eligible, line
        assert counts["projected_unique"] + counts["projected_repeats"] == eligible, line
        assert counts["projected_unique"] <= counts["full_unique"], line
        assert counts["projected_repeats"] >= counts["full_repeats"], line
        rows.append({"source": 8799, "env": 0, "authority": int(fields["authority"]),
                     "scope": fields["scope"] == "true", "budget": int(fields["budget"]),
                     **counts, "cross_frame_collapse": counts["full_unique"]
                     - counts["projected_unique"]})
        assert len(rows) <= 8, "unexpectedly broad C146 source census"
    return rows


def parse_c147_binding_upper_bound(stderr: bytes):
    """Only an optimistic revisit census; levels and pending are erased here."""
    rows = []
    keys = ("head_total", "target_total", "missing", "full_unique",
            "projected_unique", "full_repeats", "projected_repeats")
    for line in stderr.decode(errors="replace").splitlines():
        if not line.startswith(C147_UPPER_PREFIX):
            continue
        fields = dict(part.split("=", 1) for part in
                      line[len(C147_UPPER_PREFIX):].split(":"))
        assert (int(fields["source"]), int(fields["env"])) == (8799, 0), line
        assert fields["scope"] in ("true", "false"), line
        assert int(fields["authority"]) >= 0 and int(fields["budget"]) > 0, line
        assert fields["overflow"] in ("true", "false"), line
        counts = {key: int(fields[key]) for key in keys}
        assert all(n >= 0 for n in counts.values()), line
        total = counts["target_total"]
        assert total <= counts["head_total"] and counts["missing"] <= total, line
        assert counts["projected_unique"] <= counts["full_unique"] <= total, line
        complete = fields["overflow"] == "false"
        if complete:
            eligible = total - counts["missing"]
            assert counts["full_unique"] + counts["full_repeats"] == eligible, line
            assert counts["projected_unique"] + counts["projected_repeats"] == eligible, line
            assert counts["projected_repeats"] >= counts["full_repeats"], line
        rows.append({"source": 8799, "env": 0, "authority": int(fields["authority"]),
                     "scope": fields["scope"] == "true", "budget": int(fields["budget"]),
                     "overflow": not complete, "status": "COMPLETE_UPPER_BOUND_ONLY"
                     if complete else "UNKNOWN_OVERFLOW", **counts,
                     "optimistic_additional_key_merges": counts["full_unique"]
                     - counts["projected_unique"]})
        assert len(rows) <= 8, "unexpected C147 source breadth"
    return rows


def parse_c148_binding_group_sample(stderr: bytes):
    """Group-complete deterministic sample; full universe and pending context retained."""
    rows = []
    keys = ("head_total", "target_total", "sampled", "pending_nonempty",
            "missing", "full_unique", "projected_unique", "full_repeats",
            "projected_repeats")
    for line in stderr.decode(errors="replace").splitlines():
        if not line.startswith(C148_GROUP_PREFIX):
            continue
        fields = dict(part.split("=", 1) for part in
                      line[len(C148_GROUP_PREFIX):].split(":"))
        assert (int(fields["source"]), int(fields["env"])) == (8799, 0), line
        assert fields["scope"] in ("true", "false"), line
        assert int(fields["authority"]) >= 0 and int(fields["budget"]) > 0, line
        assert fields["overflow"] in ("true", "false"), line
        counts = {key: int(fields[key]) for key in keys}
        assert all(n >= 0 for n in counts.values()), line
        assert 0 <= counts["missing"] <= counts["target_total"] <= counts["head_total"], line
        assert 0 <= counts["pending_nonempty"] <= counts["sampled"] <= counts["target_total"], line
        assert counts["projected_unique"] <= counts["full_unique"] <= counts["sampled"], line
        complete = fields["overflow"] == "false"
        if complete:
            assert counts["full_unique"] + counts["full_repeats"] == counts["sampled"], line
            assert counts["projected_unique"] + counts["projected_repeats"] == counts["sampled"], line
            assert counts["projected_repeats"] >= counts["full_repeats"], line
        rows.append({"source": 8799, "env": 0, "authority": int(fields["authority"]),
                     "scope": fields["scope"] == "true", "budget": int(fields["budget"]),
                     "overflow": not complete, "status": "COMPLETE_GROUP_SAMPLE_ONLY"
                     if complete else "UNKNOWN_OVERFLOW", **counts,
                     "exact_context_additional_collisions": counts["full_unique"]
                     - counts["projected_unique"]})
        assert len(rows) <= 8, "unexpectedly broad C148 source sample"
    return rows


def validate_source(source: bytes):
    assert hashlib.sha256(source).hexdigest() == SOURCE_SHA256, "frozen N7 hash mismatch"
    app = None
    for line in source.splitlines():
        row = json.loads(line)
        if row.get("ie") == 8835:
            app = row.get("app")
            break
    assert app == {"fn": 8805, "arg": 8834}, "N7 expression 8835 shape drifted"


def summarize_owner_traces(stderr: bytes):
    """Capture resource-owner counters, not an inferred semantic equivalence."""
    lines = stderr.decode(errors="replace").splitlines()
    prefixes = ("NUCLEUS_C95_PHASE:", "NUCLEUS_C96_OWNER:",
                "NUCLEUS_C97_OWNER:", "NUCLEUS_C97_REPEAT_HEAD:",
                "NUCLEUS_NESTED_REPLAY_FAILURE:", "NUCLEUS_NESTED_RECURSOR_IOTA:")
    counts = {p[:-1]: sum(line.startswith(p) for line in lines) for p in prefixes}
    owners = [line for line in lines if line.startswith("NUCLEUS_C97_OWNER:")]
    def numeric(line, field):
        match = re.search(r"(?:^|:)" + re.escape(field) + r"=(\d+)(?=:|$)", line)
        return int(match.group(1)) if match else 0
    return {"counts": counts,
            "c97_total_spent": sum(numeric(line, "spent") for line in owners),
            "c97_max_spent": max((numeric(line, "spent") for line in owners), default=0),
            "c97_repeated_node_env": sum(numeric(line, "repeat_node_env") for line in owners),
            "c97_repeated_head_pending": sum(numeric(line, "repeat_head_pending") for line in owners),
            "owner_samples": owners[:3] + owners[-3:],
            "nested_failure_samples": [line[:350] for line in lines
                if line.startswith("NUCLEUS_NESTED_REPLAY_FAILURE:")][:6],
            "source_rhs_samples": [line[:350] for line in lines
                if line.startswith("NUCLEUS_NESTED_RECURSOR_IOTA:")][:8]}


def run(binary: Path, source: bytes, budget: int, trace: bool,
        owner_trace: bool = False, app_trace: bool = False,
        arg_trace: bool = False, conversion_trace: bool = False,
        app_arg_trace: bool = False, inner_infer_trace: bool = False,
        recursor_owner_trace: bool = False, recursor_trial_trace: bool = False,
        owner_route_trace: bool = False, owner_worklist_trace: bool = False,
        deferred_rule_trace: bool = False, value_comparison_trace: bool = False,
        rhs_exposure_work_trace: bool = False,
        cache_provenance_trace: bool = False,
        exact_miss_cost_trace: bool = False,
        head_reuse_sample_trace: bool = False,
        head_action_mix_trace: bool = False,
        binding_projection_trace: bool = False,
        binding_upper_bound_trace: bool = False,
        binding_group_sample_trace: bool = False):
    env = {k: v for k, v in os.environ.items() if not k.startswith("NUCLEUS_")}
    env.update(NUCLEUS_EXPERIMENTAL_RELEVANCE="1",
               NUCLEUS_EXPERIMENTAL_DEMAND_MAJOR="1")
    if trace:
        env.update(NUCLEUS_C126_N7_TYPE_HEAD="1",
                   NUCLEUS_TRACE_CHECKED_RELEVANCE="1",
                   NUCLEUS_TRACE_APPLICATION_FUNCTION_TYPE="1",
                   NUCLEUS_TRACE_DOWNSTREAM="1")
        if owner_trace:
            env.update(NUCLEUS_C95_PHASE_TRACE="1",
                       NUCLEUS_C96_MAJOR_TRACE="1",
                       NUCLEUS_C97_MAJOR_STEP_TRACE="1",
                       NUCLEUS_TRACE_NESTED_RECURSOR_IOTA_FAILURE="1",
                       NUCLEUS_TRACE_NESTED_RECURSOR_IOTA="1")
        if app_trace:
            env["NUCLEUS_C129_APP_EDGE"] = "1"
        if arg_trace:
            env["NUCLEUS_C130_APP_ARG"] = "1"
        if conversion_trace:
            env["NUCLEUS_C131_ARG_CONVERT"] = "1"
        if app_arg_trace:
            env["NUCLEUS_C132_APP_ARG"] = "1"
        if inner_infer_trace:
            env["NUCLEUS_C133_ARG_CONVERT"] = "1"
        if (recursor_owner_trace or recursor_trial_trace or owner_route_trace or
                owner_worklist_trace or deferred_rule_trace or value_comparison_trace or
                rhs_exposure_work_trace or cache_provenance_trace or exact_miss_cost_trace
                or head_reuse_sample_trace):
            env["NUCLEUS_C134_RECURSOR_OWNER"] = "1"
        if recursor_trial_trace:
            env["NUCLEUS_C135_RECURSOR_TRIAL"] = "1"
        if owner_route_trace:
            env["NUCLEUS_C136_OWNER_ROUTE"] = "1"
        if (owner_worklist_trace or deferred_rule_trace or value_comparison_trace or
                rhs_exposure_work_trace or cache_provenance_trace or exact_miss_cost_trace
                or head_reuse_sample_trace):
            env["NUCLEUS_C137_OWNER_WORKLIST"] = "1"
        if (deferred_rule_trace or value_comparison_trace or rhs_exposure_work_trace
                or cache_provenance_trace or exact_miss_cost_trace or head_reuse_sample_trace):
            env["NUCLEUS_C138_DEFERRED_ROUTE"] = "1"
        if value_comparison_trace:
            env["NUCLEUS_C139_EXACT_COMPARE"] = "1"
        if rhs_exposure_work_trace:
            env["NUCLEUS_C140_EXACT_RHS_WORK"] = "1"
        if cache_provenance_trace:
            env["NUCLEUS_C140_EXACT_RHS_WORK"] = "1"
            env["NUCLEUS_C141_EXACT_CACHE"] = "1"
        if exact_miss_cost_trace or head_reuse_sample_trace:
            env["NUCLEUS_C140_EXACT_RHS_WORK"] = "1"
            env["NUCLEUS_C141_EXACT_CACHE"] = "1"
            env["NUCLEUS_C142_EXACT_MISS_COST"] = "1"
        if head_reuse_sample_trace:
            env["NUCLEUS_C143_HEAD_REUSE_SAMPLE"] = "1"
        if head_action_mix_trace:
            env["NUCLEUS_C145_ACTIONS"] = "1"
        if binding_projection_trace:
            env["NUCLEUS_C146_BINDING_PROJECTED"] = "1"
        if binding_upper_bound_trace:
            env["NUCLEUS_C147_BINDING_UPPER"] = "1"
        if binding_group_sample_trace:
            env["NUCLEUS_C148_BINDING_GROUP"] = "1"
    process = subprocess.run([str(binary), str(budget)], input=source,
                             stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                             env=env, timeout=240)
    assert process.returncode in (0, 2), (budget, trace, process.returncode,
                                        process.stderr[-500:])
    return process


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("binary", type=Path)
    parser.add_argument("source", type=Path)
    parser.add_argument("--budgets", nargs="+", type=int, default=BUDGETS,
                        help="source-native diagnostic budget ladder; original C126 pair is the default")
    parser.add_argument("--owner-trace", action="store_true",
                        help="C128 read-only nested recursor owner phase/cost receipts")
    parser.add_argument("--app-trace", action="store_true",
                        help="C129 read-only source application dependency chain")
    parser.add_argument("--arg-trace", action="store_true",
                        help="C130 read-only source application argument obligation")
    parser.add_argument("--conversion-trace", action="store_true",
                        help="C131 separate source argument type inference and conversion")
    parser.add_argument("--app-arg-trace", action="store_true",
                        help="C132 read-only nested application argument judgment census")
    parser.add_argument("--inner-infer-trace", action="store_true",
                        help="C133 read-only exact inner argument Expr1477 inference and conversion")
    parser.add_argument("--recursor-owner-trace", action="store_true",
                        help="C134 exact second captured conversion owner and recursor mismatch")
    parser.add_argument("--recursor-trial-trace", action="store_true",
                        help="C135 certified recursor step outcome inside exact C134 owner")
    parser.add_argument("--owner-route-trace", action="store_true",
                        help="C136 positive source conversion rule inside exact second capture")
    parser.add_argument("--owner-worklist-trace", action="store_true",
                        help="C137 exact deferred worklist identities inside second capture")
    parser.add_argument("--deferred-rule-trace", action="store_true",
                        help="C138 only the first blocking C137 deferred equality's rule stages")
    parser.add_argument("--value-comparison-trace", action="store_true",
                        help="C139 exact blocked value comparison's nested rule and head stages")
    parser.add_argument("--rhs-exposure-work-trace", action="store_true",
                        help="C140 exact C139 right-hand evaluator loop, replay and key work")
    parser.add_argument("--cache-provenance-trace", action="store_true",
                        help="C141 exact right-hand exposure cache hit, miss and publication lineage")
    parser.add_argument("--exact-miss-cost-trace", action="store_true",
                        help="C142 source-qualified per-miss evaluator work and fuel ledger")
    parser.add_argument("--head-reuse-sample-trace", action="store_true",
                        help="C143 bounded head ExprId census and immutable closure-revisit sample")
    parser.add_argument("--head-action-mix-trace", action="store_true",
                        help="C145 disjoint source head constructors and dynamic BVar outcomes")
    parser.add_argument("--binding-projection-trace", action="store_true",
                        help="C146 compare exact and projected binding+pending sampled keys")
    parser.add_argument("--binding-upper-bound-trace", action="store_true",
                        help="C147 all hot BVar1/2 revisits with optimistic context-free key")
    parser.add_argument("--binding-group-sample-trace", action="store_true",
                        help="C148 full groups of bound nodes with complete levels and pending")
    args = parser.parse_args()
    if args.binding_projection_trace:
        args.head_action_mix_trace = True
    if args.head_action_mix_trace:
        args.head_reuse_sample_trace = True
    if args.binding_upper_bound_trace:
        args.head_reuse_sample_trace = True
    if args.binding_group_sample_trace:
        args.head_reuse_sample_trace = True
    source = args.source.read_bytes()
    validate_source(source)
    exact_edges = source_app_edges(source)
    binary = args.binary.resolve()
    observations = []
    assert all(budget > 0 for budget in args.budgets), "budgets must be positive"
    assert len(args.budgets) == len(set(args.budgets)), "repeated budgets obscure the ladder"
    for budget in args.budgets:
        silent = run(binary, source, budget, False)
        observed = run(binary, source, budget, True, args.owner_trace,
                       args.app_trace, args.arg_trace, args.conversion_trace,
                       args.app_arg_trace, args.inner_infer_trace,
                       args.recursor_owner_trace, args.recursor_trial_trace,
                       args.owner_route_trace, args.owner_worklist_trace,
                       args.deferred_rule_trace, args.value_comparison_trace,
                       args.rhs_exposure_work_trace, args.cache_provenance_trace,
                       args.exact_miss_cost_trace, args.head_reuse_sample_trace,
                       args.head_action_mix_trace, args.binding_projection_trace,
                       args.binding_upper_bound_trace,
                       args.binding_group_sample_trace)
        assert (silent.returncode, silent.stdout) == (observed.returncode, observed.stdout), (
            "observer changed the checker verdict or output", budget)
        heads = parse_traces(observed.stderr)
        assert heads, ("source 8835 type-head trace absent", budget)
        stderr_lines = observed.stderr.decode(errors="replace").splitlines()
        row = {"budget": budget,
                             "verdict_exit": observed.returncode,
                             "source_head_records": len(heads),
                             "pi_head_count": sum(r["pi_head"] for r in heads),
                             "proof_relevance_certificates": sum(
                                 s.startswith("NUCLEUS_CHECKED_RELEVANCE:")
                                 for s in stderr_lines),
                             "heads": heads[:8],
                             "last_downstream": [s[:350] for s in stderr_lines
                                                 if "NUCLEUS_DOWNSTREAM:" in s][-2:]}
        if args.owner_trace:
            row["owner_trace"] = summarize_owner_traces(observed.stderr)
        if args.app_trace:
            edges = parse_app_edges(observed.stderr, exact_edges)
            assert any(e["app"] == 8805 for e in edges), ("source 8805 edge absent", budget)
            row["source_app_edges"] = edges[:512]
            row["source_app_edge_count"] = len(edges)
        if args.arg_trace:
            obligations = parse_arg_obligations(observed.stderr, exact_edges)
            assert obligations, ("source 8805 argument obligation absent", budget)
            row["source_arg_obligations"] = obligations[:8]
        if args.conversion_trace:
            stages = parse_conversion_stages(observed.stderr, exact_edges)
            assert any(s["stage"] == "infer" for s in stages), ("inference receipt absent", budget)
            # A type-inference UNKNOWN must *not* invent a conversion call.
            # Conversion is attempted only on a PROVEN inferred type.
            if any(s["stage"] == "infer" and s["state"] == "PROVEN" for s in stages):
                assert any(s["stage"] == "convert" for s in stages), (
                    "proven inference without expected conversion receipt", budget)
            row["source_arg_conversion_stages"] = stages[:24]
        if args.app_arg_trace:
            inner_args = parse_inner_arg_edges(observed.stderr, exact_edges)
            assert inner_args, ("no source-native inner argument judgments", budget)
            row["inner_source_arg_edges"] = inner_args[:1024]
            row["inner_source_arg_count"] = len(inner_args)
        if args.inner_infer_trace:
            stages = parse_c133_stages(observed.stderr, exact_edges)
            assert any(s["stage"] == "infer" for s in stages), (
                "source Expr1477 type inference absent", budget)
            if any(s["stage"] == "infer" and s["state"] == "PROVEN" for s in stages):
                assert any(s["stage"] == "convert" for s in stages), (
                    "proven inner inference but no conversion receipt", budget)
            row["source_1477_stages"] = stages[:24]
            source_rows = [json.loads(line) for line in source.splitlines()
                           if json.loads(line).get("ie") == 1477]
            assert len(source_rows) == 1, "source Expr1477 not uniquely represented"
            row["source_1477_ast"] = source_rows[0]
        if (args.recursor_owner_trace or args.recursor_trial_trace or
                args.owner_route_trace or args.owner_worklist_trace or
                args.deferred_rule_trace or args.value_comparison_trace or
                args.rhs_exposure_work_trace or args.cache_provenance_trace or
                args.exact_miss_cost_trace or args.head_reuse_sample_trace):
            traced = parse_c134_owner_traces(observed.stderr)
            assert traced["owner"], ("exact captured conversion owner absent", budget)
            row["second_captured_conversion_owner"] = traced
        if args.recursor_trial_trace:
            trials = parse_c135_trials(observed.stderr)
            assert trials, ("exact captured recursor trial absent", budget)
            row["second_captured_recursor_trials"] = trials
        if args.owner_route_trace:
            route = parse_c136_routes(observed.stderr)
            assert any(step["event"] == "pop" for step in route), (
                "exact captured conversion route absent", budget)
            row["second_captured_conversion_route"] = route
        if (args.owner_worklist_trace or args.deferred_rule_trace or
                args.value_comparison_trace or args.rhs_exposure_work_trace or
                args.cache_provenance_trace or args.exact_miss_cost_trace or
                args.head_reuse_sample_trace):
            entries = parse_c137_worklist(observed.stderr)
            assert entries, ("exact captured deferred worklist absent", budget)
            row["second_captured_conversion_worklist"] = entries
        if (args.deferred_rule_trace or args.value_comparison_trace or
                args.rhs_exposure_work_trace or args.cache_provenance_trace or
                args.exact_miss_cost_trace or args.head_reuse_sample_trace):
            entries = row["second_captured_conversion_worklist"]
            assert len(entries) >= 3 and entries[2]["pop"] == 2, entries
            assert entries[2]["left"].startswith("Expr1@Env66182@Levels"), entries[2]
            assert entries[2]["right"].startswith("Expr8799@Env0@Levels"), entries[2]
            route = parse_c138_deferred_route(observed.stderr)
            assert route, ("C138 second deferred equality trace absent", budget)
            row["second_deferred_conversion_route"] = route
        if args.value_comparison_trace:
            rows = parse_c139_value_comparison(observed.stderr)
            assert rows and rows[0]["depth"] == 0, (
                "C139 exact comparison entry absent", budget)
            row["second_deferred_value_comparison"] = rows
        if args.rhs_exposure_work_trace:
            rows = parse_c140_rhs_exposure(observed.stderr)
            assert len(rows) == 1, ("C140 exact RHS observer absent", budget)
            assert rows[0]["budget"] == row["second_deferred_conversion_route"][1]["remaining"], (
                "C140 right-hand allowance differs from C138", budget)
            row["second_deferred_rhs_exposure_work"] = rows[0]
        if args.cache_provenance_trace:
            cache_rows = parse_c141_cache_provenance(observed.stderr)
            assert cache_rows and any(r["scope"] for r in cache_rows), (
                "C141 exact scoped exposure absent", budget)
            row["exact_rhs_cache_provenance"] = cache_rows
        if args.exact_miss_cost_trace or args.head_reuse_sample_trace:
            cache_rows = parse_c141_cache_provenance(observed.stderr)
            assert any(r["scope"] for r in cache_rows), (
                "C142 companion source cache trace absent", budget)
            row["exact_rhs_cache_provenance"] = cache_rows
            cost_rows = parse_c142_exact_miss_cost(observed.stderr)
            assert cost_rows, ("C142 exact miss cost absent", budget)
            if budget == 65_536:
                assert any(r["scope"] for r in cost_rows), (
                    "C142 standard scoped miss cost absent", budget)
            else:
                assert any(r["scope"] and r["event"] == "lookup-hit"
                           for r in cache_rows), (
                    "C142 diagnostic expected prior C141 scoped hit", budget)
            row["exact_rhs_miss_cost"] = cost_rows
        if args.head_reuse_sample_trace:
            reuse = parse_c143_head_reuse_sample(observed.stderr)
            assert reuse and any(r["budget"] > 8_388_608 for r in reuse) == (
                budget > 8_388_608), ("C143 exact high producer census absent", budget)
            row["exact_rhs_head_reuse_sample"] = reuse
        if args.head_action_mix_trace:
            actions = parse_c145_action_mix(observed.stderr)
            assert actions and len(actions) == len(reuse), (
                "C145 action-mix census absent or mismatched", budget)
            for counted, sampled in zip(actions, reuse):
                assert (counted["budget"], counted["scope"], counted["total"]) == (
                    sampled["budget"], sampled["scope"], sampled["total"]), (
                    "C145 changes C143 exact source-head count", budget)
            row["exact_rhs_head_actions"] = actions
        if args.binding_projection_trace:
            projections = parse_c146_binding_projection(observed.stderr)
            assert projections and len(projections) == len(actions), (
                "C146 source binding census absent or mismatched", budget)
            for binding, counted, sampled in zip(projections, actions, reuse):
                assert (binding["budget"], binding["scope"], binding["head_total"],
                        binding["bvar_total"]) == (
                        counted["budget"], counted["scope"], counted["total"],
                        counted["bvar"]), "C146 inconsistent with C145 conserved heads"
                assert binding["target_total"] == sum(
                    entry["count"] for entry in sampled["top"]
                    if entry["expr"] in (1, 6, 11)), (
                    "C146 three source BVars do not conserve C143 ID counts", budget)
            row["exact_rhs_binding_projection_sample"] = projections
        if args.binding_upper_bound_trace:
            uppers = parse_c147_binding_upper_bound(observed.stderr)
            assert uppers and len(uppers) == len(reuse), (
                "C147 full target census absent or mismatched", budget)
            for upper, sampled in zip(uppers, reuse):
                assert (upper["budget"], upper["scope"], upper["head_total"]) == (
                    sampled["budget"], sampled["scope"], sampled["total"]), (
                    "C147 exact source-head count mismatch", budget)
                assert upper["target_total"] == sum(
                    entry["count"] for entry in sampled["top"]
                    if entry["expr"] in (6, 11)), (
                    "C147 target visits disagree with source IDs", budget)
                assert upper["status"] == "COMPLETE_UPPER_BOUND_ONLY", (
                    "C147 bounds unavailable: key-set overflow", budget)
            row["exact_rhs_binding_optimistic_upper"] = uppers
        if args.binding_group_sample_trace:
            groups = parse_c148_binding_group_sample(observed.stderr)
            assert groups and len(groups) == len(reuse), (
                "C148 full-group source sample absent", budget)
            for group, sampled in zip(groups, reuse):
                assert (group["budget"], group["scope"], group["head_total"]) == (
                    sampled["budget"], sampled["scope"], sampled["total"]), (
                    "C148 exact source-head mismatch", budget)
                assert group["target_total"] == sum(
                    entry["count"] for entry in sampled["top"]
                    if entry["expr"] in (6, 11)), (
                    "C148 BVar target source count inconsistent", budget)
                assert group["missing"] == 0 and group["status"] == (
                    "COMPLETE_GROUP_SAMPLE_ONLY"), (
                    "C148 could not complete binding-group sample", budget)
            row["exact_rhs_binding_group_sample"] = groups
        observations.append(row)
    if args.app_arg_trace and len(observations) == 2:
        low, high = observations
        def by_source(row):
            return {entry["app"]: entry["state"] for entry in row["inner_source_arg_edges"]}
        left, right = by_source(low), by_source(high)
        difference = [{"app": app, "standard": left[app], "diagnostic": right[app]}
                      for app in sorted(left.keys() & right.keys()) if left[app] != right[app]]
        # No common-edge divergence is itself useful negative evidence:
        # inference may fail along a function-type route instead.
        observations.append({"c132_cross_budget_common_edges": len(left.keys() & right.keys()),
                             "c132_inner_argument_divergences": difference})
    print(json.dumps({"status": "CANDIDATE_C105_SURROGATE_NATIVE_REPLAY",
                      "lineage": "C105 descendant, not recovered C124/C125b source",
                      "source": "original unchanged magma-list-pair-n7",
                      "sha256": SOURCE_SHA256,
                      "configuration": ["NUCLEUS_EXPERIMENTAL_RELEVANCE",
                                        "NUCLEUS_EXPERIMENTAL_DEMAND_MAJOR"],
                      "observations": observations}, sort_keys=True))


if __name__ == "__main__":
    main()
