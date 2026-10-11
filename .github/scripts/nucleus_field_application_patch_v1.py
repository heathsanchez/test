#!/usr/bin/env python3
"""Experiment: sound, checked application congruence after constructor projection.

Layer on top of the source-pinned contextual capability patch. This is a
fully optional semantic rule. We do NOT infer constructor majors from output
types, and we do NOT equate any two syntactically similar environments.
"""
from pathlib import Path
import sys
root=Path(sys.argv[1] if len(sys.argv)>1 else "metatron-kernel")

def once(source, old, new, tag):
    c=source.count(old)
    if c!=1:
        raise SystemExit(f"FIELD_APP_PATCH_FAILED {tag} matches={c}")
    return source.replace(old,new,1)

tc=root/"src"/"typecheck.rs"
t=tc.read_text()
anchor="""    pub fn convert(&self, left: &TypeValue, right: &TypeValue, budget: usize) -> Judgment<()> {"""
addition=r'''
    /// A kernel-authorized congruence step for two source-certified
    /// constructor fields, each applied to a captured argument telescope.
    /// Unlike eager projection normalization, this checks the field equality
    /// plus each dependent Pi-domain and both argument types independently.
    /// A matched projection name, hash or sort alone NEVER grants equality.
    pub(crate) fn checked_field_application_congruence(
        &self,
        left_field: &Closure,
        right_field: &Closure,
        left_args: &[Closure],
        right_args: &[Closure],
        context: &[TypeValue],
        budget: usize,
    ) -> bool {
        if budget < 2048 || context.len() > 24
            || left_args.len() != right_args.len()
            || left_args.len() > 8
        {
            return false;
        }
        // Do not recursively invoke this rule to prove one of its own
        // premises. Premise conversion uses the preexisting trusted rules.
        thread_local! {
            static FIELD_APP_ACTIVE: std::cell::Cell<bool> =
                const { std::cell::Cell::new(false) };
        }
        let first=FIELD_APP_ACTIVE.with(|c|{
            if c.get() {false} else {c.set(true);true}
        });
        if !first {return false}
        struct Reset;
        impl Drop for Reset {
            fn drop(&mut self) {
                FIELD_APP_ACTIVE.with(|c|c.set(false));
            }
        }
        let _reset=Reset;

        let mut lf=budget.min(8192);
        let Some(mut left_ty)=self.infer_exact_closure_in_context(
            left_field,context,&mut lf,0,
        ) else {return false};
        let mut rf=budget.min(8192);
        let Some(mut right_ty)=self.infer_exact_closure_in_context(
            right_field,context,&mut rf,0,
        ) else {return false};

        let equal = |a:&TypeValue,b:&TypeValue| {
            crate::convert::convert_with_policy_in_context(
                self,a,b,2048,
                crate::convert::DeltaPolicy::PreferredOnly,
                context.len(),context,
            ).is_proven()
        };
        if !equal(&left_ty,&right_ty)
            || !equal(
                &TypeValue::Term(left_field.clone()),
                &TypeValue::Term(right_field.clone()),
            )
        {
            return false;
        }

        for (larg,rarg) in left_args.iter().zip(right_args) {
            let Some((ldomain,lbody))=self.pi_view(
                Judgment::proven(left_ty,"certified-left-field-type"),2048,
            ) else {return false};
            let Some((rdomain,rbody))=self.pi_view(
                Judgment::proven(right_ty,"certified-right-field-type"),2048,
            ) else {return false};
            if !equal(&ldomain,&rdomain) {
                return false;
            }
            let mut lf=budget.min(8192);
            let Some(larg_ty)=self.infer_exact_closure_in_context(
                larg,context,&mut lf,0,
            ) else {return false};
            let mut rf=budget.min(8192);
            let Some(rarg_ty)=self.infer_exact_closure_in_context(
                rarg,context,&mut rf,0,
            ) else {return false};
            if !equal(&larg_ty,&ldomain)
                || !equal(&rarg_ty,&rdomain)
                || !equal(&TypeValue::Term(larg.clone()),
                          &TypeValue::Term(rarg.clone()))
            {
                return false;
            }

            let next = |body:PiBody,arg:&Closure,dom:&TypeValue|
                -> Option<TypeValue> {
                match body {
                    PiBody::Fixed(binder,ty)=>{
                        let mut fuel=budget.min(4096);
                        self.instantiate_fixed_pi_body(&ty,binder,arg,&mut fuel)
                    },
                    PiBody::Closure(body)=>{
                        let frame=body.env.extend(arg.clone());
                        self.retain_checked_elimination(
                            &frame,dom.clone(),context,
                        );
                        Some(TypeValue::Term(Closure::with_levels(
                            body.expr,frame,body.levels,
                        )))
                    },
                }
            };
            let Some(next_left)=next(lbody,larg,&ldomain) else {return false};
            let Some(next_right)=next(rbody,rarg,&rdomain) else {return false};
            left_ty=next_left;
            right_ty=next_right;
        }

        // No need to normalize a potentially enormous application. Its
        // equality follows from the already checked field and Pi telescope
        // congruence. Resource exhaustion in ANY premise refuses the rule.
        true
    }

'''
t=once(t,anchor,addition+anchor,"typed field application method")
tc.write_text(t)

cv=root/"src"/"convert.rs"
s=cv.read_text()
old="""                let machine = checker.machine();
                let left_value = machine.projection_value_for_conversion("""
new="""                let machine = checker.machine();
                // Constructor-field iota can expose the exact selected
                // fields while normalizing their applications still stalls.
                // Only use the definitional congruence rule after *both*
                // selections and the entire dependent function-application
                // telescopes are independently source-checked.
                if std::env::var_os(
                    "NUCLEUS_EXPERIMENTAL_CERTIFIED_FIELD_APPLICATION",
                ).is_some()
                    && depth == context.len()
                    && current_budget >= 2048
                    && let (Some(lfield),Some(rfield)) = (
                        machine.projection_field_for_conversion(
                            left_structure.clone(),*left_type,*left_index,2048,
                        ).proven_value().cloned(),
                        machine.projection_field_for_conversion(
                            right_structure.clone(),*right_type,*right_index,2048,
                        ).proven_value().cloned(),
                    )
                    && checker.checked_field_application_congruence(
                        &lfield,&rfield,left_spine,right_spine,
                        context,current_budget.min(8192),
                    )
                {
                    #[cfg(feature="diagnostics")]
                    if std::env::var_os(
                        "NUCLEUS_TRACE_CERTIFIED_FIELD_APPLICATION",
                    ).is_some() {
                        use std::sync::atomic::{AtomicUsize,Ordering};
                        static COUNT:AtomicUsize=AtomicUsize::new(0);
                        if COUNT.fetch_add(1,Ordering::Relaxed)<96 {
                            eprintln!(
                                "NUCLEUS_FIELD_APP_PROVEN:type={left_type:?}:index={left_index}:depth={depth}:arity={}",
                                left_spine.len(),
                            );
                        }
                    }
                    return Judgment::proven(
                        (),"checked-constructor-field-dependent-application-congruence",
                    );
                }
                let left_value = machine.projection_value_for_conversion("""
s=once(s,old,new,"source projection extraction congruence")
cv.write_text(s)
print("PATCHED_FIELD_APPLICATION_V1")
