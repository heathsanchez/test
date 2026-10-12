#!/usr/bin/env python3
"""Diagnostic-only source-bound closure environment separator; no verdict changes."""
from pathlib import Path
import sys
p=Path(sys.argv[1])/"src/typecheck.rs"
s=p.read_text()
needle="""                return trace_first_failed_field_premise(16);
            }"""
assert s.count(needle)==1, f"STAGE16_ENV_SOURCE_MISMATCH:{s.count(needle)}"
replacement="""                #[cfg(feature = "diagnostics")]
                if std::env::var_os("NUCLEUS_TRACE_STAGE16_ENV_SEPARATOR").is_some() {
                    eprintln!(
                        "NUCLEUS_STAGE16_ENV_SEPARATOR:expr_equal={}:env_equal={}:levels_equal={}:left_expr={:?}:right_expr={:?}:left_env={:?}:right_env={:?}",
                        larg.expr == rarg.expr,
                        larg.env.id() == rarg.env.id(),
                        larg.levels == rarg.levels,
                        larg.expr, rarg.expr, larg.env, rarg.env
                    );
                }
                #[cfg(feature = "diagnostics")]
                if std::env::var_os("NUCLEUS_TRACE_STAGE16_CONVERSION_OUTCOME").is_some() {
                    let outcome = crate::convert::convert_with_policy_in_context(
                        self,
                        &TypeValue::Term(larg.clone()),
                        &TypeValue::Term(rarg.clone()),
                        2048,
                        crate::convert::DeltaPolicy::PreferredOnly,
                        context.len(),
                        context,
                    );
                    eprintln!("NUCLEUS_STAGE16_CONVERSION_OUTCOME:proven={}:result={:?}",outcome.is_proven(),outcome);
                }
                return trace_first_failed_field_premise(16);
            }"""
s=s.replace(needle,replacement,1)
p.write_text(s)
print("NUCLEUS_STAGE16_ENV_SEPARATOR_DIAGNOSTIC_ONLY",flush=True)
