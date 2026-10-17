"""V13: source-derived *diagnostic* branch observations from protected native tests.

Instrumentation does NOT modify original source, author tests or the V10 native
verifier. A trace locates AST guards at runtime without supplying a filename,
line, replacement, or winning method. It is an observation, not causal proof,
not a universal Python sandbox and not prospective G2.
"""
from __future__ import annotations
import ast
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import tempfile
import time

from . import typed_source_inventory_v5 as typed
from . import typed_native_authority_v10 as native

SOURCE_OBSERVATION_AUTHORITY="DIAGNOSTIC_NOT_NATIVE_WARRANT"
G2=G3=G4=G5=G6="UNKNOWN"
SCHEMA="UDM_V13_PROTECTED_FAILURE_SOURCE_BRANCH_OBSERVATION"


def _hash(data):
    return hashlib.sha256(data).hexdigest()


def _canonical(value):
    return json.dumps(value,sort_keys=True,separators=(",",":"),allow_nan=False)


def guard_nodes(path,source):
    """Find all conservative 'if not self.field' AST slots, not a chosen fix."""
    typed._path(path)
    if not path.endswith(".py"):
        raise ValueError("source-line observations require original Python source")
    if isinstance(source,bytes):
        try:
            source=source.decode("utf-8")
        except UnicodeError as error:
            raise ValueError("original Python source not UTF8") from error
    if not isinstance(source,str):
        raise ValueError("typed source bytes required")
    try:
        tree=ast.parse(source,filename=path)
    except (SyntaxError,UnicodeError) as error:
        raise ValueError("original Python AST refused") from error
    found=[]
    for node in ast.walk(tree):
        if not isinstance(node,ast.If):continue
        x=node.test
        if not (isinstance(x,ast.UnaryOp) and isinstance(x.op,ast.Not)
                and isinstance(x.operand,ast.Attribute)
                and isinstance(x.operand.value,ast.Name)
                and x.operand.value.id=="self"):
            continue
        lines=sorted({y.lineno for stmt in node.body for y in ast.walk(stmt)
                      if hasattr(y,"lineno") and y.lineno>node.lineno})
        if not lines:continue
        found.append({
            "path":path,"line":node.lineno,"attribute":x.operand.attr,
            "kind":"IF_NOT_SELF_ATTRIBUTE","then_lines":lines
        })
    return sorted(found,key=lambda x:(x["path"],x["line"],x["attribute"]))


