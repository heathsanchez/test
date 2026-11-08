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
use std::cell::RefCell;
use std::sync::OnceLock;
thread_local! {
    static C69: RefCell<[u64;11]> = const {RefCell::new([0;11])};
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
        eprintln!("NUCLEUS_C69_COUNTS:{{\"expose_steps\":{},\"source_constants\":{},\"nat_mul_heads\":{},\"nat_mod_heads\":{},\"nat_add_heads\":{},\"qualified_recursor_heads\":{},\"source_decidable_rec_heads\":{},\"nat_native_result\":{},\"nat_native_unknown\":{},\"nat_ext_result\":{},\"source_projection_heads\":{}}}",
            x[0],x[1],x[2],x[3],x[4],x[5],x[6],x[7],x[8],x[9],x[10]);
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

replace_once(Path("src/machine.rs"),"""                Expr::Const { name, levels } => {
                    if let Some(arithmetic)""",
"""                Expr::Const { name, levels } => {
                    #[cfg(feature="diagnostics")] {
                        crate::diagnostics::c69_count(1);
                        if let Some(nat)=self.nat_primitives.as_ref() {
                            if nat.mul==Some(*name){crate::diagnostics::c69_count(2);}
                            if nat.modulo==Some(*name){crate::diagnostics::c69_count(3);}
                            if nat.add==Some(*name){crate::diagnostics::c69_count(4);}
                        }
                        if *name==NameId(147){crate::diagnostics::c69_count(6);}
                    }
                    if let Some(arithmetic)""")
replace_once(Path("src/machine.rs"),"""                            Judgment::Proven{value,..}=>{
                                record_transition(&mut transitions,record_witnesses,TransitionWitness::NatExtension);""",
"""                            Judgment::Proven{value,..}=>{
                                #[cfg(feature="diagnostics")]
                                crate::diagnostics::c69_count(7);
                                record_transition(&mut transitions,record_witnesses,TransitionWitness::NatExtension);""")
replace_once(Path("src/machine.rs"),"""                            Judgment::Unknown{residual}=>Judgment::Unknown{residual},
                            Judgment::Refuted{obstruction}=>Judgment::Refuted{obstruction},""",
"""                            Judgment::Unknown{residual}=>{
                                #[cfg(feature="diagnostics")]
                                crate::diagnostics::c69_count(8);
                                Judgment::Unknown{residual}
                            },
                            Judgment::Refuted{obstruction}=>Judgment::Refuted{obstruction},""")
replace_once(Path("src/machine.rs"),"""                    if let Some(native) = self.try_native_nat_reduction(
                        *name,""",
"""                    if let Some(native) = self.try_native_nat_reduction(
                        *name,""")
# Count only an actual successfully applied Nat extension.
replace_once(Path("src/machine.rs"),"""                    ) {
                        record_transition(
                            &mut transitions,
                            record_witnesses,
                            TransitionWitness::NatExtension,
                        );
                        return exposed(native, transitions);
                    }

                    if let Some(next) = self.try_quot_reduction""",
"""                    ) {
                        #[cfg(feature="diagnostics")]
                        crate::diagnostics::c69_count(9);
                        record_transition(
                            &mut transitions,
                            record_witnesses,
                            TransitionWitness::NatExtension,
                        );
                        return exposed(native, transitions);
                    }

                    if let Some(next) = self.try_quot_reduction""")
# Every encountered eligible certified recursor head
replace_once(Path("src/machine.rs"),"""                    if let Some(reduction) = self.recursor_reductions.get(name) {
                        if std::env::var_os("NUCLEUS_TRACE_NAT_IOTA")""",
"""                    if let Some(reduction) = self.recursor_reductions.get(name) {
                        #[cfg(feature="diagnostics")]
                        crate::diagnostics::c69_count(5);
                        if std::env::var_os("NUCLEUS_TRACE_NAT_IOTA")""")
# Report the same worker's thread-local census through the C64 diagnostic runner.
p=Path("experiments/nucleus-bool-recursor-eligibility-20261106/nucleus-diagnostic.rs")
s=p.read_text()
assert "diagnostic_steps={steps}" in s
s=s.replace('eprintln!("diagnostic_steps={steps}:verdict={verdict:?}");',
'''#[cfg(feature="diagnostics")]
 metatron_kernel::diagnostics::c69_report();
 eprintln!("diagnostic_steps={steps}:verdict={verdict:?}");''')
p.write_text(s)
print("C69_INSTRUMENT_APPLIED_NO_PROOF_RULE_CHANGED")
