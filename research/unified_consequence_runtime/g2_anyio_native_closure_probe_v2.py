#!/usr/bin/env python3
"""Fresh-process source-derived stale-closure probe for exposed AnyIO training.

The workflow separately replays the authenticated outer author tests. This probe
extracts the exact testdir.makepyfile payloads from those protected author tests,
runs those payloads directly under the unchanged original production source, and
profiles only source-derived outer/nested function call/return environments.
No production or test repair is generated.
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
            node.name:node for node in outer.body
            if isinstance(node,(ast.FunctionDef,ast.AsyncFunctionDef))
        }
        for node in ast.walk(outer):
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
                if chain is None:
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


def extract_children(test_source: bytes, protected: list[str], out: Path):
    tree=ast.parse(test_source.decode("utf-8"))
    child_files={}
    for index,parent in enumerate(protected):
        fn_name=parent.split("::")[-1]
        fn=next(
            node for node in tree.body
            if isinstance(node,(ast.FunctionDef,ast.AsyncFunctionDef)) and node.name==fn_name
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
            raise ValueError("protected author child source not unique: "+parent)
        path=(out/f"test_author_child_{index}.py").resolve()
        path.write_text(payloads[0],encoding="utf-8")
        child_files[path]=parent
    return child_files


class Monitor:
    def __init__(self,production: Path,sites,child_files):
        self.production=production.resolve()
        self.sites=sites
        self.child_files=child_files
        self.current=None
        self.outer=defaultdict(list)
        self.nested=defaultdict(list)
        self.outcomes=[]
        self.collected=[]
        self.deselected=[]

    def profile(self,frame,event,arg):
        if event not in ("call","return"):
            return
        try:
            if Path(frame.f_code.co_filename).resolve()!=self.production:
                return
        except Exception:
            return
        scalars={
            name:value for name,raw in frame.f_locals.items()
            if (value:=scalar(raw)) is not None
        }
        for site in self.sites:
            site_key=(site["outer_function"],tuple(site["attribute_path"]),site["nested_function"])
            if event=="return" and frame.f_code.co_name==site["outer_function"]:
                self.outer[(self.current,site_key)].append({"line":frame.f_lineno,"scalars":scalars})
            elif event=="call" and frame.f_code.co_name==site["nested_function"]:
                self.nested[(self.current,site_key)].append({"line":frame.f_lineno,"scalars":scalars})


def main(world: Path,out: Path):
    out.mkdir(parents=True,exist_ok=False)
    frozen=git(ROOT,"show",PROTOCOL_FREEZE+":"+PROTOCOL_PATH,raw=True)
    assert frozen==(ROOT/PROTOCOL_PATH).read_bytes(),"PROTOCOL_MUTATION"
    p=json.loads(frozen)
    production=p["source_file"];author=p["author_test_file"]
    source=(world/production).read_bytes();tests=(world/author).read_bytes()
    assert git(world,"rev-parse","HEAD")==p["original_source"].split("@")[-1]
    assert source==git(world,"show","HEAD:"+production,raw=True)
    assert tests==git(world,"show",p["original_test_head"]+":"+author,raw=True)
    assert sha256(source)==p["source_sha256"] and sha256(tests)==p["test_sha256"]
    assert git(world,"diff","--name-only")==author

    sites=discover_sites(ast.parse(source,filename=production))
    direct_dir=out/"author-child"
    direct_dir.mkdir()
    child_files=extract_children(tests,p["protected"],direct_dir)
    result={
        "schema":"UDM_ANYIO_FRESH_PROCESS_SOURCE_DERIVED_CLOSURE_PROBE_V2",
        "status":"UNKNOWN_NOT_EXECUTED",
        "source_derived_mutable_closure_sites":sites,
        "source_derived_mutable_closure_site_count":len(sites),
        "child_source_map":{str(path):parent for path,parent in child_files.items()},
        "future_source":"UNOPENED","repair_trials":0,"G2":"UNKNOWN",
    }
    if not sites:
        result["status"]="UNKNOWN_NO_SOURCE_DERIVED_MUTABLE_CLOSURE_SITE"
        (out/"RESULT.json").write_text(json.dumps(result,indent=2,sort_keys=True)+"\n")
        return result

    import pytest
    monitor=Monitor(world/production,sites,child_files)

    class Plugin:
        @pytest.hookimpl(hookwrapper=True,tryfirst=True)
        def pytest_runtest_call(self,item):
            try:path=Path(str(item.path)).resolve()
            except Exception:path=None
            old=monitor.current
            monitor.current=child_files.get(path)
            try:yield
            finally:monitor.current=old

        def pytest_collection_modifyitems(self,session,config,items):
            monitor.collected=[item.nodeid for item in items]

        def pytest_deselected(self,items):
            monitor.deselected.extend(item.nodeid for item in items)

        def pytest_runtest_logreport(self,report):
            if report.when=="call":
                monitor.outcomes.append({"nodeid":report.nodeid,"outcome":report.outcome})

    sys.path[:0]=[str(world/"src"),str(world)]
    argv=["-q","-p","no:cacheprovider","--rootdir="+str(direct_dir)] + [
        str(path) for path in sorted(child_files)
    ]
    old=sys.getprofile()
    sys.setprofile(monitor.profile)
    try:
        code=pytest.main(argv,plugins=[Plugin()])
    finally:
        sys.setprofile(old)

    sequence=[]
    for key,outers in monitor.outer.items():
        nested=monitor.nested.get(key,[])
        for index,(outer,nest) in enumerate(zip(outers,nested)):
            for name in sorted(set(outer["scalars"]) & set(nest["scalars"])):
                current=outer["scalars"][name];captured=nest["scalars"][name]
                if current!=captured:
                    sequence.append({
                        "protected_test":key[0],
                        "site_key":[key[1][0],list(key[1][1]),key[1][2]],
                        "pair_index":index,
                        "name":name,
                        "current_outer":current,
                        "executed_nested":captured,
                    })

    result.update({
        "native_exit":int(code),
        "collected":monitor.collected,
        "deselected":monitor.deselected,
        "outcomes":monitor.outcomes,
        "outer_snapshots":{str(k):v for k,v in monitor.outer.items()},
        "nested_calls":{str(k):v for k,v in monitor.nested.items()},
        "outer_snapshot_count":sum(map(len,monitor.outer.values())),
        "nested_call_count":sum(map(len,monitor.nested.values())),
        "stale_capture_observations":sequence,
        "stale_capture_observation_count":len(sequence),
        "protected_tests_with_stale_capture":sorted({
            x["protected_test"] for x in sequence if x["protected_test"]
        }),
    })
    failed=sum(x["outcome"]=="failed" for x in monitor.outcomes)
    passed=sum(x["outcome"]=="passed" for x in monitor.outcomes)
    skipped=sum(x["outcome"]=="skipped" for x in monitor.outcomes)
    result["direct_outcome_counts"]={"passed":passed,"failed":failed,"skipped":skipped}
    if int(code) not in (0,1) or skipped:
        result["status"]="UNKNOWN_DIRECT_AUTHOR_CHILD_APPARATUS"
    elif len(result["protected_tests_with_stale_capture"])==2:
        result["status"]="WARRANTED_BOUNDED_NATIVE_SOURCE_DERIVED_STALE_CLOSURE_OBSERVATION"
    elif sequence:
        result["status"]="WARRANTED_BOUNDED_NATIVE_STALE_CLOSURE_PARTIAL"
    else:
        result["status"]="UNKNOWN_NO_NATIVE_STALE_CLOSURE_SEPARATOR"

    assert (world/production).read_bytes()==source
    assert (world/author).read_bytes()==tests
    result["source_test_bytes_preserved"]=True
    (out/"RESULT.json").write_text(json.dumps(result,indent=2,sort_keys=True)+"\n")
    print(json.dumps({
        "status":result["status"],
        "source_derived_mutable_closure_site_count":len(sites),
        "outer_snapshot_count":result["outer_snapshot_count"],
        "nested_call_count":result["nested_call_count"],
        "stale_capture_observation_count":len(sequence),
        "protected_tests_with_stale_capture":result["protected_tests_with_stale_capture"],
        "direct_outcome_counts":result["direct_outcome_counts"],
        "G2":"UNKNOWN",
    },sort_keys=True))
    return result


if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("world",type=Path)
    p.add_argument("out",type=Path)
    a=p.parse_args()
    main(a.world.resolve(),a.out.resolve())
