#!/usr/bin/env python3
"""Source-neutral native mutable-closure observer for exposed AnyIO training.

Posthoc on the exposed training source only. It does not generate or apply a repair.
It discovers nested closures assigned into mutable object attributes from the source
AST, then traces authentic protected failures and asks whether a persisted closure's
captured scalar environment disagrees with the current invocation's same-named local.
"""
from __future__ import annotations

import argparse
import ast
from collections import defaultdict
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import xml.etree.ElementTree as ET

ROOT=Path(__file__).resolve().parents[2]
PROTOCOL_PATH="research/unified_consequence_runtime/G2_ANYIO_POSTHOC_OBSERVATION_PROTOCOL_V1.json"
PROTOCOL_FREEZE="cb958e9c03bfcc7eb17e193c8d63d22edaf96f1e"


def git(repo: Path,*args: str,raw: bool=False):
    z=subprocess.check_output(["git","--no-replace-objects","-C",str(repo),*args])
    return z if raw else z.decode().strip()


def sha256(raw: bytes)->str:
    return hashlib.sha256(raw).hexdigest()


def scalar(value):
    if value is None or isinstance(value,(bool,int,float,str)):
        return value
    if isinstance(value,tuple) and all(v is None or isinstance(v,(bool,int,float,str)) for v in value):
        return list(value)
    return None


def attribute_chain(node):
    attrs=[]
    while isinstance(node,ast.Attribute):
        attrs.append(node.attr)
        node=node.value
    if not isinstance(node,ast.Name):
        return None
    return node.id,tuple(reversed(attrs))


def discover_sites(tree: ast.Module):
    sites=[]
    for outer in tree.body:
        if not isinstance(outer,(ast.FunctionDef,ast.AsyncFunctionDef)):
            continue
        nested={
            node.name:node
            for node in outer.body
            if isinstance(node,(ast.FunctionDef,ast.AsyncFunctionDef))
        }
        if not nested:
            continue
        for node in ast.walk(outer):
            targets=[]
            value=None
            if isinstance(node,ast.Assign):
                targets=list(node.targets); value=node.value
            elif isinstance(node,ast.AnnAssign):
                targets=[node.target]; value=node.value
            else:
                continue
            if not isinstance(value,ast.Name) or value.id not in nested:
                continue
            for target in targets:
                chain=attribute_chain(target)
                if chain is None or len(chain[1])<1:
                    continue
                root,attrs=chain
                sites.append({
                    "outer_function":outer.name,
                    "outer_line":outer.lineno,
                    "nested_function":value.id,
                    "nested_line":nested[value.id].lineno,
                    "object_root_local":root,
                    "attribute_path":list(attrs),
                    "assignment_line":getattr(node,"lineno",None),
                })
    sites.sort(key=lambda x:(x["outer_line"],x["assignment_line"] or 0,tuple(x["attribute_path"])))
    return sites


def callable_closure(value):
    code=getattr(value,"__code__",None)
    cells=getattr(value,"__closure__",None)
    if code is None or not cells:
        return None
    names=tuple(code.co_freevars)
    if len(names)!=len(cells):
        return None
    out={}
    for name,cell in zip(names,cells):
        try:v=cell.cell_contents
        except ValueError:continue
        sv=scalar(v)
        if sv is not None:
            out[name]=sv
    return {
        "code_name":code.co_name,
        "qualname":getattr(value,"__qualname__",""),
        "scalar_freevars":out,
    }


