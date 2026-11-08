"""C72: isolate the local grant on authentic checked recursor-major exposure.

Exactly two verified 512-cap source calls must be present in the reconstructed
C65 reducer. Other rules, parent fuel, captured bindings and proof outcomes
are untouched. Trace-only diagnostics never authorize a constructor.
"""
from pathlib import Path

p=Path("metatron-kernel/src/machine.rs")
code=p.read_text()
begin=code.index("    fn qualified_recursor_result(")
end=code.index("    fn ",begin+9)
section=code[begin:end]
oldstart="                let major_result="
endmarker="                let Some(value)=major_result.proven_value()"
assert section.count(oldstart)==1,("C72 major declaration mismatch",section.count(oldstart))
start=section.index(oldstart)
assert endmarker in section[start:],"major result continuation missing"
stop=section.index(endmarker,start)
old=section[start:stop]
cap="self.exposure_fuel.get().unwrap_or(0).min(512)"
assert old.count(cap)==2,("C72 expected exactly two local 512 grants",old.count(cap),old[:1700])

prefix="""                // C72: no new proof, constructor, conversion or source rule.
                // Same source exposure functions, with caller-owned total fuel.
                let c72_owner_before=self.exposure_fuel.get().unwrap_or(0);
                let c72_grant=if std::env::var_os("NUCLEUS_C72_MAJOR_GRANT_2048").is_some() {
                    2048usize
                } else {512usize};
"""
calls=old.replace(cap,"self.exposure_fuel.get().unwrap_or(0).min(c72_grant)")
trace="""                #[cfg(feature="diagnostics")]
                if std::env::var_os("NUCLEUS_C72_SOURCE_MAJOR").is_some()
                    && crate::typecheck::c56_source_root_active()
                {
                    use std::sync::atomic::{AtomicUsize,Ordering};
                    static C72_EVENTS:AtomicUsize=AtomicUsize::new(0);
                    let number=C72_EVENTS.fetch_add(1,Ordering::Relaxed)+1;
                    if number<=96 || number.is_power_of_two(){
                        let src=&neutral.spine[required-1];
                        let status=match major_result.proven_value(){
                            None => "unknown",
                            Some(Value::Neutral(n)) if matches!(&n.head,
                                NeutralHead::Const{name,..} if self.recursor_reductions.contains_key(name)) => "nested_recursor",
                            Some(Value::Neutral(_)) => "neutral",
                            Some(Value::NatLit(_)) => "nat",
                            Some(Value::StuckProjection{..}) => "stuck_projection",
                            Some(_) => "value",
                        };
                        eprintln!("NUCLEUS_C72_MAJOR:event={number}:recursor={name:?}:major_expr={:?}:major_env={}:major_env_hash={:?}:levels={}:grant={}:owner_before={c72_owner_before}:owner_after={}:status={status}:parent_frames={}",
                            src.expr,src.env.id(),src.env.diagnostic_content_fingerprint(),
                            src.levels.entries().count(),c72_grant.min(c72_owner_before),
                            self.exposure_fuel.get().unwrap_or(0),parents.len());
                    }
                }
"""
new_section=section[:start]+prefix+calls+trace+section[stop:]
p.write_text(code[:begin]+new_section+code[end:])
print("C72_EXACT_SOURCE_MAJOR_PATCHED: two local grants, no proof rules")
