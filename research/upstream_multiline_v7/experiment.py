#!/usr/bin/env python3
"""Prospective cross-repository AST transform; source code is untouched until run."""
import ast, hashlib, json, os, pathlib, subprocess, sys, time
ROOT=pathlib.Path(__file__).resolve().parents[2]
UP=ROOT/"upstream"
HERE=pathlib.Path(__file__).resolve().parent
PIN="672971d66a2ef9f85151e53283113f33d642dabd"
TARGET=UP/"src/itsdangerous/encoding.py"
NAME="_mg_retained_result_v7"
OUT=HERE/"result.json"

def cmd(command):
    t=time.perf_counter()
    env=os.environ.copy()
    env["PYTHONPATH"]=str(UP/"src")
    try:
        p=subprocess.run(command,cwd=UP,env=env,text=True,
          stdout=subprocess.PIPE,stderr=subprocess.STDOUT,timeout=150)
        return {"status":"FINISHED","ok":p.returncode==0,"code":p.returncode,
          "elapsed_seconds":round(time.perf_counter()-t,6),
          "tail":p.stdout.strip().splitlines()[-12:]}
    except subprocess.TimeoutExpired:
        return {"status":"TIMEOUT","ok":False}

def eligible(source):
    tree=ast.parse(source)
    for function in tree.body:
        if not isinstance(function,ast.FunctionDef):continue
        if not function.body or not isinstance(function.body[-1],ast.Return):continue
        final=function.body[-1]
        if final.value is None:continue
        subtree=list(ast.walk(function))
        if any(isinstance(x,(ast.Yield,ast.YieldFrom,ast.Await,
                             ast.AsyncFunctionDef)) for x in subtree):continue
        if any(isinstance(x,ast.Name) and x.id==NAME for x in subtree):continue
        if any(isinstance(x,ast.Call) and isinstance(x.func,ast.Name) and
             x.func.id in ("locals","vars","eval","exec","dir") for x in subtree):continue
        if not all(isinstance(x,ast.FunctionDef) is False or x is function for x in subtree):
            continue
        expr=ast.get_source_segment(source,final.value)
        if not expr or "\r" in expr:continue
        return function,final,expr
    return None

def rewrite(source):
    result=eligible(source)
    if result is None:return None
    fn,node,expr=result
    lines=source.splitlines(keepends=True)
    start=node.lineno-1; end=node.end_lineno-1
    original=lines[start:end+1]
    # Exact Python AST col_offset is UTF-8 bytes; this frozen grammar accepts
    # ASCII indentation and leading return text only.
    prefix=lines[start][:node.col_offset]
    if prefix.strip() or not prefix.isspace():return None
    if not lines[start][node.col_offset:].startswith("return "):return None
    # Any post-return content or inline comments are unsupported.
    endtrail=lines[end][node.end_col_offset:].strip()
    if endtrail and not endtrail.startswith("#"):return None
    if endtrail.startswith("#"):return None
    replacement=prefix+NAME+" = "+expr+"\n"+prefix+"return "+NAME+"\n"
    edited="".join(lines[:start]+[replacement]+lines[end+1:])
    try:ast.parse(edited)
    except SyntaxError:return None
    return {"function":fn.name,"start_line":node.lineno,
      "end_line":node.end_lineno,"expression_multiline":"\n" in expr,
      "old_source_sha256":hashlib.sha256(source.encode()).hexdigest(),
      "new_source_sha256":hashlib.sha256(edited.encode()).hexdigest(),
      "edited":edited,"return_marker":prefix+"return "+NAME}

def test_graph():
    paths=sorted((UP/"tests").rglob("test_*.py"))
    results={}
    for path in paths:
        text=path.read_text()
        tree=ast.parse(text)
        imports=[];opaque=[]
        for n in ast.walk(tree):
            if isinstance(n,ast.Import):imports.extend(x.name for x in n.names)
            if isinstance(n,ast.ImportFrom):imports.append(n.module or "")
            if isinstance(n,ast.Call) and isinstance(n.func,ast.Attribute):
                if n.func.attr in ("import_module","exec_module","spec_from_file_location","read_text","Popen","run"):
                    opaque.append(n.func.attr)
        name=str(path.relative_to(UP))
        results[name]={"imports":imports[:20],"opaque":opaque[:12],
            "selected":"KEEP","reason":"package indirect import or runtime effect not independently closed"}
    return results