class Monitor:
    def __init__(self,world: Path,production: str,protected: list[str],sites: list[dict]):
        self.world=world
        self.production=(world/production).resolve()
        self.protected=set(protected)
        self.sites=sites
        self.current=None
        self.outcomes=[]
        self.collected=[]
        self.deselected=[]
        self.observations=[]
        self.outer_snapshots=defaultdict(list)
        self.nested_calls=defaultdict(list)
        self.seen=set()

    def trace(self,frame,event,arg):
        if event not in ("call","line","return"):
            return self.trace
        try:
            if Path(frame.f_code.co_filename).resolve()!=self.production:
                return self.trace
        except Exception:
            return self.trace
        for site in self.sites:
            scalar_locals={
                name:value for name,raw in frame.f_locals.items()
                if (value:=scalar(raw)) is not None
            }
            site_key=(site["outer_function"],tuple(site["attribute_path"]),site["nested_function"])
            if event=="return" and frame.f_code.co_name==site["outer_function"]:
                self.outer_snapshots[(self.current,site_key)].append({
                    "line":frame.f_lineno,
                    "scalars":scalar_locals,
                })
            if event=="call" and frame.f_code.co_name==site["nested_function"]:
                self.nested_calls[(self.current,site_key)].append({
                    "line":frame.f_lineno,
                    "scalars":scalar_locals,
                })
            if frame.f_code.co_name!=site["outer_function"] or event=="call":
                continue
            obj=frame.f_locals.get(site["object_root_local"])
            if obj is None:
                continue
            try:
                for attr in site["attribute_path"][:-1]:
                    obj=getattr(obj,attr)
                final_attr=site["attribute_path"][-1]
                value=getattr(obj,final_attr)
            except (AttributeError,TypeError):
                continue
            closure=callable_closure(value)
            if not closure or closure["code_name"]!=site["nested_function"]:
                continue
            mismatches=[]
            agreements=[]
            for name,old in closure["scalar_freevars"].items():
                if name not in frame.f_locals:
                    continue
                current=scalar(frame.f_locals[name])
                if current is None:
                    continue
                row={"name":name,"captured":old,"current":current}
                (mismatches if old!=current else agreements).append(row)
            key=(
                self.current,site["outer_function"],tuple(site["attribute_path"]),frame.f_lineno,
                json.dumps(closure,sort_keys=True),json.dumps(mismatches,sort_keys=True)
            )
            if key in self.seen:
                continue
            self.seen.add(key)
            self.observations.append({
                "protected_test":self.current,
                "event":event,
                "trace_line":frame.f_lineno,
                "site":site,
                "closure":closure,
                "same_named_scalar_mismatches":mismatches,
                "same_named_scalar_agreements":agreements,
            })
        return self.trace