_TRACE_SOURCE=r'''
import ast,hashlib,json,os,pathlib,sys,time
world=pathlib.Path(sys.argv[1]).resolve(strict=True)
trace_file=pathlib.Path(sys.argv[2]).resolve()
source_guards=json.loads(sys.argv[3])
required=json.loads(sys.argv[4])
testpaths=json.loads(sys.argv[5])
sys.path[:0]=[str(world/"src"),str(world)]
import pytest
class Observation:
    def __init__(self):
        self.active=False;self.pending={};self.events=[]
        self.selected=[];self.calls=[];self.deselected=[]
        self.protected_executed=[];self.skipped=[]
        self.by_slot={}
        for guard in source_guards:
            self.by_slot.setdefault((guard["path"],guard["line"]),[]).append(guard)
    def match(self,node):
        return any(node==target or node.startswith(target+"[") or node.startswith(target+"::")
                   for target in required)
    def tracer(self,frame,event,arg):
        if event not in ("call","line","return"):
            return self.tracer
        if event=="return":
            self.pending.pop(id(frame),None);return self.tracer
        if event=="call":return self.tracer
        try:
            file=pathlib.Path(frame.f_code.co_filename).resolve(strict=True)
            rel=str(file.relative_to(world)).replace(os.sep,"/")
        except (ValueError,OSError,RuntimeError):return self.tracer
        key=id(frame);line=frame.f_lineno
        prior=self.pending.pop(key,None)
        if prior and line in prior["then_lines"]:
            self.events.append({
                "path":prior["path"],"line":prior["line"],"attribute":prior["attribute"],
                "kind":prior["kind"],"branch":"THEN","callable":True,
                "then_line":line
            })
        for row in self.by_slot.get((rel,line),()):
            owner=frame.f_locals.get("self")
            if owner is None:continue
            try:
                # object.__getattribute__ avoids user-defined __getattribute__
                # and avoids evaluating a custom __bool__ during observation.
                namespace=object.__getattribute__(owner,"__dict__")
            except (AttributeError,TypeError):continue
            if not isinstance(namespace,dict) or row["attribute"] not in namespace:
                continue
            if callable(namespace[row["attribute"]]):
                self.pending[key]=row
                break
        return self.tracer
    def pytest_collection_modifyitems(self,session,config,items):
        self.selected=[item.nodeid for item in items]
    def pytest_deselected(self,items):
        self.deselected.extend(item.nodeid for item in items)
    @pytest.hookimpl(hookwrapper=True)
    def pytest_runtest_call(self,item):
        if self.match(item.nodeid):
            self.active=True;sys.settrace(self.tracer)
            try:yield
            finally:
                sys.settrace(None);self.active=False;self.pending.clear()
        else:
            yield
    def pytest_runtest_logreport(self,report):
        if report.when=="call":
            self.calls.append({"nodeid":report.nodeid,"outcome":report.outcome})
        if report.when=="setup" and report.skipped:
            self.skipped.append(report.nodeid)
monitor=Observation()
argv=["-q","-p","no:cacheprovider","-p","pytest_cov",
      "--rootdir="+str(world)]
for name in ("pytest.ini",".pytest.ini","pyproject.toml","tox.ini","setup.cfg"):
    if (world/name).is_file():
        argv.extend(["-c",str(world/name)]);break
argv.extend(str(world/name) for name in testpaths)
started=time.monotonic()
try:code=int(pytest.main(argv,plugins=[monitor]))
except BaseException as error:
    code=4;err=type(error).__name__+": "+str(error)
else:err=None
record={
    "source":"EXECUTED_ORIGINAL_PROTECTED_TEST_INSTRUMENTED",
    "native_exit":code,"selected":monitor.selected,"deselected":monitor.deselected,
    "calls":monitor.calls,"setup_skipped":monitor.skipped,
    "events":sorted({json.dumps(x,sort_keys=True) for x in monitor.events}),
    "bootstrap_error":err,"native_seconds":time.monotonic()-started}
trace_file.write_text(json.dumps(record,sort_keys=True)+"\n")
raise SystemExit(code)
'''


