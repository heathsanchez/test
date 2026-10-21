#!/usr/bin/env python3
"""Discover the NEXT original-source dependent-telescope premise.

The original Nucleus source's *diagnostic-only* function attempted 256-step
PreferredOnly conversion and stopped at Π argument 3 in two real Magma exports.
An independent held-out replay already showed GuardedSemanticFallback at the
same 256 budget PROVEN on the same source-typed pair (and PreferredOnly at
2048 PROVEN). This experiment changes ONLY that diagnostic's choice of
existing policy to find which premise comes next. It may NOT influence a
kernel verdict and confers no new checking authority.
"""
from pathlib import Path
import sys
if len(sys.argv)!=2: raise SystemExit("usage: script.py TYPECHECK_RS")
p=Path(sys.argv[1]);s=p.read_text()
needle='''            let relation = crate::convert::convert_with_policy_in_context(
                &probe, &actual_type, &domain,
                remaining.min(256),
                crate::convert::DeltaPolicy::PreferredOnly,
                context.len(), context,
            );
            if !relation.is_proven() {
                return format!(
                    "first-undischarged-domain:argument={position}:actual={actual_type:?}:required={domain:?}:relation={relation:?}:context_depth={}",
                    context.len(),
                );
            }'''
replace='''            // DIAGNOSTIC-ONLY replacement, inside a cfg(feature="diagnostics")
            // source-telescope probe, never inside the verdict evaluator.
            // Consume the SAME 256 local conversion budget but use the
            // existing full checked policy demonstrated by the source A/B.
            let relation = crate::convert::convert_with_policy_in_context(
                &probe, &actual_type, &domain,
                remaining.min(256),
                crate::convert::DeltaPolicy::GuardedSemanticFallback,
                context.len(), context,
            );
            if !relation.is_proven() {
                return format!(
                    "first-undischarged-domain:argument={position}:actual={actual_type:?}:required={domain:?}:relation={relation:?}:context_depth={}",
                    context.len(),
                );
            }'''
assert s.count(needle)==1,("diagnostic source drift",s.count(needle))
assert s.count("fn diagnostic_neutral_source_telescope_inner(")==1
s=s.replace(needle,replace)
p.write_text(s)
print("NUCLEUS_PI_CONTINUATION=DIAGNOSTIC_ONLY_NO_VERDICT_CHANGES",flush=True)
