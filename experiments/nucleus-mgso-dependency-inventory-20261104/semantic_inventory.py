"""Conservative, source-stable *candidate* declaration inventory for Lean NDJSON.

This is a source observer, not a Lean kernel, a proof checker, a trusted
environment snapshot, or a safe cache applicability algorithm. Nucleus's
preflight guards can depend on *future* declarations. Every identity computed
here is explicitly denied proof-skipping authority, even when it matches.

Supported source schema: the data constructors read by Nucleus's 3.1.0 parser.
The input-size cap deliberately precludes full Mathlib qualification here.
"""

from __future__ import annotations

import hashlib
import json


MAX_SOURCE = 20 << 20
SCHEMA = "nucleus.dependency_candidate.v1"


class InventoryError(ValueError):
    """The candidate inventory is incomplete/ambiguous and must abstain."""


def _pairs(pairs):
    obj = {}
    for key, value in pairs:
        if key in obj:
            raise InventoryError(f"duplicate JSON key {key}")
        obj[key] = value
    return obj


def _canonical(obj):
    return json.dumps(obj, sort_keys=True, separators=(",", ":"),
                      ensure_ascii=False, allow_nan=False).encode("utf-8")


def _sha(obj):
    return hashlib.sha256(_canonical(obj)).hexdigest()


def _integer(value, field):
    if type(value) is not int or value < 0 or value >= 2**64:
        raise InventoryError(f"invalid nonnegative integer: {field}")
    return value


def _list(value, field):
    if not isinstance(value, list):
        raise InventoryError(f"invalid array: {field}")
    return value


def _field(obj, key):
    if not isinstance(obj, dict) or key not in obj:
        raise InventoryError(f"missing field: {key}")
    return obj[key]


def _parse(source):
    if not isinstance(source, bytes) or not 0 < len(source) <= MAX_SOURCE:
        raise InventoryError("source size or type unsupported")
    records = []
    for i, line in enumerate(source.splitlines(), 1):
        try:
            records.append(json.loads(line, object_pairs_hook=_pairs,
                                      parse_constant=lambda x: (_ for _ in ()).throw(
                                          InventoryError(f"invalid numeric token {x}"))))
        except (json.JSONDecodeError, UnicodeDecodeError) as err:
            raise InventoryError(f"malformed JSON at line {i}: {err}") from err
    if not records or not isinstance(records[0], dict) or "meta" not in records[0]:
        raise InventoryError("missing export metadata")
    meta = records[0]
    if meta.get("meta", {}).get("format", {}).get("version") != "3.1.0":
        raise InventoryError("unsupported export schema")
    return meta, records[1:]


