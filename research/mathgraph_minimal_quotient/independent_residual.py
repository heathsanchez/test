#!/usr/bin/env python3
"""Post-result independent native confirmation of the framing/error-hint residual.

This file was written AFTER examining the finite native quotient outcome.
It is an independent replay, not a new blind discovery, and intentionally uses
the real h11 public API rather than importing the original quotient observer.
"""
import json
import os
from pathlib import Path
import subprocess
import sys

BASE="62c5068c971579d61fa1b55373390e12f25fd856"
HEAD="05972a8b34faeb91c22b9a6283da84e45e7f0781"
REPO="python-hyper/h11"
CAP=96

def source_worker(root):
    sys.path.insert(0, str(Path(root).resolve()))
    import h11
    assert Path(root).resolve() in Path(h11.__file__).resolve().parents
    suites={
        "valid_big": b"GET / HTTP/1.0\r\nX: "+b"a"*96+b"\r\n\r\n",
        "malformed_big": b"GET / HTTP/1.0\r\nBad Header: "+b"a"*96+b"\r\n\r\n",
        "valid_small": b"GET / HTTP/1.0\r\nX: a\r\n\r\n",
        "malformed_small": b"GET / HTTP/1.0\r\nBad Header: a\r\n\r\n",
    }
    def one(wire,chunks):
        conn=h11.Connection(h11.SERVER,max_incomplete_event_size=CAP)
        for part in chunks:
            try:
                conn.receive_data(part)
                event=conn.next_event()
                if event is h11.NEED_DATA:continue
                return {"disposition":"ACCEPT","event":type(event).__name__}
            except h11.RemoteProtocolError as exc:
                return {"disposition":"REJECT","hint":exc.error_status_hint}
        return {"disposition":"INCOMPLETE"}
    result={}
    for name,wire in suites.items():
        result[name]={
            "nbytes":len(wire),"cap":CAP,
            "whole":one(wire,[wire]),
            "bytewise":one(wire,[wire[i:i+1] for i in range(len(wire))]),
        }
    print(json.dumps(result,sort_keys=True))

def main(root,out):
    root=Path(root)
    result={}
    for label,sha in (("base",BASE),("pr206",HEAD)):
        subprocess.run(["git","-C",str(root),"checkout","--quiet","--detach",sha],check=True)
        actual=subprocess.check_output(["git","-C",str(root),"rev-parse","HEAD"],text=True).strip()
        assert actual==sha
        p=subprocess.run([sys.executable,str(Path(__file__).resolve()),
                          "--source-worker",str(root.resolve())],
                         capture_output=True,text=True,check=True,timeout=25)
        result[label]=json.loads(p.stdout)
    a,b=result["base"],result["pr206"]
    assert a["valid_big"]["whole"]["disposition"]=="ACCEPT"
    assert a["valid_big"]["bytewise"]=={"disposition":"REJECT","hint":431}
    assert b["valid_big"]["whole"]==b["valid_big"]["bytewise"]=={"disposition":"REJECT","hint":431}
    assert a["malformed_big"]["whole"]==b["malformed_big"]["whole"]=={"disposition":"REJECT","hint":400}
    assert a["malformed_big"]["bytewise"]==b["malformed_big"]["bytewise"]=={"disposition":"REJECT","hint":431}
    for label in result:
        for schedule in ("whole","bytewise"):
            assert result[label]["valid_small"][schedule]["disposition"]=="ACCEPT"
            assert result[label]["malformed_small"][schedule]=={"disposition":"REJECT","hint":400}
    payload={"scope":"POST_HOC_INDEPENDENT_NATIVE_REPLAY_NOT_BLIND_DISCOVERY",
             "original_repo":REPO,"base_sha":BASE,"author_head_sha":HEAD,
             "native_result":result,
             "finding":"FULL_VALID_OVERLIMIT_REJECTED_BUT_MALFORMED_OVERLIMIT_ERROR_HINT_DEPENDS_ON_FRAMING",
             "policy_question":"Whether malformed+overlimit must always report 400 or 431 is UNKNOWN",
             "authority":"ADVISORY_ONLY"}
    Path(out).write_text(json.dumps(payload,indent=2)+"\n")
    print("MATHGRAPH_JPL_INDEPENDENT_RESIDUAL "+json.dumps({
        "valid_big":b["valid_big"],"malformed_big":b["malformed_big"],
        "valid_small":b["valid_small"],"malformed_small":b["malformed_small"]}))

if __name__=="__main__":
    if len(sys.argv)==3 and sys.argv[1]=="--source-worker":
        source_worker(sys.argv[2])
    elif len(sys.argv)==3:
        main(sys.argv[1],sys.argv[2])
    else:
        raise SystemExit("usage: independent_residual.py source_root output_json")
