#!/usr/bin/env python3
"""Execute only allowlisted upstream constructor and method with AST-decoded literals."""
import builtins,importlib,json,sys
rows=json.load(open(sys.argv[1],encoding="utf-8"))
def decode(v):
    if v["type"]=="bytes":return bytes.fromhex(v["value"])
    if v["type"] in ("str","int","float","bool","NoneType"):return v["value"]
    raise ValueError("UNKNOWN_INPUT_TYPE")
matched=0;failures=[]
for case in rows:
    module=case["constructor_module"]
    cls=case["constructor_class"]
    method=case["method"]
    name=case["expected_exception"]
    if not module.startswith("itsdangerous.") or any(not part.isidentifier() for part in (cls,method)):
        raise ValueError("DISALLOWED_SOURCE_OBJECT")
    expected=getattr(builtins,name,None)
    if expected is None or not isinstance(expected,type) or not issubclass(expected,BaseException):
        raise ValueError("UNKNOWN_EXCEPTION_CLASS")
    import_source=importlib.import_module(module)
    obj=getattr(import_source,cls)(*(decode(v) for v in case["constructor_args"]))
    caught=None
    try:
        getattr(obj,method)(*(decode(v) for v in case["method_args"]))
    except BaseException as exc:
        caught=type(exc)
    ok=caught is not None and issubclass(caught,expected)
    matched+=int(ok)
    if not ok:failures.append({"line":case["line"],"caught":caught.__name__ if caught else None,
                             "expected":name})
print(json.dumps({"total":len(rows),"matched":matched,"failures":failures},sort_keys=True))
