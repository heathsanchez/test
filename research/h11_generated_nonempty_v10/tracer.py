#!/usr/bin/env python3
import json,pathlib,sys,pytest
suite=sys.argv[1];out=pathlib.Path(sys.argv[2])
target=pathlib.Path("h11/_receivebuffer.py").resolve()
calls=0
def trace(frame,event,arg):
    global calls
    if event=="call" and frame.f_code.co_name=="__bool__" and pathlib.Path(frame.f_code.co_filename).resolve()==target:
        calls+=1
    return trace
sys.settrace(trace)
try:
    outcome=pytest.main(["-q",suite])
finally:
    sys.settrace(None)
    out.write_text(json.dumps({"trace_status":"OK","target_calls":calls,"pytest_exit":int(outcome) if "outcome" in locals() else None})+"\n")
sys.exit(int(outcome))
