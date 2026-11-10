"""Diagnostic-only C87 source recursor-name histogram at C50 worklist loss.

Only an exact source NeutralHead::Const NameId is counted as a named frame.
Projection/free heads remain explicit nonconst. This is not a completion,
constructor witness, dependency proof, reduction rule, or cache authority.
Run after existing C82b, C84 and C85 patch scripts.
"""
from pathlib import Path


def apply_c87(source=Path("metatron-kernel/src/machine.rs")):
    text = source.read_text()
    marker = '                        eprintln!("NUCLEUS_C50_LOST:{}",serde_json::json!({'
    assert text.count(marker) == 1, "C87 exact C50 failure-site anchor drift"
    added = r"""
                        // C87 observation only. Inspect pending certified
                        // source-worklist Major parents at the existing C50
                        // failure point; do not alter evaluator decisions.
                        if std::env::var_os("NUCLEUS_C87_PENDING_MAJOR").is_some() {
                            let mut major_names=HashMap::<u64,u64>::new();
                            let mut major_nonconst=0u64;
                            for pending in &parents {
                                if let Continuation::Major(neutral,_) = pending {
                                    match &neutral.head {
                                        NeutralHead::Const{name,..}=>{
                                            let count=major_names.entry(name.0).or_insert(0);
                                            *count=count.saturating_add(1);
                                        }
                                        _=>major_nonconst=major_nonconst.saturating_add(1),
                                    }
                                }
                            }
                            eprintln!("NUCLEUS_C87_PENDING:{}",serde_json::json!({
                                "seq":seq,"stage":$stage,"parents":parents.len(),
                                "finish_parents":finish,"major_parents":major,
                                "projected_parents":projected,
                                "major_const_names":major_names,
                                "major_nonconst":major_nonconst,
                                "owner_remaining":self.exposure_fuel.get().unwrap_or(0),
                            }));
                        }
"""
    source.write_text(text.replace(marker, added + marker))


if __name__ == "__main__":
    apply_c87()
    print("C87_PENDING_SOURCE_RECURSOR_OBSERVER_APPLIED")
