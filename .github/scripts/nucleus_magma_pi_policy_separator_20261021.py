#!/usr/bin/env python3
"""Prospective Nucleus source-Pi separator, DIAGNOSTIC ONLY.

A captured neutral's exact argument type is independently inferred and its
expected Π-domain belongs to the same original source telescope. The existing
diagnostic conversion tries PreferredOnly and sometimes reports a rigid type
mismatch. Before changing ANY semantics, independently query the already
implemented guarded delta/typing policy on exactly that source pair.

This patch is inserted only in a cfg(feature="diagnostics")-only function;
it changes no production conversion/checking result and cannot authorize ACCEPT.
"""
from pathlib import Path
import sys
if len(sys.argv)!=2: raise SystemExit("usage: SCRIPT TYPECHECK_RS")
p=Path(sys.argv[1])
s=p.read_text()
original='''            if !relation.is_proven() {
                return format!(
                    "first-undischarged-domain:argument={position}:actual={actual_type:?}:required={domain:?}:relation={relation:?}:context_depth={}",
                    context.len(),
                );
            }'''
replacement=r'''            if !relation.is_proven() {
                // EXPERIMENT ONLY. Merely making two Π-shaped objects look
                // similar is not an equality warrant. Do not replace the
                // original PreferredOnly judgment with any trial outcome.
                #[cfg(feature = "diagnostics")]
                if std::env::var_os("NUCLEUS_TRACE_PI_POLICY_SEPARATOR").is_some()
                    && matches!(&actual_type, TypeValue::Pi { .. })
                    && let TypeValue::Term(source_expected) = &domain
                {
                    use std::sync::atomic::{AtomicUsize, Ordering};
                    static PI_DIAGNOSTIC: AtomicUsize = AtomicUsize::new(0);
                    if PI_DIAGNOSTIC.fetch_add(1, Ordering::Relaxed) < 8 {
                        let guarded256 = crate::convert::convert_with_policy_in_context(
                            &probe, &actual_type, &domain, 256,
                            crate::convert::DeltaPolicy::GuardedSemanticFallback,
                            context.len(), context,
                        );
                        let guarded2048 = crate::convert::convert_with_policy_in_context(
                            &probe, &actual_type, &domain, 2048,
                            crate::convert::DeltaPolicy::GuardedSemanticFallback,
                            context.len(), context,
                        );
                        let same_preferred2048 = crate::convert::convert_with_policy_in_context(
                            &probe, &actual_type, &domain, 2048,
                            crate::convert::DeltaPolicy::PreferredOnly,
                            context.len(), context,
                        );
                        let reducible = probe.machine().expose(
                            source_expected.clone(),
                            Transparency::Reducible, 2048,
                        );
                        let full = probe.machine().expose(
                            source_expected.clone(),
                            Transparency::Full, 2048,
                        );
                        let mut source_fuel = 2048usize;
                        let source_formation = probe.infer_exact_closure_in_context(
                            source_expected, context, &mut source_fuel, 0
                        );
                        eprintln!(
                            "NUCLEUS_PI_POLICY_SEPARATOR:arg={position}:depth={}:free_binder={:?}:source_expected_expr={:?}:source_env={}:source_levels={:?}:original={relation:?}:preferred2048={same_preferred2048:?}:guarded256={guarded256:?}:guarded2048={guarded2048:?}:source_formation={}:reducible={}:full={}",
                            context.len(),
                            match &actual_type {
                                TypeValue::Pi { binder, .. } => Some(*binder),
                                _ => None,
                            },
                            source_expected.expr,
                            source_expected.env.id(),
                            source_expected.levels,
                            format!("{source_formation:?}").chars().take(950).collect::<String>(),
                            format!("{reducible:?}").chars().take(1100).collect::<String>(),
                            format!("{full:?}").chars().take(1100).collect::<String>(),
                        );
                    }
                }
                return format!(
                    "first-undischarged-domain:argument={position}:actual={actual_type:?}:required={domain:?}:relation={relation:?}:context_depth={}",
                    context.len(),
                );
            }'''
assert s.count(original)==1,("SOURCE_DRIFT",s.count(original))
assert s.count("fn diagnostic_neutral_source_telescope_inner(")==1
s=s.replace(original,replacement)
p.write_text(s)
print("NUCLEUS_PI_POLICY_SEPARATOR=DIAGNOSTIC_ONLY_SAME_SOURCE_CONTEXT",flush=True)
