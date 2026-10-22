#!/usr/bin/env python3
"""V12b post-exposure local-def-use source-author exception witness."""
import ast,hashlib,json,os,pathlib,subprocess,sys,time
ROOT=pathlib.Path(__file__).resolve().parents[2];UP=ROOT/"upstream"
HERE=pathlib.Path(__file__).resolve().parent
PIN="672971d66a2ef9f85151e53283113f33d642dabd"
TEST=UP/"tests/test_itsdangerous/test_signer.py"
SOURCE=UP/"src/itsdangerous/signer.py"
OUT=HERE/"postexposure_result.json"
TEST_BLOB="1e053883aad5b517cb3acf3f7c46d2561bb33b96"
SOURCE_BLOB="e324dc03da90d9002200b68088f501df62777cd6"
ORIGINAL="        raise NotImplementedError()"
MUTATED='        return b""'
def git(*args):
    return subprocess.check_output(["git",*args],cwd=UP,text=True).strip()
def literal(node):
    return ast.literal_eval(node)
def extract(test):
    t=ast.parse(test)
    imported={}
    for node in t.body:
        if isinstance(node,ast.ImportFrom) and node.module and node.module.startswith("itsdangerous"):
            for alias in node.names:
                imported[alias.asname or alias.name]=(node.module,alias.name)
    items=[]
    for fn in t.body:
        if not isinstance(fn,(ast.FunctionDef,ast.ClassDef)):continue
        # No class methods or fixtures accepted; directly body of top-level def.
        if not isinstance(fn,ast.FunctionDef):continue
        for idx,node in enumerate(fn.body):
            if not isinstance(node,ast.With) or idx<1:continue
            prev=fn.body[idx-1]
            if not isinstance(prev,ast.Assign) or len(prev.targets)!=1 or not isinstance(prev.targets[0],ast.Name):
                continue
            variable=prev.targets[0].id
            ctor=prev.value
            if not isinstance(ctor,ast.Call) or not isinstance(ctor.func,ast.Name) or ctor.func.id not in imported or ctor.keywords:continue
            try:ctor_args=tuple(literal(a) for a in ctor.args)
            except (ValueError,TypeError,OverflowError,RecursionError):continue
            if len(node.items)!=1 or node.items[0].optional_vars is not None or len(node.body)!=1:continue
            ctx=node.items[0].context_expr
            if not isinstance(ctx,ast.Call) or ast.unparse(ctx.func)!="pytest.raises" or len(ctx.args)!=1 or ctx.keywords:continue
            if not isinstance(ctx.args[0],ast.Name):continue
            expect=ctx.args[0].id
            if expect not in vars(__builtins__) and expect not in imported and expect!="NotImplementedError":
                continue
            body=node.body[0]
            if not isinstance(body,ast.Expr) or not isinstance(body.value,ast.Call):continue
            call=body.value
            if not isinstance(call.func,ast.Attribute) or not isinstance(call.func.value,ast.Name) or call.func.value.id!=variable or call.keywords:continue
            try:args=tuple(literal(a) for a in call.args)
            except (ValueError,TypeError,OverflowError,RecursionError):continue
            items.append({"line":node.lineno,"constructor_module":imported[ctor.func.id][0],
              "constructor_class":imported[ctor.func.id][1],"constructor_args":ctor_args,
              "method":call.func.attr,"method_args":args,"expected_exception":expect,
              "source":ast.get_source_segment(test,node)})
    return items
def safe_encode(value):
    if isinstance(value,bytes):return {"type":"bytes","value":value.hex()}
    if isinstance(value,(str,int,float,bool)) or value is None:return {"type":type(value).__name__,"value":value}
    raise TypeError("NOT_ADMITTED_LITERAL")
def worker(cases):
    material=[{k:([safe_encode(x) for x in v] if k in ("constructor_args","method_args") else v)
      for k,v in case.items() if k!="source"} for case in cases]
    spec=HERE/"cases.json";spec.write_text(json.dumps(material,indent=2)+"\n")
    env=os.environ.copy();env["PYTHONPATH"]=str(UP/"src")
    t=time.perf_counter()
    proc=subprocess.run([sys.executable,str(HERE/"worker.py"),str(spec)],cwd=UP,
       env=env,text=True,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,timeout=90)
    try:response=json.loads(proc.stdout.strip().splitlines()[-1])
    except Exception:response={"worker_error":proc.stdout[-500:]}
    return {"exit":proc.returncode,"result":response,"elapsed_seconds":round(time.perf_counter()-t,6)}
def native():
    t=time.perf_counter()
    env=os.environ.copy();env["PYTHONPATH"]=str(UP/"src")
    proc=subprocess.run([sys.executable,"-m","pytest","-q","tests/test_itsdangerous/test_signer.py"],
        cwd=UP,env=env,text=True,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,timeout=120)
    return {"passed":proc.returncode==0,"exit":proc.returncode,
            "elapsed_seconds":round(time.perf_counter()-t,6),"tail":proc.stdout.splitlines()[-8:]}