class _Normalizer:
    def __init__(self, records):
        self.names = {0: None}
        self.levels = {0: None}
        self.exprs = {}
        self.declarations = []
        self.n_cache = {0: ()}
        self.l_cache = {0: ["zero"]}
        self.e_cache = {}
        self.refs_cache = {}
        self.active = set()
        for rec in records:
            if not isinstance(rec, dict):
                raise InventoryError("unsupported non-object record")
            if "meta" in rec:
                raise InventoryError("duplicate metadata")
            if "in" in rec:
                ident = _integer(rec["in"], "in")
                if ident in self.names:
                    raise InventoryError("duplicate name id")
                kind = [k for k in ("str", "num") if k in rec]
                if len(kind) != 1 or set(rec) != {"in", kind[0]}:
                    raise InventoryError("unsupported name encoding")
                value = _field(rec, kind[0])
                if set(value) != ({"pre", "str"} if kind[0] == "str" else {"pre", "i"}):
                    raise InventoryError("unsupported name fields")
                self.names[ident] = (kind[0], value)
            elif "il" in rec:
                ident = _integer(rec["il"], "il")
                if ident in self.levels:
                    raise InventoryError("duplicate level id")
                kind = [k for k in ("succ", "max", "imax", "param") if k in rec]
                if len(kind) != 1 or set(rec) != {"il", kind[0]}:
                    raise InventoryError("unsupported level encoding")
                self.levels[ident] = (kind[0], rec[kind[0]])
            elif "ie" in rec:
                ident = _integer(rec["ie"], "ie")
                if ident in self.exprs:
                    raise InventoryError("duplicate expression id")
                kind = [k for k in ("bvar", "natVal", "strVal", "sort", "const",
                                    "app", "lam", "forallE", "letE", "proj") if k in rec]
                if len(kind) != 1 or set(rec) != {"ie", kind[0]}:
                    raise InventoryError("unsupported expression encoding")
                self.exprs[ident] = (kind[0], rec[kind[0]])
            else:
                kinds = [k for k in ("axiom", "def", "opaque", "thm", "quot", "inductive")
                         if k in rec]
                if len(kinds) != 1 or set(rec) != {kinds[0]}:
                    raise InventoryError("unsupported declaration constructor")
                self.declarations.append((kinds[0], rec[kinds[0]]))

    def _guard(self, kind, ident):
        node = (kind, ident)
        if node in self.active:
            raise InventoryError(f"cyclic {kind} reference")
        self.active.add(node)
        return node

    def name(self, ident):
        ident = _integer(ident, "name id")
        if ident in self.n_cache:
            return self.n_cache[ident]
        if ident not in self.names:
            raise InventoryError("missing name")
        token = self._guard("name", ident)
        try:
            kind, value = self.names[ident]
            prefix = self.name(_field(value, "pre"))
            raw = _field(value, kind if kind == "str" else "i")
            if kind == "str":
                if not isinstance(raw, str):
                    raise InventoryError("invalid string name")
            else:
                raw = _integer(raw, "numeric name")
            out = (*prefix, (kind, raw))
            self.n_cache[ident] = out
            return out
        finally:
            self.active.remove(token)

    def level(self, ident):
        ident = _integer(ident, "level id")
        if ident in self.l_cache:
            return self.l_cache[ident]
        if ident not in self.levels:
            raise InventoryError("missing universe level")
        token = self._guard("level", ident)
        try:
            kind, value = self.levels[ident]
            if kind == "succ":
                out = [kind, self.level(value)]
            elif kind in ("max", "imax"):
                parts = _list(value, kind)
                if len(parts) != 2:
                    raise InventoryError("malformed universe pair")
                out = [kind, self.level(parts[0]), self.level(parts[1])]
            else:
                out = [kind, self.name(value)]
            self.l_cache[ident] = out
            return out
        finally:
            self.active.remove(token)

    def expr(self, ident):
        ident = _integer(ident, "expression id")
        if ident in self.e_cache:
            return self.e_cache[ident], self.refs_cache[ident]
        if ident not in self.exprs:
            raise InventoryError("missing expression")
        token = self._guard("expression", ident)
        try:
            kind, raw = self.exprs[ident]
            refs = set()

            def child(n):
                out, found = self.expr(n)
                refs.update(found)
                return out

            if kind == "bvar":
                out = [kind, _integer(raw, kind)]
            elif kind == "natVal":
                if not isinstance(raw, str) or not raw.isdigit() or (len(raw) > 1 and raw[0] == "0"):
                    raise InventoryError("noncanonical Nat literal")
                out = [kind, raw]
            elif kind == "strVal":
                if not isinstance(raw, str):
                    raise InventoryError("invalid string literal")
                out = [kind, raw]
            elif kind == "sort":
                out = [kind, self.level(raw)]
            elif kind == "const":
                name = self.name(_field(raw, "name"))
                refs.add(name)
                out = [kind, name, [self.level(l) for l in _list(_field(raw, "us"), "us")]]
                if set(raw) != {"name", "us"}:
                    raise InventoryError("unsupported const expression")
            elif kind == "app":
                if set(raw) != {"fn", "arg"}:
                    raise InventoryError("unsupported application")
                out = [kind, child(raw["fn"]), child(raw["arg"])]
            elif kind in ("lam", "forallE"):
                if set(raw) != {"name", "binderInfo", "type", "body"}:
                    raise InventoryError("unsupported binder")
                out = [kind, self.name(raw["name"]), raw["binderInfo"],
                       child(raw["type"]), child(raw["body"])]
            elif kind == "letE":
                if not {"name", "type", "value", "body"}.issubset(raw) or (set(raw) - {"name", "type", "value", "body", "nondep"}):
                    raise InventoryError("unsupported let expression")
                out = [kind, self.name(raw["name"]), child(raw["type"]),
                       child(raw["value"]), child(raw["body"]), raw.get("nondep")]
            elif kind == "proj":
                if set(raw) != {"typeName", "idx", "struct"}:
                    raise InventoryError("unsupported projection")
                name = self.name(raw["typeName"])
                refs.add(name)
                out = [kind, name, _integer(raw["idx"], "projection index"), child(raw["struct"])]
            else:
                raise InventoryError("unsupported expression kind")
            result = (out, frozenset(refs))
            self.e_cache[ident], self.refs_cache[ident] = result
            return result
        finally:
            self.active.remove(token)

    def declaration(self, kind, raw):
        if not isinstance(raw, dict):
            raise InventoryError("invalid declaration")
        refs = set()

        def expression(field):
            normalized, found = self.expr(_field(raw, field))
            refs.update(found)
            return normalized

        if kind != "inductive":
            required = {
                "axiom": {"name", "levelParams", "type"},
                "def": {"name", "levelParams", "type", "value", "hints"},
                "opaque": {"name", "levelParams", "type", "value", "all", "isUnsafe"},
                "thm": {"name", "levelParams", "type", "value", "all"},
                "quot": {"name", "levelParams", "type", "kind"},
            }[kind]
            optional = {"axiom": {"isUnsafe"}, "def": {"all", "safety"}}.get(kind, set())
            if not required.issubset(raw) or (set(raw) - required - optional):
                raise InventoryError(f"unsupported {kind} declaration fields")
            name = self.name(raw["name"])
            normalized = {"kind": kind, "name": name,
                          "levelParams": [self.name(x) for x in _list(raw["levelParams"], "levelParams")],
                          "type": expression("type")}
            if "value" in raw:
                normalized["value"] = expression("value")
            if "all" in raw:
                normalized["all"] = [self.name(x) for x in _list(raw["all"], "all")]
            for key in ("hints", "safety", "isUnsafe", "kind"):
                if key in raw:
                    normalized[key] = raw[key]
            owned = (name,)
        else:
            if set(raw) != {"types", "ctors", "recs"}:
                raise InventoryError("unsupported inductive block")
            normalized = {"kind": kind, "types": [], "ctors": [], "recs": []}
            owned = []
            shapes = {
                "types": ("all", "ctors", "levelParams", "name", "type"),
                "ctors": ("levelParams", "name", "induct", "type"),
                "recs": ("all", "levelParams", "name", "type"),
            }
            for component in ("types", "ctors", "recs"):
                for item in _list(raw[component], component):
                    if not isinstance(item, dict):
                        raise InventoryError("unsupported inductive member")
                    result = {}
                    for key, value in item.items():
                        if key in ("name", "induct"):
                            result[key] = self.name(value)
                        elif key in ("all", "ctors", "levelParams"):
                            result[key] = [self.name(x) for x in _list(value, key)]
                        elif key == "type":
                            result[key], found = self.expr(value)
                            refs.update(found)
                        elif key == "rules" and component == "recs":
                            result[key] = []
                            for rule in _list(value, "rules"):
                                if set(rule) != {"ctor", "nfields", "rhs"}:
                                    raise InventoryError("unsupported recursor rule")
                                rhs, found = self.expr(rule["rhs"])
                                refs.update(found)
                                result[key].append({"ctor": self.name(rule["ctor"]),
                                                    "nfields": _integer(rule["nfields"], "nfields"),
                                                    "rhs": rhs})
                        elif key.startswith("is") or key in ("k", "cidx", "numFields", "numParams",
                                                                 "numIndices", "numNested", "numMinors", "numMotives"):
                            if type(value) not in (bool, int):
                                raise InventoryError("invalid inductive metadata")
                            result[key] = value
                        else:
                            raise InventoryError("unsupported inductive metadata")
                    if not set(shapes[component]).issubset(result):
                        raise InventoryError("incomplete inductive member")
                    owned.append(result["name"])
                    normalized[component].append(result)
            owned = tuple(owned)
            name = owned[0] if owned else ()
        return name, owned, normalized, refs


