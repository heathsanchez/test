"""V15 bounded compositional AST candidate language at verified observed source slots.

Uses generic Python AST atoms and pairwise Boolean composition. The grammar is
explicitly engineer supplied; candidate identity and the winning expression
are not. This only generates candidates; independent native execution decides
their consequences. This is NOT an open-ended intelligence or G2 warrant.
"""
from __future__ import annotations

import ast
import copy
import hashlib
from . import typed_source_inventory_v5 as typed

G2=G3=G4=G5=G6="UNKNOWN"
SCHEMA="UDM_V15_SOURCE_OBSERVED_BOUNDED_COMPOSITION"


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def _locate(tree,path,event):
    fields={"path","line","then_line","attribute","branch","callable","kind"}
    if (not isinstance(event,dict) or not fields<=event.keys() or
        event["path"]!=path or event["branch"]!="THEN" or
        event["kind"]!="IF_NOT_SELF_ATTRIBUTE" or
        event["callable"] is not True or
        not isinstance(event["line"],int) or event["line"]<=0 or
        not isinstance(event["then_line"],int) or event["then_line"]<=event["line"] or
        not isinstance(event["attribute"],str)):
        raise ValueError("missing source-bound native branch observation")
    slots=[]
    for node in ast.walk(tree):
        if not isinstance(node,ast.If) or node.lineno!=event["line"]:
            continue
        old=node.test
        if not (isinstance(old,ast.UnaryOp) and isinstance(old.op,ast.Not)
                and isinstance(old.operand,ast.Attribute)
                and isinstance(old.operand.value,ast.Name)
                and old.operand.value.id=="self"
                and old.operand.attr==event["attribute"]):
            continue
        executable={part.lineno for stmt in node.body for part in ast.walk(stmt)
                    if hasattr(part,"lineno") and part.lineno>node.lineno}
        if event["then_line"] in executable:
            slots.append(node)
    if len(slots)!=1:
        raise ValueError("ambiguous or missing observed original guard")
    return slots[0]


def _atoms(attribute,original):
    def attr():return copy.deepcopy(attribute)
    def call(name):
        return ast.Call(func=ast.Name(id=name,ctx=ast.Load()),
                        args=[attr()],keywords=[])
    old=copy.deepcopy(original)
    return (
       ("ORIGINAL_NOT",old),
       ("IS_NONE",ast.Compare(left=attr(),ops=[ast.Is()],
                               comparators=[ast.Constant(None)])),
       ("EQUALS_ZERO",ast.Compare(left=attr(),ops=[ast.Eq()],
                               comparators=[ast.Constant(0)])),
       ("NOT_CALLABLE",ast.UnaryOp(op=ast.Not(),operand=call("callable"))),
       ("CALLABLE",call("callable")),
       ("BOOL",call("bool")),
    )


def emit(source,path,event,*,cap=24):
    typed._path(path)
    if (not isinstance(source,str) or not path.endswith(".py")
            or type(cap) is not int or cap<1 or cap>24):
        raise ValueError("invalid original Python source or frozen finite cap")
    try:
        tree=ast.parse(source,filename=path)
    except (SyntaxError,ValueError,UnicodeError) as error:
        raise ValueError("original source Python syntax unavailable") from error
    node=_locate(tree,path,event)
    members=_atoms(node.test.operand,node.test)
    proposals=[]
    for name,expr in members:
        if name=="ORIGINAL_NOT":continue
        proposals.append((name,expr))
    for i,(left_name,left_expr) in enumerate(members):
        for right_name,right_expr in members[i+1:]:
            for tag,op in (("AND",ast.And()),("OR",ast.Or())):
                expr=ast.BoolOp(op=op,values=[
                    copy.deepcopy(left_expr),copy.deepcopy(right_expr)])
                proposals.append((tag+"_"+left_name+"_"+right_name,expr))

    # Fixed source-agnostic MDL: fewer AST constructors first, then a
    # deterministic source-independent hash. Neither test nor native outcome
    # selects an expression. No source-specific winning guard is supplied.
    proposals.sort(key=lambda item:(
        len(tuple(ast.walk(item[1]))),
        digest(("UDM_V15_COMPOSITION_ORDER|"+item[0]).encode()),
        item[0]))
    output=[];seen={ast.dump(node.test,include_attributes=False)}
    for name,expr in proposals:
        signature=ast.dump(expr,include_attributes=False)
        if signature in seen:continue
        seen.add(signature)
        edited=copy.deepcopy(tree)
        target=_locate(edited,path,event)
        target.test=copy.deepcopy(expr)
        try:
            result=ast.unparse(ast.fix_missing_locations(edited))
            ast.parse(result,filename=path)
        except (SyntaxError,ValueError,TypeError,UnicodeError):
            continue
        sha=digest(result.encode("utf-8"))
        output.append({
           "schema":SCHEMA,"status":"CANDIDATE_NOT_NATIVE_WARRANT",
           "path":path,"source_line":event["line"],
           "attribute":event["attribute"],"signature":name,
           "predicate_ast":signature,
           "predicate_nodes":len(tuple(ast.walk(expr))),
           "source_sha256":digest(source.encode("utf-8")),
           "sha256":sha,"source":result,
           "grammar":"SUPPLIED_GENERIC_AST_ATOM_AND_PAIR_COMPOSITION",
           "G2":"UNKNOWN"
        })
        if len(output)>=cap:break
    return output
