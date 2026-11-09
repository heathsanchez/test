"""Fail-closed source inventory of explicit axiom dependencies.

This does not validate proof terms, authentic exporter provenance, the Lean
kernel, built-in primitive semantics, or external intended claims. It reports
only explicit axiom declarations reachable in a supported NDJSON subset.
"""

from __future__ import annotations

import hashlib
import json


class UnsupportedSource(ValueError):
    pass


def _unique_object(pairs: list[tuple[str, object]]) -> dict:
    obj = {}
    for key, value in pairs:
        if key in obj:
            raise UnsupportedSource(f"duplicate JSON key: {key}")
        obj[key] = value
    return obj


def _require_int(value: object) -> int:
    if not isinstance(value, int) or isinstance(value, bool) or value < 0:
        raise UnsupportedSource(f"invalid nonnegative index: {value!r}")
    return value


def trace_axioms(source: bytes, theorem: str) -> dict:
    """Inventory explicit export axioms reachable from a named theorem.

    Unknown source forms never produce a clean empty-axiom finding. The
    returned digest identifies exact bytes but does not authenticate them.
    """
    digest = hashlib.sha256(source).hexdigest()
    try:
        rows = [json.loads(line, object_pairs_hook=_unique_object)
                for line in source.splitlines() if line.strip()]
        if not rows or rows[0].get("meta", {}).get("format", {}).get("version") != "3.1.0":
            raise UnsupportedSource("unsupported or absent export format metadata")

        names: dict[int, str] = {0: ""}
        exprs: dict[int, dict] = {}
        decls: dict[str, tuple[str, dict]] = {}

        for row in rows[1:]:
            if "in" in row:
                i = _require_int(row["in"])
                part = row.get("str", row.get("num"))
                if i in names or not isinstance(part, dict):
                    raise UnsupportedSource("invalid or repeated name component")
                pre = _require_int(part.get("pre"))
                if pre not in names:
                    raise UnsupportedSource("unknown name prefix")
                segment = part.get("str", part.get("i"))
                if not isinstance(segment, (str, int)) or isinstance(segment, bool):
                    raise UnsupportedSource("unsupported name segment")
                names[i] = names[pre] + ("." if pre else "") + str(segment)
            elif "ie" in row:
                i = _require_int(row["ie"])
                if i in exprs or len(row) != 2:
                    raise UnsupportedSource("duplicate expression index or unrecognized expression field")
                exprs[i] = row
            else:
                for kind in ("axiom", "thm", "def", "opaque"):
                    if kind in row:
                        entry = row[kind]
                        name = names.get(_require_int(entry.get("name")))
                        if name is None or name in decls:
                            raise UnsupportedSource("unknown or repeated declaration name")
                        decls[name] = (kind, entry)
                        break

        if theorem not in decls or decls[theorem][0] != "thm":
            raise UnsupportedSource(f"theorem {theorem!r} absent from export")

        visiting_decls: set[str] = set()
        finished_decls: set[str] = set()
        axioms: set[str] = set()
        visiting_exprs: set[int] = set()

        def visit_decl(name: str) -> None:
            if name in finished_decls:
                return
            if name in visiting_decls:
                raise UnsupportedSource(f"cyclic declaration dependency: {name}")
            if name not in decls:
                raise UnsupportedSource(f"unresolved declaration reference: {name}")
            visiting_decls.add(name)
            kind, entry = decls[name]
            if kind == "axiom":
                visit_expr(_require_int(entry.get("type")))
                axioms.add(name)
            else:
                visit_expr(_require_int(entry.get("type")))
                # Opaque bodies and definitions can also carry assumptions.
                if "value" not in entry:
                    raise UnsupportedSource(f"declaration without visible proof/body: {name}")
                visit_expr(_require_int(entry["value"]))
            visiting_decls.remove(name)
            finished_decls.add(name)

        def visit_expr(i: int) -> None:
            if i in visiting_exprs:
                raise UnsupportedSource(f"cyclic expression reference: {i}")
            row = exprs.get(i)
            if row is None:
                raise UnsupportedSource(f"unresolved expression index: {i}")
            visiting_exprs.add(i)
            if "const" in row:
                name = names.get(_require_int(row["const"].get("name")))
                if name is None:
                    raise UnsupportedSource("unknown constant name")
                visit_decl(name)
            elif "app" in row:
                for field in ("fn", "arg"):
                    visit_expr(_require_int(row["app"].get(field)))
            elif "lam" in row or "forallE" in row:
                binder = row.get("lam", row.get("forallE"))
                for field in ("type", "body"):
                    visit_expr(_require_int(binder.get(field)))
            elif "letE" in row:
                for field in ("type", "value", "body"):
                    visit_expr(_require_int(row["letE"].get(field)))
            elif "sort" in row or "bvar" in row:
                pass
            else:
                raise UnsupportedSource(f"unsupported expression constructor at index {i}")
            visiting_exprs.remove(i)

        visit_decl(theorem)
        return {"status": "BOUNDED", "source_sha256": digest,
                "theorem": theorem, "explicit_axioms": sorted(axioms),
                "limitation": "explicit source axiom closure only; not a proof or intent warrant"}
    except (UnsupportedSource, KeyError, ValueError, TypeError, json.JSONDecodeError) as exc:
        return {"status": "UNKNOWN", "source_sha256": digest,
                "theorem": theorem, "reason": str(exc)}
