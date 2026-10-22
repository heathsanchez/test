"""Observe author-written pytest.raises context obligations without replacing their logic.

This plugin deliberately stores no payloads or secrets. It is documentary trace
evidence of exact native test execution, not a separately replayable witness.
"""
import functools
import hashlib
import inspect
import json
import os
from pathlib import Path
import pytest

_RECORDS=[]
_REAL_RAISES=pytest.raises
TEST_REL="tests/test_types/test_IntRange.py"

class _RaisesObserver:
    def __init__(self,real_cm,meta):
        self._cm=real_cm
        self._meta=meta
    def __enter__(self):
        return self._cm.__enter__()
    def __exit__(self,exc_type,exc_value,traceback):
        entry=dict(self._meta)
        entry["observed_exception"]=exc_type.__name__ if exc_type is not None else None
        try:
            handled=self._cm.__exit__(exc_type,exc_value,traceback)
            entry["native_context_accepted"]=bool(handled)
            return handled
        except BaseException as exc:
            entry["native_context_accepted"]=False
            entry["native_context_failure"]=type(exc).__name__
            raise
        finally:
            _RECORDS.append(entry)

def _wrap_raises(*args,**kwargs):
    frame=inspect.currentframe().f_back
    path=Path(frame.f_code.co_filename)
    origin=path.as_posix()
    expected=args[0] if args else kwargs.get("expected_exception")
    name=(expected.__module__+"."+expected.__qualname__) if isinstance(expected,type) else repr(type(expected))
    cm=_REAL_RAISES(*args,**kwargs)
    if len(args)!=1 or not origin.endswith(TEST_REL):
        return cm
    return _RaisesObserver(cm,{"test_path":TEST_REL,
        "source_line":frame.f_lineno,"expected_exception":name})

def pytest_configure(config):
    pytest.raises=_wrap_raises

def pytest_unconfigure(config):
    pytest.raises=_REAL_RAISES
    target=os.environ.get("MG_OBLIGATION_TRACE_JSON")
    if not target:return
    source=Path(os.environ["MG_ORIGINAL_UPSTREAM_TEST"])
    receipt={"schema":"mathgraph.runtime-pytest-raises-observations.v1",
      "source_author_test":"pallets/click@2247b35ea1c47c727d7a06e51fa280e12a863ff6",
      "test_source_sha256":hashlib.sha256(source.read_bytes()).hexdigest(),
      "obligations":_RECORDS,
      "obligation_occurrences":len(_RECORDS),
      "matched_occurrences":sum(bool(r["native_context_accepted"]) for r in _RECORDS),
      "scope":"one pinned test file and process; no independent invocation replay"}
    Path(target).write_text(json.dumps(receipt,indent=2,sort_keys=True)+"\n")
