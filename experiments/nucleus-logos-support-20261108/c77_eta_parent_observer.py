"""C77 observe the actual f in the source lambda (fun x => f x).

This prints only the semantic owner reached by BVar1 in each C74 event28
captured closure. No proof or equality rule changes.
"""
from pathlib import Path

p=Path("metatron-kernel/src/machine.rs")
src=p.read_text()
needle="""            let levels=source.levels.entries()"""
assert src.count(needle)==1,("C77 C74 observer anchor changed",src.count(needle))
insert=r'''            // C77: source-frozen event28 only. BVar2 under the source lambda
            // Expr7369 would denote the outer captured slot1. BVar1 in
            // Expr6 denotes its own captured slot1. Observe both instead of
            // assuming identical allocation/context or calling eta equality.
            let c77_parent_slot1 = if seq==28 {
                match source.env.lookup(0) {
                    Some(EnvBinding::Closure(root)) => {
                        let parent = root.env.lookup(1);
                        let resolved = parent.as_ref().map(|b| match b {
                            EnvBinding::Closure(c)=>format!(
                                "closure:expr={:?}:level_entries={}:env_fingerprint={}",
                                c.expr,c.levels.entries().count(),
                                c.env.diagnostic_content_fingerprint()),
                            EnvBinding::Neutral(n)=>format!(
                                "neutral:head={:?}:spine={}",n.head,n.spine.len()),
                            EnvBinding::Free(f)=>format!("free:{f:?}"),
                            EnvBinding::NatLit(n)=>format!("nat:limbs={}",n.limb_count()),
                        });
                        Some(serde_json::json!({
                            "root_expr":root.expr.0,
                            "root_capture_env_fingerprint":
                                root.env.diagnostic_content_fingerprint(),
                            "root_levels":root.levels.entries().count(),
                            "outer_slot1":resolved,
                            "captures_equivalent_unproved":true,
                        }))
                    },
                    _ => None,
                }
            } else { None };
'''
src=src.replace(needle,insert+needle)
anchor='"no_source_equality_or_proof_authority":true,'
assert src.count(anchor)==1,("C77 output anchor changed",src.count(anchor))
src=src.replace(anchor,'"c77_source_parent_slot1":c77_parent_slot1,\n                '+anchor)
p.write_text(src)
print("C77_SOURCE_CAPTURE_OBSERVER_ONLY_PATCHED")
