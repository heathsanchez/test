"""Source-neutral native trace for persisted nested closure observations.

Loaded only by the dedicated G2 V2 experiment. Static AST patterns are supplied
through an environment variable by the frozen observer. The plugin never chooses
or edits a source location.
"""
from __future__ import annotations

import atexit
import json
import os
from pathlib import Path
import sys

_PATTERNS = json.loads(os.environ.get("UDM_G2_MUTABLE_CLOSURE_PATTERNS", "[]"))
_WORLD = Path(os.environ.get("UDM_G2_WORLD_ROOT", ".")).resolve()
_LOG = os.environ.get("UDM_G2_MUTABLE_CLOSURE_LOG")
_EVENTS: list[dict[str, object]] = []
_CURRENT_NODE: str | None = None
_INSTALLED = False
_FLUSHED = False


def _primitive(value):
    if value is None or isinstance(value, (bool, int, float, str)):
        return {"kind": "primitive", "value": value}
    if isinstance(value, tuple) and all(x is None or isinstance(x, (bool, int, float, str)) for x in value):
        return {"kind": "tuple", "value": list(value)}
    if callable(value):
        return _callable(value)
    return {"kind": "object", "type": type(value).__module__ + "." + type(value).__qualname__}


def _callable(value):
    code = getattr(value, "__code__", None)
    result = {
        "kind": "callable",
        "module": getattr(value, "__module__", None),
        "qualname": getattr(value, "__qualname__", None),
    }
    if code is not None:
        result["firstlineno"] = int(code.co_firstlineno)
        result["freevars"] = list(code.co_freevars)
        closure = getattr(value, "__closure__", None) or ()
        cells = {}
        for name, cell in zip(code.co_freevars, closure):
            try:
                cell_value = cell.cell_contents
            except ValueError:
                cells[name] = {"kind": "empty"}
            else:
                if callable(cell_value):
                    inner_code = getattr(cell_value, "__code__", None)
                    cells[name] = {
                        "kind": "callable",
                        "module": getattr(cell_value, "__module__", None),
                        "qualname": getattr(cell_value, "__qualname__", None),
                        "firstlineno": int(inner_code.co_firstlineno) if inner_code else None,
                    }
                else:
                    cells[name] = _primitive(cell_value)
        result["closure"] = cells
    return result


def _read_path(frame, path):
    if not path:
        return None
    root = path[0]
    if root not in frame.f_locals:
        return None
    value = frame.f_locals[root]
    for name in path[1:]:
        try:
            value = getattr(value, name)
        except Exception:
            return None
    return value


def _trace(frame, event, arg):
    if event not in ("call", "line", "return"):
        return _trace
    try:
        filename = Path(frame.f_code.co_filename).resolve()
        rel = str(filename.relative_to(_WORLD)).replace(os.sep, "/")
    except Exception:
        return _trace
    for pattern in _PATTERNS:
        if rel != pattern["path"]:
            continue
        if frame.f_code.co_firstlineno != pattern["function_line"]:
            continue
        if event == "line" and frame.f_lineno == pattern["guard_line"]:
            captures = {
                name: _primitive(frame.f_locals.get(name))
                for name in pattern["dynamic_captures"]
            }
            read_value = frame.f_locals.get(pattern["read_variable"])
            stored_value = _read_path(frame, pattern["attribute_path"])
            _EVENTS.append({
                "pid": os.getpid(),
                "nodeid": _CURRENT_NODE,
                "path": rel,
                "function": pattern["function"],
                "function_line": pattern["function_line"],
                "guard_line": pattern["guard_line"],
                "read_variable": pattern["read_variable"],
                "dynamic_captures": captures,
                "read_callable": _callable(read_value) if callable(read_value) else _primitive(read_value),
                "stored_callable": _callable(stored_value) if callable(stored_value) else _primitive(stored_value),
            })
    return _trace


def _flush():
    global _FLUSHED
    if _FLUSHED or not _LOG or not _EVENTS:
        return
    path = Path(_LOG)
    path.parent.mkdir(parents=True, exist_ok=True)
    row = {"schema": "UDM_G2_MUTABLE_CLOSURE_NATIVE_TRACE_V2", "pid": os.getpid(), "events": _EVENTS}
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(row, sort_keys=True, separators=(",", ":")) + "\n")


def pytest_sessionstart(session):
    global _INSTALLED
    if not _INSTALLED:
        sys.settrace(_trace)
        _INSTALLED = True


def pytest_runtest_setup(item):
    global _CURRENT_NODE
    _CURRENT_NODE = item.nodeid


def pytest_runtest_teardown(item, nextitem):
    global _CURRENT_NODE
    _CURRENT_NODE = None


def pytest_sessionfinish(session, exitstatus):
    sys.settrace(None)
    _flush()


atexit.register(_flush)