def run_observer(repo,commit,stage,*,production_paths,required,testpaths,
                 interpreter=sys.executable,timeout=90):
    started=time.monotonic()
    root=Path(repo).absolute()
    stage=Path(stage).absolute()
    checked=native.verify_stage(root,commit,stage)
    snap=typed.snapshot(root,commit)
    regular={row["path"]:row for row in snap["manifest"]
             if row["mode"] in typed.REGULAR_MODES}
    if (not isinstance(production_paths,(tuple,list)) or not production_paths
            or not isinstance(required,(tuple,list)) or not required
            or not isinstance(testpaths,(tuple,list)) or not testpaths):
        raise ValueError("nonempty source scope and protected test identities required")
    original=[]
    for path in production_paths:
        typed._path(path)
        if path not in regular or not path.endswith(".py"):
            raise ValueError("original AST scope requires a Git-authenticated production blob")
        data=typed._git(root,"cat-file","blob",regular[path]["oid"])
        if _hash(data)!=regular[path]["sha256"]:
            raise ValueError("source Git object mismatch")
        original.extend(guard_nodes(path,data))
    for path in testpaths:
        typed._path(path)
        if not path.endswith(".py") or path not in regular:
            raise ValueError("original independently authored test scope unavailable")
    for node in required:
        if not isinstance(node,str) or not native.accepts_class_method(node):
            raise ValueError("protected original test node is not class-qualified")
        if node.split("::",1)[0] not in testpaths:
            raise ValueError("test obligation outside protected execution scope")
    args=[str(Path(interpreter).absolute()),"-I","-B","-c",_TRACE_SOURCE,
          str(stage),"",_canonical(original),_canonical(required),_canonical(testpaths)]
    env=dict(os.environ,PYTHONDONTWRITEBYTECODE="1",PYTEST_DISABLE_PLUGIN_AUTOLOAD="1",
             PYTHONHASHSEED="0")
    env.pop("GH_TOKEN",None);env.pop("GITHUB_TOKEN",None)
    env.pop("PYTHONPATH",None);env.pop("PYTEST_ADDOPTS",None)
    with tempfile.TemporaryDirectory(prefix="udm-v13-original-trace-") as tmp:
        out=Path(tmp).resolve()/"TRACE.json"
        args[6]=str(out)
        try:
            proc=subprocess.run(args,cwd=Path(tmp).resolve(),env=env,
                                capture_output=True,text=True,timeout=timeout)
        except (OSError,subprocess.TimeoutExpired) as error:
            return {"schema":SCHEMA,"status":"UNKNOWN_OBSERVER_RUNTIME",
                    "error":type(error).__name__,"native_calls":1,
                    "source_commit":commit,"events":[]}
        native.verify_stage(root,commit,stage)
        try:
            data=json.loads(out.read_text())
        except (OSError,ValueError,UnicodeError) as error:
            return {"schema":SCHEMA,"status":"UNKNOWN_OBSERVER_RECEIPT",
                    "error":type(error).__name__,"native_calls":1,
                    "source_commit":commit,"events":[]}
    failed=[row["nodeid"] for row in data["calls"]
            if row["outcome"]=="failed" and
            any(row["nodeid"]==n or row["nodeid"].startswith(n+"[") or row["nodeid"].startswith(n+"::")
                for n in required)]
    selected=data["selected"]
    deselected=data["deselected"]
    executed={row["nodeid"] for row in data["calls"]}
    full_test=bool(selected) and all(
        any(n==req or n.startswith(req+"[") or n.startswith(req+"::") for n in executed)
        for req in required)
    no_skip=not data["setup_skipped"] and not deselected and all(
        row["outcome"] in ("passed","failed") for row in data["calls"])
    raw_events=[json.loads(x) for x in data["events"]]
    warranted={ (x["path"],x["line"],x["attribute"],x["then_line"],x["branch"],x["callable"]):x
                for x in raw_events if (
                    x["branch"]=="THEN" and x["callable"] is True
                    and any(x["path"]==g["path"] and x["line"]==g["line"]
                            and x["attribute"]==g["attribute"]
                            and x["then_line"] in g["then_lines"] for g in original))}
    has_real_fail=proc.returncode==data["native_exit"]==1 and bool(failed)
    status="UNKNOWN_PROTECTED_NOT_FAILED"
    if has_real_fail:
        status=("OBSERVED_PROTECTED_FAILURE_BRANCH_EDGE"
                if full_test and no_skip and warranted
                else "UNKNOWN_NO_WARRANTED_BRANCH_EDGE")
    result={"schema":SCHEMA,"status":status,
            "observation_authority":SOURCE_OBSERVATION_AUTHORITY,
            "source_commit":commit,"source_manifest_sha256":checked["typed_manifest_sha256"],
            "source_patterns":len(original),
            "source_original_guard_sha256":_hash(_canonical(original).encode()),
            "required":list(required),"failed_protected":failed,
            "native_exit":proc.returncode,"native_calls":1,
            "selected_count":len(selected),"selected":selected,
            "executed_count":len(executed),"deselected":deselected,
            "events":sorted(warranted.values(),
                            key=lambda x:(x["path"],x["line"],x["attribute"])),
            "native_stdout_sha256":_hash(proc.stdout.encode()),
            "native_stderr_sha256":_hash(proc.stderr.encode()),
            "native_seconds":data["native_seconds"],
            "elapsed_seconds":time.monotonic()-started,
            "G2":"UNKNOWN","G3":"UNKNOWN","G4":"UNKNOWN",
            "not_an_unchanged_verifier_native_certificate":True,
            "test_source_unchanged":True}
    return result
