"""C74: observational binder-context separator at C73 event 26.

Exact restored C65 machine only. Source closure/binder fingerprints do not
grant equality, iota, constructor, cache or verification authority.
"""
from pathlib import Path

path=Path("metatron-kernel/src/machine.rs")
src=path.read_text()
needle="""        let Some(seq)=crate::diagnostics::c48_ticket() else { return; };
        let c49_fingerprint="""
assert src.count(needle)==1,("C74 source C48/C49 hook drift",src.count(needle))
insert="""        let Some(seq)=crate::diagnostics::c48_ticket() else { return; };
        // Source-specific bounded observer; only reports actual captured
        // bindings, without mutating any closure, rule, work owner or cache.
        if std::env::var_os("NUCLEUS_C74_CAPTURE_CONTEXT").is_some()
            && matches!(seq,0|2|26|28|30)
            && source.expr.0==11
        {
            let mut binders=Vec::new();
            for i in 0usize..128usize {
                let Some(b)=source.env.lookup(i) else {break;};
                let descriptor=match b {
                    EnvBinding::Closure(c)=>format!(
                        "closure:expr={:?}:levels={}:captured_env={}",
                        c.expr,c.levels.entries().count(),c.env.id()),
                    EnvBinding::Neutral(n)=>format!(
                        "neutral:head={:?}:spine={}",
                        n.head,n.spine.len()),
                    EnvBinding::Free(f)=>format!("free:{f:?}"),
                    EnvBinding::NatLit(n)=>format!("nat:limbs={}",n.limb_count()),
                };
                binders.push((i,descriptor));
            }
            let levels=source.levels.entries()
                .take(12).map(|(n,v)|format!("{n:?}:{v:?}")).collect::<Vec<_>>();
            eprintln!("NUCLEUS_C74_CONTEXT:{}",serde_json::json!({
                "seq":seq,
                "recursor":name.0,
                "source_expr":source.expr.0,
                "source_env":source.env.id(),
                "source_env_fingerprint":source.env.diagnostic_content_fingerprint(),
                "source_level_entries":levels,
                "sampled_binders":binders,
                "no_source_equality_or_proof_authority":true,
            }));
        }
        let c49_fingerprint="""
path.write_text(src.replace(needle,insert))
print("C74_DIAGNOSTIC_CONTEXT_ONLY_PATCHED")
