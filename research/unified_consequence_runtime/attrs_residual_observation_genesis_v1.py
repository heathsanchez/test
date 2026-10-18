#!/usr/bin/env python3
from __future__ import annotations

import ast
import hashlib
import importlib.util
import inspect
import json
from pathlib import Path
import subprocess
import sys
import xml.etree.ElementTree as ET

ROOT=Path(__file__).resolve().parents[2]
PROTOCOL="research/unified_consequence_runtime/ATTRS_RESIDUAL_OBSERVATION_GENESIS_V1_PROTOCOL.json"
PROTOCOL_COMMIT="91d5bfb55f288dd712b625bc35abcaccd798f6ab"

def sha(data: bytes)->str:
    return hashlib.sha256(data).hexdigest()

def canonical(x)->str:
    return json.dumps(x,sort_keys=True,separators=(",",":"),default=repr)

def git(repo,*args,raw=False):
    out=subprocess.check_output(["git","--no-replace-objects","-C",str(repo),*args])
    return out if raw else out.decode().strip()

def frozen_protocol():
    live=(ROOT/PROTOCOL).read_bytes()
    frozen=git(ROOT,"show",PROTOCOL_COMMIT+":"+PROTOCOL,raw=True)
    if live!=frozen:
        raise ValueError("PROTOCOL_CHANGED_AFTER_FREEZE")
    return json.loads(frozen)

def load_module(path: Path):
    spec=importlib.util.spec_from_file_location("_udm_attrs_author_test",path)
    if spec is None or spec.loader is None:
        raise ValueError("AUTHOR_TEST_IMPORT_SPEC_FAILED")
    module=importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module

def find_test_function(tree: ast.Module,name:str):
    for node in tree.body:
        if isinstance(node,(ast.FunctionDef,ast.AsyncFunctionDef)) and node.name==name:
            return node
    raise ValueError("TEST_FUNCTION_NOT_FOUND:"+name)

def derive_classifier_and_cases(test_path: Path):
    source=test_path.read_text()
    tree=ast.parse(source,filename=str(test_path))
    fn=find_test_function(tree,"test_is_class_var")
    asserts=[n for n in ast.walk(fn) if isinstance(n,ast.Assert)]
    if len(asserts)!=1 or not isinstance(asserts[0].test,ast.Call):
        raise ValueError("UNSUPPORTED_PROTECTED_ASSERT_SHAPE")
    call=asserts[0].test
    if not isinstance(call.func,ast.Name) or len(call.args)!=1 or not isinstance(call.args[0],ast.Name):
        raise ValueError("UNSUPPORTED_CLASSIFIER_CALL_SHAPE")
    classifier_name=call.func.id
    arg_name=call.args[0].id
    expected=True
    param_exprs=None
    for dec in fn.decorator_list:
        if not isinstance(dec,ast.Call) or len(dec.args)<2:
            continue
        func=dec.func
        ok=(isinstance(func,ast.Attribute) and func.attr=="parametrize")
        if not ok:
            continue
        try:param_name=ast.literal_eval(dec.args[0])
        except Exception:continue
        if param_name!=arg_name or not isinstance(dec.args[1],(ast.List,ast.Tuple)):
            continue
        param_exprs=list(dec.args[1].elts)
        break
    if param_exprs is None:
        raise ValueError("PARAMETRIZE_CASES_NOT_DERIVED")
    module=load_module(test_path)
    ns=vars(module)
    classifier=ns.get(classifier_name)
    if not callable(classifier):
        raise ValueError("CLASSIFIER_NOT_CALLABLE")
    cases=[]
    for expr in param_exprs:
        value=eval(compile(ast.Expression(expr),str(test_path),"eval"),ns,ns)
        cases.append(value)
    return {
        "classifier_name":classifier_name,
        "argument_name":arg_name,
        "expected":expected,
        "classifier":classifier,
        "cases":cases,
        "source_module":getattr(classifier,"__module__",None),
        "source_file":inspect.getsourcefile(classifier),
    }

def primitive(value):
    if value is None or isinstance(value,(bool,int,float,str,bytes)):
        return True
    if isinstance(value,tuple):
        return all(x is None or isinstance(x,(bool,int,float,str,bytes)) for x in value)
    return False

