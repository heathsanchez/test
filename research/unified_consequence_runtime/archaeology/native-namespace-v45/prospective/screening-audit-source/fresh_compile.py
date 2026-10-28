#!/usr/bin/env python
"""Compile original declaration bytes independently; never execute their code.

CLI (launch only after authenticating the chosen local interpreter/profile)::

    /absolute/profile/python -I -B fresh_compile.py input.json output.json

The script is compatible with CPython 3.6.5 / pytest 5.4.3 and CPython 3.12.14 /
pytest 8.4.1.  Its only non-stdlib imports are installed pytest and its assertion
rewrite module.  It does not import repository modules, run pytest collection,
execute source modules, load a worker's expected-code.json, or use worker code.
Installed pytest is trusted tooling and is imported normally.

Input JSON (the ``sources`` shape also accepts the original compiler payload)::

    {
      "profile": {"python_version": "3.12.14", "pytest_version": "8.4.1"},
      "sources": {
        "tests/test_original.py": {
          "source": "<base64 of original bytes>",
          "source_sha256": "<independently selected original source digest>",
          "origins": {
            "tests/test_original.py::TestChild::test_inherited":
              "TestBase::test_inherited"
          }
        }
      }
    }

``profile`` is optional; if supplied, both fields are required and checked.
Exactly one byte representation is required in each source row: ``source`` or
``source_b64`` for strict base64, or ``source_bytes`` for a JSON list of integers
in [0,255].  The Python API also accepts a bytes/bytearray ``source_bytes``.
``source_sha256`` is required and verified before any source parsing/compiling.
Origins must be selected independently from original source/C3 resolution; the
script verifies each origin's unique lexical AST path and unique compiled-code
path, ending at a function, without evaluating decorators, imports, or bases.
It does not itself resolve class inheritance.  A prefix is the selected pytest
declaration prefix, while an origin identifies the actual original declaration.

API: ``compile_payload(payload) -> dict``.  No call executes compiled code.
The result includes per-mode hashes and the sorted distinct ``code_sha256``
allowlist, source and local AST hashes, and exact interpreter/pytest/rewrite
metadata.  AST hashes describe this interpreter's AST grammar; compare them
across equal interpreter versions only.  All logical source filenames must be
normalized relative POSIX paths.  The path handed to compile is that exact
logical path, and the serializer resolves/relativizes it against cwd exactly
as the original worker does.  This makes cwd's absolute prefix irrelevant.

Hash semantics were independently transcribed from the original v2 typed code
representation and v3 compatibility adaptation, read as source data.  The
serializer deliberately keeps absent-field and superseded-co_lnotab markers,
IEEE float bytes, recursive typed constants, exact JSON options, all portable
code fields, line tables, and original logical filenames.  It takes CodeType
objects directly, as the v45 fresh compiler does; no callable unwrapping occurs.
"""

from __future__ import print_function

import argparse
import ast
import base64
import hashlib
import inspect
import json
import pathlib
import platform
import struct
import sys
import types


SCHEMA = "INDEPENDENT_ORIGINAL_DECLARATION_COMPILE_V1"
PROFILES = {
    ("3.6.5", "5.4.3"),
    ("3.12.14", "8.4.1"),
}


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def canonical(value):
    # Defaults (notably ensure_ascii=True and allow_nan=True) match the worker.
    return json.dumps(value, sort_keys=True, separators=(",", ":"))


def file_identity(filename):
    path = pathlib.Path(filename).resolve()
    raw = path.read_bytes()
    return {"path": str(path), "sha256": digest(raw), "size": len(raw)}


def code_field(code, name):
    if not hasattr(code, name):
        return ["absent-code-field", name]
    value = getattr(code, name)
    return value.hex() if isinstance(value, bytes) else value


def typed_constant(value, world):
    if isinstance(value, types.CodeType):
        return ["code", portable_code(value, world)]
    if isinstance(value, tuple):
        return ["tuple", [typed_constant(item, world) for item in value]]
    if isinstance(value, frozenset):
        items = [typed_constant(item, world) for item in value]
        # This ordering intentionally uses the default json separators.
        items.sort(key=lambda item: json.dumps(item, sort_keys=True))
        return ["frozenset", items]
    if isinstance(value, bytes):
        return ["bytes", value.hex()]
    if isinstance(value, float):
        return ["float", struct.pack("!d", value).hex()]
    if isinstance(value, complex):
        return ["complex", typed_constant(value.real, world),
                typed_constant(value.imag, world)]
    if value is Ellipsis:
        return ["ellipsis"]
    if value is None or type(value) in (str, int, bool):
        return [type(value).__name__, value]
    raise TypeError("unsupported native code constant: " + type(value).__name__)


