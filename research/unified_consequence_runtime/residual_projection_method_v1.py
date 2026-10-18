#!/usr/bin/env python3
"""Generic transfer surface learned from attrs residual observation genesis V1.

No target repository identities or semantic attribute names occur here.
"""
from __future__ import annotations
import ast, importlib.util, inspect, json
from pathlib import Path
from research.unified_consequence_runtime.attrs_residual_observation_genesis_v1 import (
    enumerate_projection_observations,
    generate_repair,
    run_pytest,
)

def callable_map(raw: bytes):
    tree=ast.parse(raw.decode("utf-8"));out={}
    def walk(nodes,prefix=()):
        for node in nodes:
            if isinstance(node,(ast.FunctionDef,ast.AsyncFunctionDef)) and node.name.startswith("test"):
                out["::".join((*prefix,node.name))]=ast.dump(node,include_attributes=False)
            elif isinstance(node,ast.ClassDef) and node.name.startswith("Test"):
                walk(node.body,(*prefix,node.name))
    walk(tree.body)
    return out

def changed_nodes(base_raw: bytes, head_raw: bytes):
    base=callable_map(base_raw);head=callable_map(head_raw)
    return sorted(k for k,v in head.items() if base.get(k)!=v)

def _find_test(tree: ast.Module,node_path: str):
    parts=node_path.split("::")
    body=tree.body
    for part in parts:
        found=None
        for node in body:
            if isinstance(node,ast.ClassDef) and node.name==part:
                found=node;body=node.body;break
            if isinstance(node,(ast.FunctionDef,ast.AsyncFunctionDef)) and node.name==part:
                found=node;break
        if found is None:return None
    return found if isinstance(found,(ast.FunctionDef,ast.AsyncFunctionDef)) else None

def _load(path: Path):
    spec=importlib.util.spec_from_file_location("_udm_future_author_test",path)
    if spec is None or spec.loader is None:raise ValueError("TEST_IMPORT_SPEC")
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module);return module

def derive_direct_boolean_residual(test_path: Path,node_path: str):
    raw=test_path.read_text();tree=ast.parse(raw,filename=str(test_path))
    fn=_find_test(tree,node_path)
    if fn is None:return None
    asserts=[n for n in ast.walk(fn) if isinstance(n,ast.Assert)]
    direct=[]
    for ass in asserts:
        expected=True;expr=ass.test
        if isinstance(expr,ast.UnaryOp) and isinstance(expr.op,ast.Not):
            expected=False;expr=expr.operand
        if not isinstance(expr,ast.Call) or not isinstance(expr.func,ast.Name) or len(expr.args)!=1 or not isinstance(expr.args[0],ast.Name):
            continue
        direct.append((ass,expr.func.id,expr.args[0].id,expected))
    if len(direct)!=1:return None
    _,classifier_name,arg_name,expected=direct[0]
    exprs=None
    for dec in fn.decorator_list:
        if not isinstance(dec,ast.Call) or len(dec.args)<2:continue
        if not (isinstance(dec.func,ast.Attribute) and dec.func.attr=="parametrize"):continue
        try:name=ast.literal_eval(dec.args[0])
        except Exception:continue
        if name!=arg_name or not isinstance(dec.args[1],(ast.List,ast.Tuple)):continue
        exprs=list(dec.args[1].elts);break
    if exprs is None:return None
    module=_load(test_path);ns=vars(module);classifier=ns.get(classifier_name)
    if not callable(classifier):return None
    cases=[]
    for expr in exprs:
        try:cases.append(eval(compile(ast.Expression(expr),str(test_path),"eval"),ns,ns))
        except Exception:return None
    return {
        "node_path":node_path,"classifier_name":classifier_name,"argument_name":arg_name,
        "expected":expected,"classifier":classifier,"cases":cases,
        "source_file":inspect.getsourcefile(classifier),
    }

def propose(test_path: Path,changed: list[str],production_path: Path):
    proposals=[]
    for node in changed:
        residual=derive_direct_boolean_residual(test_path,node)
        if residual is None:continue
        if residual["source_file"] is None or Path(residual["source_file"]).resolve()!=production_path.resolve():
            continue
        base,failing,candidates,classes=enumerate_projection_observations(
            residual["classifier"],residual["cases"],residual["expected"])
        if failing and classes:
            proposals.append({
                "node":node,"residual":residual,"base_vector":base,"failing":failing,
                "candidates":candidates,"classes":classes,
            })
    return proposals

def serializable(proposal):
    r=proposal["residual"]
    return {
        "node":proposal["node"],"classifier_name":r["classifier_name"],
        "argument_name":r["argument_name"],"expected":r["expected"],
        "case_count":len(r["cases"]),"base_vector":proposal["base_vector"],
        "failing":proposal["failing"],"classes":proposal["classes"],
    }