def enumerate_projection_observations(classifier,cases,expected):
    base=[]
    for i,x in enumerate(cases):
        try:out=bool(classifier(x))
        except Exception as e:
            base.append({"case":i,"status":"EXCEPTION","type":type(e).__name__})
        else:
            base.append({"case":i,"status":"OK","value":out})
    failing=[i for i,row in enumerate(base) if row.get("status")=="OK" and row.get("value")!=expected]
    passing=[i for i,row in enumerate(base) if row.get("status")=="OK" and row.get("value")==expected]
    if not failing:
        return base,[],[],[]
    attrs=set()
    for i in failing:
        x=cases[i]
        for name in dir(x):
            try:value=getattr(x,name)
            except Exception:continue
            if primitive(value):
                attrs.add(name)
    candidates=[]
    classes={}
    for name in sorted(attrs):
        vector=[]
        repaired=[]
        valid=True
        for x,row in zip(cases,base):
            old=row.get("value") if row.get("status")=="OK" else None
            try:
                projected=getattr(x,name)
                proj=(bool(classifier(projected))
                      if projected is not x else False)
            except Exception:
                proj=False
            vector.append(proj)
            repaired.append(bool(old or proj) if old is not None else None)
        if any(repaired[i] != expected for i in failing):
            continue
        if any(repaired[i] != base[i]["value"] for i in passing):
            continue
        if not any(vector[i] for i in failing):
            continue
        key=tuple(vector)
        classes.setdefault(key,[]).append(name)
        candidates.append({"attribute":name,"projection_vector":vector,"repaired_vector":repaired})
    quotient=[]
    for vector,names in classes.items():
        quotient.append({
            "class_id":"obs-class:"+sha(canonical(list(vector)).encode())[:20],
            "projection_vector":list(vector),
            "members":sorted(names),
            "representative":sorted(names)[0],
        })
    quotient.sort(key=lambda row:(1,row["representative"]))
    return base,failing,candidates,quotient

def function_node(source: bytes,name:str):
    tree=ast.parse(source)
    found=[n for n in tree.body if isinstance(n,(ast.FunctionDef,ast.AsyncFunctionDef)) and n.name==name]
    if len(found)!=1:
        raise ValueError("TARGET_FUNCTION_NOT_UNIQUE")
    return found[0]

def generate_repair(source: bytes,classifier_name:str,arg_name:str,attribute:str)->bytes:
    text=source.decode()
    fn=function_node(source,classifier_name)
    lines=text.splitlines(keepends=True)
    if not fn.body:
        raise ValueError("EMPTY_TARGET_FUNCTION")
    insert_line=fn.body[0].lineno-1
    indent=" " * (fn.col_offset+4)
    temp="__udm_projection"
    snippet=[
        f"{indent}try:\n",
        f"{indent}    {temp} = getattr({arg_name}, {attribute!r})\n",
        f"{indent}except (AttributeError, TypeError):\n",
        f"{indent}    pass\n",
        f"{indent}else:\n",
        f"{indent}    if {temp} is not {arg_name} and {classifier_name}({temp}):\n",
        f"{indent}        return True\n",
    ]
    repaired="".join(lines[:insert_line]+snippet+lines[insert_line:])
    ast.parse(repaired)
    return repaired.encode()

def junit_counts(path:Path):
    root=ET.parse(path).getroot()
    suites=[root] if root.tag=="testsuite" else list(root.iter("testsuite"))
    return {k:sum(int(s.get(k,0)) for s in suites) for k in ("tests","failures","errors","skipped")}

def run_pytest(world:Path,args:list[str],out:Path,timeout=240):
    out.mkdir(parents=True,exist_ok=False)
    xml=out/"junit.xml"
    cmd=[sys.executable,"-m","pytest","-q","--junitxml="+str(xml),*args]
    proc=subprocess.run(cmd,cwd=world,capture_output=True,text=True,timeout=timeout)
    counts=junit_counts(xml) if xml.is_file() else {"tests":0,"failures":0,"errors":1,"skipped":0}
    return {
        "returncode":proc.returncode,"counts":counts,
        "stdout_sha256":sha(proc.stdout.encode()),"stderr_sha256":sha(proc.stderr.encode()),
        "stdout_tail":proc.stdout[-2500:],"stderr_tail":proc.stderr[-2500:],
    }

