"""Diagnostics-only source-origin census for C88's distinct unfinished Majors.

This records the *major argument source closure* of every pending recursor,
without changing source reduction, the work owner, proof rules, or verdicts.
Same ExprId may be instantiated under different checked captured environments.
"""
from pathlib import Path


def apply_c89(source=Path("metatron-kernel/src/machine.rs")):
    text = source.read_text()
    anchor = '                            if std::env::var_os("NUCLEUS_C88_EXACT_PENDING").is_some() {'
    assert text.count(anchor) == 1, "C89 exact C88 failure-site anchor drift"
    observer = r'''
                            if std::env::var_os("NUCLEUS_C89_MAJOR_SOURCE").is_some() {
                                let mut expr_counts=std::collections::BTreeMap::<u64,usize>::new();
                                let mut exact_major_closures=HashSet::<Closure>::new();
                                let mut repeated_major_closures=0usize;
                                let mut missing=0usize;
                                for pending in &parents {
                                    if let Continuation::Major(neutral,_) = pending {
                                        let source=match &neutral.head {
                                            NeutralHead::Const {name,..}=>self.recursor_reductions.get(name)
                                                .and_then(|reduction| {
                                                    let required=reduction.num_params.saturating_add(1)
                                                        .saturating_add(reduction.rules.len())
                                                        .saturating_add(reduction.num_indices)
                                                        .saturating_add(1);
                                                    neutral.spine.get(required-1)
                                                }),
                                            _=>None,
                                        };
                                        if let Some(major)=source {
                                            *expr_counts.entry(major.expr.0).or_insert(0)+=1;
                                            if !exact_major_closures.insert(major.clone()) {
                                                repeated_major_closures+=1;
                                            }
                                        } else {missing+=1;}
                                    }
                                }
                                let mut source_expr_groups:Vec<(u64,usize)>=expr_counts.into_iter().collect();
                                source_expr_groups.sort_by(|a,b|b.1.cmp(&a.1).then(a.0.cmp(&b.0)));
                                eprintln!("NUCLEUS_C89_MAJOR_SOURCE:{}",serde_json::json!({
                                    "seq":seq,
                                    "major_parents":major,
                                    "source_expr_groups":source_expr_groups,
                                    "unique_source_exprs":source_expr_groups.len(),
                                    "unique_major_closures":exact_major_closures.len(),
                                    "major_closure_repeats":repeated_major_closures,
                                    "missing_major_source":missing,
                                }));
                            }
'''
    source.write_text(text.replace(anchor, observer + anchor))


if __name__ == "__main__":
    apply_c89()
    print("C89_PENDING_MAJOR_SOURCE_CENSUS_APPLIED")
