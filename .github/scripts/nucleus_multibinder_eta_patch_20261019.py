#!/usr/bin/env python3
"""Frozen optional multi-binder eta contraction, without new equality axioms.

Recognizes only a fully η-long literal source:
  fun x_1 ... x_n => f x_1 ... x_n
with all binders checked syntactically and zero uses of any newly bound variable
inside f. Leaves all unrelated lambda/neutral comparisons untouched.
"""
from pathlib import Path
import sys
p=Path(sys.argv[1] if len(sys.argv)>1 else "metatron-kernel/src/convert.rs")
s=p.read_text()
anchor="fn eta_contract(checker: &TypeChecker<'_>, closure: &Closure, depth: usize) -> Option<Closure> {\n"
assert s.count(anchor)==1
helper=r'''// Source-certified multi-binder η for the literal curried telescope.
// The final application must supply exactly the introduced binders in
// source order and its original head must be independent of all of them.
// All environments and universe substitutions come from the *original*
// closure; new locals are placeholders for bindings that the head does not
// use. Not a blanket lambda-versus-neutral equality.
fn eta_contract_telescope(
    checker: &TypeChecker<'_>,
    raw: &Closure,
    depth: usize,
) -> Option<Closure> {
    if std::env::var_os("NUCLEUS_EXPERIMENTAL_MULTIBINDER_ETA").is_none() {
        return None;
    }
    let source=resolve_local_closure(checker,raw)?;
    let mut body=source.expr;
    let mut n=0usize;
    while let Some(Expr::Lam {body:next,..})=checker.expression(body) {
        if n==4 {return None}
        n+=1;
        body=*next;
    }
    if n<2 {return None}
    let mut head=body;
    for index in 0..n {
        let Some(Expr::App {fun,arg})=checker.expression(head) else {return None};
        if !matches!(checker.expression(*arg),Some(Expr::BVar(j)) if *j==index as u64) {
            return None
        }
        head=*fun;
    }
    // The head may itself contain binders: expression_uses_bvar performs
    // de Bruijn-aware, conservative support checking across all constructors.
    if (0..n).any(|index|expression_uses_bvar(checker,head,index as u64,2048)) {
        return None
    }
    let mut captured=source.env.clone();
    for index in 0..n {
        captured=captured.extend_free(fresh_local(depth.checked_add(index)?)?);
    }
    let contracted=source.sibling(head,captured);
    #[cfg(feature="diagnostics")]
    if std::env::var_os("NUCLEUS_TRACE_MULTIBINDER_ETA").is_some() {
        eprintln!(
            "NUCLEUS_MULTIBINDER_ETA:original={:?}:body={body:?}:head={head:?}:arity={n}:depth={depth}:candidate={contracted:?}",
            source,
        );
    }
    Some(contracted)
}

'''
s=s.replace(anchor,helper+anchor)
needle="    let closure = resolve_local_closure(checker, closure)?;\n"
# present elsewhere? need restrict replace by function anchor
offset=s.index(anchor)+len(anchor)
assert s[offset:offset+len(needle)]==needle,repr(s[offset:offset+len(needle)])
s=s[:offset]+'''    if let Some(contracted)=eta_contract_telescope(checker,closure,depth) {
        return Some(contracted);
    }
'''+s[offset:]
p.write_text(s)
print("source-checked, strict two-to-four-binder eta experiment installed")
