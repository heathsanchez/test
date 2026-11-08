"""C72: exact-source major-grant observation and single-variable experiment.

Runs only against reconstructed C65 Rust source; refuses source drift. No
constructor/equality inference is added. Variant merely changes *local* major
exposure allowance, still bounded by the existing shared work owner.
"""
from pathlib import Path
p=Path("metatron-kernel/src/machine.rs")
s=p.read_text()
start=s.index("    fn qualified_recursor_result(")
end=s.index("    fn ",start+9)
section=s[start:end]
old="""                let major_result=if self.replay_projection_major {
                    self.expose_for_conversion(neutral.spine[required-1].clone(),
                        Transparency::Full,self.exposure_fuel.get().unwrap_or(0).min(512))
                } else {
                    self.expose(neutral.spine[required-1].clone(),
                        Transparency::Full,self.exposure_fuel.get().unwrap_or(0).min(512))
                };"""
assert section.count(old)==1,("major-grant source anchor drift",section.count(old))
new="""                // C72: the same source-exposure algorithms, original total
                // owner fuel, and registered kernel reductions; only the
                // local grant ceiling is changed for one experimental arm.
                let c72_grant = if std::env::var_os("NUCLEUS_C72_MAJOR_GRANT_2048").is_some()
                    { 2048usize } else { 512usize };
                let c72_owner_before=self.exposure_fuel.get().unwrap_or(0);
                let major_result=if self.replay_projection_major {
                    self.expose_for_conversion(neutral.spine[required-1].clone(),
                        Transparency::Full,c72_owner_before.min(c72_grant))
                } else {
                    self.expose(neutral.spine[required-1].clone(),
                        Transparency::Full,c72_owner_before.min(c72_grant))
                };
                #[cfg(feature="diagnostics")]
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
                }"""
section=section.replace(old,new)
p.write_text(s[:start]+section+s[end:])
print("C72_SOURCE_OWNED_MAJOR_GRANT_PATCHED")
