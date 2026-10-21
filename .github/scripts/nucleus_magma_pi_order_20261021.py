#!/usr/bin/env python3
"""Cold-vs-warm prospective dependent Pi proof acquisition; diagnostic ONLY.

Applied after nucleus_magma_pi_policy_separator_20261021.py. Instrument the
original captured-neutral source-telescope observer (cfg diagnostics), NOT
production conversion. Two exact equal-budget GuardedSemanticFallback calls
are made *before* the original PreferredOnly trial in an opt-in process.
Compare that with the unchanged ordering:
PreferredOnly(256) then Guarded(256) then extended trials.

The extra diagnostics are source-local, same original Γ and source captures.
No new acceptance, weakening of REJECT, or equality admission is possible.
"""
from pathlib import Path
import sys
if len(sys.argv)!=2:raise SystemExit("usage: SCRIPT TYPECHECK_RS")
p=Path(sys.argv[1]);s=p.read_text()
needle='''            let relation = crate::convert::convert_with_policy_in_context(
                &probe, &actual_type, &domain,
                remaining.min(256),
                crate::convert::DeltaPolicy::PreferredOnly,
                context.len(), context,
            );'''
insert=r'''            // This method exists under #[cfg(feature = "diagnostics")].
            // The selected real pair is source-owned, not reconstructed.
            if std::env::var_os("NUCLEUS_TRACE_PI_ORDER").is_some()
                && matches!(&actual_type, TypeValue::Pi { .. })
                && matches!(&domain, TypeValue::Term(_))
            {
                use std::sync::atomic::{AtomicUsize,Ordering};
                static COLD_ORDER:AtomicUsize=AtomicUsize::new(0);
                if COLD_ORDER.fetch_add(1,Ordering::Relaxed)<8 {
                    let first=crate::convert::convert_with_policy_in_context(
                        &probe,&actual_type,&domain,256,
                        crate::convert::DeltaPolicy::GuardedSemanticFallback,
                        context.len(),context,
                    );
                    let second=crate::convert::convert_with_policy_in_context(
                        &probe,&actual_type,&domain,256,
                        crate::convert::DeltaPolicy::GuardedSemanticFallback,
                        context.len(),context,
                    );
                    eprintln!(
                        "NUCLEUS_PI_COLD_ORDER:arg={position}:depth={}:source={:?}:first_guarded256={first:?}:second_guarded256={second:?}:context_len={}:synthetic_binder={:?}",
                        context.len(), match &domain {
                            TypeValue::Term(c)=>c.expr,
                            _=>unreachable!(),
                        }, context.len(),
                        match &actual_type {TypeValue::Pi{binder,..}=>Some(*binder),_=>None},
                    );
                }
            }
'''+needle
assert s.count(needle)==1,("SOURCE_DRIFT",s.count(needle))
assert s.count("NUCLEUS_PI_POLICY_SEPARATOR:")==1,"expected existing diagnostic-only source patch"
assert s.count("fn diagnostic_neutral_source_telescope_inner(")==1
s=s.replace(needle,insert)
p.write_text(s)
print("NUCLEUS_PI_ORDER=DIAGNOSTIC_ONLY_TWO_COLD_GUARDED_TRIALS",flush=True)
