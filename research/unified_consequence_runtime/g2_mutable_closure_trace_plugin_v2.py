"""Source-neutral native profile for persisted nested closure observations.

Static AST patterns are supplied through the frozen observer. The plugin never
chooses or edits a source location. It samples only return events for the
statically detected production function, where current outer context and the
persistent callable read by that invocation are both still available.
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

_TARGETS: dict[tuple[str, int], list[dict[str, object]]] = {}
for _pattern in _PATTERNS:
    _abs = str((_WORLD / _pattern["path"]).resolve())
    _TARGETS.setdefault((_abs, int(_pattern["code_first_line"])), []).append(_pattern)


def _primitive(value):
    if value is None or isinstance(value, (bool, int, float, str)):
        return {"kind": "primitive", "value": value}
    if isinstance(value, tuple) and all(
        x is None or isinstance(x, (bool, int, float, str)) for x in value
    ):
        return {"kind": "tuple", "value": list(value)}
    if callable(value):
        return _callable(value)
    return {
        "kind": "object",
        "type": type(value).__module__ + "." + type(value).__qualname__,
    }


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
                        "firstlineno": (
                            int(inner_code.co_firstlineno) if inner_code else None
                        ),
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


def _profile(frame, event, arg):
    if event != "return":
        return
    key = (str(Path(frame.f_code.co_filename).resolve()), int(frame.f_code.co_firstlineno))
    patterns = _TARGETS.get(key, ())
    for pattern in patterns:
        if pattern["read_variable"] not in frame.f_locals:
            continue
        captures = {
            name: _primitive(frame.f_locals.get(name))
            for name in pattern["dynamic_captures"]
        }
        read_value = frame.f_locals.get(pattern["read_variable"])
        stored_value = _read_path(frame, pattern["attribute_path"])
        _EVENTS.append(
            {
                "pid": os.getpid(),
                "nodeid": _CURRENT_NODE,
                "path": pattern["path"],
                "function": pattern["function"],
                "function_line": pattern["function_line"],
                "code_first_line": pattern["code_first_line"],
                "guard_line": pattern["guard_line"],
                "observation_event": "RETURN",
                "read_variable": pattern["read_variable"],
                "dynamic_captures": captures,
                "read_callable": (
                    _callable(read_value)
                    if callable(read_value)
                    else _primitive(read_value)
                ),
                "stored_callable": (
                    _callable(stored_value)
                    if callable(stored_value)
                    else _primitive(stored_value)
                ),
            }
        )


def _flush():
    global _FLUSHED
    if _FLUSHED or not _LOG:
        return
    path = Path(_LOG)
    path.parent.mkdir(parents=True, exist_ok=True)
    row = {
        "schema": "UDM_G2_MUTABLE_CLOSURE_NATIVE_PROFILE_V2",
        "pid": os.getpid(),
        "events": _EVENTS,
    }
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(row, sort_keys=True, separators=(",", ":")) + "\n")
    _FLUSHED = True


def pytest_sessionstart(session):
    global _INSTALLED
    if not _INSTALLED:
        sys.setprofile(_profile)
        _INSTALLED = True


def pytest_runtest_setup(item):
    global _CURRENT_NODE
    _CURRENT_NODE = item.nodeid


def pytest_runtest_teardown(item, nextitem):
    global _CURRENT_NODE
    _CURRENT_NODE = None


def pytest_sessionfinish(session, exitstatus):
    sys.setprofile(None)
    _flush()


atexit.register(_flush)
