#!/usr/bin/env python3
"""Opt-in, fail-closed source-checked Eq-over-Prop congruence A/B.

Never admits conversion from a common Eq head alone. Every actual neutral
argument of both independently formed equality types must convert under
the *original* context; no identities inferred from name or numeric FreeId.
"""
from pathlib import Path
import sys

source = Path(sys.argv[1] if len(sys.argv) > 1 else "metatron-kernel/src/typecheck.rs")
body = source.read_text()
anchor = "    fn undecided_propositional_equality_proof(\n"
assert body.count(anchor) == 1
helper = r'''
    /// A narrow structural congruence candidate, not a new equality axiom.
    /// Both captured types have already been inferred/formed by the caller.
    /// Check ALL Eq arguments under the original Gamma; an omitted, refuted
    /// or exhausted premise cannot license acceptance. Diagnostic A/B only.
    fn experimental_checked_eq_prop_congruence(
        &self,
        actual: &TypeValue,
        expected: &TypeValue,
        context: &[TypeValue],
        budget: usize,
    ) -> bool {
        if budget < 128 || context.len() > 64 {
            return false;
        }
        let expose_eq = |ty: &TypeValue| -> Option<Neutral> {
            let TypeValue::Term(term) = ty else { return None };
            let observed = self.machine().expose_for_conversion(
                term.clone(), Transparency::Reducible, budget.min(2048),
            );
            let Value::Neutral(eq) = observed.proven_value()? else {return None};
            if eq.spine.len()!=3 {return None}
            let carrier = self.machine().expose_for_conversion(
                eq.spine[0].clone(),Transparency::Reducible,budget.min(2048),
            );
            if !matches!(carrier.proven_value(),Some(Value::Sort(LevelTerm::Zero))) {
                return None;
            }
            Some(eq.clone())
        };
        let (Some(left),Some(right))=(expose_eq(actual),expose_eq(expected)) else {
            return false
        };
        let (
            NeutralHead::Const {name:ln,levels:ll},
            NeutralHead::Const {name:rn,levels:rl},
        )=(&left.head,&right.head) else {return false};
        if ln!=rn || ll.len()!=rl.len() ||
            !ll.iter().zip(rl.iter()).all(|(l,r)|{
                crate::level::level_equal(l.clone(),r.clone(),budget.min(1024)).is_proven()
            }) {return false}
        for (index,(lhs,rhs)) in left.spine.iter().zip(right.spine.iter()).enumerate() {
            let verdict=crate::convert::convert_with_policy_in_context(
                self,
                &TypeValue::Term(lhs.clone()),
                &TypeValue::Term(rhs.clone()),
                budget.min(2048),
                crate::convert::DeltaPolicy::GuardedSemanticFallback,
                context.len(),context,
            );
            #[cfg(feature="diagnostics")]
            if std::env::var_os("NUCLEUS_TRACE_EQPROP_CERTIFIED_CONGRUENCE").is_some() {
                eprintln!(
                    "NUCLEUS_EQPROP_CERTIFIED_CONGRUENCE:argument={index}:context_len={}:result={verdict:?}:left={lhs:?}:right={rhs:?}",
                    context.len(),
                );
            }
            #[cfg(feature="diagnostics")]
            if index==1 && !verdict.is_proven()
                && std::env::var_os("NUCLEUS_TRACE_EQPROP_ENDPOINT_PROVENANCE").is_some()
            {
                use std::sync::atomic::{AtomicUsize,Ordering};
                static TRACES:AtomicUsize=AtomicUsize::new(0);
                if TRACES.fetch_add(1,Ordering::Relaxed)<6 {
                    let mut left_fuel=2048;
                    let left_type=self.infer_exact_closure_in_context(
                        lhs,context,&mut left_fuel,0
                    );
                    let mut right_fuel=2048;
                    let right_type=self.infer_exact_closure_in_context(
                        rhs,context,&mut right_fuel,0
                    );
                    let mut identity_fuel=2048;
                    let exact_identity=self.exact_source_capture_identity(
                        lhs,rhs,&mut identity_fuel,
                    );
                    let left_whnf=self.machine().expose_for_conversion(
                        lhs.clone(),Transparency::Reducible,budget.min(2048),
                    );
                    let right_whnf=self.machine().expose_for_conversion(
                        rhs.clone(),Transparency::Reducible,budget.min(2048),
                    );
                    eprintln!(
                        "NUCLEUS_EQPROP_ENDPOINT_PROVENANCE:context_len={}:left_type={left_type:?}:right_type={right_type:?}:source_identity={exact_identity}:left_whnf={left_whnf:?}:right_whnf={right_whnf:?}",
                        context.len(),
                    );
                }
            }
            let mut witnessed=verdict.is_proven();
            // Separate checked, compositional route for identical rigid heads.
            // Every child conversion must itself be proven in the ORIGINAL
            // lexical context. Sharing a head or a numeric FreeId is never
            // enough. This cannot downgrade a definitive negative.
            if !witnessed && index>0 && budget>=256 {
                let lex=self.machine().expose_for_conversion(
                    lhs.clone(),Transparency::Reducible,budget.min(2048),
                );
                let rex=self.machine().expose_for_conversion(
                    rhs.clone(),Transparency::Reducible,budget.min(2048),
                );
                if let (Some(Value::Neutral(ln)),Some(Value::Neutral(rn)))=
                    (lex.proven_value(),rex.proven_value())
                {
                    if let (
                        NeutralHead::Const{name:lname,levels:ll},
                        NeutralHead::Const{name:rname,levels:rl},
                    )=(&ln.head,&rn.head)
                    {
                        if lname==rname && ll.len()==rl.len()
                            && ln.spine.len()==rn.spine.len()
                            && (1..=6).contains(&ln.spine.len())
                            && ll.iter().zip(rl.iter()).all(|(a,b)|
                                crate::level::level_equal(a.clone(),b.clone(),budget.min(1024)).is_proven()
                            )
                        {
                            witnessed=true;
                            for (child,(a,b)) in ln.spine.iter().zip(rn.spine.iter()).enumerate() {
                                let sub=crate::convert::convert_with_policy_in_context(
                                    self,&TypeValue::Term(a.clone()),&TypeValue::Term(b.clone()),
                                    budget.min(2048),
                                    crate::convert::DeltaPolicy::GuardedSemanticFallback,
                                    context.len(),context,
                                );
                                #[cfg(feature="diagnostics")]
                                if std::env::var_os("NUCLEUS_TRACE_EQPROP_ENDPOINT_PROVENANCE").is_some() {
                                    eprintln!(
                                        "NUCLEUS_EQPROP_NESTED_CONGRUENCE:outer_argument={index}:child={child}:head={lname:?}:result={sub:?}:lhs={a:?}:rhs={b:?}",
                                    );
                                }
                                if !sub.is_proven() {
                                    witnessed=false;
                                    break;
                                }
                            }
                        }
                    }
                }
            }
            if !witnessed {return false}
        }
        true
    }

'''
body = body.replace(anchor, helper + anchor)
target='''                    Judgment::unknown("source-Eq-Prop-dependent-conversion-unresolved")
'''
assert body.count(target) == 1
replacement='''                    if std::env::var_os("NUCLEUS_EXPERIMENTAL_EQPROP_CERTIFIED_CONGRUENCE").is_some()
                        && self.experimental_checked_eq_prop_congruence(
                            &value, expected, context, (*remaining).min(4096)
                        )
                    {
                        Judgment::proven((), "source-certified-Eq-Prop-type-congruence")
                    } else {
                        Judgment::unknown("source-Eq-Prop-dependent-conversion-unresolved")
                    }
'''
body = body.replace(target,replacement)
source.write_text(body)
print("Nucleus opt-in EqProp certified congruence applied")
