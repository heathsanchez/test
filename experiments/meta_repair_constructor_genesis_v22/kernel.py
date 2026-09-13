#!/usr/bin/env python3
"""Frozen V22 meta-repair constructor genesis kernel.

Repair programs are synthesized over the generic SET(source,target) edit
language. Repeated verified programs may be compiled into an anonymous schema
by generic first-order structural anti-unification.
"""
from __future__ import annotations

from dataclasses import dataclass
import hashlib
import itertools
import json
from typing import Any, Dict, Iterable, List, Mapping, Optional, Sequence, Tuple

from basis import (
    Cell,
    ConsequenceWorld,
    EditProgram,
    Mapping as CellMapping,
    SetEdit,
    apply_program,
    cell_atom,
    consequence_preserving_factorized_mappings,
    factorized_mapping_set,
    mapping_is_bijection,
    mapping_preserves_consequence,
    orbit_partition_from_mappings,
    program_term,
)


Term = Any


@dataclass(frozen=True)
class Residual:
    left: Cell
    right: Cell
    consequence: int
    left_orbit: int
    right_orbit: int

    def data(self) -> Any:
        return {
            "left": list(self.left),
            "right": list(self.right),
            "consequence": self.consequence,
            "left_orbit": self.left_orbit,
            "right_orbit": self.right_orbit,
        }


@dataclass(frozen=True)
class CompiledSchema:
    schema_id: str
    term: Term
    provenance: Tuple[str, ...]

    def data(self) -> Any:
        return {
            "schema_id": self.schema_id,
            "term": term_to_json(self.term),
            "provenance": list(self.provenance),
            "variable_count": len(schema_variables(self.term)),
            "concrete_constant_count": count_constants(self.term),
        }


def term_to_json(term: Term) -> Any:
    if isinstance(term, tuple):
        return [term_to_json(x) for x in term]
    return term


def is_var(term: Term) -> bool:
    return (
        isinstance(term, tuple)
        and len(term) == 2
        and term[0] == "VAR"
        and isinstance(term[1], int)
    )


def schema_variables(term: Term) -> Tuple[Term, ...]:
    out = set()

    def walk(t):
        if is_var(t):
            out.add(t)
        elif isinstance(t, tuple):
            for x in t:
                walk(x)

    walk(term)
    return tuple(sorted(out, key=lambda x: x[1]))


def count_constants(term: Term) -> int:
    if is_var(term):
        return 0
    if isinstance(term, tuple):
        if term and term[0] in ("SEQ", "SET"):
            return sum(count_constants(x) for x in term[1:])
        return sum(count_constants(x) for x in term)
    if isinstance(term, str) and term in ("SEQ", "SET"):
        return 0
    return 1


def generic_anti_unify(left: Term, right: Term) -> Optional[Term]:
    """Least general generalization for same-shaped first-order constructor terms.

    This routine knows only constructor equality, arity, atomic equality, and
    repeated disagreement-pair reuse. It contains no transformation-specific
    abstraction rule.
    """
    disagreements: Dict[Tuple[str, str], Term] = {}
    next_id = [0]

    def freeze(x: Term) -> str:
        return json.dumps(term_to_json(x), sort_keys=True, separators=(",", ":"))

    def rec(a: Term, b: Term) -> Optional[Term]:
        if a == b:
            return a

        if isinstance(a, tuple) or isinstance(b, tuple):
            if not (isinstance(a, tuple) and isinstance(b, tuple)):
                return None
            if is_var(a) or is_var(b):
                return None
            if not a or not b:
                return None
            if a[0] != b[0] or len(a) != len(b):
                return None
            children = []
            for xa, xb in zip(a[1:], b[1:]):
                child = rec(xa, xb)
                if child is None:
                    return None
                children.append(child)
            return (a[0], *children)

        key = (freeze(a), freeze(b))
        if key not in disagreements:
            disagreements[key] = ("VAR", next_id[0])
            next_id[0] += 1
        return disagreements[key]

    return rec(left, right)


def match_schema(
    schema: Term,
    ground: Term,
    seed: Optional[Mapping[Term, Term]] = None,
) -> Optional[Dict[Term, Term]]:
    bindings: Dict[Term, Term] = dict(seed or {})

    def rec(s: Term, g: Term) -> bool:
        if is_var(s):
            old = bindings.get(s)
            if old is None:
                bindings[s] = g
                return True
            return old == g

        if isinstance(s, tuple):
            if not isinstance(g, tuple):
                return False
            if len(s) != len(g) or not s or not g or s[0] != g[0]:
                return False
            return all(rec(xs, xg) for xs, xg in zip(s[1:], g[1:]))

        return s == g

    return bindings if rec(schema, ground) else None


