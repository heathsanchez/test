#!/usr/bin/env python3
"""Opt-in existing guarded conversion after source-checked argument typing."""
from pathlib import Path
import sys

p = Path(sys.argv[1]) / 'src/typecheck.rs'
s = p.read_text()
old = '''            if !equal(&TypeValue::Term(larg.clone()),
                      &TypeValue::Term(rarg.clone())) {'''
new = '''            if !equal(&TypeValue::Term(larg.clone()),
                      &TypeValue::Term(rarg.clone()))
                && !(std::env::var_os("NUCLEUS_EXPERIMENTAL_GUARDED_FIELD_ARGUMENT").is_some()
                    && crate::convert::convert_with_policy_in_context(
                        self,
                        &TypeValue::Term(larg.clone()),
                        &TypeValue::Term(rarg.clone()),
                        budget.min(8192),
                        crate::convert::DeltaPolicy::GuardedSemanticFallback,
                        context.len(),
                        context,
                    ).is_proven())
            {'''
assert s.count(old) == 1, 'GUARDED_FIELD_ARGUMENT_SOURCE_MISMATCH'
p.write_text(s.replace(old, new, 1))
print('GUARDED_FIELD_ARGUMENT_PATCHED_OPT_IN')
