"""V14: schedule ORIGINAL source-pinned V104 builders at an observed AST slot.

Emission and candidate syntax only; no new grammar or trusted native outcome.
Original V104 SELECTORS, BUILDERS, build_expr and h are loaded from their
independently pinned Git source, not reimplemented. The only change is asking
which authentic site to try *before* the fixed program emission budget.

This is a previously exposed Tenacity diagnostic, NOT autonomous G2.
"""
from __future__ import annotations

import ast
import copy
import hashlib
import json
from pathlib import Path

from . import qualify_v8_exposed_stratified_v104 as previous
from . import typed_source_inventory_v5 as typed
from . import decisive_native as original

G2=G3=G4=G5=G6="UNKNOWN"
SCHEMA="UDM_V14_OBSERVED_SOURCE_SLOT_ORIGINAL_V104_SCHEDULER"


def original_programs(triskelion):
    """Only the exact historical authenticated V104 grammar may be loaded."""
    ns,pin=previous._original_program_namespace(Path(triskelion).absolute())
    if (pin["commit"]!="426c54f7c774560e0fabe7213c5ef333b1327c71"
            or len(ns["BUILDERS"])!=15
            or len(ns["SELECTORS"])!=5
            or ("If","test") not in ns["SELECTORS"]):
        raise ValueError("original V104 grammar identity changed")
    return ns,pin


def targeted_original_candidates(src,path,event,triskelion,*,cap=8):
    typed._path(path)
    if not path.endswith(".py") or not isinstance(src,str):
        raise ValueError("original Python production source required")
    if not isinstance(event,dict):
        raise ValueError("independent source/branch observation required")
    fields={"path","line","attribute","branch","callable","kind","then_line"}
    if (not fields <= event.keys() or event["path"]!=path
            or not isinstance(event["line"],int) or event["line"]<1
            or not isinstance(event["then_line"],int)
            or event["then_line"]<=event["line"]
            or not isinstance(event["attribute"],str)
            or event["kind"]!="IF_NOT_SELF_ATTRIBUTE"
            or event["branch"]!="THEN" or event["callable"] is not True):
        raise ValueError("unwarranted or incomplete observed source slot")
    if not isinstance(cap,int) or cap<1 or cap>64:
        raise ValueError("source method emission cap out of range")
    try:tree=ast.parse(src,filename=path)
    except (SyntaxError,UnicodeError) as error:
        raise ValueError("source AST unavailable") from error

    slot=[]
    for node in ast.walk(tree):
        if not isinstance(node,ast.If) or node.lineno!=event["line"]:
            continue
        x=node.test
        if not (isinstance(x,ast.UnaryOp) and isinstance(x.op,ast.Not)
                and isinstance(x.operand,ast.Attribute)
                and isinstance(x.operand.value,ast.Name)
                and x.operand.value.id=="self"
                and x.operand.attr==event["attribute"]):
            continue
        then_lines={child.lineno for body in node.body for child in ast.walk(body)
                    if hasattr(child,"lineno") and child.lineno>node.lineno}
        if event["then_line"] in then_lines:slot.append(node)
    if len(slot)!=1:
        raise ValueError("observed source cannot be uniquely mapped to original If.test AST")
    target=slot[0]
    ns,pin=original_programs(triskelion)
    selector=("If","test")
    positions=ns["nodes_for_selector"](tree,selector)
    matching=[i for i,(n,field,arg) in enumerate(positions)
              if n is target and field=="test" and arg is None]
    if len(matching)!=1:
        raise ValueError("original V104 selector cannot identify observed slot")
    index=matching[0]
    names=sorted({n.id for n in ast.walk(tree) if isinstance(n,ast.Name)})
    programs=sorted(((selector,b) for b in ns["BUILDERS"]),
                    key=lambda pair:ns["h"]("program|"+repr(pair)))
    out=[];seen={src}
    for sel,builder in programs:
        for replacement in ns["build_expr"](builder,names,target.test):
            amended=copy.deepcopy(tree)
            slots=ns["nodes_for_selector"](amended,sel)
            if index>=len(slots):
                raise ValueError("original V104 AST source index changed")
            new_node,field,arg=slots[index]
            if field!="test" or arg is not None:
                raise ValueError("V104 slot grammar unexpectedly differs")
            setattr(new_node,field,copy.deepcopy(replacement))
            try:
                text=ast.unparse(ast.fix_missing_locations(amended))
                parsed=ast.parse(text,filename=path)
            except (SyntaxError,ValueError,TypeError,UnicodeError):
                continue
            if text in seen:continue
            changed=original.changed_lines(src,text)
            if event["line"] not in changed:
                continue
            seen.add(text)
            out.append({"schema":SCHEMA,"grammar":"PINNED_ORIGINAL_V104_BUILDERS_ONLY",
                        "status":"CANDIDATE_NO_NATIVE_WARRANT",
                        "path":path,"observed_line":event["line"],
                        "observed_attribute":event["attribute"],"selector":sel,
                        "builder":builder,"source":text,
                        "source_sha256":hashlib.sha256(text.encode("utf-8")).hexdigest(),
                        "original_v104_method_sha256":pin["sha256"],
                        "changed_lines":list(changed)})
            if len(out)>=cap:
                return out
    return out
