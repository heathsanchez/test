#!/usr/bin/env python3
"""Diagnostic-only stage16 actual operand and context witness, no verdict changes."""
from pathlib import Path
import sys
p=Path(sys.argv[1])/"src/typecheck.rs"
s=p.read_text()
needle="""            if !equal(&TypeValue::Term(larg.clone()),
                      &TypeValue::Term(rarg.clone())) {
                return trace_first_failed_field_premise(16);
            }"""
assert s.count(needle)==1, "STAGE16_SOURCE_MISMATCH"
replacement="""            if !equal(&TypeValue::Term(larg.clone()),
                      &TypeValue::Term(rarg.clone())) {
                #[cfg(feature = "diagnostics")]
                if std::env::var_os("NUCLEUS_TRACE_STAGE16_TYPED_OPERAND").is_some() {
                    eprintln!(
                        "NUCLEUS_STAGE16_TYPED_OPERAND:left={:?}:right={:?}:left_type={:?}:right_type={:?}:left_domain={:?}:right_domain={:?}",
                        larg, rarg, larg_ty, rarg_ty, ldomain, rdomain
                    );
                }
                return trace_first_failed_field_premise(16);
            }"""
p.write_text(s.replace(needle,replacement,1))
print("NUCLEUS_STAGE16_TYPED_DIAGNOSTIC_ONLY",flush=True)
