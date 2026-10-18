#!/usr/bin/env python3
"""Diagnostic-only source comparison of original Quotient.ind case proof domain.

Isolate original Expr549 = (Expr539 Expr548) under Γ11.
Do NOT alter the independent checker verdict or productive work budget.
"""
from pathlib import Path
import sys
p=Path(sys.argv[1] if len(sys.argv)>1 else "metatron-kernel/src/typecheck.rs")
s=p.read_text()
anchor='''                if !domain_check.is_proven() {
                    #[cfg(feature = "diagnostics")]
                    self.record_capture_source_failure(term, context, *remaining, depth, &format!("argument-domain-relation:{domain_check:?}"));
'''
assert s.count(anchor)==1
report=r'''                #[cfg(feature="diagnostics")]
                if std::env::var_os("NUCLEUS_TRACE_QUOTIENT_MINOR_DOMAIN").is_some()
                    && term.expr.0==549 && context.len()==11 && depth==0
                {
                    let transparency_expose=|ty:&TypeValue, full:bool| -> Option<String>{
                        let TypeValue::Term(c)=ty else{return None};
                        let mode=if full {Transparency::Full} else {Transparency::Reducible};
                        let out=self.machine().expose_for_conversion(
                            c.clone(),mode,8192,
                        );
                        Some(format!("{out:?}"))
                    };
                    let preferred=crate::convert::convert_with_policy_in_context(
                        self,&argument_ty,&domain,8192,
                        crate::convert::DeltaPolicy::PreferredOnly,context.len(),context,
                    );
                    let guarded512=crate::convert::convert_with_policy_in_context(
                        self,&argument_ty,&domain,512,
                        crate::convert::DeltaPolicy::GuardedSemanticFallback,
                        context.len(),context,
                    );
                    let guarded8192=crate::convert::convert_with_policy_in_context(
                        self,&argument_ty,&domain,8192,
                        crate::convert::DeltaPolicy::GuardedSemanticFallback,
                        context.len(),context,
                    );
                    let typed_source=if let (TypeValue::Term(lhs),TypeValue::Term(rhs))=
                        (&argument_ty,&domain)
                    {
                        Some(self.checked_source_conversion(lhs,rhs,context,8192))
                    } else {None};
                    eprintln!(
                        "NUCLEUS_QUOTIENT_MINOR_DOMAIN:expr={:?}:Gamma_depth={}:Gamma_frame={}:original_remaining={}:actual_case={argument:?}:case_type={argument_ty:?}:required_domain={domain:?}:primary={domain_check:?}:preferred8192={preferred:?}:guarded512={guarded512:?}:guarded8192={guarded8192:?}:checked_source={typed_source:?}:actual_reducible={:?}:expected_reducible={:?}:actual_full={:?}:expected_full={:?}",
                        term.expr,context.len(),term.env.id(),*remaining,
                        transparency_expose(&argument_ty,false),
                        transparency_expose(&domain,false),
                        transparency_expose(&argument_ty,true),
                        transparency_expose(&domain,true),
                    );
                }
'''
s=s.replace(anchor,report+anchor)
p.write_text(s)
print("source-only Quotient.ind minor domain diagnostic installed; original check path unchanged")