def portable_code(code, world):
    if type(code) is not types.CodeType:
        raise TypeError("portable_code requires a native CodeType")
    filename = code.co_filename
    try:
        filename = str(pathlib.Path(filename).resolve().relative_to(world))
    except ValueError:
        pass
    old_lines = (code_field(code, "co_lnotab")
                 if not hasattr(code, "co_linetable") else
                 ["superseded-code-field", "co_lnotab", "co_linetable"])
    return [
        code.co_argcount,
        code_field(code, "co_posonlyargcount"),
        code.co_kwonlyargcount,
        code.co_nlocals,
        code.co_stacksize,
        code.co_flags,
        code.co_code.hex(),
        typed_constant(code.co_consts, world),
        code.co_names,
        code.co_varnames,
        code.co_freevars,
        code.co_cellvars,
        filename,
        code.co_name,
        code_field(code, "co_qualname"),
        code.co_firstlineno,
        code_field(code, "co_linetable"),
        code_field(code, "co_exceptiontable"),
        old_lines,
    ]


def code_digest(code, world):
    return digest(canonical(portable_code(code, world)).encode())


def source_bytes(row):
    keys = [key for key in ("source", "source_b64", "source_bytes") if key in row]
    if len(keys) != 1:
        raise ValueError("each source needs exactly one byte representation")
    key = keys[0]
    value = row[key]
    if key != "source_bytes":
        if not isinstance(value, str):
            raise TypeError("base64 source must be a string")
        raw = base64.b64decode(value.encode("ascii"), validate=True)
    elif isinstance(value, (bytes, bytearray)):
        raw = bytes(value)
    else:
        if (not isinstance(value, list) or
                any(type(item) is not int or not 0 <= item <= 255 for item in value)):
            raise TypeError("source_bytes must contain integer bytes")
        raw = bytes(value)
    expected = row.get("source_sha256")
    if not isinstance(expected, str) or len(expected) != 64 or digest(raw) != expected:
        raise ValueError("original source digest mismatch")
    return raw


def logical_path(filename):
    if not isinstance(filename, str) or not filename:
        raise TypeError("source filename must be a nonempty string")
    path = pathlib.PurePosixPath(filename)
    if (path.is_absolute() or ".." in path.parts or "\\" in filename or
            str(path) != filename or "\x00" in filename):
        raise ValueError("source filename must be a normalized relative POSIX path")
    return filename


def origin_parts(origin):
    if not isinstance(origin, str):
        raise TypeError("declaration origin must be a string")
    parts = origin.split("::")
    if not parts or any(not part.isidentifier() for part in parts):
        raise ValueError("invalid original declaration origin: " + origin)
    return parts


def ast_declaration(tree, origin):
    current = tree
    declaration_types = (ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef)
    for name in origin_parts(origin):
        matches = [node for node in current.body
                   if isinstance(node, declaration_types) and node.name == name]
        if len(matches) != 1:
            raise ValueError("ambiguous or missing original AST declaration: " + origin)
        current = matches[0]
    if not isinstance(current, (ast.FunctionDef, ast.AsyncFunctionDef)):
        raise ValueError("original origin must end at a function: " + origin)
    return current


def compiled_declaration(module, origin):
    current = module
    for name in origin_parts(origin):
        matches = [value for value in current.co_consts
                   if type(value) is types.CodeType and value.co_name == name]
        if len(matches) != 1:
            raise ValueError("ambiguous or missing original compiled declaration: " + origin)
        current = matches[0]
    return current


def package_manifest(module):
    """Read package Python bytes, avoiding metadata/distribution helper imports."""
    location = pathlib.Path(module.__file__).resolve()
    root = location.parent
    # Older pytest distributions expose pytest.py rather than a pytest package.
    # Never recurse through the entire site-packages directory in that case.
    is_package = hasattr(module, "__path__")
    candidates = sorted(root.rglob("*.py")) if is_package else [location]
    files = []
    for path in candidates:
        if path.is_file():
            files.append({"path": str(path.relative_to(root)),
                          "sha256": digest(path.read_bytes())})
    return {"root": str(root), "is_package": is_package, "python_file_count": len(files),
            "python_files_sha256": digest(canonical(files).encode()),
            "python_files": files}


def tooling():
    import pytest
    import _pytest
    import _pytest.assertion.rewrite as rewrite

    pair = (platform.python_version(), pytest.__version__)
    if pair not in PROFILES:
        raise ValueError("unselected Python/pytest profile: " + repr(pair))
    if sys.implementation.name != "cpython":
        raise ValueError("only the selected CPython profiles are permitted")
    if sys.flags.optimize != 0:
        raise ValueError("optimized interpreter would change original compiler semantics")
    metadata = {
        "python_version": pair[0],
        "pytest_version": pair[1],
        "implementation": sys.implementation.name,
        "version_info": list(sys.version_info),
        "sys_version": sys.version,
        "executable": file_identity(sys.executable),
        "base_prefix": sys.base_prefix,
        "prefix": sys.prefix,
        "flags": {name: getattr(sys.flags, name) for name in
                  ("isolated", "ignore_environment", "no_user_site", "dont_write_bytecode", "optimize")},
        "pytest": file_identity(pytest.__file__),
        "rewrite": file_identity(rewrite.__file__),
        "rewrite_function": {
            "module": rewrite.rewrite_asserts.__module__,
            "name": rewrite.rewrite_asserts.__name__,
            "signature": str(inspect.signature(rewrite.rewrite_asserts)),
            "arguments_used": ["tree", "original_bytes", "logical_path"],
            "config": None,
        },
        "pytest_package": package_manifest(pytest),
        "_pytest_package": package_manifest(_pytest),
        "compiler": {"mode": "exec", "dont_inherit": True, "optimize": -1},
    }
    return metadata, rewrite.rewrite_asserts


