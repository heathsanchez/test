#!/usr/bin/env python3
"""Source-typed Prop proof irrelevance at EXACT missing field-app argument edge.

Requires the existing verified conditional proof-pair rule on *both* source
arguments in the *same lexical context*. Never erase data arguments, never
compare constructor outputs to infer a major, never accept a hash collision.
Only installed under feature flag; all unresolved premises stay UNKNOWN.
"""
from pathlib import Path
import sys
root=Path(sys.argv[1] if len(sys.argv)>1 else "metatron-kernel")
p=root/"src/typecheck.rs"
s=p.read_text()
old="""            if !equal(&larg_ty,&ldomain)
                || !equal(&rarg_ty,&rdomain)
                || !equal(&TypeValue::Term(larg.clone()),
                          &TypeValue::Term(rarg.clone()))
            {
                return false;
            }
"""
new="""            // All domain/type checks are mandatory. Proof irrelevance is a
            // *fallback* only at the remaining actual-argument comparison,
            // and is justified solely when BOTH exact source terms are
            // independently typed proofs of the SAME checked proposition.
            if !equal(&larg_ty,&ldomain)
                || !equal(&rarg_ty,&rdomain)
            {
                return false;
            }
            if !equal(&TypeValue::Term(larg.clone()),
                      &TypeValue::Term(rarg.clone()))
            {
                if std::env::var_os(
                    "NUCLEUS_EXPERIMENTAL_FIELD_ARG_PROOF_IRREL",
                ).is_none()
                    || !self.checked_proof_pair_in_bounded_context(
                        larg,rarg,context,budget.min(8192),
                    )
                {
                    return false;
                }
                #[cfg(feature="diagnostics")]
                if std::env::var_os(
                    "NUCLEUS_TRACE_FIELD_ARG_PROOF_IRREL",
                ).is_some() {
                    use std::sync::atomic::{AtomicUsize,Ordering};
                    static COUNT:AtomicUsize=AtomicUsize::new(0);
                    if COUNT.fetch_add(1,Ordering::Relaxed)<96 {
                        eprintln!(
                            "NUCLEUS_FIELD_ARG_PROOF_IRREL:context={}:fuel={}:source_arguments_checked=true",
                            context.len(),budget,
                        );
                    }
                }
            }
"""
assert s.count(old)==1,s.count(old)
p.write_text(s.replace(old,new,1))
print("SOURCE_CERTIFIED_ARGUMENT_PROOF_IRRELEVANCE_V1")
