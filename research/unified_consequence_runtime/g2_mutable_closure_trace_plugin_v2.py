"""Source-neutral nested-pytest observer for persistent closure state.

The outer protected author tests use Pytester to execute an inner pytest run.
This diagnostic plugin injects itself into that already-existing Pytester plugin
list and wraps the same pytest hook named by the statically detected source
pattern. It never edits source/test bytes or changes hook results.
"""
from __future__ import annotations

import atexit
import json
import os
from pathlib import Path
import sys

import pytest

_PATTERNS = json.loads(os.environ.get("UDM_G2_MUTABLE_CLOSURE_PATTERNS", "[]"))
_LOG = os.environ.get("UDM_G2_MUTABLE_CLOSURE_LOG")
_EVENTS: list[dict[str, object]] = []
_FLUSHED = False
_PLUGIN_NAME = __name__


def _primitive(value):
    if value is None or isinstance(value, (bool, int, float, str)):
        return {"kind": "primitive", "value": value}
    if isinstance(value, tuple) and all(
        x is None or isinstance(x, (bool, int, float, str)) for x in value
    ):
        return {"kind": "tuple", "value": list(value)}
    return None


def _callable(value):
    code = getattr(value, "__code__", None)
    result = {
        "kind": "callable",
        "identity": str(id(value)),
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
                primitive = _primitive(cell_value)
                if primitive is not None:
                    cells[name] = primitive
                elif callable(cell_value):
                    inner_code = getattr(cell_value, "__code__", None)
                    cells[name] = {
                        "kind": "callable",
                        "identity": str(id(cell_value)),
                        "module": getattr(cell_value, "__module__", None),
                        "qualname": getattr(cell_value, "__qualname__", None),
                        "firstlineno": (
                            int(inner_code.co_firstlineno) if inner_code else None
                        ),
                    }
                else:
                    cells[name] = {
                        "kind": "object",
                        "type": type(cell_value).__module__
                        + "."
                        + type(cell_value).__qualname__,
                    }
        result["closure"] = cells
    return result


def _read_item_path(pyfuncitem, path):
    if not path or path[0] != "pyfuncitem":
        return None
    value = pyfuncitem
    for name in path[1:]:
        try:
            value = getattr(value, name)
        except Exception:
            return None
    return value


def _external_context(pyfuncitem):
    out = {}
    for name, value in sorted(getattr(pyfuncitem, "funcargs", {}).items()):
        row = _primitive(value)
        if row is not None:
            out[name] = row
    return out


def _pytest_patterns():
    return [p for p in _PATTERNS if p.get("function") == "pytest_pyfunc_call"]


@pytest.hookimpl(wrapper=True, tryfirst=True)
def pytest_pyfunc_call(pyfuncitem):
    patterns = _pytest_patterns()
    pre = []
    for pattern in patterns:
        value = _read_item_path(pyfuncitem, pattern["attribute_path"])
        pre.append(_callable(value) if callable(value) else None)
    try:
        outcome = yield
        return outcome
    finally:
        # The protected failure itself throws through the wrapper. Observation
        # must therefore be exception-transparent and still record post-state.
        context = _external_context(pyfuncitem)
        for pattern, before in zip(patterns, pre):
            after_value = _read_item_path(pyfuncitem, pattern["attribute_path"])
            after = _callable(after_value) if callable(after_value) else None
            if before is None and after is None:
                continue
            _EVENTS.append(
                {
                    "pid": os.getpid(),
                    "rootpath": str(pyfuncitem.config.rootpath),
                    "nodeid": pyfuncitem.nodeid,
                    "path": pattern["path"],
                    "function": pattern["function"],
                    "pattern_id": pattern["pattern_id"],
                    "wrapper": pattern["wrapper"],
                    "attribute_path": pattern["attribute_path"],
                    "external_context": context,
                    "pre_callable": before,
                    "post_callable": after,
                }
            )


def pytest_runtest_setup(item):
    # The author tests call Pytester.runpytest() in-process. Pytester's explicit
    # plugin list is the correct non-mutating bridge into that nested run.
    for value in getattr(item, "funcargs", {}).values():
        if (
            value.__class__.__module__ == "_pytest.pytester"
            and value.__class__.__name__ == "Pytester"
            and hasattr(value, "plugins")
        ):
            if _PLUGIN_NAME not in value.plugins:
                value.plugins.append(_PLUGIN_NAME)
            # Avoid a duplicate env-based registration inside the new plugin manager.
            os.environ.pop("PYTEST_PLUGINS", None)


def _flush():
    global _FLUSHED
    if _FLUSHED or not _LOG:
        return
    path = Path(_LOG)
    path.parent.mkdir(parents=True, exist_ok=True)
    row = {
        "schema": "UDM_G2_MUTABLE_CLOSURE_NESTED_PYTEST_OBSERVATION_V2",
        "pid": os.getpid(),
        "events": _EVENTS,
    }
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(row, sort_keys=True, separators=(",", ":")) + "\n")
    _FLUSHED = True


def pytest_sessionfinish(session, exitstatus):
    _flush()


atexit.register(_flush)
