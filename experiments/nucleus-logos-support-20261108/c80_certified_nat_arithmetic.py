"""C80: source-owned completed numeric operation sharing, not proof caching.

This composes with the frozen C65 independent checker. It interns only
genuinely completed registered primitive arithmetic on *proven numerals*,
across differing lexical argument frames, but solely under the same
immutable definition/operation authority. No guessed Nat, recursor, proof,
neutral or UNKNOWN is ever retained as a native computation result.
"""
from pathlib import Path
p=Path("metatron-kernel/src/machine.rs")
s=p.read_text()
def change(old,new):
    global s
    c=s.count(old)
    if c!=1:raise AssertionError(("C80 exact source anchor drift",c,old[:140]))
    s=s.replace(old,new)
key=r"""
// C80. Numeric source result identity is narrower than closure identity,
// but valid only after both original operands have *actually* reduced to
// well-formed native Nat literals under the registered source primitive.
// Retaining the owner Rc prevents false pointer equality through reuse.
#[derive(Clone,Eq,Hash,PartialEq)]
struct C80NativeArithmeticKey {
    authority: AuthorityId,
    source_definitions: ImmutableMapWitness<HashMap<NameId,DefinitionBody>>,
    native_nat: NatPrimitives,
    operation: NameId,
    left: crate::nat::BigNat,
    right: crate::nat::BigNat,
}
struct ClockExposure {value:Value,referenced:bool}
"""
change("struct ClockExposure {value:Value,referenced:bool}",key)
change("    completed_replay_count:usize,","    completed_replay_count:usize,\n    c80_native_arithmetic:HashMap<C80NativeArithmeticKey,crate::nat::BigNat>,")
start=s.index("    fn try_native_bounded_arithmetic(")
end=s.index("    fn try_native_nat_reduction(",start)
f=s[start:end]
anchor="        let mut work=budget;\n        let result=match operation {"
assert f.count(anchor)==1,("C80 arithmetic evaluation site drift",f.count(anchor))
insert=r"""        // Only the already-qualified operation, actual native numerals and
        // identical immutable source authority may share computation.
        // A miss cannot cause any new rejection; cache key work is charged
        // to the same actual outer evaluation owner, never a fresh budget.
        let c80_enabled=std::env::var_os("NUCLEUS_C80_EXACT_NAT_VALUE_SHARE").is_some();
        let mut c80_key=None;
        if c80_enabled
            && self.exposure_cache.is_some()
            && left.limb_count()<=4 && right.limb_count()<=4
            && budget>=128
        {
            let charge=8usize.saturating_add(left.limb_count().saturating_mul(8))
                .saturating_add(right.limb_count().saturating_mul(8));
            if self.exposure_fuel.get().is_some_and(|available|available>charge+16)
                && self.reserve_replay_work(charge)
            {
                let exact=C80NativeArithmeticKey{
                    authority:self.authority,
                    source_definitions:ImmutableMapWitness(self.definitions.clone()),
                    native_nat:nat.clone(),operation:name,
                    left:left.clone(),right:right.clone(),
                };
                let cached=self.exposure_cache.as_ref().and_then(|owned|
                    owned.borrow().c80_native_arithmetic.get(&exact).cloned());
                if let Some(number)=cached{
                    #[cfg(feature="diagnostics")]
                    if std::env::var_os("NUCLEUS_C80_ARITH_TRACE").is_some(){
                        use std::sync::atomic::{AtomicUsize,Ordering};
                        static HITS:AtomicUsize=AtomicUsize::new(0);
                        let count=HITS.fetch_add(1,Ordering::Relaxed)+1;
                        if count.is_power_of_two(){
                            eprintln!("NUCLEUS_C80_ARITH:kind=exact-hit:count={count}:operation={name:?}");
                        }
                    }
                    pending.clear();
                    return Some(Judgment::proven(Value::NatLit(number),
                        "c80-completed-certified-Nat-operation"));
                }
                c80_key=Some(exact);
            }
        }
        let mut work=budget;
        let result=match operation {"""
f=f.replace(anchor,insert)
endanchor=r"""        Some(match result {
            Some(number)=>{pending.clear();Judgment::proven(Value::NatLit(number),"qualified-bounded-native-Nat-arithmetic")}
            None=>Judgment::unknown("native-Nat-arithmetic-budget"),
        })"""
assert f.count(endanchor)==1,"C80 result capture site drift"
replacement=r"""        Some(match result {
            Some(number)=>{
                // The only admissible entry is the complete source primitive
                // computation, not a guessed result or an unfinished recursor.
                if let (Some(key),Some(owned))=(c80_key,self.exposure_cache.as_ref()){
                    let mut entries=owned.borrow_mut();
                    if entries.c80_native_arithmetic.len()<4096 {
                        entries.c80_native_arithmetic.entry(key).or_insert_with(||number.clone());
                        #[cfg(feature="diagnostics")]
                        if std::env::var_os("NUCLEUS_C80_ARITH_TRACE").is_some(){
                            use std::sync::atomic::{AtomicUsize,Ordering};
                            static WRITES:AtomicUsize=AtomicUsize::new(0);
                            let count=WRITES.fetch_add(1,Ordering::Relaxed)+1;
                            if count.is_power_of_two() {
                                eprintln!("NUCLEUS_C80_ARITH:kind=completed-write:count={count}:operation={name:?}");
                            }
                        }
                    }
                }
                pending.clear();
                Judgment::proven(Value::NatLit(number),"qualified-bounded-native-Nat-arithmetic")
            }
            None=>Judgment::unknown("native-Nat-arithmetic-budget"),
        })"""
f=f.replace(endanchor,replacement)
s=s[:start]+f+s[end:]
p.write_text(s)
print("C80_EXACT_CERTIFIED_NAT_NUMERALS_ONLY_PATCH_APPLIED")