def compile_payload(payload):
    if not isinstance(payload, dict) or not isinstance(payload.get("sources"), dict):
        raise TypeError("payload.sources must be an object")
    sources = payload["sources"]
    if not sources:
        raise ValueError("original sources must not be empty")
    metadata, rewrite_asserts = tooling()
    profile = payload.get("profile")
    if profile is not None:
        if (not isinstance(profile, dict) or
                set(profile) != {"python_version", "pytest_version"} or
                any(profile[name] != metadata[name] for name in profile)):
            raise ValueError("selected profile differs from actual interpreter/pytest")
    world = pathlib.Path.cwd().resolve()
    declarations = {}
    source_report = {}
    for filename, row in sorted(sources.items()):
        filename = logical_path(filename)
        if not isinstance(row, dict):
            raise TypeError("source entry must be an object")
        raw = source_bytes(row)
        origins = row.get("origins")
        if not isinstance(origins, dict) or not origins:
            raise ValueError("each source needs selected original origins")

        # Validate selection before modifying a fresh, separate AST for pytest.
        original_tree = ast.parse(raw, filename=filename)
        selected = {}
        for prefix, origin in sorted(origins.items()):
            if not isinstance(prefix, str) or not prefix or prefix in declarations:
                raise ValueError("invalid or duplicate selected declaration prefix")
            node = ast_declaration(original_tree, origin)
            selected[prefix] = {
                "origin": origin,
                "local_ast_sha256": digest(ast.dump(node, include_attributes=False).encode()),
                "declaration_kind": type(node).__name__,
                "declaration_line": node.lineno,
            }

        # The original module is compiled in full twice.  Neither CodeType is
        # executed or transformed into a callable, and no source import occurs.
        plain = compile(raw, filename, "exec", dont_inherit=True)
        rewrite_tree = ast.parse(raw, filename=filename)
        rewrite_asserts(rewrite_tree, raw, filename)
        rewritten = compile(rewrite_tree, filename, "exec", dont_inherit=True)

        for prefix, selection in sorted(selected.items()):
            origin = selection["origin"]
            modes = {}
            for mode, module in (("raw", plain), ("pytest_rewrite", rewritten)):
                code = compiled_declaration(module, origin)
                modes[mode] = {
                    "code_sha256": code_digest(code, world),
                    "co_filename": code.co_filename,
                    "normalized_co_filename": portable_code(code, world)[12],
                    "co_name": code.co_name,
                    "co_firstlineno": code.co_firstlineno,
                }
            result = dict(selection)
            result.update({
                "path": filename,
                "source_sha256": digest(raw),
                "code_sha256": sorted(set(item["code_sha256"] for item in modes.values())),
                "modes": modes,
            })
            declarations[prefix] = result
        source_report[filename] = {
            "source_sha256": digest(raw),
            "byte_length": len(raw),
            "selected_declaration_count": len(origins),
        }
    return {
        "schema": SCHEMA,
        "status": "COMPILED_ORIGINAL_DECLARATIONS_WITHOUT_EXECUTION",
        "helper": file_identity(__file__),
        "tooling": metadata,
        "sources": source_report,
        "declarations": declarations,
        "claims": {
            "source_execution": False,
            "repository_imports": False,
            "pytest_collection": False,
            "hash_modes": ["raw", "pytest_rewrite"],
            "code_serializer": "v2-typed-plus-v3-portable-code-fields",
            "filename_normalization": "resolve-relative-to-cwd-else-unchanged",
            "c3_origins": "provided-by-independent-source-selection;lexically-validated-here",
        },
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("input", help="JSON payload path, or - for stdin")
    parser.add_argument("output", help="fresh result path, or - for stdout")
    args = parser.parse_args()
    raw = (sys.stdin.buffer.read() if args.input == "-" else
           pathlib.Path(args.input).read_bytes())
    report = compile_payload(json.loads(raw.decode("utf-8")))
    rendered = canonical(report) + "\n"
    if args.output == "-":
        sys.stdout.write(rendered)
    else:
        # Refuse accidental replacement of prior audit evidence.
        with open(args.output, "x", encoding="utf-8") as handle:
            handle.write(rendered)


if __name__ == "__main__":
    main()
