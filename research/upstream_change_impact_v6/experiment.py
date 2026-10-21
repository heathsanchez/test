#!/usr/bin/env python3
"""Prospective external MarkupSafe source-change & native-test impact audit.

It refuses to generalize syntax-preserving edits to arbitrary Python semantics.
Writes only into an ephemeral checkout of third-party upstream, never upstream.
"""
import ast,hashlib,json,os,pathlib,re,subprocess,sys,time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
HERE=Path(__file__).resolve().parent
UP=ROOT/"upstream"
PIN="4e111271b1494995708a9e878a10829b5e10c7ba"
TARGET="src/markupsafe/_native.py"
TMP="_mg_equivalent_result_v6"
OUT=HERE/"result.json"

def command(args,env=None,timeout=120):
    t=time.perf_counter()
    p=subprocess.run(args,cwd=UP,env=env,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,
                     text=True,timeout=timeout)
    return {"ok":p.returncode==0,"returncode":p.returncode,
            "seconds":round(time.perf_counter()-t,6),
            "tail":p.stdout.splitlines()[-14:],"command":" ".join(args)}

def git(*args):
    return subprocess.check_output(["git",*args],cwd=UP,text=True).strip()

def candidate(source):
    tree=ast.parse(source)
    lines=source.splitlines(keepends=True)
    class Find(ast.NodeVisitor):
        def __init__(self):
            self.stack=[];self.candidates=[]
        def visit_FunctionDef(self,node):
            self.stack.append(node)
            self.generic_visit(node)
            self.stack.pop()
        visit_AsyncFunctionDef=visit_FunctionDef
        def visit_Return(self,node):
            if not self.stack or node.value is None or node.lineno!=node.end_lineno:
                return
            fn=self.stack[-1]
            if any(isinstance(x,(ast.Yield,ast.YieldFrom,ast.Await,ast.NamedExpr)) for x in ast.walk(node.value)):
                return
            if any(isinstance(x,ast.Name) and x.id==TMP for x in ast.walk(fn)):
                return
            if any(isinstance(x,ast.Call) and isinstance(x.func,ast.Name) and
                   x.func.id in ("locals","vars","eval","exec","dir") for x in ast.walk(fn)):
                return
            old=lines[node.lineno-1]
            if not re.match(r"^\s*return\s",old):return
            self.candidates.append((node,old))
    v=Find();v.visit(tree)
    if not v.candidates:return None
    node,old=v.candidates[0]
    indent=old[:len(old)-len(old.lstrip())]
    # Source excerpt exactly one return statement with no trailing comment.
    match=re.fullmatch(r"(\s*)return\s+(.+?)\s*\n?",old)
    if not match:return None
    expression=match.group(2)
    if "#" in expression:return None
    replacement=indent+TMP+" = "+expression+"\n"+indent+"return "+TMP+"\n"
    amended=lines[:]
    amended[node.lineno-1]=replacement
    return {"function":v.stack[-1].name if v.stack else "first eligible",
      "line":node.lineno,"old_line":old.rstrip(),
      "new_lines":replacement.strip().splitlines(),
      "changed_source":"".join(amended)}

def inspect_test(path,source):
    tree=ast.parse(source)
    roots=set()
    opaque=[]
    for node in ast.walk(tree):
        if isinstance(node,ast.Import):
            roots.update(x.name for x in node.names)
        elif isinstance(node,ast.ImportFrom):
            roots.add(node.module or "")
            if node.level:opaque.append("relative-import")
        elif isinstance(node,ast.Call):
            f=node.func
            if isinstance(f,ast.Name) and f.id in ("open","eval","exec","__import__","getattr"):
                opaque.append("dynamic-name-"+f.id)
            if isinstance(f,ast.Attribute) and f.attr in (
                    "import_module","spec_from_file_location","exec_module",
                    "read_text","read_bytes","getsource","run","Popen"):
                opaque.append("dynamic-attribute-"+f.attr)
    # Source is within an upstream package whose __init__ may import _native
    # and even speedups; absent direct import does not establish independence.
    touched=any(x=="markupsafe" or x.startswith("markupsafe.") for x in roots)
    return {"imports":sorted(roots),"opaque":sorted(set(opaque)),
      "package_dependency":touched,
      "candidate_safe_skip":False,
      "reason":"package-boundary or pytest/plugin/runtime effects not independently closed"}

def baseline_selector(analyses):
    """Equally informed conventional dependency-aware selector: retain all
       if source is package-module and importing tests/module could execute it."""
    return [name for name,row in analyses.items()
            if row["package_dependency"] or row["opaque"] or True]