def _label(path):
    return ".".join(str(value) if kind == "str" else f"{value}#" for kind, value in path)


def inventory(source: bytes):
    """Return semantic candidate inventory; never issue a kernel verdict."""
    meta, records = _parse(source)
    normalizer = _Normalizer(records)
    declarations = []
    owners = {}
    normalized = []
    for index, (kind, raw) in enumerate(normalizer.declarations):
        name, all_owned, shape, direct = normalizer.declaration(kind, raw)
        for owner in all_owned:
            if owner in owners:
                raise InventoryError("duplicate declaration ownership")
            owners[owner] = index
        normalized.append((kind, name, shape, direct, tuple(all_owned)))

    for index, (kind, name, shape, direct, all_owned) in enumerate(normalized):
        dependency_names = set()
        for ref in direct:
            if kind == "inductive" and ref in all_owned:
                continue  # internal reference within one inductive block
            owner_index = owners.get(ref)
            if owner_index is None or owner_index >= index:
                raise InventoryError(f"constant not previously established: {_label(ref)}")
            dependency_names.add(ref)
        dependency_indices = sorted({owners[name] for name in dependency_names})
        shape_id = _sha({"schema": SCHEMA, "metadata": meta, "declaration": shape})
        dependencies = [declarations[i]["semantic_id"] for i in dependency_indices]
        support_id = _sha({"schema": SCHEMA, "owner": shape_id,
                           "dependencies": [declarations[i]["support_id"] for i in dependency_indices]})
        declarations.append({
            "index": index, "kind": kind, "name": _label(name),
            "name_key": _canonical(name).decode("utf-8"),
            "semantic_id": shape_id, "support_id": support_id,
            "direct_references": sorted(_label(p) for p in dependency_names),
            "direct_reference_keys": sorted(_canonical(p).decode("utf-8")
                                            for p in dependency_names),
            "direct_dependencies": dependencies,
            "source_observed_only": True,
        })
    return {"type": SCHEMA,
            "source_sha256": hashlib.sha256(source).hexdigest(),
            "context_sha256": _sha(meta),
            "status": "CANDIDATE_ONLY", "authority": "NONE",
            "complete_kernel_dependency_closure": "UNKNOWN",
            "fresh_kernel_invocations": 0, "proof_skips": 0,
            "declarations": declarations}


