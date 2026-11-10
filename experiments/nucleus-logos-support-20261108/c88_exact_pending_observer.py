"""C88 diagnostics-only duplicate check for exact pending source Majors.

Neutral equality retains source head, universe substitution, full captured
closure spine and immutable EnvFrame identities. This is a conservative
NECESSARY diagnostic for potential within-call sharing, not proof authority.
Run after C87 source-name histogram patch.
"""
from pathlib import Path


def apply_c88(source=Path("metatron-kernel/src/machine.rs")):
    text=source.read_text()
    anchor='                            eprintln!("NUCLEUS_C87_PENDING:{}",serde_json::json!({'
    assert text.count(anchor)==1, "C88 exact C87 failure-site anchor drift"
    observer=r"""
                            if std::env::var_os("NUCLEUS_C88_EXACT_PENDING").is_some() {
                                // All pending parents share this source work
                                // owner and replay goal. A complete Neutral
                                // includes captured closure spines and levels;
                                // EnvFrame identity is conservative.
                                let mut distinct=Vec::<&Neutral>::new();
                                let mut repeated=0u64;
                                for pending in &parents {
                                    if let Continuation::Major(neutral,_) = pending {
                                        if distinct.iter().any(|saved|(*saved).eq(neutral)) {
                                            repeated=repeated.saturating_add(1);
                                        } else {
                                            distinct.push(neutral);
                                        }
                                    }
                                }
                                eprintln!("NUCLEUS_C88_EXACT_PENDING:{}",serde_json::json!({
                                    "seq":seq,"major_parents":major,
                                    "unique_exact_neutrals":distinct.len(),
                                    "exact_repeats":repeated,
                                    "full_captured_spine_and_environment":true,
                                    "same_source_name_alone_insufficient":true,
                                }));
                            }
"""
    source.write_text(text.replace(anchor,observer+anchor))


if __name__=="__main__":
    apply_c88()
    print("C88_EXACT_PENDING_NEUTRAL_CENSUS_APPLIED")