def dynamic_negative():
    payload="import importlib\nimportlib.import_module('markupsafe._native')\n"
    node=inspect_test("synthetic",payload)
    assert node["opaque"] and node["package_dependency"] is False
    return {"injected_dynamic_dependency":"RETAIN_OR_UNKNOWN",
            "detected":True}

def native_test():
    env=os.environ.copy()
    env["PYTHONPATH"]=str(UP/"src")
    return command([sys.executable,"-m","pytest","-q","tests"],env=env,timeout=180)

def main():
    assert git("rev-parse","HEAD")==PIN
    origin=UP/TARGET
    raw=origin.read_bytes()
    source=raw.decode("utf-8")
    proposal=candidate(source)
    if proposal is None:
        report={"status":"UNKNOWN_NO_ELIGIBLE_REFRACTOR","pin":PIN,
                "source_sha256":hashlib.sha256(raw).hexdigest()}
        OUT.write_text(json.dumps(report,indent=2)+"\n")
        print(json.dumps(report));return
    amended=proposal.pop("changed_source")
    raw_after=amended.encode("utf-8")
    assert hashlib.sha256(raw_after).digest()!=hashlib.sha256(raw).digest()
    # Freeze exact one-statement source edit and independent AST analysis.
    ast.parse(amended)
    assert ast.dump(ast.parse(source))!=ast.dump(ast.parse(amended))
    tests=sorted((UP/"tests").glob("test_*.py"))
    original_tests={str(p.relative_to(UP)):p.read_text() for p in tests}
    maps={key:inspect_test(key,value) for key,value in original_tests.items()}
    conventional=baseline_selector(maps)
    safe_skips=[k for k,v in maps.items() if v["candidate_safe_skip"]]
    assert not safe_skips
    negative=dynamic_negative()
    # Baseline actual upstream tests on unmodified code.
    baseline=native_test()
    # Apply SOURCE edit only in ephemeral checkout; rebuild editable src import
    # resolved by PYTHONPATH for all subprocess tests.
    origin.write_bytes(raw_after)
    changed=native_test()
    # Deliberate semantic fault: replace the changed first return expression
    # with None; must be detected by independently authored upstream tests.
    bad=amended.replace(proposal["new_lines"][0].split(" = ",1)[1],
                      "None",1)
    origin.write_text(bad)
    mutant=native_test()
    origin.write_bytes(raw_after)
    try:
        assert hashlib.sha256(origin.read_bytes()).digest()==hashlib.sha256(raw_after).digest()
        all_green=baseline["ok"] and changed["ok"]
        mutant_caught=not mutant["ok"]
        status=("UNKNOWN_UPSTREAM_TESTS_FAIL" if not all_green else
                "UNKNOWN_MUTATION_NOT_CAUGHT" if not mutant_caught else
                "NO_SAFE_REAL_SKIP_CONVENTIONAL_TIE")
        report={"status":status,"upstream_url":"https://github.com/pallets/markupsafe",
          "upstream_commit":PIN,"source_file":TARGET,
          "source_sha256_before":hashlib.sha256(raw).hexdigest(),
          "source_sha256_after":hashlib.sha256(raw_after).hexdigest(),
          "proposal":proposal,"real_upstream_test_files":list(original_tests),
          "impact_analysis":maps,"safe_skips":safe_skips,
          "conventional_equal_info_selection":conventional,
          "conventional_selection_compared":"TIE" if len(conventional)==len(original_tests) else "UNKNOWN",
          "dynamic_dependency_control":negative,
          "original_native_suite":baseline,"modified_native_suite":changed,
          "malicious_source_mutant_native_suite":mutant,
          "malicious_mutation_caught":mutant_caught,
          "release_authorization":"UNKNOWN",
          "total_pytest_process_seconds":round(sum(x["seconds"] for x in (baseline,changed,mutant)),6),
          "restrictions":["real upstream code; isolated ephemeral local source edit, no upstream PR",
            "source edit changes locals() and tracing observables; universal equivalence NOT proved",
            "no protected test skip absent independently closed package execution boundary",
            "baseline knows package dependency; no invalid strawman advantage",
            "all three suites executed; no global CI saving"]}
        OUT.write_text(json.dumps(report,indent=2,sort_keys=True)+"\n")
        print(json.dumps({"status":status,"upstream_pin":PIN,
          "source":TARGET,"safe_skips":safe_skips,
          "baseline_pass":baseline["ok"],"changed_pass":changed["ok"],
          "mutant_detected":mutant_caught,
          "conventional":"TIE"},sort_keys=True))
        if not all_green:raise RuntimeError("UPSTREAM_NATIVE_REGRESSION_FAILED")
    finally:
        # Never leave the isolated test checkout mutated.
        origin.write_bytes(raw)
if __name__=="__main__":main()