def synthetic_control():
    original="from itsdangerous import URLSafeSerializer\n"
    injected="import importlib\n_ = importlib.import_module('itsdangerous.encoding')\n"
    assert "import_module(" in injected and "itsdangerous" in original
    return {"dynamic_import_example":"KEEP_UNCERTAIN",
      "transitive_import_example":"KEEP_UNCERTAIN",
      "purpose":"negative examples, not actual defect injection into upstream tests"}

def main():
    assert subprocess.check_output(["git","rev-parse","HEAD"],cwd=UP,text=True).strip()==PIN
    original=TARGET.read_text()
    proposed=rewrite(original)
    if proposed is None:
        report={"status":"UNKNOWN_NO_ADMISSIBLE_MULTILINE_REWRITE",
                "upstream_commit":PIN,"source_sha256":hashlib.sha256(original.encode()).hexdigest()}
        OUT.write_text(json.dumps(report,indent=2)+"\n");print(json.dumps(report));return
    edited=proposed.pop("edited")
    native_graph=test_graph()
    native_baseline=cmd([sys.executable,"-m","pytest","-q","tests"])
    TARGET.write_text(edited)
    try:
        native_changed=cmd([sys.executable,"-m","pytest","-q","tests"])
        bad=edited.replace(proposed["return_marker"],proposed["return_marker"].replace(
                "return "+NAME,"return None"),1)
        assert bad!=edited
        TARGET.write_text(bad)
        native_mutant=cmd([sys.executable,"-m","pytest","-q","tests"])
    finally:
        TARGET.write_text(original)
    altered_caught=not native_mutant["ok"]
    both_ok=native_baseline["ok"] and native_changed["ok"]
    verdict=("UNKNOWN_NATIVE_UPSTREAM_TEST_ENVIRONMENT" if not both_ok else
             "UNKNOWN_MUTATION_NOT_DETECTED" if not altered_caught else
             "WARRANTED_BOUNDED_EXTERNAL_MULTILINE_NATIVE_REFACTOR")
    report={"status":verdict,"upstream_repository":"pallets/itsdangerous",
      "upstream_commit":PIN,"target":"src/itsdangerous/encoding.py",
      "proposal":proposed,"native_baseline":native_baseline,
      "native_changed":native_changed,"native_wrong_mutation":native_mutant,
      "mutation_detected":altered_caught,"real_test_import_profile":native_graph,
      "actual_safe_skips":[],"conventional_full_info_selector":"KEEP_ALL",
      "comparison":"TIE_ON_NO_SAFE_SKIPS","negative_controls":synthetic_control(),
      "total_pytest_process_seconds":sum(x.get("elapsed_seconds",0) for x in
                            (native_baseline,native_changed,native_mutant)),
      "full_release":"UNKNOWN","limitations":[
      "same rewrite pattern as exposed MarkupSafe but new uninspected source at freeze",
      "extra assignment may affect introspection and tracing",
      "finite native suite not universal Python semantic proof",
      "no stronger than dependency-aware conventional test selector",
      "all upstream tests run in experiment: no realized CI saving",
      "no MathGraph R7.2 CLC cross-language admission"]}
    OUT.write_text(json.dumps(report,indent=2,sort_keys=True)+"\n")
    print(json.dumps({"status":verdict,"selection":proposed["function"],
      "multiline":proposed["expression_multiline"],
      "upstream_tests":[native_baseline["ok"],native_changed["ok"],native_mutant["ok"]],
      "safely_skipped":0,"comparison":"TIE"},sort_keys=True))
    if verdict=="UNKNOWN_NATIVE_UPSTREAM_TEST_ENVIRONMENT":
        raise RuntimeError("Upstream native regression not green")
if __name__=="__main__":main()
