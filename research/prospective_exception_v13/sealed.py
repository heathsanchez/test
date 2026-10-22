#!/usr/bin/env python3
"""Sealed independent upstream one-hop exception acquisition V13.

Reads only fixed source-author tests. Produces UNKNOWN on ineligible sources.
Does not execute the AST or infer requirements from test failures.
"""
import ast,hashlib,json,pathlib,subprocess
ROOT=pathlib.Path(__file__).resolve().parents[2]
UP=ROOT/"upstream";HERE=pathlib.Path(__file__).resolve().parent
PIN="672971d66a2ef9f85151e53283113f33d642dabd"
TARGETS=(
 "tests/test_itsdangerous/test_serializer.py",
 "tests/test_itsdangerous/test_timed.py",
 "tests/test_itsdangerous/test_url_safe.py",
)
OUT=HERE/"result.json"

def eligible_source(test):
    tree=ast.parse(test)
    imported={}
    for node in tree.body:
        if isinstance(node,ast.ImportFrom) and node.module and (
                node.module=="itsdangerous" or node.module.startswith("itsdangerous.")):
            for alias in node.names:
                imported[alias.asname or alias.name]=(node.module,alias.name)
    accepted=[];declined=[]
    for fn in tree.body:
        if not isinstance(fn,ast.FunctionDef):continue
        for index,node in enumerate(fn.body):
            if not isinstance(node,ast.With):continue
            reason="UNSUPPORTED_CONTEXT_OR_LOCAL_DATAFLOW"
            if index<1:
                declined.append({"line":node.lineno,"reason":"NO_IMMEDIATELY_PRECEDING_CONSTRUCTOR"});continue
            prev=fn.body[index-1]
            if not (isinstance(prev,ast.Assign) and len(prev.targets)==1 and
                    isinstance(prev.targets[0],ast.Name) and isinstance(prev.value,ast.Call) and
                    isinstance(prev.value.func,ast.Name) and prev.value.func.id in imported):
                declined.append({"line":node.lineno,"reason":"NO_ADMITTED_CONSTRUCTOR"});continue
            variable=prev.targets[0].id
            ctor=prev.value
            ctx=node.items[0].context_expr if len(node.items)==1 else None
            if (len(node.items)!=1 or node.items[0].optional_vars is not None or
                not isinstance(ctx,ast.Call) or not isinstance(ctx.func,ast.Attribute) or
                not isinstance(ctx.func.value,ast.Name) or ctx.func.value.id!="pytest" or
                ctx.func.attr!="raises" or len(ctx.args)!=1 or ctx.keywords or
                not isinstance(ctx.args[0],ast.Name) or len(node.body)!=1 or
                not isinstance(node.body[0],ast.Expr) or
                not isinstance(node.body[0].value,ast.Call)):
                declined.append({"line":node.lineno,"reason":reason});continue
            call=node.body[0].value
            if not (isinstance(call.func,ast.Attribute) and
                isinstance(call.func.value,ast.Name) and call.func.value.id==variable):
                declined.append({"line":node.lineno,"reason":"UNSUPPORTED_RECEIVER"});continue
            try:
                constructor_args=[ast.literal_eval(x) for x in ctor.args]
                constructor_kwargs={x.arg:ast.literal_eval(x.value) for x in ctor.keywords}
                invocation_args=[ast.literal_eval(x) for x in call.args]
                invocation_kwargs={x.arg:ast.literal_eval(x.value) for x in call.keywords}
                if None in constructor_kwargs or None in invocation_kwargs:raise ValueError
            except (ValueError,TypeError,RecursionError,OverflowError):
                declined.append({"line":node.lineno,"reason":"NONLITERAL_EXPRESSION"});continue
            accepted.append({"line":node.lineno,"constructor":imported[ctor.func.id],
                "constructor_args":repr(constructor_args),"constructor_kwargs":repr(constructor_kwargs),
                "method":call.func.attr,"args":repr(invocation_args),
                "kwargs":repr(invocation_kwargs),"exception":ctx.args[0].id})
    return accepted,declined

def main():
    assert subprocess.check_output(["git","rev-parse","HEAD"],cwd=UP,text=True).strip()==PIN
    audit=[]
    selection=None
    for path in TARGETS:
        source=(UP/path).read_text()
        accepted,declined=eligible_source(source)
        entry={"path":path,"sha256":hashlib.sha256(source.encode()).hexdigest(),
               "git_blob":subprocess.check_output(["git","rev-parse","HEAD:"+path],cwd=UP,text=True).strip(),
               "accepted_count":len(accepted),"declined_count":len(declined),
               "accepted":accepted[:12],"declined":declined[:15]}
        audit.append(entry)
        if accepted:
            selection=entry;break
    verdict="WARRANTED_PROSPECTIVE_EXCEPTION_EXTRACTION" if selection else "UNKNOWN_NO_ADMISSIBLE_EXCEPTION_OBLIGATION"
    report={"status":verdict,"upstream":"pallets/itsdangerous","upstream_commit":PIN,
        "precommitted_targets":list(TARGETS),"selection":selection,"audited":audit,
        "source_grammar":"top-level test function, direct preceding literal constructor, unbound raises context",
        "postexposure_adaptation":"NONE","source_author_witness_executed":False,
        "native_mutation_checked":False,"release":"UNKNOWN"}
    OUT.write_text(json.dumps(report,indent=2,sort_keys=True)+"\n")
    print(json.dumps({"status":verdict,"audited":[(e["path"],e["accepted_count"]) for e in audit],
       "witness_count":0 if selection is None else selection["accepted_count"]},sort_keys=True))
if __name__=="__main__":main()
