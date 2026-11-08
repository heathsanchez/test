"""C69: insert observation-only counters into the C64 reconstructed checker.

All changes are diagnostics-gated. No rule, budget or verdict branch changes.
Fail closed if the source anchors drift; do not guess a new patch location.
"""
from pathlib import Path

ROOT=Path("metatron-kernel")
def replace_once(path,old,new):
    p=ROOT/path
    text=p.read_text()
    assert text.count(old)==1,(p,"expected one anchor",text.count(old),old[:85])
    p.write_text(text.replace(old,new))

# A single per-process, thread-local instrumented work census. The diagnostic
# binary runs checking inside one worker thread; report before worker exits.
p=ROOT/"src/diagnostics.rs"
s=p.read_text()
assert "c69_counts" not in s
s += r"""
// C69 source cost attribution. Counts are local to the checking worker.
use std::sync::OnceLock;
thread_local! {
    static C69: std::cell::RefCell<[u64;11]> = const {std::cell::RefCell::new([0;11])};
}
pub fn c69_enabled()->bool {
    static ENABLED:OnceLock<bool>=OnceLock::new();
    *ENABLED.get_or_init(||std::env::var_os("NUCLEUS_C69_SOURCE_COST").is_some())
}
pub fn c69_count(which:usize) {
    if !c69_enabled(){return;}
    C69.with(|c|{let mut x=c.borrow_mut();x[which]=x[which].saturating_add(1)});
}
pub fn c69_report() {
    if !c69_enabled(){return;}
    C69.with(|c| {
        let x=c.borrow();
        eprintln!("NUCLEUS_C69_COUNTS:{{\"expose_steps\":{},\"source_constants\":{},\"nat_mul_heads\":{},\"nat_mod_heads\":{},\"nat_add_heads\":{},\"qualified_recursor_heads\":{},\"source_decidable_rec_heads\":{},\"source_projection_heads\":{}}}",
            x[0],x[1],x[2],x[3],x[4],x[5],x[6],x[10]);
    });
}
"""
p.write_text(s)

# Work counter at a unique location *inside* the named reducer.
# Earlier C47 observer versions insert their own line after decrement.
p=ROOT/"src/machine.rs"
body=p.read_text()
start=body.index("    fn expose_uncached_internal_with_pending(")
end=body.index("    fn ",start+9)
chunk=body[start:end]
anchor="            budget -= 1;"
assert chunk.count(anchor)==1,("budget anchor drift",chunk.count(anchor))
chunk=chunk.replace(anchor,anchor+'''
            #[cfg(feature="diagnostics")]
            crate::diagnostics::c69_count(0);''')
p.write_text(body[:start]+chunk+body[end:])

# Attribute only expression-head visits. This is an *observation* of attempted
# source reductions, not a count of successful primitive reductions.
p=ROOT/"src/machine.rs"
body=p.read_text()
start=body.index("    fn expose_uncached_internal_with_pending(")
end=body.index("    fn ",start+9)
chunk=body[start:end]
anchor="            match expression {"
assert chunk.count(anchor)==1,("expression match anchor drift",chunk.count(anchor))
insert='''            #[cfg(feature="diagnostics")]
            if crate::diagnostics::c69_enabled() {
                match expression {
                    Expr::Const{name,..}=>{
                        crate::diagnostics::c69_count(1);
                        if let Some(nat)=self.nat_primitives.as_ref() {
                            if nat.mul==Some(*name){crate::diagnostics::c69_count(2);}
                            if nat.modulo==Some(*name){crate::diagnostics::c69_count(3);}
                            if nat.add==Some(*name){crate::diagnostics::c69_count(4);}
                        }
                        if self.recursor_reductions.contains_key(name){crate::diagnostics::c69_count(5);}
                        if *name==NameId(147){crate::diagnostics::c69_count(6);}
                    }
                    Expr::Proj{..}=>crate::diagnostics::c69_count(10),
                    _=>{}
                }
            }
'''
chunk=chunk.replace(anchor,insert+anchor)
p.write_text(body[:start]+chunk+body[end:])

# Locate the binary actually compiled from the authenticated C37 source
# archive. The research-tree example under experiments is not this binary.
candidates=list((ROOT/"src").rglob("nucleus-diagnostic.rs"))
assert len(candidates)==1,("actual diagnostic binary source missing/ambiguous",candidates)
p=candidates[0]
s=p.read_text()
assert "diagnostic_steps={steps}" in s,("diagnostic output anchor missing",p)
assert s.count('eprintln!("diagnostic_steps={steps}:verdict={verdict:?}");')==1
s=s.replace('eprintln!("diagnostic_steps={steps}:verdict={verdict:?}");',
'''#[cfg(feature="diagnostics")]
 metatron_kernel::diagnostics::c69_report();
 eprintln!("diagnostic_steps={steps}:verdict={verdict:?}");''')
p.write_text(s)
print("C69_INSTRUMENT_APPLIED_NO_PROOF_RULE_CHANGED:binary="+str(p))