def main(world: Path,out: Path):
    out.mkdir(parents=True,exist_ok=False)
    result={
        "schema":"UDM_ANYIO_NATIVE_MUTABLE_CLOSURE_OBSERVER_V1",
        "status":"UNKNOWN_NOT_EXECUTED",
        "G2":"UNKNOWN","future_source":"UNOPENED","repair_trials":0,
    }
    frozen=git(ROOT,"show",PROTOCOL_FREEZE+":"+PROTOCOL_PATH,raw=True)
    assert frozen==(ROOT/PROTOCOL_PATH).read_bytes(),"PROTOCOL_MUTATION"
    protocol=json.loads(frozen)
    production=protocol["source_file"]
    author=protocol["author_test_file"]
    assert git(world,"rev-parse","HEAD")==protocol["original_source"].split("@")[-1]
    source=(world/production).read_bytes()
    tests=(world/author).read_bytes()
    assert sha256(source)==protocol["source_sha256"]
    assert sha256(tests)==protocol["test_sha256"]
    assert source==git(world,"show","HEAD:"+production,raw=True)
    assert tests==git(world,"show",protocol["original_test_head"]+":"+author,raw=True)
    assert git(world,"diff","--name-only")==author

    tree=ast.parse(source,filename=production)
    sites=discover_sites(tree)
    result["source_derived_mutable_closure_sites"]=sites
    result["source_derived_mutable_closure_site_count"]=len(sites)
    if not sites:
        result["status"]="UNKNOWN_NO_SOURCE_DERIVED_MUTABLE_CLOSURE_SITE"
        (out/"RESULT.json").write_text(json.dumps(result,indent=2,sort_keys=True)+"\n")
        return result

    import pytest

    monitor=Monitor(world,production,protocol["protected"],sites)

    class Plugin:
        @pytest.hookimpl(hookwrapper=True,tryfirst=True)
        def pytest_runtest_call(self,item):
            nodeid=item.nodeid
            if nodeid not in monitor.protected:
                yield
                return
            old=sys.gettrace()
            monitor.current=nodeid
            sys.settrace(monitor.trace)
            try:
                yield
            finally:
                sys.settrace(old)
                monitor.current=None

        def pytest_collection_modifyitems(self,session,config,items):
            monitor.collected=[item.nodeid for item in items]

        def pytest_deselected(self,items):
            monitor.deselected.extend(item.nodeid for item in items)

        def pytest_runtest_logreport(self,report):
            if report.when=="call":
                monitor.outcomes.append({"nodeid":report.nodeid,"outcome":report.outcome})

    sys.path[:0]=[str(world/"src"),str(world)]
    junit=out/"native.xml"
    argv=[
        "-q","-p","no:cacheprovider","-p","pytest_cov",
        "--junitxml="+str(junit),"--rootdir="+str(world),
        "-c",str(world/"pyproject.toml"),
    ] + [
        str(world/author)+"::"+node.split("::",1)[1]
        for node in protocol["protected"]
    ]
    result["pytest_argv"]=argv
    result["native_calls"]=1
    code=pytest.main(argv,plugins=[Plugin()])
    result["native_exit"]=int(code)
    result["actual_calls"]=monitor.outcomes
    result["collected"]=monitor.collected
    result["deselected"]=monitor.deselected
    result["observations"]=monitor.observations
    result["outer_snapshots"]={
        str(key):value for key,value in monitor.outer_snapshots.items()
    }
    result["nested_calls"]={
        str(key):value for key,value in monitor.nested_calls.items()
    }

    sequence_mismatches=[]
    for key,outers in monitor.outer_snapshots.items():
        nested=monitor.nested_calls.get(key,[])
        for index,(outer_row,nested_row) in enumerate(zip(outers,nested)):
            common=sorted(set(outer_row["scalars"]) & set(nested_row["scalars"]))
            for name in common:
                current=outer_row["scalars"][name]
                captured=nested_row["scalars"][name]
                if current!=captured:
                    sequence_mismatches.append({
                        "protected_test":key[0],
                        "site_key":list(key[1]),
                        "pair_index":index,
                        "name":name,
                        "current_outer":current,
                        "executed_nested":captured,
                    })
    result["sequence_stale_capture_observations"]=sequence_mismatches
    result["sequence_stale_capture_observation_count"]=len(sequence_mismatches)

    suite=ET.parse(junit).getroot()
    ts=suite if suite.tag=="testsuite" else next(suite.iter("testsuite"))
    counts={k:int(ts.get(k,0)) for k in ("tests","failures","errors","skipped")}
    result["junit"]=counts
    assert (world/production).read_bytes()==source
    assert (world/author).read_bytes()==tests
    result["source_test_bytes_preserved"]=True

    outcomes={r["nodeid"]:r["outcome"] for r in monitor.outcomes}
    valid=(
        int(code)==1 and counts=={"tests":2,"failures":2,"errors":0,"skipped":0}
        and set(monitor.collected)==set(protocol["protected"])
        and not monitor.deselected
        and outcomes=={key:"failed" for key in protocol["protected"]}
    )
    if not valid:
        result["status"]="UNKNOWN_INSTRUMENTED_NATIVE_AUTHORITY"
    else:
        # The protected author tests are meta-tests that create exact child test
        # source via testdir.makepyfile(). Extract those literal payloads from the
        # authenticated author test AST; do not author a replacement test.
        author_tree=ast.parse(tests.decode("utf-8"),filename=author)
        direct_dir=out/"direct-author-child"
        direct_dir.mkdir()
        child_files={}
        for index,parent in enumerate(protocol["protected"]):
            fn_name=parent.split("::")[-1]
            fn=next(
                node for node in author_tree.body
                if isinstance(node,(ast.FunctionDef,ast.AsyncFunctionDef))
                and node.name==fn_name
            )
            payloads=[]
            for node in ast.walk(fn):
                if not isinstance(node,ast.Call) or not isinstance(node.func,ast.Attribute):
                    continue
                if node.func.attr!="makepyfile" or not node.args:
                    continue
                arg=node.args[0]
                if isinstance(arg,ast.Constant) and isinstance(arg.value,str):
                    payloads.append(arg.value)
            if len(payloads)!=1:
                raise AssertionError("PROTECTED_AUTHOR_CHILD_SOURCE_NOT_UNIQUE:"+parent)
            path=(direct_dir/f"test_author_child_{index}.py").resolve()
            path.write_text(payloads[0],encoding="utf-8")
            child_files[path]=parent

        direct=Monitor(world,production,protocol["protected"],sites)

        class DirectPlugin:
            @pytest.hookimpl(hookwrapper=True,tryfirst=True)
            def pytest_runtest_call(self,item):
                try:path=Path(str(item.path)).resolve()
                except Exception:path=None
                parent=child_files.get(path)
                old_current=direct.current
                direct.current=parent
                try:
                    yield
                finally:
                    direct.current=old_current

            def pytest_collection_modifyitems(self,session,config,items):
                direct.collected=[item.nodeid for item in items]

            def pytest_deselected(self,items):
                direct.deselected.extend(item.nodeid for item in items)

            def pytest_runtest_logreport(self,report):
                if report.when=="call":
                    direct.outcomes.append({"nodeid":report.nodeid,"outcome":report.outcome})

        direct_argv=[
            "-q","-p","no:cacheprovider",
            "--rootdir="+str(direct_dir),
            *[str(path) for path in sorted(child_files)],
        ]
        old_trace=sys.gettrace()
        sys.settrace(direct.trace)
        try:
            direct_code=pytest.main(direct_argv,plugins=[DirectPlugin()])
        finally:
            sys.settrace(old_trace)

        result["direct_author_child"]={
            "pytest_argv":direct_argv,
            "exit":int(direct_code),
            "outcomes":direct.outcomes,
            "collected":direct.collected,
            "deselected":direct.deselected,
            "source_map":{str(path):parent for path,parent in child_files.items()},
        }
        result["direct_outer_snapshots"]={
            str(key):value for key,value in direct.outer_snapshots.items()
        }
        result["direct_nested_calls"]={
            str(key):value for key,value in direct.nested_calls.items()
        }

        sequence_mismatches=[]
        for key,outers in direct.outer_snapshots.items():
            nested=direct.nested_calls.get(key,[])
            for index,(outer_row,nested_row) in enumerate(zip(outers,nested)):
                common=sorted(set(outer_row["scalars"]) & set(nested_row["scalars"]))
                for name in common:
                    current=outer_row["scalars"][name]
                    captured=nested_row["scalars"][name]
                    if current!=captured:
                        sequence_mismatches.append({
                            "protected_test":key[0],
                            "site_key":list(key[1]),
                            "pair_index":index,
                            "name":name,
                            "current_outer":current,
                            "executed_nested":captured,
                        })
        result["sequence_stale_capture_observations"]=sequence_mismatches
        result["sequence_stale_capture_observation_count"]=len(sequence_mismatches)

        direct_mismatches=[
            obs for obs in direct.observations
            if obs["same_named_scalar_mismatches"]
        ]
        mismatches=direct_mismatches+sequence_mismatches
        result["direct_stale_capture_observation_count"]=len(direct_mismatches)
        result["stale_capture_observation_count"]=len(mismatches)
        result["stale_capture_observations"]=mismatches
        tests_with_mismatch=sorted({
            obs.get("protected_test") for obs in mismatches if obs.get("protected_test")
        })
        result["protected_tests_with_stale_capture"]=tests_with_mismatch
        direct_failed=sum(row["outcome"]=="failed" for row in direct.outcomes)
        direct_errors=sum(row["outcome"] not in ("passed","failed","skipped") for row in direct.outcomes)
        result["direct_author_child_failure_count"]=direct_failed
        result["direct_author_child_error_like_count"]=direct_errors

        if int(direct_code) not in (0,1) or direct_errors:
            result["status"]="UNKNOWN_DIRECT_AUTHOR_CHILD_APPARATUS"
        elif len(tests_with_mismatch)==2:
            result["status"]="WARRANTED_BOUNDED_NATIVE_SOURCE_DERIVED_STALE_CLOSURE_OBSERVATION"
        elif mismatches:
            result["status"]="WARRANTED_BOUNDED_NATIVE_STALE_CLOSURE_PARTIAL"
        else:
            result["status"]="UNKNOWN_NO_NATIVE_STALE_CLOSURE_SEPARATOR"

    (out/"RESULT.json").write_text(json.dumps(result,indent=2,sort_keys=True)+"\n")
    print(json.dumps({
        "status":result["status"],
        "source_derived_mutable_closure_site_count":result.get("source_derived_mutable_closure_site_count"),
        "stale_capture_observation_count":result.get("stale_capture_observation_count",0),
        "protected_tests_with_stale_capture":result.get("protected_tests_with_stale_capture",[]),
        "junit":result.get("junit"),
        "G2":result["G2"],
    },sort_keys=True))
    return result


if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("world",type=Path)
    p.add_argument("out",type=Path)
    a=p.parse_args()
    r=main(a.world.resolve(),a.out.resolve())
    # The workflow qualifies scientific subclaims independently. Preserve
    # UNKNOWN/negative observations as evidence rather than hiding them behind
    # an apparatus exit code.
    raise SystemExit(0)
