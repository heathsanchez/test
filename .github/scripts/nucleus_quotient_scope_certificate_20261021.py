#!/usr/bin/env python3
"""Exact-source Nucleus Γ12 scope diagnostic; no semantics or verdict changes.

Authority: Lean 4.34.1 @ 5045d0056413266e57c625dcd7c365b10e377c52;
original NDJSON 3.1.0 sha256:da02144b2d6109c86e5067b1e987744c2122820629bc8ece04dfb276f243239b.
Use only on a deliberately isolated branch; this is not a trusted equality rule.
"""
import hashlib
import json
import pathlib
import sys

SOURCE_HASH="da02144b2d6109c86e5067b1e987744c2122820629bc8ece04dfb276f243239b"

def inspect(source, destination):
    raw=pathlib.Path(source).read_bytes()
    digest=hashlib.sha256(raw).hexdigest()
    assert digest == SOURCE_HASH, (digest, SOURCE_HASH)
    rows=[json.loads(x) for x in raw.splitlines()]
    assert rows[0]["meta"]["format"]["version"] == "3.1.0"
    names={r["in"]:r for r in rows if "in" in r}
    exprs={r["ie"]:r for r in rows if "ie" in r}
    def name(i):
        if i == 0: return "_root_"
        r=names[i]
        if "str" in r:
            pre=name(r["str"]["pre"]); cur=r["str"]["str"]
        else:
            pre=name(r["num"]["pre"]); cur=str(r["num"]["i"])
        return cur if pre == "_root_" else pre+"."+cur
    def source_expr(i,depth=5):
        node=exprs[i]
        if depth <= 0: return {"id":i,"next":"..."}
        if "bvar" in node: return {"id":i,"bvar":node["bvar"]}
        if "const" in node:
            c=node["const"]
            return {"id":i,"const":name(c["name"]),"name_id":c["name"],"universe_ids":c["us"]}
        if "app" in node:
            a=node["app"]
            return {"id":i,"app":[source_expr(a["fn"],depth-1),source_expr(a["arg"],depth-1)]}
        for k in ("forallE","lam"):
            if k in node:
                b=node[k]
                return {"id":i,"binder_kind":k,"binder":name(b["name"]),
                        "type":source_expr(b["type"],depth-1),
                        "body":source_expr(b["body"],depth-1)}
        return {"id":i,"tag":sorted(k for k in node if k!="ie"),"node":node}
    theorem=next(r["thm"] for r in rows if "thm" in r and r["thm"]["value"]==561)
    body=theorem["value"]
    binders=[]
    while "lam" in exprs[body]:
        b=exprs[body]["lam"]
        binders.append({"source_position":len(binders),
                        "binder_name":name(b["name"]),
                        "binder_type_expr":b["type"],"binder_expr":body})
        body=b["body"]
    assert len(binders)==11 and body==550
    assert exprs[550]["app"]=={"fn":549,"arg":12}
    assert exprs[549]["app"]=={"fn":539,"arg":548}
    report={"source_sha256":digest,"format_version":rows[0]["meta"]["format"]["version"],
        "original_lean":rows[0]["meta"]["lean"],
        "case_theorem":name(theorem["name"]),
        "name_id_48":name(48),"source_telescope":binders,
        "source_nodes":{str(i):source_expr(i) for i in (11,12,94,302,376,441,442,534,539,548,549,550)},
        "method":"syntax-only source classification, not a proof of defeq or soundness"}
    pathlib.Path(destination).write_text(json.dumps(report,indent=2,ensure_ascii=False)+"\n")
    print("NUCLEUS_QUOTIENT_SOURCE_SCOPE="+json.dumps(report,ensure_ascii=False))
    return report

def patch(source):
    path=pathlib.Path(source)
    old=path.read_text()
    anchor='                let l=format!("{:?}",left.head);'
    assert old.count(anchor)==1, "PROBE_ANCHOR_DRIFT"
    addition=r'''                // Diagnostic-only captured-context witness for the exact
                // native Quotient.lift₂._proof_2 Γ11 domain separator.
                // No equality rule, mode switch or fuel budget is changed.
                #[cfg(feature = "diagnostics")]
                if std::env::var_os("NUCLEUS_TRACE_QUOTIENT_SCOPE").is_some()
                    && depth==12 && context.len()==12
                    && matches!(&left.head,
                        NeutralHead::Const { name, .. } if name.0==48)
                    && matches!(&right.head,
                        NeutralHead::Free(free) if free.0==5)
                {
                    use std::sync::atomic::{AtomicUsize,Ordering};
                    static SCOPE_COUNT:AtomicUsize=AtomicUsize::new(0);
                    if SCOPE_COUNT.fetch_add(1,Ordering::Relaxed)<4 {
                        let captured_free5=context.get(5);
                        let captured_fresh11=context.get(11);
                        let left_proposition=left.spine.last().map(|term| {
                            checker.is_proposition_in_context(
                                term.expr,context,&term.env,budget.min(2048))
                        });
                        let right_proposition=right.spine.last().map(|term| {
                            checker.is_proposition_in_context(
                                term.expr,context,&term.env,budget.min(2048))
                        });
                        let exposed_free5=match captured_free5 {
                            Some(TypeValue::Term(c)) =>
                                Some(checker.machine().expose(
                                    c.clone(),Transparency::Reducible,budget.min(1024))),
                            _=>None,
                        };
                        eprintln!(
                            "NUCLEUS_QUOTIENT_SCOPE:depth={depth}:Gamma={}:left_const={:?}:left_levels={:?}:left_arity={}:right_free={:?}:right_arity={}:free5_type={captured_free5:?}:fresh11_type={captured_fresh11:?}:free5_reducible={exposed_free5:?}:left_last_is_proof={left_proposition:?}:right_last_is_proof={right_proposition:?}",
                            context.len(),left.head,
                            match &left.head { NeutralHead::Const { levels,.. } => Some(levels), _=>None },
                            left.spine.len(),right.head,right.spine.len(),
                        );
                    }
                }
'''
    path.write_text(old.replace(anchor,addition+anchor))
    print("NUCLEUS_QUOTIENT_SCOPE_PATCH=diagnostic-only:no-semantics-change")

if __name__=="__main__":
    if len(sys.argv)==4 and sys.argv[1]=="inspect":
        inspect(sys.argv[2],sys.argv[3])
    elif len(sys.argv)==3 and sys.argv[1]=="patch":
        patch(sys.argv[2])
    else:
        raise SystemExit("usage: script inspect INPUT OUTPUT | script patch convert.rs")
