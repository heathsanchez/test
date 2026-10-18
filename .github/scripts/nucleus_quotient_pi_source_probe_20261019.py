#!/usr/bin/env python3
"""Diagnostic-only source-owned Pi/codomain witness at immutable Expr550.

The independent checker verdict is unchanged. Every reported positive premise
must come from the real checked source Gamma, captured closure and universe map.
No inferred equality, name special case, or production fuel change is added.
"""
from pathlib import Path
import sys
p=Path(sys.argv[1] if len(sys.argv)>1 else "metatron-kernel/src/typecheck.rs")
s=p.read_text()
old='''                    return Judgment::unknown("application-function-type");
'''
assert s.count(old)==1
replacement=r'''                    #[cfg(feature="diagnostics")]
                    if std::env::var_os("NUCLEUS_TRACE_QUOTIENT_ORIGINAL_PI").is_some()
                        && expression.0==550 && fun.0==549 && arg.0==12
                        && context.len()==11
                    {
                        // Bounded witness-only probe; do not charge or alter
                        // the original failed judgment's remaining fuel.
                        let probe_cap=16384usize;
                        let mut source_fuel=probe_cap;
                        let function=self.closure(*fun,frame.clone());
                        let argument=self.closure(*arg,frame.clone());
                        let complete=self.closure(expression,frame.clone());
                        let _scope=CaptureSourceFailureScope::enter();
                        let function_type=self.infer_exact_closure_in_context(
                            &function,context,&mut source_fuel,0,
                        );
                        let first_source_obstruction=CaptureSourceFailureScope::first();
                        let argument_type=self.infer_exact_closure_in_context(
                            &argument,context,&mut source_fuel,0,
                        );
                        let source_function_pi=function_type.clone().and_then(|ty|{
                            self.pi_view(
                                Judgment::proven(ty,"original-source-function-inference"),
                                source_fuel.min(4096),
                            )
                        });
                        let mut domain=None;
                        let mut domain_verdict=None;
                        let mut instantiated_codomain=None;
                        let mut independently_inferred_app=None;
                        let mut codomain_verdict=None;
                        if let Some((expected_domain,body))=source_function_pi {
                            domain=Some(expected_domain.clone());
                            if let Some(actual_arg_type)=argument_type.clone() {
                                let relation=crate::convert::convert_with_policy_in_context(
                                    self,&actual_arg_type,&expected_domain,
                                    source_fuel.min(4096),
                                    crate::convert::DeltaPolicy::GuardedSemanticFallback,
                                    context.len(),context,
                                );
                                let permitted=relation.is_proven();
                                domain_verdict=Some(relation);
                                if permitted {
                                    let codomain=match body {
                                        PiBody::Closure(captured_body)=>Some(TypeValue::Term(
                                            Closure::with_levels(
                                                captured_body.expr,
                                                self.checked_captured_pi_frame(
                                                    &captured_body,&argument,
                                                    expected_domain.clone(),context,
                                                ),
                                                captured_body.levels,
                                            ),
                                        )),
                                        PiBody::Fixed(binder,ty)=>
                                            self.instantiate_fixed_pi_body(
                                                &ty,binder,&argument,&mut source_fuel,
                                            ),
                                    };
                                    instantiated_codomain=codomain.clone();
                                    independently_inferred_app=self.infer_exact_closure_in_context(
                                        &complete,context,&mut source_fuel,0,
                                    );
                                    if let (Some(expected),Some(actual))=
                                        (codomain.as_ref(),independently_inferred_app.as_ref())
                                    {
                                        codomain_verdict=Some(
                                            crate::convert::convert_with_policy_in_context(
                                                self,actual,expected,source_fuel.min(4096),
                                                crate::convert::DeltaPolicy::GuardedSemanticFallback,
                                                context.len(),context,
                                            )
                                        );
                                    }
                                }
                            }
                        }
                        eprintln!(
                            "NUCLEUS_QUOTIENT_ORIGINAL_PI:expr={expression:?}:Gamma_depth={}:frame={}:remaining_original={}:function={function:?}:argument={argument:?}:source_function_type={function_type:?}:first_source_obstruction={first_source_obstruction:?}:source_argument_type={argument_type:?}:Pi_domain={domain:?}:argument_domain_conversion={domain_verdict:?}:source_substituted_codomain={instantiated_codomain:?}:independent_application_type={independently_inferred_app:?}:codomain_conversion={codomain_verdict:?}:probe_consumed={}",
                            context.len(),frame.id(),*remaining,probe_cap-source_fuel,
                        );
                    }
                    return Judgment::unknown("application-function-type");
'''
s=s.replace(old,replacement)
p.write_text(s)
print("Nucleus original Γ11 Pi/codomain diagnosis installed without semantic changes")