def main(world:Path,out:Path):
    p=frozen_protocol()
    world=world.resolve(strict=True);out=out.resolve();out.mkdir(parents=True,exist_ok=False)
    src=p["source"]; production=src["production"]; author_test=src["author_test"]
    if git(world,"rev-parse","HEAD")!=src["base"]:
        raise ValueError("WRONG_ATTRS_BASE")
    original=git(world,"show",src["base"]+":"+production,raw=True)
    if (world/production).read_bytes()!=original:
        raise ValueError("PRODUCTION_NOT_FROZEN_ORIGINAL")
    head_test=git(world,"show",src["author_head"]+":"+author_test,raw=True)
    if (world/author_test).read_bytes()!=head_test:
        raise ValueError("AUTHOR_TEST_OVERLAY_DIFFERS")
    role=derive_classifier_and_cases(world/author_test)
    if Path(role["source_file"]).resolve()!= (world/production).resolve():
        raise ValueError("CLASSIFIER_NOT_FROM_FROZEN_PRODUCTION")
    base,failing,candidates,classes=enumerate_projection_observations(
        role["classifier"],role["cases"],role["expected"]
    )
    result={
        "schema":"UDM_ATTRS_RESIDUAL_OBSERVATION_GENESIS_V1_RESULT",
        "status":"UNKNOWN",
        "source_base":src["base"],"author_head":src["author_head"],
        "classifier_name":role["classifier_name"],"argument_name":role["argument_name"],
        "case_count":len(role["cases"]),"base_vector":base,
        "failing_case_indices":failing,
        "candidate_observation_count":len(candidates),
        "observation_classes":classes,
        "future":"tox-dev/tox#4168","future_source":"UNOPENED",
        "G2":"UNKNOWN","G3":"UNKNOWN","G4":"UNKNOWN","G5":"UNKNOWN","G6":"UNKNOWN"
    }
    protected=[str(world/node.split("::",1)[0])+"::"+node.split("::",1)[1] for node in src["protected_nodes"]]
    baseline=run_pytest(world,protected,out/"baseline")
    result["baseline"]=baseline
    if baseline["counts"]["failures"]<1 or baseline["counts"]["errors"]!=0:
        result["status"]="UNKNOWN_BASELINE_RESIDUAL_NOT_REPRODUCED"
        (out/"RESULT.json").write_text(json.dumps(result,indent=2,sort_keys=True)+"\n")
        return result
    if not classes:
        result["status"]="REJECTED_NO_GENERATED_PROJECTION_OBSERVATION"
        (out/"RESULT.json").write_text(json.dumps(result,indent=2,sort_keys=True)+"\n")
        return result
    selected=classes[0]
    attribute=selected["representative"]
    repaired=generate_repair(original,role["classifier_name"],role["argument_name"],attribute)
    result["selected_observation"]={
        "class_id":selected["class_id"],"members":selected["members"],
        "selected_attribute":attribute,"repair_sha256":sha(repaired)
    }
    (out/"GENERATED_REPAIR.py").write_bytes(repaired)
    (world/production).write_bytes(repaired)
    a=run_pytest(world,protected,out/"repair-a")
    b=run_pytest(world,protected,out/"repair-b")
    full=run_pytest(world,[str(world/author_test)],out/"repair-full",timeout=420)
    result["repair_runs"]={"a":a,"b":b,"full_author_test":full}
    repair_good=(a["counts"]["failures"]==0 and a["counts"]["errors"]==0 and
                 b["counts"]["failures"]==0 and b["counts"]["errors"]==0 and
                 full["counts"]["tests"]>0 and full["counts"]["failures"]==0 and full["counts"]["errors"]==0)
    if not repair_good:
        (world/production).write_bytes(original)
        result["status"]="REJECTED_GENERATED_OBSERVATION_REPAIR_NATIVE"
        (out/"RESULT.json").write_text(json.dumps(result,indent=2,sort_keys=True)+"\n")
        return result
    (world/production).write_bytes(original)
    withdrawal=run_pytest(world,protected,out/"withdrawal")
    result["withdrawal"]=withdrawal
    if withdrawal["counts"]["failures"]<1 or withdrawal["counts"]["errors"]!=0:
        result["status"]="UNKNOWN_WITHDRAWAL_NOT_CAUSAL"
        (out/"RESULT.json").write_text(json.dumps(result,indent=2,sort_keys=True)+"\n")
        return result
    (world/production).write_bytes(repaired)
    restoration=run_pytest(world,protected,out/"restoration")
    result["restoration"]=restoration
    if restoration["counts"]["failures"] or restoration["counts"]["errors"]:
        result["status"]="UNKNOWN_RESTORATION_NOT_REVERIFIED"
        (out/"RESULT.json").write_text(json.dumps(result,indent=2,sort_keys=True)+"\n")
        return result
    result["status"]="WARRANTED_BOUNDED_REAL_SOURCE_RESIDUAL_TO_OBSERVATION_TO_REPAIR"
    result["causal_withdrawal"]=True
    result["restoration"]=True
    (out/"RESULT.json").write_text(json.dumps(result,indent=2,sort_keys=True)+"\n")
    return result

if __name__=="__main__":
    if len(sys.argv)!=3:
        raise SystemExit("usage: attrs_residual_observation_genesis_v1.py ATTRS_WORLD OUT")
    r=main(Path(sys.argv[1]),Path(sys.argv[2]))
    print(json.dumps({
      "status":r.get("status"),"classifier":r.get("classifier_name"),
      "failing_cases":r.get("failing_case_indices"),
      "observation_classes":len(r.get("observation_classes",[])),
      "selected":r.get("selected_observation",{}).get("selected_attribute"),
      "future_source":r.get("future_source"),"G2":r.get("G2")
    },sort_keys=True))
    raise SystemExit(0 if r.get("status") in {
      "WARRANTED_BOUNDED_REAL_SOURCE_RESIDUAL_TO_OBSERVATION_TO_REPAIR",
      "REJECTED_NO_GENERATED_PROJECTION_OBSERVATION",
      "REJECTED_GENERATED_OBSERVATION_REPAIR_NATIVE"
    } else 2)
