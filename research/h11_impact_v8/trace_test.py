#!/usr/bin/env python3
"""Instrument upstream pytest process: count entry into ReceiveBuffer.__bool__."""
import json, pathlib,sys
import pytest
suite=sys.argv[1]
report=pathlib.Path(sys.argv[2])
calls=0
target=pathlib.Path("h11/_receivebuffer.py").resolve()
def tracer(frame,event,arg):
    global calls
    if event=="call" and frame.f_code.co_name=="__bool__":
        if pathlib.Path(frame.f_code.co_filename).resolve()==target:
            calls+=1
    return tracer
sys.settrace(tracer)
try:
    outcome=pytest.main(["-q",suite])
finally:
    sys.settrace(None)
    report.write_text(json.dumps({"trace_status":"OK",
       "target":"h11/_receivebuffer.py:ReceiveBuffer.__bool__",
       "target_calls":calls,"pytest_exit":int(outcome) if "outcome" in locals() else None})+"\n")
sys.exit(int(outcome))
