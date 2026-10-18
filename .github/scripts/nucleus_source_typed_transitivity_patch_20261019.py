#!/usr/bin/env python3
"""Opt-in independent source-typed application re-inference.

Never uses a new axiom. Requires BOTH (1) ordinary and source-inferred types
convert, and (2) source-inferred and expected types convert. Only then can
transitivity license an ACCEPT; otherwise preserves the prior verdict.
"""
from pathlib import Path
import sys
p=Path(sys.argv[1] if len(sys.argv)>1 else "metatron-kernel/src/typecheck.rs")
s=p.read_text()
anchor="    fn undecided_propositional_equality_proof(\n"
assert s.count(anchor)==1
guard=r'''
thread_local! {
    static SOURCE_TYPE_TRANSITIVITY_ACTIVE: std::cell::Cell<bool> =
        const { std::cell::Cell::new(false) };
}
struct SourceTypeTransitivityScope;
impl Drop for SourceTypeTransitivityScope {
    fn drop(&mut self) {
        SOURCE_TYPE_TRANSITIVITY_ACTIVE.with(|state| state.set(false));
    }
}

'''
# Top-level adjacent to existing owned source declarations.
root="pub struct TypeChecker<'a> {\n"
assert s.count(root)==1
s=s.replace(root,guard+root)
marker=r'''                // Only a witnessed source proof of Eq between propositions
'''
assert s.count(marker)==1
alternate=r'''                // Source-authorized transitive replay of an original
                // proposition equality proof. A separate typed-inference
                // derivation cannot replace the normal derivation unless BOTH
                // conversions have already been proved in the original Gamma.
                // A failed/undecided premise leaves the old verdict unchanged.
                let replay = if std::env::var_os(
                    "NUCLEUS_EXPERIMENTAL_SOURCE_TYPED_TRANSITIVITY",
                ).is_some()
                    && !conversion.is_proven()
                    && self.undecided_propositional_equality_proof(
                        expression, &value, expected, (*remaining).min(4096)
                    )
                    && SOURCE_TYPE_TRANSITIVITY_ACTIVE.with(|state|{
                        if state.get() {false} else {state.set(true);true}
                    })
                {
                    let _scope=SourceTypeTransitivityScope;
                    let allowance=(*remaining).min(4096);
                    let mut source_fuel=allowance;
                    let exact=self.infer_exact_closure_in_context(
                        &self.closure(expression,frame.clone()),
                        context,&mut source_fuel,0,
                    );
                    let transport=exact.as_ref().map(|alt|{
                        let ordinary_to_exact=crate::convert::convert_with_policy_in_context(
                            self,&value,alt,allowance.min(2048),
                            crate::convert::DeltaPolicy::GuardedSemanticFallback,
                            context.len(),context,
                        );
                        let exact_to_expected=crate::convert::convert_with_policy_in_context(
                            self,alt,expected,allowance.min(2048),
                            crate::convert::DeltaPolicy::GuardedSemanticFallback,
                            context.len(),context,
                        );
                        (ordinary_to_exact,exact_to_expected)
                    });
                    #[cfg(feature="diagnostics")]
                    if std::env::var_os("NUCLEUS_TRACE_SOURCE_TYPED_TRANSITIVITY").is_some() {
                        eprintln!(
                            "NUCLEUS_SOURCE_TYPED_TRANSITIVITY:expr={expression:?}:context_len={}:frame={}:normal_type={value:?}:exact_type={exact:?}:relations={transport:?}:allowance={allowance}:source_spent={}",
                            context.len(),frame.id(),allowance-source_fuel,
                        );
                    }
                    if transport.as_ref().is_some_and(|(a,b)|a.is_proven()&&b.is_proven()) {
                        *remaining=remaining.saturating_sub(allowance-source_fuel);
                        Some(Judgment::proven((),"exact-source-typed-transitivity"))
                    } else {None}
                } else {None};
                let conversion = replay.unwrap_or(conversion);
'''
s=s.replace(marker,alternate+marker)
p.write_text(s)
print("source-owned type transitivity patch installed (experiment only)")
