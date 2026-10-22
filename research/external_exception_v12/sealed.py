#!/usr/bin/env python3
"""Sealed V12 extractor: no post-exposure fitting of fixture-bound receivers."""
import ast,hashlib,json,pathlib,subprocess
ROOT=pathlib.Path(__file__).resolve().parents[2]
UP=ROOT/"upstream"
P=UP/"tests/test_itsdangerous/test_signer.py"
OUT=pathlib.Path(__file__).with_name("sealed_result.json")
PIN="672971d66a2ef9f85151e53283113f33d642dabd"
SHA="1e053883aad5b517cb3acf3f7c46d2561bb33b96"
def main():
    assert subprocess.check_output(["git","rev-parse","HEAD"],cwd=UP,text=True).strip()==PIN
    assert subprocess.check_output(["git","rev-parse","HEAD:tests/test_itsdangerous/test_signer.py"],cwd=UP,text=True).strip()==SHA
    text=P.read_text()
    tree=ast.parse(text)
    candidates=[]
    declined=[]
    for node in ast.walk(tree):
        if not isinstance(node,ast.With):continue
        if len(node.items)!=1 or node.items[0].optional_vars is not None:
            declined.append({"line":node.lineno,"reason":"MULTI_OR_BOUND_CONTEXT"});continue
        item=node.items[0].context_expr
        if not isinstance(item,ast.Call) or item.keywords or len(item.args)!=1:
            declined.append({"line":node.lineno,"reason":"UNKNOWN_PYTEST_RAISES_CONTEXT"});continue
        if ast.unparse(item.func)!="pytest.raises" or len(node.body)!=1 or not isinstance(node.body[0],ast.Expr) or not isinstance(node.body[0].value,ast.Call):
            declined.append({"line":node.lineno,"reason":"UNSUPPORTED_CONTEXT_BODY"});continue
        expr=node.body[0].value
        try:
            for a in expr.args:ast.literal_eval(a)
            for kw in expr.keywords:ast.literal_eval(kw.value)
        except (TypeError,ValueError,OverflowError,RecursionError):
            declined.append({"line":node.lineno,"reason":"NONLITERAL_ARGUMENT"});continue
        receiver=ast.unparse(expr.func)
        if not receiver.startswith("itsdangerous."):
            declined.append({"line":node.lineno,"reason":"UNKNOWN_RECEIVER_AUTHORITY"});continue
        candidates.append({"line":node.lineno,"native_call":receiver,"expected":ast.unparse(item.args[0])})
    result={"status":"WARRANTED_BOUNDED_EXCEPTION_OBLIGATIONS" if candidates else "UNKNOWN_NO_ADMISSIBLE_EXCEPTION_OBLIGATIONS",
      "upstream":"pallets/itsdangerous","commit":PIN,"source_test_git_blob":SHA,
      "source_sha256":hashlib.sha256(text.encode()).hexdigest(),
      "eligible":candidates[:12],"declined":declined,
      "syntax_grammar":"no bound pytest.raises context; direct imported project dotted caller and literal args",
      "postexposure_relaxation":"NOT_APPLIED"}
    OUT.write_text(json.dumps(result,indent=2,sort_keys=True)+"\n")
    print(json.dumps({"status":result["status"],"eligible":len(candidates),
      "declined":len(declined)},sort_keys=True))
if __name__=="__main__":main()
