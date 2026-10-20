#!/usr/bin/env python3
"""Soundness-gated prospective lambda/theorem proof-irrelevance candidate.

No raw constant-versus-lambda conversion. A positive result requires TWO
independent exact source Γ typings, both proposition formations in Sort 0,
and definitional equality of their dependent proposition types.
"""
from pathlib import Path
import sys
path=Path(sys.argv[1] if len(sys.argv)>1 else 'metatron-kernel/src/convert.rs')
s=path.read_text()
anchor='''                match compare_values(
                    checker,
                    cheap_left,
                    cheap_right,
                    remaining,
                    depth,
                    context,
                    &mut work,
                    &mut proof_function_frees,
                ) {'''
assert s.count(anchor)==1,'TERM_VALUE_COMPARE_ANCHOR_DRIFT'
probe=r'''                // A theorem proof may be represented by a neutral constant
                // while a second proof of the SAME proposition is a lambda.
                // Never equate their head shapes. Require independently formed
                // proposition types in the identical captured source Γ.
                if std::env::var_os("NUCLEUS_EXPERIMENTAL_PAIRED_PROOF_LAMBDA").is_some()
                    && depth == local_context.len()
                    && (4..=24).contains(&depth)
                    && remaining >= 1024
                    && (matches!((cheap_left,cheap_right),
                        (Value::Neutral(Neutral { head: NeutralHead::Const{..}, spine }),Value::Lam {..})
                            if !spine.is_empty() && spine.len()<=12)
                        || matches!((cheap_left,cheap_right),
                        (Value::Lam {..},Value::Neutral(Neutral { head: NeutralHead::Const{..},spine }))
                            if !spine.is_empty() && spine.len()<=12))
                {
                    let certified=checker.checked_proof_pair_in_bounded_context(
                        &left,&right,&local_context,remaining.min(8192),
                    );
                    #[cfg(feature="diagnostics")]
                    if std::env::var_os("NUCLEUS_TRACE_PAIRED_PROOF_LAMBDA").is_some() {
                        use std::sync::atomic::{AtomicUsize,Ordering};
                        static PAIRS:AtomicUsize=AtomicUsize::new(0);
                        if PAIRS.fetch_add(1,Ordering::Relaxed)<24 {
                            eprintln!(
                                "NUCLEUS_PAIRED_PROOF_LAMBDA:source_left={left:?}:source_right={right:?}:Gamma={depth}:certified={certified}",
                            );
                        }
                    }
                    if certified { continue; }
                }
'''
path.write_text(s.replace(anchor,probe+anchor))
print('NUCLEUS_PAIRED_PROOF_LAMBDA_CANDIDATE=exact source proof irrelevance only')