def compare(prior: bytes, current: bytes):
    """Compare candidate shapes; all verification reuse remains unauthorized."""
    left = inventory(prior)
    right = inventory(current)
    by_name = {record["name_key"]: record for record in left["declarations"]}
    after_name = {record["name_key"]: record for record in right["declarations"]}
    stable = [record["name"] for record in right["declarations"]
              if (old := by_name.get(record["name_key"])) is not None
              and old["semantic_id"] == record["semantic_id"]]
    reusable = [record["name"] for record in right["declarations"]
                if (old := by_name.get(record["name_key"])) is not None
                and old["support_id"] == record["support_id"]]
    return {"type": "nucleus.source-invalidation-comparison.v1",
            "original_source_sha256": left["source_sha256"],
            "current_source_sha256": right["source_sha256"],
            "unchanged_semantic_names": stable,
            "candidate_reuse_names": reusable,
            "candidate_reuse_count": len(reusable),
            "removed_names": sorted(by_name[key]["name"] for key in set(by_name) - set(after_name)),
            "new_or_changed_names": [record["name"] for record in right["declarations"]
                                     if record["name_key"] not in by_name
                                     or by_name[record["name_key"]]["semantic_id"] != record["semantic_id"]],
            "complete_kernel_dependency_closure": "UNKNOWN",
            "verification_reuse_authority": "NONE", "proof_skips": 0}
