#!/usr/bin/env python3
"""Opt-in candidate for source-owned Quot reduction on a beta/zeta-reduced major.

Only an exact, registered Quot.mk constructor with three source arguments
licenses the primitive quotient beta step. No name-specific theorem hack.
This is NOT a promoted rule until native source + adversaries qualify it.
"""
from pathlib import Path
import sys
p=Path(sys.argv[1] if len(sys.argv)>1 else 'metatron-kernel/src/machine.rs')
s=p.read_text()
anchor1='self.try_quot_reduction(*name, levels, &mut pending)'
assert s.count(anchor1)==1, 'QUOT_CALL_SITE_DRIFT'
s=s.replace(anchor1,
    'self.try_quot_reduction(*name, levels, &mut pending, transparency, budget)')
anchor2='''    fn try_quot_reduction(
        &self,
        name: NameId,
        levels: &[LevelId],
        pending: &mut Vec<Closure>,
    ) -> Option<Closure> {'''
assert s.count(anchor2)==1, 'QUOT_SIGNATURE_DRIFT'
s=s.replace(anchor2,'''    fn try_quot_reduction(
        &self,
        name: NameId,
        levels: &[LevelId],
        pending: &mut Vec<Closure>,
        transparency: Transparency,
        budget: usize,
    ) -> Option<Closure> {''')
anchor3='''        let (constructor, constructor_arguments) = self.constructor_application(target)?;
        if constructor != primitives.mk || constructor_arguments.len() != 3 {'''
assert s.count(anchor3)==1, 'QUOT_CONSTRUCTOR_PREMISE_DRIFT'
sub=r'''        let direct = self.constructor_application(target);
        #[cfg(feature="diagnostics")]
        if std::env::var_os("NUCLEUS_TRACE_QUOT_MAJOR").is_some() {
            use std::sync::atomic::{AtomicUsize,Ordering};
            static QUOT_DIRECT:AtomicUsize=AtomicUsize::new(0);
            if QUOT_DIRECT.fetch_add(1,Ordering::Relaxed)<20 {
                eprintln!(
                    "NUCLEUS_QUOT_MAJOR_DIRECT:target={:?}:direct={direct:?}:required={:?}:arity=3",
                    target.expr,primitives.mk,
                );
            }
        }
        let candidate = direct.filter(|(ctor,args)| *ctor == primitives.mk && args.len()==3).or_else(|| {
            // The original evaluator recognized only a syntactically direct
            // Quot.mk. Lean permits beta/zeta (and authorized delta) reductions
            // that expose the same primitive constructor. This fallback
            // *inspects*, never fabricates or guesses, the source major.
            if std::env::var_os("NUCLEUS_EXPERIMENTAL_QUOT_MAJOR").is_none()
                || budget < 16 || self.exposure_depth.get() >= 32
            {
                return None;
            }
            let exposed = self.expose_internal(
                target.clone(), Transparency::Full, budget.saturating_sub(1).min(256),
                false, false,
            );
            #[cfg(feature="diagnostics")]
            if std::env::var_os("NUCLEUS_TRACE_QUOT_MAJOR").is_some() {
                use std::sync::atomic::{AtomicUsize,Ordering};
                static QUOT_EXPOSED:AtomicUsize=AtomicUsize::new(0);
                if QUOT_EXPOSED.fetch_add(1,Ordering::Relaxed)<20 {
                    eprintln!(
                        "NUCLEUS_QUOT_MAJOR_EXPOSED:target={:?}:policy={transparency:?}:full_exposure={exposed:?}",
                        target.expr,
                    );
                }
            }
            let Value::Neutral(Neutral {
                head: NeutralHead::Const { name, .. }, spine,
            }) = exposed.proven_value()?.value.clone() else {
                return None;
            };
            #[cfg(feature="diagnostics")]
            if std::env::var_os("NUCLEUS_TRACE_QUOT_MAJOR").is_some() {
                eprintln!(
                    "NUCLEUS_QUOT_MAJOR:source_target={:?}:constructor={name:?}:arity={}:registered_constructor={:?}",
                    target.expr,spine.len(),primitives.mk,
                );
            }
            Some((name, spine))
        });
        let (constructor, constructor_arguments) = candidate?;
        if constructor != primitives.mk || constructor_arguments.len() != 3 {'''
s=s.replace(anchor3,sub)
p.write_text(s)
print('NUCLEUS_QUOT_MAJOR_CANDIDATE=opt-in exact registered constructor fallback')