def instantiate_schema(schema: Term, bindings: Mapping[Term, Term]) -> Optional[Term]:
    if is_var(schema):
        return bindings.get(schema)
    if isinstance(schema, tuple):
        children = []
        for x in schema[1:]:
            y = instantiate_schema(x, bindings)
            if y is None:
                return None
            children.append(y)
        return (schema[0], *children)
    return schema


def find_constructor_subterms(term: Term, constructor: str) -> Tuple[Term, ...]:
    out = []

    def walk(t):
        if isinstance(t, tuple):
            if t and t[0] == constructor:
                out.append(t)
            for x in t[1:]:
                walk(x)

    walk(term)
    return tuple(out)


def term_to_program(world: ConsequenceWorld, term: Term) -> Optional[EditProgram]:
    if not isinstance(term, tuple) or not term or term[0] != "SEQ":
        return None

    atom_to_cell = {
        cell_atom(world, cell): cell
        for cell in world.cells()
    }

    edits = []
    for child in term[1:]:
        if (
            not isinstance(child, tuple)
            or len(child) != 3
            or child[0] != "SET"
        ):
            return None
        source = atom_to_cell.get(child[1])
        target = atom_to_cell.get(child[2])
        if source is None or target is None:
            return None
        edits.append(SetEdit(source, target))

    try:
        edits.sort(key=lambda e: e.source)
        return EditProgram(tuple(edits))
    except ValueError:
        return None


