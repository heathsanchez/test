"""Deterministic FAMILY-BALANCED enumeration of the ORIGINAL source-pinned V104.

NO new selectors, builders or source-editing rules are defined here. Reuses
decisive_constructor._original's SHA-verified V104 program_candidates and
existing pre-cap 'allowed' grammar filtering, then schedules distinct original
selector/builder families round-robin within the SAME finite 64 emission budget.

This is a source-only exposed diagnostic, not autonomous policy acquisition
or native evidence. Host caller must verify every resulting candidate afresh.
"""
from __future__ import annotations
import ast
import hashlib
import json
from pathlib import Path

from . import decisive_constructor as verified

SCHEMA="UDM_V104_ORIGINAL_GRAMMAR_BALANCED_EMITTER_V7"


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def canonical(obj):
    return json.dumps(obj,sort_keys=True,separators=(",",":"),allow_nan=False)


def emit(source_repo,source,*,cap=64):
    if not isinstance(source,str) or not 0<cap<=320 or type(cap) is not int:
        raise ValueError("exact finite V104 original source text and cap<=320 required")
    try:ast.parse(source)
    except (SyntaxError,UnicodeError) as error:
        raise ValueError("unparseable original Python source") from error
    native,_=verified._original(source_repo)
    # Use the EXACT original V104 hash ordering for operation signatures.
    signatures=sorted([(tuple(s),tuple(b)) for s in native["SELECTORS"] for b in native["BUILDERS"]],
                      key=lambda pair:native["h"]("program|"+repr(pair)))
    rows,seen,calls=[],set(),0
    for slot_rank in range(1,cap+1):
        for signature in signatures:
            programs=native["program_candidates"](source,allowed={signature},cap=slot_rank)
            calls+=1
            if len(programs)<slot_rank:
                continue
            selector,builder,replacement=programs[slot_rank-1]
            if (tuple(selector),tuple(builder))!=signature:
                raise ValueError("original V104 signature left predeclared family")
            if replacement in seen:
                continue
            seen.add(replacement)
            spec={"selector":list(selector),"builder":list(builder),
                  "replacement":replacement,"slot_rank":slot_rank}
            rows.append({"id":sha(canonical(spec).encode()),**spec})
            if len(rows)==cap:
                return _answer(source,native,rows,cap,calls)
        if not rows:
            break
    return _answer(source,native,rows,cap,calls)


def _answer(source,native,rows,cap,calls):
    families=sorted({canonical((row["selector"],row["builder"])) for row in rows})
    return {"schema":SCHEMA,"scope":"EXPOSED_DIAGNOSTIC_ORIGINAL_GRAMMAR_ONLY",
            "source_pin":verified.SOURCE_PIN,
            "source_sha256":sha(source.encode()),
            "cap":cap,
            "emitted_count":len(rows),
            "unique_signature_families":len(families),
            "family_signatures":families,
            "rows":rows,"program_generator_calls":calls,
            "method":"ROUND_ROBIN_FAMILY_PREFIX_USING_ORIGINAL_ALLOWED_FILTER",
            "grammar_extension":"NONE",
            "verification":"NONE_NO_NATIVE_SOURCE_TEST",
            "native_calls":0,
            "G2":"UNKNOWN","G3":"UNKNOWN","G4":"UNKNOWN"}
