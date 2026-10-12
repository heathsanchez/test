#!/usr/bin/env python3
"""Source-exact, feature-flagged guarded fallback for independently typed LAMBDA field arguments.

Apply *after* contextual and strict checked-field-application scripts. Preserve
type/domain/source checks and their non-reentrancy guard. No benchmark names.
"""
from pathlib import Path
import sys
p=Path(sys.argv[1] if len(sys.argv)>1 else "metatron-kernel")/"src/typecheck.rs"
s=p.read_text()
old="""            if !equal(&larg_ty,&ldomain)
                || !equal(&rarg_ty,&rdomain)
                || !equal(&TypeValue::Term(larg.clone()),
                          &TypeValue::Term(rarg.clone()))
            {
                return false;
            }
"""
new="""            // First admit both arguments only after checking their exact
            // dependent Pi domains and individually inferred source types.
            if !equal(&larg_ty,&ldomain)
                || !equal(&rarg_ty,&rdomain)
            {
                return false;
            }
            if !equal(&TypeValue::Term(larg.clone()),
                      &TypeValue::Term(rarg.clone()))
            {
                // These two source terms must BOTH be syntactic lambdas.
                // The guarded native converter is a full independent
                // obligation, never an unconditional lambda/eta rewrite.
                if std::env::var_os(
                    "NUCLEUS_EXPERIMENTAL_GUARDED_LAMBDA_ARGUMENT",
                ).is_none()
                    || !matches!(self.expressions.get(larg.expr),Some(Expr::Lam{ .. }))
                    || !matches!(self.expressions.get(rarg.expr),Some(Expr::Lam{ .. }))
                    || !crate::convert::convert_with_policy_in_context(
                        self,
                        &TypeValue::Term(larg.clone()),
                        &TypeValue::Term(rarg.clone()),
                        8192,
                        crate::convert::DeltaPolicy::GuardedSemanticFallback,
                        context.len(),context,
                    ).is_proven()
                {
                    return false;
                }
                #[cfg(feature="diagnostics")]
                if std::env::var_os("NUCLEUS_TRACE_GUARDED_LAMBDA_ARGUMENT").is_some(){
                    use std::sync::atomic::{AtomicUsize,Ordering};
                    static COUNT:AtomicUsize=AtomicUsize::new(0);
                    if COUNT.fetch_add(1,Ordering::Relaxed)<128{
                        eprintln!(
                            "NUCLEUS_GUARDED_LAMBDA_ARG_PROVEN:context={}:l={:?}:r={:?}:lexical_typed=true",
                            context.len(),larg.expr,rarg.expr
                        );
                    }
                }
            }
"""
if s.count(old)!=1:
    raise SystemExit("SOURCE_FIELD_ARGUMENT_ANCHOR_NOT_UNIQUE:"+str(s.count(old)))
p.write_text(s.replace(old,new,1))
print("EXACT_SOURCE_GUARDED_LAMBDA_ARGUMENT_PATCHED",flush=True)