class Kernel:
    @staticmethod
    def _authority(world: ConsequenceWorld) -> Optional[Dict[str, Any]]:
        if not world.complete:
            return {
                "status": "UNKNOWN_AUTHORITY",
                "reason": "consequence_table_incomplete",
            }
        return None

    def exhaust_current_language(self, world: ConsequenceWorld) -> Dict[str, Any]:
        auth = self._authority(world)
        if auth:
            return auth

        all_l0 = factorized_mapping_set(world)
        lawful = consequence_preserving_factorized_mappings(world)
        orbits = orbit_partition_from_mappings(world, lawful)

        return {
            "status": "VERIFIED",
            "candidate_count": len(all_l0),
            "lawful_count": len(lawful),
            "orbits": [[list(c) for c in orbit] for orbit in orbits],
            "_all_l0": all_l0,
            "_lawful": lawful,
            "_orbits": orbits,
        }

    def diagnose_residual(
        self,
        world: ConsequenceWorld,
        exhausted: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        auth = self._authority(world)
        if auth:
            return auth

        exhausted = exhausted or self.exhaust_current_language(world)
        if exhausted.get("status") != "VERIFIED":
            return exhausted

        orbits = exhausted["_orbits"]
        orbit_of: Dict[Cell, int] = {
            cell: i
            for i, orbit in enumerate(orbits)
            for cell in orbit
        }

        for i in range(len(orbits)):
            for j in range(i + 1, len(orbits)):
                for left in orbits[i]:
                    for right in orbits[j]:
                        lv = world.consequence(left)
                        rv = world.consequence(right)
                        if lv is not None and lv == rv:
                            residual = Residual(
                                left=left,
                                right=right,
                                consequence=int(lv),
                                left_orbit=i,
                                right_orbit=j,
                            )
                            return {
                                "status": "CERTIFIED_RESIDUAL",
                                "residual": residual.data(),
                                "_residual": residual,
                                "current_orbit_count": len(orbits),
                            }

        return {
            "status": "NO_RESIDUAL",
            "current_orbit_count": len(orbits),
        }

    @staticmethod
    def verify_program(
        world: ConsequenceWorld,
        residual: Residual,
        program: EditProgram,
        all_l0: frozenset[CellMapping],
        *,
        verification_enabled: bool = True,
    ) -> Dict[str, Any]:
        if not verification_enabled:
            return {
                "status": "UNKNOWN_NO_VERIFIER",
                "accepted": False,
            }

        mapping = apply_program(world, program)
        cells = world.cells()
        index = {cell: i for i, cell in enumerate(cells)}

        bijection = mapping_is_bijection(world, mapping)
        discharge = mapping[index[residual.left]] == residual.right
        consequence_ok = (
            mapping_preserves_consequence(world, mapping)
            if bijection else False
        )
        novel = mapping not in all_l0

        accepted = bijection and discharge and consequence_ok and novel

        return {
            "status": "VERIFIED" if accepted else "REJECTED",
            "accepted": accepted,
            "bijection": bijection,
            "residual_discharge": discharge,
            "consequence_preserving": consequence_ok,
            "novel_outside_current_language": novel,
            "mapping": [list(c) for c in mapping],
        }

    def synthesize_minimum_repair(
        self,
        world: ConsequenceWorld,
        residual: Residual,
        *,
        max_depth: int = 3,
        verification_enabled: bool = True,
    ) -> Dict[str, Any]:
        auth = self._authority(world)
        if auth:
            return auth
        if not verification_enabled:
            return {
                "status": "UNKNOWN_NO_VERIFIER",
                "frontier": [],
                "acquisition_search_count": 0,
            }

        all_l0 = factorized_mapping_set(world)
        cells = world.cells()
        tested = 0

        for depth in range(1, int(max_depth) + 1):
            valid: List[Tuple[EditProgram, Dict[str, Any]]] = []

            for sources in itertools.combinations(cells, depth):
                for targets in itertools.product(cells, repeat=depth):
                    edits = tuple(
                        SetEdit(source, target)
                        for source, target in zip(sources, targets)
                    )
                    program = EditProgram(edits)
                    tested += 1

                    verdict = self.verify_program(
                        world,
                        residual,
                        program,
                        all_l0,
                        verification_enabled=True,
                    )
                    if verdict["accepted"]:
                        valid.append((program, verdict))

            if valid:
                valid.sort(
                    key=lambda row: tuple(
                        (e.source, e.target)
                        for e in row[0].edits
                    )
                )
                return {
                    "status": "VERIFIED",
                    "minimum_edit_depth": depth,
                    "tested_program_count": tested,
                    "frontier": [p.data() for p, _ in valid],
                    "verification_rows": [
                        {
                            "program": p.data(),
                            "verdict": v,
                        }
                        for p, v in valid
                    ],
                    "_frontier_objects": tuple(p for p, _ in valid),
                    "acquisition_search_count": 1,
                }

        return {
            "status": "CERTIFIED_NO_REPAIR_WITHIN_EDIT_BOUND",
            "tested_program_count": tested,
            "frontier": [],
            "_frontier_objects": tuple(),
            "acquisition_search_count": 1,
        }

    def compile_schema(
        self,
        training: Sequence[Tuple[str, ConsequenceWorld, Residual, EditProgram]],
    ) -> Dict[str, Any]:
        if len(training) < 2:
            return {
                "status": "INSUFFICIENT_INDEPENDENT_REPAIRS",
            }

        terms = [
            program_term(world, program)
            for _origin, world, _residual, program in training
        ]

        schema = terms[0]
        for term in terms[1:]:
            schema = generic_anti_unify(schema, term)
            if schema is None:
                return {
                    "status": "NO_SCHEMA",
                }

        vars_ = schema_variables(schema)
        if not vars_:
            return {
                "status": "NO_ABSTRACTION",
            }

        matches = []
        for term in terms:
            bindings = match_schema(schema, term)
            if bindings is None:
                return {
                    "status": "SCHEMA_REPLAY_FAILED",
                }
            instantiated = instantiate_schema(schema, bindings)
            matches.append(instantiated == term)

        if not all(matches):
            return {
                "status": "SCHEMA_REPLAY_FAILED",
            }

        schema_constants = count_constants(schema)
        instance_constants = [count_constants(t) for t in terms]
        if not all(schema_constants < n for n in instance_constants):
            return {
                "status": "NO_COMPRESSION",
            }

        provenance = tuple(origin for origin, *_rest in training)
        schema_id = "mr_" + hashlib.sha256(
            json.dumps(
                term_to_json(schema),
                sort_keys=True,
                separators=(",", ":"),
            ).encode()
        ).hexdigest()[:16]

        compiled = CompiledSchema(
            schema_id=schema_id,
            term=schema,
            provenance=provenance,
        )

        return {
            "status": "VERIFIED",
            "schema": compiled.data(),
            "training_terms": [term_to_json(t) for t in terms],
            "training_replay": matches,
            "instance_constant_counts": instance_constants,
            "schema_constant_count": schema_constants,
            "_compiled": compiled,
        }

    @staticmethod
    def instantiate_for_obligation(
        world: ConsequenceWorld,
        residual: Residual,
        schema: CompiledSchema,
    ) -> Tuple[EditProgram, ...]:
        obligation = (
            "SET",
            cell_atom(world, residual.left),
            cell_atom(world, residual.right),
        )
        variables = set(schema_variables(schema.term))
        programs = []

        for subterm in find_constructor_subterms(schema.term, "SET"):
            bindings = match_schema(subterm, obligation)
            if bindings is None:
                continue
            if not variables.issubset(set(bindings)):
                continue
            ground = instantiate_schema(schema.term, bindings)
            if ground is None:
                continue
            program = term_to_program(world, ground)
            if program is not None:
                programs.append(program)

        unique = {
            tuple((e.source, e.target) for e in p.edits): p
            for p in programs
        }
        return tuple(unique[k] for k in sorted(unique))

    def solve_residual(
        self,
        world: ConsequenceWorld,
        residual: Residual,
        *,
        schema: Optional[CompiledSchema] = None,
        allow_acquisition_search: bool = True,
        verification_enabled: bool = True,
    ) -> Dict[str, Any]:
        auth = self._authority(world)
        if auth:
            return auth
        if not verification_enabled:
            return {
                "status": "UNKNOWN_NO_VERIFIER",
                "route": "STOP",
                "acquisition_search_count": 0,
            }

        all_l0 = factorized_mapping_set(world)

        if schema is not None:
            candidates = self.instantiate_for_obligation(
                world,
                residual,
                schema,
            )
            replay_rows = []
            for program in candidates:
                verdict = self.verify_program(
                    world,
                    residual,
                    program,
                    all_l0,
                    verification_enabled=True,
                )
                replay_rows.append({
                    "program": program.data(),
                    "verdict": verdict,
                })
                if verdict["accepted"]:
                    return {
                        "status": "VERIFIED",
                        "route": "REUSE_COMPILED_SCHEMA",
                        "program": program.data(),
                        "schema": schema.data(),
                        "replay_rows": replay_rows,
                        "acquisition_search_count": 0,
                        "_program": program,
                    }

            return {
                "status": "REPLAY_FAILED",
                "route": "REUSE_COMPILED_SCHEMA",
                "schema": schema.data(),
                "replay_rows": replay_rows,
                "acquisition_search_count": 0,
            }

        if not allow_acquisition_search:
            return {
                "status": "UNKNOWN_REPAIR_SCHEMA",
                "route": "STOP",
                "acquisition_search_count": 0,
            }

        synthesis = self.synthesize_minimum_repair(
            world,
            residual,
            verification_enabled=True,
        )
        if synthesis.get("status") != "VERIFIED":
            return {
                "status": synthesis.get("status"),
                "route": "SYNTHESIZE",
                "synthesis": {
                    k: v
                    for k, v in synthesis.items()
                    if not k.startswith("_")
                },
                "acquisition_search_count": synthesis.get(
                    "acquisition_search_count", 1
                ),
            }

        program = synthesis["_frontier_objects"][0]
        return {
            "status": "VERIFIED",
            "route": "SYNTHESIZE",
            "program": program.data(),
            "synthesis": {
                k: v
                for k, v in synthesis.items()
                if not k.startswith("_")
            },
            "acquisition_search_count": 1,
            "_program": program,
        }

    def develop(
        self,
        world: ConsequenceWorld,
        *,
        schema: Optional[CompiledSchema] = None,
        allow_acquisition_search: bool = True,
        verification_enabled: bool = True,
    ) -> Dict[str, Any]:
        auth = self._authority(world)
        if auth:
            return auth

        exhausted = self.exhaust_current_language(world)
        diagnosis = self.diagnose_residual(world, exhausted)

        if diagnosis.get("status") == "NO_RESIDUAL":
            return {
                "status": "VERIFIED_NO_GROWTH",
                "current_language": {
                    k: v for k, v in exhausted.items()
                    if not k.startswith("_")
                },
                "diagnosis": diagnosis,
                "constructor_growth_authorized": False,
                "acquisition_search_count": 0,
            }

        if diagnosis.get("status") != "CERTIFIED_RESIDUAL":
            return diagnosis

        residual = diagnosis["_residual"]
        solve = self.solve_residual(
            world,
            residual,
            schema=schema,
            allow_acquisition_search=allow_acquisition_search,
            verification_enabled=verification_enabled,
        )

        return {
            "status": solve.get("status"),
            "current_language": {
                k: v for k, v in exhausted.items()
                if not k.startswith("_")
            },
            "diagnosis": {
                k: v for k, v in diagnosis.items()
                if not k.startswith("_")
            },
            "constructor_growth_authorized": True,
            "repair": {
                k: v for k, v in solve.items()
                if not k.startswith("_")
            },
            "_residual": residual,
            "_program": solve.get("_program"),
            "acquisition_search_count": solve.get(
                "acquisition_search_count", 0
            ),
        }