def warrant(valid):
    sys.path.insert(0,str(ROOT/"mathgraph_pinned"))
    from mathgraph_check.warrant_resolution import Claim,Receipt,Route,resolve_graph
    scope="itsdangerous:signer-exception-witness:v12b"
    claims=[Claim(i,"documentary",scope) for i in ("source","witness","protected","independent","release")]
    receipts=[Receipt(i,"documentary",scope) for i in
        ("source_pin","test_pin","witness_native","policy","independent_evidence")]
    routes=[Route("source",("source_pin","test_pin")),
            Route("witness",("witness_native",)),
            Route("protected",("policy",),("source","witness")),
            Route("independent",("independent_evidence",))]
    initial=frozenset() if valid else frozenset({"witness_native"})
    states=dict(resolve_graph(claims,routes,receipts,withdrawn=initial).states)
    assert states["release"]=="UNKNOWN"
    assert states["protected"]==("SOURCE_DOCUMENTED" if valid else "UNKNOWN")
    assert states["independent"]=="SOURCE_DOCUMENTED"
    if valid:
        for x in ("source_pin","test_pin","witness_native","policy"):
            s=dict(resolve_graph(claims,routes,receipts,withdrawn=frozenset((x,))).states)
            assert s["protected"]=="UNKNOWN" and s["independent"]=="SOURCE_DOCUMENTED"
    return states["protected"]
def main():
    assert git("rev-parse","HEAD")==PIN
    assert git("rev-parse","HEAD:tests/test_itsdangerous/test_signer.py")==TEST_BLOB
    assert git("rev-parse","HEAD:src/itsdangerous/signer.py")==SOURCE_BLOB
    tests=TEST.read_text();original=SOURCE.read_text()
    cases=extract(tests)
    assert cases,"POSTEXPOSURE_LOCAL_DEFUSE_EXTRACTOR_FOUND_ZERO"
    assert original.count(ORIGINAL)==1
    mutated=original.replace(ORIGINAL,MUTATED,1)
    assert mutated.replace(MUTATED,ORIGINAL,1)==original
    try:
        original_witness=worker(cases)
        original_suite=native()
        SOURCE.write_text(mutated)
        bad_witness=worker(cases)
        bad_suite=native()
    finally:
        SOURCE.write_text(original)
    match_original=original_witness["result"].get("matched")==len(cases)
    match_bad=bad_witness["result"].get("matched",len(cases))<len(cases)
    qualified=match_original and match_bad and original_suite["passed"] and not bad_suite["passed"]
    doc={"original":warrant(match_original),"wrong_source":warrant(False)}
    result={"status":"POSTEXPOSURE_EXCEPTION_OBLIGATION_WARRANTED" if qualified else "UNKNOWN_POSTEXPOSURE_NATIVE_QUALIFICATION",
      "original_sealed_v12":"UNKNOWN_NO_ADMISSIBLE_EXCEPTION_OBLIGATIONS",
      "upstream":"pallets/itsdangerous","upstream_commit":PIN,
      "test_git_blob":TEST_BLOB,"implementation_git_blob":SOURCE_BLOB,
      "source_sha256_original":hashlib.sha256(original.encode()).hexdigest(),
      "source_sha256_mutated":hashlib.sha256(mutated.encode()).hexdigest(),
      "extracted_count":len(cases),
      "source_authored_cases":[{"line":x["line"],"expected_exception":x["expected_exception"],"source":x["source"]} for x in cases],
      "original_generated_native":original_witness,"mutated_generated_native":bad_witness,
      "original_upstream_test":original_suite,"mutated_upstream_test":bad_suite,
      "actual_mathgraph_documentary_warrants":doc,
      "source_rewrite":"exact first SigningAlgorithm.get_signature NotImplementedError raise -> return b''",
      "comparison":"conventional upstream tests also kill mutant; no unique advantage",
      "acquisition_scope":"single local constructor assignment preceding pytest.raises body; post-exposure",
      "full_release":"UNKNOWN"}
    OUT.write_text(json.dumps(result,indent=2,sort_keys=True)+"\n")
    print(json.dumps({"status":result["status"],"cases":len(cases),
      "matches":[original_witness["result"].get("matched"),bad_witness["result"].get("matched")],
      "upstream_suite_passes":[original_suite["passed"],bad_suite["passed"]],
      "original_sealed":"UNKNOWN","conventional":"TIE"},sort_keys=True))
    if not qualified:raise RuntimeError("POSTEXPOSURE_NATIVE_QUALIFICATION_FAILED")
if __name__=="__main__":main()
