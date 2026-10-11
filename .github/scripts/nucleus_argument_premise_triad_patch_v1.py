#!/usr/bin/env python3
"""Pure diagnostic split of field-application argument-validation triad.

Prior stage11 combined left argument type, right argument type, and equality
of the two *actual* arguments. Decompose in the exact original short-circuit
order. Source acceptance, conversion policy, resource bounds unchanged.
"""
from pathlib import Path
import sys
p=Path(sys.argv[1] if len(sys.argv)>1 else "metatron-kernel")/"src/typecheck.rs"
s=p.read_text()
old="""            if !equal(&larg_ty,&ldomain)
                || !equal(&rarg_ty,&rdomain)
                || !equal(&TypeValue::Term(larg.clone()),
                          &TypeValue::Term(rarg.clone()))
            {
                return trace_first_failed_field_premise(11);
            }
"""
new="""            // Exactly the original left-to-right short-circuit expression,
            // with only a *diagnostic* provenance at each false exit.
            if !equal(&larg_ty,&ldomain) {
                return trace_first_failed_field_premise(14);
            }
            if !equal(&rarg_ty,&rdomain) {
                return trace_first_failed_field_premise(15);
            }
            if !equal(&TypeValue::Term(larg.clone()),
                      &TypeValue::Term(rarg.clone())) {
                return trace_first_failed_field_premise(16);
            }
"""
count=s.count(old)
assert count==1,f"ARGUMENT_TRIAD_SOURCE_MISMATCH count={count}"
p.write_text(s.replace(old,new,1))
print("ARGUMENT_TRIAD_SEPARATED_PRESERVING_SHORT_CIRCUIT")
